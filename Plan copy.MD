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

## Part 3: Complete Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│   STAGE 1          STAGE 2           STAGE 3            STAGE 4            │
│   Event            Company           Decision-Maker     Outreach           │
│   Discovery        Qualification     Finding            Generation         │
│   ─────────────    ──────────────    ──────────────     ──────────────     │
│   Claude           Firecrawl +       Clay API           LLM                │
│   WebSearch +      LLM               (People Search     (Copywriting)      │
│   Firecrawl + LLM                    + Enrichment)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

##### STAGE 1: EVENT DISCOVERY

**Objective:** Discover relevant industry events and extract exhibitor/attendee company lists.

**Input:**
- Predefined search queries targeting signage/graphics industry events
- Seed list of known major events (ISA Sign Expo, PRINTING United, FESPA, etc.)

**Processing Pipeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.1: CLAUDE WEBSEARCH                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Integration:                                                                │
│   • Tool: Claude's built-in WebSearch capability                            │
│                                                                             │
│ Input:                                                                      │
│   search_queries = [                                                        │
│     "signage industry trade shows 2024 2025 exhibitor list",                │
│     "ISA Sign Expo exhibitors floor plan",                                  │
│     "PRINTING United Expo exhibitor directory",                             │
│     "FESPA Global Print Expo companies attending",                          │
│     "vehicle wrap conference exhibitors 2024"                               │
│   ]                                                                         │
│                                                                             │
│ Output per search:                                                          │
│   - URLs of relevant event pages                                            │
│   - Event names, dates, locations from search snippets                      │
│   - Links to exhibitor directories                                          │
│                                                                             │
│ Note: Claude WebSearch returns results that Claude can immediately          │
│ process—no separate parsing step needed. URLs are passed to Firecrawl       │
│ for full page content extraction.                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.2: FIRECRAWL SCRAPING                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Integration:                                                                │
│   • Endpoint: firecrawl.scrape_url()                                        │
│   • Format: markdown (clean, LLM-friendly output)                           │
│   • Handles: JS rendering, anti-bot, dynamic content                        │
│                                                                             │
│ Input:                                                                      │
│   • Event page URLs from Claude WebSearch results                           │
│   • Exhibitor list URLs (often linked from main event page)                 │
│                                                                             │
│ Output:                                                                     │
│   {                                                                         │
│     "url": "https://signexpo.org/exhibitors",                               │
│     "markdown": "# ISA Sign Expo 2024 Exhibitors\n\n## Booth A1\n...",      │
│     "metadata": { "title": "...", "description": "..." }                    │
│   }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.3: LLM EXTRACTION                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ SYSTEM PROMPT (Event Extraction):                                           │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Role: You are a data extraction specialist for trade show analysis.         │
│                                                                             │
│ Task: Extract structured event and exhibitor data from scraped content.     │
│                                                                             │
│ Instructions:                                                               │
│ • Identify event name, dates (start/end), location (city, venue)            │
│ • Extract all company/exhibitor names from the content                      │
│ • Ignore booth numbers, ad copy, and non-company text                       │
│ • Normalize company names (remove Inc., LLC suffixes for matching)          │
│ • Flag if content appears to be partial (login wall, pagination)            │
│                                                                             │
│ Output JSON Schema:                                                         │
│ {                                                                           │
│   "event_name": "string",                                                   │
│   "date_start": "YYYY-MM-DD",                                               │
│   "date_end": "YYYY-MM-DD",                                                 │
│   "location_city": "string",                                                │
│   "location_venue": "string",                                               │
│   "event_website": "string",                                                │
│   "exhibitor_list_url": "string or null",                                   │
│   "companies_extracted": ["company1", "company2", ...],                     │
│   "extraction_confidence": "high|medium|low",                               │
│   "notes": "string - any issues or observations"                            │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 1.4: LLM RELEVANCE SCORING                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ SYSTEM PROMPT (Event Relevance):                                            │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Role: You evaluate trade show relevance for DuPont Tedlar's GTM strategy.   │
│                                                                             │
│ Context: DuPont Tedlar sells protective PVF films for signage, graphics,    │
│ vehicle wraps, and architectural applications. Their ICP includes           │
│ mid-market to enterprise companies in large-format printing, sign           │
│ manufacturing, and protective film distribution.                            │
│                                                                             │
│ Scoring Criteria (0-100):                                                   │
│ • Industry Alignment (0-40): How directly does this event serve signage,    │
│   graphics, wraps, or protective film industries?                           │
│ • Attendee Quality (0-30): Are exhibitors/attendees likely to be Tedlar's   │
│   ICP (manufacturers, not end consumers)?                                   │
│ • Event Prestige (0-20): Size, industry recognition, decision-maker         │
│   attendance                                                                │
│ • Timing (0-10): Is the event upcoming (actionable) or recently passed      │
│   (follow-up opportunity)?                                                  │
│                                                                             │
│ Output JSON Schema:                                                         │
│ {                                                                           │
│   "relevance_score": 0-100,                                                 │
│   "industry_alignment_score": 0-40,                                         │
│   "attendee_quality_score": 0-30,                                           │
│   "event_prestige_score": 0-20,                                             │
│   "timing_score": 0-10,                                                     │
│   "rationale": "2-3 sentence explanation",                                  │
│   "recommended_action": "prioritize|include|deprioritize|skip"              │
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

##### STAGE 2: COMPANY QUALIFICATION

**Objective:** Enrich company data and score ICP fit using website analysis.

**Input:**
```json
{
  "company_name": "Avery Dennison",
  "domain": "averydennison.com",
  "source_event": "evt_001",
  "source_event_name": "ISA International Sign Expo 2024"
}
```

**Processing Pipeline:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2.1: FIRECRAWL WEBSITE SCRAPING                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Integration:                                                                │
│   • Endpoint: firecrawl.scrape_url()                                        │
│   • Format: markdown                                                        │
│   • Timeout: 30 seconds per page                                            │
│   • Error handling: Continue on 404s, log failures                          │
│                                                                             │
│ Pages to Scrape (in order of priority):                                     │
│   1. https://{domain}              - Homepage (company overview)            │
│   2. https://{domain}/about        - Company history, mission, size signals │
│   3. https://{domain}/about-us     - Alternative about page path            │
│   4. https://{domain}/products     - Product portfolio                      │
│   5. https://{domain}/solutions    - Industry solutions                     │
│   6. https://{domain}/company      - Alternative company info path          │
│   7. https://{domain}/careers      - Employee count signals (job count)     │
│   8. https://{domain}/press        - News, funding, growth signals          │
│   9. https://{domain}/news         - Alternative news path                  │
│                                                                             │
│ Scraping Strategy:                                                          │
│   • Attempt all URLs, collect successful scrapes                            │
│   • Truncate each page to 3000 chars for LLM context efficiency             │
│   • Combine into single context document                                    │
│                                                                             │
│ Output:                                                                     │
│   {                                                                         │
│     "domain": "averydennison.com",                                          │
│     "pages_scraped": 6,                                                     │
│     "pages_failed": 3,                                                      │
│     "combined_content": "# Homepage\n...\n\n# About\n...\n\n# Products...",│
│     "total_chars": 18000                                                    │
│   }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Step 2.2: LLM FIRMOGRAPHIC ANALYSIS & ICP SCORING                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ SYSTEM PROMPT (Company Qualification):                                      │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Role: You are a B2B sales intelligence analyst specializing in company      │
│ qualification for industrial materials sales.                               │
│                                                                             │
│ Context: You are qualifying companies for DuPont Tedlar, which sells        │
│ protective PVF films for signage, large-format graphics, vehicle wraps,     │
│ and architectural applications. Their ideal customer:                       │
│ • Industry: Sign manufacturing, large-format printing, vehicle wraps,       │
│   architectural graphics, protective film distribution                      │
│ • Size: Mid-market to enterprise ($50M+ revenue preferred)                  │
│ • Signals: Trade show presence, R&D investment, durability/quality focus    │
│                                                                             │
│ Task: Analyze the provided website content to:                              │
│ 1. Infer company firmographics (size, revenue estimate, employee range)     │
│ 2. Identify their industry and product focus                                │
│ 3. Assess strategic fit with Tedlar's value proposition                     │
│ 4. Identify buying signals or pain points                                   │
│                                                                             │
│ Revenue Inference Signals (use these to estimate):                          │
│ • Global presence / multiple office locations → $100M+                      │
│ • "Fortune 500" / "S&P 500" mention → $1B+                                  │
│ • Publicly traded → Check for revenue in filings                            │
│ • "Leading provider" + multiple product lines → $50M+                       │
│ • Regional player, single location → <$50M                                  │
│ • Number of job postings on careers page                                    │
│ • Customer logos / case studies (enterprise customers = larger company)     │
│                                                                             │
│ Output JSON Schema:                                                         │
│ {                                                                           │
│   "company_name": "string",                                                 │
│   "domain": "string",                                                       │
│   "firmographics": {                                                        │
│     "estimated_revenue": "$10M-50M | $50M-100M | $100M-500M | $500M-1B | $1B+",
│     "revenue_confidence": "high|medium|low",                                │
│     "revenue_signals": ["signal1", "signal2"],                              │
│     "estimated_employees": "1-50 | 50-200 | 200-1000 | 1000-5000 | 5000+",  │
│     "headquarters": "City, State/Country",                                  │
│     "geographic_presence": "local|regional|national|global",                │
│     "company_type": "public|private|subsidiary",                            │
│     "founded_year": "YYYY or null"                                          │
│   },                                                                        │
│   "industry_fit": {                                                         │
│     "primary_industry": "string",                                           │
│     "sub_industries": ["string"],                                           │
│     "relevance_to_tedlar": "direct|adjacent|tangential|none",               │
│     "products_services": ["product1", "product2"],                          │
│     "score": 0-30,                                                          │
│     "rationale": "string"                                                   │
│   },                                                                        │
│   "size_revenue": {                                                         │
│     "meets_threshold": true|false,  // $50M+ preferred                      │
│     "score": 0-25,                                                          │
│     "rationale": "string"                                                   │
│   },                                                                        │
│   "strategic_relevance": {                                                  │
│     "value_prop_alignment": ["UV resistance", "durability", ...],           │
│     "likely_pain_points": ["pain1", "pain2"],                               │
│     "use_cases": ["signage", "vehicle wraps", ...],                         │
│     "score": 0-20,                                                          │
│     "rationale": "string"                                                   │
│   },                                                                        │
│   "market_activity_signals": {                                              │
│     "signals_found": [                                                      │
│       {"signal": "ISA Sign Expo exhibitor", "strength": "strong"},          │
│       {"signal": "Recent product launch", "strength": "medium"}             │
│     ],                                                                      │
│     "score": 0-25,                                                          │
│     "rationale": "string"                                                   │
│   },                                                                        │
│   "overall_icp_score": 0-100,  // sum of category scores                    │
│   "qualification_tier": "Tier 1|Tier 2|Tier 3|Disqualified",                │
│   "qualification_summary": "2-3 sentence summary of why qualified/not",     │
│   "recommended_next_step": "immediate_outreach|nurture|research|archive"    │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

**Stage 2 Output Schema:**

```json
{
  "company_id": "comp_001",
  "company_name": "Avery Dennison",
  "domain": "averydennison.com",
  "source_event_id": "evt_001",

  "firmographics": {
    "estimated_revenue": "$1B+",
    "revenue_confidence": "high",
    "revenue_signals": ["Fortune 500", "publicly traded", "global operations"],
    "estimated_employees": "5000+",
    "headquarters": "Mentor, Ohio, USA",
    "geographic_presence": "global",
    "company_type": "public",
    "founded_year": "1935"
  },

  "industry_fit": {
    "primary_industry": "Materials Manufacturing",
    "sub_industries": ["Pressure-sensitive materials", "Graphics solutions", "Labels"],
    "relevance_to_tedlar": "direct",
    "products_services": ["Graphics films", "Protective overlaminates", "Vehicle wraps"],
    "score": 28,
    "rationale": "Direct competitor/partner in graphics films space with overlapping product lines"
  },

  "size_revenue": {
    "meets_threshold": true,
    "score": 25,
    "rationale": "Fortune 500 company with $8B+ revenue, well above $50M threshold"
  },

  "strategic_relevance": {
    "value_prop_alignment": ["durability", "UV resistance", "weather resistance"],
    "likely_pain_points": ["Competitive differentiation", "Premium positioning"],
    "use_cases": ["Vehicle wraps", "Architectural graphics", "Outdoor signage"],
    "score": 18,
    "rationale": "Strong alignment—they sell similar products and could benefit from Tedlar as input material"
  },

  "market_activity_signals": {
    "signals_found": [
      {"signal": "ISA Sign Expo exhibitor", "strength": "strong"},
      {"signal": "Recent sustainability initiative", "strength": "medium"},
      {"signal": "New graphics product line launched", "strength": "strong"}
    ],
    "score": 21,
    "rationale": "Active in target events, investing in product development"
  },

  "overall_icp_score": 92,
  "qualification_tier": "Tier 1",
  "qualification_summary": "Enterprise-scale graphics materials company with direct relevance to Tedlar's value proposition. Their focus on durability and outdoor applications aligns perfectly with Tedlar's UV/weather resistance benefits.",
  "recommended_next_step": "immediate_outreach",

  "pages_analyzed": 6,
  "analysis_timestamp": "2024-01-15T11:45:00Z"
}
```

**Qualification Tiers:**
| Tier | Score Range | Action | Contact Priority |
|------|-------------|--------|------------------|
| Tier 1 | 80-100 | Immediate outreach | Find 3+ decision-makers |
| Tier 2 | 60-79 | High priority | Find 2+ decision-makers |
| Tier 3 | 40-59 | Standard nurture | Find 1 decision-maker |
| Disqualified | <40 | Archive | No contact search |

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
│       "personal_email",      // Backup                                      │
│       "phone",               // If available                                │
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
│ SYSTEM PROMPT (Contact Scoring):                                            │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Role: You are a sales intelligence analyst preparing contact briefs for     │
│ B2B outreach at DuPont Tedlar.                                              │
│                                                                             │
│ Context:                                                                    │
│ • DuPont Tedlar sells protective PVF films for signage/graphics             │
│ • Target personas: Product leaders, R&D directors, Operations VPs,          │
│   Procurement directors who influence material purchasing decisions         │
│ • Value props: UV resistance, durability, anti-graffiti, weather resistance │
│                                                                             │
│ Task: For each contact, analyze their:                                      │
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
  "contact_id": "cont_001",
  "company_id": "comp_001",
  "company_name": "Avery Dennison",

  "contact_data": {
    "full_name": "Laura Noll",
    "title": "Vice President, Product Development",
    "department": "Product",
    "email": "laura.noll@averydennison.com",
    "email_confidence": "high",
    "linkedin_url": "https://linkedin.com/in/laura-noll-6388a55",
    "sales_nav_search_url": "https://linkedin.com/sales/search/people?query=(keywords:Laura%20Noll%20Avery%20Dennison)",
    "phone": null,
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
  },

  "source": "clay_enrichment",
  "enriched_at": "2024-01-15T12:30:00Z"
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
│ SYSTEM PROMPT (Email Outreach):                                             │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Role: You are a B2B sales copywriter for DuPont Tedlar, specializing in     │
│ personalized outreach to materials and manufacturing executives.            │
│                                                                             │
│ DuPont Tedlar Value Proposition:                                            │
│ • Protective PVF films for signage, graphics, and architectural applications│
│ • 25+ year outdoor durability (industry-leading)                            │
│ • Superior UV resistance—no yellowing, cracking, or fading                  │
│ • Anti-graffiti properties—easy cleaning with mild solvents                 │
│ • Weather resistance—performs in extreme temps (-70°F to 230°F)             │
│ • Reduced total cost of ownership (fewer replacements, lower maintenance)   │
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
│   "tone_check": {                                                           │
│     "word_count": number,                                                   │
│     "reading_level": "string",                                              │
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
    "tone": "consultative",
    "reading_level": "professional"
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
Tools:  Claude WebSearch → Firecrawl → LLM (extraction) → LLM (scoring)
Output: Event objects with company lists
        └── Events: 5-10 relevant events
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
