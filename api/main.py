"""
SESSION 3 — FastAPI + Claude AI Insight Engine
───────────────────────────────────────────────
Serves clean data from DuckDB and calls Claude to generate
structured business insights for each product.

Run locally with:
    uvicorn api.main:app --reload
    (run this from the ROOT folder, not from inside api/)

Then open: http://127.0.0.1:8000/docs
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
DB_PATH  = os.path.join(ROOT_DIR, "data", "sales.duckdb")

VALID_PRODUCTS = ["Product_A", "Product_B", "Product_C"]

# ── Pydantic response model ─────────────────────────────────────────────────
# This defines the exact shape of JSON the API will return.
# Pydantic validates Claude's output against this before sending it.

class InsightResponse(BaseModel):
    product: str
    total_revenue: float
    best_month: str
    worst_month: str
    avg_mom_growth_pct: float
    risk_flag: bool
    summary: str
    recommendations: list[str]


# ── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Mini Decision Feed",
    description="AI-powered business insights from your sales pipeline.",
    version="1.0.0",
)


# ── Helper: query DuckDB ────────────────────────────────────────────────────
def get_product_data(product: str) -> dict:
    """Pulls all mart data for one product and computes summary stats."""
    con = duckdb.connect(DB_PATH, read_only=True)

    rows = con.execute("""
        SELECT
            month,
            revenue,
            units_sold,
            mom_growth_pct,
            rolling_3m_avg_revenue,
            is_revenue_drop
        FROM mart_revenue_growth
        WHERE product = ?
        ORDER BY month
    """, [product]).fetchdf()

    con.close()

    if rows.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {product}")

    # Build a clean summary dict to pass to Claude
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
def get_claude_insight(data: dict) -> dict:
    """
    Sends product data to Claude and asks for structured JSON back.
    Returns a dict with: summary (str) + recommendations (list of 3 strings).
    """

    from anthropic import Anthropic
    import os, json

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Build monthly trend block cleanly
    lines = []
    for r in data["monthly_data"]:
        month = str(r["month"])[:7]
        revenue = f"${r['revenue']:,.0f}"
        mom = (
            f"{r['mom_growth_pct']:+.1f}%"
            if r["mom_growth_pct"] is not None
            else "n/a"
        )
        lines.append(f"  {month}: {revenue} | MoM: {mom}")

    monthly_block = "\n".join(lines)

    # Prompt
    prompt = f"""
You are a senior business analyst. Analyze this sales data and return a JSON object.

PRODUCT DATA:
- Product: {data['product']}
- Total 2024 revenue: ${data['total_revenue']:,.0f}
- Best month: {data['best_month']} (${data['best_month_revenue']:,.0f})
- Worst month: {data['worst_month']} (${data['worst_month_revenue']:,.0f})
- Average month-over-month growth: {data['avg_mom_growth_pct']}%
- Revenue drop alerts: {data['risk_months'] if data['risk_months'] else 'None'}

Monthly revenue trend (oldest to newest):

{monthly_block}

Return ONLY a valid JSON object with exactly these two fields:
{{
  "summary": "A single sentence (max 30 words) summarizing the product's 2024 performance.",
  "recommendations": [
    "First specific, actionable recommendation based on the data.",
    "Second specific, actionable recommendation based on the data.",
    "Third specific, actionable recommendation based on the data."
  ]
}}

No preamble. No markdown. No explanation. Only the JSON object.
"""

    # New SDK call
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=800,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.content[0].text.strip()

    # Remove accidental code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


# ── Route ───────────────────────────────────────────────────────────────────
@app.get("/insights/{product}", response_model=InsightResponse)
def get_insights(product: str):
    """
    Returns AI-generated insights for a given product.

    Valid values: Product_A, Product_B, Product_C
    """
    if product not in VALID_PRODUCTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product '{product}'. Valid options: {VALID_PRODUCTS}"
        )

    # Step 1: Pull data from DuckDB
    data = get_product_data(product)

    # Step 2: Ask Claude for the insight
    insight = get_claude_insight(data)

    # Step 3: Assemble and validate the full response via Pydantic
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


# ── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Quick check that the API is running."""
    return {"status": "ok", "db": DB_PATH}
