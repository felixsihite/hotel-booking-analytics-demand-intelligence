# Data Dictionary

This document describes the primary analytical tables used by the Streamlit application and SQL BI layer.

## hotel_bookings_cleaned

| Column | Type | Non-Null Rate | Business Definition |
|---|---:|---:|---|
| booking_id | int64 | 100.00% | Unique analytical booking identifier generated during preprocessing. |
| hotel | object | 100.00% | Hotel type: City Hotel or Resort Hotel. |
| is_canceled | int64 | 100.00% | Cancellation flag where 1 means canceled and 0 means not canceled. |
| lead_time | int64 | 100.00% | Number of days between booking creation and arrival date. |
| arrival_date_year | int64 | 100.00% | Source or engineered analytical field. |
| arrival_date_month | object | 100.00% | Source or engineered analytical field. |
| arrival_date_week_number | int64 | 100.00% | Source or engineered analytical field. |
| arrival_date_day_of_month | int64 | 100.00% | Source or engineered analytical field. |
| stays_in_weekend_nights | int64 | 100.00% | Source or engineered analytical field. |
| stays_in_week_nights | int64 | 100.00% | Source or engineered analytical field. |
| adults | int64 | 100.00% | Source or engineered analytical field. |
| children | int64 | 100.00% | Source or engineered analytical field. |
| babies | int64 | 100.00% | Source or engineered analytical field. |
| meal | object | 100.00% | Source or engineered analytical field. |
| country | object | 100.00% | Source or engineered analytical field. |
| market_segment | object | 100.00% | Commercial market segment for the reservation. |
| distribution_channel | object | 100.00% | Booking distribution channel. |
| is_repeated_guest | int64 | 100.00% | Source or engineered analytical field. |
| previous_cancellations | int64 | 100.00% | Source or engineered analytical field. |
| previous_bookings_not_canceled | int64 | 100.00% | Source or engineered analytical field. |
| reserved_room_type | object | 100.00% | Source or engineered analytical field. |
| assigned_room_type | object | 100.00% | Source or engineered analytical field. |
| booking_changes | int64 | 100.00% | Source or engineered analytical field. |
| deposit_type | object | 100.00% | Source or engineered analytical field. |
| agent | int64 | 100.00% | Source or engineered analytical field. |
| company | int64 | 100.00% | Source or engineered analytical field. |
| days_in_waiting_list | int64 | 100.00% | Source or engineered analytical field. |
| customer_type | object | 100.00% | Customer contract or booking type. |
| adr | float64 | 100.00% | Source or engineered analytical field. |
| required_car_parking_spaces | int64 | 100.00% | Source or engineered analytical field. |
| total_of_special_requests | int64 | 100.00% | Source or engineered analytical field. |
| reservation_status | object | 100.00% | Source or engineered analytical field. |
| reservation_status_date | object | 100.00% | Source or engineered analytical field. |
| arrival_month_number | int64 | 100.00% | Source or engineered analytical field. |
| arrival_date | datetime64[ns] | 100.00% | Constructed guest arrival date. |
| arrival_year_month | object | 100.00% | Arrival period in YYYY-MM format. |
| arrival_quarter | object | 100.00% | Source or engineered analytical field. |
| arrival_day_name | object | 100.00% | Source or engineered analytical field. |
| season | object | 100.00% | Arrival season derived from arrival month. |
| has_agent | int64 | 100.00% | Source or engineered analytical field. |
| has_company | int64 | 100.00% | Source or engineered analytical field. |
| total_guests | int64 | 100.00% | Total adults, children, and babies. |
| total_nights | int64 | 100.00% | Weekend nights plus week nights. |
| weekend_share | float64 | 100.00% | Source or engineered analytical field. |
| is_family_booking | int64 | 100.00% | Source or engineered analytical field. |
| room_type_changed | int64 | 100.00% | Source or engineered analytical field. |
| is_transient | int64 | 100.00% | Source or engineered analytical field. |
| is_group_or_contract | int64 | 100.00% | Source or engineered analytical field. |
| zero_guest_flag | int64 | 100.00% | Source or engineered analytical field. |
| zero_night_flag | int64 | 100.00% | Source or engineered analytical field. |
| negative_adr_flag | int64 | 100.00% | Source or engineered analytical field. |
| extreme_lead_time_flag | int64 | 100.00% | Source or engineered analytical field. |
| adr_outlier_flag | int64 | 100.00% | Source or engineered analytical field. |
| adr_clean | float64 | 100.00% | Cleaned average daily rate after negative values and extreme outliers are handled. |
| lead_time_band | object | 100.00% | Business-friendly lead-time category. |
| stay_length_band | object | 100.00% | Source or engineered analytical field. |
| guest_size_segment | object | 100.00% | Guest-size category for customer behavior analysis. |
| gross_booking_value | float64 | 100.00% | Estimated booking value using cleaned ADR multiplied by total nights. |
| realized_room_nights | int64 | 100.00% | Room nights retained from non-canceled bookings. |
| canceled_room_nights | int64 | 100.00% | Room nights lost to canceled bookings. |
| realized_revenue | float64 | 100.00% | Estimated revenue retained from non-canceled bookings. |
| lost_revenue_estimate | float64 | 100.00% | Estimated revenue exposure from canceled bookings. |
| booking_reliability_score | int64 | 100.00% | Composite reliability score based on cancellation, lead time, prior cancellation, repeat guest, and special request signals. |
| cancellation_risk_tier | object | 100.00% | Low, Moderate, High, or Critical cancellation risk grouping. |

