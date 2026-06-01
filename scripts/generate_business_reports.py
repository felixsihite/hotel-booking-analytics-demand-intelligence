"""Generate business-facing markdown reports from analytics outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
OUTPUT_INSIGHTS_DIR = PROJECT_ROOT / "outputs" / "insights"
OUTPUT_TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1%}"


def load_kpis() -> dict:
    with (OUTPUT_INSIGHTS_DIR / "kpi_summary.json").open("r", encoding="utf-8") as fp:
        return json.load(fp)


def executive_report(kpis: dict) -> str:
    risk = pd.read_csv(OUTPUT_TABLES_DIR / "cancellation_risk_matrix.csv").head(5)
    revenue = pd.read_csv(OUTPUT_TABLES_DIR / "revenue_optimization_plan.csv").head(5)
    personas = pd.read_csv(OUTPUT_TABLES_DIR / "customer_persona_segments.csv").head(5)

    risk_rows = "\n".join(
        f"- {row.hotel} | {row.market_segment} | {row.distribution_channel} | {row.lead_time_band}: "
        f"{row.cancellation_rate:.1%} cancellation rate and {money(row.lost_revenue_estimate)} exposure"
        for row in risk.itertuples()
    )
    revenue_rows = "\n".join(
        f"- {row.hotel} {row.arrival_year_month}: {pct(row.revenue_opportunity_index)} opportunity index, "
        f"{money(row.estimated_revenue_upside)} estimated upside"
        for row in revenue.itertuples()
    )
    persona_rows = "\n".join(
        f"- {row.country} | {row.market_segment} | {row.customer_type}: "
        f"{money(row.realized_revenue)} realized revenue, {row.cancellation_rate:.1%} cancellation rate"
        for row in personas.itertuples()
    )

    return f"""# Executive Business Insights

## Portfolio Case

Hotel Booking Analytics & Demand Intelligence analyzes booking behavior, customer segments, cancellation risk, occupancy utilization, and revenue opportunity across the Hotel Booking Demand Dataset.

## Executive KPI Snapshot

- Total bookings analyzed: {kpis["total_bookings"]:,}
- Date coverage: {kpis["date_min"]} to {kpis["date_max"]}
- Estimated occupancy rate: {pct(kpis["estimated_occupancy_rate"])}
- Cancellation rate: {pct(kpis["cancellation_rate"])}
- Realized revenue estimate: {money(kpis["realized_revenue"])}
- Lost revenue estimate from cancellations: {money(kpis["lost_revenue_estimate"])}
- Revenue opportunity index: {pct(kpis["revenue_opportunity_index"])}

## Priority Cancellation Risks

{risk_rows}

## Revenue Optimization Priorities

{revenue_rows}

## Highest-Value Customer Segments

{persona_rows}

## Strategic Recommendations

- Apply risk-based cancellation controls for high-risk long-lead and volatile channel segments.
- Prioritize reliable high-value customer segments for loyalty, direct booking migration, and targeted retention.
- Use occupancy forecasts to align staffing, inventory restrictions, and channel availability ahead of peak months.
- Deploy promotional packages during low-demand months while protecting ADR during high-demand periods.
- Monitor lost revenue estimate as a commercial KPI alongside realized revenue, ADR, and occupancy.
"""


def revenue_report(kpis: dict) -> str:
    revenue = pd.read_csv(OUTPUT_TABLES_DIR / "revenue_optimization_plan.csv").head(12)
    monthly = pd.read_csv(PROCESSED_DIR / "monthly_demand.csv")
    peak = monthly.sort_values("occupancy_rate_estimate", ascending=False).head(6)
    low = monthly.sort_values("occupancy_rate_estimate", ascending=True).head(6)

    peak_rows = "\n".join(
        f"- {row.hotel} {row.arrival_year_month}: {pct(row.occupancy_rate_estimate)}, ADR {money(row.adr)}"
        for row in peak.itertuples()
    )
    low_rows = "\n".join(
        f"- {row.hotel} {row.arrival_year_month}: {pct(row.occupancy_rate_estimate)}, "
        f"opportunity index {pct(row.revenue_opportunity_index)}"
        for row in low.itertuples()
    )
    action_rows = "\n".join(
        f"- {row.hotel} {row.arrival_year_month}: {row.pricing_action} "
        f"({money(row.estimated_revenue_upside)} estimated upside)"
        for row in revenue.itertuples()
    )

    return f"""# Revenue Optimization Report

## Objective

Identify demand periods, utilization gaps, cancellation leakage, and pricing opportunities that can improve revenue stability and room utilization.

## Commercial Context

The dataset shows {money(kpis["lost_revenue_estimate"])} in estimated cancellation exposure and an aggregate revenue opportunity index of {pct(kpis["revenue_opportunity_index"])}. This makes cancellation mitigation and demand-period pricing controls central to the revenue strategy.

## Peak Demand Periods

{peak_rows}

## Low-Demand Periods

{low_rows}

## Dynamic Pricing Recommendations

{action_rows}

## Revenue Management Actions

- Peak demand: raise ADR selectively, restrict discounts, protect direct-channel inventory, and tighten cancellation rules.
- Base demand: maintain rate discipline, optimize channel mix, and use targeted campaigns for reliable segments.
- Low demand: create bundled packages, flexible cancellation offers, and direct booking incentives.
- High cancellation exposure: test deposits, pre-arrival confirmation workflows, and risk-based overbooking guardrails.
"""


def interview_summary(kpis: dict) -> str:
    return f"""# Interview Summary

## Business Problem

Hotels often face challenges in managing booking demand, reducing cancellation rates, and optimizing room occupancy. High cancellation rates can lead to revenue loss, while poor understanding of customer booking behavior makes operational planning difficult.

## Business Solution

Conducted comprehensive hotel booking analytics using Python, SQL, and R to identify booking trends, cancellation patterns, customer segments, and seasonal demand fluctuations. Built forecasting models and executive dashboards to support occupancy optimization, pricing strategy development, operational planning, and revenue growth initiatives.

## Business Impact

- Analyzed {kpis["total_bookings"]:,} cleaned booking records across {kpis["date_min"]} to {kpis["date_max"]}.
- Quantified cancellation rate at {pct(kpis["cancellation_rate"])} and estimated cancellation revenue exposure at {money(kpis["lost_revenue_estimate"])}.
- Built occupancy and booking demand forecasting workflows for future planning.
- Identified high-risk customer and channel segments for targeted cancellation controls.
- Created SQL KPI query suites for booking, occupancy, cancellation, and revenue optimization analysis.
- Delivered a dark-themed Streamlit executive analytics application for recruiter-ready business storytelling.
"""


def run() -> None:
    OUTPUT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    kpis = load_kpis()
    (OUTPUT_REPORTS_DIR / "executive_business_insights.md").write_text(executive_report(kpis), encoding="utf-8")
    (OUTPUT_REPORTS_DIR / "revenue_optimization_report.md").write_text(revenue_report(kpis), encoding="utf-8")
    (OUTPUT_INSIGHTS_DIR / "interview_summary.md").write_text(interview_summary(kpis), encoding="utf-8")
    print("Business reports generated.")


if __name__ == "__main__":
    run()