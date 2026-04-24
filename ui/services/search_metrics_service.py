"""
SLG Sentinel — 搜索指标服务

提供搜索量 CSV 的读取、归一化和查询。
拆分自 app_services.py。
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import pandas as pd

from ui.services.app_services import DATA_DIR, SEARCH_METRIC_COLUMNS, LEGACY_SEARCH_METRIC_COLUMNS


def _read_search_metrics_csv(csv_path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(csv_path)
    except Exception:
        pass

    rows = []
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            for raw in reader:
                if not raw:
                    continue
                if len(raw) == len(SEARCH_METRIC_COLUMNS):
                    rows.append(dict(zip(SEARCH_METRIC_COLUMNS, raw)))
                elif len(raw) == len(LEGACY_SEARCH_METRIC_COLUMNS):
                    rows.append(dict(zip(LEGACY_SEARCH_METRIC_COLUMNS, raw)))
                elif len(header) == len(raw):
                    rows.append(dict(zip(header, raw)))
    except Exception:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def load_latest_search_metrics(platform: str, limit: int = 12) -> pd.DataFrame:
    metrics_dir = DATA_DIR / "search_metrics" / platform
    if not metrics_dir.exists():
        return pd.DataFrame()

    files = sorted(metrics_dir.glob("*_search_metrics.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return pd.DataFrame()

    frames = []
    for csv_path in files[:3]:
        frame = _read_search_metrics_csv(csv_path)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    def normalize_total_value(value) -> int | None:
        try:
            if pd.isna(value) or value == "":
                return None
            return int(float(value))
        except Exception:
            return None

    if "total_results_display" not in df.columns and "total_results" in df.columns:
        df["total_results_display"] = df["total_results"].apply(
            lambda value: f">={normalized}" if (normalized := normalize_total_value(value)) is not None and normalized >= 1000 else ("" if normalize_total_value(value) is None else str(normalize_total_value(value)))
        )
    elif "total_results_display" in df.columns and "total_results" in df.columns:
        missing_display = df["total_results_display"].isna() | (df["total_results_display"].astype(str) == "")
        df.loc[missing_display, "total_results_display"] = df.loc[missing_display, "total_results"].apply(
            lambda value: f">={normalized}" if (normalized := normalize_total_value(value)) is not None and normalized >= 1000 else ("" if normalize_total_value(value) is None else str(normalize_total_value(value)))
        )
    if "is_capped" not in df.columns and "total_results" in df.columns:
        df["is_capped"] = df["total_results"].apply(lambda value: bool((normalized := normalize_total_value(value)) is not None and normalized >= 1000))
    elif "is_capped" in df.columns and "total_results" in df.columns:
        df["is_capped"] = df["is_capped"].astype("object")
        missing_capped = df["is_capped"].isna() | (df["is_capped"].astype(str) == "")
        df.loc[missing_capped, "is_capped"] = df.loc[missing_capped, "total_results"].apply(
            lambda value: bool((normalized := normalize_total_value(value)) is not None and normalized >= 1000)
        )
    for col in ("num_pages", "page_size"):
        if col not in df.columns:
            df[col] = ""
    if "created_at" in df.columns:
        df = df.sort_values("created_at", ascending=False)
    return df.head(limit)


def find_latest_search_metric(platform: str, keyword: str, started_at: datetime | None = None) -> dict:
    metrics_df = load_latest_search_metrics(platform, limit=300)
    if metrics_df.empty or "keyword" not in metrics_df.columns:
        return {}

    target = str(keyword).strip()
    filtered = metrics_df[metrics_df["keyword"].astype(str) == target].copy()
    if filtered.empty:
        return {}

    if started_at is not None and "created_at" in filtered.columns:
        created = pd.to_datetime(filtered["created_at"], errors="coerce")
        filtered = filtered[created >= pd.Timestamp(started_at)]
        if filtered.empty:
            return {}

    return filtered.iloc[0].fillna("").to_dict()
