# Recursive 模块中心可视化设计

**日期**：2026-04-27
**作者**：与用户共同 brainstorm
**适用范围**：`ui/pages/recursive_crawl.py` 的中心 atlas-shell-scene、右侧 atlas-shell-drawers、左下角 atlas-shell-panels 三块的重构

## 背景

`recursive_crawl.py` 已具备完整的递归采集执行链：起始话题 → 多轮关键词扩展 → 每轮按 keyword 调用平台适配器 → 把结果写入 `data/recursive_runs/<run_id>.json`。但页面中心目前是一段静态装饰性 SVG（`scene_html` 中的 grid + 4 个文本标签），没有承载任何 run 数据；右侧 4 个 drawer 复用通用 list 组件，缺乏对单节点的聚焦视图；左下角 3 张报表卡永远展开，挤占垂直空间。

## 目标

把中心区改造为递归搜索图，横向每一轮一列、节点显示 `keyword + 视频数`、父子节点连线；点击节点后右侧专属面板展示该节点的视频列表与下一轮候选词；左下角三张报表卡支持整体折叠收起。

## 非目标（YAGNI）

- 节点拖拽布局
- 多 run 切换器
- 任务运行中实时 polling 刷新
- 节点合并 / 子树折叠
- 图片导出
- 节点间任意跳转动画

---

## 一、数据流与文件改动边界

### 数据来源

- 沿用 `ui/services/recursive_runs.py::list_recursive_runs()` 拉取最近一次 run（按 `created_at desc` 取首条），与"历史探索库 popover"读的是同一份 JSON。
- 候选词列表：直接读 `node.candidate_metrics.candidates`（已在 JSON 中）。
- 视频列表：`VideoSnapshot` CSV 没有 keyword 列，无法直接反查。采用以下两层策略，新增 `ui/services/app_services.py::load_videos_for_node(run, node, limit=20) -> list[dict]`：
  1. **新 run（首选）**：在 `_run_recursive_crawl` 执行每个节点前后读取目标 CSV 的 `video_id` 集合差集，把本次新增的 `video_id` 列表写入 `node.crawl_metrics.video_ids`。展示时直接按这些 ID 查 CSV。
  2. **旧 run（兼容回退）**：节点缺 `video_ids` 字段时，按 `node.crawl_metrics.touched_files` 找到 videos CSV，过滤 `snapshot_date == node.started_at[:10]`，按 CSV 行尾序取最近 `crawl.videos` 条。结果可能与实际有偏差，UI 上加一个 dim 灰色 hint `数据为旧版 run 估算结果`。

数据契约变更（前向兼容）：
- 新增字段 `node.crawl_metrics.video_ids: list[str]`（新 run 写入，旧 run 缺省）
- `recursive_runs.py` 不动；写入逻辑在 `recursive_crawl.py::_run_recursive_crawl` 加 4~6 行

### 选中节点状态

- 唯一来源：`st.query_params.get("recursive_node")`。
- 缺省默认 = run 的最后一个节点（`nodes[-1].node_id`）。
- 不写入 `st.session_state`，避免与 popover 控件互踩。

### 文件改动清单（增量、零侵入第三方）

| 文件 | 改动 |
|---|---|
| `ui/pages/recursive_crawl.py` | 重写 `render_recursive_crawl_page()` 中 `scene_html` / `panels` / `drawers` 三段；新增 `_render_graph_scene(run, selected_node_id)`、`_render_node_detail_panel(run, node)`、`_url_with(**overrides)` 私有函数；在 `_run_recursive_crawl` 节点执行前后捕获 `video_id` 集合差集，写入 `node.crawl_metrics.video_ids` |
| `ui/services/app_services.py` | 新增 `load_videos_for_node(run, node, limit=20)`，复用现有 CSV 扫描逻辑；按 `run.platform` 内部分发 |
| `app.py`（CSS 段） | 新增 `.recursive-graph` / `.recursive-graph-cols` / `.recursive-graph-col` / `.recursive-graph-node` / `.recursive-graph-edges` / `.recursive-node-detail` / `.atlas-shell-panels-wrap` / `.atlas-shell-panels-summary`；删除旧装饰用 `.atlas-stage-map` 仅在 recursive 页面生效的部分 |
| `ui/services/recursive_runs.py` | 不动 |
| `src/services/`、`src/adapters/` | 不动 |

---

## 二、中心图组件结构

### 整体布局

中心区替换原 `scene_html`，渲染如下结构：

