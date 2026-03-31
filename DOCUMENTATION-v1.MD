# DuPont Tedlar AI Lead Generation System

## 1. Solution Architecture

The system is a **four-stage AI workflow** that progressively filters and enriches leads:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AI LEAD GENERATION PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   STAGE 1              STAGE 2               STAGE 3              STAGE 4        │
│   ──────────           ──────────            ──────────           ──────────     │
│   Event                Company               Target Role          Outreach       │
│   Discovery            Qualification         Identification       Generation     │
│                                                                                  │
│   ┌─────────┐         ┌─────────┐           ┌─────────┐          ┌─────────┐    │
│   │ Claude  │         │ Claude  │           │ Claude  │          │ Claude  │    │
│   │ Web     │────────▶│ Web     │──────────▶│ LLM     │─────────▶│ LLM     │    │
│   │ Search  │         │ Search  │           │         │          │         │    │
│   └─────────┘         └─────────┘           └─────────┘          └─────────┘    │
│        │                   │                     │                    │          │
│        ▼                   ▼                     ▼                    ▼          │
│   22 events           37 companies          Target roles        Personalized    │
│   discovered          discovered            identified          outreach        │
│   11 Tier 1           8 qualified           3 per company       email/LinkedIn  │
│                       5 Tier 1                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Event-driven orchestration** | Completing in-progress work is prioritized over starting new work. When Stage 2 finishes for a company, Stage 3 automatically triggers. |
| **Tiered qualification** | Scoring criteria with explicit thresholds ensure resources focus on high-potential leads. Low-scoring companies are filtered early. |
| **File-based state** | Each stage produces JSON artifacts. Enables resume from interruption without database dependencies. |

---

## 2. Data Processing Pipeline

### 2.1 Stage 1: Event Discovery

**Objective:** Identify relevant trade shows where potential customers exhibit.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: EVENT DISCOVERY                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Step 1.1: Discover Events          Step 1.2: Score & Filter Events            │
│  ─────────────────────────          ───────────────────────────────            │
│  Tool: Claude WebSearch             Tool: Claude LLM                            │
│                                                                                 │
│  Searches for:                      Scoring Criteria (each 0-10):               │
│  • Sign industry trade shows        • Industry Alignment (50%)                  │
│  • Graphics/printing expos          • Exhibitor Quality (30%)                   │
│  • Vehicle wrap events              • Scale & Timing (20%)                      │
│  • Architectural conferences                                                    │
│                                     Tier Assignment:                            │
│  Output: Raw event list             • Tier 1: Score 8-10 → Proceed              │
│  (22 events discovered)             • Tier 2: Score 5-7.9 → Proceed if budget   │
│                                     • Tier 3: Score <5 → Skip                   │
│                                                                                 │
│                                     Output: 11 Tier 1, 9 Tier 2, 2 rejected     │
│                                                                                 │
├────────────────────────────────────────────────────────────────────────────────┤
│  Step 1.3: Company Discovery                                                    │
│  ──────────────────────────                                                     │
│  Tool: Claude WebSearch                                                         │
│                                                                                 │
│  For each Tier 1 event:                                                         │
│  • Search for exhibitor lists                                                   │
│  • Identify companies with booth presence                                       │
│  • Validate with multiple sources                                               │
│                                                                                 │
│  Output: 37 unique companies discovered                                         │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stage 2: Company Research & Qualification

