# DuPont Tedlar AI Lead Generation System

## 1. Solution Architecture

A **four-stage AI GTM workflow** that progressively identifies, scores and filters leads:

![Pipeline Overview](./images/pipeline-overview.svg)

---

## 2. Data Processing Pipeline

Details found in [prompts.py](https://github.com/reiyi-lai/sample-lead-workflow/blob/main/src/prompts.py).

![Stage 1: Event Discovery](./images/stage1-vertical-flow.svg)

![Stage 2: Company Qualification](./images/stage2-vertical-flow.svg)

![Stage 3: Target Roles](./images/stage3-vertical-flow.svg)

![Stage 4: Outreach](./images/stage4-vertical-flow.svg)

## 3. AI Workflow Orchestration

Pipeline is orchestrated by `main.py` that relies on event triggers with:

1. **Priority order:** Later stages processed first such that companies closer to completion are processed through the pipeline before starting new ones.
2. **Automatic triggers:** Callbacks connect stages (when Stage 2 completes, Stage 3 starts automatically for qualified companies).
3. **Rate limiting:** Shared limiter tracks API tokens (30k/minute) across all stages.
4. **Resume capability:** Each stage produces JSON artifacts, enabling resume from interruption and preventing duplicate reruns.
5. **Tiered qualification**: Scoring thresholds before proceeding to next stage ensures resources focus on high-potential leads. Low-scoring companies filtered early.

---

## 4. Implementation Results

### 4.1 Data Outputs

Each stage produces JSON artifacts stored in `data/`:

```
data/
├── events/
│   ├── discovered_events.json      # 22 raw events from Stage 1.1
│   ├── scored_events.json          # Tiered events from Stage 1.2
│   ├── discovered_companies.json   # 37 companies from Stage 1.3
│   └── companies/
│       └── {EventName}.json        # Companies per event
├── companies
│   ├── all_qualified_companies.json # All discovered companies scored against ICP
│   └── {CompanyName}/
│       ├── research.json           # Stage 2.1 deep research
│       ├── scoring.json            # Stage 2.2 ICP scores
│       ├── target_roles.json       # Stage 3 decision-makers
└── contacts/
    ├── role_identification_results.json
    ├── linkedin_sales_nav_searches.json
    ├── clay_push_results.json
    └── {CompanyName}/
        ├── {ContactName}_analysis.json   # Stage 4.1 hooks/angles
        └── {ContactName}_outreach.json   # Stage 4.2 email draft
```

## 5. Limitations & Future Work

**Current Limitations:**
- Contact discovery generates custom LinkedIn Sales Navigator URL, but workflow doesn't route the actual LinkedIn profiles discovered back for the last stage (ie. personalized outreach to each profile)
- Rate limits require ~60s min. delays between API calls

**Potential Enhancements:**
- Add email verification step before outreach
- CRM integration for direct lead export