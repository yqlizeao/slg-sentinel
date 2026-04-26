# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

**SLG Sentinel** 是面向一款三国题材 Steam 付费 PC 单机 SLG 游戏研发团队的竞品舆情监控系统，从 B 站、YouTube、TapTap、抖音、快手、小红书采集玩家数据，驱动产品决策。

---

## 常用命令

```bash
# 激活虚拟环境（本项目使用 venv/，不是 .venv/）
source venv/bin/activate

# 启动 GUI 控制台
streamlit run app.py

# 运行全部测试
python -m pytest tests/ -v

# 运行单个测试文件
python -m pytest tests/test_core.py -v

# CLI 采集（免登录模式）
python -m src.cli crawl --platform bilibili --mode actions --limit 50
python -m src.cli crawl --platform youtube --mode actions
python -m src.cli crawl --platform taptap --mode actions

# CLI 采集（本地深度模式，需 Cookie）
python -m src.cli crawl --platform bilibili --mode local

# 生成周报
python -m src.cli analyze --type weekly

# LLM 关键词扩展
python -m src.cli expand-keywords --provider deepseek
```

---

## 三条架构铁律

违反任何一条即视为架构失败：

1. **零侵入**：禁止修改第三方库源码。高风控平台（抖音/快手/小红书）通过 `MediaCrawler` Git Submodule + `subprocess` 沙盒隔离调用。
2. **双模架构**：`--mode actions` 用于 GitHub Actions 免登录定期采集；`--mode local` 用于本地携带 Cookie 深度采集。
3. **CSV 即数据库**：禁止引入任何 DBMS。全量数据以 UTF-8 BOM（`UTF-8-SIG`）格式存于 `data/`，递归采集任务状态存为 JSON 于 `data/recursive_runs/`。

---

## 分层架构

```
app.py              → 全局配置、CSS 注入、侧边栏、页面分发（不承载业务逻辑）
ui/pages/           → 页面布局 + 调用服务（不直接拼磁盘路径，不直接统计 CSV）
ui/components/      → 可复用渲染组件（必须通过显式参数接收数据，不依赖页面局部变量）
ui/services/        → GUI 侧非 UI 逻辑（统计、文件扫描、关键词、候选词挖掘、采集汇总）
src/cli.py          → CLI 参数解析与分发（不承载业务编排）
src/services/       → CLI 侧采集/画像/报告编排
src/adapters/       → 6 平台适配器（各自独立，通过 base.py 抽象）
src/core/           → 配置、数据模型、CSV 持久层、LLM 客户端、重试装饰器
src/analysis/       → 情感分析、用户画像、周报生成
```

**关键边界**：`ui/` 和 `src/` 是两条平行服务链，GUI 调用 `ui/services/`，CLI 调用 `src/services/`，两者共享 `src/core/` 的模型和工具。

---

## 核心数据模型（`src/core/models.py`）

| 模型 | 存储位置 | 说明 |
|------|---------|------|
| `VideoSnapshot` | `data/*/videos/*.csv` | 视频多维指标快照 |
| `Comment` | `data/*/comments/*.csv` | 评论文本、点赞、IP 属地 |
| `TapTapReview` | `data/community_platforms/taptap/comments/*.csv` | 含星级评分和游玩时长 |
| `UserProfile` | `data/profiles/*.csv` | 用户画像推断结果 |

所有模型基于 ID 字段实现 `__eq__` 和 `__hash__`，`CSVStore.save()` 自动去重。

---

## 配置与密钥

- `keywords.yaml`：搜索关键词列表 + LLM 扩词配置（代码默认 `expansion.enabled = true`，当前配置文件设为 `false`）
- `targets.yaml`：定向监控的 B 站 UID、YouTube 频道 ID、TapTap 游戏 ID
- `secrets.yaml`：本地敏感凭证（已 gitignore），格式见 `src/core/config.py`
- 环境变量优先于 `secrets.yaml`，支持：`DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `QWEN_API_KEY` / `BILI_SESSDATA`

---

## 数据持久化规范

- 写入统一走 `CSVStore.save()`，自动处理去重和 BOM 头
- 搜索指标 CSV 表头为 14 列，`crawl_service.py` 会自动迁移旧 10 列格式
- 递归采集任务通过 `ui/services/recursive_runs.py` 写入 JSON

---

## GUI 视觉与文案约束

- **Dark Mode（War Atlas 工业风）**，深黑底 `#0a0c10`、金色强调 `#d4af37`、米色文字 `#e8e4dc`，标题用 Cinzel 字体，正文用 IBM Plex Sans
- 大量使用内联 HTML 渲染，避免 Streamlit 原生粗糙组件
- 表单采用 Pipeline 流水线（STEP 01 → STEP 05），禁止横向堆砌选项

**禁止出现的词汇**：探针、神经干线、潮汐、底座、阵列、汪洋、大盘、穿刺、渗透

**推荐使用**：监控目标、采集时间、系统节点、图表、分析组件、数据源

---

## 网络请求规范

- 所有适配器强制 `time.sleep(1.0+)` 礼貌间隔
- 网络波动用 `src/core/retry.py` 中的 `@retry_on_failure` 装饰器处理

---

## 待解决的核心遗留问题

- **画像推测引擎**：`profiler.py` 当前为纯启发式规则（关键词匹配），精度有限，待接入 LLM 补强
- **周报 LLM 聚类**：`weekly_report.py` 第 4 节框架已实现（`_generate_llm_insights()`），需配置 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY` 激活
- **递归采集断点续跑**：`recursive_runs.py` 已预留 `pending_queue` 和 `paused_node_id` 字段，待实现 queue 消费与恢复逻辑
- **MediaCrawler 全域联调**：local 模式下的扫码沙盒流程待完整验证
