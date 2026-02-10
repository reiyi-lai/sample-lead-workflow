import os
import asyncio
import filelock
from typing import Optional
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import MODELS, COMPANY_SCORE_CUTOFF, sanitize_name, ICP_WEIGHTS
from prompts import COMPANY_DISCOVERY_SYSTEM_PROMPT, COMPANY_RESEARCH_AND_SCORING_SYSTEM_PROMPT
from utils.llm import call_claude, extract_json_from_response
from utils.io import load_json, save_json, company_path


def company_exists(companies_dir: str, company_name: str) -> bool:
    return os.path.exists(company_path(companies_dir, company_name, "scoring.json"))


def try_claim_company(companies_dir: str, company_name: str) -> bool:
    """Claim company for research via file lock (for parallel deduplication)."""
    folder = Path(companies_dir) / sanitize_name(company_name)
    lock_file = folder / ".lock"

    try:
        folder.mkdir(parents=True, exist_ok=True)
        lock = filelock.FileLock(str(lock_file), timeout=0)
        lock.acquire()

        # Check if scoring.json exists (another agent finished)
        if (folder / "scoring.json").exists():
            lock.release()
            return False

        # Create a placeholder to signal we're working on it
        (folder / ".in_progress").touch()
        lock.release()
        return True

    except filelock.Timeout:
        return False


def calculate_icp_score(scores: dict) -> dict:
    category_scores = {}
    weighted_score = 0

    for key, weight in ICP_WEIGHTS.items():
        score = scores.get(key, {}).get("score", 5)
        weighted_score += score * weight * 10
        category_scores[key] = {"score": score, "weight": weight}

    return {
        "weighted_score": round(weighted_score, 1),
        "category_scores": category_scores,
    }


class ResearchAgent:
    """Discovers companies at an event and researches each one. Runs in parallel (one per event)."""

    def __init__(
        self,
        event_name: str,
        event_url: str,
        companies_dir: str = "data/companies",
        events_dir: str = "data/events",
        rate_limiter=None,
        on_company_scored=None,  # Callback for Stage 3 trigger
    ):
        self.event_name = event_name
        self.event_url = event_url
        self.companies_dir = companies_dir
        self.events_dir = events_dir
        self.rate_limiter = rate_limiter
        self.on_company_scored = on_company_scored

        self.stats = {"discovered": 0, "skipped": 0, "researched": 0, "qualified": 0, "errors": []}

    async def _acquire_rate_limit(self, estimated_tokens: int = 8000):
        if self.rate_limiter:
            await self.rate_limiter.acquire(estimated_tokens)

    # STEP 2.1: DISCOVER COMPANIES

    async def discover_companies(self) -> list:
        print(f"\n[{self.event_name}] Discovering companies...")

        # Check for cached discovery
        cache_path = Path(self.events_dir) / f"{sanitize_name(self.event_name)}.json"
        if cache_path.exists():
            cached = load_json(str(cache_path))
            if cached and cached.get("companies"):
                companies = cached["companies"]
                print(f"  Loaded {len(companies)} companies from cache")
                self.stats["discovered"] = len(companies)
                return companies

        await self._acquire_rate_limit(estimated_tokens=10000)
        response = call_claude(
            system_prompt=COMPANY_DISCOVERY_SYSTEM_PROMPT,
            model=MODELS["company_discovery"],
            user_message=(
                f"Identify companies at this event:\n\n"
                f"Event: {self.event_name}\nURL: {self.event_url}\n\n"
                f"Return JSON only."
            ),
            max_tokens=16384,
            enable_web_search=True,
        )

        result = extract_json_from_response(response)

        if "error" in result:
            print(f"  Discovery failed: {result['error']}")
            self.stats["errors"].append({"stage": "discovery", "error": result["error"]})
            return []

        companies = result.get("companies", [])
        print(f"  Discovered {len(companies)} companies")
        self.stats["discovered"] = len(companies)

        # Cache the discovery result
        save_json(str(cache_path), {
            "event_name": self.event_name,
            "event_url": self.event_url,
            "companies": companies,
            "total_confirmed": result.get("total_confirmed", 0),
            "total_likely": result.get("total_likely", 0),
            "sources_searched": result.get("sources_searched", []),
            "notes": result.get("notes", ""),
            "success": True,
        })

        return companies

    # STEP 2.2: RESEARCH AND SCORE COMPANY

    async def research_company(self, company_name: str, website_url: str) -> Optional[dict]:
        if company_exists(self.companies_dir, company_name):
            print(f"    [{company_name}] Already researched, skipping")
            self.stats["skipped"] += 1
            return None

        if not try_claim_company(self.companies_dir, company_name):
            print(f"    [{company_name}] Claimed by another agent, skipping")
            self.stats["skipped"] += 1
            return None

        folder = Path(self.companies_dir) / sanitize_name(company_name)
        try:
            print(f"    [{company_name}] Researching...")
            await self._acquire_rate_limit(estimated_tokens=10000)
            response = call_claude(
                system_prompt=COMPANY_RESEARCH_AND_SCORING_SYSTEM_PROMPT,
                model=MODELS["company_research"],
                user_message=f"Research and score this company for ICP qualification:\n\nCompany: {company_name}\nWebsite: {website_url}",
                max_tokens=8192,
                enable_web_search=True,
            )

            result = extract_json_from_response(response)

            if "error" in result:
                print(f"    [{company_name}] Research failed: {result['error']}")
                self.stats["errors"].append({"company": company_name, "error": result["error"]})
                return None

            # STEP 2.3: CALCULATE WEIGHTED ICP SCORE from scores in the response
            scores = result.get("scores", {})
            icp_result = calculate_icp_score(scores)

            scoring_data = {
                "company_name": result.get("company_name", company_name),
                "website_url": result.get("website_url", website_url),
                "source_event": self.event_name,
                "scores": scores,
                "qualification_summary": result.get("qualification_summary", ""),
                "icp_qualification": icp_result,
            }

            save_json(
                company_path(self.companies_dir, company_name, "scoring.json"),
                scoring_data
            )

            self.stats["researched"] += 1
            print(f"    [{company_name}] Score: {icp_result['weighted_score']}")

            # Check if qualified and trigger callback
            if icp_result["weighted_score"] >= COMPANY_SCORE_CUTOFF:
                self.stats["qualified"] += 1
                if self.on_company_scored:
                    await self.on_company_scored(company_name, website_url, icp_result["weighted_score"])

            return scoring_data

        finally:
            in_progress = folder / ".in_progress"
            if in_progress.exists():
                in_progress.unlink()

    async def run(self) -> dict:
        """Main loop: discover companies, then research each one."""
        print(f"\n[RESEARCH AGENT: {self.event_name}]")

        companies = await self.discover_companies()
        if not companies:
            print(f"[{self.event_name}] No companies found")
            return self.stats

        print(f"\n[{self.event_name}] Researching {len(companies)} companies...")
        for i, company in enumerate(companies):
            company_name = company.get("company_name", "")
            if not company_name:
                continue
            print(f"\n  [{i+1}/{len(companies)}] {company_name}")
            await self.research_company(company_name, company.get("website_url", ""))

        print(f"\n[{self.event_name}] COMPLETE - Discovered: {self.stats['discovered']}, "
              f"Researched: {self.stats['researched']}, Qualified: {self.stats['qualified']}, "
              f"Skipped: {self.stats['skipped']}, Errors: {len(self.stats['errors'])}")
        return self.stats

