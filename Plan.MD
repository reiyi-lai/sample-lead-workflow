# DuPont Tedlar GTM Lead Generation & Outreach System
## Comprehensive Implementation Plan by Stages

---

## Part 1: GTM Context

### 1.1 About DuPont Tedlar

DuPont Tedlar produces polyvinyl fluoride (PVF) films used for:
- **Protective overlaminates** for signs and graphics
- **Weather-resistant coatings** for outdoor applications
- **Architectural graphics** and building wraps
- **Vehicle wraps** and fleet graphics
- **Backlit signage** and displays

**Value Proposition:** Tedlar films provide exceptional durability, UV resistance, graffiti resistance, and longevity for graphics applications—reducing replacement costs and maintenance.

### 1.2 DuPont Tedlar's Ideal Customer Profile (ICP)

Based on the example (Avery Dennison) and industry analysis:

| Attribute | Criteria |
|-----------|----------|
| **Industry** | Large-format signage, vehicle wraps, architectural graphics, protective films, outdoor advertising |
| **Company Size** | Mid-market to Enterprise ($50M+ revenue preferred) |
| **Geographic** | Global or strong regional presence |
| **Activities** | Manufacturing graphics films, laminating materials, or producing finished signage |
| **Signals** | Exhibits at ISA Sign Expo, SGIA/PRINTING United, FESPA; active in SGIA/ISA associations |
| **Pain Points** | Durability issues, warranty claims, weather damage, graffiti, customer complaints about longevity |
---

## Part 2: Technical Architecture

### 2.1 Technology Stack

