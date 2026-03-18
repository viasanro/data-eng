# Databricks notebook source
# Gold layer:
# Build a near-real-time inventory table by combining:
# - Starting stock (seed) + streaming movements (Silver)
# - Latest available floor snapshot (Silver) as a periodic correction signal
#
# Result: an "as-of" inventory per store+SKU with both computed and snapped values.

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

# MAGIC %run ./rtpa_lib

dbutils.widgets.text("base_path", "dbfs:/tmp/rtpa", "Base path (for seeds)")
dbutils.widgets.text("db_name_silver", "rtpa_silver", "Silver schema/database")
dbutils.widgets.text("db_name_gold", "rtpa_gold", "Gold schema/database")

base_path = dbutils.widgets.get("base_path").strip().rstrip("/")
db_silver = dbutils.widgets.get("db_name_silver").strip()
db_gold = dbutils.widgets.get("db_name_gold").strip()

seed_path = f"{base_path}/input/seeds"

spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_gold}")

silver_movements_table = f"{db_silver}.inventory_movements"
silver_snapshots_table = f"{db_silver}.floor_snapshots"

gold_table = f"{db_gold}.inventory_nrt"

# COMMAND ----------

# Load starting stock (seed). Generator writes as a 1-part CSV dir; so load path recursively.
starting = (
    spark.read.format("csv")
    .option("header", True)
    .load(f"{seed_path}/starting_stock.csv")
    .select(
        F.col("store_id"),
        F.col("sku"),
        F.col("starting_qty").cast("int").alias("starting_qty"),
    )
)

movements = spark.table(silver_movements_table).select(
    "store_id",
    "sku",
    F.col("movement_time").cast("timestamp").alias("movement_time"),
    F.col("movement_qty").cast("int").alias("movement_qty"),
)

snapshots = spark.table(silver_snapshots_table).select(
    "store_id",
    "sku",
    F.col("snapshot_time").cast("timestamp").alias("snapshot_time"),
    F.col("on_floor_qty").cast("int").alias("on_floor_qty"),
)

# COMMAND ----------

# Compute movement-based inventory (append-friendly aggregation)
movement_agg = (
    movements.groupBy("store_id", "sku")
    .agg(
        F.sum("movement_qty").alias("net_movement_qty"),
        F.max("movement_time").alias("last_movement_time"),
    )
)

computed = (
    starting.join(movement_agg, on=["store_id", "sku"], how="left")
    .fillna({"net_movement_qty": 0})
    .withColumn("computed_qty", (F.col("starting_qty") + F.col("net_movement_qty")).cast("int"))
)

# COMMAND ----------

# Latest snapshot per store+sku
w = Window.partitionBy("store_id", "sku").orderBy(F.col("snapshot_time").desc())
latest_snapshot = (
    snapshots.withColumn("rn", F.row_number().over(w))
    .where(F.col("rn") == 1)
    .drop("rn")
    .withColumnRenamed("snapshot_time", "latest_snapshot_time")
    .withColumnRenamed("on_floor_qty", "latest_snapshot_qty")
)

# COMMAND ----------

# Combine into a Gold table. Snapshot is a periodic correction reference;
# consumers can choose snapshot_qty (if present) or computed_qty.
gold = (
    computed.join(latest_snapshot, on=["store_id", "sku"], how="left")
    .withColumn("as_of_time", F.greatest(F.col("last_movement_time"), F.col("latest_snapshot_time")))
    .withColumn(
        "best_qty",
        F.when(F.col("latest_snapshot_qty").isNotNull(), F.col("latest_snapshot_qty")).otherwise(F.col("computed_qty")),
    )
    .withColumn("_updated_at", F.current_timestamp())
)

(gold.write.format("delta").mode("overwrite").saveAsTable(gold_table))

display(spark.table(gold_table).orderBy(F.col("_updated_at").desc()).limit(20))

# COMMAND ----------

# Simple sanity checks / example queries
spark.sql(
    f"""
    SELECT
      store_id,
      count(*) AS sku_count,
      sum(best_qty) AS total_units_best,
      sum(computed_qty) AS total_units_computed,
      sum(latest_snapshot_qty) AS total_units_snapshot
    FROM {gold_table}
    GROUP BY store_id
    ORDER BY store_id
    """
).display()