## monthly_demand

| Column | Type | Non-Null Rate | Business Definition |
|---|---:|---:|---|
| hotel | object | 100.00% | Hotel type: City Hotel or Resort Hotel. |
| arrival_year_month | object | 100.00% | Arrival period in YYYY-MM format. |
| arrival_date | datetime64[ns] | 100.00% | Constructed guest arrival date. |
| bookings | int64 | 100.00% | Source or engineered analytical field. |
| cancellations | int64 | 100.00% | Source or engineered analytical field. |
| room_nights_requested | int64 | 100.00% | Source or engineered analytical field. |
| room_nights_realized | int64 | 100.00% | Source or engineered analytical field. |
| room_nights_canceled | int64 | 100.00% | Source or engineered analytical field. |
| gross_booking_value | float64 | 100.00% | Estimated booking value using cleaned ADR multiplied by total nights. |
| realized_revenue | float64 | 100.00% | Estimated revenue retained from non-canceled bookings. |
| lost_revenue_estimate | float64 | 100.00% | Estimated revenue exposure from canceled bookings. |
| adr | float64 | 100.00% | Source or engineered analytical field. |
| average_lead_time | float64 | 100.00% | Source or engineered analytical field. |
| total_guests | int64 | 100.00% | Total adults, children, and babies. |
| repeat_guest_rate | float64 | 100.00% | Source or engineered analytical field. |
| special_request_rate | float64 | 100.00% | Source or engineered analytical field. |
| cancellation_rate | float64 | 100.00% | Source or engineered analytical field. |
| capacity_room_night_proxy | float64 | 100.00% | Source or engineered analytical field. |
| occupancy_rate_estimate | float64 | 100.00% | Estimated occupancy using realized room nights divided by capacity proxy. |
| revenue_opportunity_index | float64 | 100.00% | Composite opportunity metric combining occupancy gap, cancellation rate, and lost revenue share. |
| revpar_estimate | float64 | 100.00% | Estimated revenue per available room using realized revenue divided by capacity proxy. |
| year | int64 | 100.00% | Source or engineered analytical field. |
| month | int64 | 100.00% | Source or engineered analytical field. |
| month_name | object | 100.00% | Source or engineered analytical field. |