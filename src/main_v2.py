import os
import sys
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stage1_event_discovery import discover_events, score_events
from stage3_contact_finding import (
    identify_target_roles, generate_sales_navigator_searches, push_company_to_clay, extract_domain,
)
from research_agent import run_research_agents_parallel
from outreach_agent import process_company_outreach
from constants import EVENT_SCORE_CUTOFF, COMPANY_SCORE_CUTOFF
from utils.io import load_json, save_json, company_path


# RATE LIMITER

class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, tokens_per_min: int = 30000):
        self.tokens_per_min = tokens_per_min
        self.tokens_used = 0
        self.window_start = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 4000):
        async with self._lock:
            while True:
                now = time.time()
                if now - self.window_start >= 60:
                    self.tokens_used = 0
                    self.window_start = now

                if self.tokens_used + estimated_tokens <= self.tokens_per_min:
                    self.tokens_used += estimated_tokens
                    return

                wait_time = 60 - (now - self.window_start) + 1
                print(f"  [Rate Limit] Waiting {wait_time:.0f}s ({self.tokens_used}/{self.tokens_per_min} tokens used)")

                self._lock.release()
                await asyncio.sleep(wait_time)
                await self._lock.acquire()


# PIPELINE ORCHESTRATOR V2

class PipelineOrchestratorV2:
    """Event-driven orchestrator using Research Agents. Auto-triggers downstream stages via callbacks."""

    def __init__(self, data_dir: str = "data", tokens_per_min: int = 30000, max_concurrent_agents: int = 3):
        self.data_dir = Path(data_dir)
        self.companies_dir = self.data_dir / "companies"
        self.events_dir = self.data_dir / "events"
        self.rate_limiter = RateLimiter(tokens_per_min=tokens_per_min)
        self.max_concurrent_agents = max_concurrent_agents
        self.stats = {"events_discovered": 0, "events_qualified": 0, "research_agents": {}, "stage3": 0, "stage4_roles": 0, "errors": []}

    def _record_error(self, context: str, stage: int, error):
        self.stats["errors"].append({"context": context, "stage": stage, "error": str(error)})

    # EVENT HANDLERS (Callbacks)

    async def on_company_scored(self, company_name: str, website_url: str, icp_score: float):
        """Stage 2 complete → trigger Stage 3 if score meets cutoff."""
        print(f"\n[Callback] Company scored: {company_name} -> ICP Score: {icp_score}")

        if icp_score >= COMPANY_SCORE_CUTOFF:
            await self._process_company_stage3(company_name, website_url)
        else:
            print(f"  Skipping Stage 3 (score {icp_score} < cutoff {COMPANY_SCORE_CUTOFF})")

    async def on_target_roles_identified(self, company_name: str, website_url: str, target_roles: List[dict]):
        """Stage 3 complete → generate Sales Nav URLs, push to Clay, trigger Stage 4."""
        print(f"\n[Callback] Target roles identified: {company_name} -> {len(target_roles)} roles")

        role_titles = [r["title"] for r in target_roles if r.get("title")]
        company_domain = extract_domain(website_url)

        # Generate and save Sales Navigator URLs
        searches = generate_sales_navigator_searches(company_name, company_domain, target_roles)
        save_json(company_path(str(self.companies_dir), company_name, "linkedin_searches.json"), searches)
        print(f"  Generated {len(searches)} LinkedIn search URLs")

        # Push to Clay webhook
        icp_score_path = company_path(str(self.companies_dir), company_name, "scoring.json")
        icp_score = (load_json(icp_score_path) or {}).get("icp_qualification", {}).get("weighted_score", 0)

        clay_result = push_company_to_clay(company_name, website_url, role_titles, icp_score)
        if clay_result.get("success"):
            print(f"  Pushed to Clay (status {clay_result.get('status_code')})")
        else:
            print(f"  Clay push failed: {clay_result.get('error')}")

        # Auto-trigger Stage 4: OutreachAgent processes ALL roles in one conversation
        await self.rate_limiter.acquire(estimated_tokens=8000)
        outreach_stats = await asyncio.to_thread(
            process_company_outreach,
            company_name,
            website_url,
            target_roles,
            str(self.companies_dir),
        )

        self.stats["stage4_roles"] += outreach_stats.get("roles_processed", 0)
        if outreach_stats.get("errors"):
            for error in outreach_stats["errors"]:
                self._record_error(f"{company_name}/{error.get('role', 'unknown')}", 4, error.get("error", ""))

    # STAGE PROCESSORS

    async def _process_company_stage3(self, company_name: str, website_url: str):
        """Process a single company through Stage 3 (target roles)."""
        roles_path = company_path(str(self.companies_dir), company_name, "target_roles.json")

        # Already processed
        if os.path.exists(roles_path):
            print(f"\n[Stage 3] {company_name} - found in existing data")
            target_roles_data = load_json(roles_path)
            if target_roles_data:
                await self.on_target_roles_identified(
                    company_name, website_url, target_roles_data.get("target_roles", [])
                )
            return

        print(f"\n[Stage 3] Processing: {company_name}")

        try:
            await self.rate_limiter.acquire(estimated_tokens=4000)
            target_roles_data = await asyncio.to_thread(
                identify_target_roles, company_name, website_url, str(self.companies_dir)
            )

            if "error" in target_roles_data:
                print(f"  Error: {target_roles_data.get('error')}")
                self._record_error(company_name, 3, target_roles_data.get("error"))
                return

            target_roles = target_roles_data.get("target_roles", [])
            self.stats["stage3"] += 1
            print(f"  Complete: {len(target_roles)} target roles identified")

            await self.on_target_roles_identified(company_name, website_url, target_roles)

        except Exception as e:
            print(f"  Exception: {e}")
            self._record_error(company_name, 3, e)

    # RESUME CAPABILITY

    async def _process_scored_companies(self):
        """Find companies with scoring.json but no target_roles.json and process them."""
        if not self.companies_dir.exists():
            return

        for folder in self.companies_dir.iterdir():
            if not folder.is_dir():
                continue

            scoring_path = folder / "scoring.json"
            if not scoring_path.exists() or (folder / "target_roles.json").exists():
                continue

            scoring = load_json(str(scoring_path))
            if not scoring:
                continue

            icp_score = scoring.get("icp_qualification", {}).get("weighted_score", 0)
            if icp_score >= COMPANY_SCORE_CUTOFF:
                await self._process_company_stage3(
                    scoring.get("company_name", folder.name),
                    scoring.get("website_url", ""),
                )

    # MAIN ENTRY POINT

    async def run_full_pipeline(self):
        """Run full pipeline: Stage 1 (events) -> Stage 2 (research agents) -> Stage 3 (roles) -> Stage 4 (outreach)."""
        print(f"TEDLAR GTM PIPELINE V2 (with Research & Outreach Agents)\n")

        for subdir in [self.events_dir, self.companies_dir]:
            subdir.mkdir(parents=True, exist_ok=True)

        events_file = self.events_dir / "discovered_events.json"
        scored_file = self.events_dir / "scored_events.json"

        # Step 1.1: Discover events
        if events_file.exists():
            events = load_json(str(events_file))
            print(f"\n[Step 1.1] Event Discovery: {len(events)} events found in cache")
        else:
            print(f"\n[Step 1.1] Event Discovery: searching for trade shows...")
            await self.rate_limiter.acquire(estimated_tokens=8000)
            events = await asyncio.to_thread(discover_events)
            save_json(str(events_file), events)
            print(f"  Discovered {len(events)} events")

        self.stats["events_discovered"] = len(events)

        # Step 1.2: Score events
        scored = load_json(str(scored_file))
        if scored and scored.get("scored_events"):
            print(f"\n[Step 1.2] Event Scoring: {len(scored.get('scored_events', []))} events found in cache")
        else:
            print(f"\n[Step 1.2] Event Scoring: scoring {len(events)} events...")
            await self.rate_limiter.acquire(estimated_tokens=8000)
            scored = await asyncio.to_thread(score_events, events)
            save_json(str(scored_file), scored)

        all_scored = scored.get("scored_events", [])
        qualified_events = [e for e in all_scored if e.get("overall_score", 0) >= EVENT_SCORE_CUTOFF]
        print(f"  {len(qualified_events)}/{len(all_scored)} events above cutoff ({EVENT_SCORE_CUTOFF})")

        self.stats["events_qualified"] = len(qualified_events)

        # Step 2: Research Agents (parallel company discovery + research)
        if qualified_events:
            print(f"\n[Step 2] Launching Research Agents for {len(qualified_events)} events...")

            agent_stats = await run_research_agents_parallel(
                events=qualified_events,
                companies_dir=str(self.companies_dir),
                events_dir=str(self.events_dir),
                rate_limiter=self.rate_limiter,
                on_company_scored=self.on_company_scored,
                max_concurrent=self.max_concurrent_agents,
            )

            self.stats["research_agents"] = agent_stats

        # Resume: process companies needing Stage 3+
        await self._process_scored_companies()

        self._print_summary()
        summary = {"pipeline": "tedlar_gtm_orchestrator_v2", "timestamp": datetime.now().isoformat(), "stats": self.stats}
        save_json(str(self.data_dir / "pipeline_summary.json"), summary)
        return summary

    def _print_summary(self):
        print(f"\n{'='*70}")
        print(f"PIPELINE COMPLETE")
        print(f"{'='*70}")
        print(f"  Events discovered: {self.stats['events_discovered']}")
        print(f"  Events qualified: {self.stats['events_qualified']}")

        ra = self.stats.get("research_agents", {})
        if ra:
            print(f"  Research Agents: {ra.get('total_discovered', 0)} discovered, "
                  f"{ra.get('total_researched', 0)} researched, {ra.get('total_qualified', 0)} qualified")

        print(f"  Stage 3 (roles): {self.stats['stage3']}")
        print(f"  Stage 4 (outreach): {self.stats['stage4_roles']} roles")
        print(f"  Errors: {len(self.stats['errors'])}")

        if self.stats["errors"]:
            print(f"\n  Recent errors:")
            for error in self.stats["errors"][:5]:
                print(f"    - {error['context']} (Stage {error['stage']}): {error['error']}")
            if len(self.stats["errors"]) > 5:
                print(f"    ... and {len(self.stats['errors']) - 5} more")


# CLI

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tedlar GTM Pipeline Orchestrator V2")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--tokens-per-min", type=int, default=30000)
    parser.add_argument("--max-concurrent", type=int, default=3)
    args = parser.parse_args()

    orchestrator = PipelineOrchestratorV2(args.data_dir, args.tokens_per_min, args.max_concurrent)
    asyncio.run(orchestrator.run_full_pipeline())


if __name__ == "__main__":
    main()
