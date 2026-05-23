-- models/staging/stg_sales.sql
-- ─────────────────────────────────────────────────────────────────
-- STAGING LAYER
-- Takes the raw table loaded by ingest.py and:
--   1. Casts columns to the correct types
--   2. Renames columns to be consistent
--   3. Filters out any bad rows (negative revenue, nulls)
-- This becomes the trusted base for all downstream models.
-- ─────────────────────────────────────────────────────────────────

with raw as (

    select * from {{ source('raw', 'raw_sales') }}

),

cleaned as (

    select
        -- Cast month to a proper date (first day of the month)
        strptime(month, '%Y-%m')::date   as month,

        -- Trim whitespace from product name just in case
        trim(product)                     as product,

        -- Ensure revenue is a float
        revenue::double                   as revenue,

        -- Ensure units is an integer
        units_sold::integer               as units_sold,

        -- Derived: average revenue per unit
        round(revenue::double / nullif(units_sold::integer, 0), 2) as avg_revenue_per_unit

    from raw

    -- Filter out rows that would break downstream calculations
    where revenue > 0
      and units_sold > 0
      and product is not null
      and month is not null

)

select * from cleaned
