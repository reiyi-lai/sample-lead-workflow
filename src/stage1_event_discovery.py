# Stage 1: Event Discovery
# 1.1 Discover trade shows (web search OR sheet import)
# 1.2 Enrich events with missing details (for sheet imports)
# 1.3 Score and filter events
# 1.4 Discover companies at qualified events (web search)

import os
import json
import shutil
from datetime import datetime
from typing import List, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import MODELS, EVENT_SCORE_CUTOFF, sanitize_name
from prompts import EVENT_SCORING_SYSTEM_PROMPT, COMPANY_DISCOVERY_SYSTEM_PROMPT
from utils.llm import call_claude, extract_json_from_response
from utils.io import load_json, save_json

# Import the new event sources
from event_sources import (
    discover_events_web,
    import_events_from_sheet,
    import_events_from_inline_data,
    enrich_events_batch
)


def _event_companies_path(output_dir: str, event_name: str) -> str:
    """Path to a per-event companies JSON file (saved directly in events/)."""
    return os.path.join(output_dir, f"{sanitize_name(event_name)}.json")


def discover_events(source: str = "web", file_path: Optional[str] = None, events_text: Optional[str] = None,
                   output_dir: str = "data/events", master_discovered_file: str = None, skip_duplicates: bool = True) -> List[dict]:
    """Step 1.1: Discover trade show events via web search or sheet import."""
    print("\n[Step 1.1] Event Discovery")

    if source == "web":
        print("  Using web discovery mode...")
        events = discover_events_web()
    elif source == "sheet":
        if file_path:
            print(f"  Using sheet import mode from file: {file_path}")
            events = import_events_from_sheet(
                file_path=file_path,
                master_discovered_file=master_discovered_file,
                skip_duplicates=skip_duplicates
            )
        elif events_text:
            print("  Using sheet import mode from provided text")
            events = import_events_from_sheet(
                events_text=events_text,
                master_discovered_file=master_discovered_file,
                skip_duplicates=skip_duplicates
            )
        else:
            print("  Using inline sheet data")
            events = import_events_from_inline_data()
    else:
        print(f"  Error: Unknown source '{source}'. Use 'web' or 'sheet'")
        return []

    print(f"  Step 1.1 complete: {len(events)} events from {source} source")
    return events


def score_events_batch_api(events_batch: List[dict]) -> List[dict]:
    """
    Score a batch of events with a single API call.

    Args:
        events_batch: List of event dictionaries to score (up to 12 recommended)

    Returns:
        List of scored event dictionaries
    """
    if not events_batch:
        return []

    print(f"  Batch scoring {len(events_batch)} events...")

    raw = call_claude(
        system_prompt=EVENT_SCORING_SYSTEM_PROMPT,
        model=MODELS["event_scoring"],
        user_message=f"Score these {len(events_batch)} events:\n\n{json.dumps(events_batch, indent=2)}",
        max_tokens=16384,  # Increased for batch processing
    )

    result = extract_json_from_response(raw)

    if isinstance(result, dict) and "error" in result:
        print(f"    -> Batch scoring error: {result['error']}")
        # Return original events with error info
        return [{**event, "scoring_error": result["error"]} for event in events_batch]

    # Handle different response formats
    if isinstance(result, list):
        # LLM returned array directly
        scored_events = result
    elif isinstance(result, dict) and "scored_events" in result:
        # LLM returned expected {scored_events: [], summary: {}} structure
        scored_events = result.get("scored_events", [])
    else:
        print(f"    -> Invalid batch response format: {type(result)}")
        return [{**event, "scoring_error": "Invalid response format"} for event in events_batch]

    # Ensure we have the right number of results
    if len(scored_events) != len(events_batch):
        print(f"    -> Mismatch: expected {len(events_batch)} results, got {len(scored_events)}")
        # Pad or truncate as needed
        while len(scored_events) < len(events_batch):
            scored_events.append({
                **events_batch[len(scored_events)],
                "scoring_error": "Missing from batch response"
            })
        scored_events = scored_events[:len(events_batch)]

    successful = sum(1 for e in scored_events if e.get("overall_score") is not None)
    print(f"    -> {successful}/{len(scored_events)} events successfully scored")

    return scored_events