async def run_research_agents_parallel(
    events: list, companies_dir: str = "data/companies", events_dir: str = "data/events",
    rate_limiter=None, on_company_scored=None, max_concurrent: int = 3,
) -> dict:
    """Run multiple Research Agents in parallel (one per event)."""
    print(f"\n[PARALLEL RESEARCH AGENTS] Events: {len(events)} | Max concurrent: {max_concurrent}")

    semaphore = asyncio.Semaphore(max_concurrent)
    all_stats = {
        "events_processed": 0,
        "total_discovered": 0,
        "total_researched": 0,
        "total_qualified": 0,
        "total_skipped": 0,
        "total_errors": 0,
    }

    async def run_with_semaphore(event: dict):
        async with semaphore:
            agent = ResearchAgent(
                event_name=event.get("event_name", ""),
                event_url=event.get("event_url", ""),
                companies_dir=companies_dir,
                events_dir=events_dir,
                rate_limiter=rate_limiter,
                on_company_scored=on_company_scored,
            )
            return await agent.run()

    # Run all agents with semaphore limiting concurrency
    tasks = [run_with_semaphore(event) for event in events]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate stats
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Agent {i} failed with exception: {result}")
            all_stats["total_errors"] += 1
        elif isinstance(result, dict):
            all_stats["events_processed"] += 1
            all_stats["total_discovered"] += result.get("discovered", 0)
            all_stats["total_researched"] += result.get("researched", 0)
            all_stats["total_qualified"] += result.get("qualified", 0)
            all_stats["total_skipped"] += result.get("skipped", 0)
            all_stats["total_errors"] += len(result.get("errors", []))

    print(f"\n[ALL AGENTS COMPLETE] Events: {all_stats['events_processed']}, "
          f"Discovered: {all_stats['total_discovered']}, Researched: {all_stats['total_researched']}, "
          f"Qualified: {all_stats['total_qualified']}, Skipped: {all_stats['total_skipped']}, "
          f"Errors: {all_stats['total_errors']}")
    return all_stats


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python research_agent.py <event_name> [event_url]")
        sys.exit(1)
    asyncio.run(ResearchAgent(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "").run())
