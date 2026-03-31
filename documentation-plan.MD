# Documentation Plan: AI Lead Generation System
## 3-Page Technical Documentation Structure

---

## Guiding Principles

**Audience:** Technical assessors evaluating the project
**Goal:** Demonstrate understanding of AI workflows, data processing design, and implementation quality
**Constraints:** Maximum 3 pages

**Key Differentiators to Highlight:**
1. Event-driven orchestration (not just sequential scripts)
2. Tiered qualification with automatic stage progression
3. Resume capability and rate limit handling
4. Quality-first approach (per-company processing over batching)

---

## Recommended Structure

### PAGE 1: System Overview & AI Workflow Design

**Purpose:** Set context, show the big picture, demonstrate architectural thinking

#### Section 1.1: Problem Statement (2-3 sentences)
- DuPont Tedlar needs to identify qualified leads from trade show exhibitors
- Manual research is time-consuming; AI can automate discovery and qualification
- Goal: Pipeline that discovers → qualifies → prepares outreach

#### Section 1.2: AI Workflow Architecture (Visual + Explanation)

```
Include high-level pipeline diagram:

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   STAGE 1   │    │   STAGE 2   │    │   STAGE 3   │    │   STAGE 4   │
│   Event     │───▶│   Company   │───▶│   Target    │───▶│   Outreach  │
│  Discovery  │    │ Qualification│    │   Roles     │    │  Generation │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
  Claude Web        Claude Web         Claude LLM         Claude LLM
  Search + LLM      Search + LLM       Analysis           Copywriting
```

**Key points to cover:**
- Each stage uses Claude API (web search or standard)
- Stages are decoupled—each produces JSON artifacts
- Event-driven: completion of one stage triggers the next
- No batching for quality-critical steps (research, scoring)

#### Section 1.3: Key Design Decisions (Brief bullets)

| Decision | Rationale |
|----------|-----------|
| Per-company processing | Maintains research quality; batching degrades LLM output |
| Event-driven orchestration | Prioritizes completing in-progress work over starting new |
| File-based state | Enables resume from interruption; no database dependency |
| Tiered qualification | Focuses resources on highest-potential leads |

---

### PAGE 2: Data Processing Pipeline (The Core)

**Purpose:** Explain exactly how data flows, what triggers each stage, scoring logic

#### Section 2.1: Stage-by-Stage Data Flow

**Stage 1: Event Discovery**
```
Input:  Search queries targeting signage/graphics industry
Tools:  Claude WebSearch (discovery) → Claude LLM (scoring)
Output: Scored events with tier assignment
        └── Tier 1 (score 8-10): Proceed to company discovery
        └── Tier 2 (score 5-7.9): Proceed if budget allows
        └── Tier 3 (score <5): Skip
```

**Stage 2: Company Research & Qualification**
```
Input:  Company name + website URL from Stage 1
Tools:  Claude WebSearch (research) → Claude LLM (scoring)
Output: Qualified companies with ICP scores

Scoring Categories (1-10 scale):
  • Industry Fit (30%)
  • Size/Revenue Fit (25%)
  • Strategic Relevance (20%)
  • Market Activity (25%)

Tier Thresholds (weighted score 0-100):
  • Tier 1: 85+ → High priority, proceed to Stage 3
  • Tier 2: 70-84 → Medium priority, proceed to Stage 3
  • Tier 3: 55-69 → Low priority, proceed to Stage 3
  • Disqualified: <55 → Do not proceed
```

**Stage 3: Target Role Identification**
```
Input:  Company research from Stage 2 (Tier 1-2 only)
Tools:  Claude LLM (analysis)
Output: Target decision-maker roles + LinkedIn search URLs

Automatic Trigger: Runs when Stage 2 completes for Tier 1/2 company
```

**Stage 4: Outreach Generation**
```
Input:  Company research + target roles + contact info
Tools:  Claude LLM (copywriting)
Output: Personalized email/LinkedIn messages

Note: Requires manual contact input from LinkedIn searches
```

