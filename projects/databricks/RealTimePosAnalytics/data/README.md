This folder is optional.

The project is designed to generate inputs into a storage path (e.g. DBFS / cloud object storage) and then ingest them into Delta tables using a lambda + medallion approach.

If you want to generate data locally into the repo for quick testing, run:

```bash
python scripts/generate_synthetic_inputs.py --out data --start 2026-01-01T00:00:00Z --days 30 --stores 2 --skus 200
```

Then you can copy `data/input/*` to your cloud storage / DBFS input paths.

