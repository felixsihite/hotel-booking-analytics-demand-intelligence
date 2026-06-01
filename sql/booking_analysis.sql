-- Hotel Booking Analytics & Demand Intelligence
-- Booking trend, channel, segment, and growth analysis
-- Target warehouse: data/warehouse/hotel_booking_analytics.sqlite

-- 1. Executive booking trend by hotel and month
SELECT
    hotel,
    arrival_year_month,
    COUNT(*) AS total_bookings,
    SUM(CASE WHEN is_canceled = 0 THEN 1 ELSE 0 END) AS realized_bookings,
    SUM(CASE WHEN is_canceled = 1 THEN 1 ELSE 0 END) AS canceled_bookings,
    ROUND(AVG(lead_time), 2) AS avg_lead_time,
    ROUND(AVG(adr_clean), 2) AS avg_daily_rate,
    ROUND(SUM(realized_revenue), 2) AS realized_revenue
FROM fact_bookings
GROUP BY hotel, arrival_year_month
ORDER BY arrival_year_month, hotel;

-- 2. Monthly booking growth
WITH monthly AS (
    SELECT
        arrival_year_month,
        COUNT(*) AS total_bookings
    FROM fact_bookings
    GROUP BY arrival_year_month
),
growth AS (
    SELECT
        arrival_year_month,
        total_bookings,
        LAG(total_bookings) OVER (ORDER BY arrival_year_month) AS previous_month_bookings
    FROM monthly
)
SELECT
    arrival_year_month,
    total_bookings,
    previous_month_bookings,
    ROUND(
        100.0 * (total_bookings - previous_month_bookings)
        / NULLIF(previous_month_bookings, 0),
        2
    ) AS month_over_month_growth_pct
FROM growth
ORDER BY arrival_year_month;

-- 3. Booking source scorecard
SELECT
    market_segment,
    distribution_channel,
    COUNT(*) AS bookings,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(AVG(lead_time), 2) AS avg_lead_time,
    ROUND(AVG(adr_clean), 2) AS avg_daily_rate,
    ROUND(SUM(realized_revenue), 2) AS realized_revenue,
    ROUND(SUM(realized_revenue) / NULLIF(COUNT(*), 0), 2) AS revenue_per_booking,
    ROUND(100.0 * AVG(is_repeated_guest), 2) AS repeat_guest_rate_pct
FROM fact_bookings
GROUP BY market_segment, distribution_channel
HAVING COUNT(*) >= 100
ORDER BY realized_revenue DESC;

-- 4. Lead-time performance analysis
SELECT
    lead_time_band,
    COUNT(*) AS bookings,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(AVG(adr_clean), 2) AS avg_daily_rate,
    ROUND(SUM(realized_revenue), 2) AS realized_revenue,
    ROUND(SUM(lost_revenue_estimate), 2) AS cancellation_revenue_exposure
FROM fact_bookings
GROUP BY lead_time_band
ORDER BY
    CASE lead_time_band
        WHEN 'Same week' THEN 1
        WHEN '1-4 weeks' THEN 2
        WHEN '1-3 months' THEN 3
        WHEN '3-6 months' THEN 4
        WHEN '6-12 months' THEN 5
        ELSE 6
    END;

-- 5. Customer booking behavior by type
SELECT
    customer_type,
    guest_size_segment,
    COUNT(*) AS bookings,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(AVG(total_nights), 2) AS avg_stay_length,
    ROUND(AVG(total_of_special_requests), 2) AS avg_special_requests,
    ROUND(SUM(realized_revenue), 2) AS realized_revenue
FROM fact_bookings
GROUP BY customer_type, guest_size_segment
ORDER BY realized_revenue DESC;