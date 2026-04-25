from __future__ import annotations

from html import escape
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as st_components

from src.core.config import load_config
from ui.components.atlas_shell import (
    atlas_chips,
    atlas_empty,
    atlas_rows,
    render_atlas_drawer,
    render_atlas_list_editor,
    render_atlas_panel,
    render_atlas_stage,
)
from ui.components.common import render_atlas_ops_board
from ui.components.crawl import (
    render_crawl_result_card,
    render_keyword_library,
    render_keyword_mind_map,
    render_recursive_crawl_flow,
    render_step_overview,
)
from ui.i18n import t
from ui.services.app_services import (
    PLATFORM_OPTIONS,
    extract_keywords_from_crawl_data,
    find_latest_search_metric,
    get_crawl_file_snapshot,
    init_crawl_progress_state,
    load_keyword_library,
    load_latest_search_metrics,
    media_crawler_exists,
    run_cli_stream,
    save_keyword_library,
    summarize_crawl_result,
    update_crawl_progress_state,
    write_temporary_keyword_file,
)
from ui.services.recursive_runs import (
    append_keyword_node,
    append_round,
    append_run_event,
    create_recursive_run,
    finish_latest_round,
    finish_recursive_run,
    list_recursive_runs,
    load_recursive_run,
    relative_output_files,
    save_recursive_run,
    update_keyword_node,
)
from ui.services.recursive_insights import (
    TOPIC_GROUPS,
    build_exploration_summary,
    business_progress_events,
    collect_candidates_from_run,
    format_score,
    group_topic_candidates,
    search_scale_label,
)



