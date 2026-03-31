"""
Event Sources Module

Provides multiple input sources for event discovery:
- Web Discovery: Search for events from scratch via Claude web search
- Sheet Import: Import events from existing CSV/sheet data
- Event Enrichment: Fill in missing event details from partial data
"""

from .web_discovery import discover_events_web
from .sheet_import import import_events_from_sheet, parse_events_data, import_events_from_inline_data, update_master_events_registry
from .enrichment import enrich_event_details, enrich_events_batch

__all__ = [
    'discover_events_web',
    'import_events_from_sheet',
    'parse_events_data',
    'import_events_from_inline_data',
    'update_master_events_registry',
    'enrich_event_details',
    'enrich_events_batch'
]