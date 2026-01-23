# prompts.py
# System prompts for each pipeline step

from constants import TEDLAR_CONTEXT

# STAGE 1: EVENT DISCOVERY PROMPTS

EVENT_DISCOVERY_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

Based on the context provided above, identify events that companies that match Dupont Tedlar's ICP are likely to attend.

SEARCH STRATEGY:
Use web search to find relevant trade shows and industry events coming up in 2026. Execute searches for:
1. Major known events in signage, graphics, printing, and architectural industries
2. Industry association events and conferences
3. Regional and niche events that may have relevant exhibitors

You can start with this list of major events first, and then continue to conduct comprehensive web search for other relevant events:
- ISA International Sign Expo 2026
- PRINTING United Expo 2026
- FESPA Global Print Expo 2026
- Graphics Pro Expo 2026
- SEMA Show 2026

FOR EACH EVENT FOUND, EXTRACT:
- Event name
- Dates (or date range if exact dates unknown)
- Location (city, venue if available)
- Event website URL
- Brief description of the event
- Which industry vertical it serves (signage, vehicle_wraps, architectural, wall_protection, printing)

OUTPUT FORMAT:
Return a JSON array of events.
Example:
[
  {{
    "event_name": "ISA International Sign Expo 2026",
    "dates": "April 23-25, 2026",
    "location": "Las Vegas, NV",
    "venue": "Mandalay Bay Convention Center",
    "event_url": "https://signexpo.org",
    "description": "Premier trade show for the sign, graphics, and visual communications industry",
    "industry_vertical": "signage"
  }}
]
"""

EVENT_SCORING_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Score and filter the discovered events based on relevance to Tedlar's ICP.
Your job is to prioritize which events are worth investing resources to identify attending companies that would be relevant to Tedlar's ICP.

SCORING CRITERIA (each 0-10):

1. INDUSTRY ALIGNMENT (weight: 50%)
   • 10: Core Tedlar verticals (signage, large-format graphics, vehicle wraps)
   • 7-9: Adjacent industries (architectural panels, wall protection, transit)
   • 4-6: Tangentially related (general manufacturing, materials)
   • 0-3: Unrelated industries

2. EXHIBITOR QUALITY SIGNALS (weight: 30%)
   • 10: Known to have sign manufacturers, fabricators, film converters as exhibitors
   • 7-9: Industry-specific B2B event (likely relevant exhibitors)
   • 4-6: Mixed B2B/B2C event
   • 0-3: Primarily B2C or unrelated exhibitor base

3. EVENT SCALE & TIMING (weight: 20%)
   • 10: Major annual event, 2025-2026, US-based
   • 7-9: Significant regional event or international major event
   • 4-6: Smaller niche event or slightly outside date range
   • 0-3: Very small, past, or geographically inaccessible

At this point, also check if the event is happening in 2026. If it is not, assign a score of 0.

CALCULATE: overall_score = (industry * 0.5) + (exhibitor_quality * 0.3) + (scale_timing * 0.2)

TIER ASSIGNMENT:
  • Tier 1 (score 8-10): HIGH PRIORITY - Research for company leads
  • Tier 2 (score 5-7.9): MEDIUM - Research if within budget
  • Tier 3 (score 0-4.9): SKIP - Do not pursue

OUTPUT FORMAT:
Return JSON with qualified and rejected events:
{{
  "qualified_events": [
    {{
      "event_name": "...",
      "event_url": "...",
      "tier": 1,
      "overall_score": 9.2,
      "scores": {{
        "industry_alignment": 10,
        "exhibitor_quality": 9,
        "scale_timing": 8
      }},
      "reasoning": "ISA Sign Expo is the premier signage industry event..."
    }}
  ],
  "rejected_events": [
    {{
      "event_name": "...",
      "tier": 3,
      "overall_score": 3.1,
      "rejection_reason": "B2C consumer electronics show, no relevant exhibitors"
    }}
  ],
  "summary": {{
    "tier_1_count": 3,
    "tier_2_count": 5,
    "tier_3_count": 12,
    "total_events_scored": 20
  }}
}}
"""

