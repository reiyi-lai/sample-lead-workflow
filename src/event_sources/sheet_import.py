"""
Sheet Import Event Source

Imports events from existing CSV/sheet data with Event Name and Link columns.
Parses the data and converts it to standardized event objects for enrichment.
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.io import load_json


def normalize_url(url: str) -> str:
    """Normalize URL for duplicate detection."""
    if not url:
        return ""

    # Remove protocol and www
    normalized = url.lower().strip().rstrip("/")
    normalized = normalized.replace("https://", "").replace("http://", "")
    normalized = normalized.replace("www.", "")

    return normalized


def update_master_events_registry(new_events: List[dict], registry_file: str) -> None:
    """
    Update the master events registry with new events.

    Args:
        new_events: List of new events to add to registry
        registry_file: Path to the master events registry JSON file
    """
    if not new_events:
        return

    # Load existing registry
    registry = load_json(registry_file) or []
    original_count = len(registry)

    # Build set of existing URLs for fast lookup
    existing_urls = set()
    for event in registry:
        url = event.get("event_url", "")
        if url:
            existing_urls.add(normalize_url(url))

    # Add new unique events to registry
    added_count = 0
    for event in new_events:
        event_url = event.get("event_url", "")
        normalized_url = normalize_url(event_url)

        if normalized_url and normalized_url not in existing_urls:
            # Add metadata for registry
            registry_event = {
                **event,
                "added_to_registry": datetime.now().isoformat(),
                "registry_id": len(registry) + added_count + 1
            }
            registry.append(registry_event)
            existing_urls.add(normalized_url)
            added_count += 1

    # Save updated registry
    from utils.io import save_json
    save_json(registry_file, registry)

    print(f"  Master registry updated: {added_count} new events added (total: {len(registry)})")


def detect_duplicates_against_existing(new_events: List[dict],
                                     existing_events_file: str = None,
                                     master_registry_file: str = None) -> tuple[List[dict], List[dict]]:
    """
    Check new events against existing events and master registry for duplicates.

    Args:
        new_events: List of new events to check
        existing_events_file: Path to current run's discovered_events.json file
        master_registry_file: Path to master events registry file

    Returns:
        Tuple of (unique_events, duplicate_events)
    """
    if not new_events:
        return [], []

    # Collect existing URLs from multiple sources
    existing_urls = set()
    sources_checked = []

    # Check master registry first (most comprehensive)
    if master_registry_file and os.path.exists(master_registry_file):
        master_events = load_json(master_registry_file) or []
        for event in master_events:
            url = event.get("event_url", "")
            if url:
                existing_urls.add(normalize_url(url))
        sources_checked.append(f"master registry ({len(master_events)} events)")

    # Check current run's events
    if existing_events_file and os.path.exists(existing_events_file):
        existing_events = load_json(existing_events_file) or []
        for event in existing_events:
            url = event.get("event_url", "")
            if url:
                existing_urls.add(normalize_url(url))
        sources_checked.append(f"current run ({len(existing_events)} events)")

    if not existing_urls:
        print(f"  No existing events found - treating all {len(new_events)} events as new")
        return new_events, []

    print(f"  Checking {len(new_events)} new events against {len(existing_urls)} existing URLs from: {', '.join(sources_checked)}")

    unique_events = []
    duplicate_events = []

    for event in new_events:
        event_url = event.get("event_url", "")
        normalized_url = normalize_url(event_url)

        if normalized_url and normalized_url in existing_urls:
            print(f"    Duplicate found: {event.get('event_name', 'Unknown')} -> {event_url}")
            duplicate_events.append(event)
        else:
            unique_events.append(event)

    print(f"  Duplicate detection complete: {len(unique_events)} unique, {len(duplicate_events)} duplicates")
    return unique_events, duplicate_events


def parse_events_data(events_text: str) -> List[dict]:
    """Parse events data from text format (tab-separated or CSV)."""
    events = []

    # Split into lines and clean up
    lines = [line.strip() for line in events_text.strip().split('\n') if line.strip()]

    if not lines:
        return events

    # Skip header line if it looks like headers
    start_idx = 0
    first_line = lines[0].lower()
    if any(header in first_line for header in ['event name', 'event_name', 'name', 'link', 'url']):
        start_idx = 1

    for i, line in enumerate(lines[start_idx:], start_idx + 1):
        try:
            # Try tab-separated first, then comma-separated
            parts = line.split('\t')
            if len(parts) < 2:
                parts = line.split(',', 1)  # Only split on first comma to preserve URLs

            if len(parts) >= 2:
                event_name = parts[0].strip().strip('"')
                event_url = parts[1].strip().strip('"')

                # Skip empty entries
                if not event_name or event_name.lower() in ['', 'n/a', 'tbd', 'tba']:
                    continue

                # Clean up URL
                if event_url and not event_url.startswith(('http://', 'https://')):
                    if event_url.startswith('www.'):
                        event_url = 'https://' + event_url
                    elif '.' in event_url:
                        event_url = 'https://' + event_url

                # Validate URL format
                if event_url:
                    try:
                        parsed = urlparse(event_url)
                        if not (parsed.scheme and parsed.netloc):
                            print(f"  Warning: Invalid URL for '{event_name}': {event_url}")
                            event_url = ""
                    except Exception:
                        print(f"  Warning: Could not parse URL for '{event_name}': {event_url}")
                        event_url = ""

                event = {
                    "event_name": event_name,
                    "event_url": event_url,
                    "source": "sheet_import",
                    "needs_enrichment": True,
                    "original_line": i
                }

                events.append(event)

        except Exception as e:
            print(f"  Warning: Could not parse line {i}: {line[:50]}... ({e})")
            continue

    return events


def import_events_from_sheet(file_path: str = None, events_text: str = None,
                           master_discovered_file: str = None,
                           skip_duplicates: bool = True) -> List[dict]:
    """
    Import events from a CSV file or text data with duplicate detection against master.

    Args:
        file_path: Path to CSV file (optional)
        events_text: Raw text data with events (optional)
        master_discovered_file: Path to master discovered_events.json for duplicate detection
        skip_duplicates: Whether to skip events that match existing ones

    Returns:
        List of event dictionaries with event_name, event_url, and metadata (deduplicated)
    """
    if file_path:
        print(f"\n[Sheet Import] Reading events from: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"  Error: File not found: {file_path}")
            return []
        except Exception as e:
            print(f"  Error reading file: {e}")
            return []
    elif events_text:
        print(f"\n[Sheet Import] Parsing events from provided text data")
        content = events_text
    else:
        print("  Error: Must provide either file_path or events_text")
        return []

    events = parse_events_data(content)

    # Filter out events without URLs (they'll be harder to enrich)
    valid_events = [e for e in events if e.get("event_url")]
    skipped = len(events) - len(valid_events)

    if skipped > 0:
        print(f"  Skipped {skipped} events without valid URLs")

    # Check for duplicates against master discovered events if requested
    if skip_duplicates and master_discovered_file:
        if os.path.exists(master_discovered_file):
            master_data = load_json(master_discovered_file) or []
            existing_urls = set()
            for event in master_data:
                url = event.get("event_url", "")
                if url:
                    existing_urls.add(normalize_url(url))

            unique_events = []
            duplicate_count = 0

            for event in valid_events:
                event_url = event.get("event_url", "")
                normalized_url = normalize_url(event_url)

                if normalized_url and normalized_url in existing_urls:
                    print(f"    Duplicate found: {event.get('event_name', 'Unknown')} -> {event_url}")
                    duplicate_count += 1
                else:
                    unique_events.append(event)

            if duplicate_count > 0:
                print(f"  Skipped {duplicate_count} duplicate events")
            final_events = unique_events
        else:
            print(f"  No master discovered events file found - treating all events as new")
            final_events = valid_events
    else:
        final_events = valid_events

    print(f"  Sheet import complete: {len(final_events)} events imported")
    return final_events


def import_events_from_inline_data() -> List[dict]:
    """Import the events from the inline data provided by the user."""

    events_data = """Event Name\tLink
