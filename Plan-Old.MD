# DuPont Tedlar GTM Lead Generation & Outreach System
## Comprehensive Implementation Plan

---

## Executive Summary

This project builds an AI-powered lead generation and outreach automation system for DuPont Tedlar's Graphics & Signage team. The system will identify relevant industry events, qualify attending companies against DuPont's ICP, enrich decision-maker profiles, generate personalized outreach, and present everything in a reviewable dashboard.

**Timeline:** 72 hours
**Budget:** Up to $200 in API costs
**Deployment:** Local demo
**Key Integrations:** Tavily (event discovery), Firecrawl (web scraping), Clay (contact enrichment only)

---

## Part 1: Understanding the Context

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

### 1.3 What Instalily AI is Evaluating

Based on the GTM Engineer role description, they're looking for:

1. **Technical Implementation Skills** - Can you build functional GTM tools?
2. **RevOps Understanding** - Do you understand the sales funnel and lead qualification?
3. **Data Proficiency** - Can you work with APIs, structure data, and create clean outputs?
4. **Practical Problem-Solving** - Can you translate business problems into working solutions?
5. **Scalable Thinking** - Is your approach repeatable and extensible?
6. **End-to-End Ownership** - Can you take a problem from concept to working demo?

---

## Part 2: Technical Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER DASHBOARD (Streamlit)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Events    │  │  Companies  │  │  Contacts   │  │  Outreach Queue     │ │
│  │   View      │  │   View      │  │   View      │  │  Review/Edit/Send   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                               │
│                     (Python + LangChain/OpenAI Functions)                   │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  EVENT FINDER   │  │ COMPANY QUAL.   │  │ CONTACT ENRICH. │  │ OUTREACH GEN.   │
│     AGENT       │  │    AGENT        │  │     AGENT       │  │     AGENT       │
│                 │  │                 │  │                 │  │                 │
│ - Web scraping  │  │ - ICP scoring   │  │ - Clay API      │  │ - LLM-powered   │
│ - Event APIs    │  │ - Revenue est.  │  │ - LinkedIn data │  │ - Personalized  │
│ - Association   │  │ - Industry fit  │  │ - Email finding │  │ - Multi-channel │
│   websites      │  │ - Signal detect │  │ - Role mapping  │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │                    │
         └────────────────────┴────────────────────┴────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER (SQLite + JSON)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   events    │  │  companies  │  │  contacts   │  │  outreach_queue     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend** | Python 3.11+ | Rapid development, excellent LLM libraries, Clay SDK support |
| **AI/LLM** | OpenAI GPT-4o / Claude | Best-in-class for reasoning and personalization |
| **Agent Framework** | LangChain or custom | Structured agent orchestration |
| **Event Discovery** | Tavily API | AI-native search, returns structured results optimized for LLM workflows |
| **Web Scraping** | Firecrawl API | Handles JS rendering, anti-bot measures, returns clean markdown |
| **Company Qualification** | Firecrawl + LLM | Website scraping + LLM inference for firmographics and ICP scoring |
| **Contact Enrichment** | Clay API | People search + enrichment with LinkedIn URLs and email (Stage 3 only) |
| **Database** | SQLite | Simple, portable, no setup required for demo |
| **Dashboard** | Streamlit | Rapid UI development, good for demos, Python-native |
| **Data Validation** | Pydantic | Type safety and data validation |

### 2.3 Technology Decision Rationale

#### Why Tavily for Event Discovery?
- **AI-native**: Returns search results optimized for LLM consumption, not raw HTML
- **Structured output**: Clean JSON with URLs, titles, content snippets
- **Fast & cheap**: ~$0.01/search, perfect for "find me events in the signage industry"
- **Better than alternatives**: More structured than Claude WebSearch, faster than building custom scrapers

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

