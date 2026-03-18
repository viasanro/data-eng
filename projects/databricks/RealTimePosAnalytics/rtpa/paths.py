from __future__ import annotations

from dataclasses import dataclass

from .config import RtpaConfig


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