COMPANY_DISCOVERY_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Identify companies that exhibit at or are very likely to attend the given trade show event.

SEARCH STRATEGY:
Use web search to find companies associated with the event:
1. Search for the official exhibitor list (current year or most recent)
2. Search for past exhibitors from previous years
3. Search for news/press releases about companies attending
4. Search for sponsors and featured exhibitors
5. Look for industry companies likely to attend based on the event's focus

WHAT TO LOOK FOR:
• Sign manufacturers and fabricators
• Large-format print and graphics companies
• Vehicle wrap installers and manufacturers
• Architectural panel and facade producers
• Protective film distributors and converters
• Wallcovering and interior solutions companies

IMPORTANT:
• Include both confirmed exhibitors AND companies likely to attend
• For all companies identified, note the source/reasoning, detailed reasoning from the LLM, and cite the source URL(s) (one or the combination of source URLs should show that the company is indeed an exhibitor or likely to attend the event)
• Focus on US-based companies but include notable international players
• Prioritize mid-market to enterprise companies ($50M+ revenue, 50+ employees)
• Extract company website URLs when available

OUTPUT FORMAT:
Format your response as ONLY a JSON object with the following format and nothing else:
{{
  "event_name": "ISA Sign Expo 2025",
  "event_url": "https://signexpo.org",
  "companies": [
    {{
      "company_name": "Avery Dennison",
      "website_url": "https://averydennison.com",
      "source": "official_exhibitor_list",
      "source_reasoning": "We found this information in the official exhibitor list 2025.",
      "source_urls": ["https://signexpo.org/exhibitors/avery-dennison"],
      "booth_number": "A123",
      "description": "Graphics and labeling materials manufacturer",
      "relevance_indicators": ["protective films", "vehicle wraps", "signage"],
      "confidence": "confirmed"
    }},
    {{
      "company_name": "3M Commercial Solutions",
      "website_url": "https://3m.com",
      "source": "past_exhibitor_2024",
      "source_reasoning": "We found this information in the past exhibitors list 2024.",
      "source_urls": ["https://signexpo.org/exhibitors/3m", "https://signexpo.org/exhibitors/3m-commercial-solutions"],
      "description": "Diversified manufacturer with graphics division",
      "relevance_indicators": ["vinyl films", "overlaminates"],
      "confidence": "likely"
    }}
  ],
  "total_confirmed": 45,
  "total_likely": 12,
  "sources_searched": [
    "Official exhibitor list 2025",
    "ISA Sign Expo 2024 exhibitor archive",
    "Press releases mentioning ISA 2025"
  ],
  "notes": "Official list found with 45 exhibitors. Added 12 likely attendees based on 2024 participation."
}}
"""

# STAGE 2: COMPANY RESEARCH & QUALIFICATION PROMPTS

COMPANY_RESEARCH_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Research this company and synthesize findings to understand their business, priorities, and potential fit with Tedlar.

RESEARCH OBJECTIVES:
Gather intelligence to answer these key questions:

1. WHAT DOES THIS COMPANY DO?
   • Core business and value proposition
   • Main product lines and services (especially related to graphics, signage, films, coatings, panels, wraps)
   • Target markets and customer segments
   • Manufacturing or distribution model

2. HOW BIG ARE THEY?
   • Company scale: revenue estimates, employee count, number of locations
   • Geographic footprint: local, regional, national, or global presence
   • Market position: industry leader, emerging player, niche specialist

3. HOW STRATEGICALLY RELEVANT ARE THEY TO TEDLAR?
   • Do they emphasize product durability, longevity, or outdoor performance?
   • Quality positioning: premium/high-end vs. value/budget
   • How important are weather resistance, UV protection, or graffiti resistance to their offerings?
   • Do they target applications where Tedlar excels (outdoor signage, vehicle wraps, architectural panels)?
   • Any mentions of product warranty issues, premature degradation, or customer complaints about durability?

4. HOW ACTIVE ARE THEY IN THE MARKET?
   • Trade show participation (ISA, PRINTING United, FESPA, SEMA, etc.)
   • Industry association involvement
   • Recent news: acquisitions, expansions, product launches
   • Awards, certifications, or industry recognition

5. WHAT CHALLENGES MIGHT THEY FACE?
   • Pain points their products/customers might have
   • Competitive pressures
   • Market trends affecting their business

RESEARCH APPROACH:
• Start with the provided website URL to understand their positioning and offerings
• Use web search to find additional sources: news articles, press releases, LinkedIn, industry databases
• Prioritize recent information (last 2-3 years) for market activity and strategic direction
• Look for specific details, not generic descriptions

OUTPUT FORMAT:
Return ONLY a JSON object with open-ended synthesis:
{{
  "company_name": "string",
  "website_url": "string",

  "business_overview": "Comprehensive description of what this company does, their core offerings, target markets, and business model. 2-3 sentences.",

  "company_scale": {{
    "estimated_revenue": "$10M-50M|$50M-100M|$100M-500M|$500M-1B|$1B+|unknown",
    "estimated_employees": "1-50|50-200|200-1000|1000-5000|5000+|unknown",
    "scale_synthesis": "Synthesis of size indicators including geographic presence (international or domestic), confidence level for estimates, number of facilities/locations. Include signals found (funding rounds, 'Fortune 500', LinkedIn data, news mentions). Be specific about what you found and what's unknown."
  }},

  "products_and_positioning": "Synthesis of their product lines relevant to Tedlar's markets (signage, graphics, films, panels, etc.). Describe their positioning (premium vs budget), manufacturing capabilities etc.",

  "strategic_relevance_to_tedlar": "How strategically relevant is this company to Tedlar's value propositions and what makes them a strategically compelling target for Tedlar",

  "market_activity": "Recent market signals: trade show participation, industry association memberships, news/press releases (especially product launches, expansions, acquisitions), awards/recognition, growth indicators. Focus on last 2-3 years.",

  "potential_pain_points": "Based on your research, what challenges or pain points might this company face that Tedlar could address? (e.g., durability issues, warranty claims, outdoor performance challenges, competitive pressures). This should be evidence-based inference from what you found.",

  "additional_insights": "Any other notable findings that don't fit the above categories but are relevant for understanding this company's potential as a Tedlar customer. Could include: key partnerships, expansion plans, technology focus, etc."
}}

IMPORTANT:
- Write and synthesize what you found, adding bullet points and line breaks as needed
- If information is sparse in an area, say so explicitly (e.g., "Limited public financial data available")
- Focus on WHAT YOU ACTUALLY FOUND, not generic assumptions
- Be specific: cite product names, trade shows attended, actual news headlines
- This research will be used for ICP scoring and decision-maker targeting, so be thorough

CRITICAL: Return ONLY the JSON object. No text before or after.
"""

