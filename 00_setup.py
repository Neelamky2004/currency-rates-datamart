# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS workspace.fx_bronze;
# MAGIC CREATE SCHEMA IF NOT EXISTS workspace.fx_silver;
# MAGIC CREATE SCHEMA IF NOT EXISTS workspace.fx_gold;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS workspace.fx_bronze.rates_raw (
# MAGIC   rate_date   DATE,
# MAGIC   base_ccy    STRING,
# MAGIC   quote_ccy   STRING,
# MAGIC   rate        DOUBLE,
# MAGIC   _loaded_at  TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS workspace.fx_silver.rates (
# MAGIC   rate_date DATE,
# MAGIC   base_ccy  STRING,
# MAGIC   quote_ccy STRING,
# MAGIC   rate      DOUBLE
# MAGIC ) USING DELTA;

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW SCHEMAS IN workspace LIKE 'fx_*';
