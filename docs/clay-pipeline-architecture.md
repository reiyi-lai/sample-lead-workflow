# InstaLILY GTM Pipeline — Clay Workbook Architecture

## Pipeline Overview

The pipeline moves from **Event Attendee Lists → Company Enrichment & Qualification → Contact Finding → Personalized Outreach → LemList Sequences**.

Everything runs inside a **Clay Workbook** with 4 linked tables, using Claygent for AI prompting and Clay's native enrichments for data. LemList handles the actual sending (email + LinkedIn).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CLAY WORKBOOK: InstaLILY GTM                           │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  TABLE 1: EVENTS & ATTENDEES (Input)                                      │  │
│  │                                                                           │  │
│  │  Data Sources:                                                            │  │
│  │    • CSV/Excel upload from AE team (attendee lists from events)           │  │
│  │    • Manual entry of event name, dates, location                          │  │
│  │    • Optional: Clay Web Scraper on event exhibitor pages                  │  │
│  │                                                                           │  │
│  │  Columns:                                                                 │  │
│  │    event_name | company_name | website_url | attendee_name |              │  │
│  │    attendee_role | attendee_email | source | confidence                   │  │
│  │                                                                           │  │
│  │  Enrichments:                                                             │  │
│  │    → Clay "Find Company" (normalize & enrich company from name/URL)       │  │
│  │    → Waterfall: domain lookup (Clearbit → Apollo → Hunter)                │  │
│  │    → Dedup filter (by domain) to remove duplicate companies               │  │
│  │                                                                           │  │
│  │  Output: Deduplicated company list with domains                           │  │
│  └──────────────────────────┬────────────────────────────────────────────────┘  │
│                             │                                                   │
│                             ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  TABLE 2: COMPANY QUALIFICATION (ICP Scoring)                             │  │
│  │                                                                           │  │
│  │  Data Sources:                                                            │  │
│  │    • Linked from Table 1 (unique companies)                               │  │
│  │                                                                           │  │
│  │  Enrichments (Waterfall + Claygent):                                      │  │
│  │    → Clay "Enrich Company" (revenue, headcount, industry, HQ, funding)    │  │
│  │    → Clearbit / Apollo / ZoomInfo waterfall for firmographics             │  │
│  │    → Claygent #1: "Research & Score ICP Fit"                              │  │
│  │        Prompt: Given {company_name}, {website_url}, {industry},           │  │
│  │        {revenue}, {headcount}, research this company and score            │  │
│  │        its fit with InstaLILY's ICP across 4 dimensions:                  │  │
│  │        industry_fit, size_fit, strategic_relevance, market_activity.      │  │
│  │        Return scores (1-10) with rationales.                              │  │
│  │    → Formula column: weighted ICP score (0-100)                           │  │
│  │    → Filter: ICP score >= 70 (qualified)                                  │  │
│  │                                                                           │  │
│  │  Columns:                                                                 │  │
│  │    company_name | domain | revenue | headcount | industry | hq |          │  │
│  │    funding_stage | pe_backed | industry_fit_score |                        │  │
│  │    size_fit_score | strategic_relevance_score |                            │  │
│  │    market_activity_score | icp_weighted_score |                            │  │
│  │    qualification_summary | qualified (Y/N)                                │  │
│  │                                                                           │  │
│  │  Output: Qualified companies (score >= 70)                                │  │
│  └──────────────────────────┬────────────────────────────────────────────────┘  │
│                             │                                                   │
│                             ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  TABLE 3: CONTACTS & TARGET ROLES                                         │  │
│  │                                                                           │  │
│  │  Data Sources:                                                            │  │
│  │    • Linked from Table 2 (qualified companies only)                       │  │
│  │    • Attendee data from Table 1 (if attendee matches a target role)       │  │
│  │                                                                           │  │
│  │  Enrichments (Claygent + People Search):                                  │  │
│  │    → Claygent #2: "Identify Target Roles"                                 │  │
│  │        Prompt: Given {company_name}, {qualification_summary},             │  │
│  │        {icp_scores_and_rationales}, identify up to 3 decision-maker       │  │
│  │        roles to target for InstaLILY. Return title, priority,             │  │
│  │        rationale for each.                                                │  │
│  │    → Clay "Find People" / Apollo People Search / LinkedIn Sales Nav       │  │
│  │        Search for actual contacts matching target role titles              │  │
│  │    → Waterfall: email finder (Apollo → Hunter → Snov.io → Dropcontact)   │  │
│  │    → Waterfall: LinkedIn URL (Apollo → Phantombuster → Prospeo)           │  │
│  │    → Email verification (ZeroBounce / NeverBounce)                        │  │
│  │                                                                           │  │
│  │  Columns:                                                                 │  │
│  │    company_name | role_title | role_priority | role_rationale |            │  │
│  │    contact_name | contact_email | email_verified | linkedin_url |          │  │
│  │    job_title_actual | seniority                                           │  │
│  │                                                                           │  │
│  │  Output: Verified contacts with emails + LinkedIn URLs                    │  │
│  └──────────────────────────┬────────────────────────────────────────────────┘  │
│                             │                                                   │
│                             ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  TABLE 4: OUTREACH PERSONALIZATION                                        │  │
│  │                                                                           │  │
│  │  Data Sources:                                                            │  │
│  │    • Linked from Table 3 (verified contacts)                              │  │
│  │    • Company data from Table 2                                            │  │
│  │    • Role rationale from Table 3                                          │  │
│  │                                                                           │  │
│  │  Enrichments (Claygent):                                                  │  │
│  │    → Claygent #3: "Engagement Strategy"                                   │  │
│  │        Prompt: Given {contact_name}, {job_title}, {company_name},         │  │
│  │        {qualification_summary}, {role_rationale}, develop a               │  │
│  │        personalized engagement strategy. Return personalization            │  │
│  │        hooks, recommended channel, and approach.                          │  │
│  │    → Claygent #4: "Write Outreach Email"                                  │  │
│  │        Prompt: Given {engagement_strategy}, {contact_name},               │  │
│  │        {company_name}, write a personalized cold email.                   │  │
│  │        80-150 words, conversational, one clear CTA.                       │  │
│  │    → Claygent #5: "Write LinkedIn Message"                                │  │
│  │        Prompt: Given {engagement_strategy}, {contact_name},               │  │
│  │        write a LinkedIn connection request (200-300 chars).               │  │
│  │                                                                           │  │
│  │  Columns:                                                                 │  │
│  │    contact_name | company_name | email | linkedin_url |                   │  │
│  │    engagement_strategy | personalization_hooks |                           │  │
│  │    email_subject | email_body | linkedin_message |                        │  │
│  │    recommended_channel | status                                           │  │
│  │                                                                           │  │
│  │  Output: Ready-to-send personalized messages                              │  │
│  └──────────────────────────┬────────────────────────────────────────────────┘  │
│                             │                                                   │
└─────────────────────────────┼───────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        LEMLIST (Outreach Execution)                             │
│                                                                                 │
│  Clay → LemList Integration (native):                                          │
│    • "Add Lead to Campaign" action pushes contacts from Table 4                │
│    • Passes: email, linkedin_url, first_name, company,                         │
│      email_subject, email_body, linkedin_message, icebreaker                   │
│    • Custom variables in LemList templates map to Clay columns                 │
│                                                                                 │
│  LemList Campaign Structure (Multichannel Sequence):                           │
│                                                                                 │
│    Day 1:  📧 Email #1 (personalized from Clay — email_body)                  │
│    Day 3:  🔗 LinkedIn Profile Visit                                           │
│    Day 5:  🔗 LinkedIn Connection Request (linkedin_message from Clay)         │
│    Day 8:  📧 Email #2 (follow-up — reference Email #1, add value)            │
│    Day 12: 🔗 LinkedIn InMail / Message (if connected)                         │
│    Day 16: 📧 Email #3 (breakup email — last touch, soft CTA)                 │
│                                                                                 │
│  Safety:                                                                       │
│    • Email: warmup via LemWarm, domain rotation, custom tracking domain        │
│    • LinkedIn: max 100 actions/day, human-like delays                          │
│    • Auto-pause on reply/out-of-office detection                               │
│                                                                                 │
│  Tracking:                                                                     │
│    • Opens, clicks, replies tracked in LemList                                 │
│    • Reply data can be synced back to Clay or CRM                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
AE Event Attendee Lists (CSV/Manual)
        │
        ▼
  ┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
  │  Table 1:   │     │  Table 2:        │     │  Table 3:        │     │  Table 4:        │
  │  Events &   │────▶│  Company         │────▶│  Contacts &      │────▶│  Outreach        │
  │  Attendees  │     │  Qualification   │     │  Target Roles    │     │  Personalization  │
  │             │     │                  │     │                  │     │                  │
  │  Import +   │     │  Firmographics + │     │  Claygent roles +│     │  Claygent email +│
  │  Dedup      │     │  Claygent ICP    │     │  People search + │     │  Claygent LI msg │
  │             │     │  Score >= 70     │     │  Email verify    │     │                  │
  └─────────────┘     └──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                                                  │
                                                                                  ▼
                                                                          ┌───────────────┐
                                                                          │   LemList     │
                                                                          │               │
                                                                          │  Email + LI   │
                                                                          │  Sequences    │
                                                                          │               │
                                                                          │  Track Opens  │
                                                                          │  & Replies    │
                                                                          └───────────────┘
