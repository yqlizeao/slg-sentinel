from __future__ import annotations

from datetime import datetime

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
from ui.components.common import render_atlas_ops_board, render_page_header
from ui.components.crawl import (
    render_crawl_result_card,
    render_keyword_library,
    render_step_block_header,
    render_step_overview,
)
from ui.i18n import t
from ui.services.app_services import (
    PLATFORM_OPTIONS,
    estimate_remaining_seconds,
    get_crawl_file_snapshot,
    init_crawl_progress_state,
    load_keyword_library,
    media_crawler_exists,
    run_cli_stream,
    summarize_crawl_result,
    update_crawl_progress_state,
)


def _render_platform_field_tables(platform: str, mode: str, depth: str) -> None:
    matrix_html_base = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        html, body { width:100%; max-width:100%; overflow-x:hidden; }
        body { font-family:'IBM Plex Sans',-apple-system,sans-serif; background:#0A0C10; color:#E8E4DC; padding:0; }
        table { width:100%; max-width:100%; table-layout:fixed; border-collapse:collapse; font-size:12px; border:1px solid rgba(180,160,120,0.12); border-radius:8px; overflow:hidden; }
        thead tr { background:rgba(180,160,120,0.06); border-bottom:1px solid rgba(180,160,120,0.12); }
        th { padding:10px 12px; font-size:10px; font-weight:600; color:rgba(232,228,220,0.4); text-align:left; text-transform:uppercase; letter-spacing:0.8px; word-break:break-word; }
        td { padding:10px 12px; border-bottom:1px solid rgba(180,160,120,0.05); vertical-align:middle; font-size:12px; color:rgba(232,228,220,0.7); word-break:break-word; overflow-wrap:anywhere; }
        tr:last-child td { border-bottom:none; }
        tr:hover td { background:rgba(180,160,120,0.04); }
        .status { display:inline-flex; align-items:center; gap:6px; flex-wrap:wrap; }
        .dot { display:inline-block; width:8px; height:8px; border-radius:50%; flex:0 0 8px; }
        .dot-g { background:#5B9A6E; }
        .dot-r { background:#E85D4A; }
        .g { color:#5B9A6E; font-weight:600; }
        .r { color:#E85D4A; font-weight:600; }
        code { background:rgba(180,160,120,0.1); padding:2px 6px; border-radius:3px; font-family:'IBM Plex Mono',monospace; font-size:10px; color:#d4af37; word-break:break-all; display:inline-block; max-width:100%; white-space:normal; }
        .desc { font-size:11px; color:rgba(232,228,220,0.4); }
    </style></head><body>
    <table>
        <thead><tr>
            <th style="width:22%">属性</th>
            <th style="width:30%">数据来源</th>
            <th style="width:24%">业务价值</th>
            <th style="width:24%">当前可见范围</th>
        </tr></thead>
        <tbody>"""

    green_status = lambda text: f"<span class='status'><span class='dot dot-g'></span><span class='g'>{text}</span></span>"
    red_status = lambda text: f"<span class='status'><span class='dot dot-r'></span><span class='r'>{text}</span></span>"

    if platform == "bilibili":
        comp_title = "采集引擎：<a href='https://github.com/Nemo2011/bilibili-api' target='_blank' style='color:#d4af37; text-decoration:none; font-family:IBM Plex Mono,monospace; font-weight:600;'>bilibili-api-python</a>"
        iframe_height = 580
        is_simple = "基础" in depth
        is_basic = "免登录" in mode
        sess_status = green_status("可获取")
        deep_status = green_status("基础模式可获取") if is_basic else green_status("鉴权模式可获取")
        api_call = "<code>search.search_by_type()</code>" if is_simple else "<code>video.Video().get_info()</code>"
        b_coin_status = red_status("基础搜索不返回") if is_simple else deep_status
        cmt_status = red_status("当前模式不可获取") if is_basic else green_status("鉴权后可获取")
        fav_status = red_status("需鉴权且用户公开") if is_basic else green_status("用户公开时可获取")
        follow_status = red_status("需切换鉴权模式") if is_basic else green_status("可获取")
        rows = f"""
        <tr><td>BV号 (ID)</td><td><code>search.search_by_type()</code></td><td class="desc">用于唯一定位内容</td><td>{sess_status}</td></tr>
        <tr><td>视频标题 (Title)</td><td><code>search.search_by_type()</code></td><td class="desc">用于判断题材与关键词相关性</td><td>{sess_status}</td></tr>
        <tr><td>UP主名称 (Author)</td><td><code>search.search_by_type()</code></td><td class="desc">用于识别重点创作者与渠道</td><td>{sess_status}</td></tr>
        <tr><td>发布日期 (Pubdate)</td><td><code>search.search_by_type()</code></td><td class="desc">用于界定分析周期</td><td>{sess_status}</td></tr>
        <tr><td>播放量 (View)</td><td>{api_call}</td><td class="desc">用于判断内容曝光规模</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>点赞数 (Like)</td><td>{api_call}</td><td class="desc">用于衡量内容正向反馈</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>投币数 (Coin)</td><td>{api_call}</td><td class="desc">用于识别高认可度内容</td><td>{b_coin_status}</td></tr>
        <tr><td>收藏数 (Favorite)</td><td>{api_call}</td><td class="desc">用于观察长期关注意愿</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>分享数 (Share)</td><td>{api_call}</td><td class="desc">用于判断传播扩散能力</td><td>{b_coin_status}</td></tr>
        <tr><td>评论者 UID</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于后续用户画像与溯源</td><td>{cmt_status}</td></tr>
        <tr><td>评论内容纯文本</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于情感与话题分析</td><td>{cmt_status}</td></tr>
        <tr><td>被点赞数 (Like)</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于识别高影响评论</td><td>{cmt_status}</td></tr>
        <tr><td>公开收藏夹</td><td><code>get_video_favorite_list(uid)</code></td><td class="desc">用于辅助判断用户偏好</td><td>{fav_status}</td></tr>
        <tr><td>关注关系链</td><td><code>API /x/relation/followings</code></td><td class="desc">用于识别关联账号与兴趣重合</td><td>{follow_status}</td></tr>"""
    elif platform == "youtube":
        comp_title = "采集引擎：<a href='https://github.com/yt-dlp/yt-dlp' target='_blank' style='color:#d4af37; text-decoration:none; font-family:IBM Plex Mono,monospace; font-weight:600;'>yt-dlp</a> · <a href='https://github.com/dermasmid/scrapetube' target='_blank' style='color:#d4af37; text-decoration:none; font-family:IBM Plex Mono,monospace; font-weight:600;'>scrapetube</a> · <a href='https://github.com/egbertbouman/youtube-comment-downloader' target='_blank' style='color:#d4af37; text-decoration:none; font-family:IBM Plex Mono,monospace; font-weight:600;'>yt-cmt-dl</a>"
        iframe_height = 540
        ok_status = green_status("可获取")
        rows = f"""
        <tr><td>视频 ID (videoId)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">用于唯一定位内容</td><td>{ok_status}</td></tr>
        <tr><td>视频标题 (Title)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">用于识别内容主题</td><td>{ok_status}</td></tr>
        <tr><td>所属频道 (Channel)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">用于识别重点创作者</td><td>{ok_status}</td></tr>
        <tr><td>下辖视频列表</td><td><code>scrapetube.get_channel()</code></td><td class="desc">用于补充频道维度内容</td><td>{ok_status}</td></tr>
        <tr><td>基础发布日期</td><td><code>scrapetube.get_channel()</code></td><td class="desc">用于筛选分析周期</td><td>{ok_status}</td></tr>
        <tr><td>基础播放量</td><td><code>scrapetube.get_channel()</code></td><td class="desc">用于快速识别高热内容</td><td>{ok_status}</td></tr>
        <tr><td>精准真播放 (viewCount)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">用于评估真实曝光规模</td><td>{ok_status}</td></tr>
        <tr><td>精准点赞数 (likeCount)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">用于判断正向反馈强度</td><td>{ok_status}</td></tr>
        <tr><td>视频受众标签 (Tags)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">用于提取话题标签与语义线索</td><td>{ok_status}</td></tr>
        <tr><td>网民 ID 与昵称</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于追踪高价值评论用户</td><td>{ok_status}</td></tr>
        <tr><td>高价值点赞数</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于识别高影响评论</td><td>{ok_status}</td></tr>
        <tr><td>详细发送时间戳</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于判断讨论时效性</td><td>{ok_status}</td></tr>
        <tr><td>评论完整纯文本</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于情感与主题分析</td><td>{ok_status}</td></tr>"""
    elif platform == "taptap":
        comp_title = "采集引擎：<span style='font-family:IBM Plex Mono,monospace; font-weight:600; color:#d4af37; background:rgba(180,160,120,0.1); padding:4px 8px; border-radius:4px;'>自有协议解析引擎</span>"
        iframe_height = 400
        ok_status = green_status("可获取")
        rows = f"""
        <tr><td>核心星评 (1-5星)</td><td><code>API /v2/review/thread</code></td><td class="desc">用于观察口碑趋势</td><td>{ok_status}</td></tr>
        <tr><td>测评明文大段内容</td><td><code>API /v2/review/thread</code></td><td class="desc">用于分析深度反馈</td><td>{ok_status}</td></tr>
        <tr><td>社区支持度 (ups)</td><td><code>API /v2/review/thread</code></td><td class="desc">用于判断观点共鸣度</td><td>{ok_status}</td></tr>
        <tr><td>社区反对数 (downs)</td><td><code>API /v2/review/thread</code></td><td class="desc">用于识别争议反馈</td><td>{ok_status}</td></tr>
        <tr><td>发帖物理设备名</td><td><code>API /v2/review/thread</code></td><td class="desc">用于辅助判断设备分布</td><td>{ok_status}</td></tr>
        <tr><td>硬核游玩时长</td><td><code>API /v2/review/thread</code></td><td class="desc">用于区分轻度与重度玩家</td><td>{ok_status}</td></tr>
        <tr><td>网民专属 UID</td><td><code>API /v2/review/thread</code></td><td class="desc">用于后续用户维度分析</td><td>{ok_status}</td></tr>
        <tr><td>玩家曾游玩游戏库</td><td><code>API /v2/game/games</code></td><td class="desc">用于识别用户偏好结构</td><td>{ok_status}</td></tr>
        <tr><td>外部竞品评价横比</td><td><code>API /v2/game/games</code></td><td class="desc">用于对比竞品体验路径</td><td>{ok_status}</td></tr>"""
    else:
        comp_title = "采集引擎：<a href='https://github.com/NanmiCoder/MediaCrawler' target='_blank' style='color:#d4af37; text-decoration:none; font-family:IBM Plex Mono,monospace; font-weight:600;'>MediaCrawler</a> 本地桥接"
        iframe_height = 480
        local_auth_status = green_status("本地授权后可获取")
        rows = f"""
        <tr><td>帖子/视频 ID</td><td><code>MediaCrawler (aweme_id)</code></td><td class="desc">用于唯一定位内容</td><td>{local_auth_status}</td></tr>
        <tr><td>视频文案标题 (Title)</td><td><code>MediaCrawler (desc)</code></td><td class="desc">用于识别内容主题</td><td>{local_auth_status}</td></tr>
        <tr><td>创作者名称 (Author)</td><td><code>MediaCrawler (nickname)</code></td><td class="desc">用于判断内容来源</td><td>{local_auth_status}</td></tr>
        <tr><td>短片真实播放量</td><td><code>MediaCrawler (play_count)</code></td><td class="desc">用于判断内容传播规模</td><td>{local_auth_status}</td></tr>
        <tr><td>核心点赞数 (like)</td><td><code>MediaCrawler (like_count)</code></td><td class="desc">用于观察正向反馈</td><td>{local_auth_status}</td></tr>
        <tr><td>二次分享转发量</td><td><code>MediaCrawler (share_count)</code></td><td class="desc">用于判断扩散能力</td><td>{local_auth_status}</td></tr>
        <tr><td>私域背书收藏数</td><td><code>MediaCrawler (collect)</code></td><td class="desc">用于观察长期关注意愿</td><td>{local_auth_status}</td></tr>
        <tr><td>内容定向算法标签</td><td><code>MediaCrawler (tags)</code></td><td class="desc">用于提取平台标签线索</td><td>{local_auth_status}</td></tr>
        <tr><td>评论者 ID (user_id)</td><td><code>MediaCrawler (comments)</code></td><td class="desc">用于用户维度分析</td><td>{local_auth_status}</td></tr>
        <tr><td>神评文本明文</td><td><code>MediaCrawler (text)</code></td><td class="desc">用于情感与话题分析</td><td>{local_auth_status}</td></tr>
        <tr><td>网民 IP 物理归属</td><td><code>MediaCrawler (ip_location)</code></td><td class="desc">用于观察地域分布</td><td>{local_auth_status}</td></tr>"""

    st.markdown(
        f"<div style='margin-top:1.5rem; margin-bottom:8px; display:flex; justify-content:space-between; align-items:flex-end;'><div><p style='font-size:13px; color:#E8E4DC; font-weight:600; margin:0; letter-spacing:0.5px;'>当前平台字段说明</p></div><div style='font-size:11px; color:rgba(232,228,220,0.4);'>{comp_title}</div></div>",
        unsafe_allow_html=True,
    )
    st_components.html(matrix_html_base + rows + "</tbody></table></body></html>", height=iframe_height, scrolling=False)

    st.markdown("<hr style='border:none; border-top:1px solid rgba(180,160,120,0.08); margin:1.5rem 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3>用户数据可访问性说明</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(232,228,220,0.35); font-size:12px; margin-bottom:0.8rem;'>各平台用户维度数据的公开程度与采集可行性总览。</p>", unsafe_allow_html=True)
    privacy_matrix_html = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        html, body { width:100%; max-width:100%; overflow-x:hidden; }
        body { font-family:'IBM Plex Sans',-apple-system,sans-serif; background:#0A0C10; color:#E8E4DC; padding:0; }
        table { width:100%; max-width:100%; table-layout:fixed; border-collapse:collapse; font-size:11px; }
        thead tr { background:rgba(180,160,120,0.08); }
        th { padding:8px 8px; font-size:9px; font-weight:600; color:rgba(232,228,220,0.4); text-align:left; text-transform:uppercase; letter-spacing:0.6px; word-break:break-word; }
        th:first-child { width:18%; }
        th:not(:first-child) { width:13.6%; }
        td { padding:8px 8px; border-bottom:1px solid rgba(180,160,120,0.05); vertical-align:middle; font-size:11px; color:rgba(232,228,220,0.65); word-break:break-word; }
        tr:last-child td { border-bottom:none; }
        tr:hover td { background:rgba(180,160,120,0.04); }
        td:first-child { font-weight:600; color:rgba(232,228,220,0.85); }
        .r { color:#E85D4A; } .y { color:#D4956B; } .g { color:#5B9A6E; }
        .dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; vertical-align:middle; }
        .dot-r { background:#E85D4A; } .dot-y { background:#D4956B; } .dot-g { background:#5B9A6E; }
        .na { color:rgba(232,228,220,0.22); font-size:10px; }
    </style></head><body>
    <table>
        <thead><tr><th>数据类型</th><th>B站</th><th>抖音</th><th>快手</th><th>小红书</th><th>TapTap</th><th>YouTube</th></tr></thead>
        <tbody>
        <tr><td>浏览记录</td><td><span class="dot dot-r"></span><span class="r">私有</span></td><td><span class="dot dot-r"></span><span class="r">私有</span></td><td><span class="dot dot-r"></span><span class="r">私有</span></td><td><span class="dot dot-r"></span><span class="r">私有</span></td><td><span class="dot dot-r"></span><span class="r">私有</span></td><td><span class="dot dot-r"></span><span class="r">私有</span></td></tr>
        <tr><td>收藏夹</td><td><span class="dot dot-y"></span><span class="y">用户设公开时可见</span></td><td><span class="dot dot-r"></span><span class="r">默认私密</span></td><td><span class="dot dot-r"></span><span class="r">默认私密</span></td><td><span class="dot dot-y"></span><span class="y">部分可见</span></td><td class="na">N/A</td><td><span class="dot dot-r"></span><span class="r">私有</span></td></tr>
        <tr><td>点赞/喜欢列表</td><td><span class="dot dot-r"></span><span class="r">仅自己可见</span></td><td><span class="dot dot-y"></span><span class="y">用户可选公开/私密</span></td><td><span class="dot dot-y"></span><span class="y">用户可选</span></td><td><span class="dot dot-y"></span><span class="y">部分可见</span></td><td class="na">N/A</td><td><span class="dot dot-r"></span><span class="r">私有</span></td></tr>
        <tr><td>关注列表</td><td><span class="dot dot-g"></span><span class="g">公开（需Cookie）</span></td><td><span class="dot dot-y"></span><span class="y">用户可选</span></td><td><span class="dot dot-y"></span><span class="y">用户可选</span></td><td><span class="dot dot-y"></span><span class="y">部分可见</span></td><td><span class="dot dot-g"></span><span class="g">公开</span></td><td><span class="dot dot-g"></span><span class="g">默认私有</span></td></tr>
        <tr><td>发布内容/评论</td><td><span class="dot dot-g"></span><span class="g">公开</span></td><td><span class="dot dot-g"></span><span class="g">公开</span></td><td><span class="dot dot-g"></span><span class="g">公开</span></td><td><span class="dot dot-g"></span><span class="g">公开</span></td><td><span class="dot dot-g"></span><span class="g">公开</span></td><td><span class="dot dot-g"></span><span class="g">公开</span></td></tr>
        <tr><td>玩过的游戏列表</td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td><td><span class="dot dot-g"></span><span class="g">公开</span></td><td class="na">N/A</td></tr>
        </tbody>
    </table></body></html>"""
    st_components.html(privacy_matrix_html, height=290, scrolling=False)

    st.markdown("<h3>视频指标可采集范围</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(232,228,220,0.35); font-size:12px; margin-bottom:0.8rem;'>各平台视频/内容维度指标的可用性与对应字段名。</p>", unsafe_allow_html=True)
    metrics_matrix_html = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        html, body { width:100%; max-width:100%; overflow-x:hidden; }
        body { font-family:'IBM Plex Sans',-apple-system,sans-serif; background:#0A0C10; color:#E8E4DC; padding:0; }
        table { width:100%; max-width:100%; table-layout:fixed; border-collapse:collapse; font-size:11px; }
        thead tr { background:rgba(180,160,120,0.08); }
        th { padding:8px 8px; font-size:9px; font-weight:600; color:rgba(232,228,220,0.4); text-align:left; text-transform:uppercase; letter-spacing:0.6px; word-break:break-word; }
        th:first-child { width:14%; }
        th:not(:first-child) { width:14.3%; }
        td { padding:8px 8px; border-bottom:1px solid rgba(180,160,120,0.05); vertical-align:middle; font-size:11px; color:rgba(232,228,220,0.65); word-break:break-word; }
        tr:last-child td { border-bottom:none; }
        tr:hover td { background:rgba(180,160,120,0.04); }
        td:first-child { font-weight:600; color:rgba(232,228,220,0.85); }
        .g { color:#5B9A6E; }
        .dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; vertical-align:middle; }
        .dot-g { background:#5B9A6E; }
        .na { color:rgba(232,228,220,0.22); font-size:10px; }
        code { background:rgba(91,154,110,0.12); color:#5B9A6E; font-size:9px; padding:1px 4px; border-radius:3px; font-family:'IBM Plex Mono',monospace; font-weight:600; word-break:break-all; display:inline-block; max-width:100%; }
    </style></head><body>
    <table>
        <thead><tr><th>指标</th><th>B站</th><th>抖音</th><th>快手</th><th>小红书</th><th>TapTap</th><th>YouTube</th></tr></thead>
        <tbody>
        <tr><td>播放量</td><td><span class="dot dot-g"></span><code>view</code></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">阅读数</span></td><td class="na">N/A（非视频平台）</td><td><span class="dot dot-g"></span><code>viewCount</code></td></tr>
        <tr><td>点赞数</td><td><span class="dot dot-g"></span><code>like</code></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">评分</span></td><td><span class="dot dot-g"></span><code>likeCount</code></td></tr>
        <tr><td>转发/分享</td><td><span class="dot dot-g"></span><code>share</code></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td class="na">N/A</td><td class="na">N/A（已隐藏）</td></tr>
        <tr><td>收藏数</td><td><span class="dot dot-g"></span><code>favorite</code></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td class="na">N/A</td><td class="na">N/A</td></tr>
        <tr><td>投币数</td><td><span class="dot dot-g"></span><code>coin</code></td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td></tr>
        <tr><td>弹幕数</td><td><span class="dot dot-g"></span><code>danmaku</code></td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td><td class="na">N/A</td></tr>
        <tr><td>评论数</td><td><span class="dot dot-g"></span><code>reply</code></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><span class="g">✓</span></td><td><span class="dot dot-g"></span><code>commentCount</code></td></tr>
        </tbody>
    </table></body></html>"""
    st_components.html(metrics_matrix_html, height=290, scrolling=False)


def render_crawl_page() -> None:
    _, merged_keywords, expansion = load_keyword_library()
    keyword_runtime = {
        "keyword_count": len(merged_keywords),
        "keywords": merged_keywords,
        "expansion": expansion,
    }
    keyword_count = len(merged_keywords)
    limit_options = {
        10: t("crawl.limit_10"),
        20: t("crawl.limit_20"),
        30: t("crawl.limit_30"),
        40: t("crawl.limit_40"),
        50: t("crawl.limit_50"),
    }
    auth_required_label = t("crawl.auth_required")
    auth_anonymous_label = t("crawl.auth_anonymous")
    auth_local_label = t("crawl.auth_local")
    depth_limited_label = t("crawl.depth_limited")
    depth_basic_label = t("crawl.depth_basic")
    depth_deep_label = t("crawl.depth_deep")
    strategy_default_label = t("crawl.strategy_default")
    media_platforms = {"xiaohongshu", "douyin", "kuaishou"}

    default_platform = st.session_state.get("crawl_platform", "bilibili")
    platform = default_platform if default_platform in PLATFORM_OPTIONS else "bilibili"
    mode = auth_required_label if platform in media_platforms else st.session_state.get("crawl_mode_general", auth_anonymous_label)
    depth = depth_limited_label if platform in media_platforms else st.session_state.get("crawl_depth_general", depth_basic_label)
    order_label = strategy_default_label
    order_val = "totalrank"
    limit_val = int(st.session_state.get("crawl_limit", 20))

    cmd_cols = st.columns([1.05, 1.15, 1.0, 1.0, 5.2], gap="small")
    with cmd_cols[0]:
        with st.popover(t('popover.route'), use_container_width=True):
            render_step_block_header("01", t("crawl.step.platform"), "#5B9A6E", t("crawl.step.platform_desc"))
            platform = st.selectbox(
                t("crawl.platform_label"),
                list(PLATFORM_OPTIONS.keys()),
                format_func=lambda x: PLATFORM_OPTIONS[x],
                key="crawl_platform",
                label_visibility="collapsed",
            )
            st.divider()
            render_step_block_header("02", t("crawl.step.auth"), "#6B8BDB", t("crawl.step.auth_desc"))
            if platform in media_platforms:
                mode = st.radio(t("crawl.auth_label"), [auth_required_label], key="crawl_mode_media", label_visibility="collapsed")
                st.caption(t("crawl.auth_required_note"))
            else:
                mode = st.radio(
                    t("crawl.auth_label"),
                    [auth_anonymous_label, auth_local_label],
                    key="crawl_mode_general",
                    label_visibility="collapsed",
                )
            st.divider()
            render_step_block_header("03", t("crawl.step.depth"), "#D4956B", t("crawl.step.depth_desc"))
            if platform in media_platforms:
                depth = st.radio(t("crawl.step.depth"), [depth_limited_label], key="crawl_depth_media", label_visibility="collapsed", disabled=True)
            else:
                depth = st.radio(t("crawl.step.depth"), [depth_basic_label, depth_deep_label], key="crawl_depth_general", label_visibility="collapsed")
            st.divider()
            render_step_block_header("04", t("crawl.step.strategy"), "#9B7FD4", t("crawl.strategy_note"))
            if platform == "bilibili":
                order_map = {
                    t("crawl.order_totalrank"): "totalrank",
                    t("crawl.order_pubdate"): "pubdate",
                    t("crawl.order_click"): "click",
                    t("crawl.order_stow"): "stow",
                }
                order_label = st.selectbox(t("crawl.step.strategy"), list(order_map.keys()), index=0, key="crawl_order_bilibili", label_visibility="collapsed")
                order_val = order_map[order_label]
            else:
                st.caption(t("crawl.strategy_empty_note"))
            st.divider()
            render_step_block_header("05", t("crawl.step.limit"), "#7FB5B0", t("crawl.step.limit_desc"))
            limit_val = st.selectbox(
                t("crawl.step.limit"),
                list(limit_options.keys()),
                format_func=lambda x: limit_options[x],
                key="crawl_limit",
                label_visibility="collapsed",
            )
            estimated_results = int(limit_val) * int(keyword_count)
            st.markdown(
                render_atlas_list_editor(
                    t("crawl.overview_title"),
                    [
                        (t('crawl.row.platform'), PLATFORM_OPTIONS[platform]),
                        (t('crawl.row.auth'), t('crawl.row.auth_anon') if mode == auth_anonymous_label else t('crawl.row.auth_local')),
                        (t('crawl.row.depth'), t('crawl.row.depth_deep') if depth == depth_deep_label else t('crawl.row.depth_basic')),
                        (t('crawl.estimated'), f"{limit_val} × {keyword_count} = {estimated_results}"),
                    ],
                    compact=True,
                ),
                unsafe_allow_html=True,
            )
            runtime_config = load_config()
            can_execute = True
            if keyword_count == 0:
                can_execute = False
                st.warning(t("crawl.empty_keywords"))
            elif platform in media_platforms and not media_crawler_exists():
                can_execute = False
                st.error(t("crawl.mediacrawler_missing"))
            elif platform == "bilibili" and mode != auth_anonymous_label and not runtime_config.bili_sessdata:
                st.info(t("crawl.bilibili_session_missing"))

            if st.button(t("crawl.run_button", platform=PLATFORM_OPTIONS[platform]), type="primary", use_container_width=True, disabled=not can_execute):
                mode_value = "actions" if mode == auth_anonymous_label else "local"
                started_at = datetime.now()
                before_snapshot = get_crawl_file_snapshot(platform)
                progress_state = init_crawl_progress_state(platform, keyword_count, int(limit_val))
                progress_title = st.empty()
                progress_bar = st.progress(0)
                progress_eta = st.empty()
                progress_detail = st.empty()

                def refresh_progress_ui() -> None:
                    eta_seconds = estimate_remaining_seconds(progress_state)
                    progress_percent = 100 if progress_state["progress"] >= 1.0 else max(min(int(progress_state["progress"] * 100), 99), 1)
                    progress_title.markdown(f"<div style='font-size:13px; color:#E8E4DC; font-weight:700;'>{t('crawl.progress')}: {progress_percent}%</div>", unsafe_allow_html=True)
                    progress_bar.progress(progress_percent)
                    if progress_percent >= 100:
                        progress_eta.caption(f"{t('crawl.stage')}: {progress_state['stage']}")
                    elif eta_seconds is None:
                        progress_eta.caption(t("crawl.connecting"))
                    else:
                        progress_eta.caption(f"{t('crawl.stage')}: {progress_state['stage']} · {t('crawl.remaining', seconds=eta_seconds)}")
                    progress_detail.caption(progress_state["detail"])

                refresh_progress_ui()
                cmd_args = ["crawl", "--platform", platform, "--mode", mode_value, "--order", order_val, "--limit", str(limit_val)]
                if platform not in media_platforms and depth == depth_basic_label:
                    cmd_args.extend(["--depth", "shallow"])
                elif platform not in media_platforms and depth == depth_deep_label:
                    cmd_args.extend(["--depth", "deep"])

                def on_progress_line(line: str) -> None:
                    update_crawl_progress_state(progress_state, line)
                    refresh_progress_ui()

                stdout, stderr, code = run_cli_stream(cmd_args, on_line=on_progress_line)
                progress_state["progress"] = 1.0 if code == 0 else max(progress_state["progress"], 0.92)
                progress_state["stage"] = t("crawl.stage_done") if code == 0 else t("crawl.stage_finished")
                refresh_progress_ui()
                after_snapshot = get_crawl_file_snapshot(platform)
                st.session_state["crawl_last_result"] = summarize_crawl_result(
                    platform=platform,
                    platform_label=PLATFORM_OPTIONS[platform],
                    before_snapshot=before_snapshot,
                    after_snapshot=after_snapshot,
                    keyword_count=keyword_count,
                    limit_val=int(limit_val),
                    started_at=started_at,
                    return_code=code,
                    stdout=stdout,
                    stderr=stderr,
                )
                if code == 0:
                    st.success(t("crawl.success", platform=PLATFORM_OPTIONS[platform]))
                else:
                    st.error(t("crawl.failed_code", code=code))
    with cmd_cols[1]:
        with st.popover(t('popover.keywords'), use_container_width=True):
            keyword_runtime = render_keyword_library("crawl")
            keyword_count = int(keyword_runtime.get("keyword_count", keyword_count))
            merged_keywords = list(keyword_runtime.get("keywords", merged_keywords))
    with cmd_cols[2]:
        with st.popover(t('popover.fields'), use_container_width=True):
            _render_platform_field_tables(platform, mode, depth)
    with cmd_cols[3]:
        with st.popover(t('popover.result'), use_container_width=True):
            if st.session_state.get("crawl_last_result"):
                render_crawl_result_card(st.session_state["crawl_last_result"])
            else:
                st.caption(t("common.empty_first_action"))

    result = st.session_state.get("crawl_last_result") or {}
    result_rows = [
        (t('crawl.row.status'), "OK" if result.get("return_code") == 0 else "WAITING"),
        (t('crawl.row.platform'), result.get("platform_label", PLATFORM_OPTIONS.get(platform, platform))),
        (t('crawl.row.keywords'), result.get("keyword_count", keyword_count)),
        (t('crawl.row.limit'), result.get("limit_val", limit_val)),
    ]
    preview_keywords = merged_keywords[:16]
    keyword_body = atlas_chips(preview_keywords) if preview_keywords else atlas_empty(t('crawl.panel.no_keywords'), t("crawl.empty_keywords"))
    scene_html = f"""
    <div class='atlas-scene-sigil'></div>
    <div class='atlas-scene-line' style='left:18%;top:58%;width:31%;transform:rotate(-18deg);'></div>
    <div class='atlas-scene-line' style='left:47%;top:48%;width:28%;transform:rotate(13deg);'></div>
    <div class='atlas-scene-line' style='left:33%;top:35%;width:24%;transform:rotate(34deg);'></div>
    <span class='atlas-scene-node' style='left:18%;top:57%;background:#5B9A6E;'></span>
    <span class='atlas-scene-node' style='left:47%;top:47%;background:#d4af37;'></span>
    <span class='atlas-scene-node' style='left:73%;top:54%;background:#6B8BDB;'></span>
    <span class='atlas-scene-node' style='left:34%;top:34%;background:#D4956B;'></span>
    <div class='atlas-stage-map'>
      <svg viewBox='0 0 1200 720' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>
        <path class='gridline' d='M120 0V720M260 0V720M400 0V720M540 0V720M680 0V720M820 0V720M960 0V720M1100 0V720M0 120H1200M0 260H1200M0 400H1200M0 540H1200'/>
        <text x='210' y='445' font-size='14'>{t('crawl.stage.timeline_start')}</text>
        <text x='545' y='365' font-size='14'>{t('crawl.metric.keywords')} {keyword_count}</text>
        <text x='850' y='422' font-size='14'>{t('label.csv')} {t('crawl.metric.output')}</text>
      </svg>
    </div>
    """
    panels = [
        render_atlas_panel(
            t('crawl.panel.route'),
            atlas_rows([
                (t('crawl.row.platform'), PLATFORM_OPTIONS.get(platform, platform)),
                (t('crawl.row.auth'), t('crawl.row.auth_anon') if mode == auth_anonymous_label else t('crawl.row.auth_local')),
                (t('crawl.row.depth'), t('crawl.row.depth_deep') if depth == depth_deep_label else t('crawl.row.depth_basic')),
            ], compact=True),
            kicker=t('crawl.kicker.route'),
        ),
        render_atlas_panel(t('crawl.panel.keywords'), keyword_body, kicker=t('crawl.kicker.signals')),
        render_atlas_panel(t('crawl.panel.result'), atlas_rows(result_rows, compact=True), kicker=t('crawl.kicker.output')),
    ]
    drawers = [
        render_atlas_drawer(t('crawl.drawer.preview'), render_atlas_list_editor(t('crawl.drawer.exec_preview'), [
            (t('crawl.row.strategy'), order_label),
            (t('crawl.row.result_limit'), limit_val),
            (t('crawl.row.estimated'), int(limit_val) * max(keyword_count, 1)),
        ], compact=True), badge=t('label.ready')),
        render_atlas_drawer(t('crawl.panel.keywords'), keyword_body, badge=str(keyword_count)),
        render_atlas_drawer(t('crawl.drawer.fields'), atlas_rows([
            ("Bilibili", "Search / Video / Comments"),
            ("YouTube", "Search / Channel / Comments"),
            ("TapTap", "Reviews / Games"),
            ("MediaCrawler", "Local Authorized Platforms"),
        ], compact=True)),
    ]
    render_atlas_stage(
        page_id="crawl",
        title=t('crawl.stage.title'),
        subtitle=t("crawl.subtitle"),
        metrics=[
            (t('crawl.stage.timeline_start'), PLATFORM_OPTIONS.get(platform, platform)),
            (t('crawl.metric.keywords'), str(keyword_count)),
            (t('crawl.metric.limit'), str(limit_val)),
            (t('crawl.metric.output'), t('label.csv')),
        ],
        scene_html=scene_html,
        panels=panels,
        drawers=drawers,
        timeline_label=t('crawl.kicker.route'),
        timeline_start=t('crawl.stage.timeline_start'),
        timeline_end=t('crawl.stage.timeline_end'),
        accent="#5B9A6E",
        mode_label=t('crawl.stage.mode'),
    )
