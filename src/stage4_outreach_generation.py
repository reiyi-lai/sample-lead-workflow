# stage4_outreach_generation.py
# Stage 4: Outreach Generation
#
# Step 4.1: Contact Analysis & Engagement Strategy
# Step 4.2: Outreach Message Generation (Email or LinkedIn)

import os
import sys
import json
import time
import re
from typing import Optional, List, Dict, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.llm import call_claude_conversation, extract_json_from_response
from prompts import (
    CONTACT_ANALYSIS_SYSTEM_PROMPT,
    OUTREACH_EMAIL_SYSTEM_PROMPT,
    OUTREACH_LINKEDIN_SYSTEM_PROMPT,
)
from constants import MODELS


# FILE MANAGEMENT HELPERS

def sanitize_name(name: str) -> str:
    """Convert name to safe folder/filename."""
    # Remove special characters, keep spaces and hyphens
    name = re.sub(r'[^\w\s-]', '', name)
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def get_contact_folder(output_dir: str, company_name: str) -> str:
    """Get folder path for contacts of a company."""
    company_folder = sanitize_name(company_name)
    return os.path.join(output_dir, company_folder)


def get_contact_file_prefix(contact_name: str) -> str:
    """Get filename prefix for a contact."""
    return sanitize_name(contact_name)


def check_analysis_exists(output_dir: str, company_name: str, contact_name: str) -> bool:
    """Check if contact analysis already exists."""
    folder = get_contact_folder(output_dir, company_name)
    prefix = get_contact_file_prefix(contact_name)
    analysis_file = os.path.join(folder, f"{prefix}_analysis.json")
    return os.path.exists(analysis_file)


def load_analysis(output_dir: str, company_name: str, contact_name: str) -> Optional[dict]:
    """Load existing contact analysis."""
    folder = get_contact_folder(output_dir, company_name)
    prefix = get_contact_file_prefix(contact_name)
    analysis_file = os.path.join(folder, f"{prefix}_analysis.json")

    if os.path.exists(analysis_file):
        with open(analysis_file, "r") as f:
            return json.load(f)
    return None


def check_outreach_exists(output_dir: str, company_name: str, contact_name: str) -> bool:
    """Check if outreach message already exists."""
    folder = get_contact_folder(output_dir, company_name)
    prefix = get_contact_file_prefix(contact_name)
    outreach_file = os.path.join(folder, f"{prefix}_outreach.json")
    return os.path.exists(outreach_file)


def save_analysis(output_dir: str, company_name: str, contact_name: str, analysis: dict):
    """Save contact analysis."""
    folder = get_contact_folder(output_dir, company_name)
    os.makedirs(folder, exist_ok=True)
    prefix = get_contact_file_prefix(contact_name)
    analysis_file = os.path.join(folder, f"{prefix}_analysis.json")

    with open(analysis_file, "w") as f:
        json.dump(analysis, f, indent=2)


def save_outreach(output_dir: str, company_name: str, contact_name: str, outreach: dict):
    """Save outreach message."""
    folder = get_contact_folder(output_dir, company_name)
    os.makedirs(folder, exist_ok=True)
    prefix = get_contact_file_prefix(contact_name)
    outreach_file = os.path.join(folder, f"{prefix}_outreach.json")

    with open(outreach_file, "w") as f:
        json.dump(outreach, f, indent=2)


# LOAD STAGE 2 & 3 DATA

def load_company_scoring(base_dir: str, company_name: str) -> Optional[dict]:
    """Load company scoring data from Stage 2."""
    from stage2_company_qualification import get_company_folder

    company_folder = get_company_folder(base_dir, company_name)
    scoring_file = os.path.join(company_folder, "scoring.json")

    if os.path.exists(scoring_file):
        with open(scoring_file, "r") as f:
            return json.load(f)
    return None


def load_target_roles(base_dir: str, company_name: str) -> Optional[dict]:
    """Load target roles from Stage 3."""
    from stage3_contact_finding import load_target_roles_json

    return load_target_roles_json(company_name, base_dir)


# ROLE-BASED OUTREACH (Auto-triggered after Stage 3)
#
# Generates analysis + outreach for a target role with [Name] placeholder.
# Files keyed by sanitized role title.

def get_role_file_prefix(role_title: str) -> str:
    """Get filename prefix for a role (e.g. 'VP of Product Development' -> 'VP_of_Product_Development')."""
    return sanitize_name(role_title).replace(' ', '_')


def check_role_outreach_exists(output_dir: str, company_name: str, role_title: str) -> bool:
    """Check if role-based outreach already exists."""
    folder = get_contact_folder(output_dir, company_name)
    prefix = get_role_file_prefix(role_title)
    return os.path.exists(os.path.join(folder, f"{prefix}_analysis.json")) and \
           os.path.exists(os.path.join(folder, f"{prefix}_outreach.json"))


