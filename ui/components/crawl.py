from __future__ import annotations

import html as _html

import pandas as pd
import streamlit as st

from ui.services.app_services import (
    get_keyword_library_last_saved_at,
    load_keyword_library,
    normalize_keyword_rows,
    save_keyword_library,
)


def render_step_overview(items: list[tuple[str, str, str]]) -> None:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:12px; color:#475569; font-weight:700; letter-spacing:0.5px; margin-bottom:12px;'>采集流程</div>",
            unsafe_allow_html=True,
        )

        layout = [1.45 if idx % 2 == 0 else 0.22 for idx in range(len(items) * 2 - 1)]
        cols = st.columns(layout)

        col_idx = 0
        for item_idx, (step, title, color) in enumerate(items):
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div style='padding:10px 12px; border:1px solid {color}22; border-radius:10px; background:{color}10; min-height:76px;'>
                        <div style='font-size:11px; color:{color}; font-weight:800; letter-spacing:0.5px;'>{step}</div>
                        <div style='font-size:15px; color:#111; font-weight:700; margin-top:6px;'>{title}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            col_idx += 1
            if item_idx < len(items) - 1:
                with cols[col_idx]:
                    st.markdown(
                        "<div style='text-align:center; font-size:22px; color:#CBD5E1; font-weight:700; padding-top:22px;'>→</div>",
                        unsafe_allow_html=True,
                    )
                col_idx += 1


