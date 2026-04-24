from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as st_components

from ui.components.common import render_page_header, render_section_title, render_data_freshness, render_kpi_card, icon
from ui.services.app_services import (
    PLATFORM_BRAND_ICONS,
    build_trending_rows_html,
    delete_all_loaded_csv_files,
    delete_loaded_csv_file,
    get_platform_stats,
    get_system_health,
    get_trending_videos,
    list_loaded_csv_files,
)
from ui.services.overview_service import (
    get_keyword_trends,
    get_top_comments,
    get_weekly_summary_text,
)


def _render_insights_hero() -> None:
    """区块 1：本周核心发现（Hero 区域）"""
    summaries = get_weekly_summary_text()
    report_icon = icon("report", color="#d4af37")

    if summaries:
        cards_html = ""
        colors = ["#d4af37", "#6B8BDB", "#D4956B", "#E85D4A", "#9B7FD4"]
        for idx, text in enumerate(summaries[:5]):
            color = colors[idx % len(colors)]
            cards_html += f"""
            <div style='padding:14px 18px; border-left:3px solid {color}; background:rgba(12,15,20,0.7);
                         border-radius:0 8px 8px 0; margin-bottom:8px; font-size:13px; color:rgba(232,228,220,0.75); line-height:1.7;'>
                {text}
            </div>"""
        st.markdown(
            f"""<div style='margin-bottom:24px;'>
                <div style='font-family:Cinzel,serif; font-size:16px; font-weight:600; color:#E8E4DC;
                            margin-bottom:14px; letter-spacing:1px;'>{report_icon} 本周核心发现</div>
                {cards_html}
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style='padding:24px; border:1px dashed rgba(180,160,120,0.15); border-radius:8px;
                        background:rgba(12,15,20,0.6); margin-bottom:24px;'>
                <div style='font-family:Cinzel,serif; font-size:15px; font-weight:600; color:rgba(232,228,220,0.5);
                            letter-spacing:1px;'>{report_icon} 暂无本周分析摘要</div>
                <div style='font-size:12px; color:rgba(232,228,220,0.3); margin-top:8px;'>
                    前往「智能报表」页面生成一份周报，系统将自动提取核心发现。</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_trends_chart() -> None:
    """区块 2：关键词搜索趋势（折线图）"""
    trend_data = get_keyword_trends(days=14)
    if not trend_data:
        return

    try:
        import pandas as pd
        import altair as alt

        df = pd.DataFrame(trend_data)
        df["date"] = pd.to_datetime(df["date"])
        top_kws = df.groupby("keyword")["total_results"].sum().nlargest(8).index.tolist()
        df_top = df[df["keyword"].isin(top_kws)]
        if df_top.empty:
            return

        trend_svg = icon("trend", color="#d4af37")
        st.markdown(f"<h3>{trend_svg} 关键词搜索趋势（近 14 天）</h3>", unsafe_allow_html=True)
        chart = (
            alt.Chart(df_top)
            .mark_line(point=alt.OverlayMarkDef(size=30), strokeWidth=1.8)
            .encode(
                x=alt.X("date:T", title="", axis=alt.Axis(format="%m-%d", labelColor="#555", gridColor="rgba(180,160,120,0.06)")),
                y=alt.Y("total_results:Q", title="", axis=alt.Axis(labelColor="#555", gridColor="rgba(180,160,120,0.06)")),
                color=alt.Color("keyword:N", title="关键词",
                    scale=alt.Scale(range=["#d4af37", "#6B8BDB", "#E85D4A", "#5B9A6E", "#9B7FD4", "#D4956B", "#7FB5B0", "#C4845C"]),
                    legend=alt.Legend(labelColor="#888", titleColor="#888")),
                tooltip=["date:T", "keyword:N", "total_results:Q"],
            )
            .properties(height=320, background="transparent")
            .configure_view(strokeWidth=0)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)
    except (ImportError, Exception):
        pass


def _render_top_comments() -> None:
    """区块 3：高赞评论精选"""
    comments = get_top_comments(limit=10)
    if not comments:
        return

    search_svg = icon("search", color="#d4af37")
    st.markdown(f"<h3>{search_svg} 高赞评论精选（近 7 天）</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(232,228,220,0.35); font-size:12px; margin-bottom:14px;'>跨平台高赞评论，展示玩家最强烈的声音。</p>", unsafe_allow_html=True)

    for c in comments:
        sentiment_badge = ""
        if c.get("sentiment") == "positive":
            sentiment_badge = "<span style='background:rgba(91,154,110,0.15); color:#5B9A6E; padding:2px 8px; border-radius:3px; font-size:10px; font-weight:600; letter-spacing:0.5px;'>POSITIVE</span>"
        elif c.get("sentiment") == "negative":
            sentiment_badge = "<span style='background:rgba(232,93,74,0.15); color:#E85D4A; padding:2px 8px; border-radius:3px; font-size:10px; font-weight:600; letter-spacing:0.5px;'>NEGATIVE</span>"

        profile_svg = icon("profile", color="rgba(232,228,220,0.3)")
        st.markdown(
            f"""<div style='background:rgba(12,15,20,0.92);border:1px solid rgba(180,160,120,0.1);border-radius:8px;padding:16px 18px;margin-bottom:8px;box-shadow:0 4px 24px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.02);'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                    <span style='font-size:10px;color:rgba(232,228,220,0.3);letter-spacing:0.5px;'>{profile_svg}
                        {c.get('author', '匿名')} · {c.get('platform', '')} · {c.get('like_count', 0)} likes</span>
                    {sentiment_badge}
                </div>
                <div style='font-size:12px;color:rgba(232,228,220,0.7);line-height:1.7;'>{c.get('content', '')}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_overview_page() -> None:
    render_page_header("总览", "实时监控数据汇总与核心洞察")
    _render_insights_hero()

    # 系统运行概况 KPI
    target_svg = icon("target", color="#d4af37")
    st.markdown(f"<h3>{target_svg} 系统运行概况</h3>", unsafe_allow_html=True)
    health = get_system_health()
    api_color = "#5B9A6E" if health["api_health"] else "#E85D4A"
    api_text = "在线" if health["api_health"] else "未配置"
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(render_kpi_card("监控目标", f"{health['targets']}频道 · {health['keywords']}词"), unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(render_kpi_card("本地数据量", f"{health['capacity']} 组", "#6B8BDB"), unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(render_kpi_card("LLM 分析引擎", api_text, api_color), unsafe_allow_html=True)
    with kpi_cols[3]:
        st.markdown(render_kpi_card("最近采集", health['last_sync'], "#D4956B"), unsafe_allow_html=True)

    _render_trends_chart()

    st.markdown("<br/>", unsafe_allow_html=True)
    db_svg = icon("database", color="#d4af37")
    st.markdown(f"<h3>{db_svg} 平台数据概览</h3>", unsafe_allow_html=True)

    platform_data = [
        ("bilibili", "哔哩哔哩"), ("youtube", "YouTube"), ("taptap", "TapTap"),
        ("douyin", "抖音"), ("kuaishou", "快手"), ("xiaohongshu", "小红书"),
    ]
    for row_idx in range(0, len(platform_data), 3):
        cols = st.columns(3)
        for col_idx, (platform_id, platform_label) in enumerate(platform_data[row_idx : row_idx + 3]):
            stats = get_platform_stats(platform_id)
            with cols[col_idx]:
                delta_color = "#5B9A6E" if (stats["videos_today"] or stats["comments_today"]) else "rgba(232,228,220,0.25)"
                st.markdown(
                    f"""<div style='background:rgba(12,15,20,0.92);border:1px solid rgba(180,160,120,0.15);border-radius:8px;padding:20px;min-height:140px;margin-bottom:14px;box-shadow:0 4px 24px rgba(0,0,0,.4),0 1px 2px rgba(0,0,0,.2),inset 0 1px 0 rgba(255,255,255,.03);'>
                        <div style='display:flex;align-items:center;margin-bottom:40px;'>
                            <img style='width:16px;height:16px;margin-right:8px;border-radius:2px;opacity:0.7;'
                                 src='{PLATFORM_BRAND_ICONS.get(platform_id, "")}' alt=''>
                            <span style='font-family:IBM Plex Sans,sans-serif;font-size:10px;font-weight:600;color:rgba(232,228,220,0.4);text-transform:uppercase;letter-spacing:1.2px;'>{platform_label}</span>
                        </div>
                        <div style='font-family:IBM Plex Mono,monospace;font-size:28px;font-weight:500;color:#E8E4DC;line-height:1;'>{stats["videos_total"] if stats["videos_total"] else 0}</div>
                        <div style='display:inline-flex;align-items:center;margin-top:18px;padding:5px 10px;
                                    border-radius:999px;background:rgba(91,154,110,0.06);border:1px solid rgba(91,154,110,0.1);
                                    color:{delta_color};font-size:11px;font-weight:500;'>
                            今日 +{stats["videos_today"]} 视频,+{stats["comments_today"]} 评论</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # 高赞评论
    st.markdown("<hr style='border:none; border-top:1px solid rgba(180,160,120,0.08); margin:2rem 0;'/>", unsafe_allow_html=True)
    _render_top_comments()

    render_data_freshness()

    # 热点内容追踪
    st.markdown("<hr style='border:none; border-top:1px solid rgba(180,160,120,0.08); margin:2rem 0;'/>", unsafe_allow_html=True)
    trend_svg = icon("trend", color="#d4af37")
    render_section_title(f"{trend_svg} 热点内容追踪", "近期跨平台表现突出的内容")
    _, ctrl_col = st.columns([8, 2])
    with ctrl_col:
        view_limit = st.selectbox("单屏显示限额", [10, 20, 50, 100, 300, 500], index=0, label_visibility="collapsed")

    trending = get_trending_videos(view_limit)
    if trending:
        all_rows = build_trending_rows_html(trending)
        table_doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ font-family:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,sans-serif; background:#0A0C10; color:#E8E4DC; }}
            table {{ width:100%; border-collapse:collapse; font-size:12px; }}
            thead tr {{ background:rgba(180,160,120,0.06); border-bottom:1px solid rgba(180,160,120,0.12); }}
            th {{ padding:10px 12px; font-size:10px; font-weight:600; color:rgba(232,228,220,0.4);
                  text-align:left; white-space:nowrap; text-transform:uppercase; letter-spacing:0.8px; }}
            th.right {{ text-align:right; }}
            td {{ padding:12px 12px; border-bottom:1px solid rgba(180,160,120,0.05); vertical-align:middle; color:rgba(232,228,220,0.7); }}
            tr:hover td {{ background:rgba(180,160,120,0.04); }}
            td.num {{ color:rgba(232,228,220,0.3); font-size:11px; text-align:center; width:28px; }}
            td.player-cell {{ width:172px; padding:10px 8px; vertical-align:middle; }}
            td.title-cell {{ min-width:180px; padding:10px 12px; }}
            td.title-cell a {{ font-weight:600; color:#E8E4DC; text-decoration:none; line-height:1.5; display:block; }}
            td.title-cell a:hover {{ color:#d4af37; }}
            td.stat {{ text-align:right; font-family:'IBM Plex Mono',monospace; font-weight:500; white-space:nowrap; color:rgba(232,228,220,0.6); }}
            td.muted {{ color:rgba(232,228,220,0.3); font-size:11px; }}
            .author {{ display:block; font-size:10px; color:rgba(232,228,220,0.35); margin-top:4px; }}
            .pfav {{ width:12px; height:12px; vertical-align:middle; margin-right:4px; opacity:0.6; }}
            .tags {{ display:flex; flex-wrap:wrap; gap:3px; margin-top:6px; }}
            .tag {{ display:inline-block; padding:2px 6px; border-radius:3px; font-size:10px;
                    background:rgba(180,160,120,0.08); color:rgba(232,228,220,0.45); white-space:nowrap;
                    border:1px solid rgba(180,160,120,0.08); }}
            .tag-hit {{ background:rgba(180,160,120,0.15); color:#d4af37; font-weight:600; border-color:rgba(180,160,120,0.2); }}
        </style></head><body>
        <table>
            <thead><tr>
                <th>#</th><th>视频</th><th>视频标题</th>
                <th class="right">播放</th><th class="right">点赞</th>
                <th class="right">评论</th><th class="right">收藏</th>
                <th class="right">分享</th><th class="right">投币</th>
                <th class="right">弹幕</th><th class="right">发布日</th>
            </tr></thead>
            <tbody>{all_rows}</tbody>
        </table>
        </body></html>"""
        st_components.html(table_doc, height=900, scrolling=True)
    else:
        st.markdown("<p style='color:rgba(232,228,220,0.35); font-size:13px;'>当前采集库中暂未发现内容，请先执行采集。</p>", unsafe_allow_html=True)

    # 底层源文件管理
    st.markdown("<hr style='border:none; border-top:1px solid rgba(180,160,120,0.08); margin:2rem 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3>当前已加载采集数据</h3>", unsafe_allow_html=True)

    loaded_files = list_loaded_csv_files()
    if not loaded_files:
        st.markdown("<p style='color:rgba(232,228,220,0.3); font-size:12px;'>当前还没有已加载的数据文件。</p>", unsafe_allow_html=True)
        return

    @st.dialog("危险操作确认")
    def confirm_clear_all() -> None:
        st.warning("确定要彻底清空所有收集到的历史数据吗？此操作不可逆！")
        c1, c2 = st.columns(2)
        if c1.button("确认清空", type="primary", use_container_width=True):
            delete_all_loaded_csv_files()
            st.rerun()
        if c2.button("取消", use_container_width=True):
            st.rerun()

    _, action_col = st.columns([9, 2])
    with action_col:
        if st.button("删除全部", type="primary", use_container_width=True):
            confirm_clear_all()

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    for item in loaded_files:
        col1, col2, col3 = st.columns([6, 3, 2])
        with col1:
            st.markdown(item["display_html"], unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='font-size:11px; color:rgba(232,228,220,0.3); padding-top:10px;'>{item['size_kb']:.1f} KB</div>", unsafe_allow_html=True)
        with col3:
            if st.button("删除", key=f"del_{item['path']}"):
                try:
                    delete_loaded_csv_file(item["path"])
                    st.rerun()
                except Exception:
                    st.error("删除受阻")
