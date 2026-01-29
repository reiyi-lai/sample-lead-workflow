# stage2_company_qualification.py
# Stage 2: Company Research & Qualification Pipeline
#
# Flow:
# 2.1 Company Research & Scoring (Claude WebSearch) - Research and score in single call
# 2.2 Python Calculation - Calculate weighted ICP score

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

# Delay between API calls to avoid rate limits (30k tokens/min)
STEP_DELAY_SECONDS = 65

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import MODELS, ICP_WEIGHTS
from prompts import COMPANY_RESEARCH_AND_SCORING_SYSTEM_PROMPT
from utils.llm import call_claude_with_web_search, extract_json_from_response

# HELPER FUNCTIONS

def sanitize_company_name(company_name: str) -> str:
    """
    Convert company name to safe folder name.

    Examples:
        "Avery Dennison, Inc." → "Avery Dennison Inc"
        "3M Commercial Solutions" → "3M Commercial Solutions"
        "Company/Name & Co." → "Company Name Co"
    """
    import re

    # Remove common suffixes and special chars
    name = company_name.replace(", Inc.", "").replace(", LLC", "").replace(" Inc.", "").replace(" LLC", "")
    name = re.sub(r'[^\w\s-]', '', name)  # Remove special chars except spaces and hyphens
    name = re.sub(r'\s+', ' ', name)  # Collapse multiple spaces
    return name.strip()


def get_company_folder(output_dir: str, company_name: str) -> str:
    """Get the folder path for a company."""
    folder_name = sanitize_company_name(company_name)
    return os.path.join(output_dir, folder_name)


def check_scoring_exists(output_dir: str, company_name: str) -> bool:
    """Check if scoring.json already exists for this company."""
    company_folder = get_company_folder(output_dir, company_name)
    scoring_file = os.path.join(company_folder, "scoring.json")
    return os.path.exists(scoring_file)


def load_existing_scoring(output_dir: str, company_name: str) -> Optional[dict]:
    """Load existing scoring.json if it exists."""
    company_folder = get_company_folder(output_dir, company_name)
    scoring_file = os.path.join(company_folder, "scoring.json")

    if not os.path.exists(scoring_file):
        return None

    try:
        with open(scoring_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"    Warning: Failed to load existing scoring: {e}")
        return None


def save_scoring_json(output_dir: str, company_name: str, scoring_data: dict, icp_result: dict):
    """Save scoring data and ICP qualification to company folder."""
    company_folder = get_company_folder(output_dir, company_name)
    os.makedirs(company_folder, exist_ok=True)

    full_scoring = {
        **scoring_data,
        "icp_qualification": icp_result,
    }

    scoring_file = os.path.join(company_folder, "scoring.json")
    with open(scoring_file, "w") as f:
        json.dump(full_scoring, f, indent=2)


# STEP 2: RESEARCH AND SCORE COMPANY (Single Call)

def research_and_score_company(
    company_name: str,
    website_url: str,
    output_dir: str = "data/companies",
) -> dict:
    """
    Research and score a company in a single web search call.
    Skips if scoring.json already exists.

    Args:
        company_name: Name of the company
        website_url: Company's website URL
        output_dir: Directory for company folders

    Returns:
        Scoring data dict (with evidence-rich rationales), or dict with "error" key
    """
    # Check if already processed
    if check_scoring_exists(output_dir, company_name):
        print(f"\n  Already scored, loading from file...")
        scoring_data = load_existing_scoring(output_dir, company_name)
        if scoring_data:
            print(f"    -> Loaded existing scoring")
            return scoring_data
        print(f"    -> Failed to load, will re-process")

    print(f"\n  Researching and scoring {company_name}...")

    user_message = f"""
Please research and score the following company for ICP qualification:

Company Name: {company_name}
Website URL: {website_url}

Return the results in the JSON format specified in your instructions.
"""

    response = call_claude_with_web_search(
        system_prompt=COMPANY_RESEARCH_AND_SCORING_SYSTEM_PROMPT,
        user_message=user_message,
        model=MODELS["company_research"],
        max_tokens=8192,
    )

    scoring_data = extract_json_from_response(response)

    if isinstance(scoring_data, dict) and "error" in scoring_data:
        print(f"    -> Failed: {scoring_data.get('error')}")
        return scoring_data

    print(f"    -> Research and scoring complete")
    return scoring_data


