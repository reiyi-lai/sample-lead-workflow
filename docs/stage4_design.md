# Stage 4: Outreach Generation - Design Document

## Overview

Stage 4 takes individual contacts (from Sales Navigator exports) and generates personalized outreach messages using all accumulated context from Stages 1-3.

## Input Data Sources

### From Sales Navigator Export (CSV/JSON)
```json
{
  "full_name": "Laura Noll",
  "title": "VP of Product Development",
  "company": "Epson America, Inc.",
  "linkedin_url": "https://linkedin.com/in/laura-noll",
  "location": "Los Angeles, CA",
  "email": "laura.noll@epson.com",  // if available
  "work_history": [...],  // if available from Sales Nav
  "education": [...]  // if available
}
```

### From Stage 2: Company Research
**File:** `data/companies/{Company Name}/research.json`
```json
{
  "company_name": "Epson America, Inc.",
  "business_overview": "...",
  "company_scale": {
    "estimated_revenue": "$1B+",
    "estimated_employees": "5000+",
    "scale_synthesis": "..."
  },
  "products_and_positioning": "...",
  "strategic_relevance_to_tedlar": "...",
  "market_activity": "...",
  "potential_pain_points": "...",
  "additional_insights": "..."
}
```

### From Stage 2: Company Scoring
**File:** `data/companies/{Company Name}/scoring.json`
```json
{
  "scores": {
    "industry_fit": {"score": 9, "rationale": "..."},
    "size_revenue_fit": {"score": 8, "rationale": "..."},
    "strategic_relevance": {"score": 9, "rationale": "..."},
    "market_activity": {"score": 8, "rationale": "..."}
  },
  "qualification_summary": "...",
  "icp_qualification": {
    "weighted_score": 85.5,
    "tier": 1,
    "tier_label": "High Priority"
  }
}
```

### From Stage 3: Target Roles Analysis
**File:** `data/companies/{Company Name}/target_roles.json`
```json
{
  "target_roles": [
    {
      "title": "VP of Product Development",
      "priority": 1,
      "rationale": "Comprehensive explanation of why this role matters, what use cases of Tedlar are relevant to them, why they'd care personally (KPIs, pain points), and how company context makes this role critical"
    }
  ]
}
```

## Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   STAGE 4: OUTREACH GENERATION              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 4.1: Contact Analysis & Engagement Strategy          │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Input:                                             │    │
│  │ - Contact info (Sales Nav export)                  │    │
│  │ - Company research.json                            │    │
│  │ - Company scoring.json                             │    │
│  │ - Target roles.json                                │    │
│  │                                                     │    │
│  │ LLM Analyzes:                                      │    │
│  │ - Match contact title to target role              │    │
│  │ - Extract personalization hooks from background    │    │
│  │ - Map company pain points to this role's concerns │    │
│  │ - Identify timing factors                          │    │
│  │                                                     │    │
│  │ Output:                                            │    │
│  │ - Recommended talking points (role-specific)      │    │
│  │ - Key strengths (why Tedlar for this person)      │    │
│  │ - Potential objections                             │    │
│  │ - Timing factors                                   │    │
│  │ - Personalization hooks                            │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  Step 4.2: Outreach Message Generation                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Input: Engagement strategy from 4.1                │    │
│  │                                                     │    │
│  │ LLM Generates:                                     │    │
│  │ - Email subject + body (80-150 words)             │    │
│  │ - OR LinkedIn message (200-300 chars)             │    │
│  │                                                     │    │
│  │ Output: Draft outreach message                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Output Schema

### Step 4.1: Contact Analysis Output
**File:** `data/contacts/{Company Name}/{Contact Name}_analysis.json`

```json
{
  "contact_id": "cont_001",
  "full_name": "Laura Noll",
  "title": "VP of Product Development",
  "company_name": "Epson America, Inc.",
  "linkedin_url": "...",

  "role_match": {
    "matched_target_role": "VP of Product Development",
    "priority": 1,
    "role_rationale_from_stage3": "..."
  },

  "engagement_strategy": {
    "recommended_talking_points": [
      "Point 1 specific to their role and company context",
      "Point 2 tied to pain points this role owns",
      "Point 3 based on company's market positioning"
    ],

    "key_strengths": [
      "Why Tedlar is compelling for this specific person at this company"
    ],

    "potential_objections": [
      "Concerns they might have based on role/company"
    ],

    "timing_factors": [
      "Recent company news/activity making now a good time",
      "Trade show they're attending",
      "Product launch timing"
    ]
  },

  "personalization_hooks": [
    {
      "hook": "8 years at 3M in product management",
      "messaging_angle": "Reference shared industry experience"
    },
    {
      "hook": "MBA from Ohio State",
      "messaging_angle": "Lead with ROI/business case"
    }
  ],

  "recommended_channel": "email",
  "recommended_approach": "Lead with product differentiation angle"
}
```

### Step 4.2: Outreach Message Output
**File:** `data/contacts/{Company Name}/{Contact Name}_outreach.json`

```json
{
  "outreach_id": "out_001",
  "contact_id": "cont_001",
  "channel": "email",

  "message": {
    "subject": "Quick question about Epson's outdoor film durability",
    "body": "Hi Laura,\n\n[Personalized opening]...",
    "word_count": 125
  },

  "personalization_analysis": {
    "hooks_used": ["3M background", "Product development role"],
    "talking_points_used": ["UV resistance", "Premium positioning"],
    "value_prop_emphasized": "25+ year outdoor durability",
    "pain_point_addressed": "Product differentiation in competitive market"
  },

  "quality_metrics": {
    "personalization_score": "high",
    "specificity_score": "high"
  },

  "status": "draft",
  "generated_at": "2026-01-23T..."
}
```

## Next: Implement Prompts

The prompts for Step 4.1 and 4.2 should be added to `src/prompts.py`.
