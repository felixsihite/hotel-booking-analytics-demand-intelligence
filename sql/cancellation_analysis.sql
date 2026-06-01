-- Hotel Booking Analytics & Demand Intelligence
-- Cancellation risk, driver, and exposure analysis

-- 1. Cancellation rate by hotel, channel, and market segment
SELECT
    hotel,
    market_segment,
    distribution_channel,
    COUNT(*) AS bookings,
    SUM(is_canceled) AS cancellations,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(SUM(lost_revenue_estimate), 2) AS lost_revenue_estimate
FROM fact_bookings
GROUP BY hotel, market_segment, distribution_channel
HAVING COUNT(*) >= 100
ORDER BY cancellation_rate_pct DESC, lost_revenue_estimate DESC;

-- 2. High-risk customer segment ranking
SELECT
    hotel,
    market_segment,
    distribution_channel,
    customer_type,
    lead_time_band,
    deposit_type,
    bookings,
    cancellations,
    ROUND(100.0 * cancellation_rate, 2) AS cancellation_rate_pct,
    ROUND(lost_revenue_estimate, 2) AS lost_revenue_estimate,
    ROUND(segment_risk_score, 2) AS segment_risk_score
FROM mart_customer_segments
WHERE bookings >= 50
ORDER BY segment_risk_score DESC
LIMIT 25;

-- 3. Cancellation exposure by deposit type
SELECT
    deposit_type,
    COUNT(*) AS bookings,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(AVG(lead_time), 2) AS avg_lead_time,
    ROUND(SUM(lost_revenue_estimate), 2) AS lost_revenue_estimate,
    ROUND(SUM(realized_revenue), 2) AS realized_revenue
FROM fact_bookings
GROUP BY deposit_type
ORDER BY cancellation_rate_pct DESC;

-- 4. Seasonal cancellation behavior
SELECT
    season,
    arrival_date_month,
    COUNT(*) AS bookings,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(SUM(lost_revenue_estimate), 2) AS lost_revenue_estimate,
    ROUND(AVG(booking_reliability_score), 2) AS avg_booking_reliability_score
FROM fact_bookings
GROUP BY season, arrival_date_month
ORDER BY
    CASE season
        WHEN 'Winter' THEN 1
        WHEN 'Spring' THEN 2
        WHEN 'Summer' THEN 3
        WHEN 'Autumn' THEN 4
        ELSE 5
    END,
    cancellation_rate_pct DESC;

-- 5. Cancellation driver indicators
SELECT
    CASE WHEN previous_cancellations > 0 THEN 'Previous cancellation history' ELSE 'No previous cancellation' END AS previous_cancel_group,
    CASE WHEN total_of_special_requests = 0 THEN 'No special requests' ELSE 'Has special requests' END AS request_group,
    CASE WHEN required_car_parking_spaces = 0 THEN 'No parking request' ELSE 'Parking requested' END AS parking_group,
    COUNT(*) AS bookings,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(AVG(booking_reliability_score), 2) AS avg_booking_reliability_score
FROM fact_bookings
GROUP BY previous_cancel_group, request_group, parking_group
ORDER BY cancellation_rate_pct DESC;