#### Complete Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE DATA PIPELINE                            │
│                                                                             │
│   STAGE 1          STAGE 2           STAGE 3            STAGE 4            │
│   Event            Company           Decision-Maker     Outreach           │
│   Discovery        Qualification     Finding            Generation         │
│   ─────────────    ──────────────    ──────────────     ──────────────     │
│   Tavily +         Firecrawl +       Clay API           LLM                │
│   Firecrawl +      LLM               (People Search     (Copywriting)      │
│   LLM              (No Clay)         + Enrichment)                         │
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
│ Step 1.1: TAVILY SEARCH                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Integration:                                                                │
│   • Endpoint: tavily.search()                                               │
│   • Search depth: "advanced" (for comprehensive results)                    │
│   • Max results: 10 per query                                               │
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
│   {                                                                         │
│     "url": "https://...",                                                   │
│     "title": "ISA Sign Expo 2024 Exhibitor List",                           │
│     "content": "snippet of page content...",                                │
│     "score": 0.95  // relevance score from Tavily                           │
│   }                                                                         │
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
│   • Event page URLs from Tavily results                                     │
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
  "source": "tavily_search",
  "scraped_at": "2024-01-15T10:30:00Z"
}
```

---

##### STAGE 2: COMPANY QUALIFICATION

**Objective:** Enrich companies with firmographic data and score ICP fit using website analysis (no Clay—reserved for Stage 3).

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
Tools:  Tavily → Firecrawl → LLM (extraction) → LLM (scoring)
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

### 2.4 Cost Estimate

| Stage | Tool | Volume | Cost/Unit | Total |
|-------|------|--------|-----------|-------|
| **Stage 1: Event Discovery** | | | | |
| └ Event Search | Tavily | 50-100 searches | ~$0.01 | $0.50-1 |
| └ Event Page Scraping | Firecrawl | 50 pages | ~$0.03 | $1.50 |
| └ Exhibitor List Scraping | Firecrawl | 100 pages | ~$0.03 | $3 |
| └ Event Extraction + Scoring | GPT-4o | 50 calls | ~$0.03 | $1.50 |
| **Stage 2: Company Qualification** | | | | |
| └ Website Scraping (multi-page) | Firecrawl | 500 pages | ~$0.03 | $15 |
| └ Firmographic Analysis + ICP Scoring | GPT-4o | 100 calls | ~$0.05 | $5 |
| **Stage 3: Decision-Maker Finding** | | | | |
| └ People Search | Clay | 70 companies | ~$0.35 | $24.50 |
| └ Contact Enrichment | Clay | 180 contacts | ~$0.15 | $27 |
| └ Contact Scoring + Hooks | GPT-4o | 180 calls | ~$0.02 | $3.60 |
| **Stage 4: Outreach Generation** | | | | |
| └ Email + LinkedIn Copy | GPT-4o | 120 messages | ~$0.05 | $6 |
| **TOTAL** | | | | **~$87** |

**Budget allocation rationale:**
- Clay budget concentrated on Stage 3 (People Search + Contact Enrichment) = ~$51.50
- Firecrawl handles both event scraping and company website analysis = ~$19.50
- LLM costs for analysis, scoring, and outreach = ~$16
- **Budget headroom:** ~$113 remaining for iterations, retries, and edge cases

### 2.5 Data Models

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

---

## Part 3: Implementation Phases

### Phase 1: Foundation & Data Collection (Hours 1-20)

#### 1.1 Project Setup (Hours 1-3)
- [ ] Initialize Python project with proper structure
- [ ] Set up virtual environment and dependencies
- [ ] Configure environment variables (API keys)
- [ ] Set up SQLite database with schema
- [ ] Create Pydantic models for data validation

#### 1.2 Event Finder Agent (Hours 4-12)
**Objective:** Identify key industry events where DuPont's ICP will be present

**Target Events/Sources:**
1. **ISA International Sign Expo** - Premier signage industry event
2. **PRINTING United Expo** (formerly SGIA) - Graphics and printing
3. **FESPA Global Print Expo** - European signage/print
4. **Graphics of the Americas** - Latin American market
5. **SEMA Show** - Vehicle wraps/automotive graphics
6. **NBM Show** - Sign, graphics, and wraps regional shows
7. **LabelExpo** - Label and packaging (adjacent market)

**Technology Stack:**
- **Tavily API** - AI-native search for event discovery
- **Firecrawl API** - Scrape event pages and exhibitor lists
- **LLM (GPT-4o/Claude)** - Extract structured data, score relevance

**Implementation Approach:**
```python
from tavily import TavilyClient
from firecrawl import FirecrawlApp

