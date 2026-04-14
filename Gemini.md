# Gemini.md — SLG Sentinel AI 助手指南

本文件为 AI 编程助手（Gemini、Claude 等）提供上下文，帮助快速理解代码库结构、约定和关键设计决策，在继续开发前请先阅读本文件。

---

## 项目一句话概述

**SLG Sentinel** 是一套针对 SLG（策略类）手游营销赛道的多平台竞品舆情监控系统。通过定时采集 B 站、YouTube、TapTap 的视频/评论数据，进行情感分析和竞品提及提取，每周自动产出 Markdown 格式的舆情周报。

系统支持两种运行模式：
- **`--mode actions`**：GitHub Actions 云端免登录自动化（主力生产模式）
- **`--mode local`**：本地 CLI 全功能运行（含 Cookie 深度采集、MediaCrawler 桥接）

---

## 目录结构

```
slg-sentinel/
├── src/
│   ├── cli.py                    # 唯一入口，argparse 分发所有子命令
│   ├── core/
│   │   ├── models.py             # 全部数据模型 (dataclass)
│   │   ├── csv_store.py          # CSV 持久化引擎（唯一存储层）
│   │   ├── config.py             # YAML 配置加载 + 环境变量注入
│   │   └── keyword_expander.py  # DeepSeek/OpenAI API 关键词扩展
│   ├── adapters/
│   │   ├── base.py               # 抽象基类 BaseAdapter
│   │   ├── bilibili.py           # B站适配器 (bilibili-api-python)
│   │   ├── youtube.py            # YouTube适配器 (yt-dlp + scrapetube + ycd)
│   │   ├── taptap.py             # TapTap适配器 (requests + webapiv2)
│   │   └── media_crawler.py     # MediaCrawler 桥接 (抖音/快手/小红书)
│   └── analysis/
│       ├── sentiment.py          # 离线规则情感分析 + 竞品实体提取
│       ├── weekly_report.py      # 周报生成器，输出 Markdown
│       └── profiler.py           # 用户画像推断 (启发式规则)
├── .github/workflows/
│   ├── crawl-bilibili.yml        # 每日 UTC 16:00
│   ├── crawl-youtube.yml         # 每日 UTC 16:30
│   ├── crawl-taptap.yml          # 每日 UTC 17:00
│   └── weekly-analysis.yml       # 每周一 UTC 02:00
├── data/                         # 数据分支 (data branch)，不提交到 main
│   ├── bilibili/videos/          # {date}_videos.csv
│   ├── bilibili/comments/        # {date}_{video_id}_comments.csv
│   ├── youtube/videos/
│   ├── youtube/comments/
│   ├── taptap/videos/
│   ├── taptap/reviews/           # TapTapReview 格式，非 Comment
│   ├── snapshots/                # 跨平台合并快照（用于周增量计算）
│   └── profiles/                 # 用户画像输出
├── reports/                      # 周报 Markdown 输出（由 data 分支管理）
├── keywords.yaml                 # 种子关键词配置（可公开提交）
├── targets.yaml                  # 跟踪目标配置（含真实 app_id，可公开提交）
└── pyproject.toml                # 项目元信息和分平台可选依赖
```

---

## 核心数据模型（`src/core/models.py`）

| 模型 | 用途 | 主键字段 |
|------|------|---------|
| `VideoSnapshot` | 视频每日指标快照 | `video_id` |
| `Comment` | B站/YouTube 评论 | `comment_id` |
| `TapTapReview` | TapTap 游戏长评 | `review_id` |
| `UserProfile` | 推断式用户画像 | `user_id` |

> **⚠️ 注意**：TapTap 评论存储格式是 `TapTapReview`，**不是** `Comment`。在 `weekly_report.py` 中读取 TapTap reviews 时需先用 `TapTapReview` 加载再手动转换为 `Comment`。

---

## CSV 存储约定（`src/core/csv_store.py`）

- **编码**：UTF-8 with BOM（`utf-8-sig`），确保 Excel 可直接打开
- **路径规则**：
  - 视频: `data/{platform}/videos/{YYYY-MM-DD}_videos.csv`
  - 评论: `data/{platform}/comments/{YYYY-MM-DD}_{video_id}_comments.csv`
  - TapTap 评论: `data/taptap/reviews/{YYYY-MM-DD}_reviews.csv`（**无 video_id**）
  - 全局快照: `data/snapshots/{YYYY-MM-DD}_snapshots.csv`
- **幂等性**：同一天重复运行只追加新记录，按 `{data_type}` 对应的 ID 字段去重
- **周增量**：`get_weekly_delta(platform, video_id)` 比较今日与 7 天前 snapshots 目录里同 video_id 的数值差

