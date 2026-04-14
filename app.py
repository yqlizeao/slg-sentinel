"""
SLG Sentinel — Streamlit 控制台

运行方式：
    streamlit run app.py

依赖：
    pip install streamlit
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
import yaml

# ─── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SLG Sentinel 舆情控制台",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 常量 ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
KEYWORDS_FILE = ROOT / "keywords.yaml"
TARGETS_FILE = ROOT / "targets.yaml"


# ─── 工具函数 ──────────────────────────────────────────────────────────────────
def run_cli(args: list[str]) -> tuple[str, str, int]:
    """运行 CLI 子命令，实时返回 stdout/stderr/returncode"""
    cmd = [sys.executable, "-m", "src.cli"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    return result.stdout, result.stderr, result.returncode


def count_csv_rows(path: Path) -> int:
    """统计 CSV 行数（不含表头）"""
    if not path.exists():
        return 0
    try:
        with open(path, encoding="utf-8-sig") as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0


def get_platform_stats(platform: str) -> dict:
    """获取平台当天的数据量统计"""
    today = datetime.now().strftime("%Y-%m-%d")
    video_dir = DATA_DIR / platform / "videos"
    comment_dir = DATA_DIR / platform / "comments"
    review_dir = DATA_DIR / platform / "reviews"

    videos = sum(
        count_csv_rows(f)
        for f in video_dir.glob(f"{today}_*.csv")
    ) if video_dir.exists() else 0

    comments = sum(
        count_csv_rows(f)
        for f in (comment_dir if comment_dir.exists() else review_dir if review_dir.exists() else Path("/dev/null/x")).parent.glob("*.csv")
    ) if True else 0

    # 更简洁的方式
    if comment_dir.exists():
        comments = sum(count_csv_rows(f) for f in comment_dir.glob(f"{today}_*.csv"))
    elif review_dir.exists():
        comments = sum(count_csv_rows(f) for f in review_dir.glob(f"{today}_*.csv"))
    else:
        comments = 0

    return {"videos": videos, "comments": comments}


def get_latest_report() -> Optional[Path]:
    """获取最新的周报文件"""
    if not REPORTS_DIR.exists():
        return None
    reports = sorted(REPORTS_DIR.glob("*_weekly_report.md"), reverse=True)
    return reports[0] if reports else None


def load_yaml(path: Path) -> dict:
    """安全加载 YAML"""
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# ─── 侧边栏 ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=60)
    st.title("SLG Sentinel")
    st.caption("竞品舆情监控系统")
    st.divider()

    page = st.radio(
        "导航",
        ["📊 数据总览", "🕷️ 数据采集", "📈 生成周报", "🔑 关键词扩展", "⚙️ 配置管理"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption(f"📅 当前日期：{datetime.now().strftime('%Y-%m-%d')}")
    st.caption("💡 首次使用请先配置 targets.yaml")


# ═══════════════════════════════════════════════════════════════════════════════
# 页面 1：数据总览
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 数据总览":
    st.title("📊 数据总览")

    # 平台指标卡
    platforms = ["bilibili", "youtube", "taptap"]
    platform_labels = {"bilibili": "🟥 B 站", "youtube": "▶️ YouTube", "taptap": "🎮 TapTap"}

    cols = st.columns(3)
    for i, platform in enumerate(platforms):
        stats = get_platform_stats(platform)
        with cols[i]:
            st.metric(
                label=platform_labels[platform],
                value=f"{stats['videos']} 条视频",
                delta=f"{stats['comments']} 条评论/评分（今日）",
            )

    st.divider()

    # 最新周报预览
    st.subheader("📄 最新舆情周报")
    report = get_latest_report()
    if report:
        st.caption(f"报告文件：`{report.name}`")
        with st.expander("📖 展开查看完整周报", expanded=True):
            st.markdown(report.read_text(encoding="utf-8"))
    else:
        st.info("暂无周报。请先完成数据采集，然后在「生成周报」页点击生成。")

    # 数据文件清单
    st.divider()
    st.subheader("📂 数据文件清单")
    if DATA_DIR.exists():
        for platform in platforms:
            p_dir = DATA_DIR / platform
            if p_dir.exists():
                csvs = list(p_dir.rglob("*.csv"))
                if csvs:
                    with st.expander(f"{platform_labels[platform]}（{len(csvs)} 个文件）"):
                        for csv in sorted(csvs, reverse=True)[:10]:
                            rows = count_csv_rows(csv)
                            st.text(f"  📄 {csv.name}  ({rows} 行)")
    else:
        st.warning("data/ 目录不存在，请先运行采集。")


# ═══════════════════════════════════════════════════════════════════════════════
# 页面 2：数据采集
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🕷️ 数据采集":
    st.title("🕷️ 数据采集")
    st.info("点击按钮将在后台调用 CLI，日志实时显示在下方（采集耗时较长请耐心等待）。")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("平台选择")
        platform = st.selectbox(
            "选择采集平台",
            ["bilibili", "youtube", "taptap"],
            format_func=lambda x: {"bilibili": "🟥 B 站", "youtube": "▶️ YouTube", "taptap": "🎮 TapTap"}[x],
        )
        mode = st.radio("运行模式", ["actions（免登录/Actions）", "local（本地完整版）"])
        mode_val = "actions" if "actions" in mode else "local"

    with col2:
        st.subheader("采集说明")
        hints = {
            "bilibili": "🟥 **B 站**：使用 bilibili-api-python 免登录采集，热门视频评论受风控影响可能为 0。配置 `BILI_SESSDATA` 可解除。",
            "youtube": "▶️ **YouTube**：使用 yt-dlp 搜索，每个关键词约 60-75 秒，8 个关键词约需 10 分钟，请勿中断。",
            "taptap": "🎮 **TapTap**：采集 targets.yaml 中配置的游戏信息和评论，速度较快。",
        }
        st.markdown(hints[platform])

    st.divider()

    if st.button(f"🚀 开始采集 {platform}", type="primary", use_container_width=True):
        log_area = st.empty()
        progress = st.progress(0, text="正在采集中...")

        with st.spinner(f"正在采集 {platform}，请稍候..."):
            stdout, stderr, code = run_cli(["crawl", "--platform", platform, "--mode", mode_val])

        progress.progress(100, text="完成！")

        if code == 0:
            st.success("✅ 采集完成！")
        else:
            st.error(f"❌ 采集失败（退出码 {code}）")

        with st.expander("📋 运行日志", expanded=True):
            combined = (stdout + "\n" + stderr).strip()
            st.code(combined or "（无输出）", language="text")


# ═══════════════════════════════════════════════════════════════════════════════
# 页面 3：生成周报
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 生成周报":
    st.title("📈 生成舆情周报")

    st.markdown("""
    周报将从 `data/` 目录读取当天各平台快照和评论，计算本周增量、情感分布、竞品提及，
    并扫描高赞负面评论作为预警，最终生成 Markdown 格式报告保存到 `reports/` 目录。
    """)

    col1, col2 = st.columns([1, 2])

    with col1:
        custom_date = st.date_input("报告日期", value=datetime.now())
        date_str = custom_date.strftime("%Y-%m-%d")
        st.caption(f"将生成 `{date_str}_weekly_report.md`")

        generate_btn = st.button("🗞️ 生成周报", type="primary", use_container_width=True)

    with col2:
        st.info("""
        **提示**  
        - 首次运行无上周数据对比，播放量增量会显示当前全量值  
        - 建议每天开始采集后，再在周一点击生成当周报告  
        - 报告会自动同步到 `reports/` 目录
        """)

    if generate_btn:
        with st.spinner("正在分析数据并生成周报..."):
            stdout, stderr, code = run_cli([
                "analyze", "--type", "weekly",
                "--date", date_str
            ])

        if code == 0:
            st.success(f"✅ 周报生成成功：`reports/{date_str}_weekly_report.md`")
            report_path = REPORTS_DIR / f"{date_str}_weekly_report.md"
            if report_path.exists():
                st.divider()
                st.markdown(report_path.read_text(encoding="utf-8"))
        else:
            st.error("❌ 生成失败")
            st.code(stderr or stdout, language="text")


# ═══════════════════════════════════════════════════════════════════════════════
# 页面 4：关键词扩展
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔑 关键词扩展":
    st.title("🔑 AI 关键词扩展")

    st.markdown("""
    使用大语言模型（DeepSeek / OpenAI 等）根据 `keywords.yaml` 中的种子词，
    自动联想 SLG 游戏的长尾搜索词、俗称、话术等，扩大监控覆盖面。
    """)

    col1, col2 = st.columns(2)
    with col1:
        provider = st.selectbox("LLM 提供商", ["deepseek", "openai", "qwen"])
        max_kw = st.slider("最大关键词数", 10, 100, 50)

    with col2:
        import os
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if api_key:
            st.success("✅ 检测到 DEEPSEEK_API_KEY 环境变量")
        else:
            st.warning("⚠️ 未检测到 `DEEPSEEK_API_KEY`，请先在终端设置：\n```\nexport DEEPSEEK_API_KEY=sk-xxx\n```")

    # 当前种子词预览
    kw_data = load_yaml(KEYWORDS_FILE)
    seed = kw_data.get("seed_keywords", {})
    current_games = seed.get("games", [])
    st.caption(f"当前种子词（{len(current_games)} 个游戏）：{', '.join(current_games)}")

    if st.button("✨ 开始 AI 扩展", type="primary", disabled=not api_key):
        with st.spinner(f"正在调用 {provider} 扩展关键词..."):
            stdout, stderr, code = run_cli([
                "expand-keywords",
                "--provider", provider,
                "--max-keywords", str(max_kw),
            ])

        if code == 0:
            st.success("✅ 扩展完成！")
            st.code(stdout, language="text")
        else:
            st.error("❌ 扩展失败")
            st.code(stderr or stdout, language="text")


# ═══════════════════════════════════════════════════════════════════════════════
# 页面 5：配置管理
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ 配置管理":
    st.title("⚙️ 配置管理")

    tab1, tab2 = st.tabs(["🎯 跟踪目标 (targets.yaml)", "🔍 关键词 (keywords.yaml)"])

    with tab1:
        st.subheader("跟踪目标配置")
        targets = load_yaml(TARGETS_FILE)
        t_data = targets.get("targets", targets)

        # TapTap 游戏列表
        st.markdown("**🎮 TapTap 游戏（已填入真实 app_id）**")
        games = t_data.get("taptap_games", [])
        if games:
            for g in games:
                col1, col2 = st.columns([2, 1])
                col1.text(g.get("name", "未命名"))
                col2.code(g.get("app_id", "?"), language=None)
        else:
            st.info("暂未配置 TapTap 游戏，请编辑 targets.yaml")

        # B站频道
        st.markdown("**📺 B 站频道**")
        channels = t_data.get("bilibili_channels", [])
        if channels:
            for c in channels:
                st.text(f"{c.get('name', '')}  |  UID: {c.get('uid', '未配置')}")
        else:
            st.info("暂未配置 B 站频道")

        # YouTube 频道
        st.markdown("**▶️ YouTube 频道**")
        yt_channels = t_data.get("youtube_channels", [])
        if yt_channels:
            for c in yt_channels:
                st.text(f"{c.get('name', '')}  |  {c.get('channel_id', '未配置')}")
        else:
            st.info("暂未配置 YouTube 频道")

        st.divider()
        st.caption("如需修改，直接编辑项目根目录的 `targets.yaml` 文件，无需重启应用。")
        with st.expander("📝 查看 targets.yaml 原始内容"):
            st.code(TARGETS_FILE.read_text(encoding="utf-8"), language="yaml")

    with tab2:
        st.subheader("关键词配置")
        kw_data = load_yaml(KEYWORDS_FILE)
        seed = kw_data.get("seed_keywords", {})

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**游戏关键词**")
            for kw in seed.get("games", []):
                st.markdown(f"- `{kw}`")

        with col2:
            st.markdown("**品类关键词**")
            for kw in seed.get("categories", []):
                st.markdown(f"- `{kw}`")

        expansion = kw_data.get("expansion", {})
        st.info(
            f"AI 扩展：{'✅ 已启用' if expansion.get('enabled') else '❌ 已禁用'} "
            f"| 提供商：`{expansion.get('llm_provider', 'deepseek')}` "
            f"| 最大数量：{expansion.get('max_expanded_keywords', 50)}"
        )

        with st.expander("📝 查看 keywords.yaml 原始内容"):
            st.code(KEYWORDS_FILE.read_text(encoding="utf-8"), language="yaml")