# STEP 2.3: CALCULATE WEIGHTED ICP SCORE

def calculate_icp_score(scoring_data: dict) -> dict:
    """
    Calculate weighted ICP score and assign tier based on LLM scores.

    Args:
        scoring_data: Dict with 'scores' containing 1-10 ratings per category

    Returns:
        Dict with weighted_score, tier, and category breakdowns
    """
    scores = scoring_data.get("scores", {})

    # Extract individual scores (default to 5 if missing)
    industry_fit = scores.get("industry_fit", {}).get("score", 5)
    size_revenue_fit = scores.get("size_revenue_fit", {}).get("score", 5)
    strategic_relevance = scores.get("strategic_relevance", {}).get("score", 5)
    market_activity = scores.get("market_activity", {}).get("score", 5)

    # Calculate weighted score (scale 1-10 to 0-100)
    weighted_score = (
        (industry_fit * ICP_WEIGHTS["industry_fit"] * 10) +
        (size_revenue_fit * ICP_WEIGHTS["size_revenue_fit"] * 10) +
        (strategic_relevance * ICP_WEIGHTS["strategic_relevance"] * 10) +
        (market_activity * ICP_WEIGHTS["market_activity"] * 10)
    )

    return {
        "weighted_score": round(weighted_score, 1),
        "category_scores": {
            "industry_fit": {
                "score": industry_fit,
                "weight": ICP_WEIGHTS["industry_fit"],
            },
            "size_revenue_fit": {
                "score": size_revenue_fit,
                "weight": ICP_WEIGHTS["size_revenue_fit"],
            },
            "strategic_relevance": {
                "score": strategic_relevance,
                "weight": ICP_WEIGHTS["strategic_relevance"],
            },
            "market_activity": {
                "score": market_activity,
                "weight": ICP_WEIGHTS["market_activity"],
            },
        },
    }


# COMPANY DEDUPLICATION

def deduplicate_companies(discovery_results: List[dict]) -> List[dict]:
    """
    Deduplicate companies across events by website URL.

    Args:
        discovery_results: List of event discovery results from Stage 1

    Returns:
        List of unique companies with their source events
    """
    seen_urls = {}
    unique_companies = []

    for event_result in discovery_results:
        if not event_result.get("success"):
            continue

        event_name = event_result.get("event_name", "Unknown Event")
        companies = event_result.get("companies", [])

        for company in companies:
            website_url = company.get("website_url", "").lower().strip()
            company_name = company.get("company_name", "")

            # Normalize URL (remove trailing slash, www prefix)
            normalized_url = website_url.rstrip("/")
            if normalized_url.startswith("https://www."):
                normalized_url = "https://" + normalized_url[12:]
            elif normalized_url.startswith("http://www."):
                normalized_url = "http://" + normalized_url[11:]

            if not normalized_url:
                # Use company name as fallback key
                normalized_url = f"name:{company_name.lower()}"

            if normalized_url not in seen_urls:
                seen_urls[normalized_url] = True
                unique_companies.append({
                    "company_name": company_name,
                    "website_url": company.get("website_url", ""),
                    "source_events": [event_name],
                    "confidence": company.get("confidence", "unknown"),
                    "relevance_indicators": company.get("relevance_indicators", []),
                    "description": company.get("description", ""),
                })
            else:
                # Add this event to the company's source events
                for uc in unique_companies:
                    if uc["website_url"].lower().strip().rstrip("/") == website_url.rstrip("/"):
                        if event_name not in uc["source_events"]:
                            uc["source_events"].append(event_name)
                        break

    return unique_companies


# MAIN PIPELINE

