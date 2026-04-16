# SLG Sentinel – 面向 AI 编程助手的工程指南 

> **AI Assistant 请注意**：在继续执行任何代码修改之前，请务必完整阅读本文件。本文件整合了本工程的核心架构哲学、依赖选型原因以及平台数据隔离边界。这是确保代码风格与项目基调一致的最高优先级指导原则。

---

## 1. 项目定义与三条铁律

**SLG Sentinel** 是一套面向 SLG（策略类）手游营销赛道的多平台竞品舆情监控系统。它不仅仅是一个爬虫工具，而是一个集成了数据抓取、历史增量快照对比、自然语言情感分析以及 Streamlit 现代化 GUI 的企业级监控系统。

我们在系统实现和架构设计中严格遵循以下 **三条铁律**。AI 生成的任何代码方案或设计均不可违背：

1. **铁律 ①：零侵入 (Zero-Intrusion)** 
   所有第三方采集仓库仅通过 `pip` 引入（或作为完全沙盒隔离的 submodule）。不修改任何第三方应用或库的源码。任何定制需求都必须通过子类化 (subclass) 或外挂注入执行。
2. **铁律 ②：双模架构 (Dual-Mode Architecture)** 
   同一套底层业务逻辑必须适应双模切换：
   - `--mode actions`：部署在 GitHub Actions 的免登录极简云模式，仅从不需要重度验证（脱网Cookie）的基础设施进行高频快照的持久捕获。
   - `--mode local`：本地/专属服务器全功能模式，支持强状态的 Cookie 深度抓取模型，并配合本地的 Streamlit 现代化企业级面板展现（`app.py`）。
3. **铁律 ③：CSV 即数据库 (CSV as Database)** 
   全量业务数据严禁使用传统或笨重的 DBMS（如 MySQL/Postgres 等）。统一遵循带 BOM 头支持 Excel 原生开启的 `UTF-8-SIG` 格式，利用 Git `data` 独立分支在 Actions 中解决版本数据推盘。

---

## 2. 工具链与其背后的选型决策

为保证免登录的稳定性和“零侵入”铁律，我们在各平台组件的设计中进行了深度验证（这曾是原先基于 Copilot 讨论后的最佳共识）：

### 2.1 Bilibili 平台 (`bilibili-api-python`)
- **抉择本质**：B 站对反爬有严防死守（如 Wbi）。我们依靠目前封装最牢固的 Python 开源 SDK 处理底层通信和自动 Wbi 签名更新。
- **免登范围**：不登录情况下依然可拿到高完整度视频快照、浅层瀑布流评论以及热门排行榜。

### 2.2 YouTube 平台（三工具混编）
不去用 YouTube 官方 Data API 是为了防止 `10,000` 日请求配额用尽（针对营销海量采集来说极其容易触顶）。因此采用了以下铁三角免配额组件组合：
- **`yt-dlp`**：负责发起类似 `ytsearch:竞品` 的引擎搜索调用。它提取完整的 JSON metadata，而不去下载真实视讯本体。
- **`scrapetube`**：专注“频道页全量检索”。因为 yt-dlp 在获取 Channel Timeline 瀑布流方面非常臃肿且效能不足。
- **`youtube-comment-downloader`**：因 yt-dlp 是一个下载器，批量处理数十万的文字弹幕评论会产生阻塞及溢出问题，于是改用这种独立的 json 请求伪装工具做评论的穿刺。

### 2.3 TapTap 平台 (自建 `requests` + 面向公开 API)
- 无需厚重封装。直接伪造手机游标或者访问 `v2 webapi` 端点能直接捞取用户的打分与设备特征等参数。TapTapAdapter 因此独立由自己开发和维护。

### 2.4 MediaCrawler（防风控黑盒突破系统）
- 对于小红书、快手、抖音，这些平台防风控机制非常变态，必须高度依赖本地 JS 逆向甚至强制扫码。
- **重构应对**：我们未将其源码暴力迁入以免遭到污染。而是使用 **Git Submodule** 挂载了原生的 `MediaCrawler`，在其内部构建独立沙盒。
- 只有在 `app.py` 中选择 `--mode local` 并点击按钮时，`src/cli.py` 才会通过 `subprocess` 底层调用其引擎。它可能会在你本地终端弹出手机扫码授权界面，之后我们将跨越沙盒壁垒收集它的 CSV 提取结果。
- **严重禁止**：在 GitHub Actions 等云端免登环境调用它会 100% 炸毁你的节点。

