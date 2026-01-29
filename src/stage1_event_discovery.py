# stage1_event_discovery.py
# Stage 1: Event Discovery Pipeline
#
# Flow:
# 1.1 Event Discovery (Claude WebSearch) - Find relevant trade shows
# 1.2 Event Relevance Scoring (LLM) - Score and filter to Tier 1 & 2
# 1.3 Company Discovery (Claude WebSearch) - Find exhibitors + likely attendees

import os
import json
import re
import time
from datetime import datetime
from typing import List, Optional

# Delay between API-heavy steps to avoid rate limits (30k tokens/min)
STEP_DELAY_SECONDS = 65  # Wait just over 1 minute between steps

# Add src to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import MODELS, EVENT_SCORE_CUTOFF
from prompts import (
    EVENT_DISCOVERY_SYSTEM_PROMPT,
    EVENT_SCORING_SYSTEM_PROMPT,
    COMPANY_DISCOVERY_SYSTEM_PROMPT,
)
from utils.llm import call_claude_with_web_search, call_claude_json, extract_json_from_response


# HELPERS

def sanitize_event_name(name: str) -> str:
    """Convert event name to safe filename."""
    # Remove special characters, keep alphanumeric, spaces, and hyphens
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    return name.strip('_')


def get_event_companies_file(output_dir: str, event_name: str) -> str:
    """Get the file path for an event's companies."""
    companies_dir = os.path.join(output_dir, "companies")
    os.makedirs(companies_dir, exist_ok=True)
    safe_name = sanitize_event_name(event_name)
    return os.path.join(companies_dir, f"{safe_name}.json")


def load_existing_company_results(output_dir: str, event_name: str) -> Optional[dict]:
    """Load existing company discovery results for an event."""
    filepath = get_event_companies_file(output_dir, event_name)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return None


def save_company_results(output_dir: str, event_name: str, result: dict):
    """Save company discovery results for an event."""
    filepath = get_event_companies_file(output_dir, event_name)
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)


# STEP 1.1: EVENT DISCOVERY

def discover_events() -> List[dict]:
    """
    Step 1.1: Discover trade show events using Claude WebSearch.

    Returns:
        List of discovered event dictionaries
    """
    print("\n" + "=" * 60)
    print("STEP 1.1: EVENT DISCOVERY")
    print("=" * 60)

    user_message = "Please discover relevant trade show events for 2025-2026 and return as a JSON array."

    print("\nDiscovering events...")

    # Call Claude with web search (using Sonnet for web search capability)
    response = call_claude_with_web_search(
        system_prompt=EVENT_DISCOVERY_SYSTEM_PROMPT,
        user_message=user_message,
        model=MODELS["event_discovery"],
    )

    # Parse the response
    events = extract_json_from_response(response)

    if isinstance(events, dict) and "error" in events:
        print(f"\nWarning: Failed to parse events JSON: {events.get('error')}")
        print(f"Raw response preview: {response[:500]}...")
        return []

    if isinstance(events, list):
        print(f"\nDiscovered {len(events)} events")
        return events
    else:
        print(f"\nUnexpected response format: {type(events)}")
        return []


# STEP 1.2: EVENT RELEVANCE SCORING

def score_events(events: List[dict]) -> dict:
    """
    Step 1.2: Score and filter events based on relevance to ICP.

    Args:
        events: List of discovered events

    Returns:
        Dict with scored_events and summary
    """
    print("\n" + "=" * 60)
    print("STEP 1.2: EVENT RELEVANCE SCORING")
    print("=" * 60)

    if not events:
        print("No events to score")
        return {"scored_events": [], "summary": {"total_events_scored": 0}}

    # Build user message with events to score
    events_json = json.dumps(events, indent=2)
    user_message = f"""
Please score the following {len(events)} events based on their relevance to Tedlar's ICP:

{events_json}

Return the scored events in the format specified in your instructions.
"""

    print(f"\nScoring {len(events)} events (using Haiku for efficiency)...")

    # Call Claude for scoring (using Haiku - simpler task)
    # Use higher max_tokens since we're scoring many events with reasoning
    response = call_claude_json(
        system_prompt=EVENT_SCORING_SYSTEM_PROMPT,
        user_message=user_message,
        model=MODELS["event_scoring"],
        max_tokens=8192,
    )

    if "error" in response:
        print(f"\nWarning: Failed to parse scoring response: {response.get('error')}")
        return {"scored_events": [], "summary": {"total_events_scored": 0}}

    # Print summary
    scored_events = response.get("scored_events", [])
    summary = response.get("summary", {})
    print(f"\nScoring Results:")
    print(f"  Total events scored: {summary.get('total_events_scored', len(scored_events))}")

    return response


