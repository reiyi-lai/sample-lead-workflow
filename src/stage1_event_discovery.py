# Stage 1: Event Discovery
# 1.1 Discover trade shows (web search)
# 1.2 Score and filter events
# 1.3 Discover companies at qualified events (web search)

import os
import json
from datetime import datetime
from typing import List

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import MODELS, EVENT_SCORE_CUTOFF, sanitize_name
from prompts import EVENT_DISCOVERY_SYSTEM_PROMPT, EVENT_SCORING_SYSTEM_PROMPT, COMPANY_DISCOVERY_SYSTEM_PROMPT
from utils.llm import call_claude, extract_json_from_response
from utils.io import load_json, save_json


def _event_companies_path(output_dir: str, event_name: str) -> str:
    """Path to a per-event companies JSON file."""
    companies_dir = os.path.join(output_dir, "companies")
    os.makedirs(companies_dir, exist_ok=True)
    return os.path.join(companies_dir, f"{sanitize_name(event_name)}.json")


def discover_events() -> List[dict]:
    """Step 1.1: Discover trade show events via Claude web search."""
    print("\n[Step 1.1] Event Discovery")
    print("  Searching for relevant trade shows via web search...")

    response = call_claude(
        system_prompt=EVENT_DISCOVERY_SYSTEM_PROMPT,
        model=MODELS["event_discovery"],
        enable_web_search=True,
    )
    events = extract_json_from_response(response)

    if isinstance(events, dict) and "error" in events:
        print(f"  Error: {events['error']}")
        return []

    if not isinstance(events, list):
        print(f"  Unexpected response format: {type(events)}")
        return []

    print(f"  Step 1.1 complete: {len(events)} events discovered")
    return events


def score_events(events: List[dict]) -> dict:
    """Step 1.2: Score events for ICP relevance."""
    print(f"\n[Step 1.2] Event Scoring")
    print(f"  Scoring {len(events)} events for ICP relevance...")

    if not events:
        return {"scored_events": [], "summary": {"total_events_scored": 0}}

    raw = call_claude(
        system_prompt=EVENT_SCORING_SYSTEM_PROMPT,
        model=MODELS["event_scoring"],
        user_message=f"Score these {len(events)} events:\n\n{json.dumps(events, indent=2)}",
        max_tokens=8192,
    )
    result = extract_json_from_response(raw)

    if "error" in result:
        print(f"  Error: {result['error']}")
        return {"scored_events": [], "summary": {"total_events_scored": 0}}

    scored = result.get("scored_events", [])
    print(f"  Step 1.2 complete: {len(scored)} events scored")
    return result


def discover_companies(events: List[dict], output_dir: str) -> List[dict]:
    """Step 1.3: Discover companies for each qualified event. Resume-safe."""
    print(f"\n[Step 1.3] Company Discovery")
    print(f"  Discovering companies for {len(events)} qualified events...")

    if not events:
        return []

    results = []

    for i, event in enumerate(events):
        event_name = event.get("event_name", "Unknown")
        event_url = event.get("event_url", "")
        score = event.get("overall_score", "?")
        filepath = _event_companies_path(output_dir, event_name)

        print(f"\n  [{i+1}/{len(events)}] {event_name} (score: {score})")

        # Load existing result if available
        existing = load_json(filepath)
        if existing:
            print(f"    Companies found in existing data ({len(existing.get('companies', []))})")
            results.append(existing)
            continue

        print(f"    Searching for companies via web search...")
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
            result = {"event_name": event_name, "event_url": event_url, "success": False, "error": result["error"]}
        else:
            companies = result.get("companies", [])
            print(f"    -> {len(companies)} companies found")
            result["success"] = True

        save_json(filepath, result)
        results.append(result)

    total = sum(len(r.get("companies", [])) for r in results if r.get("success"))
    print(f"\n  Step 1.3 complete: {total} companies discovered across {len(results)} events")
    return results


def run_stage1_pipeline(output_dir: str = "data/events") -> dict:
    """Run the complete Stage 1 pipeline."""
    print("")
    print("STAGE 1: EVENT DISCOVERY")
    print("")

    os.makedirs(output_dir, exist_ok=True)
    events_file = os.path.join(output_dir, "discovered_events.json")
    scored_file = os.path.join(output_dir, "scored_events.json")

    # 1.1 Discover events
    events = load_json(events_file)
    if events:
        print(f"\n[Step 1.1] Event Discovery")
        print(f"  {len(events)} events found in existing data")
    else:
        events = discover_events()
        save_json(events_file, events)

    # 1.2 Score events
    scored = load_json(scored_file)
    if scored and (scored.get("scored_events") or not events):
        print(f"\n[Step 1.2] Event Scoring")
        print(f"  {len(scored.get('scored_events', []))} scored events found in existing data")
    else:
        scored = score_events(events)
        save_json(scored_file, scored)

    # Filter by cutoff
    all_scored = scored.get("scored_events", [])
    qualified = [e for e in all_scored if (e.get("overall_score") or 0) >= EVENT_SCORE_CUTOFF]
    print(f"\n  {len(qualified)}/{len(all_scored)} events above score cutoff ({EVENT_SCORE_CUTOFF})")

    # 1.3 Discover companies
    discovery_results = discover_companies(qualified, output_dir)

    total_companies = sum(len(r.get("companies", [])) for r in discovery_results if r.get("success"))
    print(f"\n[Stage 1 Complete] {len(events)} events -> {len(qualified)} qualified -> {total_companies} companies")

    return {
        "pipeline": "stage1_event_discovery",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "events_discovered": len(events),
            "events_qualified": len(qualified),
            "total_companies_discovered": total_companies,
        },
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 1: Event Discovery")
    parser.add_argument("--output-dir", default="data/events")
    args = parser.parse_args()
    run_stage1_pipeline(output_dir=args.output_dir)
