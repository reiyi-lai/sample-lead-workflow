import os
import json
import sys
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stage1_event_discovery import (
    enrich_events, score_events,
    update_master_discovered_events, update_master_scored_events,
    sync_to_dashboard,
)
from utils.io import load_json, save_json

DATA_DIR = Path(os.environ.get("DATA_DIR", "dashboard/data"))
STATE_DIR = DATA_DIR / "state"
EVENTS_DIR = DATA_DIR / "events"
MASTER_DISCOVERED = str(EVENTS_DIR / "discovered_events.json")
MASTER_SCORED = str(EVENTS_DIR / "scored_events.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(title="Instalily GTM API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---

class EventInput(BaseModel):
    event_name: str
    event_url: str

class AddEventsRequest(BaseModel):
    events: list[EventInput]

class AttendanceUpdate(BaseModel):
    event_url: str
    attending: bool
    whos_going: str = ""

class FeedbackUpdate(BaseModel):
    event_url: str
    would_attend_again: bool | None = None
    notes: str = ""


# --- State helpers ---

def _load_state(filename: str) -> dict:
    path = STATE_DIR / filename
    return load_json(str(path)) or {}

def _save_state(filename: str, data: dict):
    save_json(str(STATE_DIR / filename), data)


# --- Endpoints ---

@app.get("/api/events")
def get_events():
    scored = load_json(MASTER_SCORED)
    discovered = load_json(MASTER_DISCOVERED) or []
    scored_events = (scored or {}).get("scored_events", [])

    scored_by_url = {e.get("event_url"): e for e in scored_events}
    events = []
    for d in discovered:
        url = d.get("event_url", "")
        merged = {**d, **scored_by_url.get(url, {})}
        events.append(merged)

    for s in scored_events:
        if s.get("event_url") not in {e.get("event_url") for e in discovered}:
            events.append(s)

    return {"events": events}


@app.post("/api/events/add")
async def add_events(req: AddEventsRequest):
    if not req.events:
        raise HTTPException(400, "No events provided")

    raw_events = [{"event_name": e.event_name, "event_url": e.event_url, "source": "manual_add", "needs_enrichment": True} for e in req.events]

    enriched = enrich_events(raw_events)
    scored_data = score_events(enriched)

    update_master_discovered_events(enriched, MASTER_DISCOVERED)
    update_master_scored_events(scored_data, MASTER_SCORED)

    return {
        "added": len(enriched),
        "scored": len(scored_data.get("scored_events", [])),
        "events": scored_data.get("scored_events", []),
    }


@app.get("/api/events/attendance")
def get_attendance():
    return _load_state("attendance.json")

@app.post("/api/events/attendance")
def update_attendance(req: AttendanceUpdate):
    state = _load_state("attendance.json")
    state[req.event_url] = {
        "attending": req.attending,
        "whos_going": req.whos_going,
        "updated_at": datetime.now().isoformat(),
    }
    _save_state("attendance.json", state)
    return state[req.event_url]


@app.get("/api/events/feedback")
def get_feedback():
    return _load_state("feedback.json")

@app.post("/api/events/feedback")
def update_feedback(req: FeedbackUpdate):
    state = _load_state("feedback.json")
    state[req.event_url] = {
        "would_attend_again": req.would_attend_again,
        "notes": req.notes,
        "updated_at": datetime.now().isoformat(),
    }
    _save_state("feedback.json", state)
    return state[req.event_url]


@app.get("/health")
def health():
    return {"status": "ok"}
