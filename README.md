# 🧠 Mini Decision Feed

A weekend-built, production-ready data pipeline that ingests business data,
transforms it, runs quality checks, and serves AI-generated insights via a REST API.

Inspired by the Aily Labs Data Practitioner stack.

---

## 🗂 Project Structure

```
mini-decision-feed/
├── data/
│   ├── sales.csv          ← Raw input data
│   └── sales.duckdb       ← Local database (auto-created, gitignored)
├── pipeline/
│   └── ingest.py          ← Session 1: loads CSV into DuckDB
├── dbt_project/           ← Session 2: SQL transformations
├── tests/
│   └── test_quality.py    ← Session 2: data quality checks
├── api/
│   └── main.py            ← Session 3: FastAPI + Claude insight engine
├── .env.example           ← Copy to .env and fill in your keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚡ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Database | DuckDB |
| Transformation | dbt |
| Quality | pytest |
| API | FastAPI + Pydantic |
| AI | Claude API (Anthropic) |
| Cloud Storage | AWS S3 |
| Deployment | AWS Lambda + API Gateway |
| Secrets | AWS Secrets Manager |

---

## 🚀 Quick Start (Session 1)

### Step 1 — Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/mini-decision-feed.git
cd mini-decision-feed
```

### Step 2 — Create a virtual environment
```bash
python -m venv venv

# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Copy the environment file
```bash
cp .env.example .env
# Open .env and fill in your ANTHROPIC_API_KEY (needed for Session 3)
```

### Step 5 — Run the ingestion
```bash
python pipeline/ingest.py
```

You should see:
```
🚀 Starting ingestion...
✅ Ingestion complete — 36 rows loaded into raw_sales
📋 Preview (first 5 rows):
...
🎉 Done! Your DuckDB database is ready at: data/sales.duckdb
```

---

## 📅 Build Sessions

| Session | When | Goal |
|---|---|---|
| 1 | Friday evening | Ingest CSV into DuckDB ✅ |
| 2 | Saturday morning | dbt transforms + pytest |
| 3 | Saturday afternoon | FastAPI + Claude AI insights |
| 4 | Sunday morning | AWS deployment |
| 5 | Sunday afternoon | Polish + README + GitHub |

---

## 🔗 Live API

> Coming after Session 4

`GET https://YOUR_API_GATEWAY_URL/insights/Product_A`

Sample response:
```json
{
  "product": "Product_A",
  "summary": "Product A showed consistent growth throughout 2024, with revenue increasing 117% from January to December.",
  "recommendations": [
    "Increase inventory for Q4 given the strong seasonal trend.",
    "Investigate the March dip to understand and prevent recurrence.",
    "Consider a premium pricing test in Q3 when demand peaks."
  ],
  "risk_flag": false
}
```