class EventFinderAgent:
    """
    Agent responsible for discovering relevant industry events.
    Uses Tavily for discovery, Firecrawl for scraping, LLM for extraction.
    """

    def __init__(self):
        self.tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.llm = get_llm_client()  # GPT-4o or Claude

    def discover_events(self, industry_keywords: List[str]) -> List[dict]:
        """
        Step 1: Use Tavily to find relevant events via AI-powered search.
        """
        search_queries = [
            "signage industry trade shows 2024 2025",
            "graphics printing expo exhibitor list",
            "vehicle wrap conference sign expo",
            "ISA Sign Expo PRINTING United FESPA exhibitors"
        ]

        all_results = []
        for query in search_queries:
            results = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=10
            )
            all_results.extend(results.get("results", []))

        return self._deduplicate_results(all_results)

    def scrape_event_details(self, event_url: str) -> str:
        """
        Step 2: Use Firecrawl to scrape event page content.
        """
        result = self.firecrawl.scrape_url(
            event_url,
            params={"formats": ["markdown"]}
        )
        return result.get("markdown", "")

    def extract_event_info(self, raw_content: str) -> Event:
        """
        Step 3: Use LLM to extract structured event data.
        """
        prompt = f"""
        Extract event information from this content:

        {raw_content[:4000]}

        Return JSON with: name, dates, location, description, exhibitor_list_url
        """
        return self.llm.extract_json(prompt)

    def score_event_relevance(self, event: Event) -> Tuple[float, str]:
        """
        Step 4: Use LLM to score relevance to DuPont Tedlar's ICP.
        """
        prompt = f"""
        Score this event's relevance for DuPont Tedlar (protective films for signage).

        Event: {event.name}
        Description: {event.description}

        Score 0-100 based on:
        - Industry alignment (signage, graphics, wraps)
        - Likely attendee fit for Tedlar's ICP
        - Event size and prestige

        Return JSON: {{"score": int, "rationale": "string"}}
        """
        return self.llm.extract_json(prompt)
```

#### 1.3 Exhibitor/Company Scraper (Hours 13-20)
**Objective:** Identify companies attending/exhibiting at target events

**Technology Stack:**
- **Firecrawl API** - Scrape exhibitor list pages (handles JS rendering)
- **LLM (GPT-4o/Claude)** - Extract company names from unstructured content

**Approach:**
```python
class ExhibitorScraper:
    """
    Scrapes exhibitor lists from event websites using Firecrawl.
    """

    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.llm = get_llm_client()

    def scrape_exhibitor_list(self, exhibitor_url: str) -> List[str]:
        """
        Scrape exhibitor page and extract company names.
        """
        # Step 1: Scrape with Firecrawl
        result = self.firecrawl.scrape_url(
            exhibitor_url,
            params={"formats": ["markdown"]}
        )
        content = result.get("markdown", "")

        # Step 2: Use LLM to extract company names
        prompt = f"""
        Extract all company/exhibitor names from this trade show exhibitor list.

        CONTENT:
        {content[:6000]}

        Return JSON array of company names:
        ["Company 1", "Company 2", ...]

        Only include actual company names, not booth numbers or descriptions.
        """
        companies = self.llm.extract_json(prompt)
        return companies

    def filter_relevant_companies(self, companies: List[str]) -> List[str]:
        """
        Quick LLM filter to identify companies likely relevant to Tedlar.
        """
        prompt = f"""
        Filter this list to companies likely in signage, graphics, wraps, or protective films.

        COMPANIES: {companies}

        Return JSON array of relevant company names only.
        Exclude: pure software companies, marketing agencies, unrelated manufacturing.
        """
        return self.llm.extract_json(prompt)
```

**Challenges & Solutions:**
| Challenge | Solution |
|-----------|----------|
| Exhibitor lists behind login | Focus on public lists; flag for manual review |
| PDF exhibitor lists | Firecrawl can handle some PDFs; fallback to manual |
| JavaScript-rendered lists | Firecrawl handles JS rendering automatically |
| Inconsistent company names | Normalize with LLM, use fuzzy matching for dedup |

---

### Phase 2: Lead Qualification Engine (Hours 21-35)

#### 2.1 Company Research Agent (Hours 21-28)
**Objective:** Enrich company data and qualify against ICP using website analysis + LLM inference (no Clay at this stage)

**Technology Stack:**
- **Firecrawl API** - Multi-page website scraping for company intelligence
- **LLM (GPT-4o/Claude)** - Firmographic inference + ICP scoring with nuanced reasoning

**Data Points to Gather:**
| Data Point | Source | Purpose |
|------------|--------|---------|
| Revenue/Size | LLM inference from website signals | **Critical** - required by brief |
| Employee Count | LLM inference from careers page, office locations | Size proxy, validates revenue |
| Industry | LLM analysis of products/services | ICP fit assessment |
| Headquarters | Firecrawl (about/contact pages) | Geographic targeting |
| Products/Services | Firecrawl (product pages) | Relevance to Tedlar |
| Recent News | Firecrawl (press/news pages) | Signals and timing |

**Revenue Inference Signals (used by LLM):**
- Global presence / multiple offices → $100M+
- "Fortune 500" / public company → $1B+
- "Leading provider" + multiple product lines → $50M+
- Regional player, single location → <$50M
- Enterprise customer logos in case studies → larger company
- Job posting volume on careers page

**Implementation Approach:**
```python
from firecrawl import FirecrawlApp

