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


# =============================================================================
# FILE MANAGEMENT HELPERS
# =============================================================================

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


# =============================================================================
# LOAD STAGE 2 & 3 DATA
# =============================================================================

def load_company_research(base_dir: str, company_name: str) -> Optional[dict]:
    """Load company research from Stage 2."""
    from stage2_company_qualification import get_company_folder

    company_folder = get_company_folder(base_dir, company_name)
    research_file = os.path.join(company_folder, "research.json")

    if os.path.exists(research_file):
        with open(research_file, "r") as f:
            return json.load(f)
    return None


def load_target_roles(base_dir: str, company_name: str) -> Optional[dict]:
    """Load target roles from Stage 3."""
    from stage3_contact_finding import load_target_roles_json

    return load_target_roles_json(company_name, base_dir)


# =============================================================================
# STEP 4.1: CONTACT ANALYSIS & ENGAGEMENT STRATEGY
# =============================================================================

def analyze_contact(
    contact_name: str,
    title: str,
    company_name: str,
    base_dir: str = "data/companies",
    output_dir: str = "data/contacts",
) -> Optional[dict]:
    """
    Step 4.1: Analyze contact and develop engagement strategy.

    Args:
        contact_name: Contact's full name
        title: Contact's job title
        company_name: Company name
        base_dir: Directory with company research and target roles
        output_dir: Directory to save analysis

    Returns:
        Analysis dict with engagement strategy or None if failed
    """
    # Check if analysis already exists
    if check_analysis_exists(output_dir, company_name, contact_name):
        print(f"  [Step 4.1] ✓ Analysis already exists, loading from file...")
        return load_analysis(output_dir, company_name, contact_name)

    # Load company research from Stage 2
    company_research = load_company_research(base_dir, company_name)
    if not company_research:
        print(f"  [Step 4.1] ✗ Company research not found for {company_name}")
        print(f"    Make sure Stage 2 has been run for this company")
        return None

    # Load target roles from Stage 3
    target_roles = load_target_roles(base_dir, company_name)
    if not target_roles or "target_roles" not in target_roles:
        print(f"  [Step 4.1] ✗ Target roles not found for {company_name}")
        print(f"    Make sure Stage 3 has been run for this company")
        return None

    # Prepare user message for LLM
    user_message = f"""
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

    print(f"  [Step 4.1] Analyzing contact with LLM...")

    try:
        response = call_claude_conversation(
            system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            model=MODELS.get("outreach_generation", "claude-sonnet-4-5-20250929"),
        )

        # Parse JSON response (handles markdown code blocks)
        analysis = extract_json_from_response(response)

        # Save analysis
        save_analysis(output_dir, company_name, contact_name, analysis)
        print(f"  [Step 4.1] ✓ Analysis complete")
        print(f"    Recommended channel: {analysis.get('recommended_channel', 'N/A')}")

        return analysis

    except Exception as e:
        print(f"  [Step 4.1] ✗ Error parsing response: {e}")
        print(f"  Response preview: {response[:500] if response else 'No response'}")
        return None


# =============================================================================
# STEP 4.2: OUTREACH MESSAGE GENERATION
# =============================================================================

def generate_outreach(
    contact_name: str,
    company_name: str,
    output_dir: str = "data/contacts",
    force_channel: Optional[str] = None,
) -> Optional[dict]:
    """
    Step 4.2: Generate outreach message based on analysis.

    Args:
        contact_name: Contact's full name
        company_name: Company name
        output_dir: Directory to load analysis and save outreach
        force_channel: Override recommended channel ("email" or "linkedin")

    Returns:
        Outreach dict with message or None if failed/skipped
    """
    # Check if outreach already exists
    if check_outreach_exists(output_dir, company_name, contact_name):
        print(f"  [Step 4.2] ✓ Outreach already exists, skipping...")
        return None

    # Load analysis from Step 4.1
    analysis = load_analysis(output_dir, company_name, contact_name)
    if not analysis:
        print(f"  [Step 4.2] ✗ Analysis not found for {contact_name}")
        print(f"    Run Step 4.1 first to generate analysis")
        return None

    # Determine channel (use force_channel if provided, otherwise use recommendation)
    channel = force_channel or analysis.get("recommended_channel", "email")

    # Select appropriate prompt based on channel
    if channel == "linkedin":
        system_prompt = OUTREACH_LINKEDIN_SYSTEM_PROMPT
    else:
        system_prompt = OUTREACH_EMAIL_SYSTEM_PROMPT

    # Prepare user message
    user_message = f"""
Generate a {channel} message based on this contact analysis:

{json.dumps(analysis, indent=2)}

Please write a personalized {channel} message following the output format.
"""

    print(f"  [Step 4.2] Generating {channel} message with LLM...")

    try:
        response = call_claude_conversation(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            model=MODELS.get("outreach_generation", "claude-sonnet-4-5-20250929"),
        )

        # Parse JSON response (handles markdown code blocks)
        outreach = extract_json_from_response(response)

        # Save outreach
        save_outreach(output_dir, company_name, contact_name, outreach)
        print(f"  [Step 4.2] ✓ {channel.capitalize()} message generated")

        # Print preview
        if channel == "email" and "message" in outreach:
            subject = outreach["message"].get("subject", "")
            print(f"    Subject: {subject}")

        return outreach

    except Exception as e:
        print(f"  [Step 4.2] ✗ Error parsing response: {e}")
        print(f"  Response preview: {response[:500] if response else 'No response'}")
        return None


# =============================================================================
# SINGLE CONTACT PROCESSING
# =============================================================================

def process_contact(
    contact_name: str,
    title: str,
    company_name: str,
    base_dir: str = "data/companies",
    output_dir: str = "data/contacts",
    force_channel: Optional[str] = None,
) -> Tuple[Optional[dict], Optional[dict]]:
    """
    Process a single contact through both analysis and outreach steps.

    Args:
        contact_name: Contact's full name
        title: Contact's job title
        company_name: Company name
        base_dir: Directory with company data from Stage 2 & 3
        output_dir: Directory to save contact analysis and outreach
        force_channel: Override recommended channel

    Returns:
        Tuple of (analysis, outreach) dicts. Either can be None if failed/skipped.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {contact_name} ({title}) at {company_name}")
    print(f"{'='*60}")

    # Step 4.1: Contact Analysis
    analysis = analyze_contact(
        contact_name=contact_name,
        title=title,
        company_name=company_name,
        base_dir=base_dir,
        output_dir=output_dir,
    )

    if not analysis:
        print(f"✗ Failed to analyze contact")
        return None, None

    # Step 4.2: Outreach Generation
    outreach = generate_outreach(
        contact_name=contact_name,
        company_name=company_name,
        output_dir=output_dir,
        force_channel=force_channel,
    )

    return analysis, outreach


# =============================================================================
# BATCH PROCESSING
# =============================================================================

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


# =============================================================================
# CLI FOR TESTING
# =============================================================================

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