def process_role(
    role_title: str,
    company_name: str,
    base_dir: str = "data/companies",
    output_dir: str = "data/contacts",
    force_channel: Optional[str] = None,
) -> Tuple[Optional[dict], Optional[dict]]:
    """
    Generate analysis and outreach for a target role (no specific contact).

    Uses [Name] as placeholder. Output files are keyed by role title.

    Args:
        role_title: Target role title (e.g. "VP of Product Development")
        company_name: Company name
        base_dir: Directory with company data from Stage 2 & 3
        output_dir: Directory to save analysis and outreach
        force_channel: Override recommended channel

    Returns:
        Tuple of (analysis, outreach) dicts. Either can be None if failed.
    """
    prefix = get_role_file_prefix(role_title)

    print(f"\n  [Stage 4] {role_title} at {company_name}")

    # Check if already exists
    if check_role_outreach_exists(output_dir, company_name, role_title):
        print(f"    Already generated, skipping...")
        folder = get_contact_folder(output_dir, company_name)
        analysis_file = os.path.join(folder, f"{prefix}_analysis.json")
        with open(analysis_file, "r") as f:
            analysis = json.load(f)
        return analysis, None

    # Load company scoring from Stage 2
    company_scoring = load_company_scoring(base_dir, company_name)
    if not company_scoring:
        print(f"    Scoring not found for {company_name}")
        return None, None

    # Load target roles from Stage 3
    target_roles = load_target_roles(base_dir, company_name)
    if not target_roles or "target_roles" not in target_roles:
        print(f"    Target roles not found for {company_name}")
        return None, None

    # TURN 1: Role Analysis
    print(f"    [Turn 1] Analyzing role...")

    analysis_user_message = f"""
Based on the instructions provided and context below, develop an engagement strategy for the target role at this company, providing the output in the JSON format specified above.

TARGET ROLE: {role_title}
COMPANY: {company_name}

COMPANY SCORING DATA (from Stage 2):
{json.dumps(company_scoring, indent=2)}

TARGET ROLES ANALYSIS (from Stage 3):
{json.dumps(target_roles["target_roles"], indent=2)}
"""

    try:
        response = call_claude_conversation(
            system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": analysis_user_message}],
            model=MODELS.get("contact_analysis", "claude-sonnet-4-5-20250929"),
        )

        analysis = extract_json_from_response(response)

        # Save analysis
        folder = get_contact_folder(output_dir, company_name)
        os.makedirs(folder, exist_ok=True)
        analysis_file = os.path.join(folder, f"{prefix}_analysis.json")
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        print(f"    [Turn 1] Analysis complete")
        print(f"      Recommended channel: {analysis.get('recommended_channel', 'N/A')}")

    except Exception as e:
        print(f"    [Turn 1] Error: {e}")
        return None, None

    if not analysis:
        return None, None

    # TURN 2: Outreach Generation
    channel = force_channel or analysis.get("recommended_channel", "email")

    if channel == "linkedin":
        turn2_message = OUTREACH_LINKEDIN_SYSTEM_PROMPT
    else:
        turn2_message = OUTREACH_EMAIL_SYSTEM_PROMPT

    print(f"    [Turn 2] Generating {channel} message...")

    messages = [
        {"role": "user", "content": analysis_user_message},
        {"role": "assistant", "content": json.dumps(analysis, indent=2)},
        {"role": "user", "content": turn2_message},
    ]

    try:
        response = call_claude_conversation(
            system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
            messages=messages,
            model=MODELS.get("outreach_generation", "claude-sonnet-4-5-20250929"),
        )

        outreach = extract_json_from_response(response)

        # Save outreach
        outreach_file = os.path.join(folder, f"{prefix}_outreach.json")
        with open(outreach_file, "w") as f:
            json.dump(outreach, f, indent=2)

        print(f"    [Turn 2] {channel.capitalize()} message generated")

        if channel == "email" and "message" in outreach:
            print(f"      Subject: {outreach['message'].get('subject', '')}")

        return analysis, outreach

    except Exception as e:
        print(f"    [Turn 2] Error: {e}")
        return analysis, None


# SINGLE CONTACT PROCESSING (Two-Turn Conversation)
#
# Turn 1: Contact Analysis & Engagement Strategy
# Turn 2: Outreach Message Generation (email or LinkedIn based on Turn 1)

