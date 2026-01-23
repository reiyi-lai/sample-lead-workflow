# stage3_contact_finding.py
# Stage 3: Decision-Maker/Contact Finding Pipeline
#
# Flow:
# 3.1 Identify Target Roles (LLM) - Analyze research, determine who to contact
# 3.2 Push to Clay (API) - Send company + target roles to Clay webhook
# 3.3 Receive Contacts (Webhook) - Clay sends back enriched contacts
# 3.4 LLM Contact Scoring - Score contacts and add personalization hooks

import os
import json
import time
import requests
from datetime import datetime
from typing import List, Optional, Tuple
from urllib.parse import urlparse

# Add src to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import CLAY_WEBHOOK_URL, MODELS
from prompts import TARGET_ROLES_IDENTIFICATION_SYSTEM_PROMPT
from utils.llm import call_claude, extract_json_from_response

# HELPER FUNCTIONS

def sanitize_company_name(company_name: str) -> str:
    """Convert company name to safe folder name."""
    import re
    name = company_name.replace(", Inc.", "").replace(", LLC", "").replace(" Inc.", "").replace(" LLC", "")
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def get_company_folder(company_name: str, base_dir: str = "data/companies") -> str:
    """Get the folder path for a company."""
    folder_name = sanitize_company_name(company_name)
    return os.path.join(base_dir, folder_name)


def load_research_json(company_name: str, base_dir: str = "data/companies") -> Optional[dict]:
    """Load research.json from company folder."""
    company_folder = get_company_folder(company_name, base_dir)
    research_file = os.path.join(company_folder, "research.json")

    if not os.path.exists(research_file):
        return None

    try:
        with open(research_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"    ⚠️  Failed to load research.json: {e}")
        return None


def save_target_roles_json(company_name: str, target_roles_data: dict, base_dir: str = "data/companies"):
    """Save target roles analysis to company folder."""
    company_folder = get_company_folder(company_name, base_dir)
    os.makedirs(company_folder, exist_ok=True)

    target_roles_file = os.path.join(company_folder, "target_roles.json")
    with open(target_roles_file, "w") as f:
        json.dump(target_roles_data, f, indent=2)


def load_target_roles_json(company_name: str, base_dir: str = "data/companies") -> Optional[dict]:
    """Load target_roles.json if it exists."""
    company_folder = get_company_folder(company_name, base_dir)
    target_roles_file = os.path.join(company_folder, "target_roles.json")

    if not os.path.exists(target_roles_file):
        return None

    try:
        with open(target_roles_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"    ⚠️  Failed to load target_roles.json: {e}")
        return None


def extract_domain(website_url: str) -> str:
    """
    Extract clean domain from website URL.

    Examples:
        https://www.averydennison.com → averydennison.com
        http://3m.com/ → 3m.com
        https://averydennison.com/graphics → averydennison.com
    """
    if not website_url:
        return ""

    # Parse URL
    parsed = urlparse(website_url)
    domain = parsed.netloc or parsed.path

    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]

    # Remove trailing slash
    domain = domain.rstrip("/")

    return domain


def load_qualified_companies(
    input_file: str = "data/companies/all_qualified_companies.json",
    tier_filter: Optional[int] = None,
) -> List[dict]:
    """
    Load qualified companies from Stage 2 output.

    Args:
        input_file: Path to Stage 2 output file
        tier_filter: If specified, only return companies of this tier (1, 2, or 3)

    Returns:
        List of company dicts with qualification data
    """
    with open(input_file, "r") as f:
        companies = json.load(f)

    # Filter successful qualifications only
    companies = [c for c in companies if c.get("success")]

    # Filter by tier if specified
    if tier_filter is not None:
        companies = [
            c for c in companies
            if c.get("icp_qualification", {}).get("tier") == tier_filter
        ]

    return companies


# STEP 3.1: IDENTIFY TARGET ROLES & ENGAGEMENT STRATEGY