---

## 3. 面向平台隐私墙的「用户画像」

对于 SLG 而言，分析核心用户群体玩过什么，是重中之重。但请切记：
- ⛔ **绝对无法获取的死穴**：所有平台用户的“本人浏览记录”，这些在任何互联网世界都是不通过抓包和公开协议透出的黑核。不能提供相关不切实际的需求代码妄想爬取。
- 🟢 **我们用何种逆向工程来获取喜好推断：**
  在 `user_profiler.py` 内部基于多维度拼图：
  1. 获取竞品核心长测验下的活跃有效评论者 UID
  2. B 站探查：查其公开收藏夹和被公开访问的关注列表（这很大几率挂满原神的攻略，或三战的战报）
  3. TapTap 探查：TapTap 是少见的愿意大方展示“他玩过这些游戏总计多少小时”和他的“给分历史”的平台。提取其玩过的长列表。
  4. 使用在 `keywords.yaml` 已经配好的 SLG 字典扫描交集，最后输出此 ID 拥有高度特征的 SLG "三战&率土双游活跃" 等词法标签。

---

## 4. 全局项目版图 

```text
slg-sentinel/
├── app.py                      # (🔥重点) Streamlit 构建的轻量极简企业级中台控制端
├── src/                        # 后端心智代码
│   ├── cli.py                  # 各界面的 CLI 分发网关
│   ├── core/
│   │   ├── models.py           # 四大数据模型定义 (VideoSnapshot, Comment, TapTapReview, UserProfile)，只有变动这里，后续保存 CSV 才会变 Headers
│   │   ├── csv_store.py        # 去重、BOM修复与数据历史差值追踪模块
│   │   ├── keyword_expander.py # LLM 发散型语义扩充联想器
│   │   └── config.py           # YML 装配挂载
│   ├── adapters/               # 各平台封装桥接中心
│   │   ├── base.py             
│   │   ├── bilibili.py         
│   │   ├── youtube.py
│   │   ├── taptap.py
│   │   └── media_crawler.py    
│   └── analysis/               
│       ├── sentiment.py        
│       └── weekly_report.py    
├── .github/workflows/          # 所有定时流采集设定 (各个平台的 cron 从 16:00 UTC 开始错开以防并发 Git 锁冲突)
├── keywords.yaml               # (可通过前端修改) 保存大盘所需监测的核心赛道黑话、同义词扩展
└── targets.yaml                # (可通过前端修改) 各平台要定向刺探的头部竞品 Up/频道
```

### 存储模式
必须遵照：`data/{platform}/{videos | comments | reviews | user_games}/{YYYY-MM-DD}_xxx.csv` 这一结构。所有的时序增长对比（如分析上周到本周增加了多少点赞），强依赖这种日期分割文件策略计算差量。

---

## 5. UI 与配置层维系指引 (AI 修改警示)

现在本项目不再是一个冷冰冰挂在后台的单纯爬虫。我们在 `app.py` 内实现了一整套符合 Vercel / Linear “无边界黑白暗色调” 以及“工业白底” (Light Mode Only) 的仪表盘大中台。同时具有：
1. 内联组件级别的媒体视频与封面渲染
2. 依据各平台不同封控能力构建的**全动态属性探针约束矩阵**，AI 在自动化部署前可明眸所有的底层执行映射！
3. `pyproject.toml` 中的 `[project.optional-dependencies] gui` 作为启动屏障，彻底将传统核心依赖与 `streamlit`/`pandas` 割裂，保持框架纯净。

> **[注意]** 如果你需要扩充 `keywords.yaml` 及 `targets.yaml` 的实体属性：
> 请务必联动在 GUI 控制面板 （`app.py` 内的 `st.data_editor` DataFrame映射区域）加入对应的列。这套前端支持动态行列与行内自检保护，切勿因底层改动破坏前端用户输入的自洽性与一致性。
