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
# MAGIC %python
# MAGIC # Make rtpa importable for *all* notebooks on this cluster by writing a .pth file
# MAGIC # that points to the repo's src/ directory.
# MAGIC import os
# MAGIC import site
# MAGIC from pathlib import Path
# MAGIC 
# MAGIC repo_root = repo_root  # from previous cell
# MAGIC src_path = str(Path(repo_root) / "src")
# MAGIC 
# MAGIC # Pick the first site-packages path (Databricks typically has exactly one writable path here)
# MAGIC sp = site.getsitepackages()[0]
# MAGIC pth_file = Path(sp) / "rtpa_src.pth"
# MAGIC 
# MAGIC pth_file.write_text(src_path + "\n", encoding="utf-8")
# MAGIC print("Wrote:", str(pth_file))
# MAGIC print("Contents:", pth_file.read_text(encoding="utf-8").strip())

# COMMAND ----------
# MAGIC %restart_python

# COMMAND ----------
# MAGIC %python
# MAGIC import importlib
# MAGIC import os
# MAGIC import sys
# MAGIC from pathlib import Path
# MAGIC 
# MAGIC # Recompute repo_root after restart (state is lost)
# MAGIC def _guess_repo_root() -> str:
# MAGIC     candidates = [Path(os.getcwd()).resolve()]
# MAGIC     for start in candidates:
# MAGIC         p = start if start.is_dir() else start.parent
# MAGIC         for parent in [p, *p.parents]:
# MAGIC             if (parent / "pyproject.toml").exists():
# MAGIC                 return str(parent)
# MAGIC     return "."
# MAGIC 
# MAGIC repo_root = _guess_repo_root()
# MAGIC src_path = str(Path(repo_root) / "src")
# MAGIC # `rtpa_src.pth` should have added src_path to sys.path already, but keep a safe fallback.
# MAGIC if src_path not in sys.path:
# MAGIC     sys.path.insert(0, src_path)
# MAGIC 
# MAGIC print("Repo root (post-restart):", repo_root)
# MAGIC print("Added to sys.path:", src_path)
# MAGIC print("sys.path[0:5]:", sys.path[:5])
# MAGIC 
# MAGIC m = importlib.import_module("rtpa")
# MAGIC print("rtpa import OK from:", getattr(m, "__file__", "<unknown>"))