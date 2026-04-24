"""
SLG Sentinel — 竞品对比页面
选择两个竞品游戏，自动拉取评论数据并调用 LLM 生成对比分析。
"""
from __future__ import annotations
import streamlit as st
from src.core.config import load_config
from ui.components.common import render_empty_state, render_page_header
from ui.services.app_services import load_targets_config


def _get_taptap_game_options() -> list[dict]:
    try:
        targets = load_targets_config()
        games = targets.get("targets", {}).get("taptap_games", [])
        return [g for g in games if g.get("name") and g.get("app_id")]
    except Exception:
        return []


def _run_comparison(name_a: str, name_b: str) -> str | None:
    from ui.services.overview_service import get_top_comments
    from src.core.llm_client import LLMClient

    config = load_config()
    llm = LLMClient(config)
    provider = llm.get_available_provider()
    if not provider:
        return None

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

    try:
        return llm.chat(prompt, provider=provider, temperature=0.4, timeout=120)
    except Exception as e:
        return f"分析生成失败: {e}"


def _render_game_card(name: str, color: str, label: str) -> None:
    st.markdown(f"""<div style='padding:20px; border:1px solid #EAEAEA; border-top:3px solid {color};
                border-radius:8px; background:#FFF; text-align:center; min-height:100px;'>
        <div style='font-size:11px; color:#888; margin-bottom:6px;'>{label}</div>
        <div style='font-size:20px; font-weight:700; color:#111;'>{name}</div>
    </div>""", unsafe_allow_html=True)


def render_competitor_page() -> None:
    render_page_header("竞品对比分析", "选择两个 SLG 竞品，系统将基于评论数据和 AI 生成对比报告。")

    games = _get_taptap_game_options()
    game_names = [g["name"] for g in games] if games else []

    config = load_config()
    has_llm = bool(config.deepseek_api_key or config.openai_api_key or config.qwen_api_key)

    # 选择区域：支持已配置游戏 + 手动输入
    st.markdown("<h4>选择对比目标</h4>", unsafe_allow_html=True)

    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if game_names:
            idx_a = st.selectbox("竞品 A", range(len(game_names)), format_func=lambda i: game_names[i], key="comp_a")
            name_a = game_names[idx_a]
        else:
            name_a = st.text_input("竞品 A 名称", placeholder="输入游戏名称，如：率土之滨", key="comp_a_text")
    with mode_col2:
        if game_names:
            default_b = 1 if len(game_names) > 1 else 0
            idx_b = st.selectbox("竞品 B", range(len(game_names)), format_func=lambda i: game_names[i], key="comp_b", index=default_b)
            name_b = game_names[idx_b]
        else:
            name_b = st.text_input("竞品 B 名称", placeholder="输入游戏名称，如：三国志战略版", key="comp_b_text")

    if not name_a or not name_b:
        render_empty_state("⚔️", "请选择两个竞品",
                           "从下拉列表中选择或直接输入游戏名称，系统将自动分析两者的差异。",
                           "提示：在「设置」页面添加 TapTap 游戏后可在此直接选择。")
        return

    if name_a == name_b:
        st.info("请选择两个不同的竞品进行对比。")
        return

    # 对照卡片
    card_col1, card_vs, card_col2 = st.columns([1, 0.3, 1])
    with card_col1:
        _render_game_card(name_a, "#2563eb", "竞品 A")
    with card_vs:
        st.markdown("<div style='text-align:center; padding-top:28px; font-size:24px; font-weight:700; color:#ccc;'>VS</div>", unsafe_allow_html=True)
    with card_col2:
        _render_game_card(name_b, "#dc2626", "竞品 B")

    st.markdown("<br>", unsafe_allow_html=True)

    if not has_llm:
        st.warning("竞品对比功能需要配置 LLM API Key（DeepSeek / OpenAI / Qwen）。请前往「设置」页面配置。")

    if st.button(f"生成对比报告：{name_a} vs {name_b}", type="primary", use_container_width=True, disabled=not has_llm):
        with st.spinner("正在调用 AI 分析引擎，请稍候..."):
            result = _run_comparison(name_a, name_b)

        if result:
            st.session_state["competitor_last_result"] = result
            st.session_state["competitor_last_names"] = (name_a, name_b)
        else:
            st.error("对比分析生成失败，请检查 LLM API Key 配置。")

    # 展示结果
    if "competitor_last_result" in st.session_state:
        names = st.session_state.get("competitor_last_names", (name_a, name_b))
        st.markdown("---")
        st.markdown(f"### 📊 {names[0]} vs {names[1]}")
        st.markdown(st.session_state["competitor_last_result"])
