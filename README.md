# 🧠 Mini Decision Feed

A production-ready data pipeline that ingests business data, transforms it with dbt,
validates it with pytest, and serves AI-generated insights via a REST API — deployed on AWS.

---

## 🌐 Live API

| Endpoint | URL |
|---|---|
| Health check | `GET /health` |
| Product A insights | `GET /insights/Product_A` |
| Product B insights | `GET /insights/Product_B` |
| Product C insights | `GET /insights/Product_C` |

**Base URL:** `https://j9owsglvo3.execute-api.us-east-1.amazonaws.com` ← replace with your API Gateway URL

**Sample response:**
```json
{
  "product": "Product_A",
  "total_revenue": 209000.0,
  "best_month": "2024-12",
  "worst_month": "2024-03",
  "avg_mom_growth_pct": 8.14,
  "risk_flag": true,
  "summary": "Product A generated $209,000 in 2024 with strong 8.14% average growth, though March and June experienced revenue drops requiring investigation.",
  "recommendations": [
    "Investigate root causes of March and June revenue drops to identify seasonal patterns.",
    "Implement early warning systems to detect monthly revenue declines exceeding 10%.",
    "Capitalize on Q4 momentum by replicating successful strategies into 2025."
  ]
}
```

---

## 🏗 Architecture

```
CSV Data
   │
   ▼
Python Ingest ──► DuckDB (raw_sales)
                     │
                     ▼
                  dbt Models
                  ├── stg_sales        (clean + typed)
                  └── mart_revenue_growth  (MoM growth, risk flags)
                     │
                     ├──► pytest (10 quality checks)
                     │
                     ▼
                  FastAPI + Claude API
                     │
                     ▼
              AWS Lambda + API Gateway
                  (public HTTPS endpoint)
```

---

## ⚡ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Database | DuckDB |
| Transformation | dbt-duckdb |
| Quality | pytest |
| API framework | FastAPI + Pydantic |
| AI insight engine | Claude API (Anthropic) |
| Deployment | AWS Lambda + API Gateway |
| Secret storage | AWS Secrets Manager |
| Infrastructure | AWS (us-east-1) |

---

## 🗂 Project Structure

```
mini-decision-feed/
├── data/
│   └── sales.csv              ← Raw input (3 products × 12 months)
├── pipeline/
│   └── ingest.py              ← Loads CSV into DuckDB
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── schema.yml
│       ├── staging/
│       │   └── stg_sales.sql          ← Cleans raw data
│       └── marts/
│           └── mart_revenue_growth.sql ← MoM growth + risk flags
├── tests/
│   └── test_quality.py        ← 10 pytest data quality checks
├── api/
│   └── main.py                ← FastAPI app + Claude insight engine
├── deployment/
│   ├── lambda_handler.py      ← Mangum adapter for AWS Lambda
│   └── build_lambda.ps1       ← Packages app for Lambda (Windows)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Run Locally

### Prerequisites
- Python 3.11+
- Git

### Setup

```bash
git clone https://github.com/gviacava-code/mini-decision-feed.git
cd mini-decision-feed

python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### Run the pipeline

```bash
# Step 1 — Ingest
python pipeline/ingest.py

# Step 2 — Transform
cd dbt_project
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..

# Step 3 — Quality checks
pytest tests/ -v

# Step 4 — Start API
uvicorn api.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for the interactive API explorer.

---

## ☁️ AWS Deployment

The app runs on AWS Lambda behind API Gateway.

**To redeploy after changes:**

```powershell
# Windows PowerShell — run from project root
.\deployment\build_lambda.ps1
# Then upload lambda_package.zip to S3 and update Lambda
```

**AWS services used:**
- **Lambda** — runs the FastAPI app serverlessly
- **API Gateway (HTTP)** — public HTTPS URL with routing
- **S3** — stores the deployment zip (>50MB)
- **Secrets Manager** — stores the Anthropic API key securely
- **CloudWatch** — logs and monitoring

---

## 📊 Data Quality

10 automated pytest checks run after every dbt transformation:

| Check | Layer |
|---|---|
| Table exists | Raw |
| Row count = 36 | Raw |
| No null products | Raw |
| No null revenue | Raw |
| No negative revenue | Raw |
| No negative units | Raw |
| Only valid product names | Raw |
| Mart row count matches | Mart |
| Growth % null only for first month | Mart |
| Revenue always positive in mart | Mart |

---

## 🤖 AI Insight Engine

Each API call sends the product's full monthly trend to Claude (claude-sonnet-4-5)
and receives back a structured JSON response validated by Pydantic:

- **summary** — one sentence describing 2024 performance
- **recommendations** — 3 specific, data-driven action items
- **risk_flag** — true if any month had >10% revenue drop
