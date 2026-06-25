## Part 5: TO-DO

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

