# SLG Sentinel – 面向 AI 编程助手的工程指南 (v3)

> **AI Assistant 请注意**：你在接手本项目之前，这是你**必须完整阅读**的第一份文件。我们已经完成了基础爬虫与企业级控制台搭建。如果你是新开的 session，请严格根据此文档迅速对齐项目上下文！

---

## 1. 当前项目形态与终极目标

**核心愿景**：我们正在研发一款 **三国题材、上线 Steam 平台、暂仅支持 Windows 的单机 SLG 游戏**。
在这个背景下，**SLG Sentinel** 是一套专为「我们自己的独立单机游戏研发」提供市场风向、玩家心智雷达、核心受众痛点发掘的多平台竞品舆情智能监控中台。它不是为了传统手游买量，而是为了**找到中国 PC 端 hardcore 战略玩家真正需要什么样的三国单机游戏**。

**三条架构铁律 (违反即视为失败)：**
1. **零侵入 (Zero-Intrusion)** 
   所有第三方采集库通过 `pip` 引入，绝对禁止修改任何第三方包的本地源码。对于防风控变态的平台（抖音/小红书），我们采用 Git Submodule 外挂的形式隔离引擎，利用 `subprocess` 沙盒调用。
2. **双模架构 (Dual-Mode Architecture)** 
   系统被严格切分为：
   - `--mode actions`：部署在 GitHub Actions 的免登云模式，定期高频捕获浅层大盘数据（防风控、无凭证）。
   - `--mode local`：部署在本地/原生服务器的全功能模式，具有深网探针（携带 Cookie）甚至唤起手机扫码的 GUI 环境。
3. **CSV 即数据库 (CSV as Database)** 
   系统严禁引入 MySQL/Postgres 等笨重 DBMS。全量业务数据采用 `UTF-8-SIG` 格式（带 BOM 头，完美适配 Excel），利用独立 `data/` 目录结构作为时序数据库。

---

## 2. 系统核心模块分布图

```text
slg-sentinel/
├── app.py                      # (🔥 GUI核心) Streamlit 线性美学企业级大中台
├── src/                        # 后端引擎层
│   ├── cli.py                  # 指令分发网关
│   ├── core/
│   │   ├── models.py           # 数据的元基石 (VideoSnapshot, Comment, TapTapReview, UserProfile)
│   │   ├── csv_store.py        # 去重、BOM 修复与周增量差值计算的持久化模块
│   │   ├── keyword_expander.py # (AI 模块) 调用 LLM 根据游戏简介自动逆向提纯搜索词
│   │   └── config.py           # 配置与靶点目标装载中心
│   ├── adapters/               # 各大平台采集桥接器
│   │   ├── bilibili.py         # 依赖 bilibili-api-python
│   └── analysis/               
│       ├── profiler.py         # (🚧 待攻坚核心) 跨越隐私墙的用户画像拼图合成器
│       ├── sentiment.py        # 本地离线自然语言情感分析 / 竞品 NER 实体识别
│       └── weekly_report.py    # 基于增量的 Markdown 周报生成器
├── data/                       # 核心时序数据库 (唯一落盘点，立体分类体系)
│   ├── summary/                # 【周期汇总层】
│   │   ├── daily/              # 顶层每日全网快照大盘，专供 `weekly_report.py` 利用减法进行“周真实热度增量”差值追踪。
│   │   ├── weekly/             # 预留周表结果
│   │   └── monthly/            
│   ├── video_platforms/        # 【流媒体/中短视频阵地】
│   │   ├── bilibili/               
│   │   │   ├── videos/         # 每日搜集/热门列表视频元数据
│   │   │   └── comments/       # 深网纯文字评论池 (含IP属性)
│   │   ├── youtube/                
│   │   │   ├── videos/         
│   │   │   └── comments/       # 管子原生态评论防封穿刺取回区
│   │   ├── douyin/             # (含有 kuaishou/, xiaohongshu/ 等，依靠沙盒爬去，但统一落库在此)
│   │   │   ├── videos/         
│   │   │   └── comments/       
│   └── community_platforms/    # 【硬核图文/游戏专属社区】
│       ├── taptap/                 
│       │   ├── videos/         # 实体化为对应 SLG 游戏本体 (Game)
│       │   └── comments/       # 为与主框架结构强制对齐，TapTap 极具价值的长测评 (Reviews) 全部落库在 comments/ 目录下。
├── cloudflare_pages/           # 云端流媒体反代静态入口 (index.html, 处理 CF iFrame 部署)
├── keywords.yaml               # 核心赛道黑话、同义词扩展池
├── targets.yaml                # 定向刺探的极高价值竞品 Up/频道
└── Gemini.md                   # 也就是本文件，所有 AI 接手之前的共识核心
```

