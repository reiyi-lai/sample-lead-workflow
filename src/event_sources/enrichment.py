"""
Event Enrichment Service

Takes partial event data (name + URL) and enriches it with missing details
like dates, location, description, attendee info, etc. via web search.
"""

import json
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import MODELS
from utils.llm import call_claude, extract_json_from_response


EVENT_ENRICHMENT_SYSTEM_PROMPT = """You are an expert at researching trade show and conference events. Your job is to enrich partial event data by finding missing details through web search.

You will be given multiple events, each with basic information (name and URL), and you need to find and return detailed information about each event.

REQUIRED OUTPUT FORMAT (JSON array):
[
  {
    "event_name": "string - official event name",
    "dates": "string - event dates (e.g., 'December 5-8, 2026')",
    "location": "string - city, state/country (e.g., 'Orlando, FL')",
    "cost": "string - cost information if available (e.g., '$3,500 per attendee' or null)",
    "venue": "string - venue name (e.g., 'Orlando Convention Center' or null)",
    "event_url": "string - main event website",
    "description": "string - brief description of the event",
    "industry_vertical": "string - primary industry/vertical (e.g., 'distribution', 'manufacturing')",
    "exhibitor_mix": "string - types of exhibitors/vendors at the event",
    "audience_mix": "string - types of attendees/audience at the event",
    "source": "string - always 'enriched'",
    "enriched": true,
    "enrichment_success": true/false,
    "enrichment_notes": "string - any issues or limitations in finding information"
  }
  // ... more events
]

INSTRUCTIONS:
1. Use web search to find detailed information about each event
2. Focus on finding official event details from event websites and industry sources
3. Look for dates, location, venue, cost, description, industry focus, exhibitor/audience info
4. For industry_vertical, focus on: distribution, manufacturing, construction, HVAC, etc.
5. For exhibitor_mix: describe types of companies/vendors that exhibit
6. For audience_mix: describe types of professionals who attend
7. If you cannot find certain information, set those fields to null (not empty strings)
8. Set enrichment_success to true only if you found most of the key details (dates, location, description)
9. Return a JSON array with one object per event, in the same order as provided
10. Always return valid JSON in the exact format specified above

Remember: You are looking for factual, current information about real trade shows and conferences. Focus on business details that would help evaluate the event's relevance for B2B lead generation."""


