from __future__ import annotations

import html as _html
import math

import pandas as pd
import streamlit as st
import streamlit.components.v1 as st_components

from ui.services.app_services import (
    get_keyword_library_last_saved_at,
    load_keyword_library,
    save_keyword_library,
)


def render_step_overview(items: list[tuple[str, str, str]]) -> None:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:12px; color:rgba(232,228,220,0.5); font-weight:700; letter-spacing:0.5px; margin-bottom:12px;'>采集流程</div>",
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
                        <div style='font-size:15px; color:#E8E4DC; font-weight:700; margin-top:6px;'>{title}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            col_idx += 1
            if item_idx < len(items) - 1:
                with cols[col_idx]:
                    st.markdown(
                        "<div style='text-align:center; font-size:22px; color:rgba(180,160,120,0.15); font-weight:700; padding-top:22px;'>→</div>",
                        unsafe_allow_html=True,
                    )
                col_idx += 1


def render_recursive_crawl_flow() -> None:
    st.markdown(
        """
        <div style='border:1px solid rgba(180,160,120,0.12); border-radius:8px; background:rgba(12,15,20,0.92); padding:16px; margin-bottom:16px;'>
            <div style='display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:14px;'>
                <div>
                    <div style='font-size:17px; font-weight:800; color:#E8E4DC;'>AI 递归采集链路</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.4); margin-top:4px; line-height:1.6;'>从种子关键词启动，采集后用标题、标签和高赞评论提炼下一轮关键词，并由上限与停止规则控制递归深度。</div>
                </div>
                <div style='font-size:12px; color:#6B8BDB; font-weight:700; background:rgba(107,139,219,0.08); border:1px solid rgba(107,139,219,0.2); border-radius:8px; padding:6px 10px; white-space:nowrap;'>Local NLP / jieba-ready</div>
            </div>
            <div style='display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; align-items:stretch;'>
                <div style='border:1px solid rgba(91,154,110,0.2); background:rgba(91,154,110,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#5B9A6E; font-weight:800;'>01 SEED</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>种子关键词</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>人工给定或关键词库维护</div>
                </div>
                <div style='border:1px solid rgba(107,139,219,0.2); background:rgba(107,139,219,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#6B8BDB; font-weight:800;'>02 CRAWL</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>平台采集</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>按平台、排序、限额获取视频与评论</div>
                </div>
                <div style='border:1px solid rgba(155,127,212,0.2); background:rgba(155,127,212,0.08); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#9B7FD4; font-weight:800;'>03 MINE</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>语义提词</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>标题、标签、高赞评论加权排序</div>
                </div>
                <div style='border:1px solid rgba(212,175,55,0.2); background:rgba(212,175,55,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#D4956B; font-weight:800;'>04 RECURSE</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>二次采集</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>候选词进入下一轮临时词表</div>
                </div>
                <div style='border:1px solid rgba(232,93,74,0.2); background:rgba(232,93,74,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#E85D4A; font-weight:800;'>05 STOP</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>停止规则</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>深度、增量、候选词分数触发停止</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_keyword_mind_map(candidates: list[dict], root_label: str = "采集结果") -> None:
    if not candidates:
        return

    top_candidates = candidates[:18]
    branches = {
        "标题": [],
        "标签": [],
        "高赞评论": [],
    }
    for candidate in top_candidates:
        source_text = str(candidate.get("sources", ""))
        placed = False
        for branch in branches:
            if branch in source_text:
                branches[branch].append(candidate)
                placed = True
                break
        if not placed:
            branches["标签"].append(candidate)

    branch_html = []
    colors = {
        "标题": ("#6B8BDB", "rgba(107,139,219,0.08)", "rgba(107,139,219,0.2)"),
        "标签": ("#9B7FD4", "rgba(155,127,212,0.08)", "rgba(155,127,212,0.2)"),
        "高赞评论": ("#D4956B", "rgba(212,175,55,0.06)", "rgba(212,175,55,0.2)"),
    }
    for branch_name, items in branches.items():
        if not items:
            continue
        color, bg, border = colors[branch_name]
        node_html = []
        max_score = max(float(item.get("score", 0) or 0) for item in items) or 1
        for item in items:
            score = float(item.get("score", 0) or 0)
            score_label = str(int(round(score)))
            formula = str(item.get("formula", "") or f"热度分 {score_label}")
            size = 12 + min(10, math.sqrt(score / max_score) * 8)
            node_html.append(
                f"""
                <div class="kw-node" title="{_html.escape(formula)} · {_html.escape(str(item.get('evidence', '')))}" style="border-color:{border}; background:{bg};">
                    <span style="font-size:{size:.1f}px;">{_html.escape(str(item.get('keyword', '')))}</span>
                    <b>{score_label}</b>
                </div>
                """
            )
        branch_html.append(
            f"""
            <div class="mind-branch" style="--branch-color:{color};">
                <div class="branch-title">{_html.escape(branch_name)}</div>
                <div class="branch-line"></div>
                <div class="node-wrap">{''.join(node_html)}</div>
            </div>
            """
        )

    html = f"""
    <style>
        .mindmap {{
            border: 1px solid rgba(180,160,120,0.12);
            border-radius: 8px;
            background: rgba(12,15,20,0.92);
            padding: 16px;
            overflow-x: auto;
        }}
        .mindmap-grid {{
            display: grid;
            grid-template-columns: 170px repeat({max(len(branch_html), 1)}, minmax(210px, 1fr));
            gap: 18px;
            align-items: center;
            min-width: 760px;
        }}
        .mind-root {{
            border: 1px solid rgba(180,160,120,0.15);
            background: rgba(12,15,20,0.7);
            border-radius: 8px;
            min-height: 92px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 14px;
            font-size: 15px;
            font-weight: 800;
            color: rgba(232,228,220,0.8);
            position: relative;
        }}
        .mind-root:after {{
            content: "";
            position: absolute;
            right: -18px;
            width: 18px;
            height: 1px;
            background: rgba(180,160,120,0.15);
        }}
        .mind-branch {{
            position: relative;
            border-left: 2px solid var(--branch-color);
            padding-left: 14px;
            min-height: 150px;
        }}
        .branch-title {{
            display: inline-flex;
            font-size: 12px;
            font-weight: 800;
            color: var(--branch-color);
            background: rgba(12,15,20,0.92);
            border: 1px solid currentColor;
            border-radius: 999px;
            padding: 4px 10px;
            margin-bottom: 10px;
        }}
        .branch-line {{
            position: absolute;
            left: -18px;
            top: 28px;
            width: 18px;
            height: 1px;
            background: var(--branch-color);
        }}
        .node-wrap {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: flex-start;
        }}
        .kw-node {{
            border: 1px solid;
            border-radius: 8px;
            padding: 7px 9px;
            display: inline-flex;
            gap: 7px;
            align-items: baseline;
            color: rgba(232,228,220,0.8);
            max-width: 190px;
        }}
        .kw-node span {{
            line-height: 1.1;
            word-break: break-word;
            font-weight: 750;
        }}
        .kw-node b {{
            font-size: 10px;
            color: rgba(232,228,220,0.4);
            font-weight: 700;
            white-space: nowrap;
        }}
        .kw-node b:before {{
            content: "热度 ";
            font-weight: 600;
            color: rgba(232,228,220,0.35);
        }}
    </style>
    <div class="mindmap">
        <div class="mindmap-grid">
            <div class="mind-root">{_html.escape(root_label)}</div>
            {''.join(branch_html)}
        </div>
    </div>
    """
    st_components.html(html, height=300 + 34 * max(len(branch_html), 1), scrolling=True)


def render_step_block_header(step: str, title: str, color: str, description: str | None = None) -> None:
    desc_html = (
        f"<div style='font-size:12px; color:rgba(232,228,220,0.4); margin-top:2px; line-height:1.5;'>{description}</div>"
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
                <div style='font-size:16px; font-weight:700; color:#E8E4DC;'>{title}</div>
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
    status_color = "#5B9A6E" if result["status"] == "success" else "#E85D4A"

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
        f"<div style='font-size:13px; color:rgba(232,228,220,0.5); margin:8px 0 12px 0;'>当前平台：<span style='color:{status_color}; font-weight:700;'>{_html.escape(result['platform_label'])}</span></div>",
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


def _parse_keyword_input(raw_text: str) -> list[str]:
    if not raw_text:
        return []

    normalized = raw_text.replace("，", ",").replace("；", ",").replace(";", ",").replace("、", ",")
    parts = []
    for chunk in normalized.replace("\r", "\n").split("\n"):
        parts.extend(item.strip() for item in chunk.split(","))

    keywords = []
    seen = set()
    for item in parts:
        keyword = item.strip()
        if keyword and keyword not in seen:
            keywords.append(keyword)
            seen.add(keyword)
    return keywords


def render_keyword_library(editor_prefix: str = "crawl") -> dict:
    kw_data, merged_keywords, expansion = load_keyword_library()
    save_status = {"text": "已同步到本地", "tone": "normal"}
    current_keywords = list(merged_keywords)

    with st.container(border=True):
        st.markdown(
            """
            <div style='padding:4px 2px 10px 2px;'>
                <div style='font-size:18px; font-weight:700; color:#E8E4DC;'>关键词库</div>
                <div style='font-size:13px; color:rgba(232,228,220,0.4); margin-top:6px; line-height:1.6;'>在这里统一维护采集关键词，并在同一处完成扩词与保存。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(
                f"<div style='padding:12px 14px; border:1px solid rgba(180,160,120,0.12); border-radius:10px; background:rgba(12,15,20,0.92); min-height:92px;'><div style='font-size:12px; color:rgba(232,228,220,0.4);'>当前关键词数</div><div style='font-size:24px; font-weight:700; color:#E8E4DC; margin-top:8px;'>{len(merged_keywords)}</div></div>",
                unsafe_allow_html=True,
            )
        with meta_col2:
            last_saved_placeholder = st.empty()

        def render_last_saved_card() -> None:
            last_saved_placeholder.markdown(
                f"<div style='padding:12px 14px; border:1px solid rgba(180,160,120,0.12); border-radius:10px; background:rgba(12,15,20,0.92); min-height:92px;'><div style='font-size:12px; color:rgba(232,228,220,0.4);'>最近保存时间</div><div style='font-size:16px; font-weight:700; color:#E8E4DC; margin-top:12px;'>{get_keyword_library_last_saved_at()}</div></div>",
                unsafe_allow_html=True,
            )

        render_last_saved_card()

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 编辑关键词")
            st.caption("日常维护优先使用快速添加和搜索删除；只有需要改词时再编辑过滤后的表格并点击保存。")

            quick_add = st.text_area(
                "快速添加关键词",
                placeholder="每行一个，或用逗号/顿号/分号分隔",
                height=86,
                key=f"{editor_prefix}_quick_add",
            )
            add_cols = st.columns([1, 1])
            with add_cols[0]:
                if st.button("添加到关键词库", type="secondary", use_container_width=True, key=f"{editor_prefix}_add_keywords"):
                    incoming = _parse_keyword_input(quick_add)
                    merged = list(current_keywords)
                    added = 0
                    for keyword in incoming:
                        if keyword not in merged:
                            merged.append(keyword)
                            added += 1
                    try:
                        save_keyword_library(
                            kw_data,
                            merged,
                            bool(expansion.get("enabled", True)),
                            expansion.get("llm_provider", "deepseek"),
                            int(expansion.get("max_expanded_keywords", 50)),
                        )
                        current_keywords = merged
                        save_status = {"text": f"已添加 {added} 个关键词", "tone": "success"}
                        render_last_saved_card()
                        st.success(f"已添加 {added} 个新关键词。")
                    except Exception as e:
                        save_status = {"text": "添加失败", "tone": "error"}
                        st.error(f"添加失败：{e}")
            with add_cols[1]:
                st.markdown(
                    f"<div style='padding:10px 12px; border:1px solid rgba(180,160,120,0.12); border-radius:8px; background:rgba(12,15,20,0.6); font-size:13px; color:rgba(232,228,220,0.5);'>粘贴后不会自动保存，需要点击左侧按钮。</div>",
                    unsafe_allow_html=True,
                )

            search_query = st.text_input(
                "搜索/过滤关键词",
                placeholder="输入关键词片段，过滤后再编辑或删除",
                key=f"{editor_prefix}_keyword_filter",
            ).strip()
            filtered_pairs = [
                (idx, keyword)
                for idx, keyword in enumerate(current_keywords)
                if not search_query or search_query.lower() in keyword.lower()
            ]

            st.caption(f"当前显示 {len(filtered_pairs)} / {len(current_keywords)} 个关键词。")
            editor_df = pd.DataFrame(
                [
                    {"删除": False, "序号": idx + 1, "原关键词": keyword, "关键词": keyword}
                    for idx, keyword in filtered_pairs
                ]
            )
            if editor_df.empty:
                editor_df = pd.DataFrame(columns=["删除", "序号", "原关键词", "关键词"])

            edited_keywords = st.data_editor(
                editor_df,
                use_container_width=True,
                hide_index=True,
                height=min(360, max(150, 42 + 36 * max(len(editor_df), 3))),
                column_config={
                    "删除": st.column_config.CheckboxColumn("删", width=44),
                    "序号": st.column_config.NumberColumn("序号", width=58, disabled=True),
                    "原关键词": None,
                    "关键词": st.column_config.TextColumn("关键词", help="修改后点击“保存表格修改”才会写入本地"),
                },
                key=f"{editor_prefix}_keyword_editor",
            )

            table_cols = st.columns([1, 1, 1])
            with table_cols[0]:
                if st.button("保存表格修改", type="secondary", use_container_width=True, key=f"{editor_prefix}_save_table"):
                    updated = list(current_keywords)
                    for _, row in edited_keywords.iterrows():
                        old_keyword = str(row.get("原关键词", "")).strip()
                        new_keyword = str(row.get("关键词", "")).strip()
                        if not old_keyword:
                            continue
                        try:
                            old_idx = updated.index(old_keyword)
                        except ValueError:
                            continue
                        updated[old_idx] = new_keyword

                    normalized = []
                    seen = set()
                    for keyword in updated:
                        keyword = str(keyword).strip()
                        if keyword and keyword not in seen:
                            normalized.append(keyword)
                            seen.add(keyword)

                    try:
                        save_keyword_library(
                            kw_data,
                            normalized,
                            bool(expansion.get("enabled", True)),
                            expansion.get("llm_provider", "deepseek"),
                            int(expansion.get("max_expanded_keywords", 50)),
                        )
                        current_keywords = normalized
                        save_status = {"text": "表格修改已保存", "tone": "success"}
                        render_last_saved_card()
                        st.success("表格修改已保存。")
                    except Exception as e:
                        save_status = {"text": "表格保存失败", "tone": "error"}
                        st.error(f"表格保存失败：{e}")

            with table_cols[1]:
                delete_count = int(edited_keywords["删除"].sum()) if "删除" in edited_keywords.columns else 0
                if st.button(
                    f"删除勾选项 ({delete_count})",
                    use_container_width=True,
                    key=f"{editor_prefix}_delete_checked",
                    disabled=delete_count == 0,
                ):
                    delete_set = {
                        str(row.get("原关键词", "")).strip()
                        for _, row in edited_keywords.iterrows()
                        if row.get("删除")
                    }
                    kept = [keyword for keyword in current_keywords if keyword not in delete_set]
                    try:
                        save_keyword_library(
                            kw_data,
                            kept,
                            bool(expansion.get("enabled", True)),
                            expansion.get("llm_provider", "deepseek"),
                            int(expansion.get("max_expanded_keywords", 50)),
                        )
                        current_keywords = kept
                        save_status = {"text": f"已删除 {len(delete_set)} 个关键词", "tone": "success"}
                        render_last_saved_card()
                        st.success(f"已删除 {len(delete_set)} 个关键词。")
                    except Exception as e:
                        save_status = {"text": "删除失败", "tone": "error"}
                        st.error(f"删除失败：{e}")

            with table_cols[2]:
                if st.button(
                    "删除当前过滤结果",
                    use_container_width=True,
                    key=f"{editor_prefix}_delete_filtered",
                    disabled=not search_query or not filtered_pairs,
                ):
                    delete_set = {keyword for _, keyword in filtered_pairs}
                    kept = [keyword for keyword in current_keywords if keyword not in delete_set]
                    try:
                        save_keyword_library(
                            kw_data,
                            kept,
                            bool(expansion.get("enabled", True)),
                            expansion.get("llm_provider", "deepseek"),
                            int(expansion.get("max_expanded_keywords", 50)),
                        )
                        current_keywords = kept
                        save_status = {"text": f"已删除过滤结果 {len(delete_set)} 个", "tone": "success"}
                        render_last_saved_card()
                        st.success(f"已删除当前过滤结果中的 {len(delete_set)} 个关键词。")
                    except Exception as e:
                        save_status = {"text": "删除过滤结果失败", "tone": "error"}
                        st.error(f"删除过滤结果失败：{e}")

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
                tone_color = {"success": "#5B9A6E", "error": "#E85D4A", "normal": "rgba(232,228,220,0.5)"}.get(save_status["tone"], "rgba(232,228,220,0.5)")
                st.markdown(
                    f"<div style='padding:10px 12px; border:1px dashed rgba(180,160,120,0.12); border-radius:10px; background:rgba(12,15,20,0.7); font-size:13px; color:{tone_color}; font-weight:600;'>{save_status['text']}</div>",
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
