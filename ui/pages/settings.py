from __future__ import annotations
import pandas as pd
import streamlit as st
from src.core.config import load_secrets
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
    render_page_header(
        t("settings.title"),
        t("settings.subtitle"),
        [("config", "local"), ("targets", "yaml"), ("secrets", "safe")],
    )
    render_atlas_ops_board(
        t("settings.ops.title"),
        t("settings.ops.subtitle"),
        [("Targets", str(target_count)), ("Secrets", "local"), ("Mode", "safe"), ("Files", "yaml")],
        t("settings.ops.eyebrow"),
    )

    targets_tab, secrets_tab = st.tabs([t("settings.targets_tab"), t("settings.secrets_tab")])
    with targets_tab:
        target_svg = icon("target", color="rgba(232,228,220,0.4)")
        st.markdown(f"<p style='font-size:12px; color:rgba(232,228,220,0.4); margin-bottom:1.2rem;'>{target_svg} {t('settings.targets_help')}</p>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<h5>{t('settings.bilibili_channels')}</h5>", unsafe_allow_html=True)
            bili_df = pd.DataFrame(target_values.get("bilibili_channels", []))
            if bili_df.empty: bili_df = pd.DataFrame(columns=["name", "uid"])
            edit_bili = st.data_editor(bili_df, num_rows="dynamic", use_container_width=True, key="ed_bili", hide_index=True)
        with c2:
            st.markdown(f"<h5>{t('settings.youtube_channels')}</h5>", unsafe_allow_html=True)
            yt_df = pd.DataFrame(target_values.get("youtube_channels", []))
            if yt_df.empty: yt_df = pd.DataFrame(columns=["name", "channel_id"])
            edit_yt = st.data_editor(yt_df, num_rows="dynamic", use_container_width=True, key="ed_yt", hide_index=True)
        with c3:
            st.markdown(f"<h5>{t('settings.taptap_games')}</h5>", unsafe_allow_html=True)
            tap_df = pd.DataFrame(target_values.get("taptap_games", []))
            if tap_df.empty: tap_df = pd.DataFrame(columns=["name", "app_id"])
            edit_tap = st.data_editor(tap_df, num_rows="dynamic", use_container_width=True, key="ed_tap", hide_index=True)

        if st.button(t("settings.save_targets"), type="primary"):
            target_values["bilibili_channels"] = edit_bili.dropna(how="all").to_dict("records")
            target_values["youtube_channels"] = edit_yt.dropna(how="all").to_dict("records")
            target_values["taptap_games"] = edit_tap.dropna(how="all").to_dict("records")
            try:
                save_targets_config({"targets": target_values})
                st.success(t("settings.targets_saved"))
            except Exception as exc:
                st.error(t("settings.save_failed", error=exc))

    with secrets_tab:
        shield_svg = icon("shield", color="rgba(232,228,220,0.4)")
        st.markdown(f"<p style='font-size:12px; color:rgba(232,228,220,0.4); margin-bottom:1rem;'>{shield_svg} {t('settings.secrets_help')}</p>", unsafe_allow_html=True)
        sec_data = load_secrets()
        llm = sec_data.get("llm_keys", {})
        bili = sec_data.get("bilibili", {})
        mc = sec_data.get("mediacrawler", {})

        st.markdown(f"<h5>{t('settings.llm_keys')}</h5>", unsafe_allow_html=True)
        ds_key = st.text_input("DeepSeek API Key", value=llm.get("deepseek", ""), type="password", placeholder="sk-...")
        oa_key = st.text_input("OpenAI API Key", value=llm.get("openai", ""), type="password", placeholder="sk-...")
        qw_key = st.text_input("Qwen API Key (阿里云百炼)", value=llm.get("qwen", ""), type="password", placeholder="sk-...")

        st.markdown("<hr style='border:none; border-top:1px solid rgba(180,160,120,0.08); margin:1.5rem 0;'/>", unsafe_allow_html=True)
        st.markdown(f"<h5>{t('settings.platform_session')}</h5>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:11px; color:rgba(232,228,220,0.3);'>{t('settings.platform_session_desc')}</p>", unsafe_allow_html=True)
        sess_bili = st.text_input("Bilibili SESSDATA", value=bili.get("sessdata", ""), type="password", placeholder=t("settings.bili_placeholder"))
        sess_mc = st.text_area("MediaCrawler Session/Cookie", value=mc.get("session", ""), height=100, placeholder=t("settings.cookie_placeholder"))

        if st.button(t("settings.save_secrets"), type="primary"):
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
