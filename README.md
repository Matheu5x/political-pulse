# Political Pulse – Starter Repo

A lean, solo-friendly starter for a **Weekly Political Sentiment Report** that can scale to a team.

## What you get
- Deterministic **ETL scripts** (Google Trends + Reddit) with a **mock mode** (works without API keys).
- Lightweight **analysis**: sentiment (VADER), issue classification, dedupe.
- **Report generator**: builds a weekly PDF from processed CSVs.
- Optional **Flask dashboard** skeleton.
- Clear foldering + a single `run_etl.py` to orchestrate.

## Quick start
```bash
# 1) Create a virtual env (Windows PowerShell example)
python -m venv .venv
. .venv/Scripts/Activate.ps1

# 2) Install deps
pip install -r requirements.txt

# 3) Copy config and edit
cp config.example.yaml config.yaml
# (Optional) set env vars in .env

# 4) Run ETL in MOCK mode (no API keys needed)
python run_etl.py --mock

# 5) Generate sample report (PDF)
python reports/generate_report.py --week 2025-08-10
```

The ETL writes CSVs to `data/processed/`. The report generator reads those CSVs and builds a PDF in `reports/`.

## Folder structure
```
political-pulse/
├── data/
│   ├── raw/
│   └── processed/
├── etl/
│   ├── fetch_google_trends.py
│   ├── fetch_reddit.py
│   └── clean_text.py
├── analysis/
│   ├── sentiment_analysis.py
│   └── topic_classifier.py
├── app/
│   └── main.py
├── reports/
│   ├── templates/weekly_report_template.md
│   └── generate_report.py
├── tests/
├── run_etl.py
├── requirements.txt
├── config.example.yaml
├── .env.example
└── README.md
```

## Data flow
```
fetch_*  -> data/raw/*.json
cleaning -> data/processed/items.csv (one row per item)
analysis -> adds columns: sentiment, issues[], locality, is_duplicate
report   -> reads processed CSVs and renders PDF
```

## Notes
- **Mock mode** produces deterministic fake items so you can demo immediately.
- When ready, add API keys and disable `--mock` to fetch real data.
- Keep it ethical: only collect public/allowed data, respect ToS and local laws.
