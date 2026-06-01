# Data Quality Report

## Summary

The dataset has been cleaned and converted into SQL-ready analytical tables for hospitality analytics, forecasting, segmentation, cancellation risk, and revenue optimization.

## Core Data Health Checks

| Check | Value | Interpretation |
|---|---:|---|
| Raw rows | 119,390 | Reference input volume |
| Processed booking rows | 119,210 | Cleaned analytical booking rows |
| Removed invalid rows | 180 | Rows removed during preprocessing, primarily invalid guest records |
| Processed duplicate booking_id | 0 | Should be 0 |
| Missing arrival_date | 0 | Should be 0 |
| Zero guest records | 0 | Should be 0 after cleaning |
| Negative ADR after cleaning | 0 | Should be 0 |
| ADR outlier flags retained | 589 | Flags retained for auditability |
| Monthly demand rows | 52 | Hotel-month analytical mart |
| Forecast input rows | 26 | Monthly time-series rows |

## Raw Missing Value Profile

Top raw missing-value fields:

- company: 94.31%
- agent: 13.69%
- country: 0.41%
- children: 0.00%
- arrival_date_month: 0.00%
- arrival_date_week_number: 0.00%
- hotel: 0.00%
- is_canceled: 0.00%

## Cleaning Decisions

- Missing `company` and `agent` identifiers are converted to `0` and paired with binary indicators for auditability.
- Missing `country` values are assigned to `Unknown`.
- Missing `children` values are imputed to `0`.
- Negative ADR values and extreme ADR values are handled through the engineered `adr_clean` field.
- Invalid zero-guest bookings are removed from the cleaned analytical dataset.
- Outlier and anomaly flags are retained so the cleaning process stays transparent.

## Professional Use Notes

The dataset does not include true room inventory. Occupancy and RevPAR are therefore estimated using a capacity proxy derived from observed realized room-night peaks by hotel. This is clearly documented for portfolio transparency and should be replaced with actual inventory data in production.