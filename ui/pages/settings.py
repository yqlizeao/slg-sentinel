from __future__ import annotations

import pandas as pd
import streamlit as st

from src.core.config import load_secrets
from ui.services.app_services import load_targets_config, save_secrets_config, save_targets_config


def render_settings_page() -> None:
    st.info("关键词库已经移动到「采集」页面右侧，可在采集过程中直接维护。")

    targets_tab, secrets_tab = st.tabs(["追踪目标 (targets.yaml)", "运行环境变量"])
    with targets_tab:
        targets_data = load_targets_config()
        target_values = targets_data["targets"]

        st.info("在这里维护需要持续追踪的频道和游戏目标。保存后，系统会按最新配置执行后续采集。")
        st.markdown("<p style='font-size:13px; color:#666; margin-bottom:1.5rem;'>操作说明：在下方表格单元格双击可直接修改追踪目标。在末尾空白行输入即可新增，选中行首数字按 Delete 键可删除整行。编辑完成后请点击底部保存。</p>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### Bilibili 频道", unsafe_allow_html=True)
            bili_df = pd.DataFrame(target_values.get("bilibili_channels", []))
            if bili_df.empty:
                bili_df = pd.DataFrame(columns=["name", "uid"])
            edit_bili = st.data_editor(bili_df, num_rows="dynamic", use_container_width=True, key="ed_bili", hide_index=True)

        with c2:
            st.markdown("##### YouTube 频道", unsafe_allow_html=True)
            yt_df = pd.DataFrame(target_values.get("youtube_channels", []))
            if yt_df.empty:
                yt_df = pd.DataFrame(columns=["name", "channel_id"])
            edit_yt = st.data_editor(yt_df, num_rows="dynamic", use_container_width=True, key="ed_yt", hide_index=True)

        with c3:
            st.markdown("##### TapTap 游戏", unsafe_allow_html=True)
            tap_df = pd.DataFrame(target_values.get("taptap_games", []))
            if tap_df.empty:
                tap_df = pd.DataFrame(columns=["name", "app_id"])
            edit_tap = st.data_editor(tap_df, num_rows="dynamic", use_container_width=True, key="ed_tap", hide_index=True)

        if st.button("保存追踪目标", type="primary"):
            target_values["bilibili_channels"] = edit_bili.dropna(how="all").to_dict("records")
            target_values["youtube_channels"] = edit_yt.dropna(how="all").to_dict("records")
            target_values["taptap_games"] = edit_tap.dropna(how="all").to_dict("records")
            try:
                save_targets_config({"targets": target_values})
                st.success("追踪目标已保存，后续采集将按新配置执行。")
            except Exception as exc:
                st.error(f"保存失败：{exc}")

    with secrets_tab:
        st.info("在这里填写的敏感配置会保存到本地 `secrets.yaml`，优先于环境变量读取，也不会被提交到代码仓库。")
        sec_data = load_secrets()
        llm = sec_data.get("llm_keys", {})
        bili = sec_data.get("bilibili", {})
        mc = sec_data.get("mediacrawler", {})

        st.markdown("##### AI 大模型密钥")
        ds_key = st.text_input("DeepSeek API Key", value=llm.get("deepseek", ""), type="password", placeholder="sk-...")
        oa_key = st.text_input("OpenAI API Key", value=llm.get("openai", ""), type="password", placeholder="sk-...")
        qw_key = st.text_input("Qwen API Key (阿里云百炼)", value=llm.get("qwen", ""), type="password", placeholder="sk-...")

        st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:1.5rem 0;'/>", unsafe_allow_html=True)
        st.markdown("##### 平台会话身份 (Cookies / Sessions)")
        st.markdown("<p style='font-size:12px; color:#666;'>用于访问需要登录态的平台接口，一般需要从浏览器当前会话中提取。</p>", unsafe_allow_html=True)

        sess_bili = st.text_input("Bilibili SESSDATA", value=bili.get("sessdata", ""), type="password", placeholder="请输入 B站 SESSDATA...")
        sess_mc = st.text_area("MediaCrawler Session/Cookie", value=mc.get("session", ""), height=100, placeholder="预留的跨平台通用长 Cookie 载体字符串...")

        if st.button("保存密钥配置", type="primary"):
            new_sec = {
                "llm_keys": {"deepseek": ds_key, "openai": oa_key, "qwen": qw_key},
                "bilibili": {"sessdata": sess_bili},
                "mediacrawler": {"session": sess_mc},
            }
            try:
                save_secrets_config(new_sec)
                st.success("密钥配置已保存到本地，并立即生效。")
            except Exception as exc:
                st.error(f"保存发生异常：{exc}")
