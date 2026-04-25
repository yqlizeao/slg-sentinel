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
from ui.i18n import t


def render_step_overview(items: list[tuple[str, str, str]]) -> None:
    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:12px; color:rgba(232,228,220,0.5); font-weight:700; letter-spacing:0.5px; margin-bottom:12px; text-transform:uppercase;'>{t('crawl.flow_title')}</div>",
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
        f"""
        <div style='border:1px solid rgba(180,160,120,0.12); border-radius:8px; background:rgba(12,15,20,0.92); padding:16px; margin-bottom:16px;'>
            <div style='display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:14px;'>
                <div>
                    <div style='font-size:17px; font-weight:800; color:#E8E4DC;'>{t('recursive_flow.title')}</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.4); margin-top:4px; line-height:1.6;'>{t('recursive_flow.desc')}</div>
                </div>
                <div style='font-size:12px; color:#6B8BDB; font-weight:700; background:rgba(107,139,219,0.08); border:1px solid rgba(107,139,219,0.2); border-radius:8px; padding:6px 10px; white-space:nowrap;'>Local NLP / jieba-ready</div>
            </div>
            <div style='display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; align-items:stretch;'>
                <div style='border:1px solid rgba(91,154,110,0.2); background:rgba(91,154,110,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#5B9A6E; font-weight:800;'>01 SEED</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>{t('recursive_flow.seed')}</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>{t('recursive_flow.seed_desc')}</div>
                </div>
                <div style='border:1px solid rgba(107,139,219,0.2); background:rgba(107,139,219,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#6B8BDB; font-weight:800;'>02 CRAWL</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>{t('recursive_flow.crawl')}</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>{t('recursive_flow.crawl_desc')}</div>
                </div>
                <div style='border:1px solid rgba(155,127,212,0.2); background:rgba(155,127,212,0.08); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#9B7FD4; font-weight:800;'>03 MINE</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>{t('recursive_flow.mine')}</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>{t('recursive_flow.mine_desc')}</div>
                </div>
                <div style='border:1px solid rgba(212,175,55,0.2); background:rgba(212,175,55,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#D4956B; font-weight:800;'>04 RECURSE</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>{t('recursive_flow.recurse')}</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>{t('recursive_flow.recurse_desc')}</div>
                </div>
                <div style='border:1px solid rgba(232,93,74,0.2); background:rgba(232,93,74,0.06); border-radius:8px; padding:12px; min-height:106px;'>
                    <div style='font-size:11px; color:#E85D4A; font-weight:800;'>05 STOP</div>
                    <div style='font-size:14px; color:#E8E4DC; font-weight:750; margin-top:8px;'>{t('recursive_flow.stop')}</div>
                    <div style='font-size:12px; color:rgba(232,228,220,0.5); margin-top:6px; line-height:1.45;'>{t('recursive_flow.stop_desc')}</div>
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

    status_text = t('crawl_result.success') if result["status"] == "success" else t('crawl_result.failed')
    status_color = "#5B9A6E" if result["status"] == "success" else "#E85D4A"

    st.markdown(f"##### {t('crawl_result.title')}")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric(t('crawl_result.status'), status_text, delta=f"{result['duration_seconds']:.1f} {t('crawl_result.seconds')}")
    with metric_cols[1]:
        st.metric(t('crawl_result.estimated'), str(result["estimated_results"]), delta=f"{result['keyword_count']} × {result['limit_val']}")
    with metric_cols[2]:
        st.metric(t('crawl_result.new_items'), f"{result['added_videos']} / {result['added_comments']}")
    with metric_cols[3]:
        st.metric(t('crawl_result.files'), str(len(result["touched_files"])))

    st.markdown(
        f"<div style='font-size:13px; color:rgba(232,228,220,0.5); margin:8px 0 12px 0;'>{t('crawl_result.platform')}<span style='color:{status_color}; font-weight:700;'>{_html.escape(result['platform_label'])}</span></div>",
        unsafe_allow_html=True,
    )

    if result["touched_files"]:
        st.markdown(f"**{t('crawl_result.file_receipt')}**")
        for item in result["touched_files"][:6]:
            delta_text = f"+{item['row_delta']}" if item["row_delta"] >= 0 else str(item["row_delta"])
            st.markdown(f"- `{item['path']}`  {t('crawl_result.row_delta')}`{delta_text}`")
        if len(result["touched_files"]) > 6:
            st.caption(t('crawl_result.more_files', count=len(result['touched_files']) - 6))
    else:
        st.info(t('crawl_result.no_change'))

    with st.expander(t('crawl_result.logs'), expanded=result["status"] != "success"):
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
    save_status = {"text": t("keyword.status_synced"), "tone": "normal"}
    current_keywords = list(merged_keywords)

    with st.container(border=True):
        st.markdown(
            f"""
            <div class='atlas-library-head'>
                <div>
                    <div class='atlas-mini-label'>{t("keyword.eyebrow")}</div>
                    <div class='atlas-library-title'>{t("keyword.title")}</div>
                    <div class='atlas-library-subtitle'>{t("keyword.subtitle")}</div>
                </div>
                <div class='atlas-library-radar'>
                    <span>{t("keyword.status_synced")}</span>
                    <strong>{len(merged_keywords):02d}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(
                f"""
                <div class='atlas-library-metric'>
                    <span>{t("keyword.count")}</span>
                    <b>{len(merged_keywords)}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with meta_col2:
            last_saved_placeholder = st.empty()

        def render_last_saved_card() -> None:
            last_saved_placeholder.markdown(
                f"""
                <div class='atlas-library-metric'>
                    <span>{t("keyword.last_saved")}</span>
                    <b class='is-small'>{get_keyword_library_last_saved_at()}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_last_saved_card()

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f"""
                <div class='atlas-panel-title'>{t("keyword.editor_title")}</div>
                <div class='atlas-panel-caption'>{t("keyword.editor_caption")}</div>
                """,
                unsafe_allow_html=True,
            )

            quick_add = st.text_area(
                t("keyword.quick_add"),
                placeholder=t("keyword.quick_add_placeholder"),
                height=86,
                key=f"{editor_prefix}_quick_add",
            )
            add_cols = st.columns([1, 1])
            with add_cols[0]:
                if st.button(t("keyword.add_button"), type="secondary", use_container_width=True, key=f"{editor_prefix}_add_keywords"):
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
                        save_status = {"text": t("keyword.status_added", count=added), "tone": "success"}
                        render_last_saved_card()
                        st.success(t("keyword.add_success", count=added))
                    except Exception as e:
                        save_status = {"text": t("keyword.status_add_failed"), "tone": "error"}
                        st.error(t("keyword.add_failed", error=e))
            with add_cols[1]:
                st.markdown(
                    f"<div class='atlas-status-strip'>{t('keyword.add_note')}</div>",
                    unsafe_allow_html=True,
                )

            search_query = st.text_input(
                t("keyword.filter"),
                placeholder=t("keyword.filter_placeholder"),
                key=f"{editor_prefix}_keyword_filter",
            ).strip()
            filtered_pairs = [
                (idx, keyword)
                for idx, keyword in enumerate(current_keywords)
                if not search_query or search_query.lower() in keyword.lower()
            ]

            st.caption(t("keyword.visible_count", visible=len(filtered_pairs), total=len(current_keywords)))
            editor_df = pd.DataFrame(
                [
                    {"__delete": False, "__index": idx + 1, "__original": keyword, "__keyword": keyword}
                    for idx, keyword in filtered_pairs
                ]
            )
            if editor_df.empty:
                editor_df = pd.DataFrame(columns=["__delete", "__index", "__original", "__keyword"])

            edited_keywords = st.data_editor(
                editor_df,
                use_container_width=True,
                hide_index=True,
                height=min(360, max(150, 42 + 36 * max(len(editor_df), 3))),
                row_height=34,
                column_order=["__delete", "__index", "__keyword"],
                disabled=["__index"],
                column_config={
                    "__delete": st.column_config.CheckboxColumn(t("keyword.col_delete"), width=44),
                    "__index": st.column_config.NumberColumn(t("keyword.col_index"), width=58, disabled=True),
                    "__original": None,
                    "__keyword": st.column_config.TextColumn(t("keyword.col_keyword"), width="large", help=t("keyword.col_keyword_help")),
                },
                key=f"{editor_prefix}_keyword_editor",
            )

            table_cols = st.columns([1, 1, 1])
            with table_cols[0]:
                if st.button(t("keyword.save_table"), type="secondary", use_container_width=True, key=f"{editor_prefix}_save_table"):
                    updated = list(current_keywords)
                    for _, row in edited_keywords.iterrows():
                        old_keyword = str(row.get("__original", "")).strip()
                        new_keyword = str(row.get("__keyword", "")).strip()
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
                        save_status = {"text": t("keyword.status_table_saved"), "tone": "success"}
                        render_last_saved_card()
                        st.success(t("keyword.table_saved"))
                    except Exception as e:
                        save_status = {"text": t("keyword.status_table_failed"), "tone": "error"}
                        st.error(t("keyword.table_failed", error=e))

            with table_cols[1]:
                delete_count = int(edited_keywords["__delete"].sum()) if "__delete" in edited_keywords.columns else 0
                if st.button(
                    t("keyword.delete_checked", count=delete_count),
                    use_container_width=True,
                    key=f"{editor_prefix}_delete_checked",
                    disabled=delete_count == 0,
                ):
                    delete_set = {
                        str(row.get("__original", "")).strip()
                        for _, row in edited_keywords.iterrows()
                        if row.get("__delete")
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
                        save_status = {"text": t("keyword.status_deleted", count=len(delete_set)), "tone": "success"}
                        render_last_saved_card()
                        st.success(t("keyword.delete_success", count=len(delete_set)))
                    except Exception as e:
                        save_status = {"text": t("keyword.status_delete_failed"), "tone": "error"}
                        st.error(t("keyword.delete_failed", error=e))

            with table_cols[2]:
                if st.button(
                    t("keyword.delete_filtered"),
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
                        save_status = {"text": t("keyword.status_deleted_filtered", count=len(delete_set)), "tone": "success"}
                        render_last_saved_card()
                        st.success(t("keyword.delete_filtered_success", count=len(delete_set)))
                    except Exception as e:
                        save_status = {"text": t("keyword.status_delete_filtered_failed"), "tone": "error"}
                        st.error(t("keyword.delete_filtered_failed", error=e))

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                f"""
                <div class='atlas-panel-title'>{t("keyword.expansion_title")}</div>
                <div class='atlas-panel-caption'>{t("keyword.expansion_caption")}</div>
                """,
                unsafe_allow_html=True,
            )

            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                exp_enabled = st.toggle(t("keyword.enable_expansion"), value=expansion.get("enabled", True), key=f"{editor_prefix}_exp_enabled")
            with exp_col2:
                provider_options = ["deepseek", "openai", "qwen"]
                provider_value = expansion.get("llm_provider", "deepseek")
                provider_index = provider_options.index(provider_value) if provider_value in provider_options else 0
                exp_provider = st.selectbox("LLM Provider", provider_options, index=provider_index, key=f"{editor_prefix}_exp_provider")

            exp_max = st.number_input(
                t("keyword.max_extract"),
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
                    save_status = {"text": t("keyword.status_auto_saved"), "tone": "success"}
                    render_last_saved_card()
                except Exception as e:
                    save_status = {"text": t("keyword.status_auto_failed"), "tone": "error"}
                    st.error(t("keyword.auto_failed", error=e))

            if auto_saved:
                st.caption(t("keyword.auto_saved_caption"))

            action_cols = st.columns([1, 1])
            with action_cols[0]:
                tone_color = {"success": "#5B9A6E", "error": "#E85D4A", "normal": "rgba(232,228,220,0.5)"}.get(save_status["tone"], "rgba(232,228,220,0.5)")
                st.markdown(
                    f"<div style='padding:10px 12px; border:1px dashed rgba(180,160,120,0.12); border-radius:10px; background:rgba(12,15,20,0.7); font-size:13px; color:{tone_color}; font-weight:600;'>{save_status['text']}</div>",
                    unsafe_allow_html=True,
                )

            with action_cols[1]:
                if st.button(t("keyword.run_expand"), type="secondary", use_container_width=True, key=f"{editor_prefix}_run_expand"):
                    from src.core.config import load_config
                    from src.core.keyword_expander import KeywordExpander

                    conf = load_config()
                    pbar = st.progress(0)
                    status_txt = st.empty()

                    def cb(cur, tot, name):
                        pbar.progress(cur / tot)
                        status_txt.text(t("keyword.expanding_source", cur=cur, tot=tot, name=name))

                    with st.spinner(t("keyword.expanding_spinner")):
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
                            save_status = {"text": t("keyword.status_expanded_saved"), "tone": "success"}
                            render_last_saved_card()
                            st.success(t("keyword.expand_success", total=len(results), added=added))
                            with st.expander(t("keyword.expand_result")):
                                st.json(results)
                        except Exception as e:
                            save_status = {"text": t("keyword.status_expanded_failed"), "tone": "error"}
                            st.error(t("keyword.expand_save_failed", error=e))
                    else:
                        status_txt.text("")
                        st.error(t("keyword.expand_empty"))

    current_keywords = current_keywords if "current_keywords" in locals() else merged_keywords
    return {
        "keywords": current_keywords,
        "keyword_count": len(current_keywords),
        "save_status": save_status,
        "last_saved_at": get_keyword_library_last_saved_at(),
    }
