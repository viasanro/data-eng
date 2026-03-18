# Databricks notebook source
# OPTIONAL Bronze ingestion from files:
# - streaming insert-oriented POS events via Auto Loader (cloudFiles)
# - batch floor snapshots via CSV load (append)
#
# Note: In Databricks Serverless Free Edition, DBFS root is often disabled, so the
# recommended path is to use `01_Generate_Inputs_On_DBFS.py` (which writes directly
# to managed Delta tables) and skip this notebook.

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %run ./rtpa_lib

# COMMAND ----------

# Pull config/paths from the setup notebook (run it first)
# If you're using Databricks Repos, ensure `src/` is on PYTHONPATH:
# %pip install -e .

# Use managed tables instead of DBFS paths for Serverless compatibility
dbutils.widgets.text("db_name_bronze", "rtpa_bronze", "Bronze schema/database")
dbutils.widgets.text("use_managed_tables", "true", "Use managed tables (Serverless-compatible)")

db_bronze = dbutils.widgets.get("db_name_bronze").strip()
use_managed = dbutils.widgets.get("use_managed_tables").strip().lower() == "true"

bronze_events_table = f"{db_bronze}.pos_events_stream"
bronze_snapshots_table = f"{db_bronze}.floor_snapshots_batch"

# For Serverless, we use managed tables and skip DBFS paths entirely
if use_managed:
    print("Using managed Delta tables (Serverless-compatible)")
    bronze_events_path = None
    bronze_snapshots_path = None
    chk_events = None
else:
    # Legacy DBFS mode (not compatible with Serverless Free Edition)
    base_path = dbutils.widgets.get("base_path", "dbfs:/tmp/rtpa").strip().rstrip("/")
    streaming_input_path = f"{base_path}/input/stream_pos_events"
    batch_input_path = f"{base_path}/input/batch_floor_snapshots"
    checkpoint_base = f"{base_path}/checkpoints"
    
    bronze_events_path = f"{base_path}/delta/bronze/pos_events_stream"
    bronze_snapshots_path = f"{base_path}/delta/bronze/floor_snapshots_batch"
    chk_events = f"{checkpoint_base}/bronze_pos_events_stream"

# COMMAND ----------

spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_bronze}")

# COMMAND ----------

# Streaming ingestion (Auto Loader)
if use_managed:
    # Serverless-compatible: write directly to managed table
    events_stream_df = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "false")
        .schema(POS_EVENT_SCHEMA)
        .load(f"{db_bronze}.pos_events_stream_input")  # Use managed input table
        .withColumn("event_time", F.col("event_time").cast("timestamp"))
        .withColumn("_ingest_time", F.current_timestamp())
    )
    
    events_query = (
        events_stream_df.writeStream.format("delta")
        .outputMode("append")
        .partitionBy("event_date")
        .trigger(availableNow=True)
        .option("checkpointLocation", f"/tmp/_checkpoint/{bronze_events_table.replace('.', '_')}")
        .toTable(bronze_events_table)
    )
    
    events_query.awaitTermination()
else:
    # Legacy DBFS mode (not compatible with Serverless Free Edition)
    events_stream_df = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "false")
        .schema(POS_EVENT_SCHEMA)
        .load(streaming_input_path)
        .withColumn("event_time", F.col("event_time").cast("timestamp"))
        .withColumn("_ingest_time", F.current_timestamp())
    )

    events_query = (
        events_stream_df.writeStream.format("delta")
        .option("checkpointLocation", chk_events)
        .outputMode("append")
        .partitionBy("event_date")
        .trigger(availableNow=True)
        .start(bronze_events_path)
    )

    events_query.awaitTermination()

    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {bronze_events_table}
        USING DELTA
        LOCATION '{bronze_events_path}'
        """
    )

display(spark.table(bronze_events_table).limit(10))

# COMMAND ----------

# Batch ingestion (snapshots)
if use_managed:
    # Serverless-compatible: read from managed input table and write to managed table
    snapshots_df = (
        spark.read.format("delta")
        .table(f"{db_bronze}.floor_snapshots_input")
        .withColumn("_ingest_time", F.current_timestamp())
    )
    
    (
        snapshots_df.write.format("delta")
        .mode("append")
        .partitionBy("snapshot_date")
        .saveAsTable(bronze_snapshots_table)
    )
else:
    # Legacy DBFS mode (not compatible with Serverless Free Edition)
    snapshots_df = (
        spark.read.format("csv")
        .option("header", True)
        .schema(FLOOR_SNAPSHOT_SCHEMA)
        .load(batch_input_path)
        .withColumn("_ingest_time", F.current_timestamp())
    )

    (
        snapshots_df.write.format("delta")
        .mode("append")
        .partitionBy("snapshot_date")
        .save(bronze_snapshots_path)
    )

    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {bronze_snapshots_table}
        USING DELTA
        LOCATION '{bronze_snapshots_path}'
        """
    )

display(spark.table(bronze_snapshots_table).limit(10))