#### Section 2.2: Orchestration Logic

**Priority Order (Later stages first):**
```python
# From main.py - prioritize completing in-progress work
1. Check: Companies needing Stage 3? (have scoring, no target_roles)
   → Process these FIRST (finish what's started)

2. Check: Companies needing Stage 2? (discovered, no scoring)
   → Process these SECOND
   → Stage 3 auto-triggers via callback when Stage 2 completes
```

**Rate Limit Handling:**
- Shared rate limiter (30k tokens/minute)
- Sequential processing within stages
- Automatic wait when approaching limit

**Resume Capability:**
- State tracked via file existence (research.json, scoring.json, etc.)
- Pipeline checks existing files before processing
- Safe to interrupt and restart

---

### PAGE 3: Implementation Results

**Purpose:** Show what was built, demonstrate outcomes, acknowledge limitations

#### Section 3.1: System Components

**Pipeline Code (src/):**
| File | Purpose |
|------|---------|
| `main.py` | Event-driven orchestrator with rate limiting |
| `stage1_event_discovery.py` | Event discovery and scoring |
| `stage2_company_qualification.py` | Company research and ICP scoring |
| `stage3_contact_finding.py` | Target role identification |
| `stage4_outreach_generation.py` | Personalized outreach generation |
| `prompts.py` | All LLM prompts with TEDLAR_CONTEXT |
| `constants.py` | Model configuration, scoring weights, thresholds |

**Dashboard (dashboard/):**
- Next.js application for reviewing pipeline outputs
- Views: Companies, Events, Outreach
- Features: Tier filtering, research modals, outreach preview/copy

#### Section 3.2: Pipeline Outputs

**Data Artifacts Generated:**
```
data/
├── events/
│   ├── discovered_events.json      # Raw event discovery
│   ├── scored_events.json          # Events with tier scores
│   └── discovered_companies.json   # Companies per event
│
└── companies/
    └── {Company Name}/
        ├── research.json           # Detailed company research
        ├── scoring.json            # ICP scores + qualification
        ├── target_roles.json       # Decision-maker analysis
        └── linkedin_searches.json  # Sales Navigator URLs
```

#### Section 3.3: Sample Results (if available)

[Include actual metrics from pipeline run if available]
- Events discovered: X
- Events qualified (Tier 1/2): X
- Unique companies identified: X
- Companies scored: X
- Tier 1 companies: X
- Tier 2 companies: X

#### Section 3.4: Limitations & Future Improvements

**Current Limitations:**
- Contact discovery requires manual LinkedIn searches (Clay API not integrated for budget)
- Rate limits require ~60s delays between API calls
- Single-threaded processing (parallelism limited by rate limits)

**Potential Improvements:**
- Integrate Clay API for automated contact enrichment
- Add email verification step
- Implement CRM integration for direct export
- Add A/B testing for outreach messages

---

## Questions Before Writing

1. **Actual metrics**: Do you have pipeline run results to include? (events found, companies scored, etc.)

2. **Technical depth**: Should I include code snippets, or keep descriptions conceptual?

3. **Dashboard emphasis**: Prominent section or brief mention?

4. **Visual style**: Plain markdown or formatted for PDF export?

---

## Alternative Structures Considered

### Option B: Results-First (for impact-focused audience)
1. Page 1: Results & Demo → What was achieved
2. Page 2: How It Works → Pipeline explanation
3. Page 3: Technical Details → Orchestration, scoring logic

### Option C: Problem-Solution-Results (classic structure)
1. Page 1: Problem + Approach
2. Page 2: Solution (pipeline details)
3. Page 3: Results + Next Steps

**Recommendation:** The proposed structure (Overview → Pipeline → Results) is best for a technical assessment because it:
- Shows architectural thinking first
- Demonstrates depth in the core pipeline section
- Ends with concrete deliverables

---

## Next Steps

1. Confirm structure and answer clarifying questions above
2. Write final documentation in `DOCUMENTATION.MD`
3. Review and refine for 3-page target