**Objective:** Research each discovered company and score their fit against Tedlar's Ideal Customer Profile (ICP).

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: COMPANY QUALIFICATION                                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Step 2.1: Deep Research            Step 2.2: ICP Scoring                       │
│  ───────────────────────            ─────────────────────                       │
│  Tool: Claude WebSearch             Tool: Claude LLM + Python                   │
│                                                                                 │
│  Researches:                        Scoring Categories (1-10 scale):            │
│  • Company overview & history       ┌──────────────────────┬────────┐           │
│  • Products/services                │ Category             │ Weight │           │
│  • Revenue & employee count         ├──────────────────────┼────────┤           │
│  • Market activity & trade shows    │ Industry Fit         │ 30%    │           │
│  • Strategic pain points            │ Size/Revenue Fit     │ 25%    │           │
│                                     │ Strategic Relevance  │ 20%    │           │
│  Output per company:                │ Market Activity      │ 25%    │           │
│  • research.json (detailed)         └──────────────────────┴────────┘           │
│  • scoring.json (ICP scores)                                                    │
│                                     Weighted Score → Tier Assignment:           │
│                                     • Tier 1: 85+ → High Priority               │
│                                     • Tier 2: 70-84 → Medium Priority           │
│                                     • Tier 3: 55-69 → Lower Priority            │
│                                     • Disqualified: <55 → Stop                  │
│                                                                                 │
│                                     Results: 5 Tier 1, 2 Tier 2, 1 Tier 3       │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Stage 3: Target Role Identification

**Objective:** Identify the right decision-makers to contact at each qualified company.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: TARGET ROLE IDENTIFICATION                                             │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Input: Company research + scoring from Stage 2                                 │
│  Tool: Claude LLM                                                               │
│  Trigger: Automatically runs when Stage 2 completes for Tier 1/2 company        │
│                                                                                 │
│  Analysis:                                                                      │
│  • Reviews company research for organizational structure                        │
│  • Identifies roles with purchasing/partnership authority                       │
│  • Prioritizes based on relevance to Tedlar value propositions                  │
│  • Generates rationale for why each role matters                                │
│                                                                                 │
│  Output per company:                                                            │
│  • target_roles.json with 3 prioritized roles                                   │
│  • LinkedIn Sales Navigator search URLs                                         │
│                                                                                 │
│  Example (Epson America):                                                       │
│  ┌────┬─────────────────────────────┬───────────────────────────────────────┐   │
│  │ #  │ Role                        │ Why This Role                         │   │
│  ├────┼─────────────────────────────┼───────────────────────────────────────┤   │
│  │ 1  │ Director of Product Mgmt    │ Owns solution strategy, controls      │   │
│  │    │                             │ partnerships for "print + protect"    │   │
│  ├────┼─────────────────────────────┼───────────────────────────────────────┤   │
│  │ 2  │ VP of Channel Sales         │ Manages 100+ resellers who need       │   │
│  │    │                             │ complete workflow solutions           │   │
│  ├────┼─────────────────────────────┼───────────────────────────────────────┤   │
│  │ 3  │ Director of Marketing       │ Owns trade show presence and          │   │
│  │    │                             │ outdoor durability messaging          │   │
│  └────┴─────────────────────────────┴───────────────────────────────────────┘   │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Stage 4: Outreach Generation

**Objective:** Generate personalized outreach messages using all gathered context.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: OUTREACH GENERATION                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Input: Company research + target role rationale + contact information          │
│  Tool: Claude LLM                                                               │
│                                                                                 │
│  Step 4.1: Contact Analysis         Step 4.2: Message Generation                │
│  ──────────────────────────         ────────────────────────────                │
│  • Analyzes contact's role          • Generates personalized email              │
│  • Identifies personalization       • 80-150 words, consultative tone           │
│    hooks from background            • References specific company context       │
│  • Determines messaging angle       • Soft CTA (15-min call)                    │
│                                                                                 │
│  Example Output:                                                                │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  Subject: Completing Epson's outdoor graphics solution                          │
│                                                                                 │
│  Hi Jason,                                                                      │
│                                                                                 │
│  I've been following Epson's push into premium outdoor applications with        │
│  the S9170 launch. Really impressive positioning.                               │
│                                                                                 │
│  One thing I've noticed across the industry—printer manufacturers like          │
│  Epson invest heavily in weather-resistant capabilities, but the actual         │
│  longevity in the field depends entirely on whatever overlaminate the           │
│  customer chooses. That gap between your equipment's potential and              │
│  real-world performance seems like a missed opportunity.                        │
│                                                                                 │
│  We work with companies looking to offer complete validated systems.            │
│  Would it make sense to explore technical validation showing how our            │
│  protective films perform with UltraChrome inks?                                │
│                                                                                 │
│  Happy to send over some technical details if this resonates.                   │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 2.5 Orchestration Architecture

