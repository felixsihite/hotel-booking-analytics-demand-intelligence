"""Python demand forecasting outputs for the Streamlit analytics app.

The script uses Prophet when available and falls back to a transparent seasonal
regression model when Prophet cannot be fitted in the local environment.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - optional package fallback
    Prophet = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FORECAST_DIR = PROJECT_ROOT / "outputs" / "forecasts"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"
FORECAST_REPORT_DIR = PROJECT_ROOT / "forecasting" / "forecast_reports"

NAVY = "#0F172A"
PURPLE = "#5B21B6"
EMERALD = "#10B981"
TEAL = "#0891B2"
CRIMSON = "#DC2626"


def make_features(dates: pd.Series, start_date: pd.Timestamp) -> pd.DataFrame:
    month = dates.dt.month
    elapsed = ((dates.dt.year - start_date.year) * 12 + dates.dt.month - start_date.month).astype(int)
    features = pd.DataFrame(
        {
            "trend": elapsed,
            "month_sin": np.sin(2 * np.pi * month / 12),
            "month_cos": np.cos(2 * np.pi * month / 12),
            "q1": dates.dt.quarter.eq(1).astype(int),
            "q2": dates.dt.quarter.eq(2).astype(int),
            "q3": dates.dt.quarter.eq(3).astype(int),
            "q4": dates.dt.quarter.eq(4).astype(int),
        }
    )
    return features


def train_forecast(ts: pd.DataFrame, target: str, periods: int = 12) -> tuple[pd.DataFrame, dict[str, float]]:
    if Prophet is not None:
        try:
            return train_prophet_forecast(ts, target, periods)
        except Exception as exc:
            print(f"Prophet forecast fallback for {target}: {exc}")
    return train_regression_forecast(ts, target, periods)


def train_prophet_forecast(ts: pd.DataFrame, target: str, periods: int = 12) -> tuple[pd.DataFrame, dict[str, float]]:
    working = ts[["ds", target]].dropna().rename(columns={target: "y"}).copy()
    working = working.sort_values("ds")
    holdout_size = min(6, max(3, len(working) // 4))
    train = working.iloc[:-holdout_size]
    test = working.iloc[-holdout_size:]

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        interval_width=0.95,
    )
    model.fit(train)
    test_pred = model.predict(test[["ds"]])["yhat"].to_numpy()
    residuals = test["y"].to_numpy() - test_pred

    rmse = float(mean_squared_error(test["y"], test_pred) ** 0.5)
    mae = float(mean_absolute_error(test["y"], test_pred))
    mape = float(np.mean(np.abs(residuals / np.maximum(np.abs(test["y"].to_numpy()), 1))) * 100)

    final_model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        interval_width=0.95,
    )
    final_model.fit(working)
    future_dates = pd.date_range(
        working["ds"].max() + pd.offsets.MonthBegin(1),
        periods=periods,
        freq="MS",
    )
    pred = final_model.predict(pd.DataFrame({"ds": future_dates}))
    future = pd.DataFrame(
        {
            "ds": future_dates,
            "forecast": pred["yhat"].to_numpy(),
            "lower_95": pred["yhat_lower"].to_numpy(),
            "upper_95": pred["yhat_upper"].to_numpy(),
            "model": "Prophet",
        }
    )
    if "rate" in target:
        for column in ["forecast", "lower_95", "upper_95"]:
            future[column] = future[column].clip(0, 1)
    else:
        for column in ["forecast", "lower_95", "upper_95"]:
            future[column] = future[column].clip(lower=0)

    metrics = {
        "target": target,
        "model": "Prophet",
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape": round(mape, 4),
        "holdout_months": int(holdout_size),
    }
    return future, metrics


def train_regression_forecast(ts: pd.DataFrame, target: str, periods: int = 12) -> tuple[pd.DataFrame, dict[str, float]]:
    working = ts[["ds", target]].dropna().copy()
    working = working.sort_values("ds")
    start_date = working["ds"].min()

    holdout_size = min(6, max(3, len(working) // 4))
    train = working.iloc[:-holdout_size]
    test = working.iloc[-holdout_size:]

    model = LinearRegression()
    model.fit(make_features(train["ds"], start_date), train[target])
    test_pred = model.predict(make_features(test["ds"], start_date))

    residuals = test[target].to_numpy() - test_pred
    rmse = float(mean_squared_error(test[target], test_pred) ** 0.5)
    mae = float(mean_absolute_error(test[target], test_pred))
    mape = float(np.mean(np.abs(residuals / np.maximum(np.abs(test[target].to_numpy()), 1))) * 100)

    final_model = LinearRegression()
    final_model.fit(make_features(working["ds"], start_date), working[target])

    future_dates = pd.date_range(
        working["ds"].max() + pd.offsets.MonthBegin(1),
        periods=periods,
        freq="MS",
    )
    future = pd.DataFrame({"ds": future_dates})
    yhat = final_model.predict(make_features(future["ds"], start_date))
    resid_std = float(np.std(working[target].to_numpy() - final_model.predict(make_features(working["ds"], start_date))))
    future["forecast"] = yhat
    future["lower_95"] = yhat - 1.96 * resid_std
    future["upper_95"] = yhat + 1.96 * resid_std
    future["model"] = "Seasonal Regression"
    if "rate" in target:
        for column in ["forecast", "lower_95", "upper_95"]:
            future[column] = future[column].clip(0, 1)
    else:
        for column in ["forecast", "lower_95", "upper_95"]:
            future[column] = future[column].clip(lower=0)

    metrics = {
        "target": target,
        "model": "Seasonal Regression",
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape": round(mape, 4),
        "holdout_months": int(holdout_size),
    }
    return future, metrics


def format_metric(value: float, target: str) -> str:
    if "rate" in target:
        return f"{value:.1%}"
    if "revenue" in target:
        return f"${value:,.0f}"
    return f"{value:,.0f}"


def write_forecast_report(
    filename: str,
    title: str,
    target: str,
    forecast: pd.DataFrame,
    metrics: dict[str, float | str],
) -> Path:
    FORECAST_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    first_three = forecast.head(3)
    peak_row = forecast.loc[forecast["forecast"].idxmax()]
    low_row = forecast.loc[forecast["forecast"].idxmin()]
    rows = "\n".join(
        "- "
        + pd.to_datetime(row.ds).strftime("%b %Y")
        + f": forecast {format_metric(row.forecast, target)} "
        + f"(95% CI {format_metric(row.lower_95, target)} to {format_metric(row.upper_95, target)})"
        for row in first_three.itertuples()
    )
    report = f"""# {title}

