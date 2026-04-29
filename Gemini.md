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
   禁止引入 MySQL / PostgreSQL 等 DBMS。全量数据以 `UTF-8-SIG`（带 BOM）格式 CSV 存储在 `data/` 目录，Excel 可直接打开。递归采集任务的运行状态以 JSON 文件存储在 `data/recursive_runs/`。

---

## 3. 目录结构

```
slg-sentinel/
├── app.py                          # Streamlit GUI 入口（全局配置、CSS、侧边栏、页面分发）
├── ui/
│   ├── pages/
│   │   ├── overview.py             # 总览页（核心发现 + 趋势图 + 高赞评论）
│   │   ├── crawl.py                # 采集页（单次采集）
│   │   ├── recursive_crawl.py      # 话题探索页（递归多轮采集 + AI 话题发现）
│   │   ├── profile.py              # 用户画像页
│   │   ├── report.py               # 智能报表页
│   │   ├── competitor.py           # 竞品对比页（LLM 驱动的双竞品分析）
│   │   └── settings.py             # 设置页
│   ├── components/
│   │   ├── common.py               # 通用组件（页面标题、空状态、数据新鲜度指示器）
│   │   └── crawl.py                # 采集步骤条、关键词库、脑图、结果卡等组件
│   └── services/
│       ├── app_services.py         # GUI 服务层主入口（兼容性 re-export）
│       ├── stats_service.py        # 平台统计、系统健康、文件管理
│       ├── keyword_service.py      # 关键词库 CRUD
│       ├── search_metrics_service.py # 搜索指标读写与归一化
│       ├── mining_service.py       # 候选词挖掘算法（jieba + 热度加权）
│       ├── crawl_runner.py         # 采集执行、进度状态机、结果汇总
│       ├── crawl_history.py        # 采集任务历史 JSON 记录与查询
│       ├── overview_service.py     # 总览页数据服务（周报洞察、关键词趋势、高赞评论）
│       ├── recursive_runs.py       # 递归采集任务的 JSON 持久层
│       └── recursive_insights.py   # 话题分类与探索摘要
├── src/
│   ├── cli.py                      # CLI 指令分发网关（argparse，尽量不承载业务编排）
│   ├── core/
│   │   ├── models.py               # 数据模型（VideoSnapshot, Comment, TapTapReview, UserProfile）
│   │   ├── csv_store.py            # CSV 持久层（去重、BOM 修复、路径路由）
│   │   ├── config.py               # 配置中心（YAML 加载、环境变量、密钥管理）
│   │   ├── llm_client.py           # 通用 LLM 客户端（DeepSeek/OpenAI/Qwen 统一调用）
│   │   ├── exceptions.py           # 自定义异常体系（LLMError, NetworkError 等）
│   │   ├── keyword_expander.py     # LLM 驱动的搜索关键词自动扩展
│   │   └── retry.py                # 网络请求重试装饰器（指数退避）
│   ├── services/
│   │   ├── crawl_service.py        # 平台无关采集入口、各平台采集编排、搜索指标记录与迁移
│   │   ├── profile_service.py      # 用户画像生成与保存编排
│   │   ├── report_service.py       # 周报/情感分析入口编排
│   │   └── alert_service.py        # 告警推送（企业微信/飞书 Webhook）
│   ├── adapters/
│   │   ├── base.py                 # 适配器抽象基类
│   │   ├── bilibili.py             # B 站适配器（bilibili-api-python）
│   │   ├── youtube.py              # YouTube 适配器（yt-dlp + scrapetube + youtube-comment-downloader）
│   │   ├── taptap.py               # TapTap 适配器（逆向移动端 API）
│   │   └── media_crawler.py        # 抖音/快手/小红书桥接器（MediaCrawler 子进程）
│   └── analysis/
│       ├── sentiment.py            # 情感分析（词典匹配 + LLM 批量分析 + 自动降级）
│       ├── profiler.py             # 用户画像推断（年龄/付费/玩家标签）
│       └── weekly_report.py        # 周报生成器（Markdown + JSON + LLM 聚类摘要）
├── tests/
│   ├── test_core.py                # 基础测试套件（models/csv_store/sentiment/config）
│   ├── test_weekly_report.py       # 周报生成、TapTap review 转换、JSON 统计
│   ├── test_profiler.py            # 用户画像聚合、规则推断、保存路径
│   ├── test_recursive_runs.py      # 递归任务 CRUD、搜索指标封顶判定、header 迁移
│   └── test_recursive_insights.py  # 话题分组规则、泛化词检测、探索摘要聚合
├── data/                           # 时序数据目录（由 data 分支管理，main 分支 gitignore）
│   ├── summary/daily/              # 每日全网快照汇总
│   ├── video_platforms/             # B 站 / YouTube / 抖音 / 快手 / 小红书
│   │   └── {platform}/videos/      # 视频元数据
│   │   └── {platform}/comments/    # 评论文本
│   ├── community_platforms/         # TapTap
│   │   └── taptap/comments/        # TapTap 长评（统一存放在 comments/ 下）
│   ├── search_metrics/              # 各平台关键词搜索量记录（含封顶判定）
│   │   └── {platform}/             # 按平台分目录的搜索指标 CSV
│   ├── recursive_runs/             # 递归采集任务 JSON 持久化
│   ├── runtime/                    # 临时关键词文件等运行时产物
│   └── profiles/                   # 用户画像推断结果
├── reports/                        # 周报输出目录（Markdown + JSON）
├── .github/workflows/
│   ├── crawl-bilibili.yml          # 每日 UTC 16:00 自动采集
│   ├── crawl-youtube.yml           # 每日 UTC 16:30 自动采集
│   ├── crawl-taptap.yml            # 每日 UTC 17:00 自动采集
│   └── weekly-analysis.yml         # 每周一自动生成周报
├── cloudflare_pages/               # Cloudflare Pages iframe 入口
├── MediaCrawler/                   # Git Submodule（抖音/快手/小红书采集引擎）
├── keywords.yaml                   # 搜索关键词配置（统一扁平列表）
├── targets.yaml                    # 监控目标频道/游戏配置
├── pyproject.toml                  # 项目元信息与依赖声明
├── requirements.txt                # pip 快速安装依赖
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

### 递归采集任务模型

递归采集任务以 JSON 文件存储在 `data/recursive_runs/`，核心结构：

| 字段 | 用途 |
|------|------|
| `run_id` | 唯一标识（时间戳 + 平台 + UUID 短码） |
| `seed_keywords` | 起始话题列表 |
| `rounds[]` | 各轮次信息（关键词列表、状态、开始/结束时间） |
| `nodes[]` | 每个关键词的采集节点（搜索指标、采集指标、候选词指标） |
| `edges[]` | 父子关键词关系（from → to） |
| `events[]` | 事件流（启动/暂停/错误/用户操作） |
| `summary` | 汇总统计（节点数、视频数、评论数） |

### 搜索指标 CSV

`data/search_metrics/{platform}/` 目录下按日期存储搜索量记录，14 列表头：`snapshot_date, platform, keyword, order, limit, total_results, total_results_display, is_capped, num_pages, page_size, fetched_count, pages, error, created_at`。支持自动识别并迁移旧 10 列表头格式。

---

## 5. 配置文件

| 文件 | 作用 |
|------|------|
| `keywords.yaml` | 搜索关键词（统一扁平列表，`games` + 空 `categories`）+ LLM 扩词配置 |
| `targets.yaml` | 定向监控目标（B 站 UP 主 UID、YouTube 频道 ID、TapTap 游戏 ID） |
| `secrets.yaml` | 本地敏感凭证（已 gitignore），格式见 `config.py` |

环境变量优先级高于 `secrets.yaml`，支持：`DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `QWEN_API_KEY` / `BILI_SESSDATA`。

