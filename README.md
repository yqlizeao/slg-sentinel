# SLG Sentinel

> **研发驱动的 Steam 单机 SLG 多平台竞品舆情中台**
> 专为我们的**【三国题材 PC 单机 SLG 游戏】**研发铺路。自动采集 B 站、YouTube、TapTap 及其他泛量平台的硬核策略社群动态，利用大模型提纯 PC 战略玩家心智与竞品痛点，避免闭门造车。

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-自动化-2088FF?logo=github-actions&logoColor=white)](https://github.com/yqlizeao/slg-sentinel/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-GUI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🧭 系统哲学与顶层设计

在当今中国市场研发一款付费买断制的的三国 PC 原创 SLG 是极其凶险的，了解硬核策略玩家在长内容测验、竞品评论区（无论是端游老害还是手游回流玩家）的真实期望极其重要。本系统严格遵守 **三条不可动摇的工程铁律**：

1. **零侵入 (Zero-Intrusion)**：杜绝魔改第三方源码，保持生态纯洁与极简升级。高危风控平台使用 Git Submodule 隔离为独立沙盒进程。
2. **绝对的双模架构 (Dual-Mode)**：
   - **云端静默版 (Actions Mode)**：纯净的免登探测器，常驻云端，防溢出抓取宏观播放与点赞数据。
   - **中台全量版 (Local Mode)**：本地携带顶级 Cookie 深入社群评论区，无视深网限制，甚至能够唤醒真机接入分析。
3. **极简数据流 (CSV as Database)**：摒弃一切沉重的数据库（免配 MySQL/Postgres），将具有 BOM 头的 `UTF-8-SIG` CSV 作为极其透明的时序版本控制介质。

---

## 🛠️ 核心功能栈

| 模块 | 说明 |
|------|------|
| 🖥 **企业级大盘 (GUI)** | 被重构为极现代的 Vercel/Linear 高级白底工业风格的 Streamlit 控制台。一站式打通从采集参数定调到趋势周报图表的闭环。 |
| 🛡️ **动态封控探针矩阵** | 独创底层感知网关。可依照当前平台的【授权强度】与【爬取深度】自动降级和拦截不可达参数（例如强制避裁容易触发风控的“投币/转化”抓取列）。 |
| 📱 **全平台网罗** | B站、YouTube（三剑客无黑盒爬虫）、TapTap（原生 API 直连），更集成独立沙盒完成对抖音/小红书/快手的高度防风控强穿刺。 |
| 🧠 **AI 大脑深度切入** | （1）连接 DeepSeek/OpenAI，基于各大 SLG 官服介绍动态扩写延伸海量搜索长尾词、黑话。<br>（2）离线本地化执行极其高效海量的玩家情感（正/负面）以及竞品提及（NER）智能识别。 |
| 🕵️‍♂️ **核心玩家画像推测 (TODO)** | 冲破隐私限制，以受众为轴心拼图：寻找这帮在 B 站留下了对《三国志14》或《全战三国》乃至跨平台手游《三战》重度吐槽的用户，反向提纯他们真正想要的 PC 单机体验！ |

---

## 🚀 极速部署指南

### 1. 环境准备 (推荐 Python 3.11/3.12)

```bash
# 包含 MediaCrawler 防风控抓取引擎，必须使用递归克隆拉取 Submodule 子模块！
git clone --recursive https://github.com/yqlizeao/slg-sentinel.git
cd slg-sentinel

# 创建虚拟环境并彻底隔离污染
python3 -m venv .venv
source .venv/bin/activate

# 安装全平台核心抓取器与 GUI 界面框架 (Mac zsh 终端提示报错请用单引号包围包名)
pip install -e ".[all,gui]"
```

### 2. 登舰！启动企业级控制台 

```bash
streamlit run app.py
```
控制台启动后，你可以在自带界面的**设置页面**直通所有的行为参数，并动态可视化配置 `targets.yaml` 和 `keywords.yaml` 监控词云，完全摒弃了易错的手搓代码。

### 3. 高端玩家：纯命令行的云端狂奔 (CLI)

用于放置服务器后台或 GitHub Actions 自动 CRON 节点，每日静如处子，动如脱兔：

```bash
# 执行 B 站免登级云端批量快照 (指定单次采集深网限额 100 条)
python -m src.cli crawl --platform bilibili --mode actions --limit 100

# 执行 YouTube 本地域深网评论挖掘
python -m src.cli crawl --platform youtube --mode local

# 启动 LLM 引擎对语料发起扫描并生成上周周报
python -m src.cli analyze --type weekly
```

### 4. 关于公网与 Cloudflare 部署架构
本工程已配置极其精简的 Cloudflare Pages `iframe` 容器逃逸沙盒。若由于 GFW 拦截或 Streamlit Community Cloud 原生安全墙（React Remix Host 一一对应防护拦截）导致你之前的 Worker 反向代理抛出 `404 Unexpected Error`，你只需将内置的 `cloudflare_pages/` 目录拖拽上传至你的 CF Pages 项目中进行挂载，并在本地保持 VPN 开启，即可直接完美化解官方的域名锁定，还原极度震撼的原生全屏沉浸体验。

---

## 🤝 开发者共识 / AI Agent 上下文入口

项目附带针对 AI 编程助手的硬核心智说明书：**[Gemini.md](./Gemini.md)**。
无论您想使用光线追踪的硅基大脑续写、拓展、或者基于此库解决某个 Bug 甚至创建一个新赛道的子探测器，请**务必在新的会话最开始，命令您的 AI 优先读取**该文件以建立对等的世界观与架构红线认同。

---
*Powered by Data ＆ Code ｜ License: MIT © 2026 yqlizeao*