## Model Summary

- Model: {metrics.get("model", "Forecast Model")}
- Holdout window: {metrics["holdout_months"]} months
- RMSE: {metrics["rmse"]}
- MAE: {metrics["mae"]}
- MAPE: {metrics["mape"]}%

## Near-Term Outlook

{rows}

## Planning Signal

- Highest forecast month: {pd.to_datetime(peak_row["ds"]).strftime("%b %Y")} at {format_metric(peak_row["forecast"], target)}
- Lowest forecast month: {pd.to_datetime(low_row["ds"]).strftime("%b %Y")} at {format_metric(low_row["forecast"], target)}

## Business Interpretation

Use this forecast as a forward-looking planning signal for staffing, inventory controls, channel strategy, cancellation-risk monitoring, and revenue management. The dataset does not include actual room inventory, so occupancy and RevPAR remain estimate-based and should be replaced with true inventory data in production.
"""
    path = FORECAST_REPORT_DIR / filename
    path.write_text(report, encoding="utf-8")
    return path


def write_model_summary(outputs: dict[str, dict[str, float | str]]) -> None:
    FORECAST_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Forecast Model Summary",
        "",
        "This folder contains business-facing forecast reports generated by the Python pipeline.",
        "",
        "| Forecast | Model | RMSE | MAE | MAPE | Holdout |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, item in outputs.items():
        label = key.replace("_", " ").title()
        lines.append(
            f"| {label} | {item.get('model', 'Forecast Model')} | {item['rmse']} | "
            f"{item['mae']} | {item['mape']}% | {item['holdout_months']} months |"
        )
    lines.extend(
        [
            "",
            "Primary artifacts:",
            "",
            "- `outputs/forecasts/booking_demand_forecast.csv`",
            "- `outputs/forecasts/occupancy_rate_forecast.csv`",
            "- `outputs/forecasts/revenue_forecast.csv`",
            "- `outputs/forecasts/forecast_accuracy_metrics.json`",
        ]
    )
    (FORECAST_REPORT_DIR / "forecast_model_summary.md").write_text("\n".join(lines), encoding="utf-8")


def plot_forecast(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
    target: str,
    title: str,
    ylabel: str,
    filename: str,
    percentage_axis: bool = False,
) -> Path:
    plt.rcParams.update(
        {
            "figure.facecolor": NAVY,
            "axes.facecolor": NAVY,
            "axes.edgecolor": "#475569",
            "axes.labelcolor": "#E5E7EB",
            "xtick.color": "#CBD5E1",
            "ytick.color": "#CBD5E1",
            "text.color": "#F8FAFC",
            "grid.color": "#334155",
        }
    )
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(history["ds"], history[target], color=TEAL, linewidth=2.6, marker="o", label="Historical")
    ax.plot(forecast["ds"], forecast["forecast"], color=EMERALD, linewidth=2.8, marker="o", label="Forecast")
    ax.fill_between(
        forecast["ds"],
        forecast["lower_95"],
        forecast["upper_95"],
        color=PURPLE,
        alpha=0.22,
        label="95% interval",
    )
    ax.set_title(title, weight="bold", fontsize=18)
    ax.set_xlabel("Month")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.35)
    if percentage_axis:
        ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.legend(frameon=False)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHARTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def run() -> None:
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    FORECAST_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    ts = pd.read_csv(PROCESSED_DIR / "forecasting_input_monthly.csv", parse_dates=["ds"])
    outputs = {}

    booking_fc, booking_metrics = train_forecast(ts, "y_booking_demand")
    booking_fc.to_csv(FORECAST_DIR / "booking_demand_forecast.csv", index=False)
    plot_forecast(
        ts,
        booking_fc,
        "y_booking_demand",
        "Booking Demand Forecast",
        "Bookings",
        "booking_demand_forecast.png",
    )
    outputs["booking_demand"] = booking_metrics
    write_forecast_report(
        "booking_demand_report.md",
        "Booking Demand Forecast Report",
        "y_booking_demand",
        booking_fc,
        booking_metrics,
    )

    occupancy_fc, occupancy_metrics = train_forecast(ts, "y_occupancy_rate")
    occupancy_fc.to_csv(FORECAST_DIR / "occupancy_rate_forecast.csv", index=False)
    plot_forecast(
        ts,
        occupancy_fc,
        "y_occupancy_rate",
        "Occupancy Rate Forecast",
        "Occupancy Rate",
        "occupancy_rate_forecast.png",
        percentage_axis=True,
    )
    outputs["occupancy_rate"] = occupancy_metrics
    write_forecast_report(
        "occupancy_forecast_report.md",
        "Occupancy Forecast Report",
        "y_occupancy_rate",
        occupancy_fc,
        occupancy_metrics,
    )

    revenue_fc, revenue_metrics = train_forecast(ts, "y_revenue")
    revenue_fc.to_csv(FORECAST_DIR / "revenue_forecast.csv", index=False)
    plot_forecast(
        ts,
        revenue_fc,
        "y_revenue",
        "Realized Revenue Forecast",
        "Revenue",
        "revenue_forecast.png",
    )
    outputs["revenue"] = revenue_metrics
    write_forecast_report(
        "revenue_forecast_report.md",
        "Revenue Forecast Report",
        "y_revenue",
        revenue_fc,
        revenue_metrics,
    )

    with (FORECAST_DIR / "forecast_accuracy_metrics.json").open("w", encoding="utf-8") as fp:
        json.dump(outputs, fp, indent=2)
    write_model_summary(outputs)

    print("Forecast outputs created.")


if __name__ == "__main__":
    run()