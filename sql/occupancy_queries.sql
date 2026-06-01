-- Hotel Booking Analytics & Demand Intelligence
-- Occupancy, utilization, and seasonal planning queries

-- 1. Estimated monthly occupancy by hotel
SELECT
    hotel,
    arrival_year_month,
    bookings,
    room_nights_requested,
    room_nights_realized,
    capacity_room_night_proxy,
    ROUND(100.0 * occupancy_rate_estimate, 2) AS occupancy_rate_pct,
    ROUND(revpar_estimate, 2) AS revpar_estimate,
    ROUND(100.0 * cancellation_rate, 2) AS cancellation_rate_pct,
    ROUND(realized_revenue, 2) AS realized_revenue
FROM mart_monthly_demand
ORDER BY arrival_year_month, hotel;

-- 2. Seasonal demand aggregation
SELECT
    hotel,
    month_name,
    ROUND(AVG(bookings), 2) AS avg_monthly_bookings,
    ROUND(AVG(room_nights_realized), 2) AS avg_realized_room_nights,
    ROUND(100.0 * AVG(occupancy_rate_estimate), 2) AS avg_occupancy_rate_pct,
    ROUND(AVG(revpar_estimate), 2) AS avg_revpar_estimate,
    ROUND(100.0 * AVG(cancellation_rate), 2) AS avg_cancellation_rate_pct,
    ROUND(SUM(realized_revenue), 2) AS realized_revenue
FROM mart_monthly_demand
GROUP BY hotel, month_name, month
ORDER BY hotel, month;

-- 3. Low-utilization months for commercial action
SELECT
    hotel,
    arrival_year_month,
    ROUND(100.0 * occupancy_rate_estimate, 2) AS occupancy_rate_pct,
    ROUND(capacity_room_night_proxy - room_nights_realized, 2) AS unused_room_night_capacity,
    ROUND((capacity_room_night_proxy - room_nights_realized) * adr, 2) AS theoretical_revenue_gap,
    ROUND(100.0 * revenue_opportunity_index, 2) AS revenue_opportunity_index_pct
FROM mart_monthly_demand
WHERE occupancy_rate_estimate < 0.70
ORDER BY theoretical_revenue_gap DESC;

-- 4. Peak occupancy months for pricing discipline
SELECT
    hotel,
    arrival_year_month,
    ROUND(100.0 * occupancy_rate_estimate, 2) AS occupancy_rate_pct,
    ROUND(adr, 2) AS avg_daily_rate,
    ROUND(revpar_estimate, 2) AS revpar_estimate,
    ROUND(realized_revenue, 2) AS realized_revenue,
    ROUND(100.0 * cancellation_rate, 2) AS cancellation_rate_pct
FROM mart_monthly_demand
WHERE occupancy_rate_estimate >= 0.85
ORDER BY occupancy_rate_estimate DESC, realized_revenue DESC;