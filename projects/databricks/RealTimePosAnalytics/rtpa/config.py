from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


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
    """
    Loads config from a json file path. Works in Databricks with DBFS paths.
    Pass dbutils if the file lives on DBFS and you want to use dbutils.fs.head.
    """
    if dbutils is not None and path.startswith("dbfs:/"):
        raw = dbutils.fs.head(path, 1024 * 1024)
        return RtpaConfig.from_dict(json.loads(raw))

    with open(path, "r", encoding="utf-8") as f:
        return RtpaConfig.from_dict(json.load(f))

