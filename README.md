# Hotel Booking Analytics & Demand Intelligence

Enterprise hospitality analytics portfolio project built with Python, SQL, Prophet forecasting, and a premium Streamlit analytics application.

Dataset source: [Hotel Booking Demand Dataset on Kaggle](https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand)

## Project Summary

This project simulates a real-world hotel analytics business case for revenue, operations, and commercial leadership. It analyzes booking behavior, cancellation patterns, customer segments, seasonal demand, occupancy utilization, forecasted demand, and revenue opportunities to support better planning and data-driven decision making.

The final deliverable is a Streamlit executive analytics application supported by a Python data pipeline, SQL business intelligence layer, forecasting outputs, data quality documentation, notebooks, and business insight reports.

## Business Objective

Hotels frequently struggle with high cancellation rates, revenue leakage, occupancy planning challenges, seasonal demand volatility, inefficient pricing strategy, and limited customer behavior visibility.

This project helps answer:

- Which booking segments create the highest revenue and cancellation exposure?
- Which channels and lead-time groups are most reliable?
- How do demand, occupancy, and cancellations vary by season?
- What are the strongest revenue optimization opportunities?
- What does future booking demand and occupancy look like?

## Portfolio Positioning

This repository is designed for Data Analyst, Business Intelligence Analyst, Revenue Analyst, Hospitality Analyst, Product Analyst, and analytics-focused portfolio applications.

Capability signal:

- Python analytics and data engineering: 45%
- SQL business intelligence: 30%
- Streamlit analytics application and forecasting storytelling: 25%

## Repository Structure

```text
hotel_booking_analytics_&_demand_intelligence/
├── data/
│   ├── raw/
│   ├── processed/
│   └── warehouse/
├── docs/
│   └── data_dictionary.md
├── forecasting/
│   ├── README.md
│   └── forecast_reports/
├── notebooks/
├── outputs/
│   ├── charts/
│   ├── forecasts/
│   ├── insights/
│   ├── reports/
│   └── tables/
├── scripts/
├── sql/
├── streamlit_app/
│   ├── .streamlit/
│   ├── app.py
│   └── README.md
├── README.md
├── requirements.txt
├── environment.yml
└── .gitignore
```

## Analytics Workflow

```text
Raw Hotel Booking Dataset
↓
Python Cleaning, Validation, and Feature Engineering
↓
Processed Analytical Tables and SQLite Warehouse
↓
SQL Business Intelligence Queries
↓
EDA, Segmentation, Cancellation Risk, Revenue Optimization
↓
Prophet / Seasonal Forecast Outputs
↓
Streamlit Executive Analytics Application
↓
Business Reports and Strategic Recommendations
```

## Key Deliverables

- Cleaned booking dataset: `data/processed/hotel_bookings_cleaned.csv`
- Monthly demand mart: `data/processed/monthly_demand.csv`
- Forecasting dataset: `data/processed/forecasting_input_monthly.csv`
- SQLite warehouse: `data/warehouse/hotel_booking_analytics.sqlite`
- SQL BI query suite: `sql/`
- Python notebooks: `notebooks/`
- Streamlit app: `streamlit_app/app.py`
- Data dictionary: `docs/data_dictionary.md`
- Data quality report: `outputs/reports/data_quality_report.md`
- Forecast reports: `forecasting/forecast_reports/`
- Business reports: `outputs/reports/`
- Executive insights: `outputs/insights/`

## Run The Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Regenerate all datasets, reports, forecasts, notebooks, and warehouse tables:

```bash
python scripts/run_pipeline.py
```

Launch the Streamlit application:

```bash
streamlit run streamlit_app/app.py
```

Local dashboard URL:

```text
http://localhost:8501
```

## Streamlit Application

The Streamlit app uses native Streamlit components and Plotly charts with a dark executive analytics theme configured in `streamlit_app/.streamlit/config.toml`.

Application pages:

- Executive Overview
- Booking Intelligence
- Customer Intelligence
- Cancellation Analytics
- Demand Forecasting
- Revenue Optimization

Interactive features:

- Sidebar navigation
- Hotel, segment, and date filters
- KPI cards
- Plotly charts
- Forecast tabs
- Segment tables
- Downloadable CSV reports
- Business recommendations

## SQL Business Intelligence

The SQL files are designed for the generated SQLite warehouse:

```text
data/warehouse/hotel_booking_analytics.sqlite
```

Core warehouse tables:

- `fact_bookings`
- `mart_monthly_demand`
- `mart_customer_segments`
- `mart_forecasting_monthly`
- `mart_executive_kpis`

Query suites:

- `sql/booking_analysis.sql`
- `sql/occupancy_queries.sql`
- `sql/cancellation_analysis.sql`
- `sql/revenue_optimization.sql`

The SQL layer covers booking aggregation, monthly growth, occupancy analysis, cancellation risk, ADR, RevPAR, customer segments, channel performance, and revenue opportunity ranking.

## Forecasting

The forecasting workflow generates 12-month forward outlooks for:

- Booking demand
- Occupancy rate
- Revenue

Forecast method:

- Prophet when available
- Seasonal regression fallback when Prophet cannot be fitted locally

Forecast deliverables:

- `outputs/forecasts/booking_demand_forecast.csv`
- `outputs/forecasts/occupancy_rate_forecast.csv`
- `outputs/forecasts/revenue_forecast.csv`
- `outputs/forecasts/forecast_accuracy_metrics.json`
- `forecasting/forecast_reports/booking_demand_report.md`
- `forecasting/forecast_reports/occupancy_forecast_report.md`
- `forecasting/forecast_reports/revenue_forecast_report.md`
- `forecasting/forecast_reports/forecast_model_summary.md`

## Data Quality And Methodology

Data quality outputs:

- `outputs/reports/data_quality_report.md`
- `outputs/tables/data_quality_summary.csv`
- `outputs/tables/raw_missing_value_profile.csv`
- `outputs/tables/data_dictionary.csv`
- `docs/data_dictionary.md`

Important methodology note:

The dataset does not include true room inventory. Occupancy and RevPAR are therefore estimated using a capacity proxy derived from observed realized room-night peaks by hotel. This is documented for transparency and should be replaced with actual inventory data in production.

## Business Impact

- Identifies high-risk cancellation segments and revenue exposure.
- Reveals seasonal booking patterns for demand planning.
- Supports dynamic pricing and occupancy optimization.
- Highlights high-value and repeat guest opportunities.
- Provides SQL-ready tables for BI reporting and executive KPIs.
- Delivers a recruiter-ready Streamlit analytics platform for business storytelling.

## Interview Summary

Built a complete hospitality analytics ecosystem using Python, SQL, Prophet forecasting, and Streamlit to analyze booking demand, cancellations, customer segments, occupancy, and revenue opportunities. The project demonstrates data cleaning, feature engineering, business intelligence, segmentation, forecasting, executive dashboard design, and strategic revenue recommendations.