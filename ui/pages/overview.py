from __future__ import annotations

from html import escape

import streamlit as st
import streamlit.components.v1 as st_components

from ui.components.atlas_shell import (
    atlas_chips,
    atlas_empty,
    atlas_rows,
    render_atlas_drawer,
    render_atlas_list_editor,
    render_atlas_panel,
    render_atlas_stage,
)
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
    #map {{ position: absolute; inset: 0; background: #0a0c10; opacity: .42; }}
    .theater-svg {{
      position: absolute;
      inset: 0;
      z-index: 2;
      width: 100%;
      height: 100%;
      pointer-events: none;
      filter: drop-shadow(0 20px 34px rgba(0,0,0,0.35));
    }}
    .theater-svg .coast {{
      fill: rgba(18,24,26,0.48);
      stroke: rgba(232,228,220,0.16);
      stroke-width: 1.2;
    }}
    .theater-svg .kingdom {{
      stroke-width: 2;
      stroke-dasharray: 6 4;
      mix-blend-mode: screen;
    }}
    .theater-svg .wei {{ fill: rgba(226,45,63,0.18); stroke: rgba(226,45,63,0.82); }}
    .theater-svg .shu {{ fill: rgba(212,175,55,0.18); stroke: rgba(212,175,55,0.84); }}
    .theater-svg .wu {{ fill: rgba(47,107,220,0.18); stroke: rgba(88,142,255,0.84); }}
    .theater-svg .route {{
      fill: none;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-dasharray: 4 5;
      opacity: .64;
    }}
    .theater-svg .battle {{
      stroke: rgba(255,255,255,.52);
      stroke-width: 1.2;
    }}
    .theater-svg .battle-halo {{
      opacity: .18;
      filter: blur(1px);
    }}
    .theater-svg text {{
      font-family: 'IBM Plex Mono', monospace;
      letter-spacing: 1.4px;
      fill: rgba(232,228,220,0.74);
      paint-order: stroke;
      stroke: rgba(10,12,16,.9);
      stroke-width: 3px;
      stroke-linejoin: round;
    }}
    .theater-svg .kingdom-label {{
      font-family: 'Cinzel', serif;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: 3px;
      fill: rgba(240,238,232,.76);
    }}
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
    .kingdom-card {{
      position: absolute;
      z-index: 3;
      right: 22px;
      bottom: 112px;
      width: min(330px, calc(100% - 44px));
      border: 1px solid rgba(180,160,120,0.15);
      border-radius: 8px;
      background: rgba(10,12,16,0.84);
      box-shadow: 0 18px 52px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.03);
      backdrop-filter: blur(16px);
      overflow: hidden;
    }}
    .kingdom-card-head {{
      padding: 16px 18px 12px;
      border-bottom: 1px solid rgba(180,160,120,0.12);
    }}
    .kingdom-card-title {{
      font-family: 'Cinzel', serif;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 1.8px;
      color: #d4af37;
      line-height: 1.05;
    }}
    .era-band {{
      height: 33px;
      display: flex;
      align-items: center;
      margin-top: 13px;
      padding: 0 13px;
      border-radius: 999px;
      background: #df143d;
      color: #fff;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
    }}
    .kingdom-row {{
      display: grid;
      grid-template-columns: 84px 1fr;
      gap: 12px;
      padding: 13px 18px;
      border-bottom: 1px solid rgba(180,160,120,0.08);
    }}
    .kingdom-row span {{
      color: rgba(232,228,220,0.35);
      font-family: 'IBM Plex Mono', monospace;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 1.4px;
      text-transform: uppercase;
    }}
    .kingdom-row b {{
      color: rgba(232,228,220,0.82);
      font-size: 14px;
      font-weight: 600;
    }}
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
      .kingdom-card {{ display: none; }}
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
    <svg class="theater-svg" viewBox="0 0 1000 520" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <path class="coast" d="M188,85 C260,44 353,35 438,54 C530,74 595,61 673,84 C773,114 845,166 880,245 C915,325 862,416 760,452 C676,482 603,449 532,456 C430,466 371,512 269,462 C171,415 116,317 130,219 C138,162 151,116 188,85 Z" />
      <path class="kingdom wei" d="M289,112 C367,63 508,69 624,102 C711,127 773,166 788,229 C715,246 662,244 594,231 C529,219 476,212 410,229 C357,243 304,238 253,209 C249,166 261,133 289,112 Z" />
      <path class="kingdom shu" d="M210,238 C253,211 316,225 381,257 C432,282 458,332 445,386 C407,435 342,466 277,436 C222,410 183,344 191,286 C194,264 199,248 210,238 Z" />
      <path class="kingdom wu" d="M458,262 C530,224 640,236 746,248 C829,260 862,318 829,377 C792,444 684,459 582,426 C505,401 459,347 458,262 Z" />
      <path class="route" d="M548,147 C526,203 538,246 580,286 C630,333 680,344 733,330" stroke="#e22d3f" />
      <path class="route" d="M337,351 C392,305 427,276 502,275 C558,276 602,285 646,316" stroke="#d4af37" />
      <path class="route" d="M725,276 C673,270 620,267 577,285 C548,303 524,333 490,363" stroke="#588eff" />
      <circle class="battle-halo" cx="545" cy="160" r="28" fill="#e22d3f" /><circle class="battle" cx="545" cy="160" r="7" fill="#e22d3f" />
      <circle class="battle-halo" cx="594" cy="287" r="36" fill="#ff4b0b" /><circle class="battle" cx="594" cy="287" r="10" fill="#ff4b0b" />
      <circle class="battle-halo" cx="505" cy="360" r="26" fill="#588eff" /><circle class="battle" cx="505" cy="360" r="7" fill="#588eff" />
      <circle class="battle-halo" cx="387" cy="318" r="25" fill="#d4af37" /><circle class="battle" cx="387" cy="318" r="7" fill="#d4af37" />
      <circle class="battle-halo" cx="411" cy="214" r="23" fill="#d4af37" /><circle class="battle" cx="411" cy="214" r="6" fill="#d4af37" />
      <text class="kingdom-label" x="468" y="154">{t('overview.map.kingdom.wei')}</text>
      <text class="kingdom-label" x="276" y="350">{t('overview.map.kingdom.shu')}</text>
      <text class="kingdom-label" x="626" y="374">{t('overview.map.kingdom.wu')}</text>
      <text x="562" y="134" font-size="12">{t('overview.map.battle.guandu')}</text>
      <text x="612" y="286" font-size="12">{t('overview.map.battle.redcliffs')}</text>
      <text x="521" y="365" font-size="12">{t('overview.map.battle.yiling')}</text>
      <text x="402" y="321" font-size="12">{t('overview.map.battle.hanzhong')}</text>
      <text x="426" y="217" font-size="12">{t('overview.map.battle.changan')}</text>
    </svg>
    <div class="signal-field" id="signal-field"></div>
    <div class="topbar">
      <div class="brand">
          <div class="brand-title">{t('overview.map.brand')}</div>
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
        <div class="display-row"><span>{t('overview.map.display.era_label')}</span><span>220 AD</span></div>
        <div class="display-row"><span>{t('overview.map.display.engine_label')}</span><span>{status_text}</span></div>
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
    <div class="kingdom-card">
      <div class="kingdom-card-head">
        <div class="kingdom-card-title">BATTLE OF RED CLIFFS</div>
        <div class="era-band">THREE KINGDOMS</div>
      </div>
      <div class="kingdom-row"><span>Result</span><b>Sun-Liu victory</b></div>
      <div class="kingdom-row"><span>Date</span><b>Winter 208 AD</b></div>
      <div class="kingdom-row"><span>Conflict</span><b>Wei · Shu · Wu theater</b></div>
    </div>
    <div class="timeline">
      <div class="timeline-top">
        <div class="play">▶</div>
        <div class="era">
          <div class="era-pill"><span class="hot-dot"></span>HAN COLLAPSE · THREE KINGDOMS</div>
          <div class="year">220 AD</div>
          <div class="battle-count"><b>9</b> BATTLES · <b>{signal_count}</b> SIGNALS</div>
        </div>
        <div class="legend">
          <div class="legend-row"><span class="legend-dot"></span>WEI</div>
          <div class="legend-row"><span class="legend-dot" style="background:#d4af37"></span>SHU</div>
          <div class="legend-row"><span class="legend-dot" style="background:#2f6bdc"></span>WU</div>
        </div>
      </div>
      <div class="track"><span>184 AD</span><div class="bar"><div class="thumb"></div></div><span>280 AD</span></div>
    </div>
  </div>
  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
  <script>
    const map = new maplibregl.Map({{
      container: 'map',
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [109.8, 31.7],
      zoom: 4.05,
      attributionControl: false,
      interactive: true
    }});
    const kingdoms = {{
      type: 'FeatureCollection',
      features: [
        {{ type: 'Feature', properties: {{ name: 'WEI', color: '#e22d3f' }}, geometry: {{ type: 'Polygon', coordinates: [[[103.0,34.1],[105.0,38.4],[111.4,40.5],[119.6,38.2],[121.6,34.2],[117.3,31.4],[111.2,30.9],[106.7,32.0],[103.0,34.1]]] }} }},
        {{ type: 'Feature', properties: {{ name: 'SHU', color: '#d4af37' }}, geometry: {{ type: 'Polygon', coordinates: [[[96.8,28.2],[99.5,33.5],[104.4,34.2],[108.8,31.0],[107.6,27.3],[103.7,24.1],[99.3,24.9],[96.8,28.2]]] }} }},
        {{ type: 'Feature', properties: {{ name: 'WU', color: '#2f6bdc' }}, geometry: {{ type: 'Polygon', coordinates: [[[108.8,30.0],[113.8,31.8],[122.4,31.0],[123.0,27.0],[120.2,23.1],[114.2,22.4],[109.1,25.5],[108.8,30.0]]] }} }}
      ]
    }};
    const battles = {{
      type: 'FeatureCollection',
      features: [
        {{ type: 'Feature', properties: {{ name: 'Guandu', year: '200 AD', side: 'WEI', color: '#e22d3f', size: 8 }}, geometry: {{ type: 'Point', coordinates: [113.7, 34.7] }} }},
        {{ type: 'Feature', properties: {{ name: 'Red Cliffs', year: '208 AD', side: 'WU / SHU', color: '#ff4b0b', size: 11 }}, geometry: {{ type: 'Point', coordinates: [114.3, 29.9] }} }},
        {{ type: 'Feature', properties: {{ name: 'Yiling', year: '222 AD', side: 'WU', color: '#2f6bdc', size: 8 }}, geometry: {{ type: 'Point', coordinates: [111.3, 30.7] }} }},
        {{ type: 'Feature', properties: {{ name: 'Hanzhong', year: '219 AD', side: 'SHU', color: '#d4af37', size: 8 }}, geometry: {{ type: 'Point', coordinates: [107.0, 33.1] }} }},
        {{ type: 'Feature', properties: {{ name: 'Wuzhang Plains', year: '234 AD', side: 'SHU', color: '#d4af37', size: 7 }}, geometry: {{ type: 'Point', coordinates: [107.6, 34.2] }} }},
        {{ type: 'Feature', properties: {{ name: 'Hefei', year: '215 AD', side: 'WEI / WU', color: '#6b8bdb', size: 7 }}, geometry: {{ type: 'Point', coordinates: [117.2, 31.8] }} }}
      ]
    }};
    const routes = {{
      type: 'FeatureCollection',
      features: [
        {{ type: 'Feature', properties: {{ color: '#e22d3f' }}, geometry: {{ type: 'LineString', coordinates: [[113.7,34.7],[114.3,29.9],[117.2,31.8]] }} }},
        {{ type: 'Feature', properties: {{ color: '#d4af37' }}, geometry: {{ type: 'LineString', coordinates: [[104.1,30.7],[107.0,33.1],[107.6,34.2]] }} }},
        {{ type: 'Feature', properties: {{ color: '#2f6bdc' }}, geometry: {{ type: 'LineString', coordinates: [[118.8,32.1],[114.3,29.9],[111.3,30.7]] }} }}
      ]
    }};
    const labels = {{
      type: 'FeatureCollection',
      features: [
        {{ type: 'Feature', properties: {{ label: 'CAO WEI' }}, geometry: {{ type: 'Point', coordinates: [113.2,36.3] }} }},
        {{ type: 'Feature', properties: {{ label: 'SHU HAN' }}, geometry: {{ type: 'Point', coordinates: [102.8,29.4] }} }},
        {{ type: 'Feature', properties: {{ label: 'EASTERN WU' }}, geometry: {{ type: 'Point', coordinates: [117.6,27.4] }} }},
        {{ type: 'Feature', properties: {{ label: 'CHANGAN' }}, geometry: {{ type: 'Point', coordinates: [108.9,34.3] }} }},
        {{ type: 'Feature', properties: {{ label: 'CHENGDU' }}, geometry: {{ type: 'Point', coordinates: [104.1,30.7] }} }},
        {{ type: 'Feature', properties: {{ label: 'JIANYE' }}, geometry: {{ type: 'Point', coordinates: [118.8,32.1] }} }}
      ]
    }};
    map.on('load', () => {{
      map.addSource('kingdoms', {{ type: 'geojson', data: kingdoms }});
      map.addSource('routes', {{ type: 'geojson', data: routes }});
      map.addSource('battles', {{ type: 'geojson', data: battles }});
      map.addSource('labels', {{ type: 'geojson', data: labels }});
      map.addLayer({{
        id: 'kingdom-fill',
        type: 'fill',
        source: 'kingdoms',
        paint: {{
          'fill-color': ['get', 'color'],
          'fill-opacity': 0.18
        }}
      }});
      map.addLayer({{
        id: 'kingdom-line',
        type: 'line',
        source: 'kingdoms',
        paint: {{
          'line-color': ['get', 'color'],
          'line-opacity': 0.68,
          'line-width': 1.2,
          'line-dasharray': [2, 1]
        }}
      }});
      map.addLayer({{
        id: 'campaign-routes',
        type: 'line',
        source: 'routes',
        paint: {{
          'line-color': ['get', 'color'],
          'line-opacity': 0.42,
          'line-width': 2,
          'line-blur': 0.5
        }}
      }});
      map.addLayer({{
        id: 'battle-halo',
        type: 'circle',
        source: 'battles',
        paint: {{
          'circle-radius': ['+', ['get', 'size'], 8],
          'circle-color': ['get', 'color'],
          'circle-opacity': 0.16,
          'circle-blur': 0.9
        }}
      }});
      map.addLayer({{
        id: 'battle-core',
        type: 'circle',
        source: 'battles',
        paint: {{
          'circle-radius': ['get', 'size'],
          'circle-color': ['get', 'color'],
          'circle-opacity': 0.92,
          'circle-stroke-width': 1,
          'circle-stroke-color': 'rgba(255,255,255,0.45)'
        }}
      }});
      map.addLayer({{
        id: 'theater-labels',
        type: 'symbol',
        source: 'labels',
        layout: {{
          'text-field': ['get', 'label'],
          'text-font': ['Open Sans Semibold', 'Arial Unicode MS Bold'],
          'text-size': 12,
          'text-letter-spacing': 0.12,
          'text-anchor': 'center'
        }},
        paint: {{
          'text-color': 'rgba(232,228,220,0.72)',
          'text-halo-color': '#0a0c10',
          'text-halo-width': 1.6
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
                            margin-bottom:14px; letter-spacing:1px;'>{report_icon} {t('overview.insights_title')}</div>
                {cards_html}
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style='padding:24px; border:1px dashed rgba(180,160,120,0.15); border-radius:8px;
                        background:rgba(12,15,20,0.6); margin-bottom:24px;'>
                <div style='font-family:Cinzel,serif; font-size:15px; font-weight:600; color:rgba(232,228,220,0.5);
                            letter-spacing:1px;'>{report_icon} {t('overview.no_insights')}</div>
                <div style='font-size:12px; color:rgba(232,228,220,0.3); margin-top:8px;'>
                    {t('overview.no_insights_hint')}</div>
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
    st.markdown(f"<h3>{search_svg} {t('overview.top_comments')}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:rgba(232,228,220,0.35); font-size:12px; margin-bottom:14px;'>{t('overview.top_comments_desc')}</p>", unsafe_allow_html=True)

    for c in comments:
        sentiment_badge = ""
        if c.get("sentiment") == "positive":
            sentiment_badge = f"<span style='background:rgba(91,154,110,0.15); color:#5B9A6E; padding:2px 8px; border-radius:3px; font-size:10px; font-weight:600; letter-spacing:0.5px;'>{t('overview.positive')}</span>"
        elif c.get("sentiment") == "negative":
            sentiment_badge = f"<span style='background:rgba(232,93,74,0.15); color:#E85D4A; padding:2px 8px; border-radius:3px; font-size:10px; font-weight:600; letter-spacing:0.5px;'>{t('overview.negative')}</span>"

        profile_svg = icon("profile", color="rgba(232,228,220,0.3)")
        st.markdown(
            f"""<div style='background:rgba(12,15,20,0.92);border:1px solid rgba(180,160,120,0.1);border-radius:8px;padding:16px 18px;margin-bottom:8px;box-shadow:0 4px 24px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.02);'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                    <span style='font-size:10px;color:rgba(232,228,220,0.3);letter-spacing:0.5px;'>{profile_svg}
                        {c.get('author', t('overview.anonymous'))} · {c.get('platform', '')} · {c.get('like_count', 0)} {t('overview.likes')}</span>
                    {sentiment_badge}
                </div>
                <div style='font-size:12px;color:rgba(232,228,220,0.7);line-height:1.7;'>{c.get('content', '')}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_overview_page() -> None:
    health = get_system_health()
    loaded_files = list_loaded_csv_files()
    view_limit = int(st.session_state.get("overview_view_limit", 10))
    trending = get_trending_videos(view_limit)
    comments = get_top_comments(limit=8)
    weekly = get_weekly_summary_text()
    platform_data = [
        ("bilibili", "Bilibili"),
        ("youtube", "YouTube"),
        ("taptap", "TapTap"),
        ("douyin", "Douyin"),
        ("kuaishou", "Kuaishou"),
        ("xiaohongshu", "RedNote"),
    ]
    platform_stats = [(platform_id, label, get_platform_stats(platform_id)) for platform_id, label in platform_data]

    @st.dialog(t("overview.confirm_clear"))
    def confirm_clear_all() -> None:
        st.warning(t("overview.delete_all_warning"))
        c1, c2 = st.columns(2)
        if c1.button(t("overview.confirm_clear_btn"), type="primary", use_container_width=True):
            delete_all_loaded_csv_files()
            st.rerun()
        if c2.button(t("overview.cancel"), use_container_width=True):
            st.rerun()

    cmd_cols = st.columns([1.0, 1.0, 1.0, 1.0, 5.5], gap="small")
    with cmd_cols[0]:
        with st.popover(t('popover.data'), use_container_width=True):
            st.caption(t("overview.loaded_data"))
            if loaded_files:
                if st.button(t("overview.delete_all"), type="primary", use_container_width=True):
                    confirm_clear_all()
                for idx, item in enumerate(loaded_files[:20]):
                    file_cols = st.columns([3, 1.4], gap="small")
                    with file_cols[0]:
                        full_name = escape(str(item["path"].name))
                        st.markdown(
                            f"<div title='{full_name}' style='overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:rgba(232,228,220,0.78);font-size:12px;'>"
                            f"{item['display_html']}"
                            f"</div>"
                            f"<div style='color:rgba(232,228,220,0.36);font-size:10px;margin-top:2px;'>{item['size_kb']:.1f} KB</div>",
                            unsafe_allow_html=True,
                        )
                    with file_cols[1]:
                        if st.button(t("overview.delete"), key=f"del_{idx}_{item['path']}", use_container_width=True):
                            try:
                                delete_loaded_csv_file(item["path"])
                                st.rerun()
                            except Exception:
                                st.error(t("overview.delete_blocked"))
            else:
                st.caption(common_empty := t("common.empty_first_action"))
    with cmd_cols[1]:
        with st.popover(t('popover.trending'), use_container_width=True):
            view_limit = st.selectbox(
                t("overview.view_limit"),
                [10, 20, 50, 100, 300, 500],
                index=[10, 20, 50, 100, 300, 500].index(view_limit) if view_limit in [10, 20, 50, 100, 300, 500] else 0,
                key="overview_view_limit",
            )
            trending = get_trending_videos(int(view_limit))
            if trending:
                visible = trending[: int(view_limit)]
                rows_html = render_atlas_list_editor(
                    t('overview.drawer.hot_title'),
                    [
                        (str(video.get("title") or video.get("video_title") or t('overview.untitled'))[:38], f"{int(video.get('view_count', 0) or 0):,}")
                        for video in visible
                    ],
                    caption=t('overview.sorted_by_views'),
                    compact=True,
                )
                st.markdown(rows_html, unsafe_allow_html=True)
                if len(visible) < int(view_limit):
                    st.markdown(
                        "<div style='margin-top:8px;padding:8px 10px;border:1px dashed rgba(180,160,120,0.18);"
                        "border-radius:6px;color:rgba(232,228,220,0.42);font-size:11px;text-align:center;letter-spacing:0.4px;'>"
                        f"{t('overview.no_more_data')}"
                        "</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption(t("common.empty_first_action"))
    with cmd_cols[2]:
        with st.popover(t('popover.comments'), use_container_width=True):
            if comments:
                for comment in comments[:8]:
                    st.markdown(
                        f"**{escape(str(comment.get('author', t('profile.unknown'))))}** · "
                        f"{escape(str(comment.get('platform', '')))} · {int(comment.get('like_count', 0) or 0)} {t('overview.likes')}"
                    )
                    st.caption(str(comment.get("content", ""))[:180])
            else:
                st.caption(t("common.empty_first_action"))
    with cmd_cols[3]:
        with st.popover(t('popover.freshness'), use_container_width=True):
            from datetime import datetime as _dt
            now_str = _dt.now().strftime("%Y-%m-%d %H:%M")
            clk = icon("clock", color="#d4af37")
            st.markdown(
                "<div style='display:flex;align-items:center;gap:10px;padding:14px 16px;"
                "border:1px solid rgba(180,160,120,0.14);border-radius:8px;background:rgba(12,15,20,0.7);'>"
                f"<div style='font-size:14px;'>{clk}</div>"
                "<div style='display:flex;flex-direction:column;line-height:1.5;'>"
                f"<span style='font-size:10px;color:rgba(232,228,220,0.42);letter-spacing:1px;text-transform:uppercase;'>{t('common.freshness')}</span>"
                f"<span style='font-size:13px;color:rgba(232,228,220,0.85);font-family:var(--wa-font-mono);'>{now_str}</span>"
                "</div>"
                "</div>",
                unsafe_allow_html=True,
            )

    api_text = t('label.online') if health["api_health"] else t('label.local')
    platform_rows = [
        (label, f"{stats['videos_total']} / +{stats['videos_today']}")
        for _, label, stats in platform_stats
    ]
    loaded_rows = [
        (item["path"].name, f"{item['size_kb']:.1f} KB")
        for item in loaded_files[:14]
    ]
    trending_rows = [
        (
            str(video.get("title") or video.get("video_title") or t('overview.untitled'))[:42],
            f"{int(video.get('view_count', 0) or 0):,}",
        )
        for video in trending[:10]
    ]
    comment_rows = [
        (
            f"{comment.get('author', t('profile.unknown'))} · {comment.get('platform', '')}",
            f"{int(comment.get('like_count', 0) or 0)}",
        )
        for comment in comments[:8]
    ]
    weekly_body = (
        "".join(f"<p class='atlas-shell-copy'>{escape(str(item))}</p>" for item in weekly[:3])
        if weekly
        else atlas_empty(t('overview.panel.no_brief'), t("common.empty_first_action"))
    )
    loaded_body = render_atlas_list_editor(
        t('overview.drawer.loaded_title'),
        loaded_rows,
        caption=t('overview.drawer.loaded_caption'),
        compact=True,
        empty_title=t('overview.drawer.no_files'),
        empty_body=t("common.empty_first_action"),
    )
    trending_body = render_atlas_list_editor(
        t('overview.drawer.hot_title'),
        trending_rows,
        caption=t('overview.drawer.hot_caption'),
        compact=True,
        empty_title=t('overview.drawer.no_hot'),
        empty_body=t("common.empty_first_action"),
    )
    comments_body = render_atlas_list_editor(
        t('overview.drawer.comments'),
        comment_rows,
        caption=t('overview.drawer.comments_caption'),
        compact=True,
        empty_title=t('overview.drawer.no_comments'),
        empty_body=t("common.empty_first_action"),
    )
    keywords = max(int(health.get("keywords", 0) or 0), 1)
    signal_count = int(health.get("capacity", 0) or 0)
    scene_html = f"""
    <div class='atlas-stage-map'>
      <svg viewBox='0 0 1200 720' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>
        <defs>
          <radialGradient id='overviewGlow' cx='50%' cy='48%' r='58%'>
            <stop offset='0%' stop-color='rgba(212,175,55,.16)'/>
            <stop offset='70%' stop-color='rgba(212,175,55,.02)'/>
            <stop offset='100%' stop-color='rgba(10,12,16,0)'/>
          </radialGradient>
        </defs>
        <rect width='1200' height='720' fill='url(#overviewGlow)'/>
        <path class='gridline' d='M120 0V720M260 0V720M400 0V720M540 0V720M680 0V720M820 0V720M960 0V720M1100 0V720M0 120H1200M0 260H1200M0 400H1200M0 540H1200'/>
        <path class='land' d='M407 100C478 76 595 82 680 129C764 175 824 211 889 250C956 291 1009 365 996 438C982 517 905 565 824 594C740 624 648 625 572 594C499 565 456 510 386 495C311 478 218 501 176 442C135 385 170 298 221 251C273 203 333 125 407 100Z'/>
        <path class='kingdom wei' d='M400 122C482 90 615 95 702 151C765 192 785 245 771 305C696 287 612 298 549 338C512 287 460 252 397 238C369 197 366 154 400 122Z'/>
        <path class='kingdom shu' d='M270 280C332 235 449 242 533 337C492 394 477 463 508 542C431 520 384 480 320 485C248 491 183 461 176 411C169 361 212 322 270 280Z'/>
        <path class='kingdom wu' d='M567 352C646 302 748 315 846 352C924 381 987 421 960 480C929 549 798 602 697 595C603 589 534 541 517 475C504 425 523 380 567 352Z'/>
        <path class='route' d='M455 232C530 276 613 316 702 371C779 419 820 468 888 512'/>
        <path class='route' d='M315 418C393 396 477 383 568 352'/>
        <circle class='signal' cx='455' cy='232' r='10' fill='#e22d3f'/><circle cx='455' cy='232' r='26' fill='rgba(226,45,63,.12)'/>
        <circle class='signal' cx='315' cy='418' r='10' fill='#d4af37'/><circle cx='315' cy='418' r='31' fill='rgba(212,175,55,.12)'/>
        <circle class='signal' cx='888' cy='512' r='10' fill='#588eff'/><circle cx='888' cy='512' r='29' fill='rgba(88,142,255,.12)'/>
        <text x='434' y='205' font-size='26'>{t('overview.stage.wei')}</text>
        <text x='268' y='454' font-size='26'>{t('overview.stage.shu')}</text>
        <text x='842' y='543' font-size='26'>{t('overview.stage.wu')}</text>
        <text x='532' y='404' font-size='15'>{t('overview.map.signals')} {signal_count}</text>
        <text x='618' y='331' font-size='13'>{t('overview.map.keywords')} {keywords}</text>
      </svg>
    </div>
    """
    panels = [
        render_atlas_panel(
            t('overview.panel.system'),
            atlas_rows([
                (t('overview.panel.api'), api_text),
                (t('overview.panel.last_sync'), health.get("last_sync", "N/A")),
                (t('overview.panel.local_sets'), health.get("capacity", 0)),
            ], compact=True),
            kicker=t('overview.stage.title'),
        ),
        render_atlas_panel(t('overview.panel.platform'), atlas_rows(platform_rows[:4], compact=True), kicker=t('overview.panel.platform')),
        render_atlas_panel(t('overview.panel.weekly'), weekly_body, kicker=t('overview.panel.weekly')),
    ]
    drawers = [
        render_atlas_drawer(t('overview.drawer.loaded'), loaded_body, badge=str(len(loaded_files))),
        render_atlas_drawer(t('overview.drawer.trending'), trending_body, badge=str(len(trending))),
        render_atlas_drawer(t('overview.drawer.comments'), comments_body, badge=str(len(comments))),
        render_atlas_drawer(t('overview.drawer.platforms'), render_atlas_list_editor(t('overview.drawer.platform_title'), platform_rows, compact=True), badge="6"),
    ]
    render_atlas_stage(
        page_id="overview",
        title=t("overview.map.brand"),
        subtitle=t("overview.map.meta"),
        metrics=[
            (t("overview.map.display.signals"), str(health.get("capacity", 0))),
            (t("overview.map.display.targets"), str(health.get("targets", 0))),
            (t("overview.map.display.keywords"), str(health.get("keywords", 0))),
            (t("overview.map.display.status"), api_text),
        ],
        scene_html=scene_html,
        panels=panels,
        drawers=drawers,
        timeline_label=t("common.year_ad"),
        timeline_start=t('overview.timeline_start'),
        timeline_end=t('overview.timeline_end'),
        mode_label=t('overview.mode_label'),
    )
