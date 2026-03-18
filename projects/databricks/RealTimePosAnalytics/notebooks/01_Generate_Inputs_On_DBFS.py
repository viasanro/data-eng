# Databricks notebook source
# Generate synthetic data directly into managed Delta tables (Serverless-safe).
#
# Databricks Serverless often has DBFS root disabled, so writing to `dbfs:/tmp/...`
# (and calling `dbutils.fs.mkdirs`) can fail. This notebook generates:
# - Bronze POS events (insert-oriented) into `rtpa_bronze.pos_events_stream`
# - Bronze floor snapshots (batch) into `rtpa_bronze.floor_snapshots_batch`
# - Seed tables into `rtpa_bronze.*_seed`

from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta, timezone

from pyspark.sql import functions as F
from pyspark.sql import types as T

# COMMAND ----------

# MAGIC %run ./rtpa_lib

# COMMAND ----------

# Parameters
dbutils.widgets.text("db_name_bronze", "rtpa_bronze", "Bronze schema/database")
dbutils.widgets.text("days", "30", "Days to simulate")
dbutils.widgets.text("stores", "2", "Stores")
dbutils.widgets.text("skus", "200", "SKUs")
dbutils.widgets.text("events_per_store_per_hour", "30", "Events per store per hour")
dbutils.widgets.text("snapshot_every_hours", "24", "Snapshot cadence (hours)")
dbutils.widgets.text("seed", "7", "Random seed")
dbutils.widgets.dropdown("reset_tables", "true", ["true", "false"], "Drop & recreate bronze tables?")

db_bronze = dbutils.widgets.get("db_name_bronze").strip()
days = int(dbutils.widgets.get("days"))
n_stores = int(dbutils.widgets.get("stores"))
n_skus = int(dbutils.widgets.get("skus"))
events_per_store_per_hour = int(dbutils.widgets.get("events_per_store_per_hour"))
snapshot_every_hours = int(dbutils.widgets.get("snapshot_every_hours"))
seed = int(dbutils.widgets.get("seed"))
reset_tables = dbutils.widgets.get("reset_tables").strip().lower() == "true"

spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_bronze}")

bronze_events_table = f"{db_bronze}.pos_events_stream"
bronze_snapshots_table = f"{db_bronze}.floor_snapshots_batch"
seed_stores_table = f"{db_bronze}.stores_seed"
seed_products_table = f"{db_bronze}.products_seed"
seed_starting_stock_table = f"{db_bronze}.starting_stock_seed"

# COMMAND ----------

if reset_tables:
    for t in [
        bronze_events_table,
        bronze_snapshots_table,
        seed_stores_table,
        seed_products_table,
        seed_starting_stock_table,
    ]:
        spark.sql(f"DROP TABLE IF EXISTS {t}")

# COMMAND ----------

rng = random.Random(seed)
stores = [f"S{idx:03d}" for idx in range(1, n_stores + 1)]
skus = [f"SKU{idx:05d}" for idx in range(1, n_skus + 1)]

# Seeds
starting_rows = [(s, sku, rng.randint(10, 80)) for s in stores for sku in skus]
starting_df = spark.createDataFrame(starting_rows, schema=["store_id", "sku", "starting_qty"])
stores_df = spark.createDataFrame([(s,) for s in stores], schema=["store_id"])
products_df = spark.createDataFrame([(sku,) for sku in skus], schema=["sku"])

stores_df.write.format("delta").mode("overwrite").saveAsTable(seed_stores_table)
products_df.write.format("delta").mode("overwrite").saveAsTable(seed_products_table)
starting_df.write.format("delta").mode("overwrite").saveAsTable(seed_starting_stock_table)

# COMMAND ----------

event_types = ["sale", "restock", "shrink", "online_order", "store_pickup"]
weights = [0.58, 0.17, 0.03, 0.12, 0.10]


def qty_for(event_type: str) -> int:
    if event_type in ("sale", "store_pickup"):
        return rng.randint(1, 5)
    if event_type == "online_order":
        return rng.randint(1, 3)
    if event_type == "restock":
        return rng.randint(5, 25)
    if event_type == "shrink":
        return rng.randint(1, 2)
    return 1


def sign_for(event_type: str) -> int:
    return 1 if event_type == "restock" else -1


stock = {(r["store_id"], r["sku"]): int(r["starting_qty"]) for r in starting_df.collect()}

start_utc = datetime(2026, 1, 1, 0, 0, 0)
end_utc = start_utc + timedelta(days=days)

current = start_utc
next_snapshot = start_utc
snapshot_every = timedelta(hours=snapshot_every_hours)

while current < end_utc:
    # Build one hour worth of events in memory and append to Bronze table
    events = []
    for store_id in stores:
        for _ in range(events_per_store_per_hour):
            sku = rng.choice(skus)
            event_type = rng.choices(event_types, weights=weights, k=1)[0]
            qty = qty_for(event_type)
            stock[(store_id, sku)] = max(0, stock[(store_id, sku)] + sign_for(event_type) * qty)
            events.append(
                {
                    "event_id": str(uuid.uuid4()),
                    # Spark Connect expects a real datetime for TimestampType columns
                    "event_time": current.replace(tzinfo=timezone.utc),
                    "event_date": current.strftime("%Y-%m-%d"),
                    "store_id": store_id,
                    "sku": sku,
                    "event_type": event_type,
                    "qty": qty,
                    "source": "pos" if event_type in ("sale", "shrink") else ("wms" if event_type == "restock" else "ecom"),
                    "channel": "instore" if event_type in ("sale", "restock", "shrink") else "online",
                }
            )

    events_df = (
        spark.createDataFrame(events, schema=POS_EVENT_SCHEMA)
        .withColumn("_ingest_time", F.current_timestamp())
    )
    events_df.write.format("delta").mode("append").saveAsTable(bronze_events_table)

    if current >= next_snapshot:
        snap_time = current + timedelta(minutes=15)
        snap_rows = []
        for (store_id, sku), true_qty in stock.items():
            noise = int(round(true_qty * rng.uniform(-0.03, 0.03)))
            snap_rows.append(
                (
                    snap_time.strftime("%Y-%m-%d"),
                    # Keep as datetime for Spark Connect compatibility
                    snap_time.replace(tzinfo=timezone.utc),
                    store_id,
                    sku,
                    max(0, true_qty + noise),
                )
            )
        snap_df = spark.createDataFrame(
            snap_rows,
            schema=T.StructType(
                [
                    T.StructField("snapshot_date", T.StringType(), False),
                    T.StructField("snapshot_time", T.TimestampType(), False),
                    T.StructField("store_id", T.StringType(), False),
                    T.StructField("sku", T.StringType(), False),
                    T.StructField("on_floor_qty", T.IntegerType(), False),
                ]
            ),
        ).withColumn("_ingest_time", F.current_timestamp())

        snap_df.write.format("delta").mode("append").saveAsTable(bronze_snapshots_table)
        next_snapshot = current + snapshot_every

    current += timedelta(hours=1)

display(
    spark.createDataFrame(
        [
            ("bronze_events_table", bronze_events_table),
            ("bronze_snapshots_table", bronze_snapshots_table),
            ("seed_starting_stock_table", seed_starting_stock_table),
        ],
        ["key", "value"],
    )
)

