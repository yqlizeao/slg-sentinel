from __future__ import annotations
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st
from ui.components.atlas_shell import (
    atlas_empty,
    atlas_rows,
    render_atlas_drawer,
    render_atlas_list_editor,
    render_atlas_panel,
    render_atlas_stage,
)
from ui.components.common import render_atlas_ops_board, render_empty_state, render_page_header, render_data_freshness, icon
from ui.i18n import t
from ui.services.app_services import load_report_artifacts, run_cli
from ui.services.overview_service import get_weekly_insights


def _render_insights_summary(insights: list[dict]) -> None:
    if not insights: return
    st.markdown(f"<h3>{t('report.insights')}</h3>", unsafe_allow_html=True)
    cols = st.columns(min(len(insights), 4))
    accent_colors = ["#d4af37", "#E85D4A", "#6B8BDB", "#5B9A6E", "#9B7FD4", "#D4956B"]
    sentiment_map = {"positive": ("trend", "#5B9A6E"), "negative": ("alert", "#E85D4A"), "mixed": ("search", "#6B8BDB")}
    for idx, item in enumerate(insights[:4]):
        with cols[idx]:
            topic = item.get("topic", "")
            sentiment = item.get("sentiment", "mixed")
            demand = item.get("core_demand", "")
            count = item.get("count", 0)
            color = accent_colors[idx % len(accent_colors)]
            icon_name, icon_color = sentiment_map.get(sentiment, ("search", "#6B8BDB"))
            svg = icon(icon_name, color=icon_color)
            st.markdown(f"""<div style='background:rgba(12,15,20,0.92); border:1px solid rgba(180,160,120,0.15); border-top:2px solid {color}; border-radius:8px; padding:20px; box-shadow:0 4px 24px rgba(0,0,0,0.25); min-height:130px;'>
                <div style='font-size:10px; color:rgba(232,228,220,0.35); text-transform:uppercase; letter-spacing:0.8px;'>
                    {svg} {sentiment} · {count} {t('report.count_suffix')}</div>
                <div style='font-family:Cinzel,serif; font-size:14px; font-weight:600; color:#E8E4DC;
                            margin:10px 0 8px; letter-spacing:0.5px;'>{topic}</div>
                <div style='font-size:11px; color:rgba(232,228,220,0.45); line-height:1.6;'>{demand}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_report_page() -> None:
    custom_date = st.session_state.get("report_date", datetime.now())
    generate_btn = False
    cmd_cols = st.columns([1.15, 1.0, 1.0, 6.0], gap="small")
    with cmd_cols[0]:
        with st.popover(t('popover.generate'), use_container_width=True):
            custom_date = st.date_input(t("report.date_label"), value=custom_date, key="report_date")
            st.caption(t("report.type_weekly"))
            generate_btn = st.button(t("report.generate"), type="primary", use_container_width=True)
    date_str = custom_date.strftime("%Y-%m-%d")
    if generate_btn:
        with st.spinner(t("report.generating")):
            _, stderr, code = run_cli(["analyze", "--type", "weekly", "--date", date_str])
        if code == 0:
            st.success(t("report.generated"))
            st.rerun()
        else:
            st.error(t("report.failed"))
            with st.expander(t("report.logs")):
                st.code(stderr, language="bash")

    artifacts = load_report_artifacts(date_str)
    payload = artifacts["payload"] if artifacts else {}
    insights = payload.get("insights", []) if artifacts else get_weekly_insights(date_str)
    sent_data = payload.get("sentiment", {}) if artifacts else {}
    mentions_data = payload.get("mentions", {}) if artifacts else {}
    markdown_body = artifacts.get("markdown", "") if artifacts else ""

    with cmd_cols[1]:
        with st.popover(t('popover.brief'), use_container_width=True):
            if markdown_body:
                st.markdown(markdown_body)
            elif insights:
                _render_insights_summary(insights)
            else:
                st.caption(t("report.no_report_hint"))
    with cmd_cols[2]:
        with st.popover(t('popover.freshness'), use_container_width=True):
            render_data_freshness()

    insight_rows = [
        (
            str(item.get("topic", "Insight"))[:42],
            f"{item.get('sentiment', 'mixed')} · {item.get('count', 0)}",
        )
        for item in insights[:8]
    ]
    sentiment_rows = [(str(k), int(v)) for k, v in sent_data.items()]
    mention_rows = sorted([(str(k), int(v)) for k, v in mentions_data.items()], key=lambda item: item[1], reverse=True)[:10]
    if markdown_body:
        report_body = "<div class='atlas-shell-copy'>" + escape(markdown_body[:4200]).replace("\n", "<br>") + "</div>"
    else:
        report_body = atlas_empty(t("report.no_report_title"), t("report.no_report_desc"))

    scene_html = f"""
    <div class='atlas-scene-sigil'></div>
    <div class='atlas-scene-line' style='left:21%;top:49%;width:28%;transform:rotate(-12deg);'></div>
    <div class='atlas-scene-line' style='left:47%;top:46%;width:29%;transform:rotate(18deg);'></div>
    <div class='atlas-scene-line' style='left:43%;top:63%;width:22%;transform:rotate(-31deg);'></div>
    <span class='atlas-scene-node' style='left:20%;top:48%;background:#d4af37;'></span>
    <span class='atlas-scene-node' style='left:47%;top:45%;background:#9B7FD4;'></span>
    <span class='atlas-scene-node' style='left:75%;top:55%;background:#E85D4A;'></span>
    <span class='atlas-scene-node' style='left:63%;top:70%;background:#5B9A6E;'></span>
    <div class='atlas-stage-map'>
      <svg viewBox='0 0 1200 720' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>
        <path class='gridline' d='M120 0V720M260 0V720M400 0V720M540 0V720M680 0V720M820 0V720M960 0V720M1100 0V720M0 120H1200M0 260H1200M0 400H1200M0 540H1200'/>
        <text x='250' y='358' font-size='14'>{t('report.map.comments')}</text>
        <text x='550' y='338' font-size='14'>{t('report.map.insights')} {len(insights)}</text>
        <text x='808' y='426' font-size='14'>{t('report.map.brief')}</text>
      </svg>
    </div>
    """
    panels = [
        render_atlas_panel(
            t('report.panel.status'),
            atlas_rows([
                (t('report.panel.date'), date_str),
                (t('report.panel.artifact'), t('report.panel.ready') if artifacts else t('report.panel.missing')),
                (t('report.panel.output'), "Markdown"),
            ], compact=True),
            kicker=t('report.panel.status'),
        ),
        render_atlas_panel(
            t('report.panel.insights'),
            render_atlas_list_editor(t('report.insights'), insight_rows[:4], compact=True, empty_title=t("report.no_report_title"), empty_body=t("report.no_report_hint")),
            kicker=t('report.panel.insights'),
        ),
        render_atlas_panel(
            t('report.panel.sentiment'),
            render_atlas_list_editor(t('report.sentiment'), sentiment_rows, compact=True, empty_title=t("report.no_sentiment"), empty_body=t("report.no_report_hint")),
            kicker=t('report.panel.sentiment'),
        ),
    ]
    drawers = [
        render_atlas_drawer(t('report.drawer.brief'), report_body, badge=t('label.markdown') if markdown_body else t('label.empty')),
        render_atlas_drawer(t('report.drawer.insights'), render_atlas_list_editor(t('report.drawer.insight_cards'), insight_rows, compact=True), badge=str(len(insight_rows))),
        render_atlas_drawer(t('report.drawer.sentiment'), render_atlas_list_editor(t("report.sentiment"), sentiment_rows, compact=True), badge=str(sum(sent_data.values()) if sent_data else 0)),
        render_atlas_drawer(t('report.drawer.rivals'), render_atlas_list_editor(t("report.mentions"), mention_rows, compact=True), badge=str(len(mention_rows))),
    ]
    render_atlas_stage(
        page_id="report",
        title=t('report.stage.title'),
        subtitle=t("report.subtitle"),
        metrics=[
            (t('report.metric.date'), date_str),
            (t('report.metric.insights'), str(len(insights))),
            (t('report.metric.rivals'), str(len(mention_rows))),
            (t('report.metric.report'), t('label.ready') if artifacts else t('label.empty')),
        ],
        scene_html=scene_html,
        panels=panels,
        drawers=drawers,
        timeline_label=t('report.stage.timeline'),
        timeline_start=t('report.stage.start'),
        timeline_end=t('report.stage.end'),
        accent="#9B7FD4",
        mode_label=t('report.stage.mode'),
    )
