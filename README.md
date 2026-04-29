# SLG Sentinel

> 面向 Steam 单机 SLG 研发的多平台竞品舆情监控系统

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-GUI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI-2088FF?logo=github-actions&logoColor=white)](https://github.com/yqlizeao/slg-sentinel/actions)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 项目简介

我们正在研发一款**三国题材的付费买断制 PC 单机 SLG 游戏**，目标平台为 Steam。

SLG Sentinel 是为这个项目配套的市场情报工具——自动采集 B 站、YouTube、TapTap、抖音、小红书、快手等平台的 SLG 品类视频与评论数据，通过情感分析和用户画像推断，帮助研发团队理解：
- 硬核策略玩家对现有 SLG 手游（三战、率土、万国觉醒等）的核心不满
- 他们真正期望的 PC 单机体验是什么
- 哪些竞品 KOL 和社区话题值得关注

---

## 架构特性

| 特性 | 说明 |
|------|------|
| **双模运行** | 云端免登（GitHub Actions 定时采集）+ 本地深度（Cookie 鉴权采集评论画像） |
| **零侵入** | 不修改任何第三方库源码，高风控平台通过 Git Submodule 隔离 |
| **CSV 数据库** | 全量数据落盘为 UTF-8 BOM CSV，Excel 直接打开，无需任何 DBMS |
| **6 平台覆盖** | B 站 · YouTube · TapTap · 抖音 · 快手 · 小红书 |
| **AI 分析** | 离线情感分析 + LLM 关键词扩展 + 启发式用户画像 |
| **话题探索** | 递归多轮采集 + 自动候选词挖掘 + 话题分类推荐 |

---

## 快速开始

### 1. 克隆仓库

```bash
# 包含 MediaCrawler 子模块，需要 --recursive
git clone --recursive https://github.com/yqlizeao/slg-sentinel.git
cd slg-sentinel
```

### 2. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate

# 安装全部平台适配器 + GUI
pip install -e ".[all,gui]"
```

### 3. 启动控制台

```bash
streamlit run app.py
```

控制台提供 7 个功能页面：
- **总览**：本周核心发现（LLM 生成）、关键词趋势图、高赞评论精选、平台数据量、全网热帖排行
- **采集**：选择平台 → 模式 → 深度 → 配额，一键启动单次采集
- **递归采集（话题探索）**：从起始话题出发，自动完成多轮采集、关键词提炼、扩展和停止判断
- **画像**：玩家派系标签、消费类型分布、核心追踪名单
- **智能报表**：情感分布图表 + 竞品声量柱状图 + Markdown 周报
- **竞品对比**：选择两个 TapTap 竞品，LLM 自动生成优劣势对比与产品机会分析
- **设置**：在线编辑 targets / keywords / 密钥配置

### 4. CLI 命令行

```bash
# B 站免登录采集（适合 CI/CD）
python -m src.cli crawl --platform bilibili --mode actions --limit 50

# YouTube 本地深度采集
python -m src.cli crawl --platform youtube --mode local

# TapTap 评论采集
python -m src.cli crawl --platform taptap --mode actions

# 生成周报
python -m src.cli analyze --type weekly

# LLM 关键词扩展
python -m src.cli expand-keywords --provider deepseek
```

---

## 目录结构

```
slg-sentinel/
├── app.py                      # Streamlit 控制台（7 页面导航）
├── ui/
│   ├── pages/                  # 总览、采集、递归采集、画像、报表、设置
│   ├── components/             # 通用 UI 组件与采集页组件
│   └── services/               # GUI 服务层
│       ├── app_services.py     # 统计、文件扫描、关键词、搜索指标、候选词挖掘
│       ├── recursive_runs.py   # 递归采集任务 JSON 持久层
│       └── recursive_insights.py # 话题分类与探索摘要
├── src/
│   ├── cli.py                  # CLI 入口：参数解析与命令分发
│   ├── core/                   # 配置、模型、存储、重试
│   ├── services/               # CLI 服务层：采集、画像、报告编排
│   ├── adapters/               # 6 平台采集适配器
│   └── analysis/               # 情感分析、画像、周报
├── tests/                      # pytest 测试套件（64 条）
├── data/                       # CSV 时序数据（data 分支）
│   ├── video_platforms/        # B 站 / YouTube 视频 + 评论
│   ├── community_platforms/    # TapTap 评论
│   ├── search_metrics/         # 关键词搜索量记录
│   ├── recursive_runs/         # 递归采集任务 JSON
│   ├── runtime/                # 临时关键词等运行时产物
│   ├── profiles/               # 用户画像推断结果
│   └── summary/                # 每日全网快照汇总
├── reports/                    # 周报输出目录
├── .github/workflows/          # 4 个自动化采集/分析 workflow
├── cloudflare_pages/           # 公网部署入口
├── MediaCrawler/               # Git Submodule（抖音/快手/小红书引擎）
├── keywords.yaml               # 搜索关键词配置
├── targets.yaml                # 监控目标配置
├── CLAUDE.md                   # Claude Code 工程指南
└── GEMINI.md                   # Gemini 工程指南
```

---

## 话题探索（递归采集）

系统的核心差异化功能。从起始话题出发，自动完成多轮 **采集 → 候选词挖掘 → 扩展 → 再采集** 的闭环：

### 工作流程

1. 用户选择平台、探索策略（标准/保守/深度）、起始关键词
2. 系统逐个关键词执行 CLI 采集，记录搜索指标
3. 从采集结果中用 jieba 分词挖掘新候选词，按推荐指数排序
4. 将高分候选词作为下一轮关键词，重复直到达到深度限制或无新发现

### 话题分类

| 分类 | 条件 | 建议 |
|------|------|------|
| 强推荐 | 推荐指数 ≥ 80，非泛化词，搜索未封顶 | 直接进入下一轮探索 |
| 待确认 | 推荐指数 ≥ 50，但泛化或搜索封顶 | 人工确认证据后决定 |
| 长尾机会 | 推荐指数 ≥ 12，非泛化词 | 小规模验证 |
| 不建议 | 其余 | 跳过 |

### 推荐指数计算

```
推荐指数 = 标题贡献(2.2 × 视频热度) + 标签贡献(2.8 × 视频热度) + 评论贡献(1.25 × 点赞系数)
视频热度系数 = 1 + min(log10(播放量), 6) / 5
评论点赞系数 = 1 + min(log10(点赞数), 4) / 4
```

---

## 自动化采集

项目配置了 4 个 GitHub Actions Workflow，每日自动运行：

| Workflow | 时间 (UTC) | 平台 | 依赖 |
|----------|-----------|------|------|
| `crawl-bilibili.yml` | 16:00 | B 站 | bilibili-api-python |
| `crawl-youtube.yml` | 16:30 | YouTube | yt-dlp + scrapetube |
| `crawl-taptap.yml` | 17:00 | TapTap | requests + bs4 |
| `weekly-analysis.yml` | 每周一 | 全平台 | - |

采集数据自动 commit 到 `data` 分支，与代码分支隔离。

---

## 配置说明

### keywords.yaml

定义搜索关键词（统一扁平列表）和 LLM 扩词设置：

```yaml
seed_keywords:
  games:
    - 三国志战略版
    - 率土之滨
    - 三国谋定天下
    - 世界启元
    # ...
  categories: []
expansion:
  enabled: false
  llm_provider: deepseek
  max_expanded_keywords: 53
```

### targets.yaml

定义定向监控的频道和游戏：

```yaml
targets:
  bilibili_channels:
    - { name: "阿志-三国志战略版", uid: "454802537" }
  youtube_channels:
    - { name: "SLG策略分析室", channel_id: "UCxxx" }
  taptap_games:
    - { name: "三国志·战略版", app_id: "139546" }
    - { name: "率土之滨", app_id: "4682" }
    - { name: "三国：谋定天下", app_id: "231537" }
    # ... 共 10 个监控游戏
```

### 密钥配置

本地创建 `secrets.yaml`（已 gitignore）或设置环境变量：

```yaml
llm_keys:
  deepseek: "sk-..."
bilibili:
  sessdata: "your_sessdata"
```

---

## 测试

```bash
python -m pytest tests/ -v
```

当前覆盖 64 条测试，验证：模型身份判等、CSV 幂等存储、情感分析准确性、配置加载容错、周报生成、TapTap review 转换、用户画像聚合与保存、递归采集任务 CRUD、搜索指标封顶判定与 CSV header 迁移、话题分组规则与泛化词检测、探索摘要聚合、LLM 客户端调用与降级、适配器搜索解析。

---

## 公网部署

采用 Cloudflare Pages iframe 模式：

1. 将 Streamlit 应用部署到 Streamlit Cloud
2. 将 `cloudflare_pages/` 上传到 Cloudflare Pages
3. 通过自定义域名访问（需 VPN）

此方案绕过了 Streamlit 原生路由检测的域名锁定问题。

---

## AI 助手入口

本项目附带两份 AI 工程指南文件，分别适配不同的 AI 编程助手：

- **[CLAUDE.md](./CLAUDE.md)** — Claude Code 工程指南（适用于 Claude Code / Cursor）
- **[GEMINI.md](./GEMINI.md)** — Gemini 工程指南（适用于 Gemini CLI / Gemini Code Assist）

在新会话开始时，请让 AI 先阅读对应的工程指南文件以建立项目上下文。

---

*License: MIT © 2026 yqlizeao*
