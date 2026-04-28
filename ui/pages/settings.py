from __future__ import annotations
import pandas as pd
import streamlit as st
from src.core.config import load_secrets
from ui.components.atlas_shell import (
    atlas_native_slot,
    atlas_rows,
    render_atlas_bar_rows,
    render_atlas_command_modal,
    render_atlas_command_nav,
    render_atlas_drawer,
    render_atlas_list_editor,
    render_atlas_metric_tiles,
    render_atlas_modal_footer,
    render_atlas_panel,
    render_atlas_stage,
)
from ui.components.common import render_atlas_ops_board, render_page_header, icon
from ui.i18n import t
from ui.services.app_services import load_targets_config, save_secrets_config, save_targets_config


def render_settings_page() -> None:
    targets_data = load_targets_config()
    target_values = targets_data["targets"]
    target_count = (
        len(target_values.get("bilibili_channels", []))
        + len(target_values.get("youtube_channels", []))
        + len(target_values.get("taptap_games", []))
    )
    sec_data = load_secrets()
    llm = sec_data.get("llm_keys", {})
    bili = sec_data.get("bilibili", {})
    mc = sec_data.get("mediacrawler", {})
    target_rows = [
        ("Bilibili", len(target_values.get("bilibili_channels", []))),
        ("YouTube", len(target_values.get("youtube_channels", []))),
        ("TapTap", len(target_values.get("taptap_games", []))),
    ]
    secret_rows = [
        ("DeepSeek", t('label.ready') if llm.get("deepseek") else t('label.empty')),
        ("OpenAI", t('label.ready') if llm.get("openai") else t('label.empty')),
        ("Qwen", t('label.ready') if llm.get("qwen") else t('label.empty')),
        ("Bilibili Session", t('label.ready') if bili.get("sessdata") else t('label.empty')),
        ("MediaCrawler", t('label.ready') if mc.get("session") else t('label.empty')),
    ]
    ready_secret_count = sum(1 for _, state in secret_rows if state == t("label.ready"))

    active_panel = render_atlas_command_nav(
        "settings",
        [
            ("targets", t("popover.targets")),
            ("secrets", t("popover.secrets")),
            ("persist", t("settings.drawer.persist")),
        ],
    )

    if active_panel == "targets":

        def _targets_body() -> None:
            max_target = max([value for _, value in target_rows] or [1])
            st.markdown(
                render_atlas_bar_rows(
                    [(label, value, value / max(max_target, 1) * 100) for label, value in target_rows],
                    title=t("settings.drawer.targets_title"),
                    tone="gold",
                ),
                unsafe_allow_html=True,
            )
            with atlas_native_slot(t("settings.drawer.targets"), t("settings.targets_help")):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"<div class='atlas-panel-title'>{t('settings.bilibili_channels')}</div>", unsafe_allow_html=True)
                    bili_df = pd.DataFrame(target_values.get("bilibili_channels", []))
                    if bili_df.empty:
                        bili_df = pd.DataFrame(columns=["name", "uid"])
                    edit_bili = st.data_editor(bili_df, num_rows="dynamic", use_container_width=True, key="ed_bili", hide_index=True)
                with c2:
                    st.markdown(f"<div class='atlas-panel-title'>{t('settings.youtube_channels')}</div>", unsafe_allow_html=True)
                    yt_df = pd.DataFrame(target_values.get("youtube_channels", []))
                    if yt_df.empty:
                        yt_df = pd.DataFrame(columns=["name", "channel_id"])
                    edit_yt = st.data_editor(yt_df, num_rows="dynamic", use_container_width=True, key="ed_yt", hide_index=True)
                with c3:
                    st.markdown(f"<div class='atlas-panel-title'>{t('settings.taptap_games')}</div>", unsafe_allow_html=True)
                    tap_df = pd.DataFrame(target_values.get("taptap_games", []))
                    if tap_df.empty:
                        tap_df = pd.DataFrame(columns=["name", "app_id"])
                    edit_tap = st.data_editor(tap_df, num_rows="dynamic", use_container_width=True, key="ed_tap", hide_index=True)
                if st.button(t("settings.save_targets"), type="primary", use_container_width=True):
                    target_values["bilibili_channels"] = edit_bili.dropna(how="all").to_dict("records")
                    target_values["youtube_channels"] = edit_yt.dropna(how="all").to_dict("records")
                    target_values["taptap_games"] = edit_tap.dropna(how="all").to_dict("records")
                    try:
                        save_targets_config({"targets": target_values})
                        st.success(t("settings.targets_saved"))
                    except Exception as exc:
                        st.error(t("settings.save_failed", error=exc))
            st.markdown(render_atlas_modal_footer(t("settings.drawer.format")), unsafe_allow_html=True)

        render_atlas_command_modal(
            page_id="settings",
            title=t("settings.drawer.targets"),
            subtitle=t("settings.targets_help"),
            metrics=[
                (t("settings.metric.targets"), target_count),
                (t("settings.bilibili_channels"), target_rows[0][1]),
                (t("settings.youtube_channels"), target_rows[1][1]),
                (t("settings.taptap_games"), target_rows[2][1]),
            ],
            filters=[
                (t("settings.bilibili_channels"), target_rows[0][1]),
                (t("settings.youtube_channels"), target_rows[1][1]),
                (t("settings.taptap_games"), target_rows[2][1]),
            ],
            body=_targets_body,
            icon="T",
        )

    elif active_panel == "secrets":

        def _secrets_body() -> None:
            st.markdown(
                render_atlas_list_editor(
                    t("settings.drawer.secrets_title"),
                    secret_rows,
                    compact=True,
                ),
                unsafe_allow_html=True,
            )
            with atlas_native_slot(t("settings.drawer.secrets"), t("settings.secrets_help")):
                ds_key = st.text_input("DeepSeek API Key", value=llm.get("deepseek", ""), type="password", placeholder="sk-...")
                oa_key = st.text_input("OpenAI API Key", value=llm.get("openai", ""), type="password", placeholder="sk-...")
                qw_key = st.text_input("Qwen API Key", value=llm.get("qwen", ""), type="password", placeholder="sk-...")
                st.divider()
                st.caption(t("settings.platform_session_desc"))
                sess_bili = st.text_input("Bilibili SESSDATA", value=bili.get("sessdata", ""), type="password", placeholder=t("settings.bili_placeholder"))
                sess_mc = st.text_area("MediaCrawler Session/Cookie", value=mc.get("session", ""), height=100, placeholder=t("settings.cookie_placeholder"))
                if st.button(t("settings.save_secrets"), type="primary", use_container_width=True):
                    new_sec = {
                        "llm_keys": {"deepseek": ds_key, "openai": oa_key, "qwen": qw_key},
                        "bilibili": {"sessdata": sess_bili},
                        "mediacrawler": {"session": sess_mc},
                    }
                    try:
                        save_secrets_config(new_sec)
                        st.success(t("settings.secrets_saved"))
                    except Exception as exc:
                        st.error(t("settings.secrets_failed", error=exc))
            st.markdown(render_atlas_modal_footer(t("settings.platform_session_desc")), unsafe_allow_html=True)

        render_atlas_command_modal(
            page_id="settings",
            title=t("settings.drawer.secrets"),
            subtitle=t("settings.secrets_help"),
            metrics=[
                (t("settings.metric.secrets"), ready_secret_count),
                (t("settings.metric.files"), "secrets.yaml"),
                (t("settings.metric.mode"), t("label.local")),
            ],
            filters=[
                (t("settings.metric.files"), "secrets.yaml"),
                (t("settings.metric.mode"), t("label.local")),
                (t("settings.metric.secrets"), ready_secret_count),
            ],
            body=_secrets_body,
            icon="S",
            metric_columns=3,
        )

    elif active_panel == "persist":

        def _persist_body() -> None:
            st.markdown(
                render_atlas_list_editor(
                    t("settings.drawer.persist"),
                    [
                        (t("settings.panel.targets_title"), "targets.yaml"),
                        (t("settings.panel.secrets"), "secrets.yaml"),
                        (t("label.format"), t("settings.drawer.format")),
                    ],
                    compact=True,
                ),
                unsafe_allow_html=True,
            )
            st.markdown(render_atlas_modal_footer(t("settings.drawer.format")), unsafe_allow_html=True)

        render_atlas_command_modal(
            page_id="settings",
            title=t("settings.drawer.persist"),
            subtitle=t("settings.drawer.format"),
            filters=[
                (t("settings.panel.targets_title"), "targets.yaml"),
                (t("settings.panel.secrets"), "secrets.yaml"),
                (t("label.format"), t("label.yaml")),
            ],
            body=_persist_body,
            icon="P",
        )
    scene_html = f"""
    <div class='atlas-scene-sigil'></div>
    <div class='atlas-scene-line' style='left:26%;top:42%;width:22%;transform:rotate(18deg);'></div>
    <div class='atlas-scene-line' style='left:49%;top:50%;width:25%;transform:rotate(-17deg);'></div>
    <div class='atlas-scene-line' style='left:36%;top:67%;width:32%;transform:rotate(-4deg);'></div>
    <span class='atlas-scene-node' style='left:25%;top:41%;background:#d4af37;'></span>
    <span class='atlas-scene-node' style='left:48%;top:49%;background:#5B9A6E;'></span>
    <span class='atlas-scene-node' style='left:73%;top:42%;background:#9B7FD4;'></span>
    <span class='atlas-scene-node' style='left:68%;top:66%;background:#6B8BDB;'></span>
    <div class='atlas-stage-map'>
      <svg viewBox='0 0 1200 720' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>
        <path class='gridline' d='M120 0V720M260 0V720M400 0V720M540 0V720M680 0V720M820 0V720M960 0V720M1100 0V720M0 120H1200M0 260H1200M0 400H1200M0 540H1200'/>
        <text x='280' y='330' font-size='14'>{t('settings.map.targets')} {target_count}</text>
        <text x='575' y='392' font-size='14'>{t('label.yaml')}</text>
        <text x='785' y='330' font-size='14'>{t('settings.map.secrets')}</text>
      </svg>
    </div>
    """
    panels = [
        render_atlas_panel(t('settings.panel.targets'), render_atlas_list_editor(t('settings.panel.targets_title'), target_rows, compact=True), kicker=t('label.yaml')),
        render_atlas_panel(t('settings.panel.secrets'), render_atlas_list_editor(t('settings.panel.secrets_title'), secret_rows[:3], compact=True), kicker=t('label.safe')),
        render_atlas_panel(t('settings.panel.session'), render_atlas_list_editor(t('settings.panel.sessions'), secret_rows[3:], compact=True), kicker=t('settings.panel.session')),
    ]
    drawers = [
        render_atlas_drawer(t('settings.drawer.targets'), render_atlas_list_editor(t('settings.drawer.targets_title'), target_rows, compact=True), badge=str(target_count)),
        render_atlas_drawer(t('settings.drawer.secrets'), render_atlas_list_editor(t('settings.drawer.secrets_title'), secret_rows, compact=True), badge=t('label.local')),
        render_atlas_drawer(t('settings.drawer.persist'), atlas_rows([(t('settings.panel.targets_title'), "targets.yaml"), (t('settings.panel.secrets'), "secrets.yaml"), (t('label.format'), t('settings.drawer.format'))], compact=True), badge=t('label.yaml')),
    ]
    render_atlas_stage(
        page_id="settings",
        title=t('settings.stage.title'),
        subtitle=t("settings.subtitle"),
        metrics=[
            (t('settings.metric.targets'), str(target_count)),
            (t('settings.metric.secrets'), t('label.local')),
            (t('settings.metric.files'), t('label.yaml')),
            (t('settings.metric.mode'), t('label.safe')),
        ],
        scene_html=scene_html,
        panels=panels,
        drawers=drawers,
        timeline_label=t('settings.stage.timeline'),
        timeline_start=t('settings.stage.start'),
        timeline_end=t('settings.stage.end'),
        accent="#D4956B",
        mode_label=t('settings.stage.mode'),
    )
