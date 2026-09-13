# Demo Instructions

## Prerequisites
- Python 3.11+
- No API keys required (all analytics use synthetic data)

## Setup
```bash
cd projects/04_project4_ai_growth_operations_agent
pip install -e ".[dev]"
```

## Run Dashboard
```bash
streamlit run app/Summary.py
```

## Run All Tests
```bash
python -m pytest tests/ -v
```

## Regenerate Synthetic Data
```bash
python scripts/generate_synthetic_data.py
```

## Key files to explore
- `process/00_overview.md` — start here
- `app/Summary.py` — dashboard entry point
- `docs/examples/channel_recommendations.json` — Phase 7 output
- `docs/notebooks/01_acquisition_analysis.ipynb` — acquisition analysis
- `docs/notebooks/02_retention_ltv.ipynb` — retention and LTV analysis
