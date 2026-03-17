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
        StructField("event_date", StringType(), False),  # yyyy-mm-dd (partition helper)
        StructField("store_id", StringType(), False),
        StructField("sku", StringType(), False),
        StructField(
            "event_type",
            StringType(),
            False,  # sale|restock|shrink|online_order|store_pickup
        ),
        StructField("qty", IntegerType(), False),  # always positive in source
        StructField("source", StringType(), True),  # pos|ecom|wms|cycle_count
        StructField("channel", StringType(), True),  # instore|online
    ]
)


FLOOR_SNAPSHOT_SCHEMA = StructType(
    [
        StructField("snapshot_date", StringType(), False),  # yyyy-mm-dd
        StructField("snapshot_time", TimestampType(), False),
        StructField("store_id", StringType(), False),
        StructField("sku", StringType(), False),
        StructField("on_floor_qty", IntegerType(), False),
    ]
)

