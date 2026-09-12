# Databricks notebook source
tests = {
    "grain_violations": """
        SELECT count(*) FROM (
          SELECT date_key, currency_code
          FROM workspace.fx_gold.fact_daily_rate
          GROUP BY date_key, currency_code
          HAVING count(*) > 1)
    """,
    "orphan_date_keys": """
        SELECT count(*) FROM workspace.fx_gold.fact_daily_rate f
        LEFT ANTI JOIN workspace.fx_gold.dim_date d ON f.date_key = d.date_key
    """,
    "orphan_currency_codes": """
        SELECT count(*) FROM workspace.fx_gold.fact_daily_rate f
        LEFT ANTI JOIN workspace.fx_gold.dim_currency c ON f.currency_code = c.currency_code
    """,
    "impossible_rates": """
        SELECT count(*) FROM workspace.fx_gold.fact_daily_rate WHERE rate <= 0
    """,
    "row_count_mismatch": """
        SELECT abs(
          (SELECT count(*) FROM workspace.fx_gold.fact_daily_rate) -
          (SELECT count(*) FROM workspace.fx_silver.rates WHERE base_ccy = 'EUR'))
    """,
    "suspicious_gaps": """
        SELECT count(*) FROM (
          SELECT datediff(full_date, lag(full_date) OVER (ORDER BY full_date)) AS gap_days
          FROM workspace.fx_gold.dim_date)
        WHERE gap_days > 5
    """,
}

# COMMAND ----------

failed = []

for name, sql in tests.items():
    result = spark.sql(sql).collect()[0][0]
    print(f"{'PASS' if result == 0 else 'FAIL'}  {name}: {result}")
    if result != 0:
        failed.append(f"{name}={result}")

# COMMAND ----------

if failed:
    raise Exception("Tests failed: " + ", ".join(failed))

print("All tests passed.")