# STEP 1.3: COMPANY DISCOVERY

def discover_companies(events: List[dict], output_dir: str) -> List[dict]:
    """
    Step 1.3: Discover companies for each qualified event using Claude WebSearch.

    This combines exhibitor identification and extraction into a single step.
    Claude searches for exhibitor lists, past exhibitors, and companies likely to attend.

    Each event's results are saved to a separate file immediately after processing.
    Already-processed events are skipped (resume-safe).

    Args:
        events: List of qualified events (above score cutoff)
        output_dir: Directory to save company files (creates companies/ subdirectory)

    Returns:
        List of discovery results with company data
    """
    print("\n" + "=" * 60)
    print("STEP 1.3: COMPANY DISCOVERY")
    print("=" * 60)

    if not events:
        print("No qualified events to research")
        return []

    discovery_results = []
    skipped_count = 0
    processed_count = 0

    for i, event in enumerate(events):
        event_name = event.get("event_name", "Unknown")
        event_url = event.get("event_url", "")
        score = event.get("overall_score", "?")

        print(f"\n[{i+1}/{len(events)}] [Score: {score}] {event_name}")

        # Check if already processed
        existing_result = load_existing_company_results(output_dir, event_name)
        if existing_result:
            print(f"  -> Already processed, loading from file...")
            companies = existing_result.get("companies", [])
            print(f"  -> {len(companies)} companies (cached)")
            discovery_results.append(existing_result)
            skipped_count += 1
            continue

        print(f"  Event URL: {event_url}")

        # Build user message for this specific event
        user_message = f"""
Based on the above instructions, identify companies that exhibit at or are very likely to attend the following event:

Event Name: {event_name}
Event URL: {event_url}

Return the results in the JSON format only, as specified in my instructions.
"""

        print(f"  Searching for exhibitors and likely attendees...")

        # Call Claude with web search (16k tokens to handle long company lists)
        response = call_claude_with_web_search(
            system_prompt=COMPANY_DISCOVERY_SYSTEM_PROMPT,
            user_message=user_message,
            model=MODELS["company_discovery"],
            max_tokens=16384,
        )

        # Parse the response
        result = extract_json_from_response(response)

        if isinstance(result, dict) and "error" in result:
            print(f"  -> Discovery failed: {result.get('error')}")
            print(f"  -> Raw response preview:\n{response[:2000]}...")
            result = {
                "event_name": event_name,
                "event_url": event_url,
                "success": False,
                "error": result.get("error"),
                "raw_response": response,
            }
        else:
            companies = result.get("companies", [])
            total_confirmed = result.get("total_confirmed", 0)
            total_likely = result.get("total_likely", 0)
            print(f"  -> Found {len(companies)} companies ({total_confirmed} confirmed, {total_likely} likely)")

            result["success"] = True

        # Save immediately after processing
        save_company_results(output_dir, event_name, result)
        print(f"  -> Saved to: companies/{sanitize_event_name(event_name)}.json")
        discovery_results.append(result)
        processed_count += 1

        # Delay between events to avoid rate limits (only if more events to process)
        remaining_to_process = sum(
            1 for e in events[i+1:]
            if not load_existing_company_results(output_dir, e.get("event_name", ""))
        )
        if remaining_to_process > 0:
            print(f"\n  Waiting {STEP_DELAY_SECONDS}s before next event...")
            time.sleep(STEP_DELAY_SECONDS)

    # Summary
    total_companies = sum(
        len(r.get("companies", []))
        for r in discovery_results
        if r.get("success")
    )
    successful_events = sum(1 for r in discovery_results if r.get("success"))
    print(f"\nDiscovery Summary:")
    print(f"  {total_companies} total companies from {successful_events}/{len(events)} events")
    print(f"  {skipped_count} events loaded from cache, {processed_count} newly processed")

    return discovery_results


