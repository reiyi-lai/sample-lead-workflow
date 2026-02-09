# Stage 2: Company Research & Qualification
# 2.1 Research & score company (web search)
# 2.2 Calculate weighted ICP score

import os
import json
from datetime import datetime
from typing import List, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import MODELS, ICP_WEIGHTS
from prompts import COMPANY_RESEARCH_AND_SCORING_SYSTEM_PROMPT
from utils.llm import call_claude, extract_json_from_response
from utils.io import load_json, save_json, company_path


def save_scoring_json(output_dir: str, company_name: str, scoring_data: dict, icp_result: dict):
    """Save scoring data and ICP qualification to company folder."""
    save_json(company_path(output_dir, company_name, "scoring.json"), {**scoring_data, "icp_qualification": icp_result})


# STEP 2.1: RESEARCH AND SCORE COMPANY

def research_and_score_company(company_name: str, website_url: str, output_dir: str = "data/companies") -> dict:
    """Research and score a company in a single web search call. Skips if scoring.json exists."""
    existing = load_json(company_path(output_dir, company_name, "scoring.json"))
    if existing:
        print(f"  Scoring found in existing data")
        return existing

    print(f"  Researching and scoring via web search...")

    response = call_claude(
        system_prompt=COMPANY_RESEARCH_AND_SCORING_SYSTEM_PROMPT,
        model=MODELS["company_research"],
        user_message=f"Research and score this company for ICP qualification:\n\nCompany: {company_name}\nWebsite: {website_url}",
        max_tokens=8192,
        enable_web_search=True,
    )

    scoring_data = extract_json_from_response(response)

    if isinstance(scoring_data, dict) and "error" in scoring_data:
        print(f"  Failed: {scoring_data.get('error')}")
        return scoring_data

    print(f"  Research and scoring complete")
    return scoring_data


# STEP 2.2: CALCULATE WEIGHTED ICP SCORE

def calculate_icp_score(scoring_data: dict) -> dict:
    """Calculate weighted ICP score (1-10 per category, scaled to 0-100)."""
    scores = scoring_data.get("scores", {})
    category_scores = {}
    weighted_score = 0

    for key, weight in ICP_WEIGHTS.items():
        score = scores.get(key, {}).get("score", 5)
        weighted_score += score * weight * 10
        category_scores[key] = {"score": score, "weight": weight}

    return {
        "weighted_score": round(weighted_score, 1), 
        "category_scores": category_scores,
    }


# COMPANY DEDUPLICATION

def deduplicate_companies(discovery_results: List[dict]) -> List[dict]:
    """Deduplicate companies across events by normalized website URL."""
    seen_urls = {}
    unique_companies = []

    for event_result in discovery_results:
        if not event_result.get("success"):
            continue

        event_name = event_result.get("event_name", "Unknown Event")

        for company in event_result.get("companies", []):
            company_name = company.get("company_name", "")
            raw_url = company.get("website_url", "").lower().strip().rstrip("/")
            normalized_url = raw_url.replace("://www.", "://") or f"name:{company_name.lower()}"

            if normalized_url not in seen_urls:
                seen_urls[normalized_url] = len(unique_companies)
                unique_companies.append({
                    "company_name": company_name,
                    "website_url": company.get("website_url", ""),
                    "source_events": [event_name],
                    "confidence": company.get("confidence", "unknown"),
                    "relevance_indicators": company.get("relevance_indicators", []),
                    "description": company.get("description", ""),
                })
            else:
                idx = seen_urls[normalized_url]
                if event_name not in unique_companies[idx]["source_events"]:
                    unique_companies[idx]["source_events"].append(event_name)

    return unique_companies


# MAIN PIPELINE
def run_stage2_pipeline(events_dir: str = "data/events/companies", output_dir: str = "data/companies", max_companies: Optional[int] = None) -> dict:
    """Run Stage 2: research, score, and qualify companies from Stage 1."""
    import glob

    print("")
    print("STAGE 2: COMPANY RESEARCH & QUALIFICATION")
    print("")

    os.makedirs(output_dir, exist_ok=True)

    # Load Stage 1 results
    print(f"\nLoading companies from: {events_dir}/")
    discovery_results = []
    for filepath in sorted(glob.glob(os.path.join(events_dir, "*.json"))):
        data = load_json(filepath)
        if data:
            discovery_results.append(data)

    print(f"  Loaded {len(discovery_results)} event files")

    # Deduplicate
    unique_companies = deduplicate_companies(discovery_results)
    print(f"  {len(unique_companies)} unique companies after deduplication")

    if max_companies:
        unique_companies = unique_companies[:max_companies]
        print(f"  Limiting to first {max_companies} companies")

    # Process each company
    successful, failed = 0, 0

    for i, company in enumerate(unique_companies):
        company_name = company["company_name"]
        website_url = company["website_url"]

        print(f"\n[{i+1}/{len(unique_companies)}] {company_name} ({website_url})")

        scoring_data = research_and_score_company(
            company_name=company_name,
            website_url=website_url,
            output_dir=output_dir,
        )

        if "error" in scoring_data:
            failed += 1
            continue

        if "icp_qualification" not in scoring_data:
            icp_result = calculate_icp_score(scoring_data)
            save_scoring_json(output_dir, company_name, scoring_data, icp_result)
        else:
            icp_result = scoring_data["icp_qualification"]
        print(f"  ICP Score: {icp_result['weighted_score']}")
        successful += 1

    print("")
    print(f"STAGE 2 COMPLETE: {successful} scored, {failed} failed")
    print("")

    return {
        "pipeline": "stage2_company_qualification",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_unique_companies": len(unique_companies),
            "successfully_processed": successful,
            "failed": failed,
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage 2: Company Qualification")
    parser.add_argument("--events-dir", default="data/events/companies")
    parser.add_argument("--output-dir", default="data/companies")
    parser.add_argument("--max-companies", type=int, default=None)
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    max_companies = args.max_companies
    if args.test:
        max_companies = 1
        print("Running in TEST mode with 1 company")

    run_stage2_pipeline(
        events_dir=args.events_dir,
        output_dir=args.output_dir,
        max_companies=max_companies,
    )