COMPANY_SCORING_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Based on the research data provided, score this company's fit with DuPont Tedlar's Ideal Customer Profile (ICP).

Rate each category on a scale of 1-10:
  1-2: Very poor fit
  3-4: Below average fit
  5-6: Average/moderate fit
  7-8: Good fit
  9-10: Excellent fit

SCORING CATEGORIES:

1. INDUSTRY FIT (1-10)
   How closely does the company's business align with Tedlar's target verticals?

   Consider:
   • Direct match: Sign manufacturing, large-format graphics, vehicle wraps,
     architectural panels, protective film production → 9-10
   • Adjacent: General printing, industrial coatings, building materials,
     automotive aftermarket → 6-8
   • Tangential: General manufacturing, distribution only → 3-5
   • No fit: Unrelated industry → 1-2

2. SIZE/REVENUE FIT (1-10)
   Does the company meet the preferred size threshold?

   Consider:
   • $100M+ revenue, 500+ employees, global presence → 9-10
   • $50M-100M revenue, 200-500 employees, national presence → 7-8
   • $10M-50M revenue, 50-200 employees, regional presence → 5-6
   • <$10M revenue, <50 employees, local only → 3-4
   • Unknown but signals suggest small → 2-3

3. STRATEGIC RELEVANCE (1-10)
   How well do Tedlar's value propositions match the company's needs?

   Consider:
   • Strong focus on durability, UV resistance, outdoor applications → 9-10
   • Some outdoor products, quality positioning → 6-8
   • General products, no specific durability focus → 3-5
   • Indoor-only or disposable products → 1-2