class CompanyQualificationAgent:
    """
    Scrapes company websites via Firecrawl and uses LLM
    for firmographic inference + ICP scoring.
    Clay is reserved for Stage 3 (contact enrichment).
    """

    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.llm = get_llm_client()

    def scrape_company_website(self, domain: str) -> dict:
        """
        Step 1: Use Firecrawl to scrape multiple pages for company intelligence.
        """
        pages_to_scrape = [
            f"https://{domain}",           # Homepage
            f"https://{domain}/about",     # About page
            f"https://{domain}/about-us",  # Alt about path
            f"https://{domain}/products",  # Products
            f"https://{domain}/solutions", # Solutions
            f"https://{domain}/careers",   # Employee signals
            f"https://{domain}/press",     # News/growth signals
            f"https://{domain}/news"       # Alt news path
        ]

        content = {}
        for url in pages_to_scrape:
            try:
                result = self.firecrawl.scrape_url(
                    url,
                    params={"formats": ["markdown"]}
                )
                content[url] = result.get("markdown", "")[:3000]
            except Exception:
                continue  # Page may not exist

        return content

    def analyze_and_score(self, company_name: str, website_content: dict) -> dict:
        """
        Step 2: Use LLM to infer firmographics and score ICP fit.
        Single prompt handles both firmographic analysis and ICP scoring.
        """
        prompt = f"""
        Analyze this company for DuPont Tedlar (protective films for signage/graphics).

        COMPANY: {company_name}

        WEBSITE CONTENT:
        {str(website_content)[:8000]}

        TASK: Infer company firmographics and score ICP fit.

        REVENUE INFERENCE SIGNALS:
        - Global presence / multiple offices → $100M+
        - "Fortune 500" / public company → $1B+
        - "Leading provider" + multiple product lines → $50M+
        - Regional player, single location → <$50M
        - Enterprise customer logos → larger company

        ICP CRITERIA:
        - Industry Fit (0-30): Makes/uses signage, graphics, wraps, protective films
        - Size/Revenue (0-25): $50M+ revenue preferred, mid-market to enterprise
        - Market Activity Signals (0-25): Trade shows, R&D, durability focus
        - Strategic Relevance (0-20): Alignment with Tedlar's UV/weather/graffiti benefits

        Return JSON with firmographics and scoring (see Stage 2 output schema).
        """
        return self.llm.extract_json(prompt)
```

**ICP Scoring Breakdown:**
| Factor | Points | What We're Looking For |
|--------|--------|------------------------|
| Industry Fit | 0-30 | Signage, large-format printing, vehicle wraps, architectural graphics |
| Company Size | 0-25 | $50M+ revenue, mid-market to enterprise |
| Signal Strength | 0-25 | Trade show presence, R&D investment, durability focus |
| Strategic Fit | 0-20 | Clear need for UV/weather/graffiti protection |

#### 2.2 Company Prioritization (Hours 29-35)
**Objective:** Rank qualified companies by priority

**Priority Matrix:**
| Score Range | Priority | Action |
|-------------|----------|--------|
| 80-100 | Tier 1 | Immediate outreach |
| 60-79 | Tier 2 | High priority |
| 40-59 | Tier 3 | Standard nurture |
| <40 | Disqualified | Archive |

---

### Phase 3: Contact Enrichment (Hours 36-48)

#### 3.1 Clay API Integration (Hours 36-42)
**Objective:** Find and enrich decision-maker contacts

**Technology Stack:**
- **Clay API** - People search + contact enrichment
- **LLM (GPT-4o/Claude)** - Contact scoring and "why this person" analysis

**Target Personas (Priority Order):**
| Priority | Title Pattern | Why They Matter | Score |
|----------|---------------|-----------------|-------|
| 1 | VP Product Development | Owns product specs, material decisions | 100 |
| 2 | Director of Innovation / R&D | Evaluates new materials and technologies | 95 |
| 3 | VP Operations / Manufacturing | Cares about durability, cost reduction | 90 |
| 4 | Director of Procurement | Controls vendor relationships | 85 |
| 5 | CTO (smaller companies) | Technical decision authority | 80 |

**Implementation Approach:**
```python
from clay import ClayClient

