"""Import all locally discovered event companies into Supabase."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from utils.supabase_sync import sync_discovered_companies_to_supabase


def load_events():
    events = []
    for folder in (REPO_ROOT / "dashboard" / "data" / "events", REPO_ROOT / "data" / "events"):
        for path in sorted(folder.glob("*.json")):
            with path.open() as source:
                data = json.load(source)
            if isinstance(data, dict) and isinstance(data.get("companies"), list):
                events.append(data)
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write companies and event links to Supabase")
    args = parser.parse_args()

    events = load_events()
    links = sum(len(event["companies"]) for event in events)
    names = {item.get("company_name", "").strip().casefold() for event in events for item in event["companies"] if isinstance(item, dict)}
    print(f"Found {links} company appearances across {len(events)} event files ({len(names - {''})} distinct names).")
    if args.apply:
        result = sync_discovered_companies_to_supabase(events)
        if result.get("missing_events"):
            raise SystemExit(f"Events without usable identity: {result['missing_events']}")
    else:
        print("Dry run only; pass --apply to import.")


if __name__ == "__main__":
    main()
