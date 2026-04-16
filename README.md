# SLG Sentinel

> **SLG 游戏跨平台竞品舆情监控系统**
> 自动采集 B 站、YouTube、TapTap 数据，每周产出竞品动态 + 玩家情感周报。现已配备现代化企业级 GUI 控制台。

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-自动化-2088FF?logo=github-actions&logoColor=white)](https://github.com/yqlizeao/slg-sentinel/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-GUI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 核心哲学: 三条铁律

1. **零侵入**：所有第三方采集库通过 pip 包引入，绝不修改第三方源码，随时可跨平台升级。
2. **双模运行**：免登录平台（B站搜索/评论、YouTube、TapTap）可通过 `GitHub Actions` 云端定时执行；需登录/高级分析操作通过本地全功能模式执行。
3. **CSV 即数据库**：所有数据存储使用 `UTF-8 BOM` 的 CSV 文件，不引入任何重型数据库，方便直接以 Excel 开启并用 Git `data` 分支进行天然版本版本控制。

## 功能概览

| 模块 | 说明 |
|------|------|
| 🖥 **企业级大盘 (GUI)** | 极简 Linear/Vercel 风格的 Streamlit 控制台，一站式管理采集、查看热度增量矩阵、编辑关键词与目标，支持图文并茂的内嵌播放器 |
| 📱 **多平台数据采集** | 原生覆盖 B站 (视频/评论)、YouTube (视频/评论)、TapTap (长评)；可通过桥接支持 抖音/快手/小红书 |
| 🤖 **云端自动化化** | 云端 GitHub Actions 每日自动存快照，每周一自动生成舆情 markdown 周报 |
| 🧠 **AI 与情感分析** | 借助 DeepSeek/OpenAI 实现大语言模型自动扩写种子搜索词，并在离线端执行玩家情感极性判断 |
| 👤 **用户画像降维推断** | 突破平台隐私限制：通过交叉比对 TapTap 玩过的游戏、B站公开收藏夹及评论区提及提取，逆向合成竞品偏好画像 |

---

## 快速开始

### 1. 环境准备

推荐使用 Python 3.11 或 3.12 (macOS 用户推荐使用 `brew install python@3.12`)：

```bash
git clone https://github.com/yqlizeao/slg-sentinel.git
cd slg-sentinel

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装全量依赖 (含 GUI)
pip install -e ".[all]"
pip install streamlit pandas
```

### 2. 启动企业级控制台 (GUI)

在终端执行通过 Streamlit 启动系统：

```bash
streamlit run app.py
```

在系统设置页面（GUI 的“设置”导航栏），您可以直接以可视化表格的方式编辑 `targets.yaml` 和 `keywords.yaml`，完全摒弃易错的代码更改。

### 3. CLI 运行方式 (Actions / 服务器使用)

在没有界面的云端或服务器中，可通过强大的 CLI 进行全自动化采集与分析：

```bash
# 执行 B站 免登录快照采集
python -m src.cli crawl --platform bilibili --mode actions

# 执行 YouTube 采集
python -m src.cli crawl --platform youtube --mode local

# 生成舆情周报
python -m src.cli analyze --type weekly
```

---

## 项目架构与依赖

基于解耦与零侵入的设计原则：
- **依赖库组合**：
  - B站：`bilibili-api-python` (处理了复杂的 Wbi 签名)
  - YouTube：`yt-dlp` (元数据获取) + `scrapetube` (频道列表检索) + `youtube-comment-downloader` (无配额的高效评论扒取) 
  - TapTap：原生 `requests` 模拟，利用公开 WebAPI
- **数据结构层** (`src/core/models.py`)： 
  使用 `VideoSnapshot` / `Comment` / `TapTapReview` / `UserProfile` 抽象各平台数据统一落盘。

完整的 Agent 开发上下文，请参阅 [GEMINI.md](./GEMINI.md) 面向 AI 研发助手的工程规格架构指南。

---

## License

MIT © 2026 yqlizeao
