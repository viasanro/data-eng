# Databricks notebook source
# MAGIC %md
# MAGIC ### Setup / verificación (Serverless friendly)
# MAGIC En Databricks **Serverless** (Free Edition), los imports de paquetes Python desde Repos/Workspace
# MAGIC pueden fallar incluso si existen en el repo.
# MAGIC 
# MAGIC Para que esto funcione de forma portable, el proyecto usa:
# MAGIC - `notebooks/rtpa_lib.py` (código compartido)
# MAGIC - y los notebooks principales hacen: `%run ./rtpa_lib`
# MAGIC 
# MAGIC Este notebook solo verifica que `%run` funciona.

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
# MAGIC %python
# MAGIC # Optional quick verification (no installs)
# MAGIC import importlib
# MAGIC 
# MAGIC # Verify shared lib loads (same mechanism as pipeline notebooks)
# MAGIC # MAGIC %run ./notebooks/rtpa_lib
# MAGIC print("RtpaConfig available:", "RtpaConfig" in globals())