def render_step_block_header(step: str, title: str, color: str, description: str | None = None) -> None:
    desc_html = (
        f"<div style='font-size:12px; color:#666; margin-top:2px; line-height:1.5;'>{description}</div>"
        if description
        else ""
    )
    st.markdown(
        f"""
        <div style='display:flex; gap:12px; align-items:flex-start; margin-bottom:12px;'>
            <div style='width:38px; height:38px; border-radius:12px; background:{color}18; color:{color}; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:800; flex-shrink:0;'>
                {step}
            </div>
            <div>
                <div style='font-size:16px; font-weight:700; color:#111;'>{title}</div>
                {desc_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_crawl_result_card(result: dict) -> None:
    if not result:
        return

    status_text = "成功" if result["status"] == "success" else "失败"
    status_color = "#16A34A" if result["status"] == "success" else "#DC2626"

    st.markdown("##### 本次执行结果")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("执行状态", status_text, delta=f"{result['duration_seconds']:.1f} 秒")
    with metric_cols[1]:
        st.metric("预计检索量", str(result["estimated_results"]), delta=f"{result['keyword_count']} 词 × {result['limit_val']} 条")
    with metric_cols[2]:
        st.metric("新增视频 / 评论", f"{result['added_videos']} / {result['added_comments']}")
    with metric_cols[3]:
        st.metric("写入文件", str(len(result["touched_files"])))

    st.markdown(
        f"<div style='font-size:13px; color:#475569; margin:8px 0 12px 0;'>当前平台：<span style='color:{status_color}; font-weight:700;'>{_html.escape(result['platform_label'])}</span></div>",
        unsafe_allow_html=True,
    )

    if result["touched_files"]:
        st.markdown("**文件回执**")
        for item in result["touched_files"][:6]:
            delta_text = f"+{item['row_delta']}" if item["row_delta"] >= 0 else str(item["row_delta"])
            st.markdown(f"- `{item['path']}`  行数变化：`{delta_text}`")
        if len(result["touched_files"]) > 6:
            st.caption(f"另有 {len(result['touched_files']) - 6} 个文件发生变化。")
    else:
        st.info("本次运行未检测到平台目录中的文件变化。")

    with st.expander("查看原始执行日志", expanded=result["status"] != "success"):
        st.code((result["stdout"] + "\n" + result["stderr"]).strip(), language="bash")


def render_keyword_library(editor_prefix: str = "crawl") -> dict:
    kw_data, merged_keywords, expansion = load_keyword_library()
    save_status = {"text": "已同步到本地", "tone": "normal"}

    with st.container(border=True):
        st.markdown(
            """
            <div style='padding:4px 2px 10px 2px;'>
                <div style='font-size:18px; font-weight:700; color:#111;'>关键词库</div>
                <div style='font-size:13px; color:#666; margin-top:6px; line-height:1.6;'>在这里统一维护采集关键词，并在同一处完成扩词与保存。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(
                f"<div style='padding:12px 14px; border:1px solid #EAEAEA; border-radius:10px; background:#FFFFFF; min-height:92px;'><div style='font-size:12px; color:#666;'>当前关键词数</div><div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{len(merged_keywords)}</div></div>",
                unsafe_allow_html=True,
            )
        with meta_col2:
            last_saved_placeholder = st.empty()

        def render_last_saved_card() -> None:
            last_saved_placeholder.markdown(
                f"<div style='padding:12px 14px; border:1px solid #EAEAEA; border-radius:10px; background:#FFFFFF; min-height:92px;'><div style='font-size:12px; color:#666;'>最近保存时间</div><div style='font-size:16px; font-weight:700; color:#111; margin-top:12px;'>{get_keyword_library_last_saved_at()}</div></div>",
                unsafe_allow_html=True,
            )

        render_last_saved_card()

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 编辑关键词")
            st.caption("双击表格即可编辑。修改会自动保存，刷新页面后仍会保留。")

            keyword_df = pd.DataFrame([{"序号": idx, "关键词": k} for idx, k in enumerate(merged_keywords, start=1)])
            if keyword_df.empty:
                keyword_df = pd.DataFrame(columns=["序号", "关键词"])

            edited_keywords = st.data_editor(
                keyword_df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                height=360,
                column_config={
                    "序号": st.column_config.NumberColumn("序号", width=56, disabled=True),
                    "关键词": st.column_config.TextColumn("关键词", help="平台搜索将直接使用的检索词"),
                },
                key=f"{editor_prefix}_keyword_editor",
            )

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 自动扩词设置")
            st.caption("基于既有目标和语料自动补充关键词，结果会直接合并回当前词库。")

            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                exp_enabled = st.toggle("启用自动扩词", value=expansion.get("enabled", True), key=f"{editor_prefix}_exp_enabled")
            with exp_col2:
                provider_options = ["deepseek", "openai", "qwen"]
                provider_value = expansion.get("llm_provider", "deepseek")
                provider_index = provider_options.index(provider_value) if provider_value in provider_options else 0
                exp_provider = st.selectbox("LLM Provider", provider_options, index=provider_index, key=f"{editor_prefix}_exp_provider")

            exp_max = st.number_input(
                "最大提取数 (10-200)",
                min_value=10,
                max_value=200,
                value=int(expansion.get("max_expanded_keywords", 50)),
                key=f"{editor_prefix}_exp_max",
            )

            current_keywords = normalize_keyword_rows(edited_keywords)
            persisted_state = {
                "keywords": merged_keywords,
                "enabled": bool(expansion.get("enabled", True)),
                "provider": expansion.get("llm_provider", "deepseek"),
                "max_keywords": int(expansion.get("max_expanded_keywords", 50)),
            }
            current_state = {
                "keywords": current_keywords,
                "enabled": bool(exp_enabled),
                "provider": exp_provider,
                "max_keywords": int(exp_max),
            }

            auto_saved = False
            if current_state != persisted_state:
                try:
                    save_keyword_library(kw_data, current_keywords, exp_enabled, exp_provider, int(exp_max))
                    auto_saved = True
                    save_status = {"text": "已自动保存到本地", "tone": "success"}
                    render_last_saved_card()
                except Exception as e:
                    save_status = {"text": "自动保存失败", "tone": "error"}
                    st.error(f"自动保存失败：{e}")

            if auto_saved:
                st.caption("已自动保存到本地 `keywords.yaml`。")

            action_cols = st.columns([1, 1])
            with action_cols[0]:
                tone_color = {"success": "#16A34A", "error": "#DC2626", "normal": "#475569"}.get(save_status["tone"], "#475569")
                st.markdown(
                    f"<div style='padding:10px 12px; border:1px dashed #D4D4D4; border-radius:10px; background:#FCFCFC; font-size:13px; color:{tone_color}; font-weight:600;'>{save_status['text']}</div>",
                    unsafe_allow_html=True,
                )

            with action_cols[1]:
                if st.button("立即执行扩词", type="secondary", use_container_width=True, key=f"{editor_prefix}_run_expand"):
                    from src.core.config import load_config
                    from src.core.keyword_expander import KeywordExpander

                    conf = load_config()
                    pbar = st.progress(0)
                    status_txt = st.empty()

                    def cb(cur, tot, name):
                        pbar.progress(cur / tot)
                        status_txt.text(f"[{cur}/{tot}] 正在抓取语料: {name}")

                    with st.spinner("正在扩展关键词，请勿刷新页面..."):
                        expander = KeywordExpander(conf)
                        results = expander.expand(provider=exp_provider, max_keywords=int(exp_max), progress_callback=cb)

                    if results:
                        keywords = list(current_keywords)
                        added = 0
                        for result in results:
                            keyword = str(result).strip()
                            if keyword and keyword not in keywords:
                                keywords.append(keyword)
                                added += 1

                        try:
                            save_keyword_library(kw_data, keywords, exp_enabled, exp_provider, int(exp_max))
                            status_txt.text("")
                            save_status = {"text": "扩词结果已写入本地", "tone": "success"}
                            render_last_saved_card()
                            st.success(f"成功提取 {len(results)} 个候选词，并自动合并了 {added} 个新词。")
                            with st.expander("查看本次提取词典"):
                                st.json(results)
                        except Exception as e:
                            save_status = {"text": "扩词结果写入失败", "tone": "error"}
                            st.error(f"扩词结果保存失败：{e}")
                    else:
                        status_txt.text("")
                        st.error("提取失败或未获取到语料。")

    current_keywords = current_keywords if "current_keywords" in locals() else merged_keywords
    return {
        "keywords": current_keywords,
        "keyword_count": len(current_keywords),
        "save_status": save_status,
        "last_saved_at": get_keyword_library_last_saved_at(),
    }
