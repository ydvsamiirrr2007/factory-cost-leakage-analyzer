# 🏭 Factory Cost Leakage Analyzer

A complete data analytics project to identify, quantify, and prioritize cost leakages in manufacturing.

## Features
- Automated leakage calculation (Material, Labor, Energy, Maintenance, Quality, Downtime).
- Priority scoring with Critical/High/Medium/Low classification.
- **Innovation**: Cascade Loss Intelligence – reveals hidden indirect losses.
- What‑if scenario analysis.
- 7‑page Power BI dashboard for executive decision support.

## Technology
- Python 3.9+, Pandas, NumPy, Matplotlib, Seaborn, Scikit‑learn.
- PostgreSQL (or any SQL DB).
- Power BI Desktop.

## Setup
1. Install Python packages: `pip install -r requirements.txt`
2. Run `python src/data_generator.py` to create synthetic data.
3. Load CSV into your database or connect Power BI directly to CSV.
4. Run `python src/analysis.py` for full analysis and cascade outputs.
5. Open Power BI, load data, and follow the dashboard design.

## Folder Structure
- `data/` – raw and generated data.
- `sql/` – analytical queries.
- `src/` – Python scripts.
- `dashboards/` – Power BI design guide.
- `reports/` – final report and visualizations.

## Quick Start
```bash
git clone <repo>
cd factory-cost-leakage-analyzer
pip install -r requirements.txt
python main.py   # runs generator + analysis