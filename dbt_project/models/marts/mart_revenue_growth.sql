-- models/marts/mart_revenue_growth.sql
-- ─────────────────────────────────────────────────────────────────
-- MART LAYER (the "gold" table the API will query)
-- For each product and month, computes:
--   - Revenue vs previous month (LAG window function)
--   - Month-over-month growth percentage
--   - An anomaly flag (growth dropped > 10% from prior month)
--   - Rolling 3-month average revenue
-- This is the table that powers the Claude AI insight in Session 3.
-- ─────────────────────────────────────────────────────────────────

with base as (

    select * from {{ ref('stg_sales') }}

),

with_lag as (

    select
        product,
        month,
        revenue,
        units_sold,
        avg_revenue_per_unit,

        -- Previous month's revenue for the same product
        lag(revenue) over (
            partition by product
            order by month
        ) as prev_month_revenue,

        -- Row number to identify the first month (no prior data)
        row_number() over (
            partition by product
            order by month
        ) as month_num

    from base

),

with_growth as (

    select
        product,
        month,
        revenue,
        units_sold,
        avg_revenue_per_unit,
        prev_month_revenue,
        month_num,

        -- Month-over-month growth %: null for the first month
        case
            when prev_month_revenue is not null and prev_month_revenue > 0
            then round(
                ((revenue - prev_month_revenue) / prev_month_revenue) * 100,
                2
            )
            else null
        end as mom_growth_pct,

        -- Rolling 3-month average revenue
        round(
            avg(revenue) over (
                partition by product
                order by month
                rows between 2 preceding and current row
            ),
            2
        ) as rolling_3m_avg_revenue

    from with_lag

),

final as (

    select
        product,
        month,
        revenue,
        units_sold,
        avg_revenue_per_unit,
        prev_month_revenue,
        mom_growth_pct,
        rolling_3m_avg_revenue,

        -- Risk flag: revenue dropped more than 10% vs prior month
        case
            when mom_growth_pct < -10 then true
            else false
        end as is_revenue_drop,

        -- Rank month within product (useful for the API to find best/worst)
        rank() over (
            partition by product
            order by revenue desc
        ) as revenue_rank

    from with_growth

)

select * from final
order by product, month
