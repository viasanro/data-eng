from __future__ import annotations

import argparse
import csv
import json
import os
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Store:
    store_id: str


@dataclass(frozen=True)
class Product:
    sku: str


EVENT_TYPES = ("sale", "restock", "shrink", "online_order", "store_pickup")


def _iso_day(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    _ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_csv(path: Path, fieldnames: List[str], rows: Iterable[dict]) -> None:
    _ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _seed_entities(n_stores: int, n_skus: int) -> Tuple[List[Store], List[Product]]:
    stores = [Store(store_id=f"S{idx:03d}") for idx in range(1, n_stores + 1)]
    products = [Product(sku=f"SKU{idx:05d}") for idx in range(1, n_skus + 1)]
    return stores, products


def _starting_stock(stores: List[Store], products: List[Product], *, rng: random.Random) -> Dict[Tuple[str, str], int]:
    stock: Dict[Tuple[str, str], int] = {}
    for s in stores:
        for p in products:
            stock[(s.store_id, p.sku)] = rng.randint(10, 80)
    return stock


def _event_qty(event_type: str, *, rng: random.Random) -> int:
    if event_type in ("sale", "store_pickup"):
        return rng.randint(1, 5)
    if event_type == "online_order":
        return rng.randint(1, 3)
    if event_type == "restock":
        return rng.randint(5, 25)
    if event_type == "shrink":
        return rng.randint(1, 2)
    return 1


def _event_sign(event_type: str) -> int:
    if event_type in ("restock",):
        return +1
    return -1


def generate_pos_events(
    *,
    stores: List[Store],
    products: List[Product],
    start_utc: datetime,
    end_utc: datetime,
    events_per_store_per_hour: int,
    rng: random.Random,
) -> Iterable[dict]:
    """
    Generates insert-oriented events as JSONL files (good for streaming ingestion).
    qty is always positive; downstream derives sign from event_type.
    """
    current = start_utc
    while current < end_utc:
        for store in stores:
            for _ in range(events_per_store_per_hour):
                prod = rng.choice(products)
                event_type = rng.choices(
                    population=list(EVENT_TYPES),
                    weights=[0.58, 0.17, 0.03, 0.12, 0.10],
                    k=1,
                )[0]
                qty = _event_qty(event_type, rng=rng)
                yield {
                    "event_id": str(uuid.uuid4()),
                    "event_time": current.replace(tzinfo=timezone.utc).isoformat(),
                    "event_date": _iso_day(current),
                    "store_id": store.store_id,
                    "sku": prod.sku,
                    "event_type": event_type,
                    "qty": qty,
                    "source": "pos" if event_type in ("sale", "shrink") else ("wms" if event_type == "restock" else "ecom"),
                    "channel": "instore" if event_type in ("sale", "restock", "shrink") else "online",
                }
        current += timedelta(hours=1)


def compute_floor_snapshot(
    *,
    asof_utc: datetime,
    stores: List[Store],
    products: List[Product],
    stock: Dict[Tuple[str, str], int],
    rng: random.Random,
    noise_pct: float,
) -> Iterable[dict]:
    """
    Generates a floor count snapshot (batch). We add small noise to mimic counting variance.
    """
    for s in stores:
        for p in products:
            true_qty = max(0, int(stock[(s.store_id, p.sku)]))
            noise = int(round(true_qty * rng.uniform(-noise_pct, noise_pct)))
            yield {
                "snapshot_date": _iso_day(asof_utc),
                "snapshot_time": asof_utc.replace(tzinfo=timezone.utc).isoformat(),
                "store_id": s.store_id,
                "sku": p.sku,
                "on_floor_qty": max(0, true_qty + noise),
            }


def apply_event_to_stock(stock: Dict[Tuple[str, str], int], event: dict) -> None:
    key = (event["store_id"], event["sku"])
    delta = _event_sign(event["event_type"]) * int(event["qty"])
    stock[key] = max(0, int(stock.get(key, 0)) + delta)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate synthetic POS streaming + batch snapshot inputs.")
    ap.add_argument("--out", required=True, help="Output base directory (local path).")
    ap.add_argument("--start", required=True, help="Start datetime UTC, e.g. 2026-01-01T00:00:00Z")
    ap.add_argument("--days", type=int, default=30, help="How many days to generate.")
    ap.add_argument("--stores", type=int, default=2, help="Number of stores.")
    ap.add_argument("--skus", type=int, default=200, help="Number of SKUs.")
    ap.add_argument("--events-per-store-per-hour", type=int, default=30, help="Streaming intensity.")
    ap.add_argument("--snapshot-every-hours", type=int, default=24, help="Batch snapshot cadence.")
    ap.add_argument("--noise-pct", type=float, default=0.03, help="Snapshot noise fraction (0.03 = 3%).")
    ap.add_argument("--seed", type=int, default=7, help="Random seed.")
    args = ap.parse_args()

    out = Path(args.out)
    streaming_root = out / "input" / "stream_pos_events"
    batch_root = out / "input" / "batch_floor_snapshots"
    seed_root = out / "input" / "seeds"

    rng = random.Random(args.seed)
    stores, products = _seed_entities(args.stores, args.skus)
    stock = _starting_stock(stores, products, rng=rng)

    _ensure_dir(streaming_root)
    _ensure_dir(batch_root)
    _ensure_dir(seed_root)

    # Persist seeds (used by notebooks for dimensions / validation).
    _write_csv(
        seed_root / "stores.csv",
        ["store_id"],
        ({"store_id": s.store_id} for s in stores),
    )
    _write_csv(
        seed_root / "products.csv",
        ["sku"],
        ({"sku": p.sku} for p in products),
    )
    _write_csv(
        seed_root / "starting_stock.csv",
        ["store_id", "sku", "starting_qty"],
        (
            {"store_id": sid, "sku": sku, "starting_qty": qty}
            for (sid, sku), qty in stock.items()
        ),
    )

    # Generate a month of events and periodic snapshots.
    start_utc = datetime.fromisoformat(args.start.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = start_utc + timedelta(days=args.days)

    # Emit events grouped hourly into partitioned folders (good for Auto Loader).
    current = start_utc
    next_snapshot = start_utc
    snapshot_every = timedelta(hours=args.snapshot_every_hours)

    while current < end_utc:
        hour_end = current + timedelta(hours=1)
        events: List[dict] = []
        for e in generate_pos_events(
            stores=stores,
            products=products,
            start_utc=current,
            end_utc=hour_end,
            events_per_store_per_hour=args.events_per_store_per_hour,
            rng=rng,
        ):
            apply_event_to_stock(stock, e)
            events.append(e)

        part = streaming_root / f"event_date={_iso_day(current)}" / f"hour={current.strftime('%H')}"
        _write_jsonl(part / f"events_{uuid.uuid4().hex}.jsonl", events)

        if current >= next_snapshot:
            snap_time = current + timedelta(minutes=15)
            snap_rows = list(
                compute_floor_snapshot(
                    asof_utc=snap_time,
                    stores=stores,
                    products=products,
                    stock=stock,
                    rng=rng,
                    noise_pct=args.noise_pct,
                )
            )
            snap_file = batch_root / f"snapshot_date={_iso_day(current)}" / f"floor_snapshot_{uuid.uuid4().hex}.csv"
            _write_csv(
                snap_file,
                ["snapshot_date", "snapshot_time", "store_id", "sku", "on_floor_qty"],
                snap_rows,
            )
            next_snapshot = current + snapshot_every

        current = hour_end

    # Small helper: write a "manifest" for convenience.
    manifest = {
        "generated_at_utc": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        "out": str(out),
        "streaming_input_path": str(streaming_root),
        "batch_input_path": str(batch_root),
        "seed_path": str(seed_root),
        "days": args.days,
        "stores": args.stores,
        "skus": args.skus,
        "events_per_store_per_hour": args.events_per_store_per_hour,
        "snapshot_every_hours": args.snapshot_every_hours,
    }
    _ensure_dir(out)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