---

## 配置系统（`keywords.yaml` + `targets.yaml`）

**`keywords.yaml`** — 种子关键词，`load_config()` 读取后作为搜索词传入各适配器：
```yaml
seed_keywords:
  games: [率土之滨, 三国志战略版, ...]
  categories: [SLG手游, ...]
expansion:
  enabled: true
  llm_provider: deepseek
```

**`targets.yaml`** — 指定跟踪目标，已填入真实 ID：
```yaml
targets:
  bilibili_channels:
    - name: "xxx"
      uid: "xxx"         # B站 UID，填真实值后自动采集该频道
  youtube_channels:
    - channel_id: "UCxxx"  # YouTube 频道 ID
  taptap_games:
    - name: "率土之滨"
      app_id: "4682"     # ✅ 已验证
    - name: "三国志战略版"
      app_id: "139546"   # ✅ 已验证
    - name: "万国觉醒"
      app_id: "82921"    # ✅ 已验证
```

**敏感配置**一律通过环境变量注入：

| 变量名 | 用途 |
|--------|------|
| `DEEPSEEK_API_KEY` | AI 关键词扩展、（未来）情感增强分析 |
| `BILI_SESSDATA` | B站深度采集（Cookie，可选） |
| `MEDIA_CRAWLER_DIR` | MediaCrawler 本地数据目录路径 |

---

## 各适配器关键细节

### B站 (`bilibili.py`)
- 使用 `bilibili-api-python`（自动处理 Wbi 签名，免登录）
- 关键导入：`from bilibili_api import search as bili_search, video as bili_video`
- `get_comments()` 需要 `oid`（视频的数值 ID），通过 `bili_video.Video(bvid).get_cid()` 获取

### YouTube (`youtube.py`)
- **三工具组合**：`yt-dlp`（搜索/元数据） + `scrapetube`（频道列表） + `youtube-comment-downloader`（评论）
- 评论点赞数格式为 `"1.9K"` 字符串，使用 `_parse_view_count()` 统一解析
- 每个关键词搜索耗时约 60-75 秒（yt-dlp 正常），8 个关键词约需 10 分钟

### TapTap (`taptap.py`)
- API 端点：`https://www.taptap.cn/webapiv2/`（2026-04 有效）
- `title` 字段为纯字符串（不是 dict），`developer` 可能为 `null`，代码已做 `isinstance` 防御
- 评论使用 cursor-based 分页（`next_cursor`），不是 offset
- 统计字段名：`hits_total`（播放量）、`fans_count`（关注）、`review_count`（评分数）、`wish_count`（心愿单）

### MediaCrawler 桥接 (`media_crawler.py`)
- **不自行爬取**，只读取 MediaCrawler 工具产出的 CSV
- 路径通过环境变量 `MEDIA_CRAWLER_DIR` 注入，默认 `MediaCrawler/data`
- 兼容抖音（`aweme_id`）和小红书（`note_id`）的不同字段命名

---

## 添加新功能的约定

### 添加新平台适配器
1. 继承 `src/adapters/base.py` 中的 `BaseAdapter`，实现 `search_videos()`、`get_video_info()`、`get_comments()`
2. 在 `src/cli.py` 的 `cmd_crawl()` 中添加 `elif args.platform == "xxx":` 分支，调用对应的 `_crawl_xxx()` 函数
3. 在 `pyproject.toml` 的 `[project.optional-dependencies]` 中添加该平台依赖
4. 在 `.github/workflows/` 中创建对应工作流，错开触发时间避免并发 git push 冲突

### 修改数据模型
- 所有模型在 `src/core/models.py`，字段即 CSV 列头，增减字段后**同时更新** `CSVStore._get_id_field()` 中的去重字段映射

### 部署到 GitHub Actions
- 数据写入 `data/` 分支，代码在 `main` 分支
- 工作流标准范式：先 checkout `data` 分支，再 `git checkout origin/main -- src/` 拉取代码，运行后 commit 回 `data` 分支

---

## 已知限制与 TODO

- **B站评论**：免登录时评论 API 对热门视频有风控限制，获取量可能为 0。配置 `BILI_SESSDATA` 后可解除
- **YouTube 采集速度慢**：yt-dlp 搜索本身较慢（~75s/关键词），这是 Actions 模式下可接受的延迟
- **TapTap 用户游戏列表**：`get_user_games()` 的旧版 API 端点已弃用，待找到新端点
- **抖音/快手/小红书**：需要先在本地运行 MediaCrawler 采集，再用桥接器导入数据
- **情感分析**：当前为离线规则版（成本趋零），可在配置 `DEEPSEEK_API_KEY` 后升级到 LLM 增强版
