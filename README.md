# SLG Sentinel

> **SLG 游戏跨平台竞品舆情监控系统**
> 自动采集 B 站、YouTube、TapTap 数据，每周产出竞品动态 + 玩家情感周报。

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-自动化-2088FF?logo=github-actions&logoColor=white)](https://github.com/yqlizeao/slg-sentinel/actions)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 功能概览

| 能力 | 说明 |
|------|------|
| 📱 **多平台采集** | B 站（视频+评论）、YouTube（视频+评论）、TapTap（游戏评分+长评） |
| 🤖 **GitHub Actions** | 三套采集 + 一套周报，全自动定时运行，无需服务器 |
| 📊 **舆情周报** | 播放量增量 Top10、情感分布、竞品提及频次、负面预警摘录 |
| 🧠 **AI 关键词扩展** | 接入 DeepSeek / OpenAI 自动联想竞品话术与长尾搜索词 |
| 👤 **用户画像** | 基于评论语义推断玩家年龄段、付费倾向、硬核/休闲标签 |
| 🔌 **MediaCrawler 桥接** | 本地 MediaCrawler 采集抖音/快手/小红书后一键导入 |

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/yqlizeao/slg-sentinel.git
cd slg-sentinel

# 全量安装（本地开发）
pip install -e ".[all]"

# 仅安装特定平台（按需）
pip install -e ".[bilibili]"    # B站
pip install -e ".[youtube]"     # YouTube
pip install -e ".[taptap]"      # TapTap
```

### 2. 配置关键词与目标

编辑 `keywords.yaml`（搜索词）和 `targets.yaml`（指定跟踪目标）：

```yaml
# keywords.yaml — 种子关键词，AI 会自动扩展
seed_keywords:
  games:
    - 率土之滨
    - 三国志战略版
    - 万国觉醒
  categories:
    - SLG手游
```

```yaml
# targets.yaml — 配置具体游戏和频道
targets:
  taptap_games:
    - name: "率土之滨"
      app_id: "4682"        # TapTap 游戏 ID
  bilibili_channels:
    - name: "官方账号名称"
      uid: "123456789"      # B站 UID
```

### 3. 配置密钥（可选）

```bash
export DEEPSEEK_API_KEY="sk-xxx"    # AI 关键词扩展
export BILI_SESSDATA="xxx"           # B站深度采集（无则免登录运行）
```

### 4. 本地运行

```bash
# 采集数据
python -m src.cli crawl --platform bilibili --mode local
python -m src.cli crawl --platform youtube  --mode local
python -m src.cli crawl --platform taptap   --mode local

# 生成本周舆情周报
python -m src.cli analyze --type weekly

# 用 AI 扩展关键词（需 DEEPSEEK_API_KEY）
python -m src.cli expand-keywords --provider deepseek

# 生成视频的用户画像
python -m src.cli profile --platform youtube --video-id OiN5f7DT1Og
```

---

## GitHub Actions 自动化

将代码推送到 GitHub 后，以下工作流将**自动定时执行**：

| 工作流 | 触发时间（UTC） | 北京时间 | 说明 |
|--------|----------------|----------|------|
| `crawl-bilibili.yml` | 每日 16:00 | 次日 00:00 | 采集 B 站视频快照 |
| `crawl-youtube.yml`  | 每日 16:30 | 次日 00:30 | 采集 YouTube 视频快照 |
| `crawl-taptap.yml`   | 每日 17:00 | 次日 01:00 | 采集 TapTap 游戏评分 |
| `weekly-analysis.yml`| 每周一 02:00 | 周一 10:00 | 生成竞品舆情周报 |

数据自动提交到独立的 **`data` 分支**，代码在 **`main` 分支**，互不干扰。

### 配置 GitHub Secrets

在 `Settings → Secrets and variables → Actions` 中添加：

| Secret 名称 | 说明 | 必填 |
|-------------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key，用于 AI 关键词扩展 | 可选 |
| `BILI_SESSDATA` | B站 Cookie，用于深度评论采集 | 可选 |

---

## 数据存储结构

所有数据以 **UTF-8 BOM 编码的 CSV** 存储（可直接用 Excel 打开），按日期分片：

```
data/
├── bilibili/
│   ├── videos/   2026-04-15_videos.csv
│   └── comments/ 2026-04-15_{video_id}_comments.csv
├── youtube/
│   ├── videos/   2026-04-15_videos.csv
│   └── comments/ 2026-04-15_{video_id}_comments.csv
├── taptap/
│   ├── videos/   2026-04-15_videos.csv       # 游戏基础信息快照
│   └── reviews/  2026-04-15_reviews.csv       # 玩家长评（TapTapReview 格式）
├── snapshots/    2026-04-15_snapshots.csv      # 跨平台合并快照，用于计算周增量
└── profiles/     user_games/                  # 用户画像
reports/
└── 2026-04-15_weekly_report.md               # Markdown 周报
```

---

## 项目架构

```
src/
├── cli.py                    # 命令行入口（argparse）
├── core/
│   ├── models.py             # 数据模型（VideoSnapshot, Comment, TapTapReview, UserProfile）
│   ├── csv_store.py          # 存储引擎（UTF-8 BOM, 幂等去重, 周增量计算）
│   ├── config.py             # 配置加载（YAML + 环境变量）
│   └── keyword_expander.py  # LLM 关键词扩展
├── adapters/
│   ├── base.py               # 抽象基类
│   ├── bilibili.py           # B站（bilibili-api-python）
│   ├── youtube.py            # YouTube（yt-dlp + scrapetube + ycd）
│   ├── taptap.py             # TapTap（requests, webapiv2 接口）
│   └── media_crawler.py     # MediaCrawler 桥接（抖音/快手/小红书）
└── analysis/
    ├── sentiment.py          # 离线情感分析 + 竞品实体提取
    ├── weekly_report.py      # 周报生成
    └── profiler.py           # 用户画像推断
```

---

## 本地全流程验证结果

| 命令 | 状态 | 产出 |
|------|------|------|
| `crawl bilibili --mode actions` | ✅ | 336 条视频快照 |
| `crawl youtube --mode local` | ✅ | 160 条视频 + 446 条评论 |
| `crawl taptap --mode local` | ✅ | 3 款游戏快照 + 30 条评论 |
| `analyze --type weekly` | ✅ | Markdown 周报（三平台全覆盖） |
| `profile youtube {video_id}` | ✅ | 100 个用户画像 |

---

## 扩展新平台

1. 在 `src/adapters/` 新建适配器，继承 `BaseAdapter`
2. 在 `src/cli.py` 的 `cmd_crawl()` 中添加分支
3. 在 `pyproject.toml` 中添加可选依赖
4. 添加对应 GitHub Actions 工作流（时间错开 30 分钟，避免并发 git push 冲突）

详见 [Gemini.md](./Gemini.md) 中的完整开发者指南。

---

## 依赖说明

| 平台 | 核心库 | 安装命令 |
|------|--------|---------|
| B站 | `bilibili-api-python`, `httpx` | `pip install -e ".[bilibili]"` |
| YouTube | `yt-dlp`, `scrapetube`, `youtube-comment-downloader` | `pip install -e ".[youtube]"` |
| TapTap | `requests`, `beautifulsoup4` | `pip install -e ".[taptap]"` |
| 分析层 | `requests` (调用 LLM API) | `pip install -e ".[analysis]"` |
| 全部 | — | `pip install -e ".[all]"` |

---

## License

MIT © 2026 yqlizeao
