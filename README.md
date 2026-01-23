# DuPont Tedlar AI Lead Generation Pipeline

## Installation & Setup

### 1. Clone this repository
```

### 2. Set up Python environment

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configure .env in root folder (see .env.example)

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAY_API_KEY=your_clay_api_key_here             # Optional: for contact enrichment
```

## Run the App

### Run the full AI workflow

```bash
python src/main.py
```

### Run individual stages

Each stage can be run independently:

**Note:** Stages 2-4 depend on output from previous stages. Run Stage 1 first to generate the initial data.

```bash
# Stage 1: Event Discovery
python src/stage1_event_discovery.py

# Stage 2: Company Qualification
python src/stage2_company_qualification.py

# Stage 3: Target Role Identification
python src/stage3_contact_finding.py

# Stage 4: Outreach Generation
python src/stage4_outreach_generation.py
```

## Running the Dashboard

```bash
cd dashboard
npm install
npm run dev
```

View at [http://localhost:3000](http://localhost:3000).

## Output Data

Pipeline outputs are saved to `data/`:

- `data/events/` — Discovered and scored events
- `data/companies/{CompanyName}/` — Research, scoring, target roles, and outreach per company

## Documentation

See [DOCUMENTATION.md](./DOCUMENTATION.md) for detailed architecture and data processing documentation.

## Project Structure

```
├── src/                    # Pipeline source code
│   ├── main.py             # Orchestrator (runs full pipeline)
│   ├── stage1_event_discovery.py
│   ├── stage2_company_qualification.py
│   ├── stage3_contact_finding.py
│   ├── stage4_outreach_generation.py
│   ├── prompts.py          # Prompts for LLMs
│   ├── constants.py        # Config & scoring weights
│   └── utils/
│       ├── llm.py          # Claude API wrapper
│       └── scraping.py     # Web scraping utilities
├── dashboard/              # Next.js visualization dashboard
└── data/                   # JSON output produced at each stage)
```
