from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as st_components

from ui.components.common import render_page_header, render_section_title, render_data_freshness
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

    if summaries:
        cards_html = ""
        colors = ["#16a34a", "#2563eb", "#d97706", "#dc2626", "#7c3aed"]
        for idx, text in enumerate(summaries[:5]):
            color = colors[idx % len(colors)]
            cards_html += f"""
            <div style='padding:14px 16px; border-left:3px solid {color}; background:#FAFAFA;
                         border-radius:0 8px 8px 0; margin-bottom:8px; font-size:14px; color:#111; line-height:1.6;'>
                {text}
            </div>"""
        st.markdown(
            f"""<div style='margin-bottom:24px;'>
                <div style='font-size:18px; font-weight:700; color:#111; margin-bottom:12px;'>📋 本周核心发现</div>
                {cards_html}
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div style='padding:20px; border:1px dashed #D4D4D4; border-radius:8px; background:#FCFCFC; margin-bottom:24px;'>
                <div style='font-size:15px; font-weight:600; color:#666;'>📋 暂无本周分析摘要</div>
                <div style='font-size:13px; color:#999; margin-top:6px;'>请先前往「智能报表」页面生成一份周报，系统将自动提取核心发现。</div>
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

        # 取搜索量最大的 Top 8 关键词
        top_kws = df.groupby("keyword")["total_results"].sum().nlargest(8).index.tolist()
        df_top = df[df["keyword"].isin(top_kws)]

        if df_top.empty:
            return

        chart = (
            alt.Chart(df_top)
            .mark_line(point=True, strokeWidth=2)
            .encode(
                x=alt.X("date:T", title="日期", axis=alt.Axis(format="%m-%d")),
                y=alt.Y("total_results:Q", title="搜索结果总量"),
                color=alt.Color("keyword:N", title="关键词"),
                tooltip=["date:T", "keyword:N", "total_results:Q"],
            )
            .properties(height=320)
            .interactive()
        )
        st.markdown("<h3>关键词搜索趋势（近 14 天）</h3>", unsafe_allow_html=True)
        st.altair_chart(chart, use_container_width=True)
    except ImportError:
        pass
    except Exception:
        pass


def _render_top_comments() -> None:
    """区块 3：高赞评论精选"""
    comments = get_top_comments(limit=10)
    if not comments:
        return

    st.markdown("<h3>高赞评论精选（近 7 天）</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:13px; margin-bottom:12px;'>跨平台高赞评论，展示玩家最强烈的声音。</p>", unsafe_allow_html=True)

    for idx, c in enumerate(comments):
        sentiment_badge = ""
        if c.get("sentiment") == "positive":
            sentiment_badge = "<span style='background:#DCFCE7; color:#16a34a; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;'>正面</span>"
        elif c.get("sentiment") == "negative":
            sentiment_badge = "<span style='background:#FEE2E2; color:#dc2626; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;'>负面</span>"

        st.markdown(
            f"""<div style='padding:12px 16px; border:1px solid #EAEAEA; border-radius:8px; margin-bottom:8px; background:#FFFFFF;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>
                    <span style='font-size:12px; color:#666;'>👤 {c.get('author', '匿名')} · {c.get('platform', '')} · 👍 {c.get('like_count', 0)}</span>
                    {sentiment_badge}
                </div>
                <div style='font-size:14px; color:#111; line-height:1.6;'>{c.get('content', '')}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_overview_page() -> None:
    render_page_header("总览", "实时监控数据汇总与核心洞察")
    # 区块 0：本周核心发现
    _render_insights_hero()

    # 系统运行概况 KPI
    st.markdown("<h3>系统运行概况</h3>", unsafe_allow_html=True)
    health = get_system_health()
    st.markdown(
        f"""
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px;'>
            <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
                <div style='font-size:12px; color:#666;'>监控目标数量</div>
                <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['targets']}<span style='font-size:12px; font-weight:400; color:#666; margin:0 4px;'>频道，</span>{health['keywords']}<span style='font-size:12px; font-weight:400; color:#666; margin-left:4px;'>关键词</span></div>
                <div style='font-size:11px; color:#999; margin-top:4px;'>覆盖当前已配置的重点监测对象</div>
            </div>
            <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
                <div style='font-size:12px; color:#666;'>本地总数据量</div>
                <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['capacity']} <span style='font-size:12px; font-weight:400; color:#666;'>组</span></div>
                <div style='font-size:11px; color:#999; margin-top:4px;'>包含全平台的视频与评论快照</div>
            </div>
            <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
                <div style='font-size:12px; color:#666;'>舆情分析组件 (LLM)</div>
                <div style='font-size:24px; font-weight:700; color:{"#16a34a" if health["api_health"] else "#dc2626"}; margin-top:8px;'>{"连接正常" if health["api_health"] else "未配置"}</div>
                <div style='font-size:11px; color:#999; margin-top:4px;'>用于支撑深度的语义总结与报告生成</div>
            </div>
            <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
                <div style='font-size:12px; color:#666;'>最近一次采集</div>
                <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['last_sync']}</div>
                <div style='font-size:11px; color:#999; margin-top:4px;'>系统最后一次成功抓取并落库的时间</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 区块 1：关键词趋势图
    _render_trends_chart()

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<h3>平台数据概览</h3>", unsafe_allow_html=True)

    platform_data = [
        ("bilibili", "哔哩哔哩"),
        ("youtube", "YouTube"),
        ("taptap", "TapTap"),
        ("douyin", "抖音"),
        ("kuaishou", "快手"),
        ("xiaohongshu", "小红书"),
    ]
    for row_idx in range(0, len(platform_data), 3):
        cols = st.columns(3)
        for col_idx, (platform_id, platform_label) in enumerate(platform_data[row_idx : row_idx + 3]):
            stats = get_platform_stats(platform_id)
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div class="platform-stat-card">
                        <div class="platform-stat-card__header">
                            <img class="platform-icon" src="{PLATFORM_BRAND_ICONS.get(platform_id, '')}" alt="">
                            <span class="platform-stat-card__label">{platform_label}</span>
                        </div>
                        <div class="platform-stat-card__value">{stats["videos_total"] if stats["videos_total"] else 0}</div>
                        <div class="platform-stat-card__delta">↑ 今日新增: {stats["videos_today"]} 视频, {stats["comments_today"]} 评论</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 区块 2：高赞评论精选
    st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:2rem 0;'/>", unsafe_allow_html=True)
    _render_top_comments()

    # 热点内容追踪
    st.markdown("<hr style='border: none; border-top: 1px solid #EAEAEA; margin: 2rem 0;'/>", unsafe_allow_html=True)
    render_section_title("热点内容追踪", "展示近期跨平台表现突出的内容，便于跟踪热点话题和高关注素材。")
    _, ctrl_col = st.columns([8, 2])
    with ctrl_col:
        view_limit = st.selectbox("单屏显示限额", [10, 20, 50, 100, 300, 500], index=0, label_visibility="collapsed")

    trending = get_trending_videos(view_limit)
    if trending:
        all_rows = build_trending_rows_html(trending)
        table_doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ font-family: -apple-system,'Inter',BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#fff; }}
            table {{ width:100%; border-collapse:collapse; font-size:13px; }}
            thead tr {{ background:#FAFAFA; border-bottom:2px solid #EAEAEA; }}
            th {{ padding:10px 12px; font-size:12px; font-weight:600; color:#666; text-align:left; white-space:nowrap; }}
            th.right {{ text-align:right; }}
            td {{ padding:12px 12px; border-bottom:1px solid #F0F0F0; vertical-align:middle; }}
            tr:hover td {{ background:#FAFAFA; }}
            td.num {{ color:#999; font-size:12px; text-align:center; width:28px; }}
            td.player-cell {{ width:172px; padding:10px 8px; vertical-align:middle; }}
            td.title-cell {{ min-width:180px; padding:10px 12px; }}
            td.title-cell a {{ font-weight:600; color:#111; text-decoration:none; line-height:1.5; display:block; }}
            td.title-cell a:hover {{ color:#1d4ed8; }}
            td.stat {{ text-align:right; font-weight:500; white-space:nowrap; color:#333; }}
            td.muted {{ color:#999; font-size:12px; }}
            .author {{ display:block; font-size:11px; color:#888; margin-top:4px; }}
            .pfav {{ width:12px; height:12px; vertical-align:middle; margin-right:4px; }}
            .tags {{ display:flex; flex-wrap:wrap; gap:3px; margin-top:6px; }}
            .tag {{ display:inline-block; padding:2px 6px; border-radius:3px; font-size:11px; background:#F5F5F5; color:#666; white-space:nowrap; }}
            .tag-hit {{ background:#EEF2FF; color:#4338CA; font-weight:600; }}
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
        st.markdown("<p style='color:#666; font-size:14px;'>当前采集库中暂未发现内容，请先执行策略采集。</p>", unsafe_allow_html=True)

    # 底层源文件管理
    st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:2rem 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3>当前已加载采集数据 (底层源文件)</h3>", unsafe_allow_html=True)

    loaded_files = list_loaded_csv_files()
    if not loaded_files:
        st.markdown("<p style='color:#999; font-size:13px;'>当前还没有已加载的数据文件，请先执行采集。</p>", unsafe_allow_html=True)
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

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
    for item in loaded_files:
        col1, col2, col3 = st.columns([6, 3, 2])
        with col1:
            st.markdown(item["display_html"], unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='font-size:12px; color:#64748b; padding-top:10px;'>{item['size_kb']:.1f} KB</div>", unsafe_allow_html=True)
        with col3:
            if st.button("删除", key=f"del_{item['path']}"):
                try:
                    delete_loaded_csv_file(item["path"])
                    st.rerun()
                except Exception:
                    st.error("删除受阻")
