# SLG Sentinel — AI 编程助手工程指南

> **AI 助手注意**：这是你接手本项目之前必须完整阅读的第一份文件。请严格根据此文档对齐项目上下文，再开始任何代码操作。

---

## 1. 项目定位

**SLG Sentinel** 是一套多平台竞品舆情监控系统，服务于一款**三国题材、面向 Steam 平台、仅支持 Windows 的付费买断制 PC 单机 SLG 游戏**的研发决策。

系统的核心价值：从 B 站、YouTube、TapTap、抖音、快手、小红书等平台持续采集 SLG 品类的玩家评论与视频数据，通过情感分析和用户画像推断，帮助研发团队找到**中国 PC 端硬核策略玩家真正需要什么样的三国单机游戏**。

---

## 2. 三条架构铁律

违反以下任何一条即视为架构失败：

1. **零侵入 (Zero-Intrusion)**  
   所有第三方采集库通过 `pip` 引入，禁止修改任何第三方包的本地源码。高风控平台（抖音/小红书/快手）采用 Git Submodule 隔离，通过 `subprocess` 沙盒调用。

2. **双模架构 (Dual-Mode)**  
   - `--mode actions`：部署在 GitHub Actions，免登录，定期采集浅层大盘数据。
   - `--mode local`：部署在本地，携带 Cookie 执行深度采集（评论、画像等）。

3. **CSV 即数据库 (CSV as Database)**  
   禁止引入 MySQL / PostgreSQL 等 DBMS。全量数据以 `UTF-8-SIG`（带 BOM）格式 CSV 存储在 `data/` 目录，Excel 可直接打开。

---

## 3. 目录结构

```
slg-sentinel/
├── app.py                          # Streamlit 企业级控制台（GUI 入口）
├── src/
│   ├── cli.py                      # CLI 指令分发网关（argparse）
│   ├── core/
│   │   ├── models.py               # 数据模型（VideoSnapshot, Comment, TapTapReview, UserProfile）
│   │   ├── csv_store.py            # CSV 持久层（去重、BOM 修复、路径路由）
│   │   ├── config.py               # 配置中心（YAML 加载、环境变量、密钥管理）
│   │   ├── keyword_expander.py     # LLM 驱动的搜索关键词自动扩展
│   │   └── retry.py                # 网络请求重试装饰器（指数退避）
│   ├── adapters/
│   │   ├── base.py                 # 适配器抽象基类
│   │   ├── bilibili.py             # B 站适配器（bilibili-api-python）
│   │   ├── youtube.py              # YouTube 适配器（yt-dlp + scrapetube + youtube-comment-downloader）
│   │   ├── taptap.py               # TapTap 适配器（逆向移动端 API）
│   │   └── media_crawler.py        # 抖音/快手/小红书桥接器（MediaCrawler 子进程）
│   └── analysis/
│       ├── sentiment.py            # 离线情感分析（词典 + 否定词反转）与竞品实体识别
│       ├── profiler.py             # 用户画像推断（年龄/付费/玩家标签）
│       └── weekly_report.py        # 周报生成器（Markdown + JSON 统计）
├── tests/
│   └── test_core.py                # 基础测试套件（20 条，覆盖 models/csv_store/sentiment/config）
├── data/                           # 时序数据目录（由 data 分支管理，main 分支 gitignore）
│   ├── summary/daily/              # 每日全网快照汇总
│   ├── video_platforms/             # B 站 / YouTube / 抖音 / 快手 / 小红书
│   │   └── {platform}/videos/      # 视频元数据
│   │   └── {platform}/comments/    # 评论文本
│   └── community_platforms/         # TapTap
│       └── taptap/comments/        # TapTap 长评（统一存放在 comments/ 下）
├── .github/workflows/
│   ├── crawl-bilibili.yml          # 每日 UTC 16:00 自动采集
│   ├── crawl-youtube.yml           # 每日 UTC 16:30 自动采集
│   ├── crawl-taptap.yml            # 每日 UTC 17:00 自动采集
│   └── weekly-analysis.yml         # 每周一自动生成周报
├── cloudflare_pages/               # Cloudflare Pages iframe 入口
├── MediaCrawler/                   # Git Submodule（抖音/快手/小红书采集引擎）
├── keywords.yaml                   # 搜索关键词配置
├── targets.yaml                    # 监控目标频道/游戏配置
├── pyproject.toml                  # 项目元信息与依赖声明
└── Gemini.md                       # 本文件
```

