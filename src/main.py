# Event-driven Pipeline Orchestrator for InstaLILY GTM Lead Generation
# Async with callbacks, shared rate limiter, file-based resume capability

import os
import sys
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stage1_event_discovery import discover_events, score_events, enrich_events
from stage2_company_qualification import (
    research_and_score_company, calculate_icp_score, save_scoring_json,
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

    # Concurrency limits for parallel processing
    MAX_CONCURRENT_STAGE2 = 2  # Companies processed in parallel for research & scoring
    MAX_CONCURRENT_STAGE3 = 3  # Companies processed in parallel for target role identification
    MAX_CONCURRENT_STAGE4 = 1  # Roles processed in parallel for outreach generation

    def __init__(self, data_dir: str = "data", tokens_per_min: int = 30000,
                 event_source: str = "web", event_file_path: str = None):
        self.data_dir = Path(data_dir)
        self.companies_dir = self.data_dir / "companies"
        self.events_dir = self.data_dir / "events"
        self.rate_limiter = RateLimiter(tokens_per_min=tokens_per_min)
        self.event_source = event_source
        self.event_file_path = event_file_path
        self.stats = {"stage1_events": 0, "stage2": 0, "stage3": 0, "stage4_roles": 0, "errors": []}
        self._stage2_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_STAGE2)
        self._stage4_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_STAGE4)
        # Incremental deduplication: track processed URLs across all events
        self._seen_urls = {}
        self._seen_urls_lock = asyncio.Lock()

    def _record_error(self, company: str, stage: int, error):
        self.stats["errors"].append({"company": company, "stage": stage, "error": str(error)})

    # EVENT HANDLERS (Callbacks)

    async def on_event_companies_discovered(self, event_name: str, companies: List[dict]):
        """Stage 1.3 complete for an event → trigger Stage 2 for each unique company."""
        print(f"\n[Event] Companies discovered at {event_name} -> {len(companies)} companies")
        self.stats["stage1_events"] += 1

        # Incremental deduplication and Stage 2 triggering
        unique_for_event = []
        async with self._seen_urls_lock:
            for company in companies:
                company_name = company.get("company_name", "")
                raw_url = company.get("website_url", "").lower().strip().rstrip("/")
                normalized_url = raw_url.replace("://www.", "://") or f"name:{company_name.lower()}"

                if normalized_url not in self._seen_urls:
                    self._seen_urls[normalized_url] = company_name
                    unique_for_event.append(company)
                else:
                    print(f"  Skipping duplicate: {company_name} (already seen)")

        if not unique_for_event:
            print(f"  No new unique companies from {event_name}")
            return

        print(f"  Processing {len(unique_for_event)} unique companies through Stage 2 (max {self.MAX_CONCURRENT_STAGE2} concurrent)...")

        # Trigger Stage 2 for each unique company (parallel with semaphore)
        async def process_with_semaphore(company: dict):
            async with self._stage2_semaphore:
                await self._process_company_stage2(company)

        await asyncio.gather(*[process_with_semaphore(c) for c in unique_for_event])

    async def on_company_scored(self, company_name: str, website_url: str, icp_score: float):
        """Stage 2 complete → trigger Stage 3 if score meets cutoff."""
        print(f"\n[Event] Company scored: {company_name} -> ICP Score: {icp_score}")

        if icp_score >= COMPANY_SCORE_CUTOFF:
            await self._process_company_stage3(company_name, website_url)
        else:
            print(f"  Skipping Stage 3 (score {icp_score} < cutoff {COMPANY_SCORE_CUTOFF})")

    async def on_target_roles_identified(self, company_name: str, website_url: str, target_roles: List[dict]):
        """Stage 3 complete → auto-trigger Stage 4 parallel processing + generate Sales Nav URLs & push to Clay"""
        print(f"\n[Event] Target roles identified: {company_name} -> {len(target_roles)} roles")

        # Auto-trigger Stage 4: outreach for each role (PARALLEL)
        valid_roles = [r for r in target_roles if r.get("title")]
        print(f"\n[Stage 4] Auto-generating outreach for {len(valid_roles)} roles at {company_name} (max {self.MAX_CONCURRENT_STAGE4} concurrent)")

        await asyncio.gather(*[self._process_role_stage4(r["title"], company_name) for r in valid_roles])
        self.stats["stage4_roles"] += len(valid_roles)

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

    # STAGE PROCESSORS

    def _discover_companies_for_event(self, event_name: str, event_url: str) -> dict:
        """Discover companies for a single event (sync, called via to_thread)."""
        from prompts import COMPANY_DISCOVERY_SYSTEM_PROMPT
        from constants import MODELS
        from utils.llm import call_claude, extract_json_from_response

        response = call_claude(
            system_prompt=COMPANY_DISCOVERY_SYSTEM_PROMPT,
            model=MODELS["company_discovery"],
            user_message=(
                f"Identify companies at this event:\n\n"
                f"Event: {event_name}\nURL: {event_url}\n\n"
                f"Return JSON only."
            ),
            max_tokens=16384,
            enable_web_search=True,
        )

        result = extract_json_from_response(response)

        if isinstance(result, dict) and "error" in result:
            print(f"    -> Error: {result['error']}")
            return {"event_name": event_name, "event_url": event_url, "success": False, "error": result["error"]}

        companies = result.get("companies", [])
        print(f"    -> {len(companies)} companies found")
        result["event_name"] = event_name
        result["event_url"] = event_url
        result["success"] = True
        return result

    async def _process_role_stage4(self, role_title: str, company_name: str):
        """Process a single role through Stage 4 (outreach generation)."""
        async with self._stage4_semaphore:
            await self.rate_limiter.acquire(estimated_tokens=8000)
            await asyncio.to_thread(process_role, role_title, company_name, base_dir=str(self.companies_dir))
            print(f"    [Stage 4] Completed: {role_title}")

    async def _process_company_stage2(self, company: dict):
        """Process a single company through Stage 2 (research + scoring)."""
        company_name = company.get("company_name", "")
        website_url = company.get("website_url", "")
        if not company_name:
            return

        scoring_path = company_path(str(self.companies_dir), company_name, "scoring.json")

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
            scoring_data = await asyncio.to_thread(research_and_score_company, company_name, website_url, str(self.companies_dir))

            if "error" in scoring_data:
                print(f"  Error: {scoring_data.get('error')}")
                self._record_error(company_name, 2, scoring_data.get("error"))
                return

            icp_result = calculate_icp_score(scoring_data)
            save_scoring_json(str(self.companies_dir), company_name, scoring_data, icp_result)

            self.stats["stage2"] += 1
            print(f"  Complete: ICP Score {icp_result['weighted_score']}")

            await self.on_company_scored(company_name, website_url, icp_result["weighted_score"])

        except Exception as e:
            print(f"  Exception: {e}")
            self._record_error(company_name, 2, e)

    async def _process_company_stage3(self, company_name: str, website_url: str):
        """Process a single company through Stage 3 (target roles)."""
        roles_path = company_path(str(self.companies_dir), company_name, "target_roles.json")

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
            target_roles_data = await asyncio.to_thread(identify_target_roles, company_name, website_url, str(self.companies_dir))

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

            scoring = load_json(company_path(str(self.companies_dir), name, "scoring.json"))
            has_stage3 = os.path.exists(company_path(str(self.companies_dir), name, "target_roles.json"))

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

        # Priority 1: Stage 3 first (closest to completion) - PARALLEL
        if needs_stage3:
            print(f"\n[Priority 1] Processing {len(needs_stage3)} companies through Stage 3 (max {self.MAX_CONCURRENT_STAGE3} concurrent)...")
            stage3_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_STAGE3)

            async def process_stage3_with_semaphore(company: dict):
                async with stage3_semaphore:
                    await self._process_company_stage3(company.get("company_name", ""), company.get("website_url", ""))

            await asyncio.gather(*[process_stage3_with_semaphore(c) for c in needs_stage3])

        # Priority 2: Stage 2 (Stage 3 auto-triggers via callback) - Sequential due to web search rate limits
        if needs_stage2:
            print(f"\n[Priority 2] Processing {len(needs_stage2)} companies through Stage 2 -> 3 (sequential - web search)...")
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
        print(f"\nINSTALILY GTM PIPELINE ORCHESTRATOR")
        print(f"  Data: {self.data_dir} | Event source: {self.event_source} | Rate limit: {self.rate_limiter.tokens_per_min} tokens/min")
        print(f"  Event cutoff: {EVENT_SCORE_CUTOFF} | Company cutoff: {COMPANY_SCORE_CUTOFF}")

        for subdir in [self.events_dir, self.companies_dir]:
            subdir.mkdir(parents=True, exist_ok=True)

        events_file = self.events_dir / "discovered_events.json"
        enriched_file = self.events_dir / "enriched_events.json"
        scored_file = self.events_dir / "scored_events.json"

        # Step 1.1: Discover events
        if events_file.exists():
            events = load_json(events_file)
            print(f"\n[Step 1.1] Event Discovery: {len(events)} events found in existing data")
        else:
            print(f"\n[Step 1.1] Event Discovery: using {self.event_source} source...")
            await self.rate_limiter.acquire(estimated_tokens=8000)
            events = await asyncio.to_thread(
                discover_events,
                source=self.event_source,
                file_path=self.event_file_path
            )
            save_json(events_file, events)
            print(f"  Discovered {len(events)} events")

        # Step 1.2: Enrich events (for sheet imports)
        final_events = events
        if self.event_source == "sheet":
            if enriched_file.exists():
                final_events = load_json(enriched_file)
                print(f"\n[Step 1.2] Event Enrichment: {len(final_events)} enriched events found in existing data")
            else:
                print(f"\n[Step 1.2] Event Enrichment: enriching {len(events)} events from sheet...")
                # With batching: estimate 48k tokens per batch of 12 events (4k per event)
                estimated_batches = (len(events) + 11) // 12  # Ceiling division
                await self.rate_limiter.acquire(estimated_tokens=estimated_batches * 48000)
                final_events = await asyncio.to_thread(enrich_events, events)
                save_json(enriched_file, final_events)
                print(f"  Enriched {len(final_events)} events")

        # Step 1.3: Score events
        scored = load_json(scored_file)
        if scored and (scored.get("scored_events") or not final_events):
            print(f"\n[Step 1.3] Event Scoring: {len(scored.get('scored_events', []))} scored events found in existing data")
        else:
            print(f"\n[Step 1.3] Event Scoring: scoring {len(final_events)} events...")
            await self.rate_limiter.acquire(estimated_tokens=8000)
            scored = await asyncio.to_thread(score_events, final_events)
            save_json(scored_file, scored)

        all_scored = scored.get("scored_events", [])
        target_events = [e for e in all_scored if e.get("overall_score", 0) >= EVENT_SCORE_CUTOFF]
        print(f"  {len(target_events)}/{len(all_scored)} events above cutoff ({EVENT_SCORE_CUTOFF})")

        # Step 1.4: Discover companies (EVENT-DRIVEN → triggers Stage 2 immediately)
        # Event company files are saved directly in events/ as {event_name}.json
        excluded_files = {"discovered_events.json", "enriched_events.json", "scored_events.json", "discovered_companies.json", "pipeline_summary.json"}
        existing_event_files = [f for f in self.events_dir.glob("*.json") if f.name not in excluded_files]

        if existing_event_files:
            # Resume: load existing event files and trigger Stage 2 for each
            print(f"\n[Step 1.4] Company Discovery: loading {len(existing_event_files)} existing event files...")
            for event_file in existing_event_files:
                event_data = load_json(event_file)
                if event_data and event_data.get("companies"):
                    event_name = event_data.get("event_name", event_file.stem)
                    await self.on_event_companies_discovered(event_name, event_data.get("companies", []))
        else:
            # Fresh run: discover companies for each event and trigger Stage 2 immediately
            print(f"\n[Step 1.4] Company Discovery: searching for companies at {len(target_events)} events (event-driven)..."
            for i, event in enumerate(target_events):
                event_name = event.get("event_name", "Unknown")
                event_url = event.get("event_url", "")
                print(f"\n  [{i+1}/{len(target_events)}] Discovering companies at: {event_name}")

                await self.rate_limiter.acquire(estimated_tokens=8000)
                event_result = await asyncio.to_thread(
                    self._discover_companies_for_event, event_name, event_url
                )

                if event_result and event_result.get("companies"):
                    # Save event file
                    from constants import sanitize_name
                    event_filepath = self.events_dir / f"{sanitize_name(event_name)}.json"
                    save_json(event_filepath, event_result)

                    # Trigger Stage 2 immediately for this event's companies
                    await self.on_event_companies_discovered(event_name, event_result.get("companies", []))

        print(f"\n  Total unique companies processed: {len(self._seen_urls)}")
        self._print_summary()

        summary = {"pipeline": "instalily_gtm_orchestrator", "timestamp": datetime.now().isoformat(), "stats": self.stats}
        save_json(self.data_dir / "pipeline_summary.json", summary)
        return summary



# CLI

def main():
    import argparse

    parser = argparse.ArgumentParser(description="InstaLILY GTM Pipeline Orchestrator")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--tokens-per-min", type=int, default=30000)
    parser.add_argument("--event-source", choices=["web", "sheet"], default="web",
                       help="Event source: 'web' for web discovery, 'sheet' for CSV/sheet import")
    parser.add_argument("--event-file", help="Path to CSV file for sheet import mode")

    args = parser.parse_args()

    if args.event_source == "sheet" and not args.event_file:
        print("Note: Using inline sheet data for sheet import mode")

    orchestrator = PipelineOrchestrator(
        data_dir=args.data_dir,
        tokens_per_min=args.tokens_per_min,
        event_source=args.event_source,
        event_file_path=args.event_file
    )
    asyncio.run(orchestrator.run_full_pipeline())


if __name__ == "__main__":
    main()