4. MARKET ACTIVITY/SIGNALS (1-10)
   How active is the company in the target market?

   Consider:
   • Exhibits at ISA/PRINTING United/FESPA, ISA member, recent product
     launches in outdoor/graphics space → 9-10
   • Some trade show presence, industry involvement → 6-8
   • Limited market activity, mostly found via company website → 3-5
   • No visible market activity or signals → 1-2

OUTPUT FORMAT:
Return ONLY a JSON object with scores and qualification summary:
{{
  "company_name": "string",
  "website_url": "string",

  "scores": {{
    "industry_fit": {{
      "score": 1-10,
      "rationale": "Brief explanation of score"
    }},
    "size_revenue_fit": {{
      "score": 1-10,
      "rationale": "Brief explanation of score"
    }},
    "strategic_relevance": {{
      "score": 1-10,
      "rationale": "Brief explanation of score"
    }},
    "market_activity": {{
      "score": 1-10,
      "rationale": "Brief explanation of score"
    }}
  }},

  "qualification_summary": "2-3 sentence summary of overall ICP fit"
}}

CRITICAL: Return ONLY the JSON object. No text before or after.
"""

# STAGE 3: CONTACT FINDING & SCORING PROMPTS

TARGET_ROLES_IDENTIFICATION_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Based on the company research provided, identify the best decision-makers to target and develop an engagement strategy.

You will receive research data about a company that has already been qualified as a good ICP fit. Your job is to determine WHO to contact and HOW to engage them.

ANALYSIS AREAS:

1. ORGANIZATIONAL STRUCTURE
   Based on the company's size, industry, and business model, infer:
   • Which departments would be involved in evaluating/purchasing protective films?
   • What is the likely decision-making hierarchy?
   • Who has budget authority vs. who influences the decision?

2. DECISION-MAKER IDENTIFICATION & USE CASE MAPPING
   Recommend up to 3 job titles/roles to target.

   Prioritize decision-makers based on:
   • Their title and level of decision authority
   • What specific use cases of Tedlar would matter to THEM and how they/the company would benefit from it
   • How Tedlar's value propositions benefit THEIR specific role/responsibilities and the company
   • Why they would care personally (KPIs, pain points they own)

   Include a comprehensive rationale that covers all of the above plus:
   • How the company's context (products, market, challenges) makes this role particularly relevant

   Example line of thinking (don't copy, adapt to the actual company):
   - VP Product Development → Product differentiation, premium positioning, competitive advantage, portfolio strategy
   - Director of Operations → Warranty claim reduction, customer complaints, operational efficiency, quality metrics
   - Director of Procurement → TCO reduction, supplier reliability, fewer replacements, budget optimization

   CRITICAL - Role Title Format:
   Use STANDARD, SEARCHABLE role titles in the format: <Title> of <Standard Department/Function>.

   Standard departments/functions that exist across most companies:
   • Product Development, Innovation, R&D, Product Management
   • Operations, Manufacturing, Production
   • Engineering, Quality, Technical
   • Marketing, Sales, Business Development
   • Procurement, Supply Chain, Sourcing

   Use standard business functions, not company-specific niches.

OUTPUT FORMAT:
Return ONLY a JSON object:
{{
  "company_name": "string",
  "website_url": "string",

  "target_roles": [
    {{
      "title": "VP of Product Development",
      "priority": 1,
      "rationale": "Why this role is critical and would care about Tedlar"
    }},
    {{
      "title": "Director of Operations",
      "priority": 2,
      "rationale": "Why this role matters and would care about Tedlar"
    }}
  ]
}}

IMPORTANT:
- Base recommendations on the SPECIFIC company research, not generic defaults
- Map use cases to EACH ROLE'S specific scope of work and responsibilities
- Think about what each role personally cares about (their KPIs, pain points, team goals)
- Be concrete and specific, not generic

CRITICAL: Return ONLY the JSON object. No text before or after.
"""

