"""SLG Sentinel — 竞品对比页面"""
from __future__ import annotations
from html import escape

import streamlit as st
from src.core.config import load_config
from ui.components.atlas_shell import (
    atlas_empty,
    atlas_rows,
    render_atlas_drawer,
    render_atlas_list_editor,
    render_atlas_panel,
    render_atlas_stage,
)
from ui.components.common import render_atlas_ops_board, render_empty_state, render_page_header, icon
from ui.i18n import t
from ui.services.app_services import load_targets_config

def _get_taptap_game_options() -> list[dict]:
    try:
        targets = load_targets_config()
        games = targets.get("targets", {}).get("taptap_games", [])
        return [g for g in games if g.get("name") and g.get("app_id")]
    except Exception: return []

def _run_comparison(name_a: str, name_b: str) -> str | None:
    from ui.services.overview_service import get_top_comments
    from src.core.llm_client import LLMClient
    config = load_config()
    llm = LLMClient(config)
    provider = llm.get_available_provider()
    if not provider: return None
    all_comments = get_top_comments(limit=50)
    comments_a = [c for c in all_comments if name_a in c.get("content", "")]
    comments_b = [c for c in all_comments if name_b in c.get("content", "")]
    a_text = "\n".join(f"- (赞{c['like_count']}) {c['content'][:100]}" for c in comments_a[:15])
    b_text = "\n".join(f"- (赞{c['like_count']}) {c['content'][:100]}" for c in comments_b[:15])
    prompt = f"""你是一位资深 SLG 游戏市场分析师。请对比以下两款 SLG 游戏的玩家口碑。
## {name_a} 相关评论
{a_text or "（暂无相关评论数据）"}
## {name_b} 相关评论
{b_text or "（暂无相关评论数据）"}
请输出以下格式的 Markdown 分析报告：
### {name_a} 核心优势
- （列出 3-5 点）
### {name_a} 主要不满
- （列出 3-5 点）
### {name_b} 核心优势
- （列出 3-5 点）
### {name_b} 主要不满
- （列出 3-5 点）
### 对比总结与产品机会
（1-2 段落，指出两者差异化定位，以及一款新的三国单机 SLG 可以从中汲取的设计启示）
要求：如果某款游戏的评论数据不足，请基于你对该游戏的公开认知进行补充分析。"""
    try: return llm.chat(prompt, provider=provider, temperature=0.4, timeout=120)
    except Exception as e: return f"分析生成失败: {e}"

