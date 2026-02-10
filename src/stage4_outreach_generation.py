# Stage 4: Outreach Generation
# 4.1 Contact/Role Analysis & Engagement Strategy (Turn 1)
# 4.2 Outreach Message Generation - Email or LinkedIn (Turn 2)

import os
import sys
import json
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.llm import call_claude, extract_json_from_response
from utils.io import load_json, save_json, company_path
from prompts import (
    CONTACT_ANALYSIS_SYSTEM_PROMPT,
    OUTREACH_EMAIL_SYSTEM_PROMPT,
    OUTREACH_LINKEDIN_SYSTEM_PROMPT,
)
from constants import MODELS, sanitize_name


def _contact_path(companies_dir: str, company_name: str, prefix: str, suffix: str) -> str:
    """Generate path for contact files under companies/{company}/contacts/."""
    return company_path(companies_dir, company_name, f"contacts/{prefix}_{suffix}.json")


def _load_company_data(base_dir: str, company_name: str) -> Tuple[Optional[dict], Optional[list]]:
    """Load scoring and target roles for a company."""
    scoring = load_json(company_path(base_dir, company_name, "scoring.json"))
    if not scoring:
        print(f"    Scoring not found for {company_name}")
        return None, None

    roles_data = load_json(company_path(base_dir, company_name, "target_roles.json"))
    if not roles_data or "target_roles" not in roles_data:
        print(f"    Target roles not found for {company_name}")
        return None, None

    return scoring, roles_data["target_roles"]


def _run_two_turn_outreach(analysis_user_message: str, force_channel: Optional[str] = None) -> Tuple[Optional[dict], Optional[dict]]:
    """Run the two-turn LLM conversation: Turn 1 = analysis, Turn 2 = outreach message."""
    # Turn 1: Analysis
    print(f"    [Turn 1] Generating engagement strategy...")
    try:
        response = call_claude(
            system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": analysis_user_message}],
            model=MODELS["contact_analysis"],
        )
        analysis = extract_json_from_response(response)
    except Exception as e:
        print(f"    [Turn 1] Error: {e}")
        return None, None

    if not analysis:
        return None, None

    print(f"    [Turn 1] Complete (channel: {analysis.get('recommended_channel', 'N/A')})")

    # Turn 2: Outreach
    channel = force_channel or analysis.get("recommended_channel", "email")
    turn2_prompt = OUTREACH_LINKEDIN_SYSTEM_PROMPT if channel == "linkedin" else OUTREACH_EMAIL_SYSTEM_PROMPT

    print(f"    [Turn 2] Generating {channel} message...")
    try:
        response = call_claude(
            system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": analysis_user_message},
                {"role": "assistant", "content": json.dumps(analysis, indent=2)},
                {"role": "user", "content": turn2_prompt},
            ],
            model=MODELS["outreach_generation"],
        )
        outreach = extract_json_from_response(response)
    except Exception as e:
        print(f"    [Turn 2] Error: {e}")
        return analysis, None

    print(f"    [Turn 2] {channel.capitalize()} message generated")
    return analysis, outreach


def process_role(role_title: str, company_name: str, base_dir: str = "data/companies", force_channel: Optional[str] = None) -> Tuple[Optional[dict], Optional[dict]]:
    """Generate analysis and outreach for a target role using [Name] placeholder."""
    prefix = sanitize_name(role_title).replace(" ", "_")

    print(f"\n  [Stage 4] Outreach for {role_title} at {company_name}")

    # Check existing
    analysis_path = _contact_path(base_dir, company_name, prefix, "analysis")
    outreach_path = _contact_path(base_dir, company_name, prefix, "outreach")

    if os.path.exists(analysis_path) and os.path.exists(outreach_path):
        print(f"    Outreach found in existing data")
        return load_json(analysis_path), None

    scoring, target_roles = _load_company_data(base_dir, company_name)
    if not scoring:
        return None, None

    user_message = f"Develop engagement strategy for this role:\n\nRole: {role_title}\nCompany: {company_name}\n\nScoring data:\n{json.dumps(scoring, indent=2)}\n\nTarget roles:\n{json.dumps(target_roles, indent=2)}"

    analysis, outreach = _run_two_turn_outreach(user_message, force_channel)

    if analysis:
        save_json(analysis_path, analysis)
    if outreach:
        save_json(outreach_path, outreach)

    return analysis, outreach


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage 4: Outreach Generation")
    parser.add_argument("--role", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--base-dir", default="data/companies")
    parser.add_argument("--force-channel", choices=["email", "linkedin"])

    args = parser.parse_args()

    process_role(
        role_title=args.role,
        company_name=args.company,
        base_dir=args.base_dir,
        force_channel=args.force_channel,
    )