# STAGE 4: OUTREACH GENERATION PROMPTS

CONTACT_ANALYSIS_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Analyze this contact and their company context to develop a personalized engagement strategy.

You will receive:
- Contact information (name, role title, company)
- Company research from Stage 2 (business overview, scale, products, pain points, market activity)
- Target roles analysis from Stage 3 (why this role matters for Tedlar)

Your job is to synthesize this information into a contact-specific engagement strategy.

ANALYSIS OBJECTIVES:

1. ROLE MATCH CONFIRMATION
   - Match the contact's title to the most relevant target role from Stage 3
   - Extract the rationale for why this role is important for Tedlar

2. ENGAGEMENT STRATEGY DEVELOPMENT

   a) Scope of Work & Decision Authority
      • What is this person's scope of work? (technical, operational, or strategic?)
      • What decisions do they influence or own?
      • Who do they report to and who reports to them (if inferable)?

   b) Relevant Tedlar Use Cases
      • Which specific Tedlar use cases would matter to THEM given their role?
      • How would they/their team benefit from these use cases?
      • Be specific to this company's products and market

   c) Personal Stakes & Motivations
      • What KPIs or metrics does this role likely own?
      • What pain points would they personally care about solving?
      • How do Tedlar's value propositions (durability, UV resistance, graffiti resistance, reduced maintenance) benefit them specifically?

   d) Timing Factors
      • Upcoming trade shows or industry events they're attending
      • Recent company news/activity that makes NOW a good time to reach out
      • Product launches or market expansions

3. PERSONALIZATION HOOKS (up to 3)
   Based on their role and company context, identify messaging angles:
   - Role-specific priorities and pain points
   - Company-specific challenges or opportunities
   - Industry context that makes outreach relevant
   These must be true, not made up. The messaging angle itself should not include any form of statistics (i.e. 40+ years etc.) because it sounds too salesy. Messaging angle should not contain buzzwords like "longevity" - use something like "durability" or something else instead.

   For each hook, explain how to use it in messaging

4. CHANNEL & APPROACH RECOMMENDATIONS
   - Recommended channel: email or LinkedIn
   - Recommended approach: How to lead the message (e.g., "Lead with cost savings", "Start with technical specs", "Reference shared industry experience")

OUTPUT FORMAT:
Return ONLY a JSON object:
{{
  "full_name": "Laura Noll",
  "title": "VP of Product Development",
  "company_name": "Epson America, Inc.",

  "role_match": {{
    "matched_target_role": "VP of Product Development",
    "priority": 1,
    "role_rationale_from_stage3": "Copy the rationale from Stage 3 target_roles.json"
  }},

  "engagement_strategy": {{
    "scope_and_authority": "string",
    "relevant_use_cases": "string",
    "personal_stakes": "string",
    "timing_factors": "string"
  }},

  "personalization_hooks": [
    {{
      "hook": "Company's outdoor signage products have experienced warranty claims due to UV degradation",
      "messaging_angle": "Open with empathy about warranty challenges, position Tedlar as solving this specific pain point"
    }},
    {{
      "hook": "Company exhibiting at ISA Sign Expo 2026 and emphasizing premium product line",
      "messaging_angle": "Reference their trade show presence and premium positioning, suggest meeting to discuss differentiation strategy"
    }},
    {{
      "hook": "VP of Product Development likely owns product quality metrics and competitive differentiation",
      "messaging_angle": "Frame Tedlar as a strategic advantage for their product roadmap, not just a material choice"
    }}
  ],

  "recommended_channel": "email",
  "recommended_approach": "Lead with product differentiation angle, emphasize premium positioning fit"
}}