def render_competitor_page() -> None:
    games = _get_taptap_game_options()
    game_names = [g["name"] for g in games] if games else []
    config = load_config()
    has_llm = bool(config.deepseek_api_key or config.openai_api_key or config.qwen_api_key)
    if game_names:
        idx_a_default = int(st.session_state.get("comp_a", 0))
        idx_b_default = int(st.session_state.get("comp_b", min(1, len(game_names) - 1)))
        name_a = game_names[min(idx_a_default, len(game_names) - 1)]
        name_b = game_names[min(idx_b_default, len(game_names) - 1)]
    else:
        name_a = st.session_state.get("comp_a_text", "")
        name_b = st.session_state.get("comp_b_text", "")

    cmd_cols = st.columns([1.05, 1.0, 1.0, 6.2], gap="small")
    with cmd_cols[0]:
        with st.popover(t('popover.select'), use_container_width=True):
            if game_names:
                idx_a = st.selectbox(t("competitor.a"), range(len(game_names)), format_func=lambda i: game_names[i], key="comp_a")
                idx_b = st.selectbox(t("competitor.b"), range(len(game_names)), format_func=lambda i: game_names[i], key="comp_b", index=min(1, len(game_names)-1))
                name_a = game_names[idx_a]
                name_b = game_names[idx_b]
            else:
                name_a = st.text_input(t("competitor.a"), placeholder=t("competitor.placeholder"), key="comp_a_text")
                name_b = st.text_input(t("competitor.b"), placeholder=t("competitor.placeholder"), key="comp_b_text")
            if not has_llm:
                st.warning(t("competitor.llm_warning"))
            if name_a == name_b and name_a:
                st.info(t("competitor.same_info"))
            generate_disabled = not has_llm or not name_a or not name_b or name_a == name_b
            if st.button(t("competitor.generate", a=name_a or "A", b=name_b or "B"), type="primary", use_container_width=True, disabled=generate_disabled):
                with st.spinner(t("competitor.generating")):
                    result = _run_comparison(name_a, name_b)
                if result:
                    st.session_state["competitor_last_result"] = result
                    st.session_state["competitor_last_names"] = (name_a, name_b)
                else:
                    st.error(t("competitor.failed"))
    with cmd_cols[1]:
        with st.popover(t('popover.result'), use_container_width=True):
            if "competitor_last_result" in st.session_state:
                st.markdown(st.session_state["competitor_last_result"])
            else:
                st.caption(t("competitor.empty_hint"))

    last_names = st.session_state.get("competitor_last_names", (name_a, name_b))
    result_markdown = st.session_state.get("competitor_last_result", "")
    report_body = (
        "<div class='atlas-shell-copy'>" + escape(result_markdown[:4200]).replace("\n", "<br>") + "</div>"
        if result_markdown
        else atlas_empty(t("competitor.empty_title"), t("competitor.empty_desc"))
    )
    display_a = name_a or t('competitor.rival_a')
    display_b = name_b or t('competitor.rival_b')
    scene_html = f"""
    <div class='atlas-stage-map'>
      <svg viewBox='0 0 1200 720' preserveAspectRatio='xMidYMid slice' aria-hidden='true'>
        <path class='gridline' d='M120 0V720M260 0V720M400 0V720M540 0V720M680 0V720M820 0V720M960 0V720M1100 0V720M0 120H1200M0 260H1200M0 400H1200M0 540H1200'/>
        <path d='M170 180H500L548 360L500 540H170L120 360Z' fill='rgba(107,139,219,.16)' stroke='rgba(107,139,219,.76)' stroke-width='2'/>
        <path d='M700 180H1030L1080 360L1030 540H700L652 360Z' fill='rgba(232,93,74,.16)' stroke='rgba(232,93,74,.76)' stroke-width='2'/>
        <path class='route' d='M500 360C555 327 612 327 700 360'/>
        <circle class='signal' cx='600' cy='360' r='18' fill='#d4af37'/><circle cx='600' cy='360' r='54' fill='rgba(212,175,55,.10)'/>
        <text x='205' y='348' font-size='20'>{escape(display_a[:22])}</text>
        <text x='742' y='348' font-size='20'>{escape(display_b[:22])}</text>
        <text x='574' y='414' font-size='16'>{t('label.vs')}</text>
      </svg>
    </div>
    """
    target_rows = [(game.get("name", t('profile.unknown')), game.get("app_id", "")) for game in games[:10]]
    panels = [
        render_atlas_panel(t('competitor.panel.rival_a'), atlas_rows([(t('competitor.panel.name'), display_a), (t('competitor.panel.role'), t('competitor.panel.left'))], compact=True), kicker=t('competitor.stage.start')),
        render_atlas_panel(t('competitor.panel.rival_b'), atlas_rows([(t('competitor.panel.name'), display_b), (t('competitor.panel.role'), t('competitor.panel.right'))], compact=True), kicker=t('competitor.stage.end')),
        render_atlas_panel(t('competitor.panel.engine'), atlas_rows([(t('competitor.panel.llm'), t('label.online') if has_llm else t('label.missing')), (t('competitor.panel.output'), t('competitor.panel.battle'))], compact=True), kicker=t('label.ai')),
    ]
    drawers = [
        render_atlas_drawer(t('competitor.drawer.brief'), report_body, badge=t('label.ready') if result_markdown else t('label.empty')),
        render_atlas_drawer(t('competitor.drawer.targets'), render_atlas_list_editor(t('competitor.drawer.targets_title'), target_rows, compact=True, empty_title=t("competitor.empty_title"), empty_body=t("competitor.empty_hint")), badge=str(len(target_rows))),
        render_atlas_drawer(t('competitor.drawer.last'), atlas_rows([(t('competitor.a'), last_names[0] or display_a), (t('competitor.b'), last_names[1] or display_b)], compact=True), badge=t('label.vs')),
    ]
    render_atlas_stage(
        page_id="competitor",
        title=t('competitor.stage.title'),
        subtitle=t("competitor.subtitle"),
        metrics=[
            (t('competitor.metric.targets'), str(len(game_names))),
            (t('competitor.metric.mode'), t('label.duel')),
            (t('competitor.metric.engine'), t('label.online') if has_llm else t('label.local')),
            (t('competitor.metric.output'), t('popover.brief')),
        ],
        scene_html=scene_html,
        panels=panels,
        drawers=drawers,
        timeline_label=t('competitor.stage.timeline'),
        timeline_start=t('competitor.stage.start'),
        timeline_end=t('competitor.stage.end'),
        accent="#E85D4A",
        mode_label=t('competitor.stage.mode'),
    )
