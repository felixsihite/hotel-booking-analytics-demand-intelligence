"""Customer segmentation and booking behavior analytics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
OUTPUT_INSIGHTS_DIR = PROJECT_ROOT / "outputs" / "insights"


def run() -> None:
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    bookings = pd.read_csv(PROCESSED_DIR / "hotel_bookings_cleaned.csv")
    segment = (
        bookings.groupby(["country", "market_segment", "customer_type"])
        .agg(
            bookings=("booking_id", "count"),
            cancellation_rate=("is_canceled", "mean"),
            realized_revenue=("realized_revenue", "sum"),
            adr=("adr_clean", "mean"),
            average_lead_time=("lead_time", "mean"),
            repeat_guest_rate=("is_repeated_guest", "mean"),
            average_special_requests=("total_of_special_requests", "mean"),
            average_total_nights=("total_nights", "mean"),
        )
        .reset_index()
    )
    segment = segment[segment["bookings"] >= 40].copy()
    features = [
        "bookings",
        "cancellation_rate",
        "realized_revenue",
        "adr",
        "average_lead_time",
        "repeat_guest_rate",
        "average_special_requests",
        "average_total_nights",
    ]
    scaled = StandardScaler().fit_transform(segment[features])
    model = KMeans(n_clusters=5, random_state=42, n_init=20)
    segment["persona_cluster"] = model.fit_predict(scaled)

    cluster_names = {
        0: "Value-managed core guests",
        1: "High-volume commercial demand",
        2: "Long-lead cancellation watchlist",
        3: "Premium reliable guests",
        4: "Niche loyalty opportunity",
    }
    segment["persona_label"] = segment["persona_cluster"].map(cluster_names)
    segment["customer_value_score"] = (
        segment["realized_revenue"].rank(pct=True) * 45
        + (1 - segment["cancellation_rate"]).rank(pct=True) * 30
        + segment["repeat_guest_rate"].rank(pct=True) * 15
        + segment["adr"].rank(pct=True) * 10
    ).round(2)
    segment = segment.sort_values("customer_value_score", ascending=False)
    segment.to_csv(OUTPUT_TABLES_DIR / "customer_persona_segments.csv", index=False)

    top = segment.iloc[0]
    insight = (
        "Customer Segmentation Summary\n"
        "=============================\n"
        f"Highest value segment: {top['country']} | {top['market_segment']} | "
        f"{top['customer_type']} ({top['persona_label']}).\n"
        f"Customer value score: {top['customer_value_score']:.1f}; "
        f"realized revenue: {top['realized_revenue']:,.2f}; "
        f"cancellation rate: {top['cancellation_rate']:.1%}.\n\n"
        "Commercial action: prioritize retention, direct-channel migration, and targeted offers "
        "for reliable high-value segments while applying risk controls to volatile long-lead groups."
    )
    (OUTPUT_INSIGHTS_DIR / "customer_segmentation_summary.txt").write_text(insight, encoding="utf-8")
    print("Customer segmentation exports created.")


if __name__ == "__main__":
    run()