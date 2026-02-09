import re

# Define models to use for each task based on complexity to optimize cost and performance

MODELS = {
    # Stage 1
    "event_discovery": "claude-sonnet-4-5-20250929",
    "event_scoring": "claude-haiku-4-5-20251001",
    "company_discovery": "claude-sonnet-4-5-20250929",

    # Stage 2
    "company_research": "claude-sonnet-4-5-20250929",

    # Stage 3
    "target_role_identification": "claude-sonnet-4-5-20250929",

    # Stage 4
    "contact_analysis": "claude-sonnet-4-5-20250929",
    "outreach_generation": "claude-sonnet-4-5-20250929",
}

CLAY_WEBHOOK_URL = "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-7015fada-05a6-4365-8523-36a8e05fa1fd"

# ICP scoring weights for Company Qualification in Stage 2
ICP_WEIGHTS = {
    "industry_fit": 0.30,
    "size_revenue_fit": 0.25,
    "strategic_relevance": 0.20,
    "market_activity": 0.25,
}

# Minimum event score (0-10) to proceed to company discovery (Stage 1.3)
EVENT_SCORE_CUTOFF = 8

# Minimum company ICP score (0-100) to proceed to role identification (Stage 3)
COMPANY_SCORE_CUTOFF = 70


def sanitize_name(name: str) -> str:
    """Convert a name (company, contact, event) to a safe folder/filename.
    Removes special characters except word chars, spaces, and hyphens,
    then collapses whitespace.
    """
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()
