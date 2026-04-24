from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as st_components

from ui.components.common import render_section_title, render_data_freshness, render_kpi_card, icon
from ui.i18n import t
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


def _render_atlas_command_map(health: dict) -> None:
    """War Atlas inspired command map for the dashboard first viewport."""
    signal_count = int(health.get("capacity", 0) or 0)
    target_count = int(health.get("targets", 0) or 0)
    keyword_count = int(health.get("keywords", 0) or 0)
    last_sync = str(health.get("last_sync", "暂无记录"))
    status_text = "ONLINE" if health.get("api_health") else "LOCAL"
    map_doc = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" />
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; width: 100%; height: 100%; overflow: hidden; background: #0a0c10; }}
    body {{ font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif; color: #e8e4dc; }}
    #map {{ position: absolute; inset: 0; background: #0a0c10; }}
    .signal-field {{
      position: absolute;
      inset: 0;
      z-index: 1;
      pointer-events: none;
      background:
        linear-gradient(rgba(212,175,55,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,175,55,0.035) 1px, transparent 1px),
        radial-gradient(circle at 57% 45%, rgba(212,175,55,0.08), transparent 14%),
        radial-gradient(circle at 72% 52%, rgba(255,75,11,0.08), transparent 18%),
        radial-gradient(circle at 36% 55%, rgba(255,75,11,0.07), transparent 16%);
      background-size: 96px 96px, 96px 96px, auto, auto, auto;
      opacity: 0.9;
    }}
    .signal-field:before {{
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse at 51% 48%, transparent 0 18%, rgba(212,175,55,0.18) 18.2%, transparent 18.6%),
        radial-gradient(ellipse at 65% 48%, transparent 0 20%, rgba(212,175,55,0.12) 20.2%, transparent 20.6%),
        radial-gradient(ellipse at 34% 54%, transparent 0 17%, rgba(212,175,55,0.12) 17.2%, transparent 17.6%),
        linear-gradient(28deg, transparent 0 44%, rgba(212,175,55,0.12) 44.1%, transparent 44.4% 100%),
        linear-gradient(-18deg, transparent 0 55%, rgba(212,175,55,0.12) 55.1%, transparent 55.4% 100%);
      opacity: 0.45;
      filter: blur(0.2px);
    }}
    .screen-signal {{
      position: absolute;
      width: var(--s);
      height: var(--s);
      left: var(--x);
      top: var(--y);
      transform: translate(-50%, -50%);
      border-radius: 50%;
      background: var(--c);
      box-shadow: 0 0 12px color-mix(in srgb, var(--c) 70%, transparent);
      opacity: 0.88;
    }}
    .screen-signal:after {{
      content: "";
      position: absolute;
      inset: -4px;
      border-radius: 50%;
      background: var(--c);
      opacity: 0.13;
    }}
    .atlas-shell {{
      position: relative;
      height: 520px;
      overflow: hidden;
      border: 1px solid rgba(180,160,120,0.16);
      border-radius: 8px;
      background: #0a0c10;
      box-shadow: 0 18px 52px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.03);
    }}
    .atlas-shell:after {{
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background:
        radial-gradient(circle at 50% 55%, rgba(212,175,55,0.08), transparent 28%),
        linear-gradient(180deg, rgba(10,12,16,0.06), rgba(10,12,16,0.44));
      mix-blend-mode: screen;
    }}
    .topbar {{
      position: absolute;
      top: 20px;
      left: 22px;
      right: 22px;
      z-index: 3;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      pointer-events: none;
    }}
    .brand {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      text-shadow: 0 2px 14px rgba(0,0,0,0.7);
    }}
    .brand-title {{
      font-family: 'Cinzel', serif;
      font-size: 34px;
      line-height: 0.9;
      font-weight: 700;
      letter-spacing: 3px;
      color: #f0eee8;
    }}
    .brand-line {{
      width: 108px;
      height: 1px;
      background: linear-gradient(90deg, #d4af37, transparent);
    }}
    .brand-meta {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 10px;
      color: rgba(232,228,220,0.42);
      letter-spacing: 1px;
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
      padding-top: 3px;
      pointer-events: auto;
    }}
    .control {{
      height: 34px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 0 14px;
      border: 1px solid rgba(180,160,120,0.15);
      border-radius: 5px;
      background: rgba(12,15,20,0.78);
      color: rgba(232,228,220,0.64);
      font-size: 12px;
      font-weight: 600;
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 28px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.03);
    }}
    .control b {{ color: #d4af37; font-family: 'IBM Plex Mono', monospace; font-weight: 500; }}
    .display {{
      min-width: 218px;
      padding: 16px 18px;
      border: 1px solid rgba(180,160,120,0.13);
      border-radius: 8px;
      background: rgba(12,15,20,0.72);
      box-shadow: 0 14px 40px rgba(0,0,0,0.32), inset 0 1px 0 rgba(255,255,255,0.03);
      backdrop-filter: blur(14px);
      pointer-events: auto;
    }}
    .display-title {{
      font-family: 'IBM Plex Mono', monospace;
      font-size: 12px;
      letter-spacing: 1.7px;
      color: #d4af37;
      margin-bottom: 10px;
    }}
    .display-row {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      font-size: 11px;
      color: rgba(232,228,220,0.5);
      line-height: 1.8;
    }}
    .display-row span:last-child {{ color: rgba(232,228,220,0.82); font-family: 'IBM Plex Mono', monospace; }}
    .search-card {{
      position: absolute;
      z-index: 3;
      top: 112px;
      left: 22px;
      width: 232px;
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 12px 14px;
      border: 1px solid rgba(180,160,120,0.15);
      border-radius: 7px;
      background: rgba(12,15,20,0.82);
      box-shadow: 0 14px 40px rgba(0,0,0,0.32), inset 0 1px 0 rgba(255,255,255,0.03);
      backdrop-filter: blur(14px);
    }}
    .search-icon {{
      width: 34px;
      height: 34px;
      display: grid;
      place-items: center;
      border-radius: 5px;
      color: #d4af37;
      background: rgba(212,175,55,0.09);
    }}
    .search-title {{ font-size: 12px; font-weight: 700; letter-spacing: 0.7px; color: rgba(232,228,220,0.86); }}
    .search-sub {{ font-size: 10px; color: rgba(232,228,220,0.34); margin-top: 3px; }}
    .timeline {{
      position: absolute;
      z-index: 3;
      left: 50%;
      bottom: 22px;
      width: min(680px, calc(100% - 56px));
      transform: translateX(-50%);
      border: 1px solid rgba(180,160,120,0.16);
      border-radius: 10px;
      background: rgba(12,15,20,0.84);
      box-shadow: 0 18px 52px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.03);
      backdrop-filter: blur(16px);
      padding: 20px 22px 18px;
    }}
    .timeline-top {{
      display: grid;
      grid-template-columns: 44px 1fr 132px;
      align-items: center;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .play {{
      width: 38px;
      height: 38px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      color: #f3dc6b;
      border: 1px solid rgba(212,175,55,0.62);
      background: rgba(212,175,55,0.08);
      box-shadow: 0 0 18px rgba(212,175,55,0.14);
    }}
    .era {{
      text-align: center;
      min-width: 0;
    }}
    .era-pill {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 5px 12px;
      border-radius: 999px;
      background: rgba(180,160,120,0.08);
      color: rgba(232,228,220,0.48);
      font-family: 'IBM Plex Mono', monospace;
      font-size: 10px;
      letter-spacing: 1px;
    }}
    .hot-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #ff4b0b;
      box-shadow: 0 0 12px rgba(255,75,11,0.8);
    }}
    .year {{
      font-family: 'Cinzel', serif;
      font-size: 31px;
      font-weight: 700;
      letter-spacing: 2px;
      color: #f0eee8;
      margin-top: 4px;
      line-height: 1;
    }}
    .battle-count {{
      margin-top: 6px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 11px;
      letter-spacing: 1px;
      color: rgba(232,228,220,0.44);
    }}
    .battle-count b {{ color: #d4af37; font-weight: 600; }}
    .legend {{
      border: 1px solid rgba(180,160,120,0.12);
      border-radius: 6px;
      padding: 9px 10px;
      background: rgba(10,12,16,0.55);
    }}
    .legend-row {{
      display: flex;
      align-items: center;
      gap: 7px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 8px;
      color: rgba(232,228,220,0.42);
      letter-spacing: 0.5px;
      line-height: 1.7;
    }}
    .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #ff4b0b; box-shadow: 0 0 9px rgba(255,75,11,0.65); }}
    .track {{
      position: relative;
      height: 24px;
      display: flex;
      align-items: center;
      gap: 10px;
      color: rgba(232,228,220,0.36);
      font-family: 'IBM Plex Mono', monospace;
      font-size: 10px;
    }}
    .bar {{
      position: relative;
      flex: 1;
      height: 10px;
      border-radius: 2px;
      background: linear-gradient(90deg, rgba(212,175,55,0.22), rgba(212,175,55,0.64));
      overflow: hidden;
    }}
    .bar:before, .bar:after {{
      content: "";
      position: absolute;
      top: 0;
      bottom: 0;
      width: 1px;
      background: rgba(10,12,16,0.38);
    }}
    .bar:before {{ left: 58%; }}
    .bar:after {{ left: 86%; }}
    .thumb {{
      position: absolute;
      right: 4px;
      top: 50%;
      width: 15px;
      height: 15px;
      transform: translateY(-50%);
      border-radius: 50%;
      background: #f3dc6b;
      box-shadow: 0 0 15px rgba(243,220,107,0.55);
    }}
    .maplibregl-ctrl-bottom-left, .maplibregl-ctrl-bottom-right {{ display: none; }}
    @media (max-width: 900px) {{
      .atlas-shell {{ height: 560px; }}
      .topbar {{ align-items: stretch; flex-direction: column; }}
      .controls {{ justify-content: flex-start; }}
      .display {{ width: 220px; }}
      .search-card {{ top: 222px; }}
      .timeline {{ bottom: 16px; }}
      .timeline-top {{ grid-template-columns: 40px 1fr; }}
      .legend {{ display: none; }}
      .brand-title {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <div class="atlas-shell">
    <div id="map"></div>
    <div class="signal-field" id="signal-field"></div>
    <div class="topbar">
      <div class="brand">
        <div class="brand-title">SLG<br/>ATLAS</div>
        <div class="brand-line"></div>
        <div class="brand-meta">{t('overview.map.meta')}</div>
      </div>
      <div class="controls">
        <div class="control">▣ {t('overview.map.guided')}</div>
        <div class="control">◷ {last_sync}</div>
        <div class="control">⌖ {t('overview.map.near_me')}</div>
        <div class="control">▥ {t('overview.map.stats')} <b>{signal_count}</b></div>
      </div>
      <div class="display">
        <div class="display-title">{t('common.display')}</div>
        <div class="display-row"><span>Engine</span><span>{status_text}</span></div>
        <div class="display-row"><span>{t('overview.map.display.targets')}</span><span>{target_count}</span></div>
        <div class="display-row"><span>{t('overview.map.display.keywords')}</span><span>{keyword_count}</span></div>
      </div>
    </div>
    <div class="search-card">
      <div class="search-icon">⌕</div>
      <div>
        <div class="search-title">{t('overview.map.search_title')}</div>
        <div class="search-sub">{t('overview.map.search_body')}</div>
      </div>
    </div>
    <div class="timeline">
      <div class="timeline-top">
        <div class="play">▶</div>
        <div class="era">
          <div class="era-pill"><span class="hot-dot"></span>CONTEMPORARY · SLG OPS</div>
          <div class="year">2026 AD</div>
          <div class="battle-count"><b>{signal_count}</b> SIGNALS</div>
        </div>
        <div class="legend">
          <div class="legend-row"><span class="legend-dot"></span>BILIBILI</div>
          <div class="legend-row"><span class="legend-dot" style="background:#d4af37"></span>TAPTAP</div>
          <div class="legend-row"><span class="legend-dot" style="background:#6b8bdb"></span>YOUTUBE</div>
        </div>
      </div>
      <div class="track"><span>{t('common.seed')}</span><div class="bar"><div class="thumb"></div></div><span>{t('common.year_ad')}</span></div>
    </div>
  </div>
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
  <script>
    const map = new maplibregl.Map({{
      container: 'map',
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [18, 31],
      zoom: 1.45,
      attributionControl: false,
      interactive: true
    }});
    const clusters = [
      [116.4, 39.9, 46], [121.5, 31.2, 24], [104.1, 30.7, 28], [113.3, 23.1, 20],
      [139.7, 35.7, 22], [77.2, 28.6, 22], [31.2, 30.0, 30], [44.4, 33.3, 28],
      [2.3, 48.8, 18], [13.4, 52.5, 16], [30.5, 50.4, 22], [37.6, 55.7, 18],
      [-74.0, 40.7, 15], [-99.1, 19.4, 10], [-46.6, -23.5, 12], [3.4, 6.5, 18],
      [28.0, -26.2, 10], [100.5, 13.7, 18], [106.8, -6.2, 18], [151.2, -33.8, 9]
    ];
    const colors = ['#ff4b0b', '#ff6a16', '#d4af37', '#6b8bdb'];
    const features = [];
    const field = document.getElementById('signal-field');
    let id = 0;
    for (const [lng, lat, count] of clusters) {{
      for (let i = 0; i < count; i++) {{
        const spread = count > 25 ? 7 : 4.5;
        const pointLng = lng + (Math.random() - 0.5) * spread;
        const pointLat = lat + (Math.random() - 0.5) * spread * 0.7;
        const color = colors[id % colors.length];
        const size = 3 + Math.random() * 3.5;
        const dot = document.createElement('span');
        dot.className = 'screen-signal';
        dot.style.setProperty('--x', `${{((pointLng + 180) / 360) * 100}}%`);
        dot.style.setProperty('--y', `${{((90 - pointLat) / 180) * 100}}%`);
        dot.style.setProperty('--s', `${{size}}px`);
        dot.style.setProperty('--c', color);
        field.appendChild(dot);
        features.push({{
          type: 'Feature',
          geometry: {{
            type: 'Point',
            coordinates: [pointLng, pointLat]
          }},
          properties: {{ id: id++, color, size }}
        }});
      }}
    }}
    map.on('load', () => {{
      map.addSource('signals', {{ type: 'geojson', data: {{ type: 'FeatureCollection', features }} }});
      map.addLayer({{
        id: 'signal-halo',
        type: 'circle',
        source: 'signals',
        paint: {{
          'circle-radius': ['+', ['get', 'size'], 3],
          'circle-color': ['get', 'color'],
          'circle-opacity': 0.12,
          'circle-blur': 0.8
        }}
      }});
      map.addLayer({{
        id: 'signal-core',
        type: 'circle',
        source: 'signals',
        paint: {{
          'circle-radius': ['get', 'size'],
          'circle-color': ['get', 'color'],
          'circle-opacity': 0.92,
          'circle-stroke-width': 0
        }}
      }});
    }});
  </script>
</body>
</html>"""
    st_components.html(map_doc, height=520, scrolling=False)


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
        st.markdown(f"<h3>{trend_svg} {t('overview.trend_title')}</h3>", unsafe_allow_html=True)
        chart = (
            alt.Chart(df_top)
            .mark_line(point=alt.OverlayMarkDef(size=30), strokeWidth=1.8)
            .encode(
                x=alt.X("date:T", title="", axis=alt.Axis(format="%m-%d", labelColor="rgba(232,228,220,0.46)", gridColor="rgba(180,160,120,0.06)")),
                y=alt.Y("total_results:Q", title="", axis=alt.Axis(labelColor="rgba(232,228,220,0.46)", gridColor="rgba(180,160,120,0.06)")),
                color=alt.Color("keyword:N", title="关键词",
                    scale=alt.Scale(range=["#d4af37", "#6B8BDB", "#E85D4A", "#5B9A6E", "#9B7FD4", "#D4956B", "#7FB5B0", "#C4845C"]),
                    legend=alt.Legend(labelColor="rgba(232,228,220,0.58)", titleColor="rgba(232,228,220,0.58)")),
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
    health = get_system_health()
    _render_atlas_command_map(health)
    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)
    _render_insights_hero()

    # 系统运行概况 KPI
    target_svg = icon("target", color="#d4af37")
    st.markdown(f"<h3>{target_svg} 系统运行概况</h3>", unsafe_allow_html=True)
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
        view_limit = st.selectbox(t("overview.view_limit"), [10, 20, 50, 100, 300, 500], index=0, label_visibility="collapsed")

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
    st.markdown(f"<h3>{t('overview.loaded_data')}</h3>", unsafe_allow_html=True)

    loaded_files = list_loaded_csv_files()
    if not loaded_files:
        st.markdown("<p style='color:rgba(232,228,220,0.3); font-size:12px;'>当前还没有已加载的数据文件。</p>", unsafe_allow_html=True)
        return

    @st.dialog("危险操作确认")
    def confirm_clear_all() -> None:
        st.warning(t("overview.delete_all_warning"))
        c1, c2 = st.columns(2)
        if c1.button("确认清空", type="primary", use_container_width=True):
            delete_all_loaded_csv_files()
            st.rerun()
        if c2.button("取消", use_container_width=True):
            st.rerun()

    _, action_col = st.columns([9, 2])
    with action_col:
        if st.button(t("overview.delete_all"), type="primary", use_container_width=True):
            confirm_clear_all()

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    for item in loaded_files:
        col1, col2, col3 = st.columns([6, 3, 2])
        with col1:
            st.markdown(item["display_html"], unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='font-size:11px; color:rgba(232,228,220,0.3); padding-top:10px;'>{item['size_kb']:.1f} KB</div>", unsafe_allow_html=True)
        with col3:
            if st.button(t("overview.delete"), key=f"del_{item['path']}"):
                try:
                    delete_loaded_csv_file(item["path"])
                    st.rerun()
                except Exception:
                    st.error(t("overview.delete_blocked"))
