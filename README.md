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

控制台提供 5 个功能页面：
- **总览**：系统健康状态、平台数据量、全网热帖排行
- **采集**：选择平台 → 模式 → 深度 → 配额，一键启动
- **画像**：玩家派系标签、消费类型分布、核心追踪名单
- **智能报表**：情感分布图表 + 竞品声量柱状图 + Markdown 周报
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
python -m src.cli expand --provider deepseek
```

---

## 目录结构

```
slg-sentinel/
├── app.py                      # Streamlit 控制台
├── src/
│   ├── cli.py                  # CLI 入口
│   ├── core/                   # 配置、模型、存储、重试
│   ├── adapters/               # 6 平台采集适配器
│   └── analysis/               # 情感分析、画像、周报
├── tests/                      # pytest 测试套件
├── data/                       # CSV 时序数据（data 分支）
├── .github/workflows/          # 4 个自动化采集/分析 workflow
├── cloudflare_pages/           # 公网部署入口
├── MediaCrawler/               # Git Submodule（抖音/快手/小红书引擎）
├── keywords.yaml               # 搜索关键词配置
├── targets.yaml                # 监控目标配置
└── Gemini.md                   # AI 助手工程指南
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

定义搜索关键词（游戏名 + 品类词）和 LLM 扩词设置：

```yaml
seed_keywords:
  games:
    - 三国志战略版
    - 率土之滨
    - 万国觉醒
  categories:
    - SLG手游
    - 策略游戏
expansion:
  enabled: true
  llm_provider: deepseek
  max_expanded_keywords: 50
```

### targets.yaml

定义定向监控的频道和游戏：

```yaml
targets:
  bilibili_channels:
    - { name: "某UP主", uid: "123456" }
  youtube_channels:
    - { name: "SomeChannel", channel_id: "UC..." }
  taptap_games:
    - { name: "率土之滨", app_id: "34222" }
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

当前覆盖 20 条测试，验证：模型身份判等、CSV 幂等存储、情感分析准确性、配置加载容错。

---

## 公网部署

采用 Cloudflare Pages iframe 模式：

1. 将 Streamlit 应用部署到 Streamlit Cloud
2. 将 `cloudflare_pages/` 上传到 Cloudflare Pages
3. 通过自定义域名访问（需 VPN）

此方案绕过了 Streamlit 原生路由检测的域名锁定问题。

---

## AI 助手入口

本项目附带 **[Gemini.md](./Gemini.md)** 工程指南文件。如果你使用 AI 编程助手（Gemini / Cursor / Claude 等），请在新会话开始时让 AI 先阅读该文件以建立项目上下文。

---

*License: MIT © 2026 yqlizeao*