def run_stage2_pipeline(
    events_dir: str = "data/events/companies",
    output_dir: str = "data/companies",
    max_companies: Optional[int] = None,
) -> dict:
    """
    Run the complete Stage 2 Company Qualification Pipeline.

    Args:
        events_dir: Directory containing per-event company JSON files
        output_dir: Directory to save output files
        max_companies: Optional limit on number of companies to process

    Returns:
        Dict with all pipeline results
    """
    import glob

    print("\n" + "=" * 60)
    print("STAGE 2: COMPANY RESEARCH & QUALIFICATION PIPELINE")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load Stage 1 results from per-event files
    print(f"\nLoading companies from: {events_dir}/")
    discovery_results = []
    for filepath in sorted(glob.glob(os.path.join(events_dir, "*.json"))):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                discovery_results.append(data)
        except Exception as e:
            print(f"  Warning: Failed to load {filepath}: {e}")

    print(f"  Loaded {len(discovery_results)} event files")

    # Deduplicate companies
    print("\nDeduplicating companies across events...")
    unique_companies = deduplicate_companies(discovery_results)
    print(f"  Found {len(unique_companies)} unique companies")

    # Limit if specified
    if max_companies:
        unique_companies = unique_companies[:max_companies]
        print(f"  Processing first {max_companies} companies")

    # Process each company
    qualified_results = []

    for i, company in enumerate(unique_companies):
        company_name = company["company_name"]
        website_url = company["website_url"]

        print(f"\n[{i+1}/{len(unique_companies)}] {company_name}")
        print(f"  URL: {website_url}")

        # Research and score (single call)
        scoring_data = research_and_score_company(
            company_name=company_name,
            website_url=website_url,
            output_dir=output_dir,
        )

        # Check for errors
        if "error" in scoring_data:
            qualified_results.append({
                "company_name": company_name,
                "website_url": website_url,
                "source_events": company["source_events"],
                "success": False,
                "error": scoring_data.get("error"),
            })
            continue

        # Calculate weighted ICP score (if not already loaded from cache)
        if "icp_qualification" not in scoring_data:
            icp_result = calculate_icp_score(scoring_data)
            print(f"  -> ICP Score: {icp_result['weighted_score']}")
            save_scoring_json(output_dir, company_name, scoring_data, icp_result)
            print(f"    -> Saved to scoring.json")
        else:
            icp_result = scoring_data["icp_qualification"]
            print(f"  -> ICP Score: {icp_result['weighted_score']} (cached)")

        qualified_results.append({
            "company_name": company_name,
            "website_url": website_url,
            "source_events": company["source_events"],
            "success": True,
            "scoring": scoring_data,
            "icp_qualification": icp_result,
        })

        # Delay between companies to avoid rate limits
        if i < len(unique_companies) - 1:
            print(f"\n  Waiting {STEP_DELAY_SECONDS}s before next company...")
            time.sleep(STEP_DELAY_SECONDS)

    # Per-company scoring.json files already saved during processing
    successful = [r for r in qualified_results if r.get("success")]
    failed = [r for r in qualified_results if not r.get("success")]

    results = {
        "pipeline": "stage2_company_qualification",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_unique_companies": len(unique_companies),
            "successfully_processed": len(successful),
            "failed": len(failed),
        },
    }

    print("\n" + "=" * 60)
    print("STAGE 2 COMPLETE")
    print("=" * 60)
    print(f"Total companies processed: {len(unique_companies)}")
    print(f"Successfully scored: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"\nOutputs saved to per-company folders:")
    print(f"  - {output_dir}/[Company Name]/scoring.json")

    return results


# CLI ENTRY POINT

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Stage 2: Company Qualification Pipeline")
    parser.add_argument(
        "--events-dir",
        default="data/events/companies",
        help="Directory containing per-event company JSON files (default: data/events/companies)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/companies",
        help="Directory to save output files (default: data/companies)",
    )
    parser.add_argument(
        "--max-companies",
        type=int,
        default=None,
        help="Maximum number of companies to process (for testing)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode with 1 company",
    )

    args = parser.parse_args()

    # Set up limits
    max_companies = args.max_companies
    if args.test:
        max_companies = 1
        print("Running in TEST mode with 1 company")

    # Run pipeline
    results = run_stage2_pipeline(
        events_dir=args.events_dir,
        output_dir=args.output_dir,
        max_companies=max_companies,
    )