# MAIN PIPELINE

def run_stage1_pipeline(
    output_dir: str = "data/events",
) -> dict:
    """
    Run the complete Stage 1 Event Discovery Pipeline.

    Args:
        output_dir: Directory to save output files

    Returns:
        Dict with all pipeline results
    """
    print("\n" + "=" * 60)
    print("STAGE 1: EVENT DISCOVERY PIPELINE")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    events_file = os.path.join(output_dir, "discovered_events.json")
    scored_file = os.path.join(output_dir, "scored_events.json")

    # Step 1.1: Discover events (or load existing)
    if os.path.exists(events_file):
        print(f"\n[Step 1.1] Loading existing events from: {events_file}")
        with open(events_file, "r") as f:
            events = json.load(f)
        print(f"  -> Loaded {len(events)} events (cached)")
    else:
        events = discover_events()
        # Save discovered events
        with open(events_file, "w") as f:
            json.dump(events, f, indent=2)
        print(f"\nSaved discovered events to: {events_file}")
        # Delay to avoid rate limits (30k tokens/min)
        print(f"\n Waiting {STEP_DELAY_SECONDS}s to avoid rate limit...")
        time.sleep(STEP_DELAY_SECONDS)

    # Step 1.2: Score events (or load existing)
    scored = None
    if os.path.exists(scored_file):
        print(f"\n[Step 1.2] Checking existing scored events: {scored_file}")
        with open(scored_file, "r") as f:
            scored = json.load(f)
        scored_count = len(scored.get("scored_events", []))
        if scored_count == 0 and len(events) > 0:
            print(f"  -> Cached file appears to be from failed parse, re-scoring...")
            scored = None
        else:
            print(f"  -> Loaded {scored_count} scored events (cached)")

    if scored is None:
        scored = score_events(events)
        # Save scored events
        with open(scored_file, "w") as f:
            json.dump(scored, f, indent=2)
        print(f"Saved scored events to: {scored_file}")

    # Filter to events above score cutoff
    all_scored_events = scored.get("scored_events", [])
    qualified_events = [
        e for e in all_scored_events
        if (e.get("overall_score") or 0) >= EVENT_SCORE_CUTOFF
    ]

    print(f"\nFiltered to {len(qualified_events)} events with score >= {EVENT_SCORE_CUTOFF} (from {len(all_scored_events)} scored)")

    # Delay before company discovery (which uses web search)
    if qualified_events:
        print(f"\n Waiting {STEP_DELAY_SECONDS}s to avoid rate limit...")
        time.sleep(STEP_DELAY_SECONDS)

    # Step 1.3: Discover companies for qualified events
    # Each event is saved to its own file in companies/ subdirectory
    discovery_results = discover_companies(qualified_events, output_dir)

    # Compile final results (individual company files already saved in discover_companies)
    total_companies = sum(
        len(r.get("companies", []))
        for r in discovery_results
        if r.get("success")
    )

    results = {
        "pipeline": "stage1_event_discovery",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "events_discovered": len(events),
            "events_qualified": len(qualified_events),
            "events_researched_successfully": sum(1 for r in discovery_results if r.get("success")),
            "total_companies_discovered": total_companies,
        },
    }

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Events discovered: {results['summary']['events_discovered']}")
    print(f"Events qualified (score >= {EVENT_SCORE_CUTOFF}): {results['summary']['events_qualified']}")
    print(f"Events researched successfully: {results['summary']['events_researched_successfully']}")
    print(f"Companies discovered: {results['summary']['total_companies_discovered']}")
    print(f"\nOutputs:")
    print(f"  {output_dir}/discovered_events.json")
    print(f"  {output_dir}/scored_events.json")
    print(f"  {output_dir}/companies/*.json (one per event)")

    return results


# CLI ENTRY POINT

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Stage 1: Event Discovery Pipeline")
    parser.add_argument(
        "--output-dir",
        default="data/events",
        help="Directory to save output files (default: data/events)",
    )

    args = parser.parse_args()

    # Run pipeline
    results = run_stage1_pipeline(
        output_dir=args.output_dir,
    )
