"""Shared War Atlas-style single viewport stage components."""
from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

from ui.i18n import t


Panel = dict[str, str]


def _safe(value: object) -> str:
    return escape(str(value), quote=True)


def render_atlas_stage(
    *,
    page_id: str,
    title: str,
    subtitle: str,
    metrics: Iterable[tuple[str, str]],
    scene_html: str,
    panels: Iterable[Panel] | None = None,
    drawers: Iterable[Panel] | None = None,
    timeline_label: str = "2026 AD",
    timeline_start: str = "SEED",
    timeline_end: str = "LIVE",
    accent: str = "#d4af37",
    mode_label: str = "COMMAND",
) -> None:
    """Render a self-contained, non-scrolling Atlas command stage.

    The body of each page becomes a fixed-height product surface. Overflow
    moves into internal drawers and panels, matching the War Atlas interaction
    model without changing service APIs.
    """
    metrics_html = "".join(
        f"<div class='atlas-shell-display-row'><span>{_safe(label)}</span><b>{_safe(value)}</b></div>"
        for label, value in list(metrics)[:6]
    )
    panel_html = "".join(
        f"""
        <article class='atlas-shell-panel {panel.get("tone", "")}'>
            <div class='atlas-shell-panel-kicker'>{_safe(panel.get("kicker", "INTEL"))}</div>
            <h3>{_safe(panel.get("title", ""))}</h3>
            <div class='atlas-shell-panel-body'>{panel.get("body", "")}</div>
        </article>
        """
        for panel in (panels or [])
    )
    drawer_html = "".join(
        f"""
        <details class='atlas-shell-drawer'>
            <summary>
                <span>{_safe(drawer.get("title", ""))}</span>
                <b>{_safe(drawer.get("badge", "OPEN"))}</b>
            </summary>
            <div class='atlas-shell-drawer-body'>{drawer.get("body", "")}</div>
        </details>
        """
        for drawer in (drawers or [])
    )
    scene_html = " ".join(str(scene_html).split())
    panel_html = " ".join(panel_html.split())
    drawer_html = " ".join(drawer_html.split())
    stage_html = (
        f"<div class='atlas-shell-stage atlas-shell-{_safe(page_id)}' style='--atlas-accent:{_safe(accent)};'>"
        f"<div class='atlas-shell-scene'>{scene_html}</div>"
        "<div class='atlas-shell-vignette'></div>"
        "<header class='atlas-shell-hero'>"
        f"<div class='atlas-shell-kicker'>SLG SENTINEL · {_safe(mode_label)}</div>"
        f"<h1>{_safe(title)}</h1>"
        "<div class='atlas-shell-title-line'></div>"
        f"<p>{_safe(subtitle)}</p>"
        "</header>"
        "<div class='atlas-shell-controls'>"
        f"<button type='button'>▣ {_safe(t('atlas.control.guided'))}</button>"
        f"<button type='button'>◷ {_safe(t('atlas.control.cycle'))}</button>"
        f"<button type='button'>⌖ {_safe(t('atlas.control.focus'))}</button>"
        f"<button type='button'>▥ {_safe(t('atlas.control.stats'))}</button>"
        "</div>"
        f"<aside class='atlas-shell-display'><div class='atlas-shell-display-title'>{_safe(t('stage.display'))}</div>{metrics_html}</aside>"
        f"<div class='atlas-shell-panels'>{panel_html}</div>"
        f"<div class='atlas-shell-drawers'>{drawer_html}</div>"
        "<footer class='atlas-shell-timeline'>"
        "<div class='atlas-shell-play'>▶</div>"
        "<div class='atlas-shell-era'>"
        f"<span>{_safe(mode_label)}</span>"
        f"<strong>{_safe(timeline_label)}</strong>"
        "</div>"
        "<div class='atlas-shell-range'>"
        f"<span>{_safe(timeline_start)}</span><div><i></i></div><span>{_safe(timeline_end)}</span>"
        "</div>"
        "</footer>"
        "</div>"
    )
    st.markdown(stage_html, unsafe_allow_html=True)


def render_atlas_drawer(title: str, body: str, *, badge: str = "OPEN") -> Panel:
    return {"title": title, "body": body, "badge": badge}


def render_atlas_panel(title: str, body: str, *, kicker: str = "INTEL", tone: str = "") -> Panel:
    return {"title": title, "body": body, "kicker": kicker, "tone": tone}


def render_atlas_list_editor(
    title: str,
    rows: Iterable[tuple[str, object]],
    *,
    caption: str = "",
    compact: bool = False,
    empty_title: str = "",
    empty_body: str = "",
) -> str:
    """Atlas-looking list surface for primary page summaries.

    Native Streamlit editors still perform persistence in command popovers; this
    helper gives the main stage the refined War Atlas list language instead of
    exposing Glide as the first visual surface.
    """
    row_list = list(rows)
    if not row_list:
        body = atlas_empty(empty_title or t('stage.no_data'), empty_body or t('stage.no_data_hint'))
    else:
        body = atlas_rows(row_list, compact=compact)
    caption_html = f"<p class='atlas-shell-list-caption'>{_safe(caption)}</p>" if caption else ""
    return (
        "<div class='atlas-shell-list-editor'>"
        f"<div class='atlas-shell-list-title'>{_safe(title)}</div>"
        f"{caption_html}"
        f"{body}"
        "</div>"
    )


def atlas_rows(rows: Iterable[tuple[str, object]], *, compact: bool = False) -> str:
    cls = " is-compact" if compact else ""
    return "".join(
        f"<div class='atlas-shell-list-row{cls}'><span>{_safe(label)}</span><b>{_safe(value)}</b></div>"
        for label, value in rows
    )


def atlas_chips(items: Iterable[str]) -> str:
    return "".join(f"<span class='atlas-shell-chip'>{_safe(item)}</span>" for item in items)


def atlas_empty(title: str, body: str) -> str:
    return (
        "<div class='atlas-shell-empty'>"
        f"<strong>{_safe(title)}</strong>"
        f"<span>{_safe(body)}</span>"
        "</div>"
    )