class ContactEnrichmentAgent:
    """
    Uses Clay API for people search and enrichment,
    LLM for contact scoring and personalization hooks.
    """

    def __init__(self):
        self.clay = ClayClient(api_key=os.getenv("CLAY_API_KEY"))
        self.llm = get_llm_client()

        self.target_titles = [
            "VP Product", "Vice President Product",
            "Director Innovation", "Director R&D", "R&D Director",
            "VP Operations", "VP Manufacturing",
            "Director Procurement", "Director Sourcing",
            "CTO", "Chief Technology Officer"
        ]

    def find_decision_makers(self, company_domain: str) -> List[dict]:
        """
        Step 1: Use Clay to search for people at company by title.
        """
        all_contacts = []

        for title_pattern in self.target_titles:
            results = self.clay.search_people(
                company_domain=company_domain,
                title_contains=title_pattern,
                limit=5
            )
            all_contacts.extend(results)

        # Deduplicate by LinkedIn URL
        seen = set()
        unique_contacts = []
        for contact in all_contacts:
            linkedin = contact.get("linkedin_url", "")
            if linkedin and linkedin not in seen:
                seen.add(linkedin)
                unique_contacts.append(contact)

        return unique_contacts

    def enrich_contact(self, contact: dict) -> dict:
        """
        Step 2: Use Clay to enrich contact with additional details.
        """
        enriched = self.clay.enrich_person(
            linkedin_url=contact.get("linkedin_url"),
            fields=[
                "full_name",
                "title",
                "email",
                "linkedin_url",
                "work_history",
                "education",
                "location"
            ]
        )
        return {**contact, **enriched}

    def score_and_rank_contacts(
        self, contacts: List[dict], company_context: dict
    ) -> List[dict]:
        """
        Step 3: Use LLM to rank contacts and generate outreach hooks.
        """
        prompt = f"""
        Rank these contacts for outreach on behalf of DuPont Tedlar.

        COMPANY CONTEXT:
        - Company: {company_context.get('name')}
        - Industry: {company_context.get('industry')}
        - Products: {company_context.get('products', 'Unknown')}
        - ICP Score: {company_context.get('icp_score')}

        CONTACTS:
        {json.dumps(contacts, indent=2)}

        For each contact, provide:
        1. Relevance score (0-100) based on title and likely decision-making power
        2. Why they're a good contact for Tedlar
        3. Personalization hooks (things to reference in outreach)

        Return JSON array sorted by relevance:
        [
            {{
                "full_name": "...",
                "title": "...",
                "linkedin_url": "...",
                "email": "...",
                "relevance_score": <0-100>,
                "why_this_person": "<1-2 sentences>",
                "personalization_hooks": ["<hook1>", "<hook2>"]
            }}
        ]
        """
        return self.llm.extract_json(prompt)
```

#### 3.2 LinkedIn Sales Navigator Link Generation (Hours 43-48)
**Objective:** Provide direct links to Sales Navigator profiles

**Approach:**
Clay returns standard LinkedIn URLs like:
```
https://www.linkedin.com/in/laura-noll-6388a55/
```

For Sales Navigator, we can construct the search URL:
```
https://www.linkedin.com/sales/search/people?query=(keywords:Laura%20Noll)
```

**Implementation:**
```python
def generate_sales_nav_link(linkedin_url: str, full_name: str) -> str:
    """
    Generate a Sales Navigator search link from LinkedIn profile.

    Note: Direct profile links require Sales Nav API access.
    This provides a search link as a workaround.
    """
    # Option 1: Direct search link (always works)
    encoded_name = urllib.parse.quote(full_name)
    search_link = f"https://www.linkedin.com/sales/search/people?query=(keywords:{encoded_name})"

    # Option 2: If we have the profile ID, try direct link
    # Format: https://www.linkedin.com/sales/people/{profile_id}
    # Profile ID can sometimes be extracted from the vanity URL

    return {
        "linkedin_url": linkedin_url,
        "sales_nav_search": search_link,
        "note": "Click search link to find in Sales Navigator"
    }
