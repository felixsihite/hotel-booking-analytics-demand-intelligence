"""Booking intelligence analysis exports."""

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

    bookings = pd.read_csv(PROCESSED_DIR / "hotel_bookings_cleaned.csv", parse_dates=["arrival_date"])

    monthly_channel = (
        bookings.groupby(["arrival_year_month", "distribution_channel"])
        .agg(
            bookings=("booking_id", "count"),
            cancellation_rate=("is_canceled", "mean"),
            realized_revenue=("realized_revenue", "sum"),
            average_lead_time=("lead_time", "mean"),
        )
        .reset_index()
        .sort_values(["arrival_year_month", "bookings"], ascending=[True, False])
    )
    monthly_channel.to_csv(OUTPUT_TABLES_DIR / "monthly_channel_performance.csv", index=False)

    source_scorecard = (
        bookings.groupby(["market_segment", "distribution_channel"])
        .agg(
            bookings=("booking_id", "count"),
            cancellation_rate=("is_canceled", "mean"),
            adr=("adr_clean", "mean"),
            realized_revenue=("realized_revenue", "sum"),
            repeat_guest_rate=("is_repeated_guest", "mean"),
            special_request_rate=("total_of_special_requests", "mean"),
        )
        .reset_index()
    )
    source_scorecard["revenue_per_booking"] = (
        source_scorecard["realized_revenue"] / source_scorecard["bookings"]
    )
    source_scorecard = source_scorecard.sort_values("realized_revenue", ascending=False)
    source_scorecard.to_csv(OUTPUT_TABLES_DIR / "booking_source_scorecard.csv", index=False)

    top_segment = source_scorecard.iloc[0]
    insight = (
        "Booking Intelligence Summary\n"
        "============================\n"
        f"Top revenue segment/channel: {top_segment['market_segment']} via "
        f"{top_segment['distribution_channel']}.\n"
        f"Bookings: {top_segment['bookings']:,.0f}; "
        f"Realized revenue: {top_segment['realized_revenue']:,.2f}; "
        f"Cancellation rate: {top_segment['cancellation_rate']:.1%}.\n\n"
        "Operational implication: prioritize reliable high-volume acquisition channels, "
        "monitor long-lead bookings separately, and align staffing around high-arrival months."
    )
    (OUTPUT_INSIGHTS_DIR / "booking_intelligence_summary.txt").write_text(insight, encoding="utf-8")
    print("Booking intelligence exports created.")


if __name__ == "__main__":
    run()