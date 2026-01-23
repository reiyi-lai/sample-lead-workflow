# main.py
# Event-driven Pipeline Orchestrator for Tedlar GTM Lead Generation
#
# Architecture:
# - Async/await with callbacks for automatic stage triggering
# - Shared rate limiter across all stages
# - File-based state for resume capability
# - Parallel processing where possible (respecting rate limits)

import os
import sys
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import stage functions
from stage1_event_discovery import (
    discover_events,
    score_events,
    discover_companies,
    sanitize_event_name,
)
from stage2_company_qualification import (
    research_and_score_company,
    calculate_icp_score,
    save_scoring_json,
    get_company_folder,
    deduplicate_companies,
)
from stage3_contact_finding import (
    identify_target_roles,
    generate_sales_navigator_searches,
    extract_domain,
)
from stage4_outreach_generation import (
    process_contact,
)


# RATE LIMITER

class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    Tracks estimated token usage and enforces rate limits.
    """

    def __init__(self, tokens_per_min: int = 30000):
        self.tokens_per_min = tokens_per_min
        self.tokens_used = 0
        self.window_start = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 4000):
        """
        Wait if necessary, then reserve tokens.

        Args:
            estimated_tokens: Estimated tokens for the API call
        """
        async with self._lock:
            while True:
                now = time.time()

                # Reset window if minute passed
                if now - self.window_start >= 60:
                    self.tokens_used = 0
                    self.window_start = now

                # Check if we can proceed
                if self.tokens_used + estimated_tokens <= self.tokens_per_min:
                    self.tokens_used += estimated_tokens
                    return

                # Calculate wait time
                wait_time = 60 - (now - self.window_start) + 1  # +1 buffer
                print(f"  [Rate Limit] Waiting {wait_time:.0f}s (used {self.tokens_used}/{self.tokens_per_min} tokens)...")

                # Release lock while waiting
                self._lock.release()
                await asyncio.sleep(wait_time)
                await self._lock.acquire()

    def get_usage(self) -> dict:
        """Get current usage stats."""
        return {
            "tokens_used": self.tokens_used,
            "tokens_per_min": self.tokens_per_min,
            "window_start": self.window_start,
        }


# HELPER FUNCTIONS

def load_json(path: Path) -> Optional[dict]:
    """Load JSON file if it exists."""
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return None


def save_json(path: Path, data: Any):
    """Save data to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def check_company_stage2_complete(data_dir: Path, company_name: str) -> bool:
    """Check if Stage 2 (research + scoring) is complete for a company."""
    from stage2_company_qualification import sanitize_company_name
    folder_name = sanitize_company_name(company_name)
    company_dir = data_dir / "companies" / folder_name

    research_file = company_dir / "research.json"
    scoring_file = company_dir / "scoring.json"

    return research_file.exists() and scoring_file.exists()


def check_company_stage3_complete(data_dir: Path, company_name: str) -> bool:
    """Check if Stage 3 (target roles) is complete for a company."""
    from stage2_company_qualification import sanitize_company_name
    folder_name = sanitize_company_name(company_name)
    company_dir = data_dir / "companies" / folder_name

    target_roles_file = company_dir / "target_roles.json"
    return target_roles_file.exists()


def get_company_tier(data_dir: Path, company_name: str) -> Optional[int]:
    """Get the tier for a company from its scoring.json."""
    from stage2_company_qualification import sanitize_company_name
    folder_name = sanitize_company_name(company_name)
    scoring_file = data_dir / "companies" / folder_name / "scoring.json"

    if scoring_file.exists():
        scoring = load_json(scoring_file)
        return scoring.get("icp_qualification", {}).get("tier")
    return None


# PIPELINE ORCHESTRATOR