```
┌─R1───────┐  ┌─R2───────┐  ┌─R3───────┐
│ ROUND 01 │  │ ROUND 02 │  │ ROUND 03 │
│ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │
│ │三国杀│─┼──┼→│SLG荣耀│─┼──┼→│蜀汉将领│ │
│ │32 视频│ │  │ │28 视频│ │  │ │14 视频│ │
│ └──────┘ │  │ └──────┘ │  │ └──────┘ │
└──────────┘  └──────────┘  └──────────┘
```

### DOM 结构（一次性服务端渲染）

```html
<div class="recursive-graph">
  <svg class="recursive-graph-edges">       <!-- 连线层，z-index:1 -->
    <path d="M..." />
  </svg>
  <div class="recursive-graph-cols">         <!-- 节点层，z-index:2 -->
    <div class="recursive-graph-col">
      <div class="recursive-graph-col-head">ROUND 01</div>
      <a class="recursive-graph-node is-success is-selected"
         href="?recursive_node=NODE_ID&...">
        <div class="node-status-dot"></div>
        <div class="node-keyword">三国杀</div>
        <div class="node-metric">32 视频</div>
        <div class="node-extras">下一轮 5 词</div>  <!-- 仅候选词数>0 时渲染 -->
      </a>
      ...
    </div>
    ...
  </div>
</div>
```

### 节点尺寸（有限自适应）

服务端按 keyword 长度估算行数（用 `wcwidth` 计算可视宽度）：

- keyword 单行（≤ 节点宽度 / 12px 字符）→ `node_height = 72px`
- keyword 双行（> 容量但 ≤ 2 行）→ `node_height = 96px`
- 超长（> 2 行）→ 第二行 ellipsis、tooltip 全文，仍按 96px

候选词数 = 0 时不渲染 `node-extras` 行，节点矮 16px（即 56 / 80）。

### 坐标算法

```python
COL_W = 220
COL_GAP = 80
COL_HEAD_H = 32
NODE_GAP = 14

# X
node.x = round_index * (COL_W + COL_GAP)

# Y（每列从列头下方累加）
y_cursor = COL_HEAD_H
for node in nodes_sorted_in_col:
    node.y = y_cursor
    y_cursor += node.height + NODE_GAP
```

`<svg>` 总高度 = `max(每列 y_cursor)`，总宽度 = `(round_count) * (COL_W + COL_GAP)`。

### 同列内节点排序

- 第 1 轮（种子轮）：按 `node_id` 字典序，稳定。
- 第 N≥2 轮：先按父节点 Y 升序（减少交叉），同父下按 `score desc`。

### 父子连线

```python
y_mid_parent = parent.y + parent.height / 2
y_mid_child  = child.y  + child.height  / 2
path = f"M{parent.x + COL_W} {y_mid_parent} " \
       f"C{parent.x + COL_W + 40} {y_mid_parent}, " \
       f"{child.x - 40} {y_mid_child}, " \
       f"{child.x} {y_mid_child}"
```

三阶贝塞尔，控制点水平偏移 40px。stroke 颜色按子节点状态色，opacity 0.4。

### 选中状态

- `is-selected` class → 4px 金色 `outline` + 8px `box-shadow` 金色低饱和外发光
- 其它节点 `opacity: .85`，hover 时 `opacity: 1`

### 状态色（边框 4px 左 + 1px 其他三边）

| status | color |
|---|---|
| success | `#5B9A6E` |
| running | `#6B8BDB` |
| paused | `#D4956B` |
| error | `#E85D4A` |

### 滚动

- `recursive-graph` 设 `overflow: auto`
- 节点过多时横/纵向滚都允许
- 不自动滚动到选中节点（下一迭代再加）

---

## 三、右侧节点详情面板

### 位置

复用 `atlas-shell-drawers` 的定位（`top:150px; right:22px; width:360px`），但删除原 4 个 `<details>` 抽屉，替换为单块固定面板 `.recursive-node-detail`，不可折叠。

### DOM 结构

```html
<aside class="recursive-node-detail" data-status="success">
  <header>
    <div class="kicker">第 2 轮 · success · 32 视频</div>
    <h3>三国群英战棋无双</h3>
  </header>
  <section class="videos">
    <div class="section-title">视频列表 (32)</div>
    <ul>
      <li>
        <div class="title">三国战棋无双 测评首发</div>
        <div class="meta">UP主 · 12.4w播放 · 03-12</div>
      </li>
      ...
    </ul>
  </section>
  <section class="candidates">
    <div class="section-title">下一轮候选词 (5)</div>
    <ul>
      <li><span>战棋玩法</span><b>★ 6.2</b></li>
      ...
    </ul>
  </section>
</aside>
```

