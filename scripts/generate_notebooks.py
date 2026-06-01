"""Generate lightweight Jupyter notebooks for portfolio review."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def markdown_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


BOOKING_NOTEBOOK = notebook(
    [
        markdown_cell("# Booking Intelligence Analysis\n\nEnterprise booking behavior analysis for hotel demand, channels, lead time, and revenue performance."),
        code_cell(
            """from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
bookings = pd.read_csv(ROOT / 'data/processed/hotel_bookings_cleaned.csv', parse_dates=['arrival_date'])
monthly = pd.read_csv(ROOT / 'data/processed/monthly_demand.csv', parse_dates=['arrival_date'])
bookings.shape, monthly.shape"""
        ),
        code_cell(
            """monthly.groupby('hotel')[['bookings', 'room_nights_realized', 'realized_revenue']].sum().style.format('{:,.0f}')"""
        ),
        code_cell(
            """channel = (bookings.groupby(['market_segment', 'distribution_channel'])
    .agg(bookings=('booking_id', 'count'),
         cancellation_rate=('is_canceled', 'mean'),
         realized_revenue=('realized_revenue', 'sum'),
         adr=('adr_clean', 'mean'))
    .sort_values('realized_revenue', ascending=False))
channel.head(12)"""
        ),
        code_cell(
            """plt.figure(figsize=(14, 6))
sns.lineplot(data=monthly, x='arrival_date', y='bookings', hue='hotel', marker='o')
plt.title('Monthly Booking Demand by Hotel Type')
plt.xlabel('Arrival Month')
plt.ylabel('Bookings')
plt.show()"""
        ),
    ]
)

CANCELLATION_NOTEBOOK = notebook(
    [
        markdown_cell("# Cancellation Risk Analysis\n\nCancellation driver exploration across lead time, channel, deposit behavior, seasonality, and customer type."),
        code_cell(
            """from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
bookings = pd.read_csv(ROOT / 'data/processed/hotel_bookings_cleaned.csv')
risk = pd.read_csv(ROOT / 'outputs/tables/cancellation_risk_matrix.csv')
risk.head(10)"""
        ),
        code_cell(
            """drivers = (bookings.groupby('lead_time_band')
    .agg(bookings=('booking_id', 'count'),
         cancellation_rate=('is_canceled', 'mean'),
         lost_revenue=('lost_revenue_estimate', 'sum'))
    .reset_index())
drivers"""
        ),
        code_cell(
            """pivot = bookings.pivot_table(index='arrival_date_month', columns='lead_time_band',
                               values='is_canceled', aggfunc='mean')
plt.figure(figsize=(12, 7))
sns.heatmap(pivot, annot=True, fmt='.0%', cmap='rocket_r')
plt.title('Cancellation Rate by Month and Lead-Time Band')
plt.show()"""
        ),
    ]
)

SEGMENTATION_NOTEBOOK = notebook(
    [
        markdown_cell("# Customer Segmentation and Revenue Intelligence\n\nCustomer persona analysis combining value, reliability, repeat behavior, booking horizon, and channel behavior."),
        code_cell(
            """from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
segments = pd.read_csv(ROOT / 'outputs/tables/customer_persona_segments.csv')
scorecard = pd.read_csv(ROOT / 'data/processed/customer_segment_performance.csv')
segments.head(12)"""
        ),
        code_cell(
            """segments.groupby('persona_label').agg(
    segments=('persona_label', 'count'),
    bookings=('bookings', 'sum'),
    avg_cancel_rate=('cancellation_rate', 'mean'),
    revenue=('realized_revenue', 'sum'),
    avg_value_score=('customer_value_score', 'mean')
).sort_values('revenue', ascending=False)"""
        ),
        code_cell(
            """top = segments.head(20)
plt.figure(figsize=(12, 7))
sns.scatterplot(data=top, x='cancellation_rate', y='realized_revenue',
                size='bookings', hue='persona_label', sizes=(80, 700))
plt.title('Top Customer Segments: Value vs Cancellation Risk')
plt.xlabel('Cancellation Rate')
plt.ylabel('Realized Revenue')
plt.show()"""
        ),
    ]
)


def write_notebook(filename: str, nb: dict) -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    with (NOTEBOOK_DIR / filename).open("w", encoding="utf-8") as fp:
        json.dump(nb, fp, indent=2)


def run() -> None:
    write_notebook("booking_analysis.ipynb", BOOKING_NOTEBOOK)
    write_notebook("cancellation_analysis.ipynb", CANCELLATION_NOTEBOOK)
    write_notebook("customer_segmentation.ipynb", SEGMENTATION_NOTEBOOK)
    print(f"Notebooks written to {NOTEBOOK_DIR}")


if __name__ == "__main__":
    run()