```

**Future Integration:**
The system is designed to easily integrate LinkedIn Sales Navigator API when available:
- Contact model includes `sales_nav_url` field
- Dashboard shows LinkedIn URLs as clickable links
- Export includes Sales Nav search links for manual lookup

---

### Phase 4: Outreach Generation (Hours 49-58)

#### 4.1 Personalized Message Agent (Hours 49-55)
**Objective:** Generate highly personalized outreach messages

**Personalization Factors:**
1. **Company-specific:** Industry, products, challenges
2. **Contact-specific:** Role, likely priorities, background
3. **Event-specific:** If meeting at event, reference it
4. **Timing-specific:** Industry trends, seasonal factors

**Message Templates (LLM-enhanced):**

```python
class OutreachGenerationAgent:
    """
    Generates personalized outreach using LLM.
    """

    SYSTEM_PROMPT = """
    You are a sales copywriter for DuPont Tedlar, specializing in
    protective films for the graphics and signage industry.

    DuPont Tedlar's value proposition:
    - Superior UV resistance (25+ year outdoor durability)
    - Anti-graffiti properties (easy cleaning)
    - Weather resistance (extreme temperatures, humidity)
    - Color retention (no fading or yellowing)
    - Reduced total cost of ownership

    Write personalized, professional outreach that:
    - References specific details about the prospect
    - Connects Tedlar's benefits to their likely pain points
    - Is concise (under 150 words for email, under 300 chars for LinkedIn)
    - Has a clear, low-friction CTA
    - Avoids being salesy or pushy
    """

    def generate_email(self, contact: Contact, company: Company) -> OutreachMessage:
        # Generate personalized email
        pass

    def generate_linkedin_message(self, contact: Contact, company: Company) -> OutreachMessage:
        # Generate shorter LinkedIn InMail
        pass
```

**Example Output:**
```
Subject: Quick question about [Company]'s outdoor signage durability

Hi [First Name],

I noticed [Company] exhibited at ISA Sign Expo and specializes in
architectural graphics. Given your focus on large-format outdoor
applications, I'm curious—how are you currently addressing UV
degradation and color fading challenges?

DuPont Tedlar's protective films have helped companies like
[Similar Company] extend their product warranties by 5+ years while
reducing warranty claims by 40%.

Would you be open to a 15-minute call to explore if there's a fit?

Best,
[Sales Rep Name]
```

#### 4.2 Message Variation & A/B Support (Hours 56-58)
- Generate 2-3 variations per contact
- Track which templates perform best (structure for future)
- Support different channels (email vs. LinkedIn)

---

### Phase 5: Dashboard Development (Hours 59-68)

#### 5.1 Streamlit Dashboard (Hours 59-65)
**Objective:** Create an intuitive interface for sales team

**Views Required:**

**1. Events View**
- List of discovered events
- Relevance scores
- Number of qualified companies per event
- Quick filters (date range, location, relevance)

**2. Companies View**
- Sortable/filterable table of qualified leads
- ICP score visualization
- Quick view of qualification rationale
- Drill-down to contacts

**3. Contacts View**
- Decision-makers with enriched profiles
- LinkedIn links (clickable)
- Contact details
- Role relevance score

**4. Outreach Queue**
- Draft messages pending review
- Edit capability (rich text)
- Approve/reject buttons
- Send simulation (or real send via integration)

```python
# Streamlit Dashboard Structure
import streamlit as st

def main():
    st.set_page_config(page_title="Tedlar Lead Gen", layout="wide")

    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigate",
        ["🎯 Dashboard", "📅 Events", "🏢 Companies", "👤 Contacts", "✉️ Outreach Queue"]
    )

    if page == "🎯 Dashboard":
        render_dashboard_overview()
    elif page == "📅 Events":
        render_events_view()
    # ... etc
```

#### 5.2 Review/Edit/Send Workflow (Hours 66-68)
**Objective:** Enable one-click send with review capability

**Workflow:**
1. Sales rep sees generated message
2. Can edit inline
3. Clicks "Approve" or "Edit & Approve"
4. "Send" button (simulated for demo, or real via API)
5. Status updates to "Sent"

---

### Phase 6: Integration & Polish (Hours 69-72)

#### 6.1 Integration Points
Document and implement integration hooks for:

1. **Clay API** (Primary - implemented)
   - Contact enrichment
   - Company data

2. **LinkedIn Sales Navigator** (Documented)
   - Profile links
   - InMail sending (future)

3. **Email Sending** (Stub/Simulation)
   - Could integrate: SendGrid, Mailchimp, Outreach.io
   - For demo: Log to file, show confirmation

4. **CRM Export** (Implemented)
   - Export to CSV format
   - Structured for Salesforce/HubSpot import

#### 6.2 Error Handling & Edge Cases
- API rate limiting and retries
- Missing data graceful handling
- Invalid URLs/contacts
- LLM output validation

#### 6.3 Demo Preparation
- Seed with real data for DuPont Tedlar scenario
- Prepare walkthrough script
- Document setup instructions

---

## Part 4: Directory Structure

```
dupont-tedlar-leadgen/
├── README.md                    # Setup and run instructions
├── Plan.MD                      # This document
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── main.py                  # Entry point / orchestration
│   ├── config.py                # Configuration management
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── event_finder.py      # Event discovery (Tavily + Firecrawl + LLM)
│   │   ├── company_qualifier.py # Company enrichment & ICP scoring (Firecrawl + LLM, no Clay)
│   │   ├── contact_enricher.py  # Decision-maker finding (Clay + LLM)
│   │   └── outreach_generator.py # Personalized message generation (LLM)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py             # Event Pydantic model
│   │   ├── company.py           # Company Pydantic model
│   │   ├── contact.py           # Contact Pydantic model
│   │   └── outreach.py          # OutreachMessage Pydantic model
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tavily_service.py    # Tavily API wrapper (event discovery)
│   │   ├── firecrawl_service.py # Firecrawl API wrapper (web scraping)
│   │   ├── clay_service.py      # Clay API wrapper (Stage 3 contact enrichment only)
│   │   ├── llm_service.py       # LLM abstraction (GPT-4o / Claude)
│   │   └── database.py          # SQLite operations
│   │
│   ├── data/
│   │   ├── seed_events.json     # Known major events (ISA, PRINTING United, etc.)
│   │   ├── icp_config.json      # ICP scoring configuration
│   │   └── prompt_templates/    # LLM prompt templates
│   │       ├── event_extraction.txt
│   │       ├── icp_scoring.txt
│   │       ├── contact_ranking.txt
│   │       └── outreach_email.txt
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Utility functions
│
├── dashboard/
│   ├── app.py                   # Streamlit application
│   ├── components/
│   │   ├── events_view.py
│   │   ├── companies_view.py
│   │   ├── contacts_view.py
│   │   └── outreach_view.py
│   └── styles/
│       └── custom.css
│
├── data/
│   └── tedlar_leads.db          # SQLite database
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_services.py
│
└── docs/
    ├── API_INTEGRATION.md       # Integration documentation
    └── DEMO_SCRIPT.md           # Demo walkthrough