The pipeline is managed by an **event-driven orchestrator** (`main.py`) that:

1. **Prioritizes later stages first** — Companies closer to completion are processed before starting new ones
2. **Automatically triggers downstream stages** — When Stage 2 completes, Stage 3 starts via callback
3. **Manages rate limits** — Shared limiter tracks API token usage (30k tokens/minute)
4. **Supports resume** — File existence checks allow safe restart after interruption

```python
# Simplified orchestration logic from main.py

async def run_pipeline():
    # PRIORITY 1: Complete in-progress work first
    companies_needing_stage3 = find_companies_with_scoring_but_no_roles()
    for company in companies_needing_stage3:
        await process_stage3(company)  # Finish what's started

    # PRIORITY 2: Process new companies through full pipeline
    companies_needing_stage2 = find_unprocessed_companies()
    for company in companies_needing_stage2:
        await process_stage2(company)
        # ↳ on_company_scored() callback auto-triggers Stage 3

async def on_company_scored(company, tier, score):
    """Callback: Automatically trigger Stage 3 for qualified companies"""
    if tier in [1, 2]:  # Only Tier 1 and 2 proceed
        await process_stage3(company)
```

---

## 3. Implementation Results

### 3.1 Pipeline Outputs

**Metrics from pipeline execution:**

| Stage | Metric | Count |
|-------|--------|-------|
| Stage 1.1 | Events discovered | 22 |
| Stage 1.2 | Tier 1 events (high priority) | 11 |
| Stage 1.2 | Tier 2 events (medium priority) | 9 |
| Stage 1.2 | Tier 3 events (rejected) | 2 |
| Stage 1.3 | Unique companies discovered | 37 |
| Stage 2 | Companies fully qualified | 8 |
| Stage 2 | Tier 1 companies | 5 |
| Stage 2 | Tier 2 companies | 2 |
| Stage 3 | Companies with target roles | 1 |
| Stage 4 | Personalized outreach generated | 1 |

**Data artifacts produced:**
```
data/
├── events/
│   ├── discovered_events.json      # 22 events with metadata
│   ├── scored_events.json          # Tiered scoring with rationale
│   └── discovered_companies.json   # 37 companies from exhibitor lists
│
└── companies/
    └── {Company Name}/
        ├── research.json           # Deep company research
        ├── scoring.json            # ICP scores + qualification tier
        ├── target_roles.json       # 3 prioritized decision-maker roles
        └── linkedin_searches.json  # Sales Navigator URLs
```

### 3.2 System Components

**Pipeline code (`src/`):**

| File | Purpose |
|------|---------|
| `main.py` | Event-driven orchestrator with rate limiting and priority queue |
| `stage1_event_discovery.py` | Event discovery, scoring, and company extraction |
| `stage2_company_qualification.py` | Company research and ICP scoring |
| `stage3_contact_finding.py` | Target role identification |
| `stage4_outreach_generation.py` | Personalized message generation |
| `prompts.py` | All LLM prompts with shared TEDLAR_CONTEXT |
| `constants.py` | Model config, scoring weights, tier thresholds |

**Dashboard (`dashboard/`):**
- Next.js application for reviewing pipeline outputs
- **Companies view:** Filterable list with score breakdowns, research modals
- **Events view:** Qualified events with attending companies
- **Outreach view:** Preview and copy generated messages

### 3.4 Limitations & Future Work

**Current Limitations:**
- Contact discovery requires manual LinkedIn searches (Clay API integration planned but not implemented for budget)
- Rate limits require delays between API calls (~60s minimum)

**Potential Enhancements:**
- Integrate Clay API for automated contact enrichment
- Add email verification step before outreach
- CRM integration for direct lead export

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| LLM | Claude 4.5 Sonnet/Haiku | Web search capability, structured output |
| Pipeline | Python + asyncio | Event-driven orchestration |
| State | JSON files | Resume capability, no database dependency |
| Dashboard | Next.js + Tailwind | React-based UI for data review |
