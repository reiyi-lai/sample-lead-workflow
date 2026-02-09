# Stage 3: Target Role Identification & LinkedIn Search
# 3.1 Identify target roles (LLM analysis)
# 3.2 Generate LinkedIn Sales Navigator URLs + Push to Clay webhook

import os
import json
import requests
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse, quote

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import CLAY_WEBHOOK_URL, MODELS, COMPANY_SCORE_CUTOFF
from prompts import TARGET_ROLES_IDENTIFICATION_SYSTEM_PROMPT
from utils.llm import call_claude, extract_json_from_response
from utils.io import load_json, save_json, company_path


def load_target_roles_json(company_name: str, base_dir: str = "data/companies") -> Optional[dict]:
    return load_json(company_path(base_dir, company_name, "target_roles.json"))


def extract_domain(website_url: str) -> str:
    """Extract clean domain from URL (strips www. and path)."""
    if not website_url:
        return ""
    domain = urlparse(website_url).netloc or urlparse(website_url).path
    return domain.removeprefix("www.").rstrip("/")


def load_qualified_companies(base_dir: str = "data/companies") -> List[dict]:
    """Load companies from per-company folders, filtered by COMPANY_SCORE_CUTOFF."""
    companies = []
    if not os.path.isdir(base_dir):
        return companies

    for folder in os.listdir(base_dir):
        scoring_file = os.path.join(base_dir, folder, "scoring.json")
        if not os.path.isfile(scoring_file):
            continue

        with open(scoring_file, "r") as f:
            scoring = json.load(f)

        icp = scoring.get("icp_qualification", {})
        if icp.get("weighted_score", 0) >= COMPANY_SCORE_CUTOFF:
            companies.append({
                "company_name": scoring.get("company_name", folder),
                "website_url": scoring.get("website_url", ""),
                "icp_qualification": icp,
                "success": True,
            })

    return companies


# STEP 3.1: IDENTIFY TARGET ROLES

def identify_target_roles(company_name: str, website_url: str, base_dir: str = "data/companies") -> dict:
    """Identify target decision-makers from scoring data. Skips if target_roles.json exists."""
    print(f"\n  [Step 3.1] Target Role Identification for {company_name}")

    existing = load_target_roles_json(company_name, base_dir)
    if existing:
        print(f"    Target roles found in existing data ({len(existing.get('target_roles', []))} roles)")
        return existing

    scoring_data = load_json(company_path(base_dir, company_name, "scoring.json"))
    if not scoring_data:
        print(f"    No scoring.json found")
        return {"error": "No scoring data found", "company_name": company_name, "website_url": website_url}

    print(f"    Analyzing scoring data to identify target decision-makers...")
    response = call_claude(
        system_prompt=TARGET_ROLES_IDENTIFICATION_SYSTEM_PROMPT,
        model=MODELS["target_role_identification"],
        user_message=f"Identify target roles for this company:\n\nCompany: {company_name}\nWebsite: {website_url}\n\nScoring data:\n{json.dumps(scoring_data, indent=2)}",
        max_tokens=4096,
    )

    target_roles_data = extract_json_from_response(response)

    if isinstance(target_roles_data, dict) and "error" in target_roles_data:
        print(f"    Failed to identify roles: {target_roles_data.get('error')}")
        return target_roles_data

    num_roles = len(target_roles_data.get("target_roles", []))
    save_json(company_path(base_dir, company_name, "target_roles.json"), target_roles_data)
    print(f"    Step 3.1 complete: {num_roles} target roles identified")

    return target_roles_data


# STEP 3.2: GENERATE LINKEDIN SALES NAVIGATOR SEARCH URLS

def generate_sales_navigator_url(company_name: str, company_domain: str, role_title: str) -> str:
    """Generate a Sales Navigator search URL for a role at a company."""
    clean_title = " ".join(role_title.replace(" of ", " ").replace(" Of ", " ").split())
    return f"https://www.linkedin.com/sales/search/people?keywords={quote(clean_title)}%20{quote(company_name)}"