def enrich_event_details(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a partial event with missing details via web search.

    Args:
        event: Dict with at least event_name and event_url

    Returns:
        Dict with enriched event details
    """
    event_name = event.get("event_name", "")
    event_url = event.get("event_url", "")

    if not event_name:
        return {
            **event,
            "enriched": False,
            "enrichment_success": False,
            "enrichment_notes": "No event name provided"
        }

    print(f"  Enriching: {event_name}")

    user_message = f"""Enrich this event with detailed information:

Event Name: {event_name}
Event URL: {event_url}

Please search for comprehensive details about this event and return the information in the required JSON format."""

    try:
        response = call_claude(
            system_prompt=EVENT_ENRICHMENT_SYSTEM_PROMPT,
            model=MODELS.get("event_discovery", "claude-3-5-sonnet-20241022"),  # Use same model as event discovery
            user_message=user_message,
            max_tokens=4096,
            enable_web_search=True,
        )

        enriched_data = extract_json_from_response(response)

        if isinstance(enriched_data, dict) and "error" in enriched_data:
            print(f"    -> Enrichment error: {enriched_data['error']}")
            return {
                **event,
                "enriched": False,
                "enrichment_success": False,
                "enrichment_notes": f"LLM error: {enriched_data['error']}"
            }

        if not isinstance(enriched_data, dict):
            print(f"    -> Invalid enrichment response format")
            return {
                **event,
                "enriched": False,
                "enrichment_success": False,
                "enrichment_notes": "Invalid response format from enrichment service"
            }

        # Ensure we preserve the original data and add enrichment metadata
        enriched_event = {
            **event,
            **enriched_data,
            "enriched": True,
            "original_event_name": event.get("event_name"),
            "original_event_url": event.get("event_url"),
        }

        success = enriched_data.get("enrichment_success", False)
        notes = enriched_data.get("enrichment_notes", "")

        print(f"    -> {'Success' if success else 'Partial'}: {notes or 'Enrichment completed'}")
        return enriched_event

    except Exception as e:
        print(f"    -> Exception during enrichment: {e}")
        return {
            **event,
            "enriched": False,
            "enrichment_success": False,
            "enrichment_notes": f"Exception during enrichment: {str(e)}"
        }


def enrich_events_batch_api(events_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich a batch of events with a single API call.

    Args:
        events_batch: List of event dictionaries to enrich (up to 12 recommended)

    Returns:
        List of enriched event dictionaries
    """
    if not events_batch:
        return []

    print(f"  Batch enriching {len(events_batch)} events...")

    # Create the batch prompt
    events_text = ""
    for i, event in enumerate(events_batch):
        events_text += f"{i+1}. Event: {event.get('event_name', 'Unknown')}\n"
        events_text += f"   URL: {event.get('event_url', 'N/A')}\n\n"

    user_message = f"""Enrich these {len(events_batch)} events with detailed information:

{events_text}

Please search for comprehensive details about each event and return a JSON array with one object per event, in the same order as listed above."""

    try:
        response = call_claude(
            system_prompt=EVENT_ENRICHMENT_SYSTEM_PROMPT,
            model=MODELS.get("event_discovery", "claude-3-5-sonnet-20241022"),
            user_message=user_message,
            max_tokens=16384,  # Increased for batch processing
            enable_web_search=True,
        )

        enriched_data = extract_json_from_response(response)

        if isinstance(enriched_data, dict) and "error" in enriched_data:
            print(f"    -> Batch enrichment error: {enriched_data['error']}")
            # Return original events with error notes
            return [{
                **event,
                "enriched": False,
                "enrichment_success": False,
                "enrichment_notes": f"Batch LLM error: {enriched_data['error']}"
            } for event in events_batch]

        if not isinstance(enriched_data, list):
            print(f"    -> Invalid batch response format (expected list, got {type(enriched_data)})")
            return [{
                **event,
                "enriched": False,
                "enrichment_success": False,
                "enrichment_notes": "Invalid batch response format"
            } for event in events_batch]

        # Ensure we have the right number of results
        if len(enriched_data) != len(events_batch):
            print(f"    -> Mismatch: expected {len(events_batch)} results, got {len(enriched_data)}")
            # Pad or truncate as needed
            while len(enriched_data) < len(events_batch):
                enriched_data.append({
                    "event_name": events_batch[len(enriched_data)].get("event_name"),
                    "event_url": events_batch[len(enriched_data)].get("event_url"),
                    "enriched": False,
                    "enrichment_success": False,
                    "enrichment_notes": "Missing from batch response"
                })
            enriched_data = enriched_data[:len(events_batch)]

        # Merge original data with enriched data
        final_events = []
        for i, (original, enriched) in enumerate(zip(events_batch, enriched_data)):
            final_event = {
                **original,
                **enriched,
                "enriched": True,
                "original_event_name": original.get("event_name"),
                "original_event_url": original.get("event_url"),
            }
            final_events.append(final_event)

        successful = sum(1 for e in final_events if e.get("enrichment_success"))
        print(f"    -> {successful}/{len(final_events)} events successfully enriched")

        return final_events

    except Exception as e:
        print(f"    -> Exception during batch enrichment: {e}")
        return [{
            **event,
            "enriched": False,
            "enrichment_success": False,
            "enrichment_notes": f"Exception during batch enrichment: {str(e)}"
        } for event in events_batch]


def enrich_events_batch(events: List[Dict[str, Any]], batch_size: int = 12) -> List[Dict[str, Any]]:
    """
    Enrich multiple events using batched API calls for efficiency.

    Args:
        events: List of event dictionaries to enrich
        batch_size: Number of events to process per API call (default: 12)

    Returns:
        List of enriched event dictionaries
    """
    if not events:
        return []

    print(f"\n[Event Enrichment] Processing {len(events)} events in batches of {batch_size}...")

    enriched_events = []

    # Process events in batches
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(events) + batch_size - 1) // batch_size

        print(f"  [Batch {batch_num}/{total_batches}] ", end="")
        batch_results = enrich_events_batch_api(batch)
        enriched_events.extend(batch_results)

    successful = sum(1 for e in enriched_events if e.get("enrichment_success"))
    print(f"  Event enrichment complete: {successful}/{len(events)} successfully enriched")

    return enriched_events