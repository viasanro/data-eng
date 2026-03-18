# Databricks notebook source
# Helper to make `import rtpa` work reliably in Databricks Repos.

import os
import sys
from pathlib import Path


def _find_repo_root() -> str:
    """
    Walk upwards from CWD to find a folder that contains the top-level `rtpa/`.
    """
    p = Path(os.getcwd()).resolve()
    for parent in [p, *p.parents]:
        if (parent / "rtpa").is_dir():
            return str(parent)
    return str(p)


repo_root = _find_repo_root()
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

print("Bootstrap repo_root:", repo_root)
print("sys.path[0]:", sys.path[0])

