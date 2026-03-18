# Databricks notebook source
# Generate synthetic inputs directly into DBFS (or mounted cloud storage).
#
# This is useful when you don't want to run the local generator + upload step.

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

# Reuse config + paths
dbutils.widgets.text("base_path", "dbfs:/tmp/rtpa", "Base path")
dbutils.widgets.text("days", "30", "Days to simulate")
dbutils.widgets.text("stores", "2", "Stores")
dbutils.widgets.text("skus", "200", "SKUs")
dbutils.widgets.text("events_per_store_per_hour", "30", "Events per store per hour")
dbutils.widgets.text("snapshot_every_hours", "24", "Snapshot cadence (hours)")
dbutils.widgets.text("seed", "7", "Random seed")

base_path = dbutils.widgets.get("base_path").strip().rstrip("/")
days = int(dbutils.widgets.get("days"))
n_stores = int(dbutils.widgets.get("stores"))
n_skus = int(dbutils.widgets.get("skus"))
events_per_store_per_hour = int(dbutils.widgets.get("events_per_store_per_hour"))
snapshot_every_hours = int(dbutils.widgets.get("snapshot_every_hours"))
seed = int(dbutils.widgets.get("seed"))

streaming_input_path = f"{base_path}/input/stream_pos_events"
batch_input_path = f"{base_path}/input/batch_floor_snapshots"
seed_path = f"{base_path}/input/seeds"

# COMMAND ----------

def rm_if_exists(path: str) -> None:
    try:
        dbutils.fs.rm(path, True)
    except Exception:
        pass


# Clean and create fresh inputs (safe for demo; remove if you want incremental generation)
rm_if_exists(streaming_input_path)
rm_if_exists(batch_input_path)
rm_if_exists(seed_path)

dbutils.fs.mkdirs(streaming_input_path)
dbutils.fs.mkdirs(batch_input_path)
dbutils.fs.mkdirs(seed_path)

# COMMAND ----------

rng = random.Random(seed)
stores = [f"S{idx:03d}" for idx in range(1, n_stores + 1)]
skus = [f"SKU{idx:05d}" for idx in range(1, n_skus + 1)]

# Starting stock
starting_rows = []
for s in stores:
    for sku in skus:
        starting_rows.append((s, sku, rng.randint(10, 80)))

starting_df = spark.createDataFrame(starting_rows, schema=["store_id", "sku", "starting_qty"])
stores_df = spark.createDataFrame([(s,) for s in stores], schema=["store_id"])
products_df = spark.createDataFrame([(sku,) for sku in skus], schema=["sku"])

stores_df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{seed_path}/stores.csv")
products_df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{seed_path}/products.csv")
starting_df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{seed_path}/starting_stock.csv")

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
    # Build one hour worth of events in memory and write as JSONL (append)
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
                    "event_time": current.replace(tzinfo=timezone.utc).isoformat(),
                    "event_date": current.strftime("%Y-%m-%d"),
                    "store_id": store_id,
                    "sku": sku,
                    "event_type": event_type,
                    "qty": qty,
                    "source": "pos" if event_type in ("sale", "shrink") else ("wms" if event_type == "restock" else "ecom"),
                    "channel": "instore" if event_type in ("sale", "restock", "shrink") else "online",
                }
            )

    part = f"{streaming_input_path}/event_date={current.strftime('%Y-%m-%d')}/hour={current.strftime('%H')}"
    tmp = f"{part}/events_{uuid.uuid4().hex}.jsonl"
    dbutils.fs.put(tmp, "\n".join(json.dumps(e) for e in events) + "\n", overwrite=True)

    if current >= next_snapshot:
        snap_time = current + timedelta(minutes=15)
        snap_rows = []
        for (store_id, sku), true_qty in stock.items():
            noise = int(round(true_qty * rng.uniform(-0.03, 0.03)))
            snap_rows.append(
                (
                    snap_time.strftime("%Y-%m-%d"),
                    snap_time.replace(tzinfo=timezone.utc).isoformat(),
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
                    T.StructField("snapshot_time", T.StringType(), False),
                    T.StructField("store_id", T.StringType(), False),
                    T.StructField("sku", T.StringType(), False),
                    T.StructField("on_floor_qty", T.IntegerType(), False),
                ]
            ),
        ).withColumn("snapshot_time", F.to_timestamp("snapshot_time"))

        snap_part = f"{batch_input_path}/snapshot_date={snap_time.strftime('%Y-%m-%d')}"
        snap_df.coalesce(1).write.mode("append").option("header", True).csv(snap_part)
        next_snapshot = current + snapshot_every

    current += timedelta(hours=1)

display(
    spark.createDataFrame(
        [
            ("streaming_input_path", streaming_input_path),
            ("batch_input_path", batch_input_path),
            ("seed_path", seed_path),
        ],
        ["key", "value"],
    )
)

