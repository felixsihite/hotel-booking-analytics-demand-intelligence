"""Streamlit dashboard for Hotel Booking Analytics & Demand Intelligence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
FORECAST_DIR = OUTPUTS_DIR / "forecasts"
INSIGHTS_DIR = OUTPUTS_DIR / "insights"

PAGE_TITLE = "Hotel Booking Analytics & Demand Intelligence"
COLOR_SEQUENCE = ["#8B5CF6", "#10B981", "#0891B2", "#F59E0B", "#DC2626", "#A78BFA"]
MONTH_ORDER = [
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
LEAD_TIME_ORDER = [
    "Same week",
    "1-4 weeks",
    "1-3 months",
    "3-6 months",
    "6-12 months",
    "12+ months",
]


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="HB",
    layout="wide",
    initial_sidebar_state="expanded",
)


def money(value: float) -> str:
    return f"${value:,.0f}"


def number(value: float) -> str:
    return f"{value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1%}"


def apply_chart_theme(fig: go.Figure, height: int = 440) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=COLOR_SEQUENCE,
        font=dict(color="#F8FAFC"),
        margin=dict(l=20, r=20, t=58, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame | dict]:
    bookings = pd.read_csv(PROCESSED_DIR / "hotel_bookings_cleaned.csv", parse_dates=["arrival_date"])
    monthly = pd.read_csv(PROCESSED_DIR / "monthly_demand.csv", parse_dates=["arrival_date"])
    segments = pd.read_csv(PROCESSED_DIR / "customer_segment_performance.csv")
    source_scorecard = pd.read_csv(TABLES_DIR / "booking_source_scorecard.csv")
    risk_matrix = pd.read_csv(TABLES_DIR / "cancellation_risk_matrix.csv")
    personas = pd.read_csv(TABLES_DIR / "customer_persona_segments.csv")
    revenue_plan = pd.read_csv(TABLES_DIR / "revenue_optimization_plan.csv", parse_dates=["arrival_date"])
    seasonal_scorecard = pd.read_csv(TABLES_DIR / "seasonal_occupancy_scorecard.csv")
    booking_forecast = pd.read_csv(FORECAST_DIR / "booking_demand_forecast.csv", parse_dates=["ds"])
    occupancy_forecast = pd.read_csv(FORECAST_DIR / "occupancy_rate_forecast.csv", parse_dates=["ds"])
    revenue_forecast = pd.read_csv(FORECAST_DIR / "revenue_forecast.csv", parse_dates=["ds"])
    forecast_metrics = json.loads((FORECAST_DIR / "forecast_accuracy_metrics.json").read_text(encoding="utf-8"))
    kpis = json.loads((INSIGHTS_DIR / "kpi_summary.json").read_text(encoding="utf-8"))
    return {
        "bookings": bookings,
        "monthly": monthly,
        "segments": segments,
        "source_scorecard": source_scorecard,
        "risk_matrix": risk_matrix,
        "personas": personas,
        "revenue_plan": revenue_plan,
        "seasonal_scorecard": seasonal_scorecard,
        "booking_forecast": booking_forecast,
        "occupancy_forecast": occupancy_forecast,
        "revenue_forecast": revenue_forecast,
        "forecast_metrics": forecast_metrics,
        "kpis": kpis,
    }


def filter_data(bookings: pd.DataFrame, monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    st.sidebar.title("Hotel Intelligence")
    st.sidebar.caption("Executive analytics workspace")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Executive Overview",
            "Booking Intelligence",
            "Customer Intelligence",
            "Cancellation Analytics",
            "Demand Forecasting",
            "Revenue Optimization",
        ],
    )

    st.sidebar.divider()
    st.sidebar.subheader("Global Filters")

    hotels = ["All"] + sorted(bookings["hotel"].dropna().unique().tolist())
    hotel = st.sidebar.selectbox("Hotel", hotels)

    market_segments = sorted(bookings["market_segment"].dropna().unique().tolist())
    selected_segments = st.sidebar.multiselect(
        "Market Segment",
        market_segments,
        default=market_segments,
    )

    min_date = bookings["arrival_date"].min().date()
    max_date = bookings["arrival_date"].max().date()
    date_range = st.sidebar.date_input(
        "Arrival Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    filtered_bookings = bookings.copy()
    if hotel != "All":
        filtered_bookings = filtered_bookings[filtered_bookings["hotel"] == hotel]
    if selected_segments:
        filtered_bookings = filtered_bookings[filtered_bookings["market_segment"].isin(selected_segments)]
    filtered_bookings = filtered_bookings[
        filtered_bookings["arrival_date"].dt.date.between(start_date, end_date)
    ]

    filtered_monthly = monthly.copy()
    if hotel != "All":
        filtered_monthly = filtered_monthly[filtered_monthly["hotel"] == hotel]
    filtered_monthly = filtered_monthly[
        filtered_monthly["arrival_date"].dt.date.between(start_date, end_date)
    ]
    if selected_segments:
        monthly_ids = filtered_bookings["arrival_year_month"].unique()
        filtered_monthly = filtered_monthly[filtered_monthly["arrival_year_month"].isin(monthly_ids)]

    st.sidebar.divider()
    st.sidebar.caption("Portfolio stack")
    stack = pd.DataFrame(
        {
            "Capability": ["Python Analytics", "SQL BI", "Streamlit App"],
            "Visibility": [40, 35, 25],
        }
    )
    st.sidebar.dataframe(stack, hide_index=True, width="stretch")

    context = {
        "page": page,
        "hotel": hotel,
        "selected_segments": selected_segments,
        "start_date": start_date,
        "end_date": end_date,
    }
    return filtered_bookings, filtered_monthly, context


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def kpi_row(bookings: pd.DataFrame, monthly: pd.DataFrame, forecast: pd.DataFrame | None = None) -> None:
    total_bookings = len(bookings)
    cancellation_rate = bookings["is_canceled"].mean() if total_bookings else 0
    adr = bookings["adr_clean"].mean() if total_bookings else 0
    realized_revenue = bookings["realized_revenue"].sum()
    occupancy_rate = (
        monthly["room_nights_realized"].sum() / monthly["capacity_room_night_proxy"].sum()
        if len(monthly) and monthly["capacity_room_night_proxy"].sum()
        else 0
    )
    revpar = (
        monthly["realized_revenue"].sum() / monthly["capacity_room_night_proxy"].sum()
        if len(monthly) and monthly["capacity_room_night_proxy"].sum()
        else 0
    )
    forecasted_demand = forecast["forecast"].head(3).mean() if forecast is not None and len(forecast) else 0

    cols = st.columns(6)
    cols[0].metric("Total Bookings", number(total_bookings))
    cols[1].metric("Occupancy Rate", pct(occupancy_rate))
    cols[2].metric("Cancellation Rate", pct(cancellation_rate))
    cols[3].metric("ADR", money(adr))
    cols[4].metric("RevPAR", money(revpar))
    cols[5].metric("3M Forecast Demand", number(forecasted_demand))


def executive_overview(data: dict, bookings: pd.DataFrame, monthly: pd.DataFrame) -> None:
    page_header(
        "Executive Overview",
        "Board-level view of booking demand, occupancy performance, cancellation exposure, ADR, RevPAR, and revenue opportunity.",
    )
    kpi_row(bookings, monthly, data["booking_forecast"])

    left, right = st.columns((1.45, 1))
    with left:
        monthly_trend = monthly.sort_values("arrival_date")
        fig = px.line(
            monthly_trend,
            x="arrival_date",
            y="bookings",
            color="hotel",
            markers=True,
            title="Monthly Booking Demand",
        )
        st.plotly_chart(apply_chart_theme(fig), width="stretch")
    with right:
        fig = px.scatter(
            monthly,
            x="occupancy_rate_estimate",
            y="cancellation_rate",
            size="bookings",
            color="hotel",
            hover_data=["arrival_year_month", "realized_revenue"],
            title="Occupancy vs Cancellation Risk",
            labels={"occupancy_rate_estimate": "Occupancy Rate", "cancellation_rate": "Cancellation Rate"},
        )
        fig.update_xaxes(tickformat=".0%")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(apply_chart_theme(fig), width="stretch")

    st.subheader("Executive Business Story")
    col_a, col_b, col_c = st.columns(3)
    col_a.info("Business problem: hotels need better demand visibility, lower cancellation exposure, and stronger occupancy planning.")
    col_b.success("Business solution: Python processing, SQL BI, forecasting, segmentation, and Streamlit executive analytics.")
    col_c.warning("Business impact: risk-based controls, pricing actions, channel optimization, and more reliable revenue planning.")

    st.download_button(
        "Download filtered booking data",
        bookings.to_csv(index=False).encode("utf-8"),
        file_name="filtered_hotel_bookings.csv",
        mime="text/csv",
    )


def booking_intelligence(data: dict, bookings: pd.DataFrame, monthly: pd.DataFrame) -> None:
    page_header(
        "Booking Intelligence",
        "Booking trends, source performance, lead-time behavior, market segment contribution, and channel reliability.",
    )
    kpi_row(bookings, monthly, data["booking_forecast"])

    trend = monthly.sort_values("arrival_date")
    fig = px.area(
        trend,
        x="arrival_date",
        y="bookings",
        color="hotel",
        title="Booking Volume by Hotel Type",
    )
    st.plotly_chart(apply_chart_theme(fig), width="stretch")

    left, right = st.columns(2)
    with left:
        source = (
            bookings.groupby(["market_segment", "distribution_channel"], as_index=False)
            .agg(
                bookings=("booking_id", "count"),
                cancellation_rate=("is_canceled", "mean"),
                realized_revenue=("realized_revenue", "sum"),
            )
            .sort_values("realized_revenue", ascending=False)
            .head(15)
        )
        fig = px.bar(
            source,
            x="realized_revenue",
            y="market_segment",
            color="distribution_channel",
            orientation="h",
            title="Top Booking Sources by Revenue",
        )
        st.plotly_chart(apply_chart_theme(fig), width="stretch")
    with right:
        fig = px.histogram(
            bookings,
            x="lead_time",
            color="is_canceled",
            nbins=60,
            title="Lead Time Distribution by Cancellation Outcome",
            labels={"is_canceled": "Canceled"},
        )
        fig.update_xaxes(range=[0, 500])
        st.plotly_chart(apply_chart_theme(fig), width="stretch")

    st.subheader("Booking Source Scorecard")
    st.dataframe(
        data["source_scorecard"].head(30),
        width="stretch",
        hide_index=True,
    )


def customer_intelligence(data: dict, bookings: pd.DataFrame, monthly: pd.DataFrame) -> None:
    page_header(
        "Customer Intelligence",
        "High-value guests, repeat behavior, loyalty opportunity, persona clusters, and segment-level risk/revenue tradeoffs.",
    )
    kpi_row(bookings, monthly, data["booking_forecast"])

    personas = data["personas"]
    filtered_personas = personas[
        personas["market_segment"].isin(bookings["market_segment"].unique())
    ].copy()

    left, right = st.columns(2)
    with left:
        fig = px.scatter(
            filtered_personas.head(80),
            x="cancellation_rate",
            y="realized_revenue",
            size="bookings",
            color="persona_label",
            hover_data=["country", "market_segment", "customer_type"],
            title="Customer Segment Value vs Risk",
        )
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(apply_chart_theme(fig), width="stretch")
    with right:
        repeat = (
            bookings.groupby("customer_type", as_index=False)
            .agg(
                bookings=("booking_id", "count"),
                repeat_guest_rate=("is_repeated_guest", "mean"),
                revenue=("realized_revenue", "sum"),
            )
            .sort_values("revenue", ascending=False)
        )
        fig = px.bar(
            repeat,
            x="customer_type",
            y="repeat_guest_rate",
            color="revenue",
            title="Repeat Guest Rate by Customer Type",
        )
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(apply_chart_theme(fig), width="stretch")

    st.subheader("Highest-Value Customer Personas")
    st.dataframe(
        filtered_personas.head(30),
        width="stretch",
        hide_index=True,
    )


def cancellation_analytics(data: dict, bookings: pd.DataFrame, monthly: pd.DataFrame) -> None:
    page_header(
        "Cancellation Analytics",
        "Cancellation drivers, seasonal risk patterns, high-risk segments, and estimated revenue leakage.",
    )
    kpi_row(bookings, monthly, data["booking_forecast"])

    heatmap = (
        bookings.pivot_table(
            index="arrival_date_month",
            columns="lead_time_band",
            values="is_canceled",
            aggfunc="mean",
            observed=False,
        )
        .reindex(MONTH_ORDER)
        .reindex(LEAD_TIME_ORDER, axis=1)
    )
    fig = px.imshow(
        heatmap,
        aspect="auto",
        color_continuous_scale=["#10B981", "#0891B2", "#8B5CF6", "#DC2626"],
        title="Cancellation Rate Heatmap by Month and Lead Time",
        labels=dict(color="Cancellation Rate"),
    )
    fig.update_coloraxes(colorbar_tickformat=".0%")
    st.plotly_chart(apply_chart_theme(fig, height=520), width="stretch")

    left, right = st.columns(2)
    with left:
        drivers = (
            bookings.groupby("lead_time_band", observed=False, as_index=False)
            .agg(
                bookings=("booking_id", "count"),
                cancellation_rate=("is_canceled", "mean"),
                lost_revenue=("lost_revenue_estimate", "sum"),
            )
        )
        drivers["lead_time_band"] = pd.Categorical(drivers["lead_time_band"], LEAD_TIME_ORDER, ordered=True)
        drivers = drivers.sort_values("lead_time_band")
        fig = px.bar(
            drivers,
            x="lead_time_band",
            y="cancellation_rate",
            color="lost_revenue",
            title="Cancellation Rate by Lead-Time Band",
        )
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(apply_chart_theme(fig), width="stretch")
    with right:
        risk = data["risk_matrix"].head(20)
        fig = px.bar(
            risk,
            x="risk_priority_score",
            y="market_segment",
            color="lost_revenue_estimate",
            orientation="h",
            title="Highest-Risk Segment Priorities",
        )
        st.plotly_chart(apply_chart_theme(fig), width="stretch")

    st.subheader("Cancellation Risk Matrix")
    st.dataframe(data["risk_matrix"].head(40), width="stretch", hide_index=True)


def forecast_chart(history: pd.DataFrame, forecast: pd.DataFrame, target: str, title: str, y_label: str, percent_axis: bool = False) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["ds"],
            y=history[target],
            mode="lines+markers",
            name="Historical",
            line=dict(color="#0891B2", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["ds"],
            y=forecast["upper_95"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["ds"],
            y=forecast["lower_95"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(139, 92, 246, 0.22)",
            line=dict(width=0),
            name="95% Confidence Interval",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["ds"],
            y=forecast["forecast"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#10B981", width=3),
        )
    )
    fig.update_layout(title=title, yaxis_title=y_label)
    if percent_axis:
        fig.update_yaxes(tickformat=".0%")
    return apply_chart_theme(fig)


def demand_forecasting(data: dict, bookings: pd.DataFrame, monthly: pd.DataFrame) -> None:
    page_header(
        "Demand Forecasting",
        "Forward-looking booking demand, occupancy, and revenue forecasts with holdout accuracy metrics.",
    )

    history = pd.read_csv(PROCESSED_DIR / "forecasting_input_monthly.csv", parse_dates=["ds"])
    metrics = data["forecast_metrics"]

    metric_cols = st.columns(3)
    for idx, key in enumerate(["booking_demand", "occupancy_rate", "revenue"]):
        item = metrics[key]
        model_name = item.get("model", "Forecast Model")
        metric_cols[idx].metric(
            f"{key.replace('_', ' ').title()} Model",
            model_name,
            f"MAPE {item['mape']:.2f}%",
        )

    tab_booking, tab_occupancy, tab_revenue = st.tabs(["Booking Demand", "Occupancy Rate", "Revenue"])
    with tab_booking:
        st.plotly_chart(
            forecast_chart(
                history,
                data["booking_forecast"],
                "y_booking_demand",
                "Booking Demand Forecast",
                "Bookings",
            ),
            width="stretch",
        )
        st.dataframe(data["booking_forecast"], width="stretch", hide_index=True)
    with tab_occupancy:
        st.plotly_chart(
            forecast_chart(
                history,
                data["occupancy_forecast"],
                "y_occupancy_rate",
                "Occupancy Forecast",
                "Occupancy Rate",
                percent_axis=True,
            ),
            width="stretch",
        )
        st.dataframe(data["occupancy_forecast"], width="stretch", hide_index=True)
    with tab_revenue:
        st.plotly_chart(
            forecast_chart(
                history,
                data["revenue_forecast"],
                "y_revenue",
                "Revenue Forecast",
                "Revenue",
            ),
            width="stretch",
        )
        st.dataframe(data["revenue_forecast"], width="stretch", hide_index=True)


def revenue_optimization(data: dict, bookings: pd.DataFrame, monthly: pd.DataFrame) -> None:
    page_header(
        "Revenue Optimization",
        "Peak demand periods, low-demand opportunities, revenue leakage, ADR strategy, and dynamic pricing recommendations.",
    )
    kpi_row(bookings, monthly, data["booking_forecast"])

    revenue_plan = data["revenue_plan"].copy()
    if len(monthly):
        periods = monthly["arrival_year_month"].unique()
        revenue_plan = revenue_plan[revenue_plan["arrival_year_month"].isin(periods)]

    left, right = st.columns((1.2, 1))
    with left:
        top_plan = revenue_plan.sort_values("estimated_revenue_upside", ascending=False).head(15)
        fig = px.bar(
            top_plan,
            x="estimated_revenue_upside",
            y="arrival_year_month",
            color="hotel",
            orientation="h",
            title="Top Revenue Upside Periods",
            hover_data=["pricing_action", "revenue_opportunity_index"],
        )
        st.plotly_chart(apply_chart_theme(fig), width="stretch")
    with right:
        seasonal = data["seasonal_scorecard"]
        fig = px.scatter(
            seasonal,
            x="average_occupancy",
            y="average_cancellation_rate",
            size="realized_revenue",
            color="hotel",
            hover_data=["month_name", "revenue_opportunity_index"],
            title="Seasonal Occupancy and Risk Map",
        )
        fig.update_xaxes(tickformat=".0%")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(apply_chart_theme(fig), width="stretch")

    st.subheader("Strategic Pricing Recommendations")
    for row in revenue_plan.sort_values("estimated_revenue_upside", ascending=False).head(5).itertuples():
        st.success(
            f"{row.hotel} {row.arrival_year_month}: {row.pricing_action} "
            f"Estimated upside: {money(row.estimated_revenue_upside)}."
        )

    st.subheader("Revenue Optimization Plan")
    st.dataframe(revenue_plan.head(40), width="stretch", hide_index=True)
    st.download_button(
        "Download revenue optimization plan",
        revenue_plan.to_csv(index=False).encode("utf-8"),
        file_name="revenue_optimization_plan.csv",
        mime="text/csv",
    )


def main() -> None:
    data = load_data()
    bookings = data["bookings"]
    monthly = data["monthly"]
    filtered_bookings, filtered_monthly, context = filter_data(bookings, monthly)

    if filtered_bookings.empty:
        st.warning("No booking records match the selected filters.")
        return

    page = context["page"]
    if page == "Executive Overview":
        executive_overview(data, filtered_bookings, filtered_monthly)
    elif page == "Booking Intelligence":
        booking_intelligence(data, filtered_bookings, filtered_monthly)
    elif page == "Customer Intelligence":
        customer_intelligence(data, filtered_bookings, filtered_monthly)
    elif page == "Cancellation Analytics":
        cancellation_analytics(data, filtered_bookings, filtered_monthly)
    elif page == "Demand Forecasting":
        demand_forecasting(data, filtered_bookings, filtered_monthly)
    elif page == "Revenue Optimization":
        revenue_optimization(data, filtered_bookings, filtered_monthly)


if __name__ == "__main__":
    main()