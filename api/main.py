"""
SESSION 3/4 — FastAPI + Claude AI Insight Engine
"""

import os
import json
import duckdb
import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# ── Config ─────────────────────────────────────────────────────────────────
load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_path():
    env_path = os.getenv("DB_PATH")
    if env_path:
        return env_path
    bundled = os.path.join(os.path.dirname(__file__), "..", "data", "sales.duckdb")
    if os.path.exists(bundled):
        return os.path.abspath(bundled)
    return os.path.join(ROOT_DIR, "data", "sales.duckdb")

VALID_PRODUCTS = ["Product_A", "Product_B", "Product_C"]

class InsightResponse(BaseModel):
    product: str
    total_revenue: float
    best_month: str
    worst_month: str
    avg_mom_growth_pct: float
    risk_flag: bool
    summary: str
    recommendations: list[str]

app = FastAPI(
    title="Mini Decision Feed",
    description="AI-powered business insights from your sales pipeline.",
    version="1.0.0",
)

def get_product_data(product: str) -> dict:
    db_path = get_db_path()
    con = duckdb.connect(db_path, read_only=True)
    rows = con.execute("""
        SELECT month, revenue, units_sold,
               mom_growth_pct, rolling_3m_avg_revenue, is_revenue_drop
        FROM mart_revenue_growth
        WHERE product = ?
        ORDER BY month
    """, [product]).fetchdf()
    con.close()

    if rows.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {product}")

    best_row  = rows.loc[rows["revenue"].idxmax()]
    worst_row = rows.loc[rows["revenue"].idxmin()]

    return {
        "product": product,
        "monthly_data": rows.to_dict(orient="records"),
        "total_revenue": round(float(rows["revenue"].sum()), 2),
        "best_month": str(best_row["month"])[:7],
        "best_month_revenue": float(best_row["revenue"]),
        "worst_month": str(worst_row["month"])[:7],
        "worst_month_revenue": float(worst_row["revenue"]),
        "avg_mom_growth_pct": round(float(rows["mom_growth_pct"].dropna().mean()), 2),
        "any_risk_flag": bool(rows["is_revenue_drop"].any()),
        "risk_months": rows[rows["is_revenue_drop"] == True]["month"].astype(str).tolist(),
    }

# ── Helper: call Claude ─────────────────────────────────────────────────────
def format_monthly_row(r):
    """Formats one row of monthly data as a readable string — avoids nested f-strings."""
    month = str(r["month"])[:7]
    revenue = r["revenue"]
    mom = r["mom_growth_pct"]
    mom_str = f"{mom:+.1f}%" if mom is not None and str(mom) != "nan" else "n/a"
    return f"  {month}: ${revenue:,.0f} | MoM: {mom_str}"

def get_claude_insight(data: dict) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    monthly_lines = "\n".join([format_monthly_row(r) for r in data["monthly_data"]])

    prompt = f"""
You are a senior business analyst. Analyze this sales data and return a JSON object.

PRODUCT DATA:
- Product: {data['product']}
- Total 2024 revenue: ${data['total_revenue']:,.0f}
- Best month: {data['best_month']} (${data['best_month_revenue']:,.0f})
- Worst month: {data['worst_month']} (${data['worst_month_revenue']:,.0f})
- Average month-over-month growth: {data['avg_mom_growth_pct']}%
- Revenue drop alerts: {data['risk_months'] if data['risk_months'] else 'None'}

Monthly revenue trend:
{monthly_lines}

Return ONLY a valid JSON object with exactly these two fields:
{{
  "summary": "A single sentence (max 30 words) summarizing performance.",
  "recommendations": [
    "First specific actionable recommendation.",
    "Second specific actionable recommendation.",
    "Third specific actionable recommendation."
  ]
}}
No preamble. No markdown. Only the JSON object.
"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

@app.get("/insights/{product}", response_model=InsightResponse)
def get_insights(product: str):
    if product not in VALID_PRODUCTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product '{product}'. Valid options: {VALID_PRODUCTS}"
        )
    data    = get_product_data(product)
    insight = get_claude_insight(data)
    return InsightResponse(
        product=data["product"],
        total_revenue=data["total_revenue"],
        best_month=data["best_month"],
        worst_month=data["worst_month"],
        avg_mom_growth_pct=data["avg_mom_growth_pct"],
        risk_flag=data["any_risk_flag"],
        summary=insight["summary"],
        recommendations=insight["recommendations"],
    )

@app.get("/health")
def health():
    return {"status": "ok", "db": get_db_path()}
