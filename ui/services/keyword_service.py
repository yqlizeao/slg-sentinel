"""
SLG Sentinel — 关键词库服务

提供关键词库的读取、归一化、保存。
拆分自 app_services.py。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from ui.services.app_services import KEYWORDS_FILE, format_file_mtime, load_yaml


def get_keyword_library_last_saved_at() -> str:
    return format_file_mtime(KEYWORDS_FILE)


def load_keyword_library() -> tuple[dict, list[str], dict]:
    kw_data = load_yaml(KEYWORDS_FILE)
    seed_keywords = kw_data.setdefault("seed_keywords", {})
    expansion = kw_data.setdefault(
        "expansion",
        {"enabled": True, "llm_provider": "deepseek", "max_expanded_keywords": 50},
    )

    merged_keywords = []
    seen = set()
    for group_name in ("games", "categories"):
        for raw_keyword in seed_keywords.get(group_name, []) or []:
            keyword = str(raw_keyword).strip()
            if keyword and keyword not in seen:
                merged_keywords.append(keyword)
                seen.add(keyword)

    return kw_data, merged_keywords, expansion


def normalize_keyword_rows(editor_df: pd.DataFrame, column_name: str = "关键词") -> list[str]:
    if column_name not in editor_df.columns:
        return []

    normalized = []
    seen = set()
    for _, row in editor_df.dropna(how="all").iterrows():
        keyword = str(row.get(column_name, "")).strip()
        if keyword and keyword not in seen:
            normalized.append(keyword)
            seen.add(keyword)
    return normalized


def save_keyword_library(kw_data: dict, keywords: list[str], enabled: bool, provider: str, max_keywords: int) -> None:
    kw_data["seed_keywords"] = {"games": keywords, "categories": []}
    kw_data["expansion"] = {
        "enabled": enabled,
        "llm_provider": provider,
        "max_expanded_keywords": int(max_keywords),
    }

    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(kw_data, f, allow_unicode=True, sort_keys=False)
