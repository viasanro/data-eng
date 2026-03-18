# Databricks notebook source
# This notebook centralizes configuration used by the demo notebooks.

# COMMAND ----------
# MAGIC %run ./rtpa_lib

import json

# COMMAND ----------

# Widget-based configuration (works in Databricks Jobs too)
dbutils.widgets.text("config_path", "dbfs:/tmp/rtpa/rtpa_config.json", "Config JSON path")
dbutils.widgets.text("base_path", "dbfs:/tmp/rtpa", "Base path (override)")
dbutils.widgets.text("db_name_bronze", "rtpa_bronze", "Bronze schema/database")
dbutils.widgets.text("db_name_silver", "rtpa_silver", "Silver schema/database")
dbutils.widgets.text("db_name_gold", "rtpa_gold", "Gold schema/database")

config_path = dbutils.widgets.get("config_path").strip()

# COMMAND ----------

# Load config from DBFS if present; otherwise build from widgets
try:
    raw = dbutils.fs.head(config_path, 1024 * 1024)
    cfg = json.loads(raw)
except Exception:
    cfg = {
        "db_name_bronze": dbutils.widgets.get("db_name_bronze").strip(),
        "db_name_silver": dbutils.widgets.get("db_name_silver").strip(),
        "db_name_gold": dbutils.widgets.get("db_name_gold").strip(),
        "base_path": dbutils.widgets.get("base_path").strip(),
        "streaming_input_path": f'{dbutils.widgets.get("base_path").strip().rstrip("/")}/input/stream_pos_events',
        "batch_input_path": f'{dbutils.widgets.get("base_path").strip().rstrip("/")}/input/batch_floor_snapshots',
        "checkpoint_base_path": f'{dbutils.widgets.get("base_path").strip().rstrip("/")}/checkpoints',
        "seed_path": f'{dbutils.widgets.get("base_path").strip().rstrip("/")}/input/seeds',
    }

cfg

# COMMAND ----------

cfg_obj = RtpaConfig.from_dict(cfg)
paths = build_paths(cfg_obj)

display(cfg_obj)

# COMMAND ----------

# Create databases (schemas) for medallion layers
spark.sql(f"CREATE DATABASE IF NOT EXISTS {cfg_obj.db_name_bronze}")
spark.sql(f"CREATE DATABASE IF NOT EXISTS {cfg_obj.db_name_silver}")
spark.sql(f"CREATE DATABASE IF NOT EXISTS {cfg_obj.db_name_gold}")

print("Databases ensured:")
print(cfg_obj.db_name_bronze, cfg_obj.db_name_silver, cfg_obj.db_name_gold)