### keywords.yaml 当前格式

关键词已合并为统一列表，不再区分"游戏名称种子词"和"游戏品类种子词"：

```yaml
seed_keywords:
  games:
    - 三国志战略版
    - 率土之滨
    - 三国谋定天下
    # ...（当前 16 个种子词）
  categories: []
expansion:
  enabled: false
  llm_provider: deepseek
  max_expanded_keywords: 53
```

---

## 6. GUI 界面约束

GUI 是基于 Streamlit 构建的企业级控制台。`app.py` 只保留全局配置、CSS 注入、侧边栏导航和页面分发；页面、组件和服务逻辑分别放在 `ui/pages/`、`ui/components/`、`ui/services/`。

### 页面导航

当前 GUI 有 **7 个页面**：
1. **总览** — 本周核心发现（LLM 生成）、关键词趋势图、高赞评论精选、平台数据量、全网热帖排行
2. **采集** — 单次采集：选择平台 → 模式 → 深度 → 配额，一键启动
3. **递归采集（话题探索）** — 多轮递归采集 + AI 话题发现，自动从采集结果中提炼新关键词并扩展
4. **画像** — 玩家派系标签、消费类型分布、核心追踪名单
5. **智能报表** — 情感分布图表 + 竞品声量柱状图 + Markdown 周报 + LLM 评论聚类摘要
6. **竞品对比** — 选择两个 TapTap 竞品，LLM 自动生成优劣势对比与产品机会分析
7. **设置** — 在线编辑 targets / keywords / 密钥配置