class PipelineOrchestrator:
    """
    Event-driven orchestrator for the Tedlar GTM pipeline.

    Automatically triggers downstream stages when data becomes available.
    Respects rate limits and supports resume from interruption.
    """

    def __init__(
        self,
        data_dir: str = "data",
        tokens_per_min: int = 30000,
        target_tiers: List[int] = [1, 2],
    ):
        self.data_dir = Path(data_dir)
        self.rate_limiter = RateLimiter(tokens_per_min=tokens_per_min)
        self.target_tiers = target_tiers

        # Stats tracking
        self.stats = {
            "companies_processed_stage2": 0,
            "companies_processed_stage3": 0,
            "contacts_processed_stage4": 0,
            "errors": [],
        }

        # Active tasks for tracking
        self._active_tasks: set = set()

    # EVENT HANDLERS (Callbacks)

    async def on_companies_discovered(self, companies: List[dict]):
        """
        Triggered when Stage 1 discovers companies.
        Starts Stage 2 for each company.
        """
        print(f"\n[Event] Companies discovered: {len(companies)} companies")

        for company in companies:
            task = asyncio.create_task(
                self._process_company_stage2(company)
            )
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)

    async def on_company_scored(self, company_name: str, website_url: str, tier: int, icp_score: float):
        """
        Triggered when Stage 2 completes for a company.
        If Tier 1 or 2, triggers Stage 3.
        """
        print(f"\n[Event] Company scored: {company_name} -> Tier {tier} (Score: {icp_score})")

        if tier in self.target_tiers:
            task = asyncio.create_task(
                self._process_company_stage3(company_name, website_url)
            )
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)
        else:
            print(f"  -> Skipping Stage 3 (Tier {tier} not in target tiers {self.target_tiers})")

    async def on_target_roles_identified(self, company_name: str, website_url: str, target_roles: List[dict]):
        """
        Triggered when Stage 3 completes for a company.
        Generates LinkedIn Sales Navigator search URLs.
        """
        print(f"\n[Event] Target roles identified: {company_name} -> {len(target_roles)} roles")

        # Generate Sales Navigator URLs
        company_domain = extract_domain(website_url)
        searches = generate_sales_navigator_searches(
            company_name=company_name,
            company_domain=company_domain,
            target_roles=target_roles,
        )

        # Save searches to company folder
        from stage2_company_qualification import sanitize_company_name
        folder_name = sanitize_company_name(company_name)
        searches_file = self.data_dir / "companies" / folder_name / "linkedin_searches.json"
        save_json(searches_file, searches)

        print(f"  -> Generated {len(searches)} LinkedIn search URLs")
        print(f"  -> Saved to: {searches_file}")

    # STAGE PROCESSORS

    async def _process_company_stage2(self, company: dict):
        """
        Process a single company through Stage 2 (research + scoring).
        """
        company_name = company.get("company_name", "")
        website_url = company.get("website_url", "")

        if not company_name:
            return

        # Check if already processed
        if check_company_stage2_complete(self.data_dir, company_name):
            print(f"\n[Stage 2] {company_name} - Already complete, loading...")
            tier = get_company_tier(self.data_dir, company_name)
            if tier is not None:
                # Load scoring to get ICP score
                from stage2_company_qualification import sanitize_company_name
                folder_name = sanitize_company_name(company_name)
                scoring = load_json(self.data_dir / "companies" / folder_name / "scoring.json")
                icp_score = scoring.get("icp_qualification", {}).get("weighted_score", 0)

                # Trigger next stage
                await self.on_company_scored(company_name, website_url, tier, icp_score)
            return

        print(f"\n[Stage 2] Processing: {company_name}")

        try:
            # Acquire rate limit tokens (research uses ~6000, scoring uses ~3000)
            await self.rate_limiter.acquire(estimated_tokens=10000)

            # Run research and scoring (synchronous, run in executor)
            loop = asyncio.get_event_loop()
            research_data, scoring_data = await loop.run_in_executor(
                None,
                lambda: research_and_score_company(
                    company_name=company_name,
                    website_url=website_url,
                    output_dir=str(self.data_dir / "companies"),
                )
            )

            # Check for errors
            if "error" in research_data or "error" in scoring_data:
                error_msg = research_data.get("error") or scoring_data.get("error")
                print(f"  -> Error: {error_msg}")
                self.stats["errors"].append({
                    "company": company_name,
                    "stage": 2,
                    "error": error_msg,
                })
                return

            # Calculate ICP score
            icp_result = calculate_icp_score(scoring_data)
            tier = icp_result["tier"]
            icp_score = icp_result["weighted_score"]

            # Save scoring with ICP result
            save_scoring_json(
                str(self.data_dir / "companies"),
                company_name,
                scoring_data,
                icp_result,
            )

            self.stats["companies_processed_stage2"] += 1
            print(f"  -> Complete: Tier {tier}, Score {icp_score}")

            # Trigger next stage
            await self.on_company_scored(company_name, website_url, tier, icp_score)

        except Exception as e:
            print(f"  -> Exception: {e}")
            self.stats["errors"].append({
                "company": company_name,
                "stage": 2,
                "error": str(e),
            })

    async def _process_company_stage3(self, company_name: str, website_url: str):
        """
        Process a single company through Stage 3 (target roles).
        """
        # Check if already processed
        if check_company_stage3_complete(self.data_dir, company_name):
            print(f"\n[Stage 3] {company_name} - Already complete, loading...")

            # Load existing target roles
            from stage2_company_qualification import sanitize_company_name
            folder_name = sanitize_company_name(company_name)
            target_roles_data = load_json(
                self.data_dir / "companies" / folder_name / "target_roles.json"
            )

            if target_roles_data:
                target_roles = target_roles_data.get("target_roles", [])
                await self.on_target_roles_identified(company_name, website_url, target_roles)
            return

        print(f"\n[Stage 3] Processing: {company_name}")

        try:
            # Acquire rate limit tokens
            await self.rate_limiter.acquire(estimated_tokens=4000)

            # Run target role identification (synchronous, run in executor)
            loop = asyncio.get_event_loop()
            target_roles_data = await loop.run_in_executor(
                None,
                lambda: identify_target_roles(
                    company_name=company_name,
                    website_url=website_url,
                    base_dir=str(self.data_dir / "companies"),
                )
            )

            # Check for errors
            if "error" in target_roles_data:
                print(f"  -> Error: {target_roles_data.get('error')}")
                self.stats["errors"].append({
                    "company": company_name,
                    "stage": 3,
                    "error": target_roles_data.get("error"),
                })
                return

            target_roles = target_roles_data.get("target_roles", [])
            self.stats["companies_processed_stage3"] += 1
            print(f"  -> Complete: {len(target_roles)} target roles identified")

            # Trigger next event
            await self.on_target_roles_identified(company_name, website_url, target_roles)

        except Exception as e:
            print(f"  -> Exception: {e}")
            self.stats["errors"].append({
                "company": company_name,
                "stage": 3,
                "error": str(e),
            })

    # MAIN ENTRY POINTS

    def _find_companies_needing_stage3(self, unique_companies: List[dict]) -> List[dict]:
        """
        Find companies that have completed Stage 2 but not Stage 3.
        These should be processed first (finish what's started).
        """
        needs_stage3 = []
        for company in unique_companies:
            company_name = company.get("company_name", "")
            if not company_name:
                continue

            # Has Stage 2 complete?
            if not check_company_stage2_complete(self.data_dir, company_name):
                continue

            # Already has Stage 3?
            if check_company_stage3_complete(self.data_dir, company_name):
                continue

            # Check tier - only process target tiers
            tier = get_company_tier(self.data_dir, company_name)
            if tier not in self.target_tiers:
                continue

            needs_stage3.append(company)

        return needs_stage3

    def _find_companies_needing_stage2(self, unique_companies: List[dict]) -> List[dict]:
        """
        Find companies that have not completed Stage 2.
        """
        needs_stage2 = []
        for company in unique_companies:
            company_name = company.get("company_name", "")
            if not company_name:
                continue

            if not check_company_stage2_complete(self.data_dir, company_name):
                needs_stage2.append(company)

        return needs_stage2

    async def run_full_pipeline(self):
        """
        Run the full pipeline from Stage 1 through Stage 3.
        Stage 4 requires manual contact input and is run separately.

        PRIORITY ORDER: Later stages first (finish what's started)
        1. First, process companies needing Stage 3 (already have Stage 2 done)
        2. Then, process companies needing Stage 2
        """
        print("\n" + "=" * 70)
        print("TEDLAR GTM PIPELINE ORCHESTRATOR")
        print("=" * 70)
        print(f"Started at: {datetime.now().isoformat()}")
        print(f"Data directory: {self.data_dir}")
        print(f"Rate limit: {self.rate_limiter.tokens_per_min} tokens/min")
        print(f"Target tiers: {self.target_tiers}")

        # Ensure directories exist
        (self.data_dir / "events").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "companies").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "contacts").mkdir(parents=True, exist_ok=True)

        # STAGE 1: Event Discovery
        events_file = self.data_dir / "events" / "discovered_events.json"
        scored_file = self.data_dir / "events" / "scored_events.json"

        # Step 1.1: Discover events (or load existing)
        if events_file.exists():
            print(f"\n[Stage 1.1] Loading existing events from: {events_file}")
            events = load_json(events_file)
            print(f"  -> Loaded {len(events)} events (cached)")
        else:
            print(f"\n[Stage 1.1] Discovering events...")
            await self.rate_limiter.acquire(estimated_tokens=8000)

            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(None, discover_events)

            save_json(events_file, events)
            print(f"  -> Discovered {len(events)} events")

        # Step 1.2: Score events (or load existing)
        scored = None
        if scored_file.exists():
            print(f"\n[Stage 1.2] Checking existing scored events: {scored_file}")
            scored = load_json(scored_file)
            qualified_count = len(scored.get("qualified_events", []))
            rejected_count = len(scored.get("rejected_events", []))

            # If both empty but we have events, it was a failed parse - re-run
            if qualified_count == 0 and rejected_count == 0 and len(events) > 0:
                print(f"  -> Cached file appears to be from failed parse, re-scoring...")
                scored = None
            else:
                print(f"  -> Loaded {qualified_count} qualified events (cached)")

        if scored is None:
            print(f"\n[Stage 1.2] Scoring {len(events)} events...")
            await self.rate_limiter.acquire(estimated_tokens=8000)

            loop = asyncio.get_event_loop()
            scored = await loop.run_in_executor(None, lambda: score_events(events))

            save_json(scored_file, scored)

        # Get qualified events
        qualified_events = scored.get("qualified_events", [])
        tier_1_events = [e for e in qualified_events if e.get("tier") == 1]

        print(f"\n[Stage 1] Summary:")
        print(f"  -> {len(events)} events discovered")
        print(f"  -> {len(qualified_events)} qualified (Tier 1 & 2)")
        print(f"  -> {len(tier_1_events)} Tier 1 events")

        # Step 1.3: Discover companies for Tier 1 events
        print(f"\n[Stage 1.3] Discovering companies for {len(tier_1_events)} Tier 1 events...")

        # Check for existing discovered_companies.json
        discovered_companies_file = self.data_dir / "events" / "discovered_companies.json"

        if discovered_companies_file.exists():
            print(f"  -> Loading existing discovered companies...")
            discovery_results = load_json(discovered_companies_file)
        else:
            # Run company discovery for each event
            loop = asyncio.get_event_loop()
            discovery_results = await loop.run_in_executor(
                None,
                lambda: discover_companies(tier_1_events, str(self.data_dir / "events"))
            )
            save_json(discovered_companies_file, discovery_results)

        # Deduplicate companies
        unique_companies = deduplicate_companies(discovery_results)
        print(f"  -> {len(unique_companies)} unique companies discovered")

        # STAGE 2 & 3: Process companies with PRIORITY ORDER
        # Priority: Later stages first (finish what's started)

        # Check what work needs to be done at each stage
        needs_stage3 = self._find_companies_needing_stage3(unique_companies)
        needs_stage2 = self._find_companies_needing_stage2(unique_companies)

        print(f"\n[Work Queue] Checking existing progress...")
        print(f"  -> {len(needs_stage3)} companies need Stage 3 (already have Stage 2)")
        print(f"  -> {len(needs_stage2)} companies need Stage 2")

        # PRIORITY 1: Process Stage 3 first (companies closest to completion)
        if needs_stage3:
            print(f"\n[Priority 1] Processing {len(needs_stage3)} companies through Stage 3...")
            for company in needs_stage3:
                company_name = company.get("company_name", "")
                website_url = company.get("website_url", "")

                # Load tier and score from existing Stage 2 data
                tier = get_company_tier(self.data_dir, company_name)
                from stage2_company_qualification import sanitize_company_name
                folder_name = sanitize_company_name(company_name)
                scoring = load_json(self.data_dir / "companies" / folder_name / "scoring.json")
                icp_score = scoring.get("icp_qualification", {}).get("weighted_score", 0) if scoring else 0

                # Process Stage 3
                await self._process_company_stage3(company_name, website_url)

        # PRIORITY 2: Process Stage 2 (then Stage 3 will auto-trigger via callback)
        if needs_stage2:
            print(f"\n[Priority 2] Processing {len(needs_stage2)} companies through Stage 2 -> 3...")
            for company in needs_stage2:
                await self._process_company_stage2(company)

        # Wait for any remaining async tasks
        while self._active_tasks:
            await asyncio.sleep(1)

        # SUMMARY
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print(f"Completed at: {datetime.now().isoformat()}")
        print(f"\nStats:")
        print(f"  Companies processed (Stage 2): {self.stats['companies_processed_stage2']}")
        print(f"  Companies processed (Stage 3): {self.stats['companies_processed_stage3']}")
        print(f"  Errors: {len(self.stats['errors'])}")

        if self.stats["errors"]:
            print(f"\nErrors:")
            for error in self.stats["errors"][:5]:
                print(f"  - {error['company']} (Stage {error['stage']}): {error['error']}")
            if len(self.stats["errors"]) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more")

        print(f"\nNext steps:")
        print(f"  1. Review target roles in data/companies/[Company]/target_roles.json")
        print(f"  2. Use LinkedIn Sales Navigator search URLs to find contacts")
        print(f"  3. Run Stage 4 for outreach generation with found contacts")

        # Save final summary
        summary = {
            "pipeline": "tedlar_gtm_orchestrator",
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "rate_limiter": self.rate_limiter.get_usage(),
        }
        save_json(self.data_dir / "pipeline_summary.json", summary)

        return summary

    async def run_from_stage2(self, companies_file: Optional[str] = None):
        """
        Run pipeline starting from Stage 2 (skip event discovery).
        Uses existing discovered_companies.json or specified file.

        PRIORITY ORDER: Later stages first (finish what's started)
        1. First, process companies needing Stage 3 (already have Stage 2 done)
        2. Then, process companies needing Stage 2
        """
        print("\n" + "=" * 70)
        print("TEDLAR GTM PIPELINE - Starting from Stage 2")
        print("=" * 70)
        print(f"Started at: {datetime.now().isoformat()}")

        # Ensure directories exist
        (self.data_dir / "companies").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "contacts").mkdir(parents=True, exist_ok=True)

        # Load companies
        if companies_file:
            companies_path = Path(companies_file)
        else:
            companies_path = self.data_dir / "events" / "discovered_companies.json"

        if not companies_path.exists():
            print(f"Error: Companies file not found: {companies_path}")
            print("Run the full pipeline first or specify a companies file.")
            return

        print(f"Loading companies from: {companies_path}")
        discovery_results = load_json(companies_path)

        # Deduplicate
        unique_companies = deduplicate_companies(discovery_results)
        print(f"  -> {len(unique_companies)} unique companies")

        # Check what work needs to be done at each stage
        needs_stage3 = self._find_companies_needing_stage3(unique_companies)
        needs_stage2 = self._find_companies_needing_stage2(unique_companies)

        print(f"\n[Work Queue] Checking existing progress...")
        print(f"  -> {len(needs_stage3)} companies need Stage 3 (already have Stage 2)")
        print(f"  -> {len(needs_stage2)} companies need Stage 2")

        # PRIORITY 1: Process Stage 3 first (companies closest to completion)
        if needs_stage3:
            print(f"\n[Priority 1] Processing {len(needs_stage3)} companies through Stage 3...")
            for company in needs_stage3:
                company_name = company.get("company_name", "")
                website_url = company.get("website_url", "")
                await self._process_company_stage3(company_name, website_url)

        # PRIORITY 2: Process Stage 2 (then Stage 3 will auto-trigger via callback)
        if needs_stage2:
            print(f"\n[Priority 2] Processing {len(needs_stage2)} companies through Stage 2 -> 3...")
            for company in needs_stage2:
                await self._process_company_stage2(company)

        # Wait for any remaining async tasks
        while self._active_tasks:
            await asyncio.sleep(1)

        print("\n" + "=" * 70)
        print("STAGE 2 & 3 COMPLETE")
        print("=" * 70)
        print(f"Companies processed (Stage 2): {self.stats['companies_processed_stage2']}")
        print(f"Companies processed (Stage 3): {self.stats['companies_processed_stage3']}")

        if self.stats["errors"]:
            print(f"Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:5]:
                print(f"  - {error['company']} (Stage {error['stage']}): {error['error']}")


# CLI ENTRY POINT

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Tedlar GTM Pipeline Orchestrator - Event-driven lead generation"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Base data directory (default: data)",
    )
    parser.add_argument(
        "--tokens-per-min",
        type=int,
        default=30000,
        help="Rate limit in tokens per minute (default: 30000)",
    )
    parser.add_argument(
        "--tiers",
        type=int,
        nargs="+",
        default=[1, 2],
        help="Tiers to process for Stage 3 (default: 1 2)",
    )
    parser.add_argument(
        "--from-stage2",
        action="store_true",
        help="Start from Stage 2 (skip event discovery)",
    )
    parser.add_argument(
        "--companies-file",
        type=str,
        default=None,
        help="Path to companies JSON file (for --from-stage2)",
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        data_dir=args.data_dir,
        tokens_per_min=args.tokens_per_min,
        target_tiers=args.tiers,
    )

    # Run appropriate pipeline
    if args.from_stage2:
        asyncio.run(orchestrator.run_from_stage2(args.companies_file))
    else:
        asyncio.run(orchestrator.run_full_pipeline())


if __name__ == "__main__":
    main()
