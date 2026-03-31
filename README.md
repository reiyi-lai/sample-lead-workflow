# DuPont Tedlar AI Lead Generation Pipeline

## Installation & Setup

### 1. Clone this repository

### 2. Set up Python environment

```bash
pip install -r requirements.txt
```

### 3. Configure .env in root folder

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Run the App

### Option 1: Run the full AI workflow

```bash
python src/main.py
```

### Option 2: Run individual stages

Each stage can be run independently, but note that Stages 2-4 depend on output from previous stages. Run Stage 1 first to generate the initial data.

```bash
python src/stage1_event_discovery.py

python src/stage2_company_qualification.py

python src/stage3_contact_finding.py

python src/stage4_outreach_generation.py
```

## Running the Dashboard

```bash
cd dashboard
npm install
npm run dev
```

View dashboard at [http://localhost:3000](http://localhost:3000).

## Output Data

Pipeline outputs are saved to `data/`:

- `data/events/` — Discovered and scored events
- `data/companies/{CompanyName}/` — Research, scoring, target roles, and outreach per company

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
└── data/                   # JSON output produced at each stage
```
## Documentation

See [DOCUMENTATION.md](./DOCUMENTATION.md) for detailed architecture and data processing documentation.