### 递归采集（话题探索）功能

这是系统最复杂的页面（`recursive_crawl.py`，1000+ 行），核心能力：

- **探索策略预设**：标准探索 / 保守探索 / 深度探索，预配参数一键切换
- **候选词挖掘**：从已采集的视频标题/标签/高赞评论中用 jieba 分词提取关键词，按推荐指数排序
- **话题分类**：强推荐 / 待确认 / 长尾机会 / 不建议继续（`recursive_insights.py`）
- **递归执行**：自动多轮 采集→挖词→扩展→再采集，直到达到深度限制或无新话题
- **任务历史**：全量任务 JSON 可复盘，支持按平台/状态/关键词/日期过滤
- **暂停恢复**：B 站搜索量无法获取时自动暂停，用户可选择继续/跳过/终止
- **专家/营销双视角**：营销视角聚焦分类卡片，专家视角保留递归树 + JSON 诊断

### 分层边界

- `ui/pages/`：只负责页面布局和调用服务，不直接拼装磁盘路径，不直接实现 CSV 统计逻辑。
- `ui/components/`：只负责可复用渲染，公共组件必须通过显式参数接收数据，不依赖页面局部变量。
- `ui/services/app_services.py`：承接 GUI 侧非 UI 逻辑，例如平台统计、系统健康、热点内容读取、关键词读写、搜索指标读取、候选词挖掘算法、采集结果汇总、报告发现、文件扫描。
- `ui/services/recursive_runs.py`：递归采集任务的 JSON CRUD 和节点/轮次/事件管理。
- `ui/services/recursive_insights.py`：话题候选词分类规则（泛化词检测、封顶判定）、探索摘要聚合、业务进度事件格式化。
- `src/services/`：承接 CLI 侧采集、画像、报告编排；`src/cli.py` 只负责 parser、参数校验、调用 service 和输出 CLI 文案。

### 视觉约束

当前 GUI 注入了自定义 CSS，定义如下：

- **Light Mode Only**，白底工业风（Inter 字体），黑灰主色调。
- 禁止使用 Streamlit 自带的粗糙 UI 组件，大量使用内联 HTML 渲染数据表格、视频播放器、标签。
- 表单配置采用严格的 **Pipeline 流水线**（STEP 01 → STEP 05），禁止横向堆砌选项。
- 递归采集页有独立的 CSS 样式（Hero 区域、KPI 卡片、递归树可视化）。

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
- 递归采集任务通过 `recursive_runs.py` 的 `save_recursive_run()` 写入 JSON。
- 搜索指标通过 `crawl_service.py` 的 `save_search_metrics()` 写入 CSV，支持新旧表头自动迁移。

### 候选词挖掘算法

`app_services.py` 中的 `extract_keywords_from_crawl_data()` 实现了基于采集数据的关键词挖掘：