def _render_recursive_config(keyword_runtime: dict, is_expert: bool) -> dict:
    keyword_count = keyword_runtime.get("keyword_count", len(load_keyword_library()[1]))
    limit_options = {
        10: "10 条 (安全试探，极速)",
        20: "20 条",
        30: "30 条",
        40: "40 条",
        50: "50 条 (常规快照)",
    }
    strategy_options = {
        "标准探索": {"max_depth": 2, "per_round_keywords": 8, "min_score": 3.0, "stop_new_keywords": 3, "limit_val": 20},
        "保守探索": {"max_depth": 2, "per_round_keywords": 5, "min_score": 6.0, "stop_new_keywords": 2, "limit_val": 10},
        "深度探索": {"max_depth": 3, "per_round_keywords": 12, "min_score": 2.0, "stop_new_keywords": 3, "limit_val": 30},
    }

    with st.container(border=True):
        quick_cols = st.columns([1, 1.2, 1])
        with quick_cols[0]:
            platform = st.selectbox(
                "平台",
                list(PLATFORM_OPTIONS.keys()),
                format_func=lambda x: PLATFORM_OPTIONS[x],
                key="recursive_platform",
            )
        with quick_cols[1]:
            selected_strategy = st.selectbox(
                "探索策略",
                list(strategy_options.keys()),
                index=0,
                key="recursive_strategy",
                help="标准探索适合日常营销选题；保守探索更快更稳；深度探索用于更完整地铺开话题。",
            )
        with quick_cols[2]:
            st.metric("起始话题", f"{keyword_count} 个")

        preset = strategy_options[selected_strategy]
        mode = "本地鉴权" if platform in ["xiaohongshu", "douyin", "kuaishou"] else "免登录"
        depth = "受限单体深度遍历" if platform in ["xiaohongshu", "douyin", "kuaishou"] else "基础采集"
        limit_val = int(preset["limit_val"])
        max_depth = int(preset["max_depth"])
        per_round_keywords = int(preset["per_round_keywords"])
        min_score = float(preset["min_score"])
        stop_new_keywords = int(preset["stop_new_keywords"])

        order_val = "totalrank"
        order_label = "平台默认策略"
        with st.expander("高级采集设置", expanded=is_expert):
            cfg_cols = st.columns([1, 1, 1])
            with cfg_cols[0]:
                if platform in ["xiaohongshu", "douyin", "kuaishou"]:
                    mode = st.selectbox("鉴权模式", ["本地鉴权"], key="recursive_mode_media")
                else:
                    mode = st.selectbox("鉴权模式", ["免登录", "本地鉴权"], key="recursive_mode_general")
            with cfg_cols[1]:
                if platform in ["xiaohongshu", "douyin", "kuaishou"]:
                    depth = st.selectbox("采集深度", ["受限单体深度遍历"], key="recursive_depth_media", disabled=True)
                else:
                    depth = st.selectbox("采集深度", ["基础采集", "深度采集"], key="recursive_depth_general")
            with cfg_cols[2]:
                limit_val = st.selectbox(
                    "每个话题获取上限",
                    list(limit_options.keys()),
                    index=list(limit_options.keys()).index(limit_val),
                    format_func=lambda x: limit_options[x],
                    key="recursive_limit",
                )

            if platform == "bilibili":
                order_map = {
                    "平台搜索默认排序 (Total Rank)": "totalrank",
                    "最新发布时间排序 (Publish Date)": "pubdate",
                    "最多点击播放排序 (Click)": "click",
                    "最多用户收藏排序 (Stow)": "stow",
                }
                order_label = st.selectbox("B站搜索排序", list(order_map.keys()), index=0, key="recursive_order_bilibili")
                order_val = order_map[order_label]

            recurse_cols = st.columns(4)
            with recurse_cols[0]:
                max_depth = st.number_input("最大探索轮数", min_value=1, max_value=4, value=max_depth, step=1, key="recursive_depth_limit")
            with recurse_cols[1]:
                per_round_keywords = st.number_input("每轮新话题上限", min_value=3, max_value=30, value=per_round_keywords, step=1, key="recursive_topk")
            with recurse_cols[2]:
                min_score = st.number_input("最低推荐指数", min_value=1.0, max_value=20.0, value=min_score, step=0.5, key="recursive_min_score")
            with recurse_cols[3]:
                stop_new_keywords = st.number_input("少于 N 个新话题暂停", min_value=1, max_value=10, value=stop_new_keywords, step=1, key="recursive_stop_new")

        mode_preview = "免登录" if mode == "免登录" else "本地鉴权"
        depth_preview = "深度采集" if "深度" in depth else "基础采集"
        st.markdown(
            f"""
            <div style='padding:10px 12px; border:1px dashed rgba(180,160,120,0.12); border-radius:8px; background:rgba(12,15,20,0.7); margin-top:8px;'>
                <div style='font-size:12px; color:rgba(232,228,220,0.4);'>本次探索概览</div>
                <div style='font-size:13px; color:#E8E4DC; margin-top:6px; line-height:1.7;'>{PLATFORM_OPTIONS[platform]} / {selected_strategy} / {mode_preview} / {depth_preview} / {order_label} / 每个话题 {limit_val} 条</div>
                <div style='font-size:13px; color:#6B8BDB; margin-top:6px; font-weight:600;'>起始话题：{keyword_count} 个 · 最大轮数：{int(max_depth)} · 每轮新话题上限：{int(per_round_keywords)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    media_platforms = {"xiaohongshu", "douyin", "kuaishou"}
    runtime_config = load_config()
    can_execute = True
    if keyword_count == 0:
        can_execute = False
        st.warning("当前关键词库为空，请先在右侧补充关键词后再执行递归采集。")
    elif platform in media_platforms and not media_crawler_exists():
        can_execute = False
        st.error("未检测到 MediaCrawler 子模块，当前平台暂不可执行。")
    elif platform == "bilibili" and mode == "本地鉴权" and not runtime_config.bili_sessdata:
        st.info("当前未检测到 Bilibili 会话，仍可执行基础采集；如需评论等深度数据，请先完成本地鉴权。")

    return {
        "platform": platform,
        "mode": mode,
        "depth": depth,
        "order_val": order_val,
        "limit_val": int(limit_val),
        "max_depth": int(max_depth),
        "per_round_keywords": int(per_round_keywords),
        "min_score": float(min_score),
        "stop_new_keywords": int(stop_new_keywords),
        "can_execute": can_execute,
        "keyword_count": keyword_count,
        "strategy": selected_strategy,
    }


def _render_search_metrics(platform: str) -> None:
    if platform != "bilibili":
        return

    metrics_df = load_latest_search_metrics(platform)
    if metrics_df.empty:
        return

    display_cols = [
        col
        for col in ["keyword", "total_results_display", "is_capped", "num_pages", "page_size", "fetched_count", "created_at"]
        if col in metrics_df.columns
    ]
    with st.expander("查看最近 B站关键词搜索量记录", expanded=False):
        st.caption("`>=1000` 表示 B站搜索接口返回结果池已封顶，不能当作真实全站总量。")
        st.dataframe(metrics_df[display_cols], use_container_width=True, hide_index=True)


def _render_recursive_tree(run: dict) -> None:
    nodes = run.get("nodes", [])
    if not nodes:
        st.info("这个任务还没有递归节点。")
        return

    status_colors = {
        "running": "#6B8BDB",
        "success": "#5B9A6E",
        "stopped": "#D4956B",
        "paused": "#D4956B",
        "error": "#E85D4A",
    }
    rounds = sorted({int(node.get("round", 0) or 0) for node in nodes})
    html_rounds = []
    for round_idx in rounds:
        cards = []
        for node in [item for item in nodes if int(item.get("round", 0) or 0) == round_idx]:
            color = status_colors.get(node.get("status"), "rgba(232,228,220,0.4)")
            search = node.get("search_metrics", {}) or {}
            crawl = node.get("crawl_metrics", {}) or {}
            candidates = node.get("candidate_metrics", {}) or {}
            total = search.get("total_results_display") or search.get("total_results") or "—"
            is_capped = " · 封顶" if search.get("is_capped") else ""
            cards.append(
                f"""
                <div class="tree-card" style="border-color:{color};">
                    <div class="tree-status" style="color:{color};">{node.get('status', '')}</div>
                    <div class="tree-keyword">{node.get('keyword', '')}</div>
                    <div class="tree-meta">搜索量 {total}{is_capped}</div>
                    <div class="tree-meta">视频 {crawl.get('videos', 0)} · 评论 {crawl.get('comments', 0)} · 候选 {candidates.get('count', 0)}</div>
                    <div class="tree-stop">{node.get('stop_reason', '')}</div>
                </div>
                """
            )
        html_rounds.append(
            f"""
            <div class="tree-round">
                <div class="round-title">第 {round_idx} 轮</div>
                <div class="round-cards">{''.join(cards)}</div>
            </div>
            """
        )

    html = f"""
    <style>
      .tree-wrap {{ border:1px solid rgba(180,160,120,0.12); border-radius:8px; padding:14px; background:rgba(12,15,20,0.92); overflow:auto; }}
      .tree-grid {{ display:flex; gap:16px; align-items:flex-start; min-width:860px; }}
      .tree-round {{ min-width:250px; }}
      .round-title {{ font-size:12px; color:rgba(232,228,220,0.4); font-weight:800; margin-bottom:8px; }}
      .round-cards {{ display:flex; flex-direction:column; gap:10px; }}
      .tree-card {{ border:1px solid; border-left-width:4px; border-radius:8px; background:rgba(12,15,20,0.7); padding:10px 12px; }}
      .tree-status {{ font-size:10px; font-weight:800; text-transform:uppercase; }}
      .tree-keyword {{ font-size:16px; color:rgba(232,228,220,0.8); font-weight:800; margin-top:3px; word-break:break-word; }}
      .tree-meta {{ font-size:12px; color:rgba(232,228,220,0.5); margin-top:5px; }}
      .tree-stop {{ font-size:12px; color:#D4956B; margin-top:5px; min-height:14px; }}
    </style>
    <div class="tree-wrap"><div class="tree-grid">{''.join(html_rounds)}</div></div>
    """
    st_components.html(html, height=min(620, 170 + 120 * max(len(nodes), 1)), scrolling=True)


def _render_node_detail(run: dict) -> None:
    nodes = run.get("nodes", [])
    if not nodes:
        return

    node_labels = {
        f"第{node.get('round')}轮 · {node.get('keyword')} · {node.get('status')}": node.get("node_id")
        for node in nodes
    }
    selected_label = st.selectbox("查看节点详情", list(node_labels.keys()), key=f"recursive_node_detail_{run.get('run_id')}")
    selected_node = next((node for node in nodes if node.get("node_id") == node_labels[selected_label]), None)
    if not selected_node:
        return

    search = selected_node.get("search_metrics", {}) or {}
    crawl = selected_node.get("crawl_metrics", {}) or {}
    candidates = selected_node.get("candidate_metrics", {}) or {}
    detail_cols = st.columns(4)
    with detail_cols[0]:
        st.metric("搜索量", search.get("total_results_display") or search.get("total_results") or "—")
    with detail_cols[1]:
        st.metric("采集视频", str(crawl.get("videos", 0)))
    with detail_cols[2]:
        st.metric("采集评论", str(crawl.get("comments", 0)))
    with detail_cols[3]:
        st.metric("候选词", str(candidates.get("count", 0)))

    if candidates.get("candidates"):
        st.markdown("##### 下一轮候选词")
        st.dataframe(pd.DataFrame(candidates["candidates"]), use_container_width=True, hide_index=True)
    if selected_node.get("evidence"):
        st.markdown("##### 证据片段")
        for evidence in selected_node["evidence"][:5]:
            st.caption(evidence)
    if crawl.get("touched_files"):
        st.markdown("##### 输出文件")
        for item in crawl["touched_files"][:8]:
            st.caption(str(item))


def _render_history_library(is_expert: bool) -> None:
    st.markdown("### 历史探索库")
    filter_cols = st.columns([1, 1, 1, 1, 1])
    with filter_cols[0]:
        platform_filter = st.selectbox("平台过滤", ["全部"] + list(PLATFORM_OPTIONS.keys()), format_func=lambda x: "全部" if x == "全部" else PLATFORM_OPTIONS[x], key="recursive_history_platform")
    with filter_cols[1]:
        status_filter = st.selectbox("状态过滤", ["全部", "running", "paused", "success", "stopped", "error"], key="recursive_history_status")
    with filter_cols[2]:
        keyword_filter = st.text_input("关键词过滤", key="recursive_history_keyword")
    with filter_cols[3]:
        date_from = st.date_input("开始日期", value=None, key="recursive_history_date_from")
    with filter_cols[4]:
        date_to = st.date_input("结束日期", value=None, key="recursive_history_date_to")

    runs = list_recursive_runs(
        platform=None if platform_filter == "全部" else platform_filter,
        status=None if status_filter == "全部" else status_filter,
        keyword=keyword_filter,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
    )
    if not runs:
        st.info("暂无递归采集历史任务。")
        return

    rows = []
    for run in runs:
        summary = run.get("summary", {})
        rows.append(
            {
                "run_id": run.get("run_id"),
                "状态": run.get("status"),
                "平台": PLATFORM_OPTIONS.get(run.get("platform"), run.get("platform")),
                "开始时间": run.get("started_at") or run.get("created_at"),
                "探索节点": summary.get("total_nodes", 0),
                "视频": summary.get("total_videos", 0),
                "评论": summary.get("total_comments", 0),
                "停止原因": run.get("stop_reason", ""),
            }
        )
    history_df = pd.DataFrame(rows)
    st.dataframe(history_df.drop(columns=["run_id"]), use_container_width=True, hide_index=True)

    selected_run_id = st.selectbox("打开任务复盘", history_df["run_id"].tolist(), key="recursive_history_selected")
    selected_run = load_recursive_run(selected_run_id)
    if not selected_run:
        st.error("任务文件不存在或读取失败。")
        return

    if selected_run.get("status") == "paused":
        action_cols = st.columns(3)
        with action_cols[0]:
            if st.button("继续（记录为待续）", use_container_width=True, key="recursive_paused_continue"):
                append_run_event(selected_run, "operator_continue", "用户选择继续；当前版本记录操作，需重新启动任务执行")
                save_recursive_run(selected_run)
                st.info("已记录继续操作。当前版本请重新启动递归任务以继续执行。")
        with action_cols[1]:
            if st.button("跳过当前分支", use_container_width=True, key="recursive_paused_skip"):
                append_run_event(selected_run, "operator_skip", "用户选择跳过当前分支")
                selected_run["pending_queue"] = []
                finish_recursive_run(selected_run, "stopped", "用户跳过暂停分支")
                save_recursive_run(selected_run)
                st.success("已将任务标记为 stopped。")
        with action_cols[2]:
            if st.button("终止任务", use_container_width=True, key="recursive_paused_stop"):
                append_run_event(selected_run, "operator_stop", "用户终止任务")
                finish_recursive_run(selected_run, "stopped", "用户终止任务")
                save_recursive_run(selected_run)
                st.success("已终止任务。")

    if is_expert:
        st.markdown("### 递归树复盘")
        _render_recursive_tree(selected_run)
        _render_node_detail(selected_run)
        with st.expander("任务 JSON 诊断", expanded=False):
            st.json(selected_run)
    else:
        _render_run_summary(selected_run)
        _render_business_progress(selected_run)


def _render_heat_formula_help(is_expert: bool) -> None:
    with st.expander("推荐指数是怎么计算的", expanded=is_expert):
        st.markdown(
            """
            **推荐指数 = 标题贡献 + 标签贡献 + 高赞评论贡献**

            当前算法会读取最近采集到的视频和评论 CSV，用 `jieba` 分词；如果环境里没有 `jieba`，会自动使用内置分词兜底。已经在关键词库里的词会被过滤，不再作为新候选词出现。

            计分规则：
            - 标题命中：`2.2 × 视频热度系数`
            - 标签命中：`2.8 × 视频热度系数`
            - 高赞评论命中：`1.25 × 评论点赞系数`

            系数规则：
            - 视频热度系数：`1 + min(log10(播放量), 6) / 5`
            - 评论点赞系数：`1 + min(log10(点赞数), 4) / 4`

            所以标签里的词通常会更高，因为它更像平台或作者明确标注的主题；高播放视频里的标题/标签也会被放大。页面卡片展示的是四舍五入后的整数推荐指数，专家明细表保留精确小数和来源拆解。
            """
        )


def _add_keyword_to_library(keyword: str) -> bool:
    kw_data, merged_keywords, expansion = load_keyword_library()
    merged = list(merged_keywords)
    if keyword in merged:
        return False
    merged.append(keyword)
    save_keyword_library(
        kw_data,
        merged,
        bool(expansion.get("enabled", True)),
        expansion.get("llm_provider", "deepseek"),
        int(expansion.get("max_expanded_keywords", 50)),
    )
    return True


def _render_topic_group_cards(grouped: dict[str, list[dict]], run_id: str = "current") -> None:
    st.markdown("##### 本次探索摘要")
    group_tabs = st.tabs([TOPIC_GROUPS[key]["label"] for key in TOPIC_GROUPS])
    for tab, group_key in zip(group_tabs, TOPIC_GROUPS.keys()):
        with tab:
            st.caption(TOPIC_GROUPS[group_key]["description"])
            items = grouped.get(group_key, [])
            if not items:
                st.info("暂无话题。")
                continue
            for index, candidate in enumerate(items):
                keyword = str(candidate.get("keyword", "")).strip()
                score = format_score(candidate.get("score", 0))
                sources = candidate.get("sources") or candidate.get("source") or "最新采集结果"
                evidence = candidate.get("evidence") or candidate.get("reason") or "暂无证据片段"
                parent_keyword = candidate.get("parent_keyword")
                with st.container(border=True):
                    top_cols = st.columns([1.2, 0.7, 0.7, 0.6])
                    with top_cols[0]:
                        st.markdown(f"**{keyword}**")
                        if parent_keyword:
                            st.caption(f"由「{parent_keyword}」扩展发现")
                    with top_cols[1]:
                        st.metric("推荐指数", score)
                    with top_cols[2]:
                        st.metric("B站搜索规模", search_scale_label(candidate))
                    with top_cols[3]:
                        if st.button("加入词库", key=f"add_topic_{run_id}_{group_key}_{index}_{keyword}", use_container_width=True):
                            if _add_keyword_to_library(keyword):
                                st.success(f"已加入：{keyword}")
                            else:
                                st.info("词库里已经有这个话题。")
                    st.caption(f"来源：{sources}")
                    st.write(str(evidence)[:180])


def _render_run_summary(run: dict) -> None:
    candidates = collect_candidates_from_run(run)
    summary = build_exploration_summary(run, candidates)
    st.markdown("### 本次探索摘要")
    seed = "、".join(summary["seed_keywords"][:4]) if summary["seed_keywords"] else "未记录"
    st.caption(f"起始话题：{seed} · 建议：{summary['next_action']}")
    metric_cols = st.columns(6)
    metric_cols[0].metric("状态", summary["status"] or "—")
    metric_cols[1].metric("已采集视频", str(summary["total_videos"]))
    metric_cols[2].metric("评论线索", str(summary["total_comments"]))
    metric_cols[3].metric("发现话题", str(summary["discovered_topics"]))
    metric_cols[4].metric("推荐继续", str(summary["recommended_topics"]))
    metric_cols[5].metric("异常数", str(summary["abnormal_count"]))
    if candidates:
        _render_topic_group_cards(summary["groups"], run_id=str(run.get("run_id", "last")))
    else:
        st.info("这个任务还没有可汇总的新发现话题。")


def _render_business_progress(run: dict) -> None:
    messages = business_progress_events(run)
    if not messages:
        return
    with st.expander("业务进度流", expanded=True):
        for message in messages:
            st.write(f"- {message}")


def _render_candidate_panel(config: dict, keyword_runtime: dict, is_expert: bool) -> list[str]:
    _render_heat_formula_help(is_expert)

    action_cols = st.columns([1, 1, 1.2])
    with action_cols[0]:
        mine_clicked = st.button("从最新结果发现话题", use_container_width=True, key="recursive_mine")
    with action_cols[1]:
        merge_clicked = st.button("合并选中话题", use_container_width=True, key="recursive_merge")
    with action_cols[2]:
        run_recursive_clicked = st.button(
            "启动 AI 话题探索",
            type="primary",
            use_container_width=True,
            key="recursive_run",
            disabled=not config["can_execute"],
        )

    if mine_clicked:
        mined = extract_keywords_from_crawl_data(
            platform=config["platform"],
            existing_keywords=keyword_runtime.get("keywords", []),
            max_keywords=config["per_round_keywords"] * 3,
            min_score=config["min_score"],
        )
        st.session_state["recursive_candidates"] = [{"启用": True, **candidate} for candidate in mined["candidates"]]
        st.session_state["recursive_mining_meta"] = mined

    candidates = st.session_state.get("recursive_candidates", [])
    mining_meta = st.session_state.get("recursive_mining_meta", {})
    if mining_meta:
        jieba_status = "jieba 分词" if mining_meta.get("used_jieba") else "内置分词兜底"
        st.info(f"已读取 {mining_meta.get('video_rows', 0)} 条视频记录、{mining_meta.get('comment_rows', 0)} 条评论记录，当前使用：{jieba_status}。")

    if candidates:
        grouped = group_topic_candidates(candidates)
        if not is_expert:
            _render_topic_group_cards(grouped, run_id="candidate")
            selected_keywords = [
                str(candidate.get("keyword", "")).strip()
                for candidate in grouped["strong"] + grouped["long_tail"] + grouped["review"]
                if str(candidate.get("keyword", "")).strip()
            ][: config["per_round_keywords"]]
        else:
            st.markdown("##### 候选词局部视图")
            render_keyword_mind_map(candidates, root_label=f"{PLATFORM_OPTIONS[config['platform']]} 最新采集结果")
            st.markdown("##### 新发现话题明细")
            edited_candidates = st.data_editor(
                pd.DataFrame(candidates),
                use_container_width=True,
                hide_index=True,
                height=320,
                column_config={
                    "启用": st.column_config.CheckboxColumn("启用", width=56),
                    "keyword": st.column_config.TextColumn("新发现话题", disabled=True),
                    "score": st.column_config.NumberColumn("推荐指数", disabled=True, format="%.2f"),
                    "frequency": st.column_config.NumberColumn("频次", disabled=True),
                    "title_score": st.column_config.NumberColumn("标题贡献", disabled=True, format="%.2f"),
                    "tag_score": st.column_config.NumberColumn("标签贡献", disabled=True, format="%.2f"),
                    "comment_score": st.column_config.NumberColumn("评论贡献", disabled=True, format="%.2f"),
                    "sources": st.column_config.TextColumn("来源", disabled=True),
                    "formula": st.column_config.TextColumn("计算拆解", disabled=True),
                    "reason": st.column_config.TextColumn("AI 判断", disabled=True),
                    "evidence": st.column_config.TextColumn("证据片段", disabled=True),
                },
                key="recursive_candidate_editor",
            )
            selected_keywords = [
                str(row.get("keyword", "")).strip()
                for _, row in edited_candidates.iterrows()
                if row.get("启用") and str(row.get("keyword", "")).strip()
            ][: config["per_round_keywords"]]
    else:
        selected_keywords = []
        st.markdown(
            "<div style='padding:12px 14px; border:1px dashed rgba(180,160,120,0.12); border-radius:8px; background:rgba(12,15,20,0.7); color:rgba(232,228,220,0.4); font-size:13px;'>暂无新发现话题。可以先运行一次基础采集，或点击“从最新结果发现话题”。</div>",
            unsafe_allow_html=True,
        )

    if merge_clicked:
        if not selected_keywords:
            st.warning("请先选择至少一个新发现话题。")
        else:
            kw_data, merged_keywords, expansion = load_keyword_library()
            merged = list(merged_keywords)
            added = 0
            for keyword in selected_keywords:
                if keyword not in merged:
                    merged.append(keyword)
                    added += 1
            save_keyword_library(
                kw_data,
                merged,
                bool(expansion.get("enabled", True)),
                expansion.get("llm_provider", "deepseek"),
                int(expansion.get("max_expanded_keywords", 50)),
            )
            st.success(f"已合并 {added} 个新话题到关键词库。")

    if run_recursive_clicked:
        _run_recursive_crawl(config, keyword_runtime, is_expert=is_expert)

    return selected_keywords


def _run_recursive_crawl(config: dict, keyword_runtime: dict, is_expert: bool = False) -> None:
    media_platforms = {"xiaohongshu", "douyin", "kuaishou"}
    platform = config["platform"]
    mode_value = "actions" if config["mode"] == "免登录" else "local"
    depth_args = []
    if platform not in media_platforms and "基础" in config["depth"]:
        depth_args = ["--depth", "shallow"]
    elif platform not in media_platforms and "深度" in config["depth"]:
        depth_args = ["--depth", "deep"]

    seed_keywords = list(keyword_runtime.get("keywords", []))
    seen_keywords = set(seed_keywords)
    round_entries = [{"keyword": keyword, "parent_id": ""} for keyword in seed_keywords]
    total_keywords_run = 0
    run = create_recursive_run(config, seed_keywords)
    st.session_state["recursive_active_run_id"] = run["run_id"]
    append_run_event(run, "start", "递归采集任务启动", {"seed_keywords": seed_keywords})
    save_recursive_run(run)
    recursive_logs = []

    status_box = st.empty()
    metric_cols = st.columns(4)
    with metric_cols[0]:
        round_metric = st.empty()
    with metric_cols[1]:
        keyword_metric = st.empty()
    with metric_cols[2]:
        total_metric = st.empty()
    with metric_cols[3]:
        next_metric = st.empty()
    recursive_progress = st.progress(0)
    recursive_detail = st.empty()
    live_log_box = st.empty()

    def refresh_recursive_ui(round_idx: int, progress_state: dict, next_count: int = 0) -> None:
        overall_base = (round_idx - 1) / max(config["max_depth"], 1)
        overall_round = progress_state.get("progress", 0.0) / max(config["max_depth"], 1)
        overall_progress = min(0.99, overall_base + overall_round)
        recursive_progress.progress(max(1, int(overall_progress * 100)))
        round_metric.metric("当前轮次", f"{round_idx}/{config['max_depth']}")
        keyword_metric.metric("本轮话题", str(len(round_entries)))
        total_value = progress_state.get("search_total_latest")
        total_metric.metric("最新搜索总量", str(total_value) if total_value is not None else "等待返回")
        next_metric.metric("下一轮新话题", str(next_count))
        recursive_detail.caption(f"{progress_state.get('stage', '准备中')} · {progress_state.get('detail', '')}")
        visible_logs = "\n".join(recursive_logs[-12:])
        if is_expert and visible_logs:
            live_log_box.code(visible_logs, language="bash")
        elif not is_expert:
            live_log_box.info(
                f"正在探索第 {round_idx} 轮：搜索量 {total_value if total_value is not None else '等待返回'}，已发现下一轮新话题 {next_count} 个。"
            )

    pause_triggered = False
    stop_reason = ""

    for round_idx in range(1, config["max_depth"] + 1):
        round_entries = [entry for entry in round_entries if entry.get("keyword")]
        if round_idx > 1:
            round_entries = round_entries[: config["per_round_keywords"]]
        if not round_entries:
            recursive_logs.append(f"第 {round_idx} 轮无可执行关键词，递归停止。")
            stop_reason = "无新关键词"
            break

        round_keywords = [entry["keyword"] for entry in round_entries]
        append_round(run, round_idx, round_keywords)
        save_recursive_run(run)
        total_keywords_run += len(round_keywords)
        status_box.info(f"第 {round_idx}/{config['max_depth']} 轮：使用 {len(round_keywords)} 个话题采集。")
        progress_state = init_crawl_progress_state(platform, len(round_keywords), config["limit_val"])
        refresh_recursive_ui(round_idx, progress_state)

        next_entries = []
        for entry in round_entries:
            keyword = entry["keyword"]
            node = append_keyword_node(run, keyword, parent_id=entry.get("parent_id"), round_index=round_idx)
            append_run_event(run, "node_start", f"开始采集关键词：{keyword}", {"node_id": node["node_id"]})
            save_recursive_run(run)

            keyword_started_at = datetime.now()
            before_snapshot = get_crawl_file_snapshot(platform)
            tmp_keywords_path = write_temporary_keyword_file([keyword], label=f"{platform}_round_{round_idx}_{keyword}")
            cmd_args = [
                "crawl",
                "--platform",
                platform,
                "--mode",
                mode_value,
                "--order",
                config["order_val"],
                "--limit",
                str(config["limit_val"]),
                "--keywords-file",
                str(tmp_keywords_path),
            ] + depth_args

            def on_recursive_line(line: str) -> None:
                update_crawl_progress_state(progress_state, line)
                recursive_logs.append(f"[Round {round_idx}] {line}")
                refresh_recursive_ui(round_idx, progress_state)

            stdout, stderr, code = run_cli_stream(cmd_args, on_line=on_recursive_line)
            after_snapshot = get_crawl_file_snapshot(platform)
            result = summarize_crawl_result(
                platform=platform,
                platform_label=PLATFORM_OPTIONS[platform],
                before_snapshot=before_snapshot,
                after_snapshot=after_snapshot,
                keyword_count=1,
                limit_val=config["limit_val"],
                started_at=keyword_started_at,
                return_code=code,
                stdout=stdout,
                stderr=stderr,
            )
            search_metric = find_latest_search_metric(platform, keyword, started_at=keyword_started_at) if platform == "bilibili" else {}
            crawl_metrics = {
                "videos": result["added_videos"],
                "comments": result["added_comments"],
                "touched_files": result["touched_files"],
            }

            error_reason = ""
            if code != 0:
                error_reason = f"CLI 返回非 0：{code}"
            elif result["added_videos"] == 0:
                error_reason = "该关键词采集视频数为 0"
            elif platform == "bilibili" and not search_metric.get("total_results_display") and not search_metric.get("total_results"):
                error_reason = "B站搜索量无法获取"

            if error_reason:
                update_keyword_node(
                    run,
                    node["node_id"],
                    status="paused",
                    search_metrics=search_metric,
                    crawl_metrics=crawl_metrics,
                    stop_reason=error_reason,
                )
                run["pending_queue"] = [entry] + round_entries[round_entries.index(entry) + 1 :]
                run["paused_node_id"] = node["node_id"]
                append_run_event(run, "pause", error_reason, {"node_id": node["node_id"], "keyword": keyword})
                finish_latest_round(run, "paused", error_reason)
                finish_recursive_run(run, "paused", error_reason)
                save_recursive_run(run)
                status_box.warning(f"任务暂停：{error_reason}")
                pause_triggered = True
                break

            mined = extract_keywords_from_crawl_data(
                platform=platform,
                existing_keywords=list(seen_keywords),
                max_keywords=config["per_round_keywords"],
                min_score=config["min_score"],
            )
            candidates = mined["candidates"]
            candidate_keywords = []
            for candidate in candidates:
                candidate_keyword = candidate["keyword"]
                if candidate_keyword not in seen_keywords:
                    seen_keywords.add(candidate_keyword)
                    candidate_keywords.append(candidate_keyword)
                    next_entries.append({"keyword": candidate_keyword, "parent_id": node["node_id"]})

            candidate_metrics = {
                "count": len(candidate_keywords),
                "top_score": candidates[0]["score"] if candidates else 0,
                "candidates": candidates[: config["per_round_keywords"]],
            }
            evidence = []
            for candidate in candidates[:5]:
                if candidate.get("evidence"):
                    evidence.append(f"{candidate['keyword']}: {candidate['evidence']}")

            if len(candidate_keywords) < config["stop_new_keywords"]:
                stop_text = f"本节点新候选词仅 {len(candidate_keywords)} 个，低于停止阈值 {config['stop_new_keywords']}"
                node_status = "paused"
                append_run_event(run, "pause", stop_text, {"node_id": node["node_id"], "keyword": keyword})
            else:
                stop_text = ""
                node_status = "success"

            update_keyword_node(
                run,
                node["node_id"],
                status=node_status,
                search_metrics=search_metric,
                crawl_metrics=crawl_metrics,
                candidate_metrics=candidate_metrics,
                evidence=evidence,
                stop_reason=stop_text,
            )
            run["output_files"] = sorted(set(run.get("output_files", []) + relative_output_files(result["touched_files"])))
            save_recursive_run(run)
            refresh_recursive_ui(round_idx, progress_state, len(next_entries))

            if node_status == "paused":
                run["pending_queue"] = next_entries + round_entries[round_entries.index(entry) + 1 :]
                run["paused_node_id"] = node["node_id"]
                finish_latest_round(run, "paused", stop_text)
                finish_recursive_run(run, "paused", stop_text)
                save_recursive_run(run)
                status_box.warning(f"任务暂停：{stop_text}")
                pause_triggered = True
                break

        if pause_triggered:
            break

        finish_latest_round(run, "success")
        save_recursive_run(run)
        if next_entries:
            latest_candidates = []
            for node in run.get("nodes", [])[-len(round_entries) :]:
                latest_candidates.extend(node.get("candidate_metrics", {}).get("candidates", []))
            if latest_candidates:
                st.markdown(f"##### 第 {round_idx} 轮扩词图")
                render_keyword_mind_map(latest_candidates[: config["per_round_keywords"]], root_label=f"第 {round_idx} 轮采集结果")

        round_entries = next_entries
        if not round_entries:
            stop_reason = "无新关键词"
            break

    recursive_progress.progress(100)
    if not pause_triggered:
        if not stop_reason and config["max_depth"]:
            stop_reason = "达到最大轮数"
        final_status = "stopped" if stop_reason == "无新关键词" else "success"
        finish_recursive_run(run, final_status, stop_reason)
        save_recursive_run(run)
        status_box.success("AI 递归采集流程已结束，任务日志已写入。")

    st.session_state["recursive_last_run"] = run
    st.session_state["recursive_last_result"] = {
        "status": "success" if run.get("status") in {"success", "stopped"} else "error",
        "duration_seconds": max((datetime.now() - datetime.fromisoformat(run["started_at"])).total_seconds(), 0.1),
        "estimated_results": max(total_keywords_run, 1) * config["limit_val"],
        "keyword_count": max(total_keywords_run, 1),
        "limit_val": config["limit_val"],
        "added_videos": run.get("summary", {}).get("total_videos", 0),
        "added_comments": run.get("summary", {}).get("total_comments", 0),
        "touched_files": [{"path": path, "row_delta": 0} for path in run.get("output_files", [])],
        "stdout": "\n".join(recursive_logs),
        "stderr": "",
        "platform_label": PLATFORM_OPTIONS[platform],
        "platform": platform,
    }


def render_recursive_crawl_page() -> None:
    _, initial_keywords, _ = load_keyword_library()
    current_expert = st.session_state.get("recursive_view_mode") == "expert"
    is_expert = current_expert
    keyword_runtime = {
        "keywords": list(initial_keywords),
        "keyword_count": len(initial_keywords),
    }
    config = {
        "platform": st.session_state.get("recursive_platform", "bilibili"),
        "strategy": st.session_state.get("recursive_strategy", "标准探索"),
        "mode": st.session_state.get("recursive_mode_general", "免登录"),
        "depth": st.session_state.get("recursive_depth_general", "基础采集"),
        "order_val": "totalrank",
        "limit_val": int(st.session_state.get("recursive_limit", 20)),
        "max_depth": int(st.session_state.get("recursive_depth_limit", 2)),
        "per_round_keywords": int(st.session_state.get("recursive_topk", 8)),
        "min_score": float(st.session_state.get("recursive_min_score", 3.0)),
        "stop_new_keywords": int(st.session_state.get("recursive_stop_new", 3)),
        "can_execute": bool(initial_keywords),
        "keyword_count": len(initial_keywords),
    }

    cmd_cols = st.columns([0.95, 1.0, 1.05, 1.15, 1.0, 4.85], gap="small")
    with cmd_cols[0]:
        with st.popover(t('popover.mode'), use_container_width=True):
            is_expert = st.checkbox(
                t("recursive.open_expert"),
                value=current_expert,
                key="recursive_expert_mode_enabled",
                help=t("recursive.expert_help"),
            )
    st.session_state["recursive_view_mode"] = "expert" if is_expert else "simple"
    with cmd_cols[1]:
        with st.popover(t('popover.seeds'), use_container_width=True):
            st.markdown(
                f"<div class='recursive-inline-note'>{t('recursive.seed_note', count=len(initial_keywords))}</div>",
                unsafe_allow_html=True,
            )
            keyword_runtime = render_keyword_library("recursive")
    with cmd_cols[2]:
        with st.popover(t('popover.config'), use_container_width=True):
            config = _render_recursive_config(keyword_runtime, is_expert)
            if is_expert:
                _render_search_metrics(config["platform"])
    with cmd_cols[3]:
        with st.popover(t('popover.candidates'), use_container_width=True):
            _render_candidate_panel(config, keyword_runtime, is_expert)
    with cmd_cols[4]:
        with st.popover(t('popover.history'), use_container_width=True):
            _render_history_library(is_expert)
            if st.session_state.get("recursive_last_run") and is_expert:
                st.divider()
                _render_node_detail(st.session_state["recursive_last_run"])

    run = st.session_state.get("recursive_last_run")
    result = st.session_state.get("recursive_last_result")
    nodes = run.get("nodes", []) if run else []
    rounds = run.get("rounds", []) if run else []
    candidates = collect_candidates_from_run(run) if run else []
    summary = run.get("summary", {}) if run else {}
    status = run.get("status", "waiting") if run else "waiting"
    seed_preview = list(keyword_runtime.get("keywords", initial_keywords))[:18]
    node_rows = [
        (
            f"R{node.get('round')} · {node.get('keyword', '')}",
            f"{node.get('status', '')} · {node.get('candidate_metrics', {}).get('count', 0)}",
        )
        for node in nodes[:12]
    ]
    round_rows = [
        (
            f"Round {item.get('round')}",
            f"{item.get('status', '')} · {len(item.get('keywords', []))} topics",
        )
        for item in rounds[:8]
    ]
    candidate_rows = [
        (
            str(item.get("keyword", "")),
            format_score(float(item.get("score", 0) or 0)),
        )
        for item in candidates[:10]
    ]
    seed_body = atlas_chips(seed_preview) if seed_preview else atlas_empty(t("recursive.step_seed"), t("common.empty_first_action"))
    tree_body = render_atlas_list_editor(
        t('recursive.panel.tree'),
        node_rows,
        compact=True,
        empty_title=t('recursive.panel.no_tree'),
        empty_body=t("common.empty_first_action"),
    )
    if run:
        progress_body = render_atlas_list_editor(t('recursive.drawer.timeline'), round_rows, compact=True)
    else:
        progress_body = atlas_empty(t('recursive.no_exploration'), t("recursive.subtitle"))

    scene_html = f"""
    <div class='atlas-scene-sigil'></div>
    <div class='atlas-scene-line' style='left:18%;top:58%;width:25%;transform:rotate(-25deg);'></div>
    <div class='atlas-scene-line' style='left:42%;top:44%;width:21%;transform:rotate(24deg);'></div>
    <div class='atlas-scene-line' style='left:58%;top:55%;width:23%;transform:rotate(-12deg);'></div>
    <div class='atlas-scene-line' style='left:42%;top:44%;width:18%;transform:rotate(92deg);'></div>
    <span class='atlas-scene-node' style='left:18%;top:57%;background:#5B9A6E;'></span>
    <span class='atlas-scene-node' style='left:42%;top:43%;background:#d4af37;'></span>
    <span class='atlas-scene-node' style='left:63%;top:56%;background:#9B7FD4;'></span>
    <span class='atlas-scene-node' style='left:81%;top:51%;background:#D4956B;'></span>
    <span class='atlas-scene-node' style='left:43%;top:62%;background:#6B8BDB;'></span>
    <div class='atlas-stage-map'>
      <svg viewBox='0 0 1200 720' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>
        <path class='gridline' d='M120 0V720M260 0V720M400 0V720M540 0V720M680 0V720M820 0V720M960 0V720M1100 0V720M0 120H1200M0 260H1200M0 400H1200M0 540H1200'/>
        <text x='212' y='444' font-size='14'>{t('recursive.map.seeds')} {len(seed_preview)}</text>
        <text x='506' y='326' font-size='14'>{t('recursive.map.round')} {len(rounds)}</text>
        <text x='730' y='438' font-size='14'>{t('recursive.map.nodes')} {len(nodes)}</text>
        <text x='500' y='540' font-size='13'>{t('recursive.map.candidates')} {len(candidates)}</text>
      </svg>
    </div>
    """
    panels = [
        render_atlas_panel(
            t('recursive.panel.state'),
            atlas_rows([
                (t('nav.mode'), t('label.expert') if is_expert else t('label.simple')),
                (t('crawl.row.platform'), PLATFORM_OPTIONS.get(config.get("platform"), config.get("platform", "bilibili"))),
                (t('crawl.row.status'), status),
            ], compact=True),
            kicker=t('crawl.kicker.route'),
        ),
        render_atlas_panel(t('recursive.panel.seeds'), seed_body, kicker=t('recursive.metric.seeds')),
        render_atlas_panel(t('recursive.panel.tree'), tree_body, kicker=t('recursive.metric.nodes')),
    ]
    drawers = [
        render_atlas_drawer(t('recursive.drawer.timeline'), progress_body, badge=str(len(rounds))),
        render_atlas_drawer(t('recursive.drawer.nodes'), tree_body, badge=str(len(nodes))),
        render_atlas_drawer(t('recursive.drawer.candidates'), render_atlas_list_editor(t('recursive.drawer.candidates_title'), candidate_rows, compact=True, empty_title=t('recursive.drawer.no_candidates'), empty_body=t("common.empty_first_action")), badge=str(len(candidate_rows))),
        render_atlas_drawer(t('recursive.drawer.result'), atlas_rows([
            (t('recursive.row.videos'), summary.get("total_videos", result.get("added_videos", 0) if result else 0)),
            (t('recursive.row.comments'), summary.get("total_comments", result.get("added_comments", 0) if result else 0)),
            (t('recursive.row.output'), len(run.get("output_files", [])) if run else 0),
        ], compact=True), badge=status.upper()),
    ]
    render_atlas_stage(
        page_id="recursive",
        title=t('recursive.stage.title'),
        subtitle=t("recursive.subtitle"),
        metrics=[
            (t('recursive.metric.seeds'), str(len(keyword_runtime.get("keywords", initial_keywords)))),
            (t('recursive.metric.mode'), t('label.expert') if is_expert else t('label.simple')),
            (t('recursive.metric.rounds'), str(len(rounds))),
            (t('recursive.metric.nodes'), str(len(nodes))),
        ],
        scene_html=scene_html,
        panels=panels,
        drawers=drawers,
        timeline_label=t('recursive.stage.timeline'),
        timeline_start=t('recursive.stage.start'),
        timeline_end=t('recursive.stage.end'),
        accent="#9B7FD4",
        mode_label=t('recursive.stage.mode'),
    )