def identify_target_roles(
    company_name: str,
    website_url: str,
    base_dir: str = "data/companies",
) -> dict:
    """
    Analyze company research and identify target decision-makers and engagement strategy.
    Skips identification if target_roles.json already exists.

    Args:
        company_name: Name of the company
        website_url: Company's website URL
        base_dir: Base directory for company folders

    Returns:
        Dict with target roles, use cases, and engagement strategy
    """
    print(f"\n  [Step 3.1] Identifying target roles for {company_name}...")

    # Check if target_roles.json already exists
    existing_roles = load_target_roles_json(company_name, base_dir)
    if existing_roles:
        print(f"    ✓ Target roles already exist, loading from file...")
        return existing_roles

    # Load research data
    research_data = load_research_json(company_name, base_dir)

    if not research_data:
        print(f"    ✗ No research.json found")
        return {
            "error": "No research data found",
            "company_name": company_name,
            "website_url": website_url,
        }

    # Build user message with research data
    user_message = f"""
Analyze the following company research and identify target decision-makers:

Company Name: {company_name}
Website URL: {website_url}

RESEARCH DATA:
{json.dumps(research_data, indent=2)}

Based on this research, identify the best roles to target and develop an engagement strategy.
Return your analysis in the JSON format specified.
"""

    # Call Claude to analyze and identify roles
    response = call_claude(
        system_prompt=TARGET_ROLES_IDENTIFICATION_SYSTEM_PROMPT,
        user_message=user_message,
        model=MODELS.get("target_role_identification", "claude-sonnet-4-5-20250929"),
        max_tokens=4096,
    )

    target_roles_data = extract_json_from_response(response)

    if isinstance(target_roles_data, dict) and "error" in target_roles_data:
        print(f"    ✗ Failed to identify roles: {target_roles_data.get('error')}")
        return target_roles_data

    print(f"    ✓ Identified {len(target_roles_data.get('target_roles', []))} target roles")

    # Save to company folder
    save_target_roles_json(company_name, target_roles_data, base_dir)
    print(f"    ✓ Saved to target_roles.json")

    return target_roles_data


# STEP 3.2: GENERATE LINKEDIN SALES NAVIGATOR SEARCH URLS

def generate_sales_navigator_url(
    company_name: str,
    company_domain: str,
    role_title: str,
) -> str:
    """
    Generate a LinkedIn Sales Navigator search URL for a specific role at a company.

    Args:
        company_name: Name of the company
        company_domain: Company domain (e.g., "epson.com")
        role_title: Job title to search for (e.g., "VP of Product Development")

    Returns:
        LinkedIn Sales Navigator search URL
    """
    from urllib.parse import quote

    # Remove " of " from role title
    clean_title = role_title.replace(" of ", " ").replace(" Of ", " ")
    clean_title = " ".join(clean_title.split())

    # Encode for URL
    encoded_title = quote(clean_title)
    encoded_company = quote(company_name)

    # Sales Navigator URL format
    # Uses both company name and title keywords for best results
    base_url = "https://www.linkedin.com/sales/search/people"

    # Simple keyword-based search (works across all Sales Nav versions)
    search_url = f"{base_url}?keywords={encoded_title}%20{encoded_company}"

    return search_url


def generate_sales_navigator_searches(
    company_name: str,
    company_domain: str,
    target_roles: list,
) -> list:
    """
    Generate Sales Navigator search URLs for all target roles at a company.

    Args:
        company_name: Name of the company
        company_domain: Company domain
        target_roles: List of role dicts with 'title' field

    Returns:
        List of dicts with role info and search URLs
    """
    searches = []

    for role in target_roles:
        title = role.get("title", "")
        if not title:
            continue

        search_url = generate_sales_navigator_url(
            company_name=company_name,
            company_domain=company_domain,
            role_title=title,
        )

        searches.append({
            "company_name": company_name,
            "role_title": title,
            "priority": role.get("priority", 0),
            "rationale": role.get("rationale", ""),
            "search_url": search_url,
        })

    return searches


# STEP 3.X (PLACEHOLDER): PUSH COMPANIES TO CLAY WEBHOOK
# Note: Clay integration kept as placeholder for future use
# Currently using LinkedIn Sales Navigator for better contact discovery