def process_contact(
    contact_name: str,
    title: str,
    company_name: str,
    base_dir: str = "data/companies",
    output_dir: str = "data/contacts",
    force_channel: Optional[str] = None,
) -> Tuple[Optional[dict], Optional[dict]]:
    """
    Process a single contact through analysis and outreach as a two-turn conversation.

    Turn 1: Analyze contact and develop engagement strategy
    Turn 2: Generate outreach message (channel determined by Turn 1 or force_channel)

    Args:
        contact_name: Contact's full name
        title: Contact's job title
        company_name: Company name
        base_dir: Directory with company data from Stage 2 & 3
        output_dir: Directory to save contact analysis and outreach
        force_channel: Override recommended channel ("email" or "linkedin")

    Returns:
        Tuple of (analysis, outreach) dicts. Either can be None if failed/skipped.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {contact_name} ({title}) at {company_name}")
    print(f"{'='*60}")

    # Check if both already exist
    if check_analysis_exists(output_dir, company_name, contact_name) and \
       check_outreach_exists(output_dir, company_name, contact_name):
        print(f"  [Turn 1] ✓ Analysis already exists, loading...")
        print(f"  [Turn 2] ✓ Outreach already exists, skipping...")
        analysis = load_analysis(output_dir, company_name, contact_name)
        return analysis, None

    # Load company scoring from Stage 2
    company_research = load_company_scoring(base_dir, company_name)
    if not company_research:
        print(f"  ✗ Company scoring not found for {company_name}")
        return None, None

    # Load target roles from Stage 3
    target_roles = load_target_roles(base_dir, company_name)
    if not target_roles or "target_roles" not in target_roles:
        print(f"  ✗ Target roles not found for {company_name}")
        return None, None

    # TURN 1: Contact Analysis
    # Check if analysis already exists (but outreach doesn't)
    if check_analysis_exists(output_dir, company_name, contact_name):
        print(f"  [Turn 1] ✓ Analysis already exists, loading...")
        analysis = load_analysis(output_dir, company_name, contact_name)
    else:
        print(f"  [Turn 1] Analyzing contact...")

        analysis_user_message = f"""
Based on the instructions provided and context provided below, develop an engagement strategy specific to this contact, providing the output in the JSON format specified above.

CONTACT INFORMATION:
- Name: {contact_name}
- Title: {title}
- Company: {company_name}

COMPANY RESEARCH (from Stage 2):
{json.dumps(company_research, indent=2)}

TARGET ROLES ANALYSIS (from Stage 3):
{json.dumps(target_roles["target_roles"], indent=2)}
"""

        try:
            response = call_claude_conversation(
                system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": analysis_user_message}],
                model=MODELS.get("contact_analysis", "claude-sonnet-4-5-20250929"),
            )

            analysis = extract_json_from_response(response)
            save_analysis(output_dir, company_name, contact_name, analysis)
            print(f"  [Turn 1] ✓ Analysis complete")
            print(f"    Recommended channel: {analysis.get('recommended_channel', 'N/A')}")

        except Exception as e:
            print(f"  [Turn 1] ✗ Error: {e}")
            return None, None

    if not analysis:
        return None, None

    # Check if outreach already exists
    if check_outreach_exists(output_dir, company_name, contact_name):
        print(f"  [Turn 2] ✓ Outreach already exists, skipping...")
        return analysis, None

    # TURN 2: Outreach Generation
    channel = force_channel or analysis.get("recommended_channel", "email")

    # Select turn 2 message based on channel
    if channel == "linkedin":
        turn2_message = OUTREACH_LINKEDIN_SYSTEM_PROMPT
    else:
        turn2_message = OUTREACH_EMAIL_SYSTEM_PROMPT

    print(f"  [Turn 2] Generating {channel} message...")

    # Build two-turn conversation
    analysis_user_message = f"""
Based on the instructions provided and context provided below, develop an engagement strategy specific to this contact, providing the output in the JSON format specified above.

CONTACT INFORMATION:
- Name: {contact_name}
- Title: {title}
- Company: {company_name}

COMPANY RESEARCH (from Stage 2):
{json.dumps(company_research, indent=2)}