---

## 4. 核心数据模型

CSV 的 Header 表头由以下 dataclass 直接生成：

| 模型 | 存储位置 | 用途 |
|------|---------|------|
| `VideoSnapshot` | `videos/*.csv` | 视频/游戏的多维指标快照（播放、点赞、弹幕等） |
| `Comment` | `comments/*.csv` | 评论文本、点赞数、IP 属地，用于情感分析 |
| `TapTapReview` | `comments/*.csv` | TapTap 长评（含星级评分、游玩时长），统一存放在 comments 目录 |
| `UserProfile` | `profiles/*.csv` | 用户画像推断结果（年龄段、付费类型、玩家标签） |

所有模型均实现了 `__eq__` 和 `__hash__`，基于各自的 ID 字段去重。

---

## 5. 配置文件

| 文件 | 作用 |
|------|------|
| `keywords.yaml` | 种子关键词（游戏名 + 品类词）+ LLM 扩词配置 |
| `targets.yaml` | 定向监控目标（B 站 UP 主 UID、YouTube 频道 ID、TapTap 游戏 ID） |
| `secrets.yaml` | 本地敏感凭证（已 gitignore），格式见 `config.py` |

环境变量优先级高于 `secrets.yaml`，支持：`DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `QWEN_API_KEY` / `BILI_SESSDATA`。

---

## 6. GUI 界面约束

`app.py` 是基于 Streamlit 构建的企业级控制台，注入了 200+ 行自定义 CSS，定义如下：

- **Light Mode Only**，白底工业风（Inter 字体），黑灰主色调。
- 禁止使用 Streamlit 自带的粗糙 UI 组件，大量使用内联 HTML 渲染数据表格、视频播放器、标签。
- 表单配置采用严格的 **Pipeline 流水线**（STEP 01 → STEP 05），禁止横向堆砌选项。

### UX 文案规范

禁止在界面中使用过度中二、科幻感的词汇。以下词汇**禁止出现**：
> 探针、神经干线、潮汐、底座、阵列、汪洋、大盘、穿刺、渗透

使用标准的 B2B 商业数据产品术语：
> 监控目标、采集时间、系统节点、图表、分析组件、数据源

### 公网部署

采用 **Cloudflare Pages (iframe) + VPN** 模式。`cloudflare_pages/index.html` 包含指向 Streamlit Cloud 实例的 iframe，绕过 Streamlit 原生路由检测的域名锁定。

---

## 7. 开发规范

### 网络请求
- 所有适配器强制执行 `time.sleep(1.0+)` 礼貌间隔。
- 使用 `src/core/retry.py` 提供的 `@retry_on_failure` 装饰器处理网络波动。

### 数据持久化
- 通过 `CSVStore.save()` 写入，自动处理去重（基于 ID 字段）和 BOM 头。
- 新建文件写入 UTF-8 BOM，追加模式不重复写入 BOM。

### 测试
- 测试位于 `tests/test_core.py`，使用 pytest 执行。
- 运行命令：`python -m pytest tests/ -v`

---

## 8. 待办事项

如果你是新唤醒的 AI，请优先检查用户是否要求解决以下核心遗留问题：

- [ ] **User Profiler 画像推测引擎落地**：当前 `profiler.py` 基于关键词启发式规则，精度有限。计划接入轻量级 LLM 提升画像质量，并将结果对接回 `app.py` 面板做图表展示。
- [ ] **周报 LLM 深度语义分析**：`weekly_report.py` 的第 4 节（深度语义洞察）目前为 TODO 占位。需接入 DeepSeek/GPT-4o 对本周高赞评论进行自动聚类摘要。
- [ ] **MediaCrawler 全域联调验证**：验证 local 模式下桥接 MediaCrawler 的扫码沙盒流程，确保 CSV 正确导入 `data/` 目录。

---

*文档最后更新：2026-04-18*