- 读取最近采集的视频和评论 CSV
- 用 `jieba` 分词（不可用时自动使用正则兜底）
- 计分规则：标题命中 `2.2 × 视频热度系数`，标签命中 `2.8 × 视频热度系数`，高赞评论命中 `1.25 × 评论点赞系数`
- 过滤已有关键词和停用词，按推荐指数排序输出

### 测试
- 测试位于 `tests/`，使用 pytest 执行。
- 当前自动测试覆盖 7 个测试文件，共 **64 条**：
  - `test_core.py`（14 条）：模型身份判等、CSV 幂等存储、情感分析、配置加载
  - `test_weekly_report.py`（4 条）：周报生成、TapTap review 转换、JSON 统计
  - `test_profiler.py`（3 条）：用户画像聚合、规则推断、保存路径
  - `test_recursive_runs.py`（9 条）：递归任务 CRUD、搜索指标封顶判定、header 迁移、历史过滤
  - `test_recursive_insights.py`（5 条）：话题分组规则、泛化词检测、探索摘要聚合、业务进度事件
  - `test_llm_client.py`（11 条）：LLM 客户端调用、JSON 解析、异常处理、Provider 切换
  - `test_adapters.py`（12 条）：B站搜索解析、LLM 情感分析降级、词典分析回归
  - 另有 `test_core.py` 中额外 6 条情感/配置相关测试
- 运行命令：`python -m pytest tests/ -v`

---

## 8. Git 提交与 PR 规范

每次对仓库产生任何内容修改后（包括但不限于代码文件、配置文件、文档、README、Markdown、YAML/JSON 配置等），必须自动执行以下流程：

### 8.1 自动提交（Commit）

- 完成仓库内容修改并确认无误后，立即使用 `git add` 暂存修改的文件，然后执行 `git commit`
- **commit message 必须使用中文**，详细描述本次修改内容
- 格式要求：

```
<类型>(<范围>): <简要说明>

<详细描述本次修改了什么、为什么修改、影响了哪些文件/功能>
```

- 类型包括：`feat`（新功能）、`fix`（修复）、`refactor`（重构）、`docs`（文档）、`style`（样式）、`test`（测试）、`chore`（杂项）
- 示例：

```
feat(采集): 新增抖音平台 B站 适配器的评论情感分析功能

- 在 src/adapters/bilibili.py 中新增 get_comment_sentiment 方法
- 调用 src/analysis/sentiment.py 实现评论文本的情感打分
- 新增对应单元测试 tests/test_bilibili_sentiment.py
- 修复了当评论为空时的 IndexError
```

### 8.2 自动推送到远程

- commit 完成后，立即执行 `git push` 推送到远程仓库
- 如果当前分支尚未跟踪远程分支，使用 `git push -u origin <branch>`
```

### 8.3 注意事项

- push 到远程的内容中不得包含敏感信息（密钥、Token 等）
- 每次修改只产生一个 commit，不要拆分成多个无意义的 commit
- commit message 和 PR body 必须准确反映实际修改的文件类型（代码、配置、文档等）

---

## 9. 待办事项

如果你是新唤醒的 AI，请优先检查用户是否要求解决以下核心遗留问题：

- [ ] **User Profiler 画像推测引擎升级**：当前 `profiler.py` 基于关键词启发式规则，已经有基础回归测试，但精度有限。后续可接入轻量级 LLM 提升画像质量，并将结果对接回画像页做更完整的图表展示。
- [ ] **周报 LLM 深度语义分析**：`weekly_report.py` 的第 4 节（深度语义洞察）目前为 TODO 占位。需接入 DeepSeek/GPT-4o 对本周高赞评论进行自动聚类摘要。
- [ ] **MediaCrawler 全域联调验证**：验证 local 模式下桥接 MediaCrawler 的扫码沙盒流程，确保 CSV 正确导入 `data/` 目录。
- [ ] **递归采集断点续跑**：当前暂停后只能记录操作日志，不能真正从暂停点恢复执行。需实现 `pending_queue` 消费机制。
- [ ] **候选词挖掘精度提升**：当前 `extract_keywords_from_crawl_data()` 基于词频 + 热度加权，可接入 LLM 对候选词做语义去重和质量打分。

---

*文档最后更新：2026-04-24*
