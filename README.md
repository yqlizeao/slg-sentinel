# SLG Sentinel

SLG Sentinel 是一款专为 SLG (策略类) 游戏定制的自动化跨平台舆情监控系统。
它通过爬取目标游戏与竞品的社交媒体动态、视频热度、用户评论等数据，提炼市场趋势、挖掘长尾话题并产出负面舆情预警周报。支持**本地 CLI（全功能）**与 **GitHub Actions（免登录云端每日自动化）**双系统运行。

---

## 📅 各阶段(Phase)已全部完成

- ✅ **Phase 0：基础骨架**
  - CLI(`cmd_crawl`, `cmd_profile`, `cmd_analyze`) 分发。
  - 标准化 `dataclass` 数据模型(`VideoSnapshot`, `Comment`, `UserProfile`)。
  - CSV 持久化存储与日期化隔离方案（零数据库，完全 Git 化存储）。
  - 支持 `keywords.yaml` 与 `targets.yaml` 全局参数注入。
- ✅ **Phase 1：Bilibili 适配器**
  - 集成 `bilibili-api-python`。
  - 自动规避风控，提供搜索、评论翻页、热门模块。
  - 本地化 Cookie 支持 + GitHub Action 自动化抓取流。
- ✅ **Phase 2：YouTube 适配器**
  - 集成 `yt-dlp` + `scrapetube` + `youtube-comment-downloader` 三合一免登录链条。
  - 支持海外 SLG 竞品查询、海外华语频道评论获取。
- ✅ **Phase 3：TapTap 适配器**
  - 自建 `requests` + 接管移动端 WebAPIV2 接口 (`ww.taptap.cn/webapiv2`)。
  - 直接抓取真实用户游戏长评、情感倾诉、打分机制。
- ✅ **Phase 4：舆情分析层**
  - `KeywordExpander`: AI 驱动竞品搜索词与垂直话术联想。
  - `SentimentAnalyzer`: 轻量高效的情感判断+实体竞品交叉提及过滤。
  - `WeeklyReportGenerator`: 算出播放增量，提取核心负面，导出 Markdown 业务周报。
- ✅ **Phase 5：进阶与扩容平台 (MediaCrawler 桥接与画像推演)**
  - `UserProfiler`: 根据社群黑话集推断玩家年龄、用户分类（微氪/重度）以及行为标签。
  - `MediaCrawlerBridge`: 一键吸收抖音、快手、小红书本地抓取结果融入分析大盘。

---

## 🛠 快速上手

### 1. 环境准备
项目采用 Python 3.9+，通过可选依赖组适配部署需求：
```bash
# 全量安装（适用于本地环境）
pip install -e ".[all]"

# 或者按需安装特定平台依赖：
pip install -e ".[bilibili]"
pip install -e ".[youtube]"
pip install -e ".[taptap]"
pip install -e ".[analysis]"  # 分析/周报/画像功能需要
```

### 2. 本地 CLI 命令演示

数据采集（以 B站、YouTube、TapTap 为例）：
```bash
python -m src.cli crawl --platform bilibili --mode actions
python -m src.cli crawl --platform youtube --mode local
python -m src.cli crawl --platform taptap --mode actions
```

舆情分析与报告生成：
```bash
# 生成包含本周各大平台竞品视频播放增量、负面提取的 Markdown 周报
python -m src.cli analyze --type weekly

# 利用 DeepSeek 扩展 SLG 关键词
python -m src.cli expand-keywords --provider deepseek
```

生成高维用户画像：
```bash
python -m src.cli profile --platform youtube --video-id {YourVideoID}
```

### 3. GitHub Actions 自动化体系

系统已为你内嵌四套 GitHub Actions 剧本 (`.github/workflows`)，触发后自动提交数据和分析报告到孤立的 `data` 分支。
- `crawl-bilibili.yml`
- `crawl-youtube.yml`
- `crawl-taptap.yml`
- `weekly-analysis.yml`

*附注：配置密钥时，请确保存放到 `Settings -> Secrets and variables -> Actions` 中（如：`DEEPSEEK_API_KEY`、`BILI_SESSDATA`）。*
