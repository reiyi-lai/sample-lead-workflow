"""Persist generated company stages to Supabase without creating fictitious contacts."""

import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from constants import ICP_WEIGHTS, MODELS, sanitize_name
from utils.io import company_path, load_json, save_json


REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / "dashboard" / ".env.local", override=False)


def _config():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    if not url and not key:
        return None
    if not url or not key:
        raise RuntimeError("Both SUPABASE_URL and SUPABASE_SECRET_KEY are required")
    return url.rstrip("/"), key


def _request(config, method, table, *, params=None, body=None, prefer="return=representation"):
    url, key = config
    response = requests.request(
        method,
        f"{url}/rest/v1/{table}",
        params=params,
        json=body,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": prefer,
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Supabase {table} {method} failed ({response.status_code}): {response.text[:400]}")
    return response.json() if response.content else []


def _first(config, table, **filters):
    params = {key: f"eq.{value}" for key, value in filters.items()}
    params.update({"select": "*", "limit": 1})
    rows = _request(config, "GET", table, params=params)
    return rows[0] if rows else None


def _save(config, table, row, **filters):
    existing = _first(config, table, **filters)
    if existing:
        rows = _request(config, "PATCH", table, params={key: f"eq.{value}" for key, value in filters.items()}, body=row)
    else:
        rows = _request(config, "POST", table, body=row)
    if not rows:
        raise RuntimeError(f"Supabase {table} returned no row")
    return rows[0]


def _normalized_domain(website_url):
    parsed = urlparse(website_url if "://" in website_url else f"https://{website_url}")
    return parsed.netloc.lower().removeprefix("www.").split(":")[0]


def _normalized_event_url(event_url):
    return event_url.strip().lower().replace("https://", "", 1).replace("http://", "", 1).removeprefix("www.").rstrip("/")


def _company_name_key(name):
    return " ".join(name.casefold().split())


def _chunks(items, size=100):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _all_rows(config, table, select):
    rows = []
    offset = 0
    while True:
        page = _request(config, "GET", table, params={"select": select, "limit": 1000, "offset": offset})
        rows.extend(page)
        if len(page) < 1000:
            return rows
        offset += len(page)


def sync_discovered_companies_to_supabase(events):
    """Import bare company names and event links without touching enrichment fields."""
    config = _config()
    if not config:
        return {"skipped": "Supabase is not configured"}

    event_rows = _all_rows(config, "events", "id,event_name,normalized_event_url")
    event_by_url = {row["normalized_event_url"]: row for row in event_rows if row.get("normalized_event_url")}
    company_rows = _all_rows(config, "companies", "id,company_name,normalized_domain")
    by_domain = {row["normalized_domain"]: row for row in company_rows if row.get("normalized_domain")}
    by_name = {_company_name_key(row["company_name"]): row for row in company_rows}

    source_links = []
    new_companies = []
    pending_domains = set()
    pending_names = set()
    event_domain_names = {}
    missing_events = []
    skipped_names = 0

    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("companies"), list):
            continue
        event_name = str(event.get("event_name") or "").strip()
        event_url = str(event.get("event_url") or "").strip()
        normalized_event_url = _normalized_event_url(event_url) if event_url else ""
        event_row = event_by_url.get(normalized_event_url)
        if not event_row:
            if not event_name or not event_url:
                missing_events.append(event_name or event_url or "unnamed event")
                continue
            event_row = _save(
                config,
                "events",
                {"event_name": event_name, "event_url": event_url, "normalized_event_url": normalized_event_url},
                normalized_event_url=normalized_event_url,
            )
            event_by_url[normalized_event_url] = event_row

        for found in event["companies"]:
            if not isinstance(found, dict):
                skipped_names += 1
                continue
            name = str(found.get("company_name") or "").strip()
            if not name:
                skipped_names += 1
                continue
            website_url = str(found.get("website_url") or found.get("company_url") or "").strip()
            domain = _normalized_domain(website_url) if website_url else ""
            name_key = _company_name_key(name)
            domain_at_event = (event_row["id"], domain)
            first_name = event_domain_names.get(domain_at_event) if domain else None
            alias_at_same_event = bool(first_name and first_name != name_key)
            if domain and not first_name:
                event_domain_names[domain_at_event] = name_key
            source_links.append((event_row["id"], name, domain, found, alias_at_same_event))

            if ((domain and domain in by_domain and not alias_at_same_event) or name_key in by_name):
                continue
            if ((domain and domain in pending_domains and not alias_at_same_event) or name_key in pending_names):
                continue
            new_companies.append({
                "company_name": name,
                "website_url": website_url or None,
                "normalized_domain": None if alias_at_same_event else domain or None,
                "raw_data": {"source": "event_discovery"},
            })
            if domain and not alias_at_same_event:
                pending_domains.add(domain)
            pending_names.add(name_key)

    for batch in _chunks(new_companies):
        inserted = _request(config, "POST", "companies", body=batch)
        for row in inserted:
            if row.get("normalized_domain"):
                by_domain[row["normalized_domain"]] = row
            by_name[_company_name_key(row["company_name"])] = row

    existing_links = _all_rows(
        config, "event_companies",
        "event_id,company_id,confidence,attendance_type,booth_number,source,source_reasoning,source_urls,relevance_indicators,raw_data",
    )
    by_pair = {(row["event_id"], row["company_id"]): row for row in existing_links}
    desired_links = {}
    confidence_rank = {"unknown": 0, "likely": 1, "confirmed": 2}
    allowed_attendance = {"exhibitor", "sponsor", "speaker", "attendee", "unknown"}

    for event_id, name, domain, found, alias_at_same_event in source_links:
        company = by_domain.get(domain) if domain and not alias_at_same_event else None
        company = company or by_name.get(_company_name_key(name))
        if not company:
            raise RuntimeError(f"Company was not imported: {name}")
        pair = (event_id, company["id"])
        previous = desired_links.get(pair) or by_pair.get(pair) or {}
        confidence = str(found.get("confidence") or "unknown").lower()
        confidence = confidence if confidence in confidence_rank else "unknown"
        existing_confidence = previous.get("confidence") or "unknown"
        stronger = confidence_rank[confidence] > confidence_rank.get(existing_confidence, 0)
        attendance = str(found.get("attendance_type") or "unknown").lower()
        attendance = attendance if attendance in allowed_attendance else "unknown"
        desired_links[pair] = {
            "event_id": event_id,
            "company_id": company["id"],
            "attendance_type": attendance if attendance != "unknown" else previous.get("attendance_type") or "unknown",
            "confidence": confidence if stronger else existing_confidence,
            "booth_number": found.get("booth_number") or previous.get("booth_number"),
            "source": found.get("source") or previous.get("source"),
            "source_reasoning": found.get("source_reasoning") or previous.get("source_reasoning"),
            "source_urls": found.get("source_urls") or previous.get("source_urls") or [],
            "relevance_indicators": found.get("relevance_indicators") or previous.get("relevance_indicators") or [],
            "raw_data": found,
            "is_active": True,
        }

    for batch in _chunks(list(desired_links.values())):
        _request(
            config, "POST", "event_companies",
            params={"on_conflict": "event_id,company_id"},
            body=batch,
            prefer="resolution=merge-duplicates,return=representation",
        )

    result = {
        "source_links": len(source_links),
        "new_companies": len(new_companies),
        "event_links": len(desired_links),
        "missing_events": missing_events,
        "skipped_names": skipped_names,
    }
    print(f"  Synced event companies to Supabase: {result}", flush=True)
    return result