(to be written when we're done with entire project)

### 2.2 Technology Decision Rationale

#### Why Claude WebSearch for Event Discovery?
- **Zero additional cost**: Included with Claude API, no separate billing
- **Simpler stack**: One fewer API to integrate and manage
- **Sufficient for our needs**: Searching for well-known trade shows (ISA Sign Expo, PRINTING United, FESPA) doesn't require specialized search tooling
- **Integrated workflow**: Results flow directly into Claude's context for immediate processing

#### Why Firecrawl for Web Scraping?
- **Handles complexity**: JavaScript rendering, anti-bot measures, login walls
- **Clean output**: Returns markdown instead of messy HTML
- **Simple API**: Single call to scrape and clean a page
- **Cost-effective**: ~$0.02-0.05/page, well within budget

#### Why Clay for Contact Enrichment (Stage 3 Only)?
- **Budget optimization**: Clay reserved exclusively for people search to maximize ROI
- **Data aggregation**: Single API pulls from 50+ providers for contact data
- **LinkedIn URLs**: Critical for Sales Navigator requirement
- **Email discovery**: High-accuracy work email finding
- **Already have access**: No additional setup or cost

**Note:** Company firmographics (Stage 2) use Firecrawl + LLM inference instead of Clay to conserve budget for higher-value contact enrichment.

### 2.3 Data Models (can be iterated on/modified as we go)

```python
# Core data models (Pydantic)

class Event:
    id: str
    name: str
    date_start: date
    date_end: date
    location: str
    website: str
    relevance_score: float  # 0-100
    relevance_rationale: str
    exhibitors_url: Optional[str]
    source: str

class Company:
    id: str
    name: str
    website: str
    industry: str
    employee_count: Optional[int]
    revenue_estimate: Optional[str]  # e.g., "$100M-500M"
    headquarters: str
    icp_score: float  # 0-100
    qualification_rationale: str
    events_attending: List[str]  # event IDs
    signals: List[str]  # e.g., ["ISA member", "exhibits at Sign Expo"]
    source: str

class Contact:
    id: str
    company_id: str
    full_name: str
    title: str
    department: str
    linkedin_url: Optional[str]
    email: Optional[str]
    relevance_score: float  # 0-100 for decision-maker fit
    enrichment_data: dict  # Additional Clay data
    source: str

class OutreachMessage:
    id: str
    contact_id: str
    company_id: str
    channel: str  # "email" or "linkedin"
    subject: Optional[str]
    body: str
    personalization_rationale: str
    status: str  # "draft", "reviewed", "approved", "sent"
    edited_body: Optional[str]  # If sales edited it
```

### 2.4 Base Context (TEDLAR_CONTEXT)

**Architecture Decision:** Each pipeline step runs as a separate API call (not one continuous chat). This enables parallelization, predictable context sizes, and different models per step. The `TEDLAR_CONTEXT` constant is injected into each prompt that requires company/ICP knowledge.

```python
# constants.py

TEDLAR_CONTEXT = """
You are leading DuPont Tedlar's Graphics & Signage go-to-market initiative.
Your role is to identify and qualify leads for Tedlar's protective film products.

PRODUCT INFORMATION:
DuPont Tedlar is a portfolio of polyvinyl fluoride (PVF) protective films with 60+ years of proven performance, used as overlaminates for:
  • Signs and graphics (outdoor and indoor)
  • Vehicle wraps and fleet graphics
  • Architectural panels and building wraps
  • Wall protection surfaces
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
    • Architectural panel and facade producers
    • Protective film distributors and converters
    • Wallcovering & Interior Solutions  

  Company Size:
    • Mid-market to Enterprise ($50M+ annual revenue preferred)
    • 50+ employees typical

  Geographic Focus:
    • US-based companies (primary)
    • Global presence is a positive signal

  Buying Signals:
    • Exhibits at ISA Sign Expo, PRINTING United, FESPA, or similar
    • Active in ISA or SGIA industry associations
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
```

**Usage:** This constant is prepended to system prompts in Steps 1.1, 1.2, 1.4, 2.2, 3.3, and 4.1. Steps that don't require ICP knowledge (e.g., pure scraping, domain extraction) can omit it.

```python
# Example usage in prompts.py

EVENT_DISCOVERY_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Discover trade show events where Tedlar's ICP companies exhibit...
"""

EVENT_SCORING_PROMPT = f"""
{TEDLAR_CONTEXT}

TASK: Score the following events based on relevance to Tedlar's ICP...
"""
```

## Part 3: Complete Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│   STAGE 1          STAGE 2           STAGE 3            STAGE 4            │
│   Event            Company           Decision-Maker     Outreach           │
│   Discovery        Qualification     Finding            Generation         │
│   ─────────────    ──────────────    ──────────────     ──────────────     │
│   Claude           Firecrawl +       Clay API           LLM                │
│   WebSearch        LLM               (People Search     (Copywriting)      │
│   + LLM                              + Enrichment)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

##### STAGE 1: EVENT DISCOVERY

**Objective:** Discover relevant industry events, qualify them, then extract exhibitor/attendee company lists from qualified events only.

**Input:**
- Predefined search queries targeting signage/graphics industry events
- Seed list of known major events (ISA Sign Expo, PRINTING United, FESPA, etc.)

**Critical Flow:** Event Relevance Scoring happens BEFORE exhibitor list scraping to conserve Firecrawl credits.

**Processing Pipeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: EVENT DISCOVERY PIPELINE                        │
│                         (Cost-Optimized Flow)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │ 1.1 Event    │    │ 1.2 Event    │    │ 1.3 Scraping │    │ 1.4       │ │
│  │ Discovery    │───▶│ Relevance    │───▶│ Decision +   │───▶│ Company   │ │
│  │ (WebSearch)  │    │ Scoring      │    │ Execution    │    │ Extraction│ │
│  └──────────────┘    │ (FILTER)     │    │ (Firecrawl/  │    │ (LLM)     │ │
│                      └──────────────┘    │ WebFetch)    │    └───────────┘ │
│                             │            └──────────────┘                   │
│                             │                                               │
│                      Tier 1 & 2 only                                        │
│                      (Tier 3 skipped)                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.1: EVENT DISCOVERY (Claude WebSearch)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: Claude's built-in WebSearch capability                                │
│ Context: TEDLAR_CONTEXT injected (see Section 2.4)                          │
│                                                                             │
│ SYSTEM PROMPT (Master Event Discovery):                                     │
│ ─────────────────────────────────────────────────────────────────────────── │
│ {TEDLAR_CONTEXT}                                                            │
│                                                                             │
│ TASK: You are a trade show and industry event researcher. Using the ICP     │
│ defined above, identify events where potential customers exhibit or attend.                                         │
│                                                                             │
│ SEARCH STRATEGY - Execute both approaches:                                  │
│                                                                             │
│ APPROACH A - Database & Association Search:                                 │
│   Search for: "[keyword] trade show 2025 2026 exhibitors"                   │
│   Search for: "[keyword] industry association events"                       │
│   Search for: "[keyword] expo conference exhibitor list"                    │
│   Target databases: 10times.com, eventbrite, tradeshowcalendar.com          │
│   Target associations: Industry-specific associations per vertical          │
│                                                                             │
│ APPROACH B - Discovery Search:                                              │
│   Search for: "[keyword] manufacturers convention"                          │
│   Search for: "[keyword] fabricators expo"                                  │
│   Search for: "architectural [keyword] trade show"                          │
│                                                                             │
│ INDUSTRY KEYWORDS TO SEARCH:                                                │
│   • Signage: "sign expo", "digital signage", "sign manufacturing"           │
│   • Wall Protection: "wall covering", "interior design trade show",         │
│     "healthcare facilities expo"                                            │
│   • Transportation: "bus manufacturing", "transit expo", "rail interiors"   │
│   • Architectural: "building materials expo", "facade", "architectural      │
│     panels"                                                                  │
│                                                                             │
│ FOR EACH EVENT FOUND, EXTRACT:                                              │
│ {                                                                           │
│   "event_name": "",                                                         │
│   "dates": "",                                                              │
│   "location": "",                                                           │
│   "event_url": "",                                                          │
│   "exhibitor_list_url": "",  // If discoverable from search results         │
│   "description": "",         // Brief description from search results       │
│   "industry_vertical": "",   // signage | wall_protection | transportation  │
│   "source": ""               // Where you found this event                  │
│ }                                                                           │
│                                                                             │
│ Output: JSON array of all discovered events (do not filter - scoring next)  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.2: EVENT RELEVANCE SCORING (The Filter - BEFORE Scraping)            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: LLM (Claude) - No external API calls, just analysis of metadata       │
│ Context: TEDLAR_CONTEXT injected (see Section 2.4)                          │
│                                                                             │
│ Purpose: Score and filter events BEFORE investing Firecrawl credits         │
│ on scraping their exhibitor lists.                                          │
│                                                                             │
│ SYSTEM PROMPT (Event Qualification):                                        │
│ ─────────────────────────────────────────────────────────────────────────── │
│ {TEDLAR_CONTEXT}                                                            │
│                                                                             │
│ TASK: You are a trade show qualification specialist. Using the ICP defined  │
│ above, score events BEFORE we invest resources scraping their exhibitor     │
│ lists.                                                            │
│                                                                             │
│ Input: List of discovered events with basic metadata (no exhibitor data)    │
│                                                                             │
│ SCORING CRITERIA (each 0-10):                                               │
│                                                                             │
│ 1. INDUSTRY ALIGNMENT (0-10)                                                │
│    • 10: Core Tedlar verticals (signage, wall protection, transit)          │
│    • 7-9: Adjacent industries (architectural panels, vehicle wraps, marine) │
│    • 4-6: Tangentially related (general manufacturing, materials)           │
│    • 0-3: Unrelated industries                                              │
│                                                                             │
│ 2. EXHIBITOR QUALITY SIGNALS (0-10)                                         │
│    • 10: Known to have sign manufacturers, fabricators, OEMs as exhibitors  │
│    • 7-9: Industry-specific B2B event (likely relevant exhibitors)          │
│    • 4-6: Mixed B2B/B2C event                                               │
│    • 0-3: Primarily B2C or unrelated exhibitor base                         │
│                                                                             │
│ 3. EVENT SCALE & TIMING (0-10)                                              │
│    • 10: Major annual event, 2025-2026, US-based                            │
│    • 7-9: Significant regional event or international major event           │
│    • 4-6: Smaller niche event or slightly outside date range                │
│    • 0-3: Very small, past, or geographically inaccessible                  │
│                                                                             │
│ CALCULATE: overall_score = (industry × 0.5) + (exhibitor × 0.3) + (scale ×  │
│ 0.2)                                                                        │
│                                                                             │
│ TIER ASSIGNMENT:                                                            │
│   • Tier 1 (score 8-10): HIGH PRIORITY - Scrape exhibitor list immediately  │
│   • Tier 2 (score 5-7.9): MEDIUM - Scrape if within budget                  │
│   • Tier 3 (score 0-4.9): SKIP - Do not scrape, not worth investment        │
│                                                                             │
│ Output JSON Schema:                                                         │
│ {                                                                           │
│   "qualified_events": [                                                     │
│     {                                                                       │
│       "event_name": "",                                                     │
│       "tier": 1,                                                            │
│       "overall_score": 9.2,                                                 │
│       "scores": {                                                           │
│         "industry_alignment": 10,                                           │
│         "exhibitor_quality": 9,                                             │
│         "scale_timing": 8                                                   │
│       },                                                                    │
│       "reasoning": "ISA Sign Expo is the premier signage event...",         │
│       "exhibitor_list_url": "",                                             │
│       "scraping_recommendation": "firecrawl"                                │
│     }                                                                       │
│   ],                                                                        │
│   "rejected_events": [                                                      │
│     {                                                                       │
│       "event_name": "",                                                     │
│       "tier": 3,                                                            │
│       "overall_score": 3.1,                                                 │
│       "rejection_reason": "B2C consumer show, no relevant exhibitors"       │
│     }                                                                       │
│   ],                                                                        │
│   "summary": {                                                              │
│     "tier_1_count": 3,                                                      │
│     "tier_2_count": 5,                                                      │
│     "tier_3_count": 12,                                                     │
│     "estimated_firecrawl_calls": 8                                          │
│   }                                                                         │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                          Filter: Tier 1 & 2 only
                          (Tier 3 events skipped)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.3: SCRAPING DECISION + EXECUTION (Qualified Events Only)             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ DECISION FLOW: Which tool to use for each exhibitor_list_url?               │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │                    SCRAPING TOOL DECISION LOGIC                         │ │
│ │                                                                         │ │
│ │   INPUT: exhibitor_list_url from qualified event                        │ │
│ │                                                                         │ │
│ │                         │                                               │ │
│ │                         ▼                                               │ │
│ │               ┌─────────────────────┐                                   │ │
│ │               │ Check URL Domain    │                                   │ │
│ │               └─────────────────────┘                                   │ │
│ │                         │                                               │ │
│ │         ┌───────────────┼───────────────┐                               │ │
│ │         │               │               │                               │ │
│ │         ▼               ▼               ▼                               │ │
│ │   ┌───────────┐   ┌───────────┐   ┌───────────┐                        │ │
│ │   │ KNOWN     │   │ UNKNOWN   │   │ KNOWN     │                        │ │
│ │   │ JS-RENDER │   │ DOMAIN    │   │ STATIC    │                        │ │
│ │   └───────────┘   └───────────┘   └───────────┘                        │ │
│ │         │               │               │                               │ │
│ │         │               ▼               │                               │ │
│ │         │      ┌─────────────────┐      │                               │ │
│ │         │      │ Try WebFetch    │      │                               │ │
│ │         │      │ First (free)    │      │                               │ │
│ │         │      └─────────────────┘      │                               │ │
│ │         │               │               │                               │ │
│ │         │      ┌────────┴────────┐      │                               │ │
│ │         │      │                 │      │                               │ │
│ │         │      ▼                 ▼      │                               │ │
│ │         │  Success?          Failed/    │                               │ │
│ │         │  (>500 chars)      Minimal    │                               │ │
│ │         │      │                 │      │                               │ │
│ │         │      ▼                 │      │                               │ │
│ │         │  Use WebFetch ◄────────┘      │                               │ │
│ │         │   Output                      │                               │ │
│ │         │               │               │                               │ │
│ │         ▼               ▼               ▼                               │ │
│ │   ┌───────────┐   ┌───────────┐   ┌───────────┐                        │ │
│ │   │ FIRECRAWL │   │ FIRECRAWL │   │ WEBFETCH  │                        │ │
│ │   │           │   │ (fallback)│   │           │                        │ │
│ │   └───────────┘   └───────────┘   └───────────┘                        │ │
│ │                                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ DOMAIN CLASSIFICATION:                                                      │
│ ┌──────────────────┬────────────────────────────────────┬─────────────────┐ │
│ │ Category         │ Domains                            │ Tool            │ │
│ ├──────────────────┼────────────────────────────────────┼─────────────────┤ │
│ │ Known JS-Render  │ 10times.com, mapyourshow.com,      │ Firecrawl       │ │
│ │                  │ expocad.com, eventbrite.com,       │                 │ │
│ │                  │ experient-inc.com                  │                 │ │
│ ├──────────────────┼────────────────────────────────────┼─────────────────┤ │
│ │ Known Static     │ Most .org association sites,       │ WebFetch        │ │
│ │                  │ Direct PDF/XLSX links              │                 │ │
│ ├──────────────────┼────────────────────────────────────┼─────────────────┤ │
│ │ Unknown          │ Everything else                    │ Try WebFetch →  │ │
│ │                  │                                    │ Fallback to     │ │
│ │                  │                                    │ Firecrawl       │ │
│ └──────────────────┴────────────────────────────────────┴─────────────────┘ │
│                                                                             │
│ DECISION LOGIC (Pseudocode):                                                │
│ ─────────────────────────────────────────────────────────────────────────── │
│   KNOWN_JS_DOMAINS = ["10times.com", "mapyourshow.com", "expocad.com",      │
│                       "eventbrite.com", "experient-inc.com"]                │
│                                                                             │
│   def decide_scraping_method(exhibitor_url):                                │
│       domain = extract_domain(exhibitor_url)                                │
│                                                                             │
│       # Rule 1: Known JS-rendered → Firecrawl immediately                   │
│       if domain in KNOWN_JS_DOMAINS:                                        │
│           return "firecrawl"                                                │
│                                                                             │
│       # Rule 2: Known static → WebFetch                                     │
│       if domain.endswith(".org") or is_direct_file(exhibitor_url):          │
│           return "webfetch"                                                 │
│                                                                             │
│       # Rule 3: Unknown → Try WebFetch, fallback to Firecrawl               │
│       result = try_webfetch(exhibitor_url)                                  │
│       if len(result.content) > 500 and has_exhibitor_keywords(result):      │
│           return "webfetch"                                                 │
│       else:                                                                 │
│           return "firecrawl"                                                │
│                                                                             │
│ Output (per URL scraped):                                                   │
│   {                                                                         │
│     "url": "https://10times.com/international-sign-expo/exhibitors",        │
│     "tool_used": "firecrawl",                                               │
│     "markdown": "# ISA Sign Expo 2026 Exhibitors\n\n## Exhibitor List...",  │
│     "metadata": { "title": "...", "description": "..." }                    │
│   }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.4: COMPANY EXTRACTION (LLM)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: LLM (Claude) - Processes scraped exhibitor page content               │
│ Context: TEDLAR_CONTEXT injected for relevance_indicators extraction        │
│                                                                             │
│ SYSTEM PROMPT (Company Extraction):                                         │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Role: You are a data extraction specialist. Extract company information     │
│ from exhibitor list page content.                                           │
│                                                                             │
│ Input: Raw scraped content from exhibitor list page (Firecrawl/WebFetch)    │
│                                                                             │
│ Instructions:                                                               │
│ • Extract all company/exhibitor names from the content                      │
│ • Capture booth numbers if available                                        │
│ • Extract or infer company website URLs                                     │
│ • Identify product categories if listed                                     │
│ • Normalize company names (remove Inc., LLC suffixes for matching)          │
│ • Flag if content appears partial (login wall, pagination detected)         │
│                                                                             │
│ DOMAIN INFERENCE RULES (when URL not provided):                             │
│   1. Try: companyname.com (remove spaces, special chars)                    │
│   2. Try: getcompanyname.com                                                │
│   3. Try: companynameusa.com                                                │
│   4. Flag for manual lookup if company name is ambiguous                    │
│                                                                             │
│ Output JSON Schema:                                                         │
│ {                                                                           │
│   "event_name": "string",                                                   │
│   "event_id": "string",                                                     │
│   "companies_extracted": [                                                  │
│     {                                                                       │
│       "company_name": "string",                                             │
│       "booth_number": "string or null",                                     │
│       "website_url": "string or null",                                      │
│       "inferred_domain": "string",                                          │
│       "description": "string or null",                                      │
│       "product_categories": [],                                             │
│       "relevance_indicators": []  // Keywords suggesting Tedlar fit         │
│     }                                                                       │
│   ],                                                                        │
│   "extraction_confidence": "high|medium|low",                               │
│   "total_companies": number,                                                │
│   "notes": "string - pagination issues, partial content, etc."              │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

**Stage 1 Output Schema:**

```json
{
  "event_id": "evt_001",
  "name": "ISA International Sign Expo 2024",
  "date_start": "2024-04-10",
  "date_end": "2024-04-12",
  "location": "Las Vegas, NV",
  "venue": "Mandalay Bay Convention Center",
  "website": "https://signexpo.org",
  "exhibitors_url": "https://signexpo.org/exhibitors",
  "relevance_score": 92,
  "relevance_rationale": "Premier signage industry event with direct ICP alignment...",
  "companies_found": [
    {"name": "Avery Dennison", "domain": "averydennison.com"},
    {"name": "3M Commercial Solutions", "domain": "3m.com"},
    {"name": "Roland DGA", "domain": "rolanddga.com"}
  ],
  "company_count": 147,
  "extraction_confidence": "high",
  "source": "claude_websearch",
  "scraped_at": "2024-01-15T10:30:00Z"
}
```

---

##### STAGE 2: COMPANY RESEARCH & QUALIFICATION

**Objective:** Research companies discovered in Stage 1 and score their ICP fit using web search.

**Input:** Company records from Stage 1 (company_name, website_url, event context)

**Processing Pipeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: COMPANY RESEARCH & QUALIFICATION                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────┐         ┌──────────────────────┐                  │
│  │ 2.1 Company Research │────────▶│ 2.2 Company          │                  │
│  │ (Claude WebSearch)   │         │ Qualification        │                  │
│  │                      │         │ (LLM + Python)       │                  │
│  └──────────────────────┘         └──────────────────────┘                  │
│         │                                   │                               │
│         │                                   │                               │
│   Gathers data on:                    Scores 1-10 on:                       │
│   • Company overview                  • Industry Fit (30%)                  │
│   • Products/services                 • Size/Revenue (25%)                  │
│   • Size indicators                   • Strategic Relevance (20%)           │
│   • Recent news/activity              • Market Activity (25%)               │
│   • Industry positioning                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2.1: COMPANY RESEARCH (Claude WebSearch)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: Claude with WebSearch capability                                      │
│ Context: TEDLAR_CONTEXT injected                                            │
│                                                                             │
│ SYSTEM PROMPT (Company Research):                                           │
│ ─────────────────────────────────────────────────────────────────────────── │
│ {TEDLAR_CONTEXT}                                                            │
│                                                                             │
│ TASK: Research the following company to gather information needed for ICP   │
│ qualification. You have access to the company's website URL and web search. │
│                                                                             │
│ RESEARCH AREAS - Gather information on:                                     │
│                                                                             │
│ 1. COMPANY OVERVIEW                                                         │
│    • What does the company do? (primary business, products/services)        │
│    • Company history and founding year                                      │
│    • Headquarters location                                                  │
│    • Geographic presence (local, regional, national, global)                │
│                                                                             │
│ 2. SIZE & SCALE INDICATORS                                                  │
│    • Estimated revenue (look for: funding rounds, press mentions,           │
│      "Fortune 500", revenue figures in articles, company size descriptors)  │
│    • Employee count (LinkedIn, careers page mentions, press)                │
│    • Number of locations/facilities                                         │
│    • Public vs private company                                              │
│                                                                             │
│ 3. PRODUCTS & SERVICES                                                      │
│    • Main product lines relevant to signage, graphics, films                │
│    • Target markets and customer segments                                   │
│    • Manufacturing capabilities                                             │
│    • Notable brands or product names                                        │
│                                                                             │
│ 4. MARKET ACTIVITY & SIGNALS                                                │
│    • Trade show participation (ISA, PRINTING United, FESPA, SEMA)           │
│    • Industry association memberships                                       │
│    • Recent news, product launches, acquisitions                            │
│    • Awards or recognition in the industry                                  │
│    • Sustainability or innovation initiatives                               │
│                                                                             │
│ 5. STRATEGIC INDICATORS                                                     │
│    • Focus on durability, weather resistance, outdoor applications          │
│    • Premium vs budget positioning                                          │
│    • Quality certifications or warranties offered                           │
│    • Competitive positioning                                                │
│                                                                             │
│ RESEARCH APPROACH:                                                          │
│ • Start with the provided website URL                                       │
│ • Use web search to find additional sources (news, LinkedIn, databases)     │
│ • Prioritize recent information (last 2-3 years)                            │
│ • Note confidence level for each data point                                 │
│                                                                             │
│ OUTPUT FORMAT:                                                              │
│ Return JSON with researched data:                                           │
│ {                                                                           │
│   "company_name": "string",                                                 │
│   "website_url": "string",                                                  │
│   "research_summary": "2-3 sentence overview of the company",               │
│                                                                             │
│   "company_overview": {                                                     │
│     "description": "string - what the company does",                        │
│     "founded_year": "YYYY or null",                                         │
│     "headquarters": "City, State/Country",                                  │
│     "geographic_presence": "local|regional|national|global",                │
│     "company_type": "public|private|subsidiary"                             │
│   },                                                                        │
│                                                                             │
│   "size_indicators": {                                                      │
│     "estimated_revenue": "$10M-50M|$50M-100M|$100M-500M|$500M-1B|$1B+|unknown",
│     "revenue_confidence": "high|medium|low",                                │
│     "revenue_sources": ["source1", "source2"],                              │
│     "estimated_employees": "1-50|50-200|200-1000|1000-5000|5000+|unknown",  │
│     "employee_confidence": "high|medium|low",                               │
│     "employee_sources": ["source1", "source2"],                             │
│     "facilities_count": "number or unknown"                                 │
│   },                                                                        │
│                                                                             │
│   "products_services": {                                                    │
│     "primary_offerings": ["product1", "product2"],                          │
│     "target_markets": ["market1", "market2"],                               │
│     "manufacturing_capabilities": ["capability1", "capability2"],           │
│     "notable_brands": ["brand1", "brand2"],                                 │
│     "relevance_to_tedlar": "direct|adjacent|tangential|none"                │
│   },                                                                        │
│                                                                             │
│   "market_activity": {                                                      │
│     "trade_shows": ["event1", "event2"],                                    │
│     "industry_associations": ["assoc1", "assoc2"],                          │
│     "recent_news": [                                                        │
│       {"headline": "string", "date": "YYYY-MM", "relevance": "string"}      │
│     ],                                                                      │
│     "awards_recognition": ["award1", "award2"],                             │
│     "growth_signals": ["signal1", "signal2"]                                │
│   },                                                                        │
│                                                                             │
│   "strategic_indicators": {                                                 │
│     "durability_focus": true|false,                                         │
│     "outdoor_applications": true|false,                                     │
│     "premium_positioning": true|false,                                      │
│     "quality_certifications": ["cert1", "cert2"],                           │
│     "warranty_offerings": "string or null",                                 │
│     "sustainability_initiatives": ["initiative1", "initiative2"]            │
│   },                                                                        │
│                                                                             │
│   "sources_consulted": [                                                    │
│     {"url": "string", "type": "website|news|linkedin|database"}             │
│   ],                                                                        │
│                                                                             │
│   "research_confidence": "high|medium|low",                                 │
│   "research_notes": "any caveats or gaps in the research"                   │
│ }                                                                           │
│                                                                             │
│ CRITICAL: Return ONLY the JSON object. No text before or after.             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2.2: COMPANY QUALIFICATION & ICP SCORING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: LLM (Claude) for scoring + Python for weighted calculation            │
│ Context: TEDLAR_CONTEXT injected                                            │
│                                                                             │
│ SCORING APPROACH:                                                           │
│ • LLM rates each category on a 1-10 scale                                   │
│ • Python calculates weighted ICP score                                      │
│ • Weights are configurable in code (not in prompt)                          │
│                                                                             │
│ CATEGORY WEIGHTS (configured in Python):                                    │
│   • Industry Fit:        30% (0.30)                                         │
│   • Size/Revenue Fit:    25% (0.25)                                         │
│   • Strategic Relevance: 20% (0.20)                                         │
│   • Market Activity:     25% (0.25)                                         │
│                                                                             │
│ WEIGHTED SCORE CALCULATION (Python):                                        │
│   icp_score = (industry_fit * 0.30 * 10) +                                  │
│               (size_revenue * 0.25 * 10) +                                  │
│               (strategic_relevance * 0.20 * 10) +                           │
│               (market_activity * 0.25 * 10)                                 │
│   # Results in 0-100 scale                                                  │
│                                                                             │
│ ─────────────────────────────────────────────────────────────────────────── │
│ SYSTEM PROMPT (Company Qualification):                                      │
│ ─────────────────────────────────────────────────────────────────────────── │
│ {TEDLAR_CONTEXT}                                                            │
│                                                                             │
│ TASK: Based on the research data provided, score this company's fit with    │
│ DuPont Tedlar's Ideal Customer Profile (ICP).                               │
│                                                                             │
│ Rate each category on a scale of 1-10:                                      │
│   1-2: Very poor fit                                                        │
│   3-4: Below average fit                                                    │
│   5-6: Average/moderate fit                                                 │
│   7-8: Good fit                                                             │
│   9-10: Excellent fit                                                       │
│                                                                             │
│ SCORING CATEGORIES:                                                         │
│                                                                             │
│ 1. INDUSTRY FIT (1-10)                                                      │
│    How closely does the company's business align with Tedlar's target       │
│    verticals?                                                               │
│                                                                             │
│    Consider:                                                                │
│    • Direct match: Sign manufacturing, large-format graphics, vehicle wraps,│
│      architectural panels, protective film production → 9-10                │
│    • Adjacent: General printing, industrial coatings, building materials,   │
│      automotive aftermarket → 6-8                                           │
│    • Tangential: General manufacturing, distribution only → 3-5             │
│    • No fit: Unrelated industry → 1-2                                       │
│                                                                             │
│ 2. SIZE/REVENUE FIT (1-10)                                                  │
│    Does the company meet the preferred size threshold?                      │
│                                                                             │
│    Consider:                                                                │
│    • $100M+ revenue, 500+ employees, global presence → 9-10                 │
│    • $50M-100M revenue, 200-500 employees, national presence → 7-8          │
│    • $10M-50M revenue, 50-200 employees, regional presence → 5-6            │
│    • <$10M revenue, <50 employees, local only → 3-4                         │
│    • Unknown but signals suggest small → 2-3                                │
│                                                                             │
│ 3. STRATEGIC RELEVANCE (1-10)                                               │
│    How well do Tedlar's value propositions match the company's needs?       │
│                                                                             │
│    Consider:                                                                │
│    • Strong focus on durability, UV resistance, outdoor applications → 9-10 │
│    • Some outdoor products, quality positioning → 6-8                       │
│    • General products, no specific durability focus → 3-5                   │
│    • Indoor-only or disposable products → 1-2                               │
│                                                                             │
│ 4. MARKET ACTIVITY/SIGNALS (1-10)                                           │
│    How active is the company in the target market?                          │
│                                                                             │
│    Consider:                                                                │
│    • Exhibits at ISA/PRINTING United/FESPA, ISA member, recent product      │
│      launches in outdoor/graphics space → 9-10                              │
│    • Some trade show presence, industry involvement → 6-8                   │
│    • Limited market activity, mostly found via company website → 3-5        │
│    • No visible market activity or signals → 1-2                            │
│                                                                             │
│ OUTPUT FORMAT:                                                              │
│ Return JSON with scores and rationale:                                      │
│ {                                                                           │
│   "company_name": "string",                                                 │
│   "website_url": "string",                                                  │
│                                                                             │
│   "scores": {                                                               │
│     "industry_fit": {                                                       │
│       "score": 1-10,                                                        │
│       "rationale": "Brief explanation of score"                             │
│     },                                                                      │
│     "size_revenue_fit": {                                                   │
│       "score": 1-10,                                                        │
│       "rationale": "Brief explanation of score"                             │
│     },                                                                      │
│     "strategic_relevance": {                                                │
│       "score": 1-10,                                                        │
│       "rationale": "Brief explanation of score"                             │
│     },                                                                      │
│     "market_activity": {                                                    │
│       "score": 1-10,                                                        │
│       "rationale": "Brief explanation of score"                             │
│     }                                                                       │
│   },                                                                        │
│                                                                             │
│   "qualification_summary": "2-3 sentence summary of overall ICP fit",       │
│                                                                             │
│   "key_strengths": ["strength1", "strength2"],                              │
│   "key_concerns": ["concern1", "concern2"],                                 │
│                                                                             │
│   "recommended_talking_points": [                                           │
│     "Talking point 1 based on their needs or smth else of note",            │
│     "Talking point 2 based on their industry or smth else of note"          │
│   ],                                                                        │
│                                                                             │
│   "potential_use_cases": ["use_case1", "use_case2"]                         │
│ }                                                                           │
│                                                                             │
│ CRITICAL: Return ONLY the JSON object. No text before or after.             │
│                                                                             │
│ ─────────────────────────────────────────────────────────────────────────── │
│ PYTHON POST-PROCESSING:                                                     │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│ # Category weights (configurable)                                           │
│ WEIGHTS = {                                                                 │
│     "industry_fit": 0.30,                                                   │
│     "size_revenue_fit": 0.25,                                               │
│     "strategic_relevance": 0.20,                                            │
│     "market_activity": 0.25,                                                │
│ }                                                                           │
│                                                                             │
│ def calculate_icp_score(scores: dict) -> float:                             │
│     """Calculate weighted ICP score (0-100)"""                              │
│     total = 0                                                               │
│     for category, weight in WEIGHTS.items():                                │
│         total += scores[category]["score"] * weight * 10                    │
│     return round(total, 1)                                                  │
│                                                                             │
│ def assign_tier(icp_score: float) -> str:                                   │
│     """Assign qualification tier based on score"""                          │
│     if icp_score >= 80:                                                     │
│         return "Tier 1"                                                     │
│     elif icp_score >= 60:                                                   │
│         return "Tier 2"                                                     │
│     elif icp_score >= 40:                                                   │
│         return "Tier 3"                                                     │
│     else:                                                                   │
│         return "Disqualified"                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

**Stage 2 Output Schema:**

```json
{
  "company_name": "Avery Dennison",
  "website_url": "https://averydennison.com",

  "research_data": {
    "company_overview": {
      "description": "Global materials science company specializing in pressure-sensitive materials, graphics solutions, and labeling",
      "founded_year": "1935",
      "headquarters": "Mentor, Ohio, USA",
      "geographic_presence": "global",
      "company_type": "public"
    },
    "size_indicators": {
      "estimated_revenue": "$1B+",
      "revenue_confidence": "high",
      "estimated_employees": "5000+",
      "employee_confidence": "high"
    },
    "products_services": {
      "primary_offerings": ["Graphics films", "Protective overlaminates", "Vehicle wrap films"],
      "target_markets": ["Signage", "Vehicle graphics", "Architectural"],
      "relevance_to_tedlar": "direct"
    },
    "market_activity": {
      "trade_shows": ["ISA Sign Expo 2024", "PRINTING United"],
      "recent_news": [
        {"headline": "New graphics film line launched", "date": "2024-01"}
      ]
    }
  },

  "scores": {
    "industry_fit": {
      "score": 9,
      "rationale": "Direct competitor/partner in graphics films space with overlapping product lines in signage, vehicle wraps, and architectural applications"
    },
    "size_revenue_fit": {
      "score": 10,
      "rationale": "Fortune 500 company with $8B+ revenue, well above $50M threshold, global presence"
    },
    "strategic_relevance": {
      "score": 8,
      "rationale": "Strong focus on durability and outdoor applications, premium positioning aligns with Tedlar value props"
    },
    "market_activity": {
      "score": 9,
      "rationale": "Active ISA Sign Expo exhibitor, recent product launches in graphics space, strong industry presence"
    }
  },

  "icp_score": 90.5,
  "qualification_tier": "Tier 1",

  "qualification_summary": "Enterprise-scale graphics materials company with direct relevance to Tedlar's value proposition. Their focus on durability and outdoor applications aligns perfectly with Tedlar's UV/weather resistance benefits.",

  "key_strengths": [
    "Direct industry alignment in graphics films",
    "Enterprise scale with global reach",
    "Active in target trade shows"
  ],
  "key_concerns": [
    "May view Tedlar as competitor rather than supplier",
    "Established supplier relationships"
  ],

  "recommended_talking_points": [
    "Partnership opportunity for premium outdoor product line",
    "Tedlar's 25+ year durability for extended warranty offerings"
  ],

  "potential_use_cases": ["Vehicle wrap overlaminates", "Outdoor signage protection", "Architectural panel films"],
}
```

**Qualification Tiers:**
| Tier | Score Range | Action |
|------|-------------|--------|
| Tier 1 | 80-100 | High priority - proceed to Stage 3 (Decision-Maker Finding) |
| Tier 2 | 60-79 | Medium priority - proceed to Stage 3 |
| Tier 3 | 40-59 | Lower priority - proceed to Stage 3 |
| Disqualified | <40 | Archive - do not proceed to Stage 3 |

---

##### STAGE 3: DECISION-MAKER FINDING

**Objective:** Find and enrich decision-maker contacts at qualified companies using Clay API (People Search + Contact Enrichment).

**Input:**
```json
{
  "company_id": "comp_001",
  "company_name": "Avery Dennison",
  "domain": "averydennison.com",
  "qualification_tier": "Tier 1",
  "overall_icp_score": 92,
  "industry": "Materials Manufacturing",
  "products": ["Graphics films", "Protective overlaminates", "Vehicle wraps"],
  "likely_pain_points": ["Competitive differentiation", "Premium positioning"],
  "contacts_to_find": 3  // Based on tier
}
```

**Processing Pipeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 3.1: CLAY PEOPLE SEARCH                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Integration:                                                                │
│   • Endpoint: Clay People Search / Enrichment Tables                        │
│   • Authentication: API key in header                                       │
│   • Rate limiting: Respect Clay's limits, implement exponential backoff     │
│                                                                             │
│ Search Strategy:                                                            │
│   Execute multiple searches by title pattern, deduplicate by LinkedIn URL   │
│                                                                             │
│ Title Patterns (Priority Order):                                            │
│   Priority 1 (Score: 100): "VP Product", "Vice President Product"           │
│   Priority 2 (Score: 95):  "Director Innovation", "Director R&D",           │
│                            "Head of R&D"                                    │
│   Priority 3 (Score: 90):  "VP Operations", "VP Manufacturing",             │
│                            "Director Operations"                            │
│   Priority 4 (Score: 85):  "Director Procurement", "Director Sourcing",     │
│                            "Head of Procurement"                            │
│   Priority 5 (Score: 80):  "CTO", "Chief Technology Officer"                │
│   Priority 6 (Score: 75):  "VP Marketing", "Director Marketing"             │
│                            (if no higher-priority found)                    │
│                                                                             │
│ Clay Search Parameters:                                                     │
│   {                                                                         │
│     "company_domain": "averydennison.com",                                  │
│     "title_contains": "VP Product",                                         │
│     "seniority": ["VP", "Director", "C-Suite"],                             │
│     "limit": 5                                                              │
│   }                                                                         │
│                                                                             │
│ Output per search:                                                          │
│   [                                                                         │
│     {                                                                       │
│       "full_name": "Laura Noll",                                            │
│       "title": "VP Product Development",                                    │
│       "linkedin_url": "https://linkedin.com/in/laura-noll-6388a55",         │
│       "location": "Cleveland, Ohio",                                        │
│       "company_name": "Avery Dennison"                                      │
│     }                                                                       │
│   ]                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 3.2: CLAY CONTACT ENRICHMENT                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Integration:                                                                │
│   • Endpoint: Clay Person Enrichment                                        │
│   • Input: LinkedIn URL (most reliable identifier)                          │
│   • Cost: ~$0.15-0.35 per contact (varies by data availability)             │
│                                                                             │
│ Enrichment Fields Requested:                                                │
│   {                                                                         │
│     "linkedin_url": "https://linkedin.com/in/laura-noll-6388a55",           │
│     "fields": [                                                             │
│       "full_name",                                                          │
│       "current_title",                                                      │
│       "current_company",                                                    │
│       "work_email",          // Primary outreach channel                    │
│       "location",                                                           │
│       "work_history",        // Past companies for personalization          │
│       "education",           // Personalization hooks                       │
│       "skills",              // Technical context                           │
│       "linkedin_headline",                                                  │
│       "linkedin_summary",                                                   │
│       "linkedin_connections" // Influence indicator                         │
│     ]                                                                       │
│   }                                                                         │
│                                                                             │
│ Output:                                                                     │
│   {                                                                         │
│     "full_name": "Laura Noll",                                              │
│     "title": "Vice President, Product Development",                         │
│     "company": "Avery Dennison",                                            │
│     "work_email": "laura.noll@averydennison.com",                           │
│     "linkedin_url": "https://linkedin.com/in/laura-noll-6388a55",           │
│     "location": "Cleveland, Ohio",                                          │
│     "work_history": [                                                       │
│       {"company": "Avery Dennison", "title": "VP Product Dev", "years": 5}, │
│       {"company": "3M", "title": "Director Product Mgmt", "years": 8}       │
│     ],                                                                      │
│     "education": [{"school": "Ohio State", "degree": "MBA"}],               │
│     "linkedin_headline": "Driving innovation in materials science..."       │
│   }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 3.3: LLM CONTACT SCORING & PERSONALIZATION HOOKS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: LLM (Claude)                                                          │
│ Context: TEDLAR_CONTEXT injected (see Section 2.4)                          │
│                                                                             │
│ SYSTEM PROMPT (Contact Scoring):                                            │
│ ─────────────────────────────────────────────────────────────────────────── │
│ {TEDLAR_CONTEXT}                                                            │
│                                                                             │
│ TASK: You are a sales intelligence analyst preparing contact briefs.        │
│ Using the ICP and target personas defined above, analyze each contact for:  │
│ 1. Decision-making authority for material/supplier choices                  │
│ 2. Relevance of their role to Tedlar's products                             │
│ 3. Personalization opportunities from their background                      │
│ 4. Best outreach approach and messaging angle                               │
│                                                                             │
│ Output JSON Schema (per contact):                                           │
│ {                                                                           │
│   "contact_id": "string",                                                   │
│   "full_name": "string",                                                    │
│   "title": "string",                                                        │
│   "relevance_score": 0-100,                                                 │
│   "scoring_breakdown": {                                                    │
│     "title_seniority": 0-40,  // VP=40, Director=30, Manager=20             │
│     "role_relevance": 0-35,   // Product/R&D=35, Ops=30, Procurement=25     │
│     "influence_signals": 0-25 // Tenure, connections, past companies        │
│   },                                                                        │
│   "why_this_person": "2-3 sentence explanation of why they're a good target",
│   "decision_authority": "final|strong_influence|influencer|unclear",        │
│   "personalization_hooks": [                                                │
│     {                                                                       │
│       "hook": "Worked at 3M for 8 years",                                   │
│       "messaging_angle": "Reference shared industry experience and          │
│                          material science background"                       │
│     },                                                                      │
│     {                                                                       │
│       "hook": "MBA from Ohio State",                                        │
│       "messaging_angle": "Appeal to business ROI and TCO reduction"         │
│     }                                                                       │
│   ],                                                                        │
│   "recommended_channel": "email|linkedin",                                  │
│   "recommended_approach": "string - suggested opening angle",               │
│   "potential_objections": ["objection1", "objection2"],                     │
│   "talking_points": ["point1", "point2"]                                    │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

**Stage 3 Output Schema:**

```json
{
  "company_name": "Avery Dennison",

  "contact_data": {
    "full_name": "Laura Noll",
    "title": "Vice President, Product Development",
    "department": "Product",
    "email": "laura.noll@averydennison.com",
    "email_confidence": "high",
    "linkedin_url": "https://linkedin.com/in/laura-noll-6388a55",
    "sales_nav_search_url": "https://linkedin.com/sales/search/people?query=(keywords:Laura%20Noll%20Avery%20Dennison)",
    "location": "Cleveland, Ohio"
  },

  "enrichment_data": {
    "work_history": [
      {"company": "Avery Dennison", "title": "VP Product Development", "years": 5},
      {"company": "3M", "title": "Director Product Management", "years": 8}
    ],
    "education": [{"school": "Ohio State University", "degree": "MBA"}],
    "linkedin_headline": "Driving innovation in materials science and graphics solutions",
    "linkedin_connections": 500,
    "tenure_at_company": "5 years"
  },

  "scoring": {
    "relevance_score": 95,
    "scoring_breakdown": {
      "title_seniority": 40,
      "role_relevance": 35,
      "influence_signals": 20
    },
    "decision_authority": "strong_influence",
    "why_this_person": "As VP of Product Development at Avery Dennison, Laura directly influences material selection for their graphics product lines. Her 8-year tenure at 3M gives her deep materials science expertise and likely familiarity with protective film technologies."
  },

  "personalization": {
    "hooks": [
      {
        "hook": "8 years at 3M in product management",
        "messaging_angle": "Reference shared industry experience; position Tedlar as innovation partner"
      },
      {
        "hook": "Currently leading product development for graphics solutions",
        "messaging_angle": "Focus on how Tedlar can differentiate their product line"
      },
      {
        "hook": "MBA background",
        "messaging_angle": "Lead with TCO/ROI business case"
      }
    ],
    "recommended_channel": "email",
    "recommended_approach": "Lead with product differentiation angle—how Tedlar's UV resistance could help Avery Dennison command premium pricing",
    "potential_objections": ["Already have established supplier relationships", "May view Tedlar as competitor"],
    "talking_points": [
      "25+ year durability extends product warranties",
      "Anti-graffiti properties reduce customer complaints",
      "Premium positioning opportunity for outdoor product lines"
    ]
  }
}
```

---

##### STAGE 4: OUTREACH GENERATION

**Objective:** Generate personalized, channel-appropriate outreach messages using all gathered context.

**Input:**
```json
{
  "contact": {
    "contact_id": "cont_001",
    "full_name": "Laura Noll",
    "title": "Vice President, Product Development",
    "email": "laura.noll@averydennison.com",
    "linkedin_url": "https://linkedin.com/in/laura-noll-6388a55",
    "personalization_hooks": [...],
    "recommended_approach": "Lead with product differentiation angle..."
  },
  "company": {
    "company_id": "comp_001",
    "company_name": "Avery Dennison",
    "industry": "Materials Manufacturing",
    "products": ["Graphics films", "Protective overlaminates"],
    "icp_score": 92,
    "qualification_summary": "Enterprise-scale graphics materials company...",
    "likely_pain_points": ["Competitive differentiation", "Premium positioning"]
  },
  "event_context": {
    "event_name": "ISA International Sign Expo 2024",
    "event_date": "April 10-12, 2024",
    "attending": true
  },
  "channel": "email"  // or "linkedin"
}
```

**Processing Pipeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 4.1: LLM OUTREACH GENERATION                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: LLM (Claude)                                                          │
│ Context: TEDLAR_CONTEXT injected (see Section 2.4)                          │
│                                                                             │
│ SYSTEM PROMPT (Email Outreach):                                             │
│ ─────────────────────────────────────────────────────────────────────────── │
│ {TEDLAR_CONTEXT}                                                            │
│                                                                             │
│ TASK: You are a B2B sales copywriter. Using the product info and ICP        │
│ defined above, write personalized outreach to materials and manufacturing   │
│ executives.                                                                 │
│                                                                             │
│ Writing Guidelines:                                                         │
│ • Length: 80-150 words for email body (concise but substantive)             │
│ • Tone: Professional, consultative, peer-to-peer (not salesy)               │
│ • Opening: Reference something specific about them or their company         │
│   (NOT generic "I hope this email finds you well")                          │
│ • Middle: Connect ONE specific Tedlar benefit to their likely pain point    │
│ • CTA: Soft ask—15-minute call, brief conversation (not a demo or meeting)  │
│ • Subject line: Specific, curiosity-inducing, under 50 characters           │
│ • Avoid: Buzzwords, hyperbole, "industry-leading", "game-changing"          │
│ • Include: Specific numbers, concrete outcomes, relevant references         │
│                                                                             │
│ Input Context You'll Receive:                                               │
│ • Contact details and personalization hooks                                 │
│ • Company context (products, pain points, ICP score)                        │
│ • Event context if applicable                                               │
│ • Recommended messaging approach                                            │
│                                                                             │
│ Output JSON Schema:                                                         │
│ {                                                                           │
│   "subject_line": "string - under 50 chars",                                │
│   "email_body": "string - 80-150 words",                                    │
│   "personalization_used": ["hook1", "hook2"],                               │
│   "value_prop_emphasized": "string - which Tedlar benefit was highlighted", │
│   "cta_type": "call|email_reply|resource",                                  │
│   "quality_checks": {                                                       │
│     "personalization_score": "high|medium|low"                              │
│   }                                                                         │
│ }                                                                           │
│                                                                             │
│ ─────────────────────────────────────────────────────────────────────────── │
│ SYSTEM PROMPT (LinkedIn Outreach):                                          │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Same role and value prop context as email, with these differences:          │
│                                                                             │
│ Writing Guidelines for LinkedIn:                                            │
│ • Length: 250-300 characters MAX (LinkedIn connection message limit)        │
│ • For InMail: 150-200 words max                                             │
│ • Tone: More casual than email, still professional                          │
│ • Opening: Reference shared connection, group, or their recent post/content │
│ • Focus: One hook, one value point, one soft CTA                            │
│ • CTA: "Open to connecting?" or "Would you be open to a brief chat?"        │
│                                                                             │
│ Output JSON Schema:                                                         │
│ {                                                                           │
│   "message_type": "connection_request|inmail",                              │
│   "message_body": "string - within character limits",                       │
│   "character_count": number,                                                │
│   "personalization_used": ["hook1"],                                        │
│   "value_prop_emphasized": "string"                                         │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

**Stage 4 Output Schema:**

```json
{
  "outreach_id": "out_001",
  "contact_id": "cont_001",
  "company_id": "comp_001",
  "channel": "email",

  "message": {
    "subject": "Quick question about Avery's outdoor film durability",
    "body": "Hi Laura,\n\nI noticed Avery Dennison's continued investment in graphics solutions—particularly your work on protective overlaminates for outdoor applications.\n\nI'm curious: how are you currently addressing long-term UV degradation in your outdoor product lines? We've worked with graphics manufacturers to extend product warranties by 5+ years using Tedlar's PVF films, which maintain clarity and color for 25+ years outdoors.\n\nGiven your background in materials science from your time at 3M, I thought you might find our approach to molecular-level UV protection interesting.\n\nWould you be open to a 15-minute call to compare notes?\n\nBest,\n[Sales Rep Name]\nDuPont Tedlar",
    "word_count": 108
  },

  "personalization_analysis": {
    "hooks_used": [
      "8 years at 3M in product management",
      "Currently leading product development for graphics solutions"
    ],
    "value_prop_emphasized": "25+ year outdoor durability and UV resistance",
    "pain_point_addressed": "UV degradation in outdoor products",
    "cta_type": "call"
  },

  "quality_metrics": {
    "personalization_score": "high",
    "specificity_score": "high",
  },

  "status": "draft",
  "generated_at": "2024-01-15T13:00:00Z",

  "variations": [
    {
      "variation_id": "out_001_v2",
      "subject": "Tedlar + Avery: outdoor durability question",
      "body": "[Alternative version with different angle]",
      "angle": "ROI/TCO focus"
    }
  ]
}
```

**LinkedIn Output Example:**

```json
{
  "outreach_id": "out_002",
  "contact_id": "cont_001",
  "company_id": "comp_001",
  "channel": "linkedin",

  "message": {
    "message_type": "connection_request",
    "body": "Hi Laura—saw your work on Avery's graphics solutions. Given your materials science background, I'd love to share how we're helping manufacturers achieve 25+ year outdoor durability. Open to connecting?",
    "character_count": 223
  },

  "personalization_analysis": {
    "hooks_used": ["Materials science background"],
    "value_prop_emphasized": "25+ year outdoor durability",
    "cta_type": "connection"
  },

  "status": "draft",
  "generated_at": "2024-01-15T13:05:00Z"
}
```

---

##### PIPELINE DATA FLOW SUMMARY

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE PIPELINE DATA FLOW                         │
└─────────────────────────────────────────────────────────────────────────────┘

STAGE 1: EVENT DISCOVERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Search queries + seed event list
Tools:  Claude WebSearch → LLM (scoring/filter) → Firecrawl/WebFetch → LLM (extraction)
Flow:   1. Discover events (WebSearch)
        2. Score & filter events (LLM) → Tier 1 & 2 only proceed
        3. Scrape exhibitor lists (Firecrawl/WebFetch decision logic)
        4. Extract companies (LLM)
Output: Event objects with company lists
        └── Events: 5-10 relevant events (filtered from 15-20 discovered)
        └── Companies: 100-200 raw company names per event
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                    │
                     Passes: company_name, domain, source_event
                                    │
                                    ▼
STAGE 2: COMPANY QUALIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Company name + domain + source event
Tools:  Firecrawl (multi-page) → LLM (firmographics + ICP scoring)
Output: Qualified company objects with ICP scores
        └── Tier 1 (80+): ~15-25 companies → 3 contacts each
        └── Tier 2 (60-79): ~25-40 companies → 2 contacts each
        └── Tier 3 (40-59): ~30-50 companies → 1 contact each
        └── Disqualified (<40): ~50+ companies → archived
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                    │
              Passes: company context + tier + contacts_to_find
                      (Only Tier 1-3 companies proceed)
                                    │
                                    ▼
STAGE 3: DECISION-MAKER FINDING (Clay API)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Qualified company + tier + industry context
Tools:  Clay (people search) → Clay (enrichment) → LLM (scoring + hooks)
Output: Enriched contact objects with personalization
        └── ~150-200 contacts total
        └── Each with: email, LinkedIn, work history, personalization hooks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                    │
          Passes: contact + company context + personalization hooks
                  (Top-scored contacts from Tier 1-2 companies)
                                    │
                                    ▼
STAGE 4: OUTREACH GENERATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Contact + company context + event context + channel preference
Tools:  LLM (copywriting)
Output: Personalized outreach messages ready for review
        └── ~100 email drafts
        └── ~50 LinkedIn messages
        └── Each with: personalization analysis, quality metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │   DASHBOARD QUEUE   │
                        │   (Review & Send)   │
                        └─────────────────────┘
```

## Part 4: Cost Estimate

| Stage | Tool | Volume | Cost/Unit | Total |
|-------|------|--------|-----------|-------|
| **Stage 1: Event Discovery** | | | | |
| └ Event Search | Claude WebSearch | 50-100 searches | $0 (included) | $0 |
| └ Event Page Scraping | Firecrawl | 50 pages | ~$0.03 | $1.50 |
| └ Exhibitor List Scraping | Firecrawl | 100 pages | ~$0.03 | $3 |
| └ Event Extraction + Scoring | LLM | 50 calls | ~$0.03 | $1.50 |
| **Stage 2: Company Qualification** | | | | |
| └ Website Scraping (multi-page) | Firecrawl | 500 pages | ~$0.03 | $15 |
| └ Firmographic Analysis + ICP Scoring | LLM | 100 calls | ~$0.05 | $5 |
| **Stage 3: Decision-Maker Finding** | | | | |
| └ People Search | Clay | 70 companies | ~$0.35 | $24.50 |
| └ Contact Enrichment | Clay | 180 contacts | ~$0.15 | $27 |
| └ Contact Scoring + Hooks | LLM | 180 calls | ~$0.02 | $3.60 |
| **Stage 4: Outreach Generation** | | | | |
| └ Email + LinkedIn Copy | LLM | 120 messages | ~$0.05 | $6 |
| **TOTAL** | | | | **~$87** |

**Budget allocation rationale:**
- Claude WebSearch is free (included with Claude API) — saves ~$1 vs Tavily
- Clay budget concentrated on Stage 3 (People Search + Contact Enrichment) = ~$51.50
- Firecrawl handles event scraping + company website analysis = ~$19.50
- LLM costs for analysis, scoring, and outreach = ~$16
- **Budget headroom:** ~$113 remaining for iterations, retries, and edge cases

**Simplified Stack (2 external APIs only):**
1. **Firecrawl** — All web scraping (events + company websites)
2. **Clay** — Contact enrichment only (Stage 3)

---

*This plan can be updated as implementation progresses and requirements are clarified by user.*
