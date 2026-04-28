from __future__ import annotations
from html import escape

import streamlit as st

import pandas as pd

from ui.components.atlas_shell import (
    atlas_native_slot,
    atlas_empty,
    atlas_rows,
    render_atlas_command_modal,
    render_atlas_command_nav,
    render_atlas_bar_rows,
    render_atlas_drawer,
    render_atlas_list_editor,
    render_atlas_metric_tiles,
    render_atlas_modal_footer,
    render_atlas_panel,
    render_atlas_segment_bar,
    render_atlas_stage,
)
from ui.components.common import (
    icon,
    render_atlas_callout,
    render_atlas_ops_board,
    render_data_freshness,
    render_empty_state,
    render_kpi_card,
    render_page_header,
)
from ui.i18n import t
from ui.services.app_services import load_profiles_dataframe

def render_profile_page() -> None:
    df = load_profiles_dataframe()
    has_data = not df.empty
    if has_data:
        whales_dolphins = len(df[df["spend_type"].isin(["whale", "dolphin"])])
        refugees = len(df[df["tags"].str.contains("重氪难民|端游遗老", na=False)])
        hardcore = len(df[df["tags"].str.contains("硬核|策略|重度", na=False)])
        tag_counts: dict[str, int] = {}
        for tags_str in df["tags"].dropna():
            for tag in str(tags_str).split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        spend_rows = [(str(k), int(v)) for k, v in df["spend_type"].value_counts().head(6).items()]
        tag_rows = sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        player_rows = [
            (
                str(row.get("username", t('profile.unknown'))),
                f"{row.get('platform', '')} · {row.get('spend_type', '')}",
            )
            for _, row in df.head(12).iterrows()
        ]
    else:
        whales_dolphins = refugees = hardcore = 0
        spend_rows = []
        tag_rows = []
        player_rows = []

    active_panel = render_atlas_command_nav(
        "profile",
        [
            ("players", t("popover.raw_players")),
            ("segments", t("popover.segments")),
            ("freshness", t("popover.freshness")),
        ],
    )

    if active_panel == "players":

        def _players_body() -> None:
            with atlas_native_slot(t("profile.drawer.players"), t("profile.subtitle")):
                if has_data:
                    st.dataframe(
                        df[["platform", "username", "age_group", "spend_type", "tags", "location"]].rename(columns={
                            "platform": t('profile.col.platform'),
                            "username": t('profile.col.player'),
                            "age_group": t('profile.col.age'),
                            "spend_type": t('profile.col.spend'),
                            "tags": t('profile.col.tags'),
                            "location": t('profile.col.location'),
                        }),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.caption(t("profile.empty_hint"))
            st.markdown(render_atlas_modal_footer(t("profile.empty_hint")), unsafe_allow_html=True)

        render_atlas_command_modal(
            page_id="profile",
            title=t("profile.drawer.players"),
            subtitle=t("profile.subtitle"),
            metrics=[
                (t("profile.kpi.players"), len(df)),
                (t("profile.kpi.high_pay"), whales_dolphins),
                (t("profile.kpi.conversion"), refugees),
                (t("profile.kpi.hardcore"), hardcore),
            ],
            filters=[
                (t("profile.kpi.players"), len(df)),
                (t("profile.kpi.high_pay"), whales_dolphins),
                (t("profile.kpi.hardcore"), hardcore),
            ],
            body=_players_body,
            icon="P",
        )

    elif active_panel == "segments":

        def _segments_body() -> None:
            total_spend = max(sum(value for _, value in spend_rows), 1)
            if spend_rows:
                palette = ["#5B9A6E", "#d4af37", "#6B8BDB", "#E85D4A", "#9B7FD4", "#D4956B"]
                st.markdown(
                    render_atlas_segment_bar(
                        [
                            (label, value / total_spend * 100, palette[index % len(palette)])
                            for index, (label, value) in enumerate(spend_rows[:6])
                        ],
                        title=t("profile.drawer.spend_title"),
                    ),
                    unsafe_allow_html=True,
                )
            top_tag_value = max([value for _, value in tag_rows[:8]] or [1])
            st.markdown(
                render_atlas_bar_rows(
                    [
                        (label, value, value / top_tag_value * 100)
                        for label, value in tag_rows[:8]
                    ],
                    title=t("profile.drawer.tags_title"),
                    tone="green",
                ),
                unsafe_allow_html=True,
            )
            st.markdown(render_atlas_list_editor(t('profile.drawer.spend_title'), spend_rows, compact=True), unsafe_allow_html=True)
            st.markdown(render_atlas_list_editor(t('profile.drawer.tags_title'), tag_rows, compact=True), unsafe_allow_html=True)
            st.markdown(render_atlas_modal_footer(t("profile.focus_desc")), unsafe_allow_html=True)

        render_atlas_command_modal(
            page_id="profile",
            title=t("profile.drawer.spend"),
            subtitle=t("profile.ops.subtitle"),
            metrics=[
                (t("profile.kpi.players"), len(df)),
                (t("profile.kpi.high_pay"), whales_dolphins),
                (t("profile.kpi.conversion"), refugees),
                (t("profile.kpi.hardcore"), hardcore),
            ],
            filters=[
                (t("profile.drawer.spend"), len(spend_rows)),
                (t("profile.drawer.tags"), len(tag_rows)),
                (t("profile.panel.priority"), len(player_rows)),
            ],
            body=_segments_body,
            icon="S",
        )

    elif active_panel == "freshness":

        def _freshness_body() -> None:
            render_data_freshness()

        render_atlas_command_modal(
            page_id="profile",
            title=t("common.freshness"),
            subtitle=t("profile.stage.mode"),
            filters=[
                (t("profile.metric.profiles"), len(df)),
                (t("profile.metric.high_pay"), whales_dolphins),
                (t("profile.metric.hardcore"), hardcore),
            ],
            body=_freshness_body,
            icon="F",
        )

    scene_html = f"""
    <div class='atlas-scene-sigil'></div>
    <div class='atlas-scene-line' style='left:25%;top:57%;width:24%;transform:rotate(-32deg);'></div>
    <div class='atlas-scene-line' style='left:50%;top:40%;width:22%;transform:rotate(22deg);'></div>
    <div class='atlas-scene-line' style='left:42%;top:68%;width:30%;transform:rotate(-8deg);'></div>
    <span class='atlas-scene-node' style='left:24%;top:56%;background:#d4af37;'></span>
    <span class='atlas-scene-node' style='left:49%;top:39%;background:#5B9A6E;'></span>
    <span class='atlas-scene-node' style='left:71%;top:48%;background:#E85D4A;'></span>
    <span class='atlas-scene-node' style='left:73%;top:66%;background:#6B8BDB;'></span>
    <div class='atlas-stage-map'>
      <svg viewBox='0 0 1200 720' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>
        <path class='gridline' d='M120 0V720M260 0V720M400 0V720M540 0V720M680 0V720M820 0V720M960 0V720M1100 0V720M0 120H1200M0 260H1200M0 400H1200M0 540H1200'/>
        <text x='265' y='428' font-size='14'>{t('profile.map.players')} {len(df)}</text>
        <text x='585' y='312' font-size='14'>{t('profile.map.high_pay')} {whales_dolphins}</text>
        <text x='820' y='392' font-size='14'>{t('profile.map.migration')} {refugees}</text>
      </svg>
    </div>
    """
    empty_profile = atlas_empty(t("profile.empty_title"), t("profile.empty_desc"))
    panels = [
        render_atlas_panel(
            t('profile.panel.scale'),
            atlas_rows([
                (t("profile.kpi.players"), len(df)),
                (t("profile.kpi.high_pay"), whales_dolphins),
                (t("profile.kpi.conversion"), refugees),
            ], compact=True) if has_data else empty_profile,
            kicker=t('profile.panel.scale'),
        ),
        render_atlas_panel(
            t('profile.panel.tags'),
            render_atlas_list_editor(t('profile.panel.top_tags'), tag_rows[:5], compact=True, empty_title=t("profile.empty_title"), empty_body=t("profile.empty_hint")),
            kicker=t('profile.panel.tags'),
        ),
        render_atlas_panel(
            t('profile.panel.priority'),
            render_atlas_list_editor(t('profile.panel.focus'), player_rows[:5], compact=True, empty_title=t("profile.empty_title"), empty_body=t("profile.empty_hint")),
            kicker=t('profile.panel.priority'),
        ),
    ]
    drawers = [
        render_atlas_drawer(t('profile.drawer.spend'), render_atlas_list_editor(t('profile.drawer.spend_title'), spend_rows, compact=True), badge=str(len(spend_rows))),
        render_atlas_drawer(t('profile.drawer.tags'), render_atlas_list_editor(t('profile.drawer.tags_title'), tag_rows, compact=True), badge=str(len(tag_rows))),
        render_atlas_drawer(t('profile.drawer.players'), render_atlas_list_editor(t('profile.drawer.players_title'), player_rows, compact=True), badge=str(len(df))),
    ]
    render_atlas_stage(
        page_id="profile",
        title=t('profile.stage.title'),
        subtitle=t("profile.subtitle"),
        metrics=[
            (t('profile.metric.profiles'), str(len(df))),
            (t('profile.metric.high_pay'), str(whales_dolphins)),
            (t('profile.metric.migration'), str(refugees)),
            (t('profile.metric.hardcore'), str(hardcore)),
        ],
        scene_html=scene_html,
        panels=panels,
        drawers=drawers,
        timeline_label=t('profile.stage.timeline'),
        timeline_start=t('profile.stage.start'),
        timeline_end=t('profile.stage.end'),
        accent="#6B8BDB",
        mode_label=t('profile.stage.mode'),
    )