def score_events(events: List[dict], batch_size: int = 12) -> dict:
    """Step 1.2: Score events for ICP relevance using batched API calls."""
    print(f"  Scoring {len(events)} events for ICP relevance in batches of {batch_size}...")

    if not events:
        return {"scored_events": [], "summary": {"total_events_scored": 0}}

    all_scored_events = []

    # Process events in batches
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(events) + batch_size - 1) // batch_size

        print(f"  [Batch {batch_num}/{total_batches}] ", end="")
        batch_results = score_events_batch_api(batch)
        all_scored_events.extend(batch_results)

    successful = sum(1 for e in all_scored_events if e.get("overall_score") is not None)
    print(f"  Scoring complete: {successful}/{len(events)} events successfully scored")

    return {
        "scored_events": all_scored_events,
        "summary": {"total_events_scored": len(all_scored_events)}
    }


def normalize_event_url(url: str) -> str:
    """Normalize URL for duplicate detection."""
    if not url:
        return ""
    normalized = url.lower().strip().rstrip("/")
    normalized = normalized.replace("https://", "").replace("http://", "")
    normalized = normalized.replace("www.", "")
    return normalized


def normalize_event_name(name: str) -> str:
    """Normalize event name for similarity comparison."""
    if not name:
        return ""

    # Convert to lowercase and remove extra whitespace
    normalized = name.lower().strip()

    # Remove common variations
    normalized = normalized.replace("'", "").replace("'", "")  # Remove different apostrophes
    normalized = normalized.replace("&", "and")  # & -> and
    normalized = normalized.replace("-", " ").replace("_", " ")  # Normalize separators

    # Remove common suffixes/prefixes that vary
    import re
    normalized = re.sub(r'\b(the|a|an)\b', '', normalized)  # Remove articles
    normalized = re.sub(r'\b\d{4}\b', 'YEAR', normalized)  # Normalize years to placeholder
    normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace

    return normalized


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL for domain-based matching."""
    if not url:
        return ""

    normalized = normalize_event_url(url)
    # Get just the domain part (before first slash)
    domain = normalized.split('/')[0] if '/' in normalized else normalized
    return domain


def events_are_similar(event1: dict, event2: dict) -> bool:
    """
    Check if two events are likely the same event using multiple criteria.

    Args:
        event1: First event to compare
        event2: Second event to compare

    Returns:
        True if events are likely duplicates
    """
    name1 = event1.get("event_name", "")
    name2 = event2.get("event_name", "")
    url1 = event1.get("event_url", "")
    url2 = event2.get("event_url", "")

    if not name1 or not name2:
        return False

    # Check 1: Exact URL match (after normalization)
    if url1 and url2:
        norm_url1 = normalize_event_url(url1)
        norm_url2 = normalize_event_url(url2)
        if norm_url1 == norm_url2:
            return True

        # Check 2: Same domain + similar names
        domain1 = get_domain_from_url(url1)
        domain2 = get_domain_from_url(url2)
        if domain1 and domain2 and domain1 == domain2:
            norm_name1 = normalize_event_name(name1)
            norm_name2 = normalize_event_name(name2)
            if norm_name1 == norm_name2:
                return True

    # Check 3: Very similar event names (exact match after normalization)
    norm_name1 = normalize_event_name(name1)
    norm_name2 = normalize_event_name(name2)
    if norm_name1 and norm_name2 and norm_name1 == norm_name2:
        return True

    # Check 4: Event names with minor differences (substring match for long names)
    if len(name1) > 20 and len(name2) > 20:  # Only for longer event names
        # Check if one name contains most of the other (after normalization)
        shorter = norm_name1 if len(norm_name1) <= len(norm_name2) else norm_name2
        longer = norm_name2 if len(norm_name1) <= len(norm_name2) else norm_name1

        if len(shorter) > 10 and shorter in longer:
            return True

    return False


def check_events_against_master_scoring(events: List[dict], master_scored_file: str) -> tuple[List[dict], List[dict]]:
    """
    Check events against master scored_events.json to avoid re-scoring.

    Args:
        events: List of events to check
        master_scored_file: Path to master scored_events.json

    Returns:
        Tuple of (events_to_score, already_scored_events)
    """
    if not os.path.exists(master_scored_file):
        print(f"  No master scoring file found - will score all {len(events)} events")
        return events, []

    master_data = load_json(master_scored_file)
    if not master_data:
        print(f"  Empty master scoring file - will score all {len(events)} events")
        return events, []

    # Get existing scored event URLs
    existing_urls = set()
    scored_events = master_data.get("scored_events", [])
    for event in scored_events:
        url = event.get("event_url", "")
        if url:
            existing_urls.add(normalize_event_url(url))

    print(f"  Checking {len(events)} events against {len(scored_events)} already scored events...")

    events_to_score = []
    already_scored = []

    for event in events:
        event_url = event.get("event_url", "")
        normalized_url = normalize_event_url(event_url)

        if normalized_url and normalized_url in existing_urls:
            print(f"    Already scored: {event.get('event_name', 'Unknown')} -> {event_url}")
            already_scored.append(event)
        else:
            events_to_score.append(event)

    print(f"  Scoring check complete: {len(events_to_score)} to score, {len(already_scored)} already scored")
    return events_to_score, already_scored


def check_events_against_master_discovered(events: List[dict], master_discovered_file: str) -> tuple[List[dict], List[dict]]:
    """
    Check events against master discovered_events.json using improved similarity matching.

    Args:
        events: List of events to check
        master_discovered_file: Path to master discovered_events.json

    Returns:
        Tuple of (events_to_process, already_discovered_events)
    """
    if not os.path.exists(master_discovered_file):
        print(f"  No master discovered events file found - will process all {len(events)} events")
        return events, []

    master_data = load_json(master_discovered_file)
    if not master_data:
        print(f"  Empty master discovered events file - will process all {len(events)} events")
        return events, []

    print(f"  Checking {len(events)} events against {len(master_data)} already discovered events...")

    events_to_process = []
    already_discovered = []

    for event in events:
        is_duplicate = False

        # Check against each existing event using similarity matching
        for existing_event in master_data:
            if events_are_similar(event, existing_event):
                print(f"    Already discovered: {event.get('event_name', 'Unknown')} -> {event.get('event_url', '')}")
                print(f"      Similar to: {existing_event.get('event_name', 'Unknown')} -> {existing_event.get('event_url', '')}")
                already_discovered.append(event)
                is_duplicate = True
                break

        if not is_duplicate:
            events_to_process.append(event)

    print(f"  Discovery check complete: {len(events_to_process)} to process, {len(already_discovered)} already discovered")
    return events_to_process, already_discovered


def update_master_discovered_events(new_events: List[dict], master_discovered_file: str) -> None:
    """
    Update master discovered_events.json with new events.

    Args:
        new_events: List of new events to add to master
        master_discovered_file: Path to master discovered_events.json
    """
    if not new_events:
        return

    # Load existing master data
    master_data = load_json(master_discovered_file) or []

    # Build set of existing URLs for fast lookup (safety check)
    existing_urls = set()
    for event in master_data:
        url = event.get("event_url", "")
        if url:
            existing_urls.add(normalize_event_url(url))

    # Add new events to master list (should already be deduplicated, but safety check)
    added_count = 0
    for event in new_events:
        event_url = event.get("event_url", "")
        normalized_url = normalize_event_url(event_url)

        if normalized_url and normalized_url not in existing_urls:
            # Add metadata for master
            master_event = {
                **event,
                "added_to_master": datetime.now().isoformat(),
                "master_id": len(master_data) + added_count + 1
            }
            master_data.append(master_event)
            existing_urls.add(normalized_url)
            added_count += 1

    # Save updated master file
    save_json(master_discovered_file, master_data)
    print(f"  Master discovered events updated: {added_count} new events added (total: {len(master_data)})")

    # Sync to dashboard
    sync_to_dashboard(master_discovered_file)


def sync_to_dashboard(src_file: str, dashboard_dir: str = "dashboard/data/events") -> None:
    """
    Copy master files to dashboard data directory for frontend access.

    Args:
        src_file: Source file path (e.g., "data/events/discovered_events.json")
        dashboard_dir: Dashboard data directory path
    """
    if not os.path.exists(src_file):
        print(f"  Warning: Source file {src_file} not found - skipping sync")
        return

    # Create dashboard data directory if it doesn't exist
    os.makedirs(dashboard_dir, exist_ok=True)

    # Get filename and create destination path
    filename = os.path.basename(src_file)
    dst_file = os.path.join(dashboard_dir, filename)

    try:
        shutil.copy2(src_file, dst_file)
        print(f"  Synced {filename} to dashboard")
    except Exception as e:
        print(f"  Warning: Failed to sync {filename} to dashboard: {e}")


def sync_all_master_files_to_dashboard() -> None:
    """Sync all master files to dashboard data directory."""
    print(f"\n[Dashboard Sync] Copying master files to dashboard/data/events/")

    master_files = [
        "data/events/discovered_events.json",
        "data/events/scored_events.json"
    ]

    for file_path in master_files:
        sync_to_dashboard(file_path)


def update_master_scored_events(new_scored_data: dict, master_scored_file: str) -> None:
    """
    Update master scored_events.json with newly scored events.

    Args:
        new_scored_data: The scoring result from score_events()
        master_scored_file: Path to master scored_events.json
    """
    new_events = new_scored_data.get("scored_events", [])
    if not new_events:
        return

    # Load existing master data
    master_data = load_json(master_scored_file) or {"scored_events": [], "summary": {"total_events_scored": 0}}

    # Add new events to master list
    existing_events = master_data.get("scored_events", [])
    all_events = existing_events + new_events

    # Update master data
    master_data["scored_events"] = all_events
    master_data["summary"]["total_events_scored"] = len(all_events)
    master_data["last_updated"] = datetime.now().isoformat()

    # Save updated master file
    save_json(master_scored_file, master_data)
    print(f"  Master scoring file updated: {len(new_events)} new events added (total: {len(all_events)})")

    # Sync to dashboard
    sync_to_dashboard(master_scored_file)


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


def enrich_events(events: List[dict]) -> List[dict]:
    """Step 1.2: Enrich events with missing details (for sheet imports)."""
    if not events:
        return events

    # Check if any events need enrichment
    needs_enrichment = [e for e in events if e.get("needs_enrichment", False) or e.get("source") == "sheet_import"]

    if not needs_enrichment:
        print(f"\n[Step 1.2] Event Enrichment: No events need enrichment")
        return events

    print(f"\n[Step 1.2] Event Enrichment")
    print(f"  {len(needs_enrichment)} events need enrichment...")

    # Enrich the events that need it
    enriched = enrich_events_batch(needs_enrichment)

    # Replace the original events with enriched versions
    enriched_dict = {e.get("original_event_name", e.get("event_name")): e for e in enriched}

    final_events = []
    for event in events:
        event_name = event.get("event_name")
        if event_name in enriched_dict:
            final_events.append(enriched_dict[event_name])
        else:
            final_events.append(event)

    print(f"  Step 1.2 complete: {len(final_events)} events processed")
    return final_events


def run_stage1_pipeline(source: str = "web", file_path: Optional[str] = None, events_text: Optional[str] = None) -> dict:
    """Run the complete Stage 1 pipeline with configurable input source."""

    # Determine directories based on source
    if source == "web":
        run_dir = "data/events/web"
    else:  # sheet source
        run_dir = "data/events/existing"

    # Master files (shared across all sources)
    master_discovered_file = "data/events/discovered_events.json"
    master_scored_file = "data/events/scored_events.json"

    print("")
    print("STAGE 1: EVENT DISCOVERY")
    print(f"  Input source: {source}")
    print(f"  Run directory: {run_dir}")
    print(f"  Master discovered file: {master_discovered_file}")
    print(f"  Master scored file: {master_scored_file}")
    print("")

    os.makedirs(run_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Run-specific files
    events_file = os.path.join(run_dir, "discovered_events.json")
    enriched_file = os.path.join(run_dir, "enriched_events.json")

    # Remove the old run-specific scored file since we use master now
    # scored_file = os.path.join(run_dir, "scored_events.json")  # OLD

    # 1.1 Discover events (with early deduplication for sheets, post-discovery for web)
    events = load_json(events_file)
    if events:
        print(f"\n[Step 1.1] Event Discovery")
        print(f"  {len(events)} events found in existing data")
        events_to_process = events  # Use existing events
    else:
        # Discover events (sheet import already deduplicates against master discovered)
        events = discover_events(source=source, file_path=file_path, events_text=events_text,
                               output_dir=run_dir, master_discovered_file=master_discovered_file)
        save_json(events_file, events)
        print(f"  Saved {len(events)} events to {events_file}")
        events_to_process = events

    # 1.2 Deduplicate against master discovered events (for web discovery)
    if source == "web":
        print(f"\n[Step 1.2] Deduplicate Against Master Discovered Events")
        events_to_process, already_discovered = check_events_against_master_discovered(events, master_discovered_file)

        if already_discovered:
            print(f"  Found {len(already_discovered)} events already in master discovered file")

        # Update master with new web events
        if events_to_process:
            print(f"\n[Step 1.3] Update Master Discovered Events")
            update_master_discovered_events(events_to_process, master_discovered_file)

    # For sheets, events_to_process already deduplicated during import

    # 1.3/1.4 Enrich events (only for new events from sheet imports)
    final_events = events_to_process

    if source == "sheet" and events_to_process:
        enriched = load_json(enriched_file)
        if enriched:
            step_num = "1.3" if source == "web" else "1.3"
            print(f"\n[Step {step_num}] Event Enrichment")
            print(f"  {len(enriched)} enriched events found in existing data")
            final_events = enriched
        else:
            step_num = "1.3" if source == "web" else "1.3"
            print(f"\n[Step {step_num}] Event Enrichment: enriching {len(events_to_process)} new events...")
            final_events = enrich_events(events_to_process)
            save_json(enriched_file, final_events)
            print(f"  Saved {len(final_events)} enriched events to {enriched_file}")

            # Update master with enriched events
            print(f"\n[Update Master] Adding enriched events to master discovered events")
            update_master_discovered_events(final_events, master_discovered_file)

    elif source == "sheet" and not events_to_process:
        print(f"\n[Step 1.3] Event Enrichment: Skipped - all events already discovered")
        final_events = []

    # 1.4/1.5 Score events (with final safety check for sheets)
    step_num = "1.4" if source == "web" else "1.4"
    print(f"\n[Step {step_num}] Event Scoring")

    if final_events:
        # For sheet imports, do a final safety check against master scored events
        if source == "sheet":
            print(f"  Final safety check against master scored events...")
            events_to_score, already_scored_final = check_events_against_master_scoring(final_events, master_scored_file)

            if already_scored_final:
                print(f"  Found {len(already_scored_final)} events already scored (safety check)")
                print(f"  Will only score {len(events_to_score)} remaining events")

            final_events_to_score = events_to_score
        else:
            # Web events - score all final_events
            final_events_to_score = final_events

        if final_events_to_score:
            print(f"  Scoring {len(final_events_to_score)} new events...")
            new_scored_data = score_events(final_events_to_score)

            # Update master scored events file
            update_master_scored_events(new_scored_data, master_scored_file)

            # For sheets, combine with already scored events from safety check
            if source == "sheet" and already_scored_final:
                all_scored_events = new_scored_data.get("scored_events", []) + already_scored_final
            else:
                all_scored_events = new_scored_data.get("scored_events", [])
        else:
            print(f"  All events already scored (caught by safety check)")
            all_scored_events = already_scored_final if source == "sheet" else []
            new_scored_data = {"scored_events": [], "summary": {"total_events_scored": 0}}
    else:
        print(f"  No events to score - all already processed")
        all_scored_events = []
        new_scored_data = {"scored_events": [], "summary": {"total_events_scored": 0}}

    # Filter by cutoff for company discovery
    qualified = [e for e in all_scored_events if (e.get("overall_score") or 0) >= EVENT_SCORE_CUTOFF]
    print(f"\n  {len(qualified)}/{len(all_scored_events)} events above score cutoff ({EVENT_SCORE_CUTOFF})")

    # 1.5 Discover companies
    discovery_results = discover_companies(qualified, run_dir)

    total_companies = sum(len(r.get("companies", [])) for r in discovery_results if r.get("success"))
    print(f"\n[Stage 1 Complete] {len(events)} events -> {len(qualified)} qualified -> {total_companies} companies")

    # Final sync to ensure dashboard has latest data
    sync_all_master_files_to_dashboard()

    return {
        "pipeline": "stage1_event_discovery",
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "run_directory": run_dir,
        "master_scored_file": master_scored_file,
        "summary": {
            "events_discovered": len(events),
            "events_enriched": len(final_events) if source == "sheet" else 0,
            "events_scored": len(all_scored_events),
            "events_qualified": len(qualified),
            "total_companies_discovered": total_companies,
        },
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 1: Event Discovery")
    parser.add_argument("--source", choices=["web", "sheet"], default="web",
                       help="Event source: 'web' for web discovery, 'sheet' for CSV/sheet import")
    parser.add_argument("--file", help="Path to CSV file for sheet import mode")
    parser.add_argument("--use-inline", action="store_true",
                       help="Use inline events data for sheet import mode")
    args = parser.parse_args()

    if args.source == "sheet" and not args.file and not args.use_inline:
        print("Error: For sheet mode, specify --file path or use --use-inline")
        exit(1)

    run_stage1_pipeline(
        source=args.source,
        file_path=args.file
    )