def _search_url(role):
    """PostgREST returns an embedded one-to-one row as either an object or a single-item list."""
    found = role.get("linkedin_searches")
    found = found[0] if isinstance(found, list) else found
    return (found or {}).get("search_url")


def hydrate_company_from_supabase(company_name, website_url, base_dir="data/companies"):
    """Restore local stage artifacts from Supabase so the existing resume checks skip re-running.

    Identity is the normalized domain, matching the unique index, because Supabase stores the
    canonical company name from scoring rather than the name event discovery found.
    """
    config = _config()
    if not config:
        return False

    domain = _normalized_domain(website_url) if website_url else ""
    company = _first(config, "companies", normalized_domain=domain) if domain else None
    if not company or company.get("overall_score") is None:
        return False

    restored = []
    if not load_json(company_path(base_dir, company_name, "scoring.json")):
        save_json(company_path(base_dir, company_name, "scoring.json"), company["raw_data"])
        restored.append("scoring")

    roles = _request(config, "GET", "target_roles", params={
        "select": "id,title,priority,rationale,linkedin_searches(search_url)",
        "company_id": f"eq.{company['id']}",
        "order": "priority",
    })
    if roles and not load_json(company_path(base_dir, company_name, "target_roles.json")):
        save_json(company_path(base_dir, company_name, "target_roles.json"), {
            "company_name": company["company_name"],
            "website_url": company.get("website_url"),
            "target_roles": [
                {"title": role["title"], "priority": role["priority"], "rationale": role["rationale"]}
                for role in roles
            ],
        })
        restored.append(f"{len(roles)} target roles")

    searches = [
        {
            "company_name": company_name,
            "role_title": role["title"],
            "priority": role["priority"],
            "rationale": role["rationale"],
            "search_url": _search_url(role),
        }
        for role in roles if _search_url(role)
    ]
    if searches and not load_json(company_path(base_dir, company_name, "linkedin_searches.json")):
        save_json(company_path(base_dir, company_name, "linkedin_searches.json"), searches)

    title_by_role_id = {role["id"]: role["title"] for role in roles}
    for draft in _request(config, "GET", "outreach_generation", params={
        "select": "target_role_id,raw_data",
        "company_id": f"eq.{company['id']}",
    }):
        title = title_by_role_id.get(draft.get("target_role_id"))
        payload = draft.get("raw_data") or {}
        if not title or not payload.get("outreach"):
            continue
        prefix = sanitize_name(title).replace(" ", "_")
        for kind in ("analysis", "outreach"):
            path = company_path(base_dir, company_name, f"roles/{prefix}_{kind}.json")
            if payload.get(kind) and not load_json(path):
                save_json(path, payload[kind])
                restored.append(f"{title} {kind}")

    if restored:
        print(f"  Restored {company_name} from Supabase: {', '.join(restored)}", flush=True)
    return True


