# Event-driven Pipeline Orchestrator for Tedlar GTM Lead Generation
# Async with callbacks, shared rate limiter, file-based resume capability

import os
import sys
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stage1_event_discovery import discover_events, score_events, discover_companies
from stage2_company_qualification import (
    research_and_score_company, calculate_icp_score, save_scoring_json, deduplicate_companies,
)
from stage3_contact_finding import (
    identify_target_roles, generate_sales_navigator_searches, push_company_to_clay, extract_domain,
)
from stage4_outreach_generation import process_role
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


# PIPELINE ORCHESTRATOR

class PipelineOrchestrator:
    """Event-driven orchestrator. Auto-triggers downstream stages via callbacks."""

    def __init__(self, data_dir: str = "data", tokens_per_min: int = 30000):
        self.data_dir = Path(data_dir)
        self.companies_dir = self.companies_dir
        self.contacts_dir = self.contacts_dir
        self.rate_limiter = RateLimiter(tokens_per_min=tokens_per_min)
        self.stats = {"stage2": 0, "stage3": 0, "stage4_roles": 0, "errors": []}

    def _record_error(self, company: str, stage: int, error):
        self.stats["errors"].append({"company": company, "stage": stage, "error": str(error)})

    # EVENT HANDLERS (Callbacks)

    async def on_company_scored(self, company_name: str, website_url: str, icp_score: float):
        """Stage 2 complete → trigger Stage 3 if score meets cutoff."""
        print(f"\n[Event] Company scored: {company_name} -> ICP Score: {icp_score}")

        if icp_score >= COMPANY_SCORE_CUTOFF:
            await self._process_company_stage3(company_name, website_url)
        else:
            print(f"  Skipping Stage 3 (score {icp_score} < cutoff {COMPANY_SCORE_CUTOFF})")

    async def on_target_roles_identified(self, company_name: str, website_url: str, target_roles: List[dict]):
        """Stage 3 complete → generate Sales Nav URLs, push to Clay, auto-trigger Stage 4."""
        print(f"\n[Event] Target roles identified: {company_name} -> {len(target_roles)} roles")

        role_titles = [r["title"] for r in target_roles if r.get("title")]
        company_domain = extract_domain(website_url)

        # Generate and save Sales Navigator URLs
        searches = generate_sales_navigator_searches(company_name, company_domain, target_roles)
        save_json(company_path(self.companies_dir, company_name, "linkedin_searches.json"), searches)
        print(f"  Generated {len(searches)} LinkedIn search URLs")

        # Push to Clay webhook
        icp_score_path = company_path(self.companies_dir, company_name, "scoring.json")
        icp_score = (load_json(icp_score_path) or {}).get("icp_qualification", {}).get("weighted_score", 0)

        clay_result = push_company_to_clay(company_name, website_url, role_titles, icp_score)
        if clay_result.get("success"):
            print(f"  Pushed to Clay (status {clay_result.get('status_code')})")
        else:
            print(f"  Clay push failed: {clay_result.get('error')}")

        # Auto-trigger Stage 4: outreach for each role
        print(f"\n[Stage 4] Auto-generating outreach for {len(target_roles)} roles at {company_name}")
        for role in target_roles:
            role_title = role.get("title", "")
            if not role_title:
                continue

            await self.rate_limiter.acquire(estimated_tokens=8000)
            await asyncio.to_thread(process_role, role_title, company_name, base_dir=self.companies_dir, output_dir=self.contacts_dir)

        self.stats["stage4_roles"] += len(target_roles)

    # STAGE PROCESSORS

    async def _process_company_stage2(self, company: dict):
        """Process a single company through Stage 2 (research + scoring)."""
        company_name = company.get("company_name", "")
        website_url = company.get("website_url", "")
        if not company_name:
            return

        scoring_path = company_path(self.companies_dir, company_name, "scoring.json")

        # Already processed
        if os.path.exists(scoring_path):
            print(f"\n[Stage 2] {company_name} - found in existing data")
            scoring = load_json(scoring_path)
            icp_score = (scoring or {}).get("icp_qualification", {}).get("weighted_score", 0)
            await self.on_company_scored(company_name, website_url, icp_score)
            return

        print(f"\n[Stage 2] Processing: {company_name}")

        try:
            await self.rate_limiter.acquire(estimated_tokens=10000)
            scoring_data = await asyncio.to_thread(research_and_score_company, company_name, website_url, self.companies_dir)

            if "error" in scoring_data:
                print(f"  Error: {scoring_data.get('error')}")
                self._record_error(company_name, 2, scoring_data.get("error"))
                return

            icp_result = calculate_icp_score(scoring_data)
            save_scoring_json(self.companies_dir, company_name, scoring_data, icp_result)

            self.stats["stage2"] += 1
            print(f"  Complete: ICP Score {icp_result['weighted_score']}")

            await self.on_company_scored(company_name, website_url, icp_result["weighted_score"])

        except Exception as e:
            print(f"  Exception: {e}")
            self._record_error(company_name, 2, e)

    async def _process_company_stage3(self, company_name: str, website_url: str):
        """Process a single company through Stage 3 (target roles)."""
        roles_path = company_path(self.companies_dir, company_name, "target_roles.json")

        # Already processed
        if os.path.exists(roles_path):
            print(f"\n[Stage 3] {company_name} - found in existing data")
            target_roles_data = load_json(roles_path)
            if target_roles_data:
                await self.on_target_roles_identified(company_name, website_url, target_roles_data.get("target_roles", []))
            return

        print(f"\n[Stage 3] Processing: {company_name}")

        try:
            await self.rate_limiter.acquire(estimated_tokens=4000)
            target_roles_data = await asyncio.to_thread(identify_target_roles, company_name, website_url, self.companies_dir)

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

    # WORK QUEUE HELPERS

    def _needs_stage(self, companies: List[dict], stage: int) -> List[dict]:
        """Find companies needing a specific stage."""
        result = []
        for company in companies:
            name = company.get("company_name", "")
            if not name:
                continue

            scoring = load_json(company_path(self.companies_dir, name, "scoring.json"))
            has_stage3 = os.path.exists(company_path(self.companies_dir, name, "target_roles.json"))

            if stage == 2 and not scoring:
                result.append(company)
            elif stage == 3 and scoring and not has_stage3:
                score = scoring.get("icp_qualification", {}).get("weighted_score", 0)
                if score >= COMPANY_SCORE_CUTOFF:
                    result.append(company)

        return result

    async def _process_work_queue(self, unique_companies: List[dict]):
        """Process companies through stages 2-4 with priority ordering (later stages first)."""
        needs_stage3 = self._needs_stage(unique_companies, 3)
        needs_stage2 = self._needs_stage(unique_companies, 2)

        print(f"\n[Work Queue]")
        print(f"  {len(needs_stage3)} companies need Stage 3 (already have Stage 2)")
        print(f"  {len(needs_stage2)} companies need Stage 2")

        # Priority 1: Stage 3 first (closest to completion)
        if needs_stage3:
            print(f"\n[Priority 1] Processing {len(needs_stage3)} companies through Stage 3...")
            for company in needs_stage3:
                await self._process_company_stage3(company.get("company_name", ""), company.get("website_url", ""))

        # Priority 2: Stage 2 (Stage 3 auto-triggers via callback)
        if needs_stage2:
            print(f"\n[Priority 2] Processing {len(needs_stage2)} companies through Stage 2 -> 3...")
            for company in needs_stage2:
                await self._process_company_stage2(company)

    def _print_summary(self):
        print(f"\nPIPELINE COMPLETE")
        print(f"  Stage 2 (scoring): {self.stats['stage2']}")
        print(f"  Stage 3 (roles): {self.stats['stage3']}")
        print(f"  Stage 4 (outreach): {self.stats['stage4_roles']} roles")
        print(f"  Errors: {len(self.stats['errors'])}")

        if self.stats["errors"]:
            for error in self.stats["errors"][:5]:
                print(f"    - {error['company']} (Stage {error['stage']}): {error['error']}")
            if len(self.stats["errors"]) > 5:
                print(f"    ... and {len(self.stats['errors']) - 5} more")

    # MAIN ENTRY POINTS

    async def run_full_pipeline(self):
        """Run full pipeline: Stage 1 (events) -> Stage 2 (scoring) -> Stage 3 (roles) -> Stage 4 (outreach)."""
        print(f"\nTEDLAR GTM PIPELINE ORCHESTRATOR")
        print(f"  Data: {self.data_dir} | Rate limit: {self.rate_limiter.tokens_per_min} tokens/min")
        print(f"  Event cutoff: {EVENT_SCORE_CUTOFF} | Company cutoff: {COMPANY_SCORE_CUTOFF}")

        for subdir in ["events", "companies", "contacts"]:
            (self.data_dir / subdir).mkdir(parents=True, exist_ok=True)

        events_file = self.data_dir / "events" / "discovered_events.json"
        scored_file = self.data_dir / "events" / "scored_events.json"

        # Step 1.1: Discover events
        if events_file.exists():
            events = load_json(events_file)
            print(f"\n[Step 1.1] Event Discovery: {len(events)} events found in existing data")
        else:
            print(f"\n[Step 1.1] Event Discovery: searching for trade shows...")
            await self.rate_limiter.acquire(estimated_tokens=8000)
            events = await asyncio.to_thread(discover_events)
            save_json(events_file, events)
            print(f"  Discovered {len(events)} events")

        # Step 1.2: Score events
        scored = load_json(scored_file)
        if scored and (scored.get("scored_events") or not events):
            print(f"\n[Step 1.2] Event Scoring: {len(scored.get('scored_events', []))} scored events found in existing data")
        else:
            print(f"\n[Step 1.2] Event Scoring: scoring {len(events)} events...")
            await self.rate_limiter.acquire(estimated_tokens=8000)
            scored = await asyncio.to_thread(score_events, events)
            save_json(scored_file, scored)

        all_scored = scored.get("scored_events", [])
        target_events = [e for e in all_scored if e.get("overall_score", 0) >= EVENT_SCORE_CUTOFF]
        print(f"  {len(target_events)}/{len(all_scored)} events above cutoff ({EVENT_SCORE_CUTOFF})")

        # Step 1.3: Discover companies
        events_companies_dir = self.data_dir / "events" / "companies"
        existing_event_files = list(events_companies_dir.glob("*.json")) if events_companies_dir.exists() else []

        if existing_event_files:
            print(f"\n[Step 1.3] Company Discovery: loading {len(existing_event_files)} existing event files...")
            discovery_results = [d for f in existing_event_files if (d := load_json(f))]
        else:
            print(f"\n[Step 1.3] Company Discovery: searching for companies at {len(target_events)} events...")
            discovery_results = await asyncio.to_thread(discover_companies, target_events, str(self.data_dir / "events"))

        unique_companies = deduplicate_companies(discovery_results)
        print(f"  {len(unique_companies)} unique companies discovered")

        # Stages 2-4
        await self._process_work_queue(unique_companies)
        self._print_summary()

        summary = {"pipeline": "tedlar_gtm_orchestrator", "timestamp": datetime.now().isoformat(), "stats": self.stats}
        save_json(self.data_dir / "pipeline_summary.json", summary)
        return summary



# CLI

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Tedlar GTM Pipeline Orchestrator")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--tokens-per-min", type=int, default=30000)

    args = parser.parse_args()

    orchestrator = PipelineOrchestrator(data_dir=args.data_dir, tokens_per_min=args.tokens_per_min)
    asyncio.run(orchestrator.run_full_pipeline())


if __name__ == "__main__":
    main()