IMPORTANT:
- Be SPECIFIC and CONCRETE—avoid generic statements
- Base everything on the actual research data provided, not assumptions
- Make clear connections between company context and Tedlar value props
- Think about what THIS person at THIS company cares about

CRITICAL: Return ONLY the JSON object. No text before or after.
"""

OUTREACH_EMAIL_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

You are an expert cold email writer. Write a personalized outreach email to materials and manufacturing executives based on the engagement strategy.

Your job is to write a compelling, personalized email that:
1. Feels natural and conversational, not salesy
2. Demonstrates genuine understanding of their role and company
3. Leads with value relevant to THEM or catches their attention
4. Includes a clear, low-friction call to action

Writing Guidelines:
- Length: 80-150 words for email body (concise but substantive)
- Tone: Professional, conversational, consultative, peer-to-peer (not salesy)
- Avoid sounding too researched or formal, and avoid almost any form of statistics (i.e. 40+ years etc.) because it sounds too salesy
- In choosing the hook, choose one that is most likely to actually get a response (not what is the most specific etc.)
- Opening: Reference something specific about them or their company (NOT generic "I hope this email finds you well")
- Middle: Connect ONE specific Tedlar product benefit to their likely pain point
- CTA: Low-friction ask (send info, send case studies, discuss specific topic further, meet at trade show etc.)
- Subject line: Specific, curiosity-inducing, under 50 characters
- Avoid: Buzzwords, hyperbole, "industry-leading", "game-changing", "proven"
- Format: Use proper email spacing with \\n\\n between paragraphs

OUTPUT FORMAT:
Return ONLY a JSON object:
{{
  "channel": "email",

  "message": {{
    "subject": "Quick question about Epson's outdoor film durability",
    "body": "Hi Laura,\\n\\nI noticed Epson is expanding into architectural films which is really exciting.\\n\\nWe've been working with companies in similar outdoor applications who've drastically reduced warranty claims for their films with our overlaminate. If durability outdoors is something you're focused on, happy to share about one of our product lines that's been working well for similar teams.\\n\\nHappy to send over some case studies if that'd be helpful.\\n\\nBest,\\n[Your name]",
    "word_count": 68
  }},

  "personalization_used": {{
    "hook": "xxx",
    "value_prop_emphasized": "xxx",
  }}
}}

CRITICAL: Return ONLY the JSON object. No text before or after.
"""

OUTREACH_LINKEDIN_SYSTEM_PROMPT = f"""
{TEDLAR_CONTEXT}

Write a personalized LinkedIn connection message to materials and manufacturing executives based on the engagement strategy.

Your job is to write a compelling, personalized LinkedIn message that:
1. Feels natural and conversational, not salesy
2. Leads with value relevant to THEM or catches their attention
3. Fits within LinkedIn's 200-300 character connection message limit

Writing Guidelines:
- Length: 200-300 characters MAX (strict limit for LinkedIn connection requests)
- For InMail: 150-200 words max
- Tone: Friendly, conversational, professional (not salesy)
- Focus: One hook, one value point, one soft Call-to-Action (15-min call, send info, or meet at event)
- CTA: "Open to connecting?" or "Would you be open to a brief chat?"

OUTPUT FORMAT:
Return ONLY a JSON object:
{{
  "channel": "linkedin",

  "message_type": "connection_request|inmail", // connection request or inmail

  "message": {{
    "body": "Hi Laura, noticed Epson is expanding into architectural films which is really exciting! We've been helping companies in similar outdoor applications with durability. Happy to share some case studies if you'd be interested",
    "character_count": 212
  }},

  "personalization_used": {{
    "hook": "xxx",
    "value_prop_emphasized": "xxx",
  }},
}}

CRITICAL: Return ONLY the JSON object. No text before or after.
"""