def _event_sources(company_name):
    for folder in (REPO_ROOT / "data" / "events", REPO_ROOT / "dashboard" / "data" / "events"):
        for path in folder.glob("*.json"):
            event = load_json(str(path))
            if not isinstance(event, dict) or not isinstance(event.get("companies"), list):
                continue
            for found in event["companies"]:
                if found.get("company_name", "").casefold() == company_name.casefold():
                    yield event, found


def sync_company_to_supabase(company_name, base_dir="data/companies"):
    """Upsert all available company data. Safe to call after each stage or on resume."""
    config = _config()
    if not config:
        return False

    scoring = load_json(company_path(base_dir, company_name, "scoring.json"))
    if not scoring:
        return False

    website_url = scoring.get("website_url", "")
    domain = _normalized_domain(website_url) if website_url else ""
    if not domain:
        raise ValueError(f"{company_name} has no website domain for Supabase identity")

    company = _save(
        config,
        "companies",
        {
            "company_name": scoring.get("company_name") or company_name,
            "website_url": website_url,
            "normalized_domain": domain,
            "overall_score": scoring.get("icp_qualification", {}).get("weighted_score"),
            "qualification_summary": scoring.get("qualification_summary"),
            "raw_data": scoring,
        },
        normalized_domain=domain,
    )
    company_id = company["id"]

    for key, weight in ICP_WEIGHTS.items():
        factor = scoring.get("scores", {}).get(key)
        if not factor:
            continue
        rationale = factor.get("rationale")
        if not isinstance(rationale, list) or not 2 <= len(rationale) <= 3:
            raise ValueError(f"{company_name}: {key} rationale must have 2–3 bullets")
        _save(
            config,
            "company_score_factors",
            {
                "company_id": company_id,
                "factor_key": key,
                "score": factor["score"],
                "weight": weight,
                "rationale": rationale,
            },
            company_id=company_id,
            factor_key=key,
        )

    for event, discovered in _event_sources(company_name):
        event_url = event.get("event_url", "").lower().replace("https://", "").replace("http://", "").removeprefix("www.").rstrip("/")
        event_row = _first(config, "events", normalized_event_url=event_url) if event_url else None
        if event_row:
            confidence = discovered.get("confidence", "unknown")
            _save(
                config,
                "event_companies",
                {
                    "event_id": event_row["id"],
                    "company_id": company_id,
                    "attendance_type": discovered.get("attendance_type") or "unknown",
                    "confidence": confidence if confidence in ("confirmed", "likely") else "unknown",
                    "booth_number": discovered.get("booth_number"),
                    "source": discovered.get("source"),
                    "source_reasoning": discovered.get("source_reasoning"),
                    "source_urls": discovered.get("source_urls") or [],
                    "relevance_indicators": discovered.get("relevance_indicators") or [],
                    "raw_data": discovered,
                },
                event_id=event_row["id"],
                company_id=company_id,
            )

    roles_data = load_json(company_path(base_dir, company_name, "target_roles.json")) or {}
    searches = load_json(company_path(base_dir, company_name, "linkedin_searches.json")) or []
    search_by_title = {item.get("role_title"): item.get("search_url") for item in searches}

    for role in roles_data.get("target_roles", []):
        title = role.get("title")
        if not title:
            continue
        target_role = _save(
            config,
            "target_roles",
            {
                "company_id": company_id,
                "title": title,
                "priority": role.get("priority") or 1,
                "rationale": role.get("rationale") or "",
            },
            company_id=company_id,
            title=title,
        )
        role_id = target_role["id"]
        if search_by_title.get(title):
            _save(config, "linkedin_searches", {"target_role_id": role_id, "search_url": search_by_title[title]}, target_role_id=role_id)

        prefix = sanitize_name(title).replace(" ", "_")
        analysis = load_json(company_path(base_dir, company_name, f"roles/{prefix}_analysis.json")) or {}
        outreach = load_json(company_path(base_dir, company_name, f"roles/{prefix}_outreach.json")) or {}
        message = outreach.get("message") or {}
        if not message.get("body"):
            continue
        channel = outreach.get("channel") or analysis.get("recommended_channel") or "email"
        if channel not in ("email", "linkedin"):
            channel = "email"
        existing = _request(config, "GET", "outreach_generation", params={
            "select": "id,status",
            "company_id": f"eq.{company_id}",
            "target_role_id": f"eq.{role_id}",
            "contact_id": "is.null",
            "limit": 1,
        })
        if existing and existing[0]["status"] != "draft":
            continue
        row = {
            "company_id": company_id,
            "target_role_id": role_id,
            "contact_id": None,
            "channel": channel,
            "engagement_strategy": analysis.get("engagement_strategy") or {},
            "personalization_hooks": analysis.get("personalization_hooks") or [],
            "subject": message.get("subject"),
            "body": message["body"],
            "status": "draft",
            "model": MODELS["outreach_generation"],
            "raw_data": {"analysis": analysis, "outreach": outreach},
        }
        if existing:
            _request(config, "PATCH", "outreach_generation", params={"id": f"eq.{existing[0]['id']}"}, body=row)
        else:
            _request(config, "POST", "outreach_generation", body=row)

    print(f"  Synced {company_name} to Supabase", flush=True)
    return True