```

---

## Part 5: Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Clay API rate limits | Can't enrich all contacts | Implement batching, prioritize top leads |
| Event exhibitor lists behind login | Missing company data | Focus on public lists, manual research for top events |
| LLM generates generic messages | Poor outreach quality | Detailed prompts, few-shot examples, human review |
| Web scraping blocked | Missing event/company data | Rotate user agents, respect robots.txt, use cached data |
| Time constraint (72 hours) | Incomplete features | Prioritize core flow, document planned enhancements |
| Company revenue data unavailable | Can't qualify by size | Use proxies (employee count, funding, news) |

---

## Part 6: Success Criteria

### Minimum Viable Demo (Must Have)
- [ ] Discover and display 5+ relevant events
- [ ] Identify and qualify 20+ companies with ICP scores
- [ ] Enrich 50+ decision-maker contacts
- [ ] Generate personalized outreach for top 10 leads
- [ ] Dashboard with all four views functional
- [ ] Edit and "send" workflow working

### Stretch Goals (Nice to Have)
- [ ] Real-time Clay API enrichment
- [ ] Multiple outreach variations per contact
- [ ] Export to CRM format (CSV)
- [ ] Email validation/verification
- [ ] Chrome extension for LinkedIn integration

---

## Part 7: Questions for Instalily Team

Before or during implementation, consider clarifying:

1. **Data Scope:** Should this focus on upcoming events (next 6-12 months) or also include recently completed events where leads can still be followed up?

2. **Geographic Focus:** Is DuPont Tedlar targeting specific regions (North America, Europe, Global)?

3. **Outreach Channel Preference:** Is email or LinkedIn InMail the preferred first touch?

4. **Compliance Requirements:** Any specific compliance needs (GDPR, CAN-SPAM) to consider for outreach?

5. **Existing CRM:** What CRM does the sales team use? This affects export format.

6. **Success Metrics:** How will the demo be evaluated? Pure functionality, or also UX/design?

---

## Part 8: Implementation Checklist

### Day 1 (Hours 1-24)
- [ ] Project setup and configuration
- [ ] Event finder agent (with seed data)
- [ ] Basic web scraping for exhibitor lists
- [ ] Initial company data collection
- [ ] Database schema and basic CRUD

### Day 2 (Hours 25-48)
- [ ] Company qualification agent
- [ ] ICP scoring implementation
- [ ] Clay API integration
- [ ] Contact enrichment pipeline
- [ ] LinkedIn URL handling

### Day 3 (Hours 49-72)
- [ ] Outreach generation agent
- [ ] Streamlit dashboard (all views)
- [ ] Review/edit/send workflow
- [ ] Integration documentation
- [ ] Demo preparation and testing
- [ ] README and final polish

---

## Appendix A: Sample ICP Scoring Configuration

```json
{
  "industry_scores": {
    "high_fit": {
      "industries": [
        "Sign Manufacturing",
        "Large Format Printing",
        "Vehicle Wraps",
        "Architectural Graphics",
        "Protective Films",
        "Laminating Materials"
      ],
      "score": 30
    },
    "medium_fit": {
      "industries": [
        "Commercial Printing",
        "Packaging",
        "Display Manufacturing",
        "Industrial Coatings"
      ],
      "score": 20
    },
    "low_fit": {
      "industries": [
        "General Manufacturing",
        "Marketing Services"
      ],
      "score": 10
    }
  },
  "size_scores": {
    "$1B+": 25,
    "$500M-1B": 25,
    "$100M-500M": 25,
    "$50M-100M": 20,
    "$10M-50M": 15,
    "<$10M": 5
  },
  "signal_scores": {
    "ISA Sign Expo Exhibitor": 15,
    "SGIA/PRINTING United Exhibitor": 15,
    "ISA Member": 10,
    "SGIA Member": 10,
    "Recent expansion news": 10,
    "New product launch": 10,
    "Hiring in R&D": 8,
    "Mentioned durability challenges": 20
  },
  "persona_priority": [
    {"title_contains": ["VP Product", "Vice President Product"], "score": 100},
    {"title_contains": ["Director Innovation", "Director R&D"], "score": 95},
    {"title_contains": ["VP Operations", "VP Manufacturing"], "score": 90},
    {"title_contains": ["Director Procurement", "Director Sourcing"], "score": 85},
    {"title_contains": ["CTO", "Chief Technology"], "score": 80}
  ]
}
```

---

## Appendix B: Example Prompt for Outreach Generation

```
You are writing a personalized sales email for DuPont Tedlar.

