# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE workspace.fx_gold.dim_date AS
# MAGIC SELECT DISTINCT
# MAGIC   date_format(rate_date, 'yyyyMMdd')  AS date_key,
# MAGIC   rate_date                           AS full_date,
# MAGIC   year(rate_date)                     AS year,
# MAGIC   quarter(rate_date)                  AS quarter,
# MAGIC   month(rate_date)                    AS month,
# MAGIC   date_format(rate_date, 'MMMM')      AS month_name,
# MAGIC   date_format(rate_date, 'EEEE')      AS day_name
# MAGIC FROM workspace.fx_silver.rates;

# COMMAND ----------

import requests

names = requests.get("https://api.frankfurter.dev/v1/currencies", timeout=30).json()
spark.createDataFrame(list(names.items()), "currency_code string, currency_name string") \
     .createOrReplaceTempView("api_names")

print("published by the API today:", len(names))

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE workspace.fx_gold.dim_currency AS
# MAGIC SELECT
# MAGIC   s.currency_code,
# MAGIC   coalesce(a.currency_name, s.currency_code) AS currency_name,
# MAGIC   a.currency_name IS NOT NULL                AS is_currently_published,
# MAGIC   s.first_date,
# MAGIC   s.last_date
# MAGIC FROM (
# MAGIC   SELECT quote_ccy     AS currency_code,
# MAGIC          min(rate_date) AS first_date,
# MAGIC          max(rate_date) AS last_date
# MAGIC   FROM workspace.fx_silver.rates
# MAGIC   GROUP BY quote_ccy
# MAGIC ) s
# MAGIC LEFT JOIN api_names a ON a.currency_code = s.currency_code;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT currency_code, first_date, last_date
# MAGIC FROM workspace.fx_gold.dim_currency
# MAGIC WHERE NOT is_currently_published
# MAGIC ORDER BY last_date DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE workspace.fx_gold.fact_daily_rate AS
# MAGIC WITH base AS (
# MAGIC   SELECT
# MAGIC     date_format(rate_date, 'yyyyMMdd') AS date_key,
# MAGIC     quote_ccy                          AS currency_code,
# MAGIC     rate_date,
# MAGIC     rate
# MAGIC   FROM workspace.fx_silver.rates
# MAGIC   WHERE base_ccy = 'EUR'
# MAGIC )
# MAGIC SELECT
# MAGIC   date_key,
# MAGIC   currency_code,
# MAGIC   rate,
# MAGIC   lag(rate) OVER w AS prev_rate,
# MAGIC   round(100 * (rate - lag(rate) OVER w) / lag(rate) OVER w, 4) AS daily_change_pct,
# MAGIC   round(avg(rate) OVER (PARTITION BY currency_code ORDER BY rate_date
# MAGIC                         ROWS BETWEEN 29 PRECEDING AND CURRENT ROW), 6) AS moving_avg_30d
# MAGIC FROM base
# MAGIC WINDOW w AS (PARTITION BY currency_code ORDER BY rate_date);

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT d.year,
# MAGIC        round(avg(f.rate), 2) AS avg_inr_per_eur,
# MAGIC        round(min(f.rate), 2) AS low,
# MAGIC        round(max(f.rate), 2) AS high
# MAGIC FROM workspace.fx_gold.fact_daily_rate f
# MAGIC JOIN workspace.fx_gold.dim_date d ON f.date_key = d.date_key
# MAGIC WHERE f.currency_code = 'INR'
# MAGIC GROUP BY d.year
# MAGIC ORDER BY d.year;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT c.currency_name,
# MAGIC        round(stddev(f.daily_change_pct), 4) AS volatility,
# MAGIC        count(*)                             AS days
# MAGIC FROM workspace.fx_gold.fact_daily_rate f
# MAGIC JOIN workspace.fx_gold.dim_currency c ON f.currency_code = c.currency_code
# MAGIC GROUP BY c.currency_name
# MAGIC ORDER BY volatility DESC
# MAGIC LIMIT 10;
