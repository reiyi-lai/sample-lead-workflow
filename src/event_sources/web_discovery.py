"""
Web Discovery Event Source

Discovers trade show events via Claude web search.
This contains the existing event discovery logic moved from stage1_event_discovery.py
"""

import json
import re
from typing import List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import MODELS
from prompts import EVENT_DISCOVERY_SYSTEM_PROMPT
from utils.llm import call_claude, extract_json_from_response


def discover_events_web() -> List[dict]:
    """Discover trade show events via Claude web search."""
    print("\n[Web Discovery] Searching for relevant trade shows...")

    response = call_claude(
        system_prompt=EVENT_DISCOVERY_SYSTEM_PROMPT,
        model=MODELS["event_discovery"],
        enable_web_search=True,
    )

    events = extract_json_from_response(response)

    # Handle different response formats from LLM
    if isinstance(events, dict):
        if "events" in events:
            events = events["events"]
        elif len(events) == 1 and isinstance(list(events.values())[0], list):
            # Sometimes LLM wraps the array in an object like {"events": [...]} or {"results": [...]}
            key = list(events.keys())[0]
            events = events[key]
        elif "event_name" in events:
            # LLM returned a single event object instead of array - try to extract all JSON objects from response
            json_objects = []
            # Look for JSON object patterns in the response
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)

            for match in matches:
                try:
                    obj = json.loads(match)
                    if isinstance(obj, dict) and "event_name" in obj:
                        json_objects.append(obj)
                except json.JSONDecodeError:
                    continue

            if json_objects:
                events = json_objects
            else:
                # Fall back to wrapping single event in array
                events = [events]

    if isinstance(events, dict) and "error" in events:
        print(f"  Error: {events['error']}")
        return []

    if not isinstance(events, list):
        print(f"  Unexpected response format: {type(events)}")
        if isinstance(events, dict):
            print(f"  Dict contents: {events}")
        return []

    print(f"  Web discovery complete: {len(events)} events discovered")
    return events