CONTEXT:
- Recipient: {contact.full_name}, {contact.title} at {company.name}
- Company: {company.description}
- Industry: {company.industry}
- Event Connection: {event.name if attending else 'None'}
- ICP Score: {company.icp_score}/100
- Key Signals: {company.signals}

DUPONT TEDLAR VALUE PROPS:
1. 25+ year outdoor durability
2. Anti-graffiti (easy cleaning with mild solvents)
3. Color retention (no fading/yellowing)
4. Temperature resistance (-70°F to 230°F)
5. Chemical resistance
6. Reduced TCO (fewer replacements, lower maintenance)

WRITING GUIDELINES:
- Keep under 150 words
- Reference something specific about their company
- Connect a Tedlar benefit to their likely pain point
- Include a soft CTA (15-minute call, not a demo)
- Professional but warm tone
- No buzzwords or jargon

OUTPUT FORMAT:
Subject: [compelling subject line]

[Email body]

Best,
[Sales Rep Name]
```

---

## Appendix C: Dashboard Wireframes

### Events View
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Events                                              [Filter ▼] [Export] │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ 📅 ISA International Sign Expo 2024                                  ││
│ │ Apr 10-12, 2024 | Las Vegas, NV                                      ││
│ │ Relevance: ████████████████████░░░░ 85%                              ││
│ │ Companies: 47 qualified | Contacts: 124 enriched                     ││
│ │ [View Companies] [View Contacts]                                     ││
│ └──────────────────────────────────────────────────────────────────────┘│
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ 📅 PRINTING United Expo 2024                                         ││
│ │ Sep 18-20, 2024 | Las Vegas, NV                                      ││
│ │ Relevance: ████████████████░░░░░░░░ 75%                              ││
│ │ Companies: 38 qualified | Contacts: 89 enriched                      ││
│ │ [View Companies] [View Contacts]                                     ││
│ └──────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Outreach Queue View
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Outreach Queue                           [All ▼] [Pending: 23] [Sent: 5]│
├─────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ To: Laura Noll, VP Product Development                               ││
│ │ Company: Avery Dennison (ICP: 92/100)                                ││
│ │ Channel: Email                                                        ││
│ │ ─────────────────────────────────────────────────────────────────    ││
│ │ Subject: Quick question about Avery's outdoor film durability        ││
│ │                                                                       ││
│ │ Hi Laura,                                                             ││
│ │                                                                       ││
│ │ I noticed Avery Dennison's recent expansion into architectural       ││
│ │ graphics and your focus on weather-resistant solutions...            ││
│ │ [Edit message]                                                        ││
│ │ ─────────────────────────────────────────────────────────────────    ││
│ │ Personalization: "References their ISA Sign Expo presence and        ││
│ │ recent architectural graphics product line expansion"                 ││
│ │                                                                       ││
│ │ [✓ Approve] [✎ Edit & Approve] [✗ Reject] [📧 Send]                  ││
│ └──────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

*This plan will be updated as implementation progresses and requirements are clarified.*
