import os
import json
from typing import Optional, List, Tuple
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import MODELS, sanitize_name
from prompts import (
    CONTACT_ANALYSIS_SYSTEM_PROMPT,
    OUTREACH_EMAIL_SYSTEM_PROMPT,
    OUTREACH_LINKEDIN_SYSTEM_PROMPT,
)
from utils.llm import call_claude, extract_json_from_response
from utils.io import load_json, save_json, company_path


def _contact_path(companies_dir: str, company_name: str, role_title: str, suffix: str) -> str:
    """Generate path for contact files under companies/{company}/contacts/."""
    prefix = sanitize_name(role_title).replace(" ", "_")
    return company_path(companies_dir, company_name, f"contacts/{prefix}_{suffix}.json")


def _role_already_processed(companies_dir: str, company_name: str, role_title: str) -> bool:
    """Check if both analysis and outreach exist for this role."""
    analysis_path = _contact_path(companies_dir, company_name, role_title, "analysis")
    outreach_path = _contact_path(companies_dir, company_name, role_title, "outreach")
    return os.path.exists(analysis_path) and os.path.exists(outreach_path)


class OutreachAgent:
    """Processes all target roles for a company in a single multi-turn conversation."""

    def __init__(
        self,
        company_name: str,
        website_url: str,
        target_roles: List[dict],
        companies_dir: str = "data/companies",
    ):
        self.company_name = company_name
        self.website_url = website_url
        self.target_roles = target_roles
        self.companies_dir = companies_dir

        self.scoring_data = load_json(company_path(companies_dir, company_name, "scoring.json"))
        self.target_roles_data = load_json(company_path(companies_dir, company_name, "target_roles.json"))
        self.messages: List[dict] = []
        self.stats = {"roles_processed": 0, "roles_skipped": 0, "errors": []}

    def _build_company_context(self) -> str:
        """Build company context string (sent once at start of conversation)."""
        return f"""COMPANY CONTEXT (for all roles in this conversation):

Company: {self.company_name}
Website: {self.website_url}

SCORING DATA:
{json.dumps(self.scoring_data, indent=2)}

TARGET ROLES:
{json.dumps(self.target_roles_data, indent=2)}

---
You will now analyze and generate outreach for multiple roles at this company.
The company context above applies to ALL roles. Do not ask for it again.
"""

    # STEP 4.1: ANALYZE ROLE + STEP 4.2: GENERATE OUTREACH

    def _process_role(self, role: dict, is_first_role: bool) -> Tuple[Optional[dict], Optional[dict]]:
        role_title = role.get("title", "")

        # Check if already processed
        if _role_already_processed(self.companies_dir, self.company_name, role_title):
            print(f"    [{role_title}] Already processed, skipping")
            self.stats["roles_skipped"] += 1
            return None, None

        print(f"    [{role_title}] Analyzing...")

        # Build the user message for this role
        if is_first_role:
            # First role: include full company context
            user_message = f"""{self._build_company_context()}

Now analyze the first role:

ROLE: {role_title}

Develop an engagement strategy for this role. Return JSON as specified in your instructions."""
        else:
            # Subsequent roles: context already in conversation
            user_message = f"""Now analyze the next role:

ROLE: {role_title}

Develop an engagement strategy for this role. Return JSON as specified in your instructions."""

        # Turn 1: Analysis
        self.messages.append({"role": "user", "content": user_message})

        try:
            response = call_claude(
                system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
                messages=self.messages,
                model=MODELS["contact_analysis"],
            )
            analysis = extract_json_from_response(response)
        except Exception as e:
            print(f"    [{role_title}] Analysis error: {e}")
            self.stats["errors"].append({"role": role_title, "stage": "analysis", "error": str(e)})
            # Remove the failed user message
            self.messages.pop()
            return None, None

        if not analysis or "error" in analysis:
            print(f"    [{role_title}] Analysis failed: {analysis.get('error', 'Unknown error')}")
            self.stats["errors"].append({"role": role_title, "stage": "analysis", "error": str(analysis)})
            self.messages.pop()
            return None, None

        # Add assistant response to conversation
        self.messages.append({"role": "assistant", "content": json.dumps(analysis, indent=2)})

        print(f"    [{role_title}] Analysis complete, generating outreach...")

        # Turn 2: Outreach generation
        channel = analysis.get("recommended_channel", "email")
        outreach_prompt = OUTREACH_LINKEDIN_SYSTEM_PROMPT if channel == "linkedin" else OUTREACH_EMAIL_SYSTEM_PROMPT

        self.messages.append({"role": "user", "content": outreach_prompt})

        try:
            response = call_claude(
                system_prompt=CONTACT_ANALYSIS_SYSTEM_PROMPT,
                messages=self.messages,
                model=MODELS["outreach_generation"],
            )
            outreach = extract_json_from_response(response)
        except Exception as e:
            print(f"    [{role_title}] Outreach error: {e}")
            self.stats["errors"].append({"role": role_title, "stage": "outreach", "error": str(e)})
            # Remove the outreach request, keep the analysis
            self.messages.pop()
            return analysis, None

        if not outreach or "error" in outreach:
            print(f"    [{role_title}] Outreach failed: {outreach.get('error', 'Unknown error')}")
            self.stats["errors"].append({"role": role_title, "stage": "outreach", "error": str(outreach)})
            self.messages.pop()
            return analysis, None

        # Add outreach response to conversation
        self.messages.append({"role": "assistant", "content": json.dumps(outreach, indent=2)})

        # Save results
        analysis_path = _contact_path(self.companies_dir, self.company_name, role_title, "analysis")
        outreach_path = _contact_path(self.companies_dir, self.company_name, role_title, "outreach")

        save_json(analysis_path, analysis)
        save_json(outreach_path, outreach)

        self.stats["roles_processed"] += 1
        print(f"    [{role_title}] Complete ({channel} outreach generated)")

        return analysis, outreach

    def run(self) -> dict:
        """Process all target roles in a single multi-turn conversation."""
        print(f"\n[Outreach Agent] {self.company_name} ({len(self.target_roles)} roles)")

        if not self.scoring_data:
            print(f"  Error: No scoring data found")
            self.stats["errors"].append({"role": "all", "stage": "init", "error": "No scoring data"})
            return self.stats

        if not self.target_roles:
            print(f"  No target roles to process")
            return self.stats

        # Process each role in sequence (within same conversation)
        for i, role in enumerate(self.target_roles):
            role_title = role.get("title", "")
            if not role_title:
                continue

            self._process_role(role, i == 0)

        print(f"\n[Outreach Agent] {self.company_name} COMPLETE - "
              f"Processed: {self.stats['roles_processed']}, Skipped: {self.stats['roles_skipped']}, "
              f"Errors: {len(self.stats['errors'])}, Turns: {len(self.messages)}")
        return self.stats


def process_company_outreach(
    company_name: str, website_url: str, target_roles: List[dict],
    companies_dir: str = "data/companies",
) -> dict:
    """Process all roles for a company using OutreachAgent."""
    return OutreachAgent(company_name, website_url, target_roles, companies_dir).run()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python outreach_agent.py <company_name>")
        sys.exit(1)
    company = sys.argv[1]
    roles_data = load_json(company_path("data/companies", company, "target_roles.json"))
    scoring = load_json(company_path("data/companies", company, "scoring.json"))
    if not roles_data:
        print(f"No target_roles.json found for {company}")
        sys.exit(1)
    process_company_outreach(company, scoring.get("website_url", "") if scoring else "",
                             roles_data.get("target_roles", []))
