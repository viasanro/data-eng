# Databricks notebook source
# MAGIC %md
# MAGIC ### Setup / install (Databricks Repos)
# MAGIC This notebook installs the project so `import rtpa` works from the other notebooks.

# COMMAND ----------
# MAGIC %python
# MAGIC import os, sys
# MAGIC from pathlib import Path
# MAGIC 
# MAGIC def _guess_repo_root() -> str:
# MAGIC     """
# MAGIC     Try to locate the repo root folder containing `pyproject.toml`.
# MAGIC     Works when this notebook is executed from within the repo.
# MAGIC     """
# MAGIC     # Databricks sets the current working directory inconsistently depending on how notebooks are run.
# MAGIC     # We search upwards from this file's path when possible.
# MAGIC     # `os.getcwd()` is a good fallback when the repo is attached as the working directory.
# MAGIC     candidates = []
# MAGIC     try:
# MAGIC         # When running as a notebook, __file__ is usually not set; keep guarded.
# MAGIC         candidates.append(Path(__file__).resolve())
# MAGIC     except Exception:
# MAGIC         pass
# MAGIC     candidates.append(Path(os.getcwd()).resolve())
# MAGIC 
# MAGIC     for start in candidates:
# MAGIC         p = start if start.is_dir() else start.parent
# MAGIC         for parent in [p, *p.parents]:
# MAGIC             if (parent / "pyproject.toml").exists():
# MAGIC                 return str(parent)
# MAGIC     return "."
# MAGIC 
# MAGIC repo_root = _guess_repo_root()
# MAGIC print("Repo root:", repo_root)
# MAGIC print("Python:", sys.version)

# COMMAND ----------
# MAGIC %pip install -e "$repo_root"

# COMMAND ----------
# MAGIC %restart_python

# COMMAND ----------
# MAGIC %python
# MAGIC import importlib
# MAGIC 
# MAGIC m = importlib.import_module("rtpa")
# MAGIC print("rtpa import OK from:", getattr(m, "__file__", "<unknown>"))