---

## 3. 核心数据对象映射 (CSV as Database)

为了配合上述文件结构，系统中存在以下不可或缺的数据类模型设定（所有的 CSV Header 表头由以下对象直接生成）：
1. **`VideoSnapshot`**: 所有外层 `videos/` 列表获取的最重基石，包含了 播放、投币、弹幕等多维矩阵字段。
2. **`Comment`**: 用于 B站/油管/抖快，主打文本自然语言挖掘与点赞排位。
3. **`TapTapReview`**: `reviews/` 包含长测游玩时间与评级星级打分。
4. **`UserProfile`**: 最终的产物，具有年龄推断、消费类型（free/dolphin/whale 指代白嫖、微氪、神豪）等终极用户画像标签。

---

## 3. UI 界面哲学与公网部署 (Cloudflare)

### 界面设计 (app.py)
Streamlit 的默认外观非常丑陋。我们使用了超过 200 行注入的 CSS 强制将其转化为 **极其现代化、具备极客感与高管视角的控制台**。
- 采用 `Light Mode Only` 工业白板底色，配合无衬线字体（Inter）。
- 绝不使用自带的粗糙 UI 组件，利用内联 HTML 大量渲染圆角头像、视频封面与状态 Badge。
- **状态矩阵约束**：前台展示了不同平台因为风控级别而动态激活的抓取能力（例如免登状态下无法抓取投币与分享），这在 `app.py` 中被定义为严苛的 UI 开关互斥机制。

### 部署架构与网络穿透（极其重要）
经过惨痛教训，普通的 Worker 代理会因为 Streamlit 原生 React Router 检测 Host 不符而触发崩溃报错 404。
因此，**公网面板目前采用 Cloudflare Pages (iFrame 挂载) + CF VPN 访问模式。**
前端部署路径：
1. 本地生成包含 `<meta charset="utf-8">` 与 iframe 指向独立 Streamlit Cloud App URL 的 `cloudflare_pages/index.html`。
2. 拖拽至 Cloudflare Pages，通过该原生态沙盒越过路由封锁进行定制化域名呈现。

---

## 4. 下一步行动纲领：目前的 TODO 列表

如果你是新唤醒的 AI，请优先检查用户是不是要求解决以下核心遗留问题：

- [ ] **TODO 1: 大战 User Profiler（画像推测引擎）落地**
  此任务已被积压并进入攻坚期！系统现在的骨架已经完成，目前 `src/analysis/profiler.py` 虽然已有基础代码，但它目前输出的仅是模拟和占位逻辑。
  **目标**：结合目前 `data/` 里巨量的 TapTap 长评论库、B 站历史评论者 UID，开发逻辑让它自动提取核心评论区里的人群特征。识别出其中的“硬核肝帝”、“休闲风景党”、“退坑回流”以及他们在跨平台最喜欢对比什么竞品（例如“某群体在《世界启元》下面特别喜欢喷《三战》”），并且把这部分画像数据对接回 `app.py` 的面板上做极其赛博朋克风的图表展示。
  
- [ ] **TODO 2: Streamlit 面板的深度舆情报表可视化**
  目前 GUI 控制面板有「周报」这个模块，但我们需要将 `weekly_report.py` 落地的底层数据提取出来。不仅是让后端吐 Markdown，而是要在前端大展身手：将情感正负面转化率、竞品黑话声量占比直接映射成饼图或折线图。

- [ ] **TODO 3: MediaCrawler 子模块全域联调验证 (本地测试)**
  检查目前的 local 模式下，桥接外部隔离的 MediaCrawler（针对跨越抖音、小红书的风控体系）能否在实际环境里无缝唤起扫码沙盒，并将生成的 CSV 顺利倒灌回我们的 `data/` 仓内。

**提示结束**：阅读完毕上述内容后，你已具备本轮对话必须拥有的满级上下文。向用户致意并直接开始工作即可。