TARGET ROLES ANALYSIS (from Stage 3):
{json.dumps(target_roles["target_roles"], indent=2)}
"""

    messages = [
        {"role": "user", "content": analysis_user_message},
        {"role": "assistant", "content": json.dumps(analysis, indent=2)},
        {"role": "user", "content": turn2_message},
    ]

    try:
        response = call_claude_conversation(
            system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
            messages=messages,
            model=MODELS.get("outreach_generation", "claude-sonnet-4-5-20250929"),
        )

        outreach = extract_json_from_response(response)
        save_outreach(output_dir, company_name, contact_name, outreach)
        print(f"  [Turn 2] ✓ {channel.capitalize()} message generated")

        if channel == "email" and "message" in outreach:
            print(f"    Subject: {outreach['message'].get('subject', '')}")

        return analysis, outreach

    except Exception as e:
        print(f"  [Turn 2] ✗ Error: {e}")
        return analysis, None


# BATCH PROCESSING

def run_stage4_outreach_generation(
    contacts: List[Dict[str, str]],
    base_dir: str = "data/companies",
    output_dir: str = "data/contacts",
    force_channel: Optional[str] = None,
    delay_seconds: int = 2,
) -> Dict[str, any]:
    """
    Run Stage 4: Outreach Generation for multiple contacts.

    Args:
        contacts: List of dicts with keys: name, title, company_name
        base_dir: Directory with company research and target roles
        output_dir: Directory to save contact analyses and outreach
        force_channel: Override recommended channel for all contacts
        delay_seconds: Delay between processing contacts (rate limiting)

    Returns:
        Summary dict with processing results
    """
    print(f"\n{'='*70}")
    print(f"STAGE 4: OUTREACH GENERATION")
    print(f"{'='*70}")
    print(f"Processing {len(contacts)} contacts")
    print(f"Base directory: {base_dir}")
    print(f"Output directory: {output_dir}")
    if force_channel:
        print(f"Force channel: {force_channel}")
    print()

    results = {
        "total_contacts": len(contacts),
        "successful_analyses": 0,
        "successful_outreach": 0,
        "failed": 0,
        "skipped": 0,
        "contacts_processed": []
    }

    for i, contact in enumerate(contacts):
        contact_name = contact.get("name")
        title = contact.get("title")
        company_name = contact.get("company_name")

        if not all([contact_name, title, company_name]):
            print(f"⚠ Skipping contact {i+1}: Missing required fields (name, title, company_name)")
            results["skipped"] += 1
            continue

        try:
            analysis, outreach = process_contact(
                contact_name=contact_name,
                title=title,
                company_name=company_name,
                base_dir=base_dir,
                output_dir=output_dir,
                force_channel=force_channel,
            )

            contact_result = {
                "name": contact_name,
                "title": title,
                "company": company_name,
                "analysis_success": analysis is not None,
                "outreach_success": outreach is not None,
            }

            if analysis:
                results["successful_analyses"] += 1
                contact_result["recommended_channel"] = analysis.get("recommended_channel")

            if outreach:
                results["successful_outreach"] += 1

            if not analysis:
                results["failed"] += 1

            results["contacts_processed"].append(contact_result)

            # Rate limiting between contacts
            if i < len(contacts) - 1:
                time.sleep(delay_seconds)

        except Exception as e:
            print(f"✗ Error processing {contact_name}: {e}")
            results["failed"] += 1
            results["contacts_processed"].append({
                "name": contact_name,
                "title": title,
                "company": company_name,
                "analysis_success": False,
                "outreach_success": False,
                "error": str(e)
            })

    # Print summary
    print(f"\n{'='*70}")
    print(f"STAGE 4 SUMMARY")
    print(f"{'='*70}")
    print(f"Total contacts: {results['total_contacts']}")
    print(f"Successful analyses: {results['successful_analyses']}")
    print(f"Successful outreach: {results['successful_outreach']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    print()

    return results


# CLI FOR TESTING

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Stage 4: Outreach Generation - Analyze contacts and generate personalized outreach"
    )
    parser.add_argument("--name", required=True, help="Contact name (e.g., 'John Smith')")
    parser.add_argument("--title", required=True, help="Contact title (e.g., 'VP of Product Development')")
    parser.add_argument("--company", required=True, help="Company name (must match Stage 2/3 data)")
    parser.add_argument("--base-dir", default="data/companies", help="Base directory with company data")
    parser.add_argument("--output-dir", default="data/contacts", help="Output directory for contact data")
    parser.add_argument("--force-channel", choices=["email", "linkedin"], help="Force specific channel (overrides recommendation)")

    args = parser.parse_args()

    # Single contact mode for testing
    print(f"\nStage 4: Testing with single contact")
    print(f"Contact: {args.name}")
    print(f"Title: {args.title}")
    print(f"Company: {args.company}")
    print()

    analysis, outreach = process_contact(
        contact_name=args.name,
        title=args.title,
        company_name=args.company,
        base_dir=args.base_dir,
        output_dir=args.output_dir,
        force_channel=args.force_channel,
    )

    if analysis:
        print(f"\n✓ Analysis saved to: {get_contact_folder(args.output_dir, args.company)}/{get_contact_file_prefix(args.name)}_analysis.json")
    if outreach:
        print(f"✓ Outreach saved to: {get_contact_folder(args.output_dir, args.company)}/{get_contact_file_prefix(args.name)}_outreach.json")
