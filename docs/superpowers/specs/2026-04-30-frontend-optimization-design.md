# SLG Sentinel 前端优化设计方案

> 参考目标：war-atlas.org 的左侧栏 + 中央视区布局模式

---

## 1. 目标

将 slg-sentinel 的前端从"全宽双栏"布局迁移到"左侧栏 + 中央主视区"的 war-atlas 风格布局，同时完成以下优化：
- CSS 提取到独立文件
- 通用数据表格组件
- 统一空状态 + CTA
- 移动端汉堡菜单
- 页面切换过渡动画

---

## 2. 布局架构

```
+----------+------------------------------------------+
|  侧边栏  |  上下文条 (页面名 + 语言 + DISPLAY) 36px  |
| 240px    +------------------------------------------+
| fixed    |                                          |
|          |                                          |
| 品牌Logo |         中央主视区                        |
| -------- |    calc(100dvh - 36px)                   |
| 页面导航 |         当前页面 stage                     |
| 7个入口  |                                          |
| -------- |                                          |
| 命令导航 |                                          |
| command  |                                          |
| pills    |                                          |
| -------- |                                          |
| 系统状态 |                                          |
| API/采集 |                                          |
| -------- |                                          |
| 语言切换 |                                          |
+----------+------------------------------------------+
```

- 侧边栏宽度 240px，fixed 定位
- 顶部上下文条高度 36px
- 中央区 margin-left: 240px
- 视口 100dvh，overflow hidden（保持现有单视口模型）

---

## 3. 侧边栏结构（自上而下）

### 3.1 品牌区
- Shield SVG icon + "SLG SENTINEL" 文字
- 字体 Cinzel，大写，字间距 2px
- 高度约 56px，与原顶部 nav 等高

### 3.2 页面导航
- 7 个页面入口，纵向排列
- 每项：SVG icon + 页面名（中文/英文）
- 当前页面高亮：左侧金色竖条 + 背景色加深
- 字体 IBM Plex Mono，11px，大写

### 3.3 命令导航（Command Pills）
- 从顶部 nav 下方移入侧边栏
- 以折叠区域（details/summary）放在页面导航下方
- 标签为当前页面名 + "COMMANDS"
- 展开后显示当前页面的命令 pill 列表

### 3.4 系统状态
- API 健康状态（绿/红点 + 文字）
- 今日采集量
- 最后同步时间
- 字体 IBM Plex Mono，10px

### 3.5 语言切换
- EN / ZH 双语 pill
- 固定在侧边栏底部

---

## 4. 顶部上下文条

- 高度 36px
- 左侧：当前页面图标 + 页面名（Cinzel，大写）
- 右侧：DISPLAY 芯片（从原 nav 移入）
- 背景：rgba(10,12,16,0.92) + backdrop-filter blur
- 底部边框：rgba(180,160,120,0.12)

---

## 5. CSS 提取策略

### 5.1 文件组织
```
static/
  war-atlas.css          # 从 app.py 提取的主样式 (~3950 行)
```

### 5.2 加载方式
app.py 通过以下方式加载：
```python
import pathlib
css = pathlib.Path("static/war-atlas.css").read_text()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
```

### 5.3 优先级
Phase 1 完成，不改变任何视觉效果，纯代码搬迁。

---

## 6. render_atlas_table 组件

### 6.1 接口
```python
def render_atlas_table(
    headers: list[str],
    rows: list[list[str]],
    accent: str = "#d4af37",
    compact: bool = False,
    max_height: str | None = None,
) -> str:
```

### 6.2 样式
- 从 war-atlas.css 统一管理表格样式
- 列宽自适应（table-layout: fixed + th 百分比）
- hover 行背景 rgba(180,160,120,0.04)
- 自定义 scrollbar

---

## 7. 空状态统一设计

### 7.1 结构
```
[图标 (48px, accent 色)]
[标题文字 - Cinzel, 14px, 大写]
[说明文字 - IBM Plex Sans, 13px, secondary 色]
[CTA 按钮 - accent 渐变]
```

### 7.2 各页面 CTA
- Overview: "开始采集" → 跳转 crawl 页
- Crawl: "选择平台开始采集"
- Profile: "先采集数据生成画像"
- Report: "先采集数据生成报表"
- Competitor: "选择两个竞品开始对比"

---

## 8. 移动端优化

### 8.1 断点
- 900px 以下：侧边栏折叠为图标模式（64px 宽）
- 600px 以下：侧边栏完全隐藏，顶部显示汉堡菜单按钮

### 8.2 汉堡菜单
- 点击后从左侧滑出侧边栏（overlay）
- 遮罩层 rgba(0,0,0,0.6)
- 点击遮罩或选择页面后自动关闭

---

## 9. 页面切换过渡动画

### 9.1 机制
- 使用 CSS transition + Streamlit session_state
- 页面路由切换时，中央区域 fade-out (200ms) → 内容更新 → fade-in (200ms)
- 实现方式：在 atlas_stage 外层容器加 CSS class 控制 opacity

### 9.2 CSS
```css
.wa-page-transition {
  transition: opacity 200ms ease;
}
.wa-page-transition--hidden {
  opacity: 0;
}
```

---

## 10. 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app.py` | 大改 | CSS 移除，路由逻辑改为侧边栏 + 上下文条布局 |
| `static/war-atlas.css` | 新建 | 从 app.py 提取的主样式 |
| `ui/components/atlas_shell.py` | 修改 | 新增侧边栏渲染函数，修改 stage 布局 |
| `ui/components/common.py` | 修改 | 统一 empty state，新增 render_atlas_table |
| `ui/components/sidebar.py` | 新建 | 侧边栏渲染逻辑 |
| `ui/pages/*.py` | 修改 | 适配新布局，移除内联表格样式 |
| `.streamlit/config.toml` | 不变 | - |
