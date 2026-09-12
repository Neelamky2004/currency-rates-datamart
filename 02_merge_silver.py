# Databricks notebook source
from delta.tables import DeltaTable

source = (spark.table("workspace.fx_bronze.rates_raw")
            .select("rate_date", "base_ccy", "quote_ccy", "rate")
            .dropDuplicates(["rate_date", "base_ccy", "quote_ccy"]))

print("silver before:", spark.table("workspace.fx_silver.rates").count())

# COMMAND ----------

(DeltaTable.forName(spark, "workspace.fx_silver.rates").alias("t")
   .merge(source.alias("s"),
          "t.rate_date = s.rate_date AND t.base_ccy = s.base_ccy AND t.quote_ccy = s.quote_ccy")
   .whenMatchedUpdateAll()
   .whenNotMatchedInsertAll()
   .execute())

print("silver after: ", spark.table("workspace.fx_silver.rates").count())

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   count(*)                  AS rows,
# MAGIC   count(DISTINCT quote_ccy) AS currencies,
# MAGIC   count(DISTINCT rate_date) AS trading_days,
# MAGIC   min(rate_date)            AS first_day,
# MAGIC   max(rate_date)            AS last_day
# MAGIC FROM workspace.fx_silver.rates;