def push_company_to_clay(
    company_name: str,
    website_url: str,
    recommended_roles: List[str],
    tier: int,
    icp_score: float,
) -> dict:
    """
    Push a single company to Clay webhook for people search & enrichment.

    Args:
        company_name: Name of the company
        website_url: Company's website URL
        recommended_roles: List of job titles to search for
        tier: ICP tier (1, 2, or 3)
        icp_score: Weighted ICP score (0-100)

    Returns:
        Response data from Clay webhook
    """
    # Extract domain
    company_domain = extract_domain(website_url)

    # Format roles as comma-separated string for Clay
    roles_string = ", ".join(recommended_roles)

    # Prepare payload for Clay
    payload = {
        "company_name": company_name,
        "company_domain": company_domain,
        "target_roles": roles_string,
        "tier": tier,
        "icp_score": icp_score,
    }

    # Send to Clay webhook
    try:
        response = requests.post(
            CLAY_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()

        # Clay may return plaintext or JSON - handle both
        response_data = {}
        if response.content:
            try:
                response_data = response.json()
            except ValueError:
                # Clay returns plaintext, not JSON
                response_data = {"message": response.text}

        return {
            "success": True,
            "company_name": company_name,
            "company_domain": company_domain,
            "status_code": response.status_code,
            "response": response_data,
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "company_name": company_name,
            "company_domain": company_domain,
            "error": str(e),
        }


def process_companies_and_generate_searches(
    companies: List[dict],
    base_dir: str = "data/companies",
    delay_seconds: int = 2,
) -> Tuple[List[dict], List[dict]]:
    """
    Process companies: identify target roles, then generate Sales Navigator search URLs.

    Args:
        companies: List of company dicts from Stage 2
        base_dir: Base directory for company folders
        delay_seconds: Delay between LLM requests to avoid rate limits

    Returns:
        Tuple of (role_identification_results, sales_nav_searches)
    """
    role_results = []
    all_searches = []

    for i, company in enumerate(companies):
        company_name = company.get("company_name", "")
        website_url = company.get("website_url", "")
        icp_qual = company.get("icp_qualification", {})
        tier = icp_qual.get("tier", 3)
        icp_score = icp_qual.get("weighted_score", 0)

        print(f"\n[{i+1}/{len(companies)}] {company_name}")
        print(f"  URL: {website_url}")
        print(f"  Tier: {tier} (ICP Score: {icp_score})")

        # Step 3.1: Identify target roles
        target_roles_data = identify_target_roles(
            company_name=company_name,
            website_url=website_url,
            base_dir=base_dir,
        )

        role_results.append({
            "company_name": company_name,
            "success": "error" not in target_roles_data,
            "data": target_roles_data,
        })

        # Check for errors in role identification
        if "error" in target_roles_data:
            print(f"  ✗ Skipping Sales Nav URL generation due to role identification error")
            continue

        # Extract target roles
        target_roles = target_roles_data.get("target_roles", [])

        # Fallback to default roles if none provided
        if not target_roles:
            target_roles = [
                {"title": "VP of Product Development", "priority": 1, "rationale": "Default role"},
                {"title": "Director of Innovation", "priority": 2, "rationale": "Default role"},
                {"title": "Director of Operations", "priority": 3, "rationale": "Default role"},
            ]
            print(f"  ⚠️  No roles identified, using defaults")

        print(f"  [Step 3.2] Generating LinkedIn Sales Navigator URLs for {len(target_roles)} roles...")

        # Step 3.2: Generate Sales Navigator search URLs
        company_domain = extract_domain(website_url)
        searches = generate_sales_navigator_searches(
            company_name=company_name,
            company_domain=company_domain,
            target_roles=target_roles,
        )

        all_searches.extend(searches)

        print(f"  ✓ Generated {len(searches)} Sales Navigator search URLs")
        for search in searches[:3]:
            print(f"    - {search['role_title']}")
        if len(searches) > 3:
            print(f"    ... and {len(searches) - 3} more")

        # Delay between companies (for LLM rate limits)
        if i < len(companies) - 1:
            print(f"\n  Waiting {delay_seconds}s before next company...")
            time.sleep(delay_seconds)

    return role_results, all_searches


# MAIN PIPELINE

def run_stage3_linkedin_search(
    input_file: str = "data/companies/all_qualified_companies.json",
    output_dir: str = "data/contacts",
    base_dir: str = "data/companies",
    tier_filter: Optional[int] = 1,
    max_companies: Optional[int] = None,
) -> dict:
    """
    Run Stage 3: Identify target roles and generate LinkedIn Sales Navigator searches.

    Pipeline:
    - Step 3.1: Identify target roles (LLM analysis)
    - Step 3.2: Generate LinkedIn Sales Navigator search URLs

    Args:
        input_file: Path to Stage 2 output file
        output_dir: Directory to save output files
        base_dir: Base directory for company folders (for research.json)
        tier_filter: Only process companies of this tier (1, 2, 3, or None for all)
        max_companies: Optional limit on number of companies to process

    Returns:
        Dict with results and summary
    """
    print("\n" + "=" * 60)
    print("STAGE 3: IDENTIFY ROLES & GENERATE LINKEDIN SEARCHES")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load companies
    print(f"\nLoading companies from: {input_file}")
    companies = load_qualified_companies(input_file, tier_filter=tier_filter)
    print(f"  Found {len(companies)} qualified companies")

    if tier_filter is not None:
        print(f"  Filtered to Tier {tier_filter} only")

    # Limit if specified
    if max_companies:
        companies = companies[:max_companies]
        print(f"  Processing first {max_companies} companies")

    # Process companies: identify roles and generate Sales Nav URLs
    print(f"\nProcessing {len(companies)} companies...")
    role_results, all_searches = process_companies_and_generate_searches(
        companies=companies,
        base_dir=base_dir,
        delay_seconds=2,
    )

    # Calculate summaries
    successful_roles = [r for r in role_results if r["success"]]
    failed_roles = [r for r in role_results if not r["success"]]

    # Save role identification results
    role_results_file = os.path.join(output_dir, "role_identification_results.json")
    with open(role_results_file, "w") as f:
        json.dump(role_results, f, indent=2)
    print(f"\nSaved role identification results to: {role_results_file}")

    # Save Sales Navigator searches to JSON
    searches_json_file = os.path.join(output_dir, "linkedin_sales_nav_searches.json")
    with open(searches_json_file, "w") as f:
        json.dump(all_searches, f, indent=2)
    print(f"Saved Sales Navigator searches to: {searches_json_file}")

    # Create summary
    summary = {
        "pipeline": "stage3_identify_roles_and_generate_linkedin_searches",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_companies": len(companies),
            "role_identification": {
                "successful": len(successful_roles),
                "failed": len(failed_roles),
            },
            "linkedin_searches_generated": len(all_searches),
            "tier_filter": tier_filter,
        },
        "output_files": {
            "role_identification": role_results_file,
            "linkedin_searches": searches_json_file,
        },
    }

    # Save summary
    summary_file = os.path.join(output_dir, "pipeline_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("STAGE 3 COMPLETE")
    print("=" * 60)
    print(f"Total companies processed: {len(companies)}")
    print(f"\nStep 3.1 - Role Identification:")
    print(f"  Successful: {len(successful_roles)}")
    print(f"  Failed: {len(failed_roles)}")
    print(f"\nStep 3.2 - LinkedIn Sales Navigator Searches:")
    print(f"  Total searches generated: {len(all_searches)}")
    print(f"\nOutputs saved to:")
    print(f"  - Per-company folders: {base_dir}/[Company Name]/target_roles.json")
    print(f"  - Role identification results: {role_results_file}")
    print(f"  - LinkedIn searches: {searches_json_file}")
    print(f"\nNext steps:")
    print(f"  1. Use the JSON file in your dashboard frontend to display clickable search links")
    print(f"  2. Search on LinkedIn Sales Navigator and export contacts")
    print(f"  3. Import exported contacts into Stage 4 for outreach personalization")

    return summary


# CLI ENTRY POINT

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Stage 3: Identify Target Roles & Generate LinkedIn Sales Navigator Searches"
    )
    parser.add_argument(
        "--input",
        default="data/companies/all_qualified_companies.json",
        help="Input file from Stage 2 (default: data/companies/all_qualified_companies.json)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/contacts",
        help="Directory to save output files (default: data/contacts)",
    )
    parser.add_argument(
        "--base-dir",
        default="data/companies",
        help="Base directory for company folders (default: data/companies)",
    )
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="Filter to specific tier (default: 1 for Tier 1 only)",
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
    results = run_stage3_linkedin_search(
        input_file=args.input,
        output_dir=args.output_dir,
        base_dir=args.base_dir,
        tier_filter=args.tier,
        max_companies=max_companies,
    )
