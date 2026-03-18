from __future__ import annotations

from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


POS_EVENT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), False),
        StructField("event_time", TimestampType(), False),
        StructField("event_date", StringType(), False),
        StructField("store_id", StringType(), False),
        StructField("sku", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("qty", IntegerType(), False),
        StructField("source", StringType(), True),
        StructField("channel", StringType(), True),
    ]
)


FLOOR_SNAPSHOT_SCHEMA = StructType(
    [
        StructField("snapshot_date", StringType(), False),
        StructField("snapshot_time", TimestampType(), False),
        StructField("store_id", StringType(), False),
        StructField("sku", StringType(), False),
        StructField("on_floor_qty", IntegerType(), False),
    ]
)

