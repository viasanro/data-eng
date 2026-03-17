# Databricks notebook source
# Silver layer:
# - normalize events into signed inventory movements
# - keep floor snapshots as-is (already clean schema)

from pyspark.sql import functions as F

# COMMAND ----------

dbutils.widgets.text("db_name_bronze", "rtpa_bronze", "Bronze schema/database")
dbutils.widgets.text("db_name_silver", "rtpa_silver", "Silver schema/database")

db_bronze = dbutils.widgets.get("db_name_bronze").strip()
db_silver = dbutils.widgets.get("db_name_silver").strip()

bronze_events_table = f"{db_bronze}.pos_events_stream"
bronze_snapshots_table = f"{db_bronze}.floor_snapshots_batch"

spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_silver}")

silver_movements_table = f"{db_silver}.inventory_movements"
silver_snapshots_table = f"{db_silver}.floor_snapshots"

# COMMAND ----------

events = spark.table(bronze_events_table)

movement_qty = (
    F.when(F.col("event_type") == F.lit("restock"), F.col("qty"))
    .otherwise(-F.col("qty"))
    .cast("int")
)

movements = (
    events.select(
        "event_id",
        "event_time",
        "event_date",
        "store_id",
        "sku",
        "event_type",
        "qty",
        movement_qty.alias("movement_qty"),
        "source",
        "channel",
        "_ingest_time",
    )
    .withColumn("event_time", F.col("event_time").cast("timestamp"))
    .withColumn("movement_time", F.col("event_time"))
)

(movements.write.format("delta").mode("overwrite").saveAsTable(silver_movements_table))

display(spark.table(silver_movements_table).limit(10))

# COMMAND ----------

snapshots = spark.table(bronze_snapshots_table).select(
    "snapshot_date",
    "snapshot_time",
    "store_id",
    "sku",
    "on_floor_qty",
    "_ingest_time",
)

(snapshots.write.format("delta").mode("overwrite").saveAsTable(silver_snapshots_table))

display(spark.table(silver_snapshots_table).limit(10))

