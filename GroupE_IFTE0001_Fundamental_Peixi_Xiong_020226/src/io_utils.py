from __future__ import annotations
from pathlib import Path
import pandas as pd

def write_excel(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=True)

def write_kv_excel(d: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([d])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
