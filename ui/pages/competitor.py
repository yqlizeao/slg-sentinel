"""SLG Sentinel — 竞品对比页面"""
from __future__ import annotations
import streamlit as st
from src.core.config import load_config
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
    render_page_header(
        t("competitor.title"),
        t("competitor.subtitle"),
        [("targets", str(len(game_names))), ("mode", "duel"), ("engine", "online" if has_llm else "local")],
    )
    render_atlas_ops_board(
        t("competitor.ops.title"),
        t("competitor.ops.subtitle"),
        [("Targets", str(len(game_names))), ("Mode", "duel"), ("Engine", "online" if has_llm else "local"), ("Output", "brief")],
        t("competitor.ops.eyebrow"),
    )

    st.markdown(f"<h3>{t('competitor.select_title')}</h3>", unsafe_allow_html=True)
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if game_names:
            idx_a = st.selectbox(t("competitor.a"), range(len(game_names)), format_func=lambda i: game_names[i], key="comp_a")
            name_a = game_names[idx_a]
        else:
            name_a = st.text_input(t("competitor.a"), placeholder=t("competitor.placeholder"), key="comp_a_text")
    with mode_col2:
        if game_names:
            idx_b = st.selectbox(t("competitor.b"), range(len(game_names)), format_func=lambda i: game_names[i], key="comp_b", index=min(1, len(game_names)-1))
            name_b = game_names[idx_b]
        else:
            name_b = st.text_input(t("competitor.b"), placeholder=t("competitor.placeholder"), key="comp_b_text")

    if not name_a or not name_b:
        render_empty_state("swords", t("competitor.empty_title"), t("competitor.empty_desc"), t("competitor.empty_hint"))
        return
    if name_a == name_b:
        st.info(t("competitor.same_info")); return

    shield_svg = icon("shield", color="#6B8BDB")
    target_svg = icon("target", color="#E85D4A")
    swords_svg = icon("swords", color="#d4af37")
    st.markdown(
        f"""<div class='atlas-duel'>
            <div class='atlas-duel-card'>
                <div class='atlas-mini-label'>{shield_svg} competitor a</div>
                <div style='font-family:Cinzel,serif; font-size:30px; font-weight:700; color:#E8E4DC; margin-top:18px; letter-spacing:2px;'>{name_a}</div>
                <div class='atlas-title-line'></div>
            </div>
            <div class='atlas-duel-vs'>{swords_svg}<div style='font-family:Cinzel,serif; font-size:18px; letter-spacing:2px; margin-left:8px;'>VS</div></div>
            <div class='atlas-duel-card red'>
                <div class='atlas-mini-label'>{target_svg} competitor b</div>
                <div style='font-family:Cinzel,serif; font-size:30px; font-weight:700; color:#E8E4DC; margin-top:18px; letter-spacing:2px;'>{name_b}</div>
                <div class='atlas-title-line'></div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if not has_llm:
        st.warning(t("competitor.llm_warning"))
    if st.button(t("competitor.generate", a=name_a, b=name_b), type="primary", use_container_width=True, disabled=not has_llm):
        with st.spinner(t("competitor.generating")):
            result = _run_comparison(name_a, name_b)
        if result:
            st.session_state["competitor_last_result"] = result
            st.session_state["competitor_last_names"] = (name_a, name_b)
        else:
            st.error(t("competitor.failed"))

    if "competitor_last_result" in st.session_state:
        names = st.session_state.get("competitor_last_names", (name_a, name_b))
        st.markdown("<hr style='border:none; border-top:1px solid rgba(180,160,120,0.08); margin:2rem 0;'/>", unsafe_allow_html=True)
        compare_svg = icon("compare", color="#d4af37")
        st.markdown(f"<h3>{compare_svg} {names[0]} vs {names[1]}</h3>", unsafe_allow_html=True)
        st.markdown(st.session_state["competitor_last_result"])
