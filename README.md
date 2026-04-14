# SLG Sentinel

> SLG 游戏营销舆情监控系统 —— 多平台数据采集 + 情感分析 + 周期报告

[![B站采集](https://github.com/your-username/slg-sentinel/actions/workflows/crawl-bilibili.yml/badge.svg)](https://github.com/your-username/slg-sentinel/actions/workflows/crawl-bilibili.yml)
[![YouTube采集](https://github.com/your-username/slg-sentinel/actions/workflows/crawl-youtube.yml/badge.svg)](https://github.com/your-username/slg-sentinel/actions/workflows/crawl-youtube.yml)
[![TapTap采集](https://github.com/your-username/slg-sentinel/actions/workflows/crawl-taptap.yml/badge.svg)](https://github.com/your-username/slg-sentinel/actions/workflows/crawl-taptap.yml)

## 架构概览

```
slg-sentinel/
├── .github/workflows/   # GitHub Actions 工作流（定时采集 + 周报）
├── src/
│   ├── core/            # 核心框架（models / csv_store / config）
│   ├── adapters/        # 各平台适配器（bilibili / youtube / taptap）
│   ├── analysis/        # 分析层（sentiment / weekly_report）
│   └── cli.py           # 唯一用户入口
├── data/                # CSV 数据（存储在 data 分支）
├── reports/             # 周度报告 Markdown（存储在 data 分支）
├── keywords.yaml        # 种子关键词配置
└── targets.yaml         # 跟踪目标配置
```

### 三条铁律

| 铁律 | 说明 |
|------|------|
| ① 零侵入 | 第三方仓库只通过 pip 引入，不修改源码 |
| ② 双模运行 | `--mode actions`（免登录） / `--mode local`（完整功能） |
| ③ CSV 即数据库 | 全部数据存储为 CSV，UTF-8 with BOM，通过 git 管理 |

## 快速开始

### 安装依赖

```bash
# 仅核心（Phase 0）
pip install pyyaml

# Phase 1：B站采集
pip install bilibili-api-python pyyaml

# Phase 2：YouTube采集
pip install yt-dlp scrapetube youtube-comment-downloader

# Phase 3：TapTap采集
pip install requests beautifulsoup4

# 全部安装
pip install -e ".[all]"
```

### 配置

1. 编辑 `keywords.yaml`，填入目标 SLG 游戏名称
2. 编辑 `targets.yaml`，填入要跟踪的频道/游戏 ID
3. 设置环境变量（需要时）：
   ```bash
   export DEEPSEEK_API_KEY="your-key"
   export BILI_SESSDATA="your-sessdata"  # 可选，B站深度功能
   ```

### CLI 使用

```bash
# 采集数据
python -m src.cli crawl --platform bilibili --mode actions
python -m src.cli crawl --platform youtube --mode actions
python -m src.cli crawl --platform taptap --mode actions

# 本地完整采集（需扫码登录）
python -m src.cli crawl --platform douyin --mode local

# 用户画像（需 Cookie）
python -m src.cli profile --platform bilibili --video-id BV1xxxxxxxxxx

# 分析报告
python -m src.cli analyze --type weekly
python -m src.cli analyze --type sentiment --platform bilibili

# 关键词扩展
python -m src.cli expand-keywords --provider deepseek
```

## 实施 Phase

| Phase | 功能 | 状态 |
|-------|------|------|
| Phase 0 | 骨架搭建（models / csv_store / config / cli） | ✅ 完成 |
| Phase 1 | B站适配器 + GitHub Actions | 🔲 待实施 |
| Phase 2 | YouTube 适配器 + GitHub Actions | 🔲 待实施 |
| Phase 3 | TapTap 适配器 + GitHub Actions | 🔲 待实施 |
| Phase 4 | 分析层（情感分析 + 周报） | 🔲 待实施 |
| Phase 5 | 进阶功能（用户画像 + MediaCrawler） | 🔲 待实施 |

## 数据分支说明

- **`main` 分支**：源代码、配置文件、工作流
- **`data` 分支**：CSV 数据文件、周度报告

GitHub Actions 自动将采集结果 commit 到 `data` 分支，与代码分支完全隔离。

## GitHub Secrets 配置

| Secret | 用途 | 必需 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | 周报 AI 生成 | Phase 4+ |
| `BILI_SESSDATA` | B站深度画像 | Phase 5（可选） |

⚠️ **安全提醒**：Cookie 等登录凭证绝不提交到代码仓库，也不存储在 GitHub Secrets 中传给 Actions（扫码登录类平台只在本地运行）。

## 工程纪律

- 请求频率：B站和 TapTap 每请求间隔 ≥ 1 秒
- 错误处理：所有网络操作有 try-except + logging
- 幂等性：同一天重复运行不产生重复数据（按 `video_id` 去重）
- 日志格式：`[%(asctime)s] %(levelname)s %(name)s: %(message)s`
