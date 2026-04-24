"""Small file-backed localization layer for the Streamlit UI."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import tomllib

import streamlit as st

DEFAULT_LOCALE = "en"
ZH_LOCALE = "zh_Hans"
SUPPORTED_LOCALES = (DEFAULT_LOCALE, ZH_LOCALE)
LOCALE_FILE = Path(__file__).with_name("locales.toml")

PAGE_ALIASES = {
    "总览": "overview",
    "采集": "crawl",
    "递归采集": "recursive",
    "画像": "profile",
    "智能报表": "report",
    "竞品对比": "competitor",
    "设置": "settings",
}


@lru_cache(maxsize=1)
def load_locales() -> dict[str, dict[str, str]]:
    with LOCALE_FILE.open("rb") as fh:
        return tomllib.load(fh)


def normalize_locale(value: str | None) -> str:
    if value in {"zh", "zh-CN", "zh_CN", ZH_LOCALE}:
        return ZH_LOCALE
    return DEFAULT_LOCALE


def current_locale() -> str:
    return normalize_locale(st.query_params.get("lang"))


def alternate_locale(locale: str | None = None) -> str:
    return ZH_LOCALE if normalize_locale(locale) == DEFAULT_LOCALE else DEFAULT_LOCALE


def t(key: str, **kwargs: object) -> str:
    locale = current_locale()
    bundles = load_locales()
    text = bundles.get(locale, {}).get(key) or bundles.get(DEFAULT_LOCALE, {}).get(key) or key
    return text.format(**kwargs) if kwargs else text


def page_id_from_query(value: str | None) -> str:
    if not value:
        return "overview"
    value = PAGE_ALIASES.get(value, value)
    return value if value in {"overview", "crawl", "recursive", "profile", "report", "competitor", "settings"} else "overview"
