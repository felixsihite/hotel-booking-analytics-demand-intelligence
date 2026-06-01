-- Hotel Booking Analytics & Demand Intelligence
-- Revenue opportunity, dynamic pricing, and commercial planning queries

-- 1. Revenue opportunity ranking by hotel-month
SELECT
    hotel,
    arrival_year_month,
    ROUND(100.0 * occupancy_rate_estimate, 2) AS occupancy_rate_pct,
    ROUND(100.0 * cancellation_rate, 2) AS cancellation_rate_pct,
    ROUND(adr, 2) AS adr,
    ROUND(revpar_estimate, 2) AS revpar_estimate,
    ROUND(realized_revenue, 2) AS realized_revenue,
    ROUND(lost_revenue_estimate, 2) AS lost_revenue_estimate,
    ROUND(100.0 * revenue_opportunity_index, 2) AS revenue_opportunity_index_pct
FROM mart_monthly_demand
ORDER BY revenue_opportunity_index DESC
LIMIT 20;

-- 2. Pricing opportunity classification
SELECT
    hotel,
    arrival_year_month,
    ROUND(100.0 * occupancy_rate_estimate, 2) AS occupancy_rate_pct,
    ROUND(adr, 2) AS avg_daily_rate,
    ROUND(100.0 * cancellation_rate, 2) AS cancellation_rate_pct,
    ROUND(realized_revenue, 2) AS realized_revenue,
    CASE
        WHEN occupancy_rate_estimate >= 0.85 AND cancellation_rate < 0.25
            THEN 'Increase ADR and restrict discounts'
        WHEN occupancy_rate_estimate >= 0.85 AND cancellation_rate >= 0.25
            THEN 'Increase ADR with cancellation controls'
        WHEN occupancy_rate_estimate BETWEEN 0.60 AND 0.85
            THEN 'Protect rate; optimize channel mix'
        WHEN occupancy_rate_estimate < 0.60 AND cancellation_rate >= 0.35
            THEN 'Stimulate demand and tighten unreliable channels'
        ELSE 'Promotional packages and direct booking campaigns'
    END AS pricing_recommendation
FROM mart_monthly_demand
ORDER BY arrival_year_month, hotel;

-- 3. Market segment revenue contribution
WITH segment_revenue AS (
    SELECT
        market_segment,
        COUNT(*) AS bookings,
        SUM(realized_revenue) AS realized_revenue,
        SUM(lost_revenue_estimate) AS lost_revenue_estimate,
        AVG(is_canceled) AS cancellation_rate
    FROM fact_bookings
    GROUP BY market_segment
),
total_revenue AS (
    SELECT SUM(realized_revenue) AS total_realized_revenue
    FROM fact_bookings
)
SELECT
    s.market_segment,
    s.bookings,
    ROUND(s.realized_revenue, 2) AS realized_revenue,
    ROUND(100.0 * s.realized_revenue / NULLIF(t.total_realized_revenue, 0), 2) AS revenue_share_pct,
    ROUND(100.0 * s.cancellation_rate, 2) AS cancellation_rate_pct,
    ROUND(s.lost_revenue_estimate, 2) AS lost_revenue_estimate
FROM segment_revenue s
CROSS JOIN total_revenue t
ORDER BY s.realized_revenue DESC;

-- 4. Estimated recoverable revenue from cancellation mitigation
SELECT
    hotel,
    market_segment,
    distribution_channel,
    COUNT(*) AS bookings,
    ROUND(100.0 * AVG(is_canceled), 2) AS cancellation_rate_pct,
    ROUND(SUM(lost_revenue_estimate), 2) AS lost_revenue_estimate,
    ROUND(SUM(lost_revenue_estimate) * 0.25, 2) AS conservative_recoverable_revenue
FROM fact_bookings
GROUP BY hotel, market_segment, distribution_channel
HAVING COUNT(*) >= 100
ORDER BY conservative_recoverable_revenue DESC;