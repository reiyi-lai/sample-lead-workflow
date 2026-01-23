# Define models to use for each task based on complexity to optimize cost and performance

MODELS = {
    # Stage 1
    "event_discovery": "claude-sonnet-4-5-20250929",
    "event_scoring": "claude-haiku-4-5-20251001",
    "company_discovery": "claude-sonnet-4-5-20250929",

    # Stage 2
    "company_research": "claude-sonnet-4-5-20250929",
    "company_scoring": "claude-sonnet-4-5-20250929",

    # Stage 3
    "target_role_identification": "claude-sonnet-4-5-20250929",

    # Stage 4
    "contact_analysis": "claude-sonnet-4-5-20250929",
    "outreach_generation": "claude-sonnet-4-5-20250929",
}

TEDLAR_CONTEXT = """
You are leading DuPont Tedlar's Graphics & Signage go-to-market initiative.
Your role is to identify and qualify leads for Tedlar's protective film products.

PRODUCT INFORMATION:
DuPont Tedlar is a portfolio of polyvinyl fluoride (PVF) protective films with 60+ years of proven performance, used as overlaminates for:
  • Signs and graphics (outdoor and indoor)
  • Vehicle wraps and fleet graphics  
  • Architectural graphics and building wraps
  • Wall protection or covering
  • Transit and rail interiors

VALUE PROPOSITIONS:
  • Extreme Durability: 12-20+ year outdoor lifespan (industry-leading)
  • UV Protection: No yellowing, fading, cracking, or color degradation
  • Graffiti Resistance: Spray paint, permanent markers, stickers clean off easily
  • Weather resistance: -70°F to 230°F operating range, mold & mildew resistant
  • Reduced total cost of ownership: Fewer replacements, lower maintenance

IDEAL CUSTOMER PROFILE (ICP):

  Industry Verticals:
    • Sign manufacturers and fabricators
    • Large-format print and graphics companies
    • Vehicle wrap installers and manufacturers
    • Architectural panel and building facade producers
    • Protective film distributors and converters
    • Wall Protection/Covering & Interior Solutions
    • Transit and bus/rail interiors
    • Outdoor advertising and signage

  Company Size:
    • Mid-market to Enterprise ($50M+ annual revenue preferred)
    • 50+ employees typical

  Geographic Focus:
    • US-based companies (primary)
    • Global presence is a positive signal

  Buying Signals:
    • Markets outdoor or durable products
    • Emphasizes quality, longevity, or premium positioning
    • Recent product launches in outdoor/architectural space

  Pain Points We Solve:
    • Durability issues with current overlaminates or films
    • Warranty claims from premature product degradation
    • Customer complaints about UV damage, fading, cracking
    • Graffiti vandalism on installed graphics
    • High replacement and maintenance costs
    • Need for competitive differentiation in premium segment
"""
CLAY_WEBHOOK_URL = "https://api.clay.com/v3/sources/webhook/pull-in-data-from-a-webhook-7015fada-05a6-4365-8523-36a8e05fa1fd"

# Number of contacts to find per tier
CONTACTS_PER_TIER = {
    1: 3,  # Tier 1 (High Priority): 3 contacts
    2: 2,  # Tier 2 (Medium Priority): 2 contacts
}
