"""Cancellation risk analysis exports."""

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

    bookings = pd.read_csv(PROCESSED_DIR / "hotel_bookings_cleaned.csv")

    risk_matrix = (
        bookings.groupby(
            ["hotel", "market_segment", "distribution_channel", "deposit_type", "lead_time_band"],
            observed=False,
        )
        .agg(
            bookings=("booking_id", "count"),
            cancellations=("is_canceled", "sum"),
            cancellation_rate=("is_canceled", "mean"),
            lost_revenue_estimate=("lost_revenue_estimate", "sum"),
            average_lead_time=("lead_time", "mean"),
            previous_cancellations=("previous_cancellations", "mean"),
            special_request_rate=("total_of_special_requests", "mean"),
        )
        .reset_index()
    )
    risk_matrix = risk_matrix[risk_matrix["bookings"] >= 50].copy()
    risk_matrix["risk_priority_score"] = (
        risk_matrix["cancellation_rate"] * 55
        + (
            risk_matrix["lost_revenue_estimate"]
            / risk_matrix["lost_revenue_estimate"].max()
        ).fillna(0)
        * 30
        + (risk_matrix["average_lead_time"] / risk_matrix["average_lead_time"].max()).fillna(0)
        * 15
    ).round(2)
    risk_matrix = risk_matrix.sort_values("risk_priority_score", ascending=False)
    risk_matrix.to_csv(OUTPUT_TABLES_DIR / "cancellation_risk_matrix.csv", index=False)

    driver_summary = (
        bookings.groupby("lead_time_band", observed=False)
        .agg(
            bookings=("booking_id", "count"),
            cancellation_rate=("is_canceled", "mean"),
            lost_revenue_estimate=("lost_revenue_estimate", "sum"),
            average_reliability_score=("booking_reliability_score", "mean"),
        )
        .reset_index()
    )
    driver_summary.to_csv(OUTPUT_TABLES_DIR / "lead_time_cancellation_drivers.csv", index=False)

    top_risk = risk_matrix.iloc[0]
    insight = (
        "Cancellation Risk Summary\n"
        "=========================\n"
        f"Highest-risk segment: {top_risk['hotel']} | {top_risk['market_segment']} | "
        f"{top_risk['distribution_channel']} | {top_risk['deposit_type']} | "
        f"{top_risk['lead_time_band']}.\n"
        f"Cancellation rate: {top_risk['cancellation_rate']:.1%}; "
        f"estimated lost revenue: {top_risk['lost_revenue_estimate']:,.2f}.\n\n"
        "Business action: apply risk-based overbooking guardrails, earlier confirmation outreach, "
        "and deposit or prepayment tests for high-risk long-lead segments."
    )
    (OUTPUT_INSIGHTS_DIR / "cancellation_risk_summary.txt").write_text(insight, encoding="utf-8")
    print("Cancellation risk exports created.")


if __name__ == "__main__":
    run()