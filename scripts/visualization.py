"""Visualization utilities for the Hotel Booking Analytics project."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"

NAVY = "#0F172A"
PURPLE = "#5B21B6"
EMERALD = "#10B981"
TEAL = "#0891B2"
CRIMSON = "#DC2626"
SLATE = "#334155"


def configure_style() -> None:
    sns.set_theme(style="darkgrid", context="talk")
    plt.rcParams.update(
        {
            "figure.facecolor": "#111827",
            "axes.facecolor": "#111827",
            "axes.edgecolor": "#475569",
            "axes.labelcolor": "#E5E7EB",
            "xtick.color": "#CBD5E1",
            "ytick.color": "#CBD5E1",
            "text.color": "#F8FAFC",
            "grid.color": "#334155",
            "axes.titleweight": "bold",
            "axes.titlesize": 18,
        }
    )


def save_chart(fig: plt.Figure, filename: str) -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHARTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bookings = pd.read_csv(PROCESSED_DIR / "hotel_bookings_cleaned.csv", parse_dates=["arrival_date"])
    monthly = pd.read_csv(PROCESSED_DIR / "monthly_demand.csv", parse_dates=["arrival_date"])
    segments = pd.read_csv(PROCESSED_DIR / "customer_segment_performance.csv")
    return bookings, monthly, segments


def booking_trend_chart(monthly: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(14, 7))
    for hotel, data in monthly.groupby("hotel"):
        ax.plot(data["arrival_date"], data["bookings"], marker="o", linewidth=2.4, label=hotel)
    ax.set_title("Monthly Booking Demand by Hotel Type")
    ax.set_xlabel("Arrival Month")
    ax.set_ylabel("Bookings")
    ax.legend(frameon=False)
    return save_chart(fig, "booking_trend_by_hotel.png")


def cancellation_heatmap(bookings: pd.DataFrame) -> Path:
    pivot = (
        bookings.pivot_table(
            index="arrival_date_month",
            columns="lead_time_band",
            values="is_canceled",
            aggfunc="mean",
            observed=False,
        )
        .reindex(
            [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
        )
        .reindex(
            ["Same week", "1-4 weeks", "1-3 months", "3-6 months", "6-12 months", "12+ months"],
            axis=1,
        )
    )
    fig, ax = plt.subplots(figsize=(13, 8))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap=sns.color_palette([EMERALD, TEAL, PURPLE, CRIMSON], as_cmap=True),
        annot=True,
        fmt=".0%",
        linewidths=0.5,
        linecolor="#1E293B",
        cbar_kws={"label": "Cancellation Rate"},
    )
    ax.set_title("Cancellation Risk Heatmap by Season and Lead Time")
    ax.set_xlabel("Lead Time Band")
    ax.set_ylabel("Arrival Month")
    return save_chart(fig, "cancellation_risk_heatmap.png")


def market_segment_chart(bookings: pd.DataFrame) -> Path:
    segment = (
        bookings.groupby("market_segment")
        .agg(
            bookings=("booking_id", "count"),
            cancellation_rate=("is_canceled", "mean"),
            realized_revenue=("realized_revenue", "sum"),
        )
        .sort_values("realized_revenue", ascending=False)
        .head(8)
        .reset_index()
    )
    fig, ax1 = plt.subplots(figsize=(14, 7))
    ax1.bar(segment["market_segment"], segment["realized_revenue"], color=TEAL, alpha=0.9)
    ax1.set_ylabel("Realized Revenue")
    ax1.tick_params(axis="x", rotation=30)
    ax2 = ax1.twinx()
    ax2.plot(segment["market_segment"], segment["cancellation_rate"], color=CRIMSON, marker="o", linewidth=2.5)
    ax2.set_ylabel("Cancellation Rate")
    ax2.yaxis.label.set_color("#FCA5A5")
    ax2.tick_params(axis="y", colors="#FCA5A5")
    ax1.set_title("Market Segment Revenue and Booking Reliability")
    return save_chart(fig, "market_segment_revenue_risk.png")


def lead_time_distribution(bookings: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(14, 7))
    sns.histplot(
        data=bookings,
        x="lead_time",
        hue="is_canceled",
        bins=60,
        kde=True,
        palette={0: EMERALD, 1: CRIMSON},
        alpha=0.55,
        ax=ax,
    )
    ax.set_xlim(0, 500)
    ax.set_title("Lead Time Distribution by Cancellation Outcome")
    ax.set_xlabel("Lead Time in Days")
    ax.set_ylabel("Booking Count")
    return save_chart(fig, "lead_time_distribution.png")


def occupancy_chart(monthly: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(14, 7))
    for hotel, data in monthly.groupby("hotel"):
        ax.plot(
            data["arrival_date"],
            data["occupancy_rate_estimate"],
            marker="o",
            linewidth=2.4,
            label=hotel,
        )
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_title("Estimated Occupancy Rate Trend")
    ax.set_xlabel("Arrival Month")
    ax.set_ylabel("Occupancy Rate Estimate")
    ax.legend(frameon=False)
    return save_chart(fig, "occupancy_rate_trend.png")


def revenue_opportunity_chart(monthly: pd.DataFrame) -> Path:
    ranking = (
        monthly.assign(period=monthly["hotel"] + " | " + monthly["arrival_year_month"])
        .sort_values("revenue_opportunity_index", ascending=False)
        .head(12)
    )
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.barh(ranking["period"], ranking["revenue_opportunity_index"], color=PURPLE)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_title("Highest Revenue Optimization Opportunity Periods")
    ax.set_xlabel("Revenue Opportunity Index")
    ax.set_ylabel("")
    return save_chart(fig, "revenue_opportunity_index.png")


def correlation_chart(bookings: pd.DataFrame) -> Path:
    cols = [
        "is_canceled",
        "lead_time",
        "adr_clean",
        "total_nights",
        "total_guests",
        "previous_cancellations",
        "booking_changes",
        "days_in_waiting_list",
        "required_car_parking_spaces",
        "total_of_special_requests",
        "is_repeated_guest",
        "realized_revenue",
    ]
    corr = bookings[cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        corr,
        ax=ax,
        cmap=sns.diverging_palette(145, 10, as_cmap=True),
        center=0,
        linewidths=0.4,
        linecolor="#1E293B",
        cbar_kws={"label": "Correlation"},
    )
    ax.set_title("Booking Behavior Correlation Matrix")
    return save_chart(fig, "correlation_matrix.png")


def create_all_charts() -> list[Path]:
    configure_style()
    bookings, monthly, _ = load_tables()
    paths = [
        booking_trend_chart(monthly),
        cancellation_heatmap(bookings),
        market_segment_chart(bookings),
        lead_time_distribution(bookings),
        occupancy_chart(monthly),
        revenue_opportunity_chart(monthly),
        correlation_chart(bookings),
    ]
    print("Generated charts:")
    for path in paths:
        print(f"- {path}")
    return paths


if __name__ == "__main__":
    create_all_charts()