HDAW'26\thttps://www.hdaw.org/about-the-show/why-attend/
World of Concrete – Jan 2026\thttps://www.worldofconcrete.com/en/home.html
The International Roofing Expo\thttps://www.theroofingexpo.com/en/home.html
POWERGEN International\thttps://www.powergen.com/attend/who-attend
IFDA Partners Executive Forum\thttps://ifdaonline.org/events/ifda-partners-executive-forum/about/
NAW Executive Summit\thttps://www.naw.org/events/executive-summit-2026/
DistribuTECH International\thttps://www.distributech.com/event-information/about-distributech-international
Manifest\thttps://manife.st/
wORLD aG eXPO 2026\thttps://www.worldagexpo.com/attendees/
National Farm Machinery Show\thttps://farmmachineryshow.org/visitors/plan-your-visit
IBS 2026\thttps://www.buildersshow.com/
World Mail & Express (WMX) Americas\t
Atlanta Build Expo\t
Natural Products Expo\thttps://www.expowest.com/en/home.html
CONEXPO-CON/AGG\thttps://www.conexpoconagg.com/
HDA Distribution Management Conference\thttps://www.hda.org/hda-events/2026-distribution-management-conference-and-expo/
ProcureCon West\thttps://procureconwest.wbresearch.com/
The MFG Meeting 2026\thttps://events.amtonline.org/event/8fd364ee-9cbc-4fb6-83f7-b060af54669d/home
The Grainger Show\thttps://www.graingershow.com/website/88103/#tickets-section
New! T-100\thttps://t-100.nawla.org/Attendees
NYC Build Expo\thttps://www.newyorkbuildexpo.com/
American Manufacturing Summit\thttps://manusummit.com/
Field Service Palm Springs\thttps://fieldserviceusa.wbresearch.com/
Sign Expo\thttps://signexpo.org/
MODEX\thttps://modexshow.com/
NAFA 2026 Institute & Expo\thttps://www.nafainstitute.org/
RAPID + TCT 2026\thttps://www.rapid3devent.com/
TIA Capital Ideas Conference\thttps://web.cvent.com/event/5fcaa2f1-f19b-4e81-a814-d17aa1a29d03/websitePage:fe4fb1cb-f5ba-4897-a32c-606d09490169
ISA26\thttps://isa26.isapartners.org/
North American Manufacturing Excellence Summit (NAMES) 2026\thttps://www.executiveplrms.com/names/
INTERPHEX 2026\thttps://www.interphex.com/en-us/show-info.html
Procurement & Supply Chain LIVE\thttps://supplychaindigital.com/events/procurement-supply-chain-live/procurement-supply-chain-live-chicago-2026?gad_source=1&gad_campaignid=23549191152&gbraid=0AAAAACjTaLHS9xINAcjnO6BuI_N_dMU5u&gclid=Cj0KCQjw7IjOBhDyARIsAFzrWQz5Tr3h3SK4Jc86xyclUeKlHAdaLBOIXKjoNa8fDfVPBxtuDNm5gksaAvlcEALw_wcB
ISM World\thttps://www.ismworld.org/events/conferences-and-events/annual-conference/
American Supply Chain Summit\thttps://supplychainus.com/
B2B Online Chicago\thttps://b2bmarketing.wbresearch.com/opportunities?utm_campaign=23414.013%20B2B%20Online%20[…]icago%202026%20-%20SPEX%20New%20ESLR%20Automation%20EM1
Offshore Technology Conference (OTC)\thttps://2026.otcnet.org/attend/who-attends
Fastener Fair USA\thttps://www.fastenerfairusa.com/
NAED\thttps://www.naed.org/national-meeting
Pharma Manufacturing World Summit\thttps://www.executiveplatforms.com/pmws/
ISA Florida Automation Expo\t
CPHI Americas\thttps://www.cphi.coamericas/en/home.html
ChemE Show – Powered by ACHEMA\thttps://www.achema.de/en/the-achema/cheme-show/short-profile
NAED WOMEN IN INDUSTRY FORUM\thttps://www.naed.org/womeninindustry
BIO International Convention 2026\thttps://convention.bio.org/
The SFA Summer Fancy Food Show\thttps://www.specialtyfood.com/fancy-food-shows/summer/"""

    return import_events_from_sheet(events_text=events_data)