```

---

## Claygent Prompts Summary

| # | Claygent | Input | Output | Maps to Pipeline Stage |
|---|----------|-------|--------|----------------------|
| 1 | ICP Research & Scoring | company_name, website, firmographics | 4 scores + rationales + summary | Stage 2 |
| 2 | Target Role Identification | company_name, ICP scores, summary | Up to 3 roles with rationale | Stage 3 |
| 3 | Engagement Strategy | contact, company, ICP data, role rationale | hooks, channel, approach | Stage 4 Turn 1 |
| 4 | Email Copy | engagement strategy, contact, company | subject + body | Stage 4 Turn 2 |
| 5 | LinkedIn Copy | engagement strategy, contact, company | connection request message | Stage 4 Turn 2 |

---

## Key Differences from Code Pipeline

| Aspect | Python Pipeline (Before) | Clay Workbook (After) |
|--------|-------------------------|----------------------|
| Event discovery | Automated via Claude web search | **Skipped** — AEs provide event attendee lists directly |
| Company enrichment | Claude web search per company | Clay waterfall enrichment (Clearbit/Apollo/ZoomInfo) + Claygent |
| ICP scoring | Claude API call | Claygent prompt (same logic, no code) |
| Contact finding | Claude identifies roles → Sales Nav URLs | Claygent identifies roles → Clay People Search finds actual contacts with verified emails |
| Outreach generation | Claude 2-turn conversation | Claygent prompts for strategy + copy |
| Outreach sending | Manual / Clay webhook | **LemList** multichannel sequences (email + LinkedIn, automated) |
| Tracking | None | LemList open/click/reply tracking |
| Resume/dedup | File-based JSON checks | Clay native dedup + table filters |
| Rate limiting | Custom token bucket | Clay handles API limits internally |

---

## Setup Steps

1. **Create Clay Workbook** with 4 tables (Events & Attendees → Company Qualification → Contacts → Outreach)
2. **Configure enrichment providers** (Clearbit, Apollo, ZoomInfo, Hunter, etc.)
3. **Build 5 Claygent prompts** using the prompts from `prompts.py` (adapted for Clay's column reference syntax `{column_name}`)
4. **Set up LemList campaign** with multichannel sequence template (email + LinkedIn steps)
5. **Connect Clay → LemList** via native integration, mapping personalized columns to LemList custom variables
6. **Import first event attendee list** as CSV into Table 1 and run the workbook