### 内容

- 头部：mono 字体 `第 N 轮 · 状态 · {videos} 视频`；display 字体 `{keyword}`；`border-left: 4px` 状态色。
- 上半区视频：每行 60px 卡片，title 加粗，副行灰字 `author · view播放 · pubdate`；前 20 条；超出显示 `...还有 X 条`；不显示缩略图。
- 下半区候选词：单行 `keyword + ★ score`（用 `format_score`）。
- 空状态：视频区 → "该节点未采集到视频"；候选词区 → "未挖掘出新候选词"。

### 高度与滚动

- 整体 `height: calc(100% - 200px)`，与 stage 共享垂直预算
- 上下两区 `flex: 1 1 50%`，一区为空时另一区吃满
- 各自 `overflow-y: auto`

### 跨平台差异

- TapTap：节点 metric 改显示评论数（`crawl.comments`）；上半区改"评论列表"（用户名 + 评分 + 游玩时长 + 部分正文）。
- B 站 / YouTube：默认视频路径。
- 抖音 / 快手 / 小红书：best-effort 复用 B 站字段渲染，待跑通后单独优化。
- 由 `load_videos_for_node` 内部按 `run.platform` 分发；UI 层无感。

---

## 四、左下角三张卡折叠交互

### DOM 改造

把 `atlas-shell-panels` 包一层 `<details>`：

```html
<details class="atlas-shell-panels-wrap" {open if not collapsed}>
  <summary class="atlas-shell-panels-summary">
    <span>状态报告 · 3</span>
    <a class="collapse-toggle" href="?...&recursive_panels=closed">▾</a>
  </summary>
  <div class="atlas-shell-panels">
    <article ...>STATE</article>
    <article ...>SEEDS</article>
    <article ...>TREE</article>
  </div>
</details>
```

### 持久化

折叠状态由 `st.query_params.get("recursive_panels", "open")` 驱动：
- `open`（缺省）→ `<details open>`
- `closed` → `<details>` 不带 `open` 属性

`<summary>` 原生 toggle 仅在当前会话有效（用户折叠完不刷新就保留），刷新走 query_params。`collapse-toggle` 的 `<a>` 链接显式触发 rerun，确保跨刷新的持久化。

### 视觉

- 展开：summary 32px 高条 + 三张原卡片
- 折叠：仅剩 summary 32px 高条，中心 graph 多出约 150px 垂直空间
- summary：米色 mono 字体，金色 ▾/▴ 图标

### Query 参数总表

页面共两个：

- `recursive_node` — 选中节点 ID
- `recursive_panels` — `closed` / 缺省=`open`

切换其一时另一保留——`href` 用 `_url_with(**overrides)` 工具拼接。

---

## 五、状态/边界场景

### A. 无 run

- 中心：`atlas_empty` 风格空态卡片"暂无递归任务，左上角『候选话题』启动一次 AI 探索"
- 右侧节点详情面板整体不渲染
- 左下角三张卡保留，TREE 卡显示"暂无节点"

### B. run 仅有种子轮

- 单列正常渲染
- `<svg>` 高度按列高，path 列表为空
- 右侧详情面板正常工作

### C. run 正在执行（status=running）

- 节点按当时快照渲染；正在执行节点蓝色边框
- 不做 polling；用户刷新页面看进度

### D. URL 中 `recursive_node` 不存在于当前 run

- 静默回退到默认节点（最后一个节点）
- 不清理 URL 参数（避免重定向循环）；下次点击其他节点自然覆盖

### E. 节点过多

- 中心区横/纵向滚动
- 选中节点不自动滚动到可视区

### F. keyword 过长

- > 2 行的部分 ellipsis + tooltip 全文

### G. 跨平台

详见第三节「跨平台差异」。

---

## 验证清单（实现完后人工过）

- [ ] 没有 run 时进入页面，空态卡片正确渲染，无 JS 报错
- [ ] B 站 run 跑完 3 轮 12 节点：列、连线、节点状态色全部正确
- [ ] 点击不同节点，URL 变化，右侧面板内容切换
- [ ] 折叠左下角三张卡，刷新页面后仍保持折叠
- [ ] 中心区横向 / 纵向滚动正常
- [ ] keyword 超长（25 字+）截断 + tooltip 正常
- [ ] paused 节点显示橙色边框，候选词列表显示空态文案
- [ ] TapTap 平台跑一次，节点 metric 切换为评论数
- [ ] running 节点蓝色边框，跑完刷新后变绿
