# Databricks notebook source
dbutils.widgets.text("history_start", "1999-01-04", "First date to load")
HISTORY_START = dbutils.widgets.get("history_start")

# COMMAND ----------

import requests
from datetime import date, timedelta
from pyspark.sql import functions as F

API  = "https://api.frankfurter.dev/v1"
BASE = "EUR"

# COMMAND ----------

watermark = spark.sql("SELECT max(rate_date) AS wm FROM workspace.fx_silver.rates").collect()[0]["wm"]
start = date.fromisoformat(HISTORY_START) if watermark is None else watermark + timedelta(days=1)
end   = date.today()

print(f"watermark={watermark}  loading {start} -> {end}")

if start > end:
    dbutils.notebook.exit("up_to_date")

# COMMAND ----------

def fetch(d1, d2):
    r = requests.get(f"{API}/{d1}..{d2}", params={"base": BASE}, timeout=90)
    r.raise_for_status()
    return r.json()

rows = []
cur  = start

while cur <= end:
    stop = min(date(cur.year, 12, 31), end)
    data = fetch(cur, stop)
    for day, quotes in data["rates"].items():
        for ccy, rate in quotes.items():
            rows.append((day, BASE, ccy, float(rate)))
    print(f"  {cur.year}: {len(data['rates'])} days")
    cur = date(cur.year + 1, 1, 1)

print("rows:", len(rows))

# COMMAND ----------

if not rows:
    dbutils.notebook.exit("no_rows")

fx = (spark.createDataFrame(rows, "rate_date string, base_ccy string, quote_ccy string, rate double")
        .withColumn("rate_date", F.to_date("rate_date"))
        .withColumn("_loaded_at", F.current_timestamp()))

fx.write.format("delta").mode("append").saveAsTable("workspace.fx_bronze.rates_raw")

print("appended", fx.count(), "| bronze total", spark.table("workspace.fx_bronze.rates_raw").count())
