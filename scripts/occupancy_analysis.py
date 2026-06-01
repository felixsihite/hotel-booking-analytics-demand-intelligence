"""Occupancy and revenue optimization analysis exports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
OUTPUT_INSIGHTS_DIR = PROJECT_ROOT / "outputs" / "insights"


def run() -> None:
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    monthly = pd.read_csv(PROCESSED_DIR / "monthly_demand.csv", parse_dates=["arrival_date"])

    revenue_plan = monthly.copy()
    revenue_plan["demand_period"] = pd.cut(
        revenue_plan["occupancy_rate_estimate"],
        bins=[-0.01, 0.45, 0.70, 0.85, 1.01],
        labels=["Low demand", "Base demand", "High demand", "Peak demand"],
    ).astype(str)
    revenue_plan["pricing_action"] = revenue_plan["demand_period"].map(
        {
            "Low demand": "Stimulate demand with packages, flexible cancellation, and channel promotions",
            "Base demand": "Maintain rate discipline and optimize channel mix",
            "High demand": "Increase ADR selectively and protect direct booking inventory",
            "Peak demand": "Yield up rates, restrict discounts, and tighten cancellation controls",
        }
    )
    revenue_plan["estimated_revenue_upside"] = (
        revenue_plan["lost_revenue_estimate"] * 0.35
        + (
            revenue_plan["capacity_room_night_proxy"] - revenue_plan["room_nights_realized"]
        ).clip(lower=0)
        * revenue_plan["adr"]
        * 0.18
    ).round(2)
    revenue_plan = revenue_plan.sort_values("estimated_revenue_upside", ascending=False)
    revenue_plan.to_csv(OUTPUT_TABLES_DIR / "revenue_optimization_plan.csv", index=False)

    occupancy_summary = (
        monthly.groupby(["hotel", "month_name"])
        .agg(
            average_bookings=("bookings", "mean"),
            average_occupancy=("occupancy_rate_estimate", "mean"),
            average_cancellation_rate=("cancellation_rate", "mean"),
            realized_revenue=("realized_revenue", "sum"),
            lost_revenue_estimate=("lost_revenue_estimate", "sum"),
            revenue_opportunity_index=("revenue_opportunity_index", "mean"),
        )
        .reset_index()
        .sort_values(["hotel", "revenue_opportunity_index"], ascending=[True, False])
    )
    occupancy_summary.to_csv(OUTPUT_TABLES_DIR / "seasonal_occupancy_scorecard.csv", index=False)

    top = revenue_plan.iloc[0]
    insight = (
        "Revenue Optimization Summary\n"
        "============================\n"
        f"Highest estimated upside period: {top['hotel']} in {top['arrival_year_month']}.\n"
        f"Revenue opportunity index: {top['revenue_opportunity_index']:.1%}; "
        f"estimated upside: {top['estimated_revenue_upside']:,.2f}.\n\n"
        f"Recommended action: {top['pricing_action']}."
    )
    (OUTPUT_INSIGHTS_DIR / "revenue_optimization_summary.txt").write_text(insight, encoding="utf-8")
    print("Occupancy and revenue optimization exports created.")


if __name__ == "__main__":
    run()