def generate_sales_navigator_searches(company_name: str, company_domain: str, target_roles: list) -> list:
    """Generate Sales Navigator search URLs for all target roles."""
    return [
        {
            "company_name": company_name,
            "role_title": role["title"],
            "priority": role.get("priority", 0),
            "rationale": role.get("rationale", ""),
            "search_url": generate_sales_navigator_url(company_name, company_domain, role["title"]),
        }
        for role in target_roles
        if role.get("title")
    ]


# STEP 3.2b: PUSH COMPANIES TO CLAY WEBHOOK

def push_company_to_clay(company_name: str, website_url: str, recommended_roles: List[str], icp_score: float) -> dict:
    """Push a company to Clay webhook for people search & enrichment."""
    payload = {
        "company_name": company_name,
        "company_domain": extract_domain(website_url),
        "target_roles": ", ".join(recommended_roles),
        "icp_score": icp_score,
    }

    try:
        response = requests.post(CLAY_WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()

        try:
            response_data = response.json()
        except ValueError:
            response_data = {"message": response.text}

        return {"success": True, "company_name": company_name, "status_code": response.status_code, "response": response_data}

    except requests.exceptions.RequestException as e:
        return {"success": False, "company_name": company_name, "error": str(e)}


# MAIN PIPELINE

def run_stage3_linkedin_search(base_dir: str = "data/companies", max_companies: Optional[int] = None) -> dict:
    """Run Stage 3: identify target roles and generate LinkedIn Sales Navigator searches."""
    print("\nSTAGE 3: IDENTIFY ROLES & GENERATE LINKEDIN SEARCHES\n")

    companies = load_qualified_companies(base_dir)
    print(f"  {len(companies)} qualified companies (score >= {COMPANY_SCORE_CUTOFF})")

    if max_companies:
        companies = companies[:max_companies]
        print(f"  Limiting to first {max_companies} companies")

    successful, failed, all_searches = 0, 0, []

    for i, company in enumerate(companies):
        company_name = company.get("company_name", "")
        website_url = company.get("website_url", "")

        print(f"\n[{i+1}/{len(companies)}] {company_name} (ICP: {company.get('icp_qualification', {}).get('weighted_score', 0)})")

        target_roles_data = identify_target_roles(company_name=company_name, website_url=website_url, base_dir=base_dir)

        if "error" in target_roles_data:
            failed += 1
            continue

        target_roles = target_roles_data.get("target_roles", [])
        if not target_roles:
            target_roles = [
                {"title": "VP of Product Development", "priority": 1, "rationale": "Default role"},
                {"title": "Director of Innovation", "priority": 2, "rationale": "Default role"},
                {"title": "Director of Operations", "priority": 3, "rationale": "Default role"},
            ]
            print(f"  Warning: No roles identified, using defaults")

        print(f"  [Step 3.2] Generating Sales Navigator URLs for {len(target_roles)} roles...")
        searches = generate_sales_navigator_searches(company_name, extract_domain(website_url), target_roles)
        all_searches.extend(searches)
        print(f"  Step 3.2 complete: {len(searches)} search URLs generated")
        successful += 1

    print(f"\nSTAGE 3 COMPLETE: {successful} companies processed, {failed} failed, {len(all_searches)} search URLs\n")

    return {
        "pipeline": "stage3_identify_roles_and_generate_linkedin_searches",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_companies": len(companies),
            "successful": successful,
            "failed": failed,
            "linkedin_searches_generated": len(all_searches),
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage 3: Target Roles & LinkedIn Searches")
    parser.add_argument("--base-dir", default="data/companies")
    parser.add_argument("--max-companies", type=int, default=None)
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    max_companies = args.max_companies
    if args.test:
        max_companies = 1
        print("Running in TEST mode with 1 company")

    run_stage3_linkedin_search(base_dir=args.base_dir, max_companies=max_companies)
