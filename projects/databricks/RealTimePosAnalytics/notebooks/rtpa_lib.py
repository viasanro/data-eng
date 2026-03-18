# Databricks notebook source
# Shared library code for Serverless-compatible runs.
#
# In Databricks Serverless (Free Edition), importing python packages from Repos/Workspace
# paths can be unreliable. `%run ./rtpa_lib` is the most portable way to share code across notebooks.

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


# ----------------------------
# Config
# ----------------------------


@dataclass(frozen=True)
class RtpaConfig:
    db_name_bronze: str
    db_name_silver: str
    db_name_gold: str
    base_path: str
    streaming_input_path: str
    batch_input_path: str
    checkpoint_base_path: str
    seed_path: str

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "RtpaConfig":
        return RtpaConfig(
            db_name_bronze=d["db_name_bronze"],
            db_name_silver=d["db_name_silver"],
            db_name_gold=d["db_name_gold"],
            base_path=d["base_path"],
            streaming_input_path=d["streaming_input_path"],
            batch_input_path=d["batch_input_path"],
            checkpoint_base_path=d["checkpoint_base_path"],
            seed_path=d.get("seed_path", f'{d["base_path"].rstrip("/")}/input/seeds'),
        )


def load_config_json(path: str, *, dbutils: Optional[Any] = None) -> RtpaConfig:
    if dbutils is not None and path.startswith("dbfs:/"):
        raw = dbutils.fs.head(path, 1024 * 1024)
        return RtpaConfig.from_dict(json.loads(raw))

    with open(path, "r", encoding="utf-8") as f:
        return RtpaConfig.from_dict(json.load(f))


# ----------------------------
# Paths
# ----------------------------


@dataclass(frozen=True)
class RtpaPaths:
    streaming_input_path: str
    batch_input_path: str
    seed_path: str
    bronze_events_path: str
    bronze_snapshots_path: str
    silver_movements_path: str
    gold_inventory_path: str
    checkpoint_stream_events: str
    checkpoint_gold_nrt: str


def build_paths(cfg: RtpaConfig) -> RtpaPaths:
    base = cfg.base_path.rstrip("/")
    checkpoints = cfg.checkpoint_base_path.rstrip("/")
    return RtpaPaths(
        streaming_input_path=cfg.streaming_input_path,
        batch_input_path=cfg.batch_input_path,
        seed_path=cfg.seed_path,
        bronze_events_path=f"{base}/delta/bronze/pos_events_stream",
        bronze_snapshots_path=f"{base}/delta/bronze/floor_snapshots_batch",
        silver_movements_path=f"{base}/delta/silver/inventory_movements",
        gold_inventory_path=f"{base}/delta/gold/inventory_nrt",
        checkpoint_stream_events=f"{checkpoints}/bronze_pos_events_stream",
        checkpoint_gold_nrt=f"{checkpoints}/gold_inventory_nrt",
    )


# ----------------------------
# Schemas
# ----------------------------


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

