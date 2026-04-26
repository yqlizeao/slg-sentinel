# Recursive 模块中心可视化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `ui/pages/recursive_crawl.py` 的中心装饰区改造为递归搜索图（横向每轮一列，节点 = 关键词 + 视频数，父子节点连线），点击节点切换右侧"节点详情"面板（视频列表 + 候选词），左下角三张报表卡支持折叠收起。

**Architecture:** 服务端一次性渲染 HTML/SVG（无 JS、无自定义 component）。点击节点 → `<a href="?recursive_node=ID">` 触发 Streamlit rerun → 服务端读 `st.query_params` 决定渲染哪个节点。新增 `ui/components/recursive_graph.py` 集中放图形/详情/折叠相关纯渲染函数；`ui/services/app_services.py` 加 `load_videos_for_node` 与 `read_video_id_set` 数据访问辅助；`ui/pages/recursive_crawl.py::_run_recursive_crawl` 在节点执行前后捕获 video_ids 写入 `node.crawl_metrics.video_ids`。

**Tech Stack:** Python 3.12, Streamlit, pandas, pytest, 内联 HTML/SVG/CSS

**Spec:** `docs/superpowers/specs/2026-04-27-recursive-graph-design.md`

---

## File Structure

| 文件 | 职责 |
|---|---|
| `ui/components/recursive_graph.py`（新） | 纯渲染：`calculate_layout`、`render_graph_scene`、`render_node_detail`、`render_panels_collapsible`、`url_with` |
| `ui/services/app_services.py`（改） | 新增 `read_video_id_set(platform)`、`load_videos_for_node(run, node, limit)` |
| `ui/pages/recursive_crawl.py`（改） | `_run_recursive_crawl` 持久化 `video_ids`；`render_recursive_crawl_page` 用新组件替换 `scene_html` / `panels` / `drawers` 三段 |
| `app.py`（改） | 在已有 CSS 块里追加 `.recursive-graph*` / `.recursive-node-detail` / `.atlas-shell-panels-wrap` 样式 |
| `tests/test_recursive_graph.py`（新） | 布局算法、URL helper、HTML 渲染断言 |
| `tests/test_recursive_runs.py`（改） | 加 `load_videos_for_node` 与 `read_video_id_set` 测试 |

---

## Task 1: `read_video_id_set` 平台视频快照

**Files:**
- Modify: `ui/services/app_services.py` (add at end of file, near `get_crawl_file_snapshot` line 719)
- Test: `tests/test_recursive_runs.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_recursive_runs.py`:

```python
def test_read_video_id_set_groups_by_csv_path(tmp_path, monkeypatch):
    from ui.services import app_services

    v_dir = tmp_path / "video_platforms" / "bilibili" / "videos"
    v_dir.mkdir(parents=True)
    (v_dir / "2026-04-27_videos.csv").write_text(
        "platform,video_id,title\nbilibili,BV1,蜀汉\nbilibili,BV2,曹魏\n",
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    snapshot = app_services.read_video_id_set("bilibili")

    paths = list(snapshot.keys())
    assert len(paths) == 1
    assert snapshot[paths[0]] == {"BV1", "BV2"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_recursive_runs.py::test_read_video_id_set_groups_by_csv_path -v
```
Expected: FAIL `AttributeError: ... has no attribute 'read_video_id_set'`

- [ ] **Step 3: Implement `read_video_id_set`**

Append to `ui/services/app_services.py`:

```python
def read_video_id_set(platform: str) -> dict[str, set[str]]:
    """Return {csv_path_str: {video_id, ...}} snapshot of all platform's videos CSVs.

    Used by the recursive graph to capture per-node video_id deltas across the
    crawl boundary.
    """
    from src.core.csv_store import VIDEO_PLATFORMS, COMMUNITY_PLATFORMS

    if platform in VIDEO_PLATFORMS:
        category = "video_platforms"
    elif platform in COMMUNITY_PLATFORMS:
        category = "community_platforms"
    else:
        category = "misc_platforms"

    v_dir = DATA_DIR / category / platform / "videos"
    snapshot: dict[str, set[str]] = {}
    if not v_dir.exists():
        return snapshot

    for csv_file in v_dir.glob("*.csv"):
        ids: set[str] = set()
        try:
            with open(csv_file, encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    vid = (row.get("video_id") or "").strip()
                    if vid:
                        ids.add(vid)
        except Exception:
            continue
        snapshot[str(csv_file)] = ids
    return snapshot
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_recursive_runs.py::test_read_video_id_set_groups_by_csv_path -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui/services/app_services.py tests/test_recursive_runs.py
git commit -m "feat(services): add read_video_id_set platform snapshot helper"
```

---

## Task 2: `load_videos_for_node` 双策略加载

**Files:**
- Modify: `ui/services/app_services.py`
- Test: `tests/test_recursive_runs.py`

- [ ] **Step 1: Write failing tests for both code paths**

Append to `tests/test_recursive_runs.py`:

```python
def test_load_videos_for_node_uses_video_ids_when_present(tmp_path, monkeypatch):
    from ui.services import app_services

    v_dir = tmp_path / "video_platforms" / "bilibili" / "videos"
    v_dir.mkdir(parents=True)
    (v_dir / "2026-04-27_videos.csv").write_text(
        "platform,video_id,title,author,view_count,publish_date,url\n"
        "bilibili,BV1,蜀汉将领,Up1,12000,2026-04-25,https://b/1\n"
        "bilibili,BV2,曹魏五子,Up2,8000,2026-04-26,https://b/2\n"
        "bilibili,BV3,东吴水军,Up3,3000,2026-04-26,https://b/3\n",
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    run = {"platform": "bilibili"}
    node = {
        "keyword": "三国",
        "started_at": "2026-04-27T10:00:00",
        "crawl_metrics": {"videos": 2, "video_ids": ["BV1", "BV3"]},
    }

    rows = app_services.load_videos_for_node(run, node, limit=20)

    ids = [r["video_id"] for r in rows]
    assert sorted(ids) == ["BV1", "BV3"]
    assert rows[0]["title"] in {"蜀汉将领", "东吴水军"}


def test_load_videos_for_node_falls_back_to_snapshot_date(tmp_path, monkeypatch):
    from ui.services import app_services

    v_dir = tmp_path / "video_platforms" / "bilibili" / "videos"
    v_dir.mkdir(parents=True)
    (v_dir / "2026-04-27_videos.csv").write_text(
        "platform,video_id,title,author,view_count,snapshot_date,publish_date,url\n"
        "bilibili,BV1,蜀汉将领,Up1,12000,2026-04-27,2026-04-25,https://b/1\n"
        "bilibili,BV2,曹魏五子,Up2,8000,2026-04-26,2026-04-26,https://b/2\n",
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    run = {"platform": "bilibili"}
    node = {
        "keyword": "三国",
        "started_at": "2026-04-27T10:00:00",
        "crawl_metrics": {"videos": 1},  # no video_ids — old run
    }

    rows = app_services.load_videos_for_node(run, node, limit=20)

    assert len(rows) == 1
    assert rows[0]["video_id"] == "BV1"
    assert rows[0]["fallback"] is True


def test_load_videos_for_node_empty_when_no_match(tmp_path, monkeypatch):
    from ui.services import app_services

    v_dir = tmp_path / "video_platforms" / "bilibili" / "videos"
    v_dir.mkdir(parents=True)
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    run = {"platform": "bilibili"}
    node = {"keyword": "无", "started_at": "2026-04-27T10:00:00", "crawl_metrics": {"videos": 0}}

    assert app_services.load_videos_for_node(run, node) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_recursive_runs.py -k load_videos_for_node -v
```
Expected: FAIL `has no attribute 'load_videos_for_node'`

- [ ] **Step 3: Implement `load_videos_for_node`**

Append to `ui/services/app_services.py`:

```python
def load_videos_for_node(run: dict, node: dict, limit: int = 20) -> list[dict]:
    """Return up to `limit` video rows associated with this recursive node.

    Strategy:
    1. If `node.crawl_metrics.video_ids` exists (new runs), filter platform
       videos CSVs by exact video_id membership.
    2. Otherwise fall back to filtering by `snapshot_date == node.started_at[:10]`
       and tag rows with `fallback=True` so callers can show a hint.
    """
    platform = run.get("platform", "")
    crawl = node.get("crawl_metrics", {}) or {}
    video_ids: list[str] = list(crawl.get("video_ids") or [])

    snapshot = read_video_id_set(platform)
    csv_paths = list(snapshot.keys())
    if not csv_paths:
        return []

    rows: list[dict] = []
    if video_ids:
        wanted = set(video_ids)
        for path_str in csv_paths:
            try:
                with open(path_str, encoding="utf-8-sig") as fh:
                    reader = csv.DictReader(fh)
                    for raw in reader:
                        if raw.get("video_id") in wanted:
                            rows.append({**raw, "fallback": False})
                            if len(rows) >= limit:
                                return rows
            except Exception:
                continue
        return rows

    # Fallback path: snapshot_date match
    target_date = (node.get("started_at") or "")[:10]
    if not target_date:
        return []
    for path_str in csv_paths:
        try:
            with open(path_str, encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                for raw in reader:
                    if (raw.get("snapshot_date") or "") == target_date:
                        rows.append({**raw, "fallback": True})
                        if len(rows) >= limit:
                            return rows
        except Exception:
            continue
    return rows
```

- [ ] **Step 4: Run tests to verify pass**

```bash
python -m pytest tests/test_recursive_runs.py -k load_videos_for_node -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add ui/services/app_services.py tests/test_recursive_runs.py
git commit -m "feat(services): load_videos_for_node with video_ids + snapshot_date fallback"
```

---

## Task 3: 节点 video_ids 持久化

**Files:**
- Modify: `ui/pages/recursive_crawl.py:732-769` (the per-keyword crawl block inside `_run_recursive_crawl`)
- Test: `tests/test_recursive_graph.py` (new file)

- [ ] **Step 1: Write the failing test**

Create `tests/test_recursive_graph.py`:

```python
def test_video_id_diff_helper(tmp_path, monkeypatch):
    """Diff between two read_video_id_set snapshots returns added IDs only."""
    from ui.components.recursive_graph import diff_video_ids

    before = {"a.csv": {"BV1", "BV2"}}
    after = {"a.csv": {"BV1", "BV2", "BV3"}, "b.csv": {"BV9"}}

    added = diff_video_ids(before, after)

    assert sorted(added) == ["BV3", "BV9"]


def test_video_id_diff_empty_when_no_change():
    from ui.components.recursive_graph import diff_video_ids

    before = {"a.csv": {"BV1"}}
    after = {"a.csv": {"BV1"}}

    assert diff_video_ids(before, after) == []
```

- [ ] **Step 2: Run test to verify failure**

```bash
python -m pytest tests/test_recursive_graph.py -v
```
Expected: FAIL `ModuleNotFoundError: ui.components.recursive_graph`

- [ ] **Step 3: Create stub component module with `diff_video_ids`**

Create `ui/components/recursive_graph.py`:

```python
"""Recursive crawl graph rendering — pure HTML/SVG, no JS."""
from __future__ import annotations


def diff_video_ids(
    before: dict[str, set[str]],
    after: dict[str, set[str]],
) -> list[str]:
    """Return video_ids present in `after` but not in `before`, across all paths."""
    added: list[str] = []
    for path, after_ids in after.items():
        before_ids = before.get(path, set())
        for vid in sorted(after_ids - before_ids):
            added.append(vid)
    return added
```

- [ ] **Step 4: Run test to verify pass**

```bash
python -m pytest tests/test_recursive_graph.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Wire into `_run_recursive_crawl`**

In `ui/pages/recursive_crawl.py`, find the per-keyword crawl block (around line 732 `keyword_started_at = datetime.now()`). Update imports at top:

```python
from ui.components.recursive_graph import diff_video_ids
from ui.services.app_services import read_video_id_set  # add to existing import block
```

Replace the block (lines 732-755 originally):

```python
            keyword_started_at = datetime.now()
            before_snapshot = get_crawl_file_snapshot(platform)
            tmp_keywords_path = write_temporary_keyword_file([keyword], label=f"{platform}_round_{round_idx}_{keyword}")
            cmd_args = [
                "crawl",
                "--platform",
                platform,
                "--mode",
                mode_value,
                "--order",
                config["order_val"],
                "--limit",
                str(config["limit_val"]),
                "--keywords-file",
                str(tmp_keywords_path),
            ] + depth_args

            def on_recursive_line(line: str) -> None:
                update_crawl_progress_state(progress_state, line)
                recursive_logs.append(f"[Round {round_idx}] {line}")
                refresh_recursive_ui(round_idx, progress_state)

            stdout, stderr, code = run_cli_stream(cmd_args, on_line=on_recursive_line)
            after_snapshot = get_crawl_file_snapshot(platform)
```

with this version (added `before_video_ids` capture + `node_video_ids` after the crawl):

```python
            keyword_started_at = datetime.now()
            before_snapshot = get_crawl_file_snapshot(platform)
            before_video_ids = read_video_id_set(platform)
            tmp_keywords_path = write_temporary_keyword_file([keyword], label=f"{platform}_round_{round_idx}_{keyword}")
            cmd_args = [
                "crawl",
                "--platform",
                platform,
                "--mode",
                mode_value,
                "--order",
                config["order_val"],
                "--limit",
                str(config["limit_val"]),
                "--keywords-file",
                str(tmp_keywords_path),
            ] + depth_args

            def on_recursive_line(line: str) -> None:
                update_crawl_progress_state(progress_state, line)
                recursive_logs.append(f"[Round {round_idx}] {line}")
                refresh_recursive_ui(round_idx, progress_state)

            stdout, stderr, code = run_cli_stream(cmd_args, on_line=on_recursive_line)
            after_snapshot = get_crawl_file_snapshot(platform)
            node_video_ids = diff_video_ids(before_video_ids, read_video_id_set(platform))
```

Then find the `crawl_metrics = {...}` dict (originally lines 769-773) and add the `video_ids` field:

```python
            crawl_metrics = {
                "videos": result["added_videos"],
                "comments": result["added_comments"],
                "touched_files": result["touched_files"],
                "video_ids": node_video_ids,
            }
```

- [ ] **Step 6: Smoke test with existing recursive flow tests**

```bash
python -m pytest tests/test_recursive_runs.py -v
```
Expected: all existing tests still PASS

- [ ] **Step 7: Commit**

```bash
git add ui/pages/recursive_crawl.py ui/components/recursive_graph.py tests/test_recursive_graph.py
git commit -m "feat(recursive): persist per-node video_ids during crawl"
```

---

## Task 4: 布局算法 `calculate_layout`

**Files:**
- Modify: `ui/components/recursive_graph.py`
- Test: `tests/test_recursive_graph.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_recursive_graph.py`:

```python
def test_calculate_layout_single_round_single_node():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "三国", "round": 1, "parent_id": "",
             "status": "success",
             "crawl_metrics": {"videos": 12},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [],
    }

    layout = calculate_layout(run)

    assert len(layout["nodes"]) == 1
    n = layout["nodes"][0]
    assert n["x"] == 0
    assert n["y"] == 32  # COL_HEAD_H
    assert n["height"] == 56  # 1-line keyword + no extras
    assert n["width"] == 220
    assert layout["edges"] == []
    assert layout["svg_height"] >= n["y"] + n["height"]
    assert layout["svg_width"] == 220


def test_calculate_layout_two_rounds_with_edge():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "三国", "round": 1, "parent_id": "",
             "status": "success", "crawl_metrics": {"videos": 5},
             "candidate_metrics": {"count": 3}},
            {"node_id": "n2", "keyword": "蜀汉", "round": 2, "parent_id": "n1",
             "status": "success", "crawl_metrics": {"videos": 9},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [{"from": "n1", "to": "n2", "keyword": "蜀汉"}],
    }

    layout = calculate_layout(run)

    n1 = next(n for n in layout["nodes"] if n["node_id"] == "n1")
    n2 = next(n for n in layout["nodes"] if n["node_id"] == "n2")
    assert n1["x"] == 0
    assert n2["x"] == 220 + 80  # COL_W + COL_GAP
    assert n1["height"] == 72  # 1-line keyword + extras
    assert n2["height"] == 56  # 1-line keyword + no extras
    assert len(layout["edges"]) == 1
    edge = layout["edges"][0]
    assert edge["from_node_id"] == "n1"
    assert edge["to_node_id"] == "n2"
    assert "M" in edge["path"] and "C" in edge["path"]


def test_calculate_layout_long_keyword_grows_height():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "三国群英战棋无双版本测评首发",
             "round": 1, "parent_id": "", "status": "success",
             "crawl_metrics": {"videos": 1}, "candidate_metrics": {"count": 0}},
        ],
        "edges": [],
    }

    layout = calculate_layout(run)

    assert layout["nodes"][0]["height"] == 80  # 2-line keyword + no extras


def test_calculate_layout_sorts_children_by_score():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "p", "keyword": "三国", "round": 1, "parent_id": "",
             "status": "success", "crawl_metrics": {"videos": 1},
             "candidate_metrics": {"count": 0}},
            {"node_id": "c1", "keyword": "弱", "round": 2, "parent_id": "p",
             "status": "success", "crawl_metrics": {"videos": 1, "score": 1.0},
             "candidate_metrics": {"count": 0}},
            {"node_id": "c2", "keyword": "强", "round": 2, "parent_id": "p",
             "status": "success", "crawl_metrics": {"videos": 1, "score": 9.0},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [
            {"from": "p", "to": "c1", "keyword": "弱"},
            {"from": "p", "to": "c2", "keyword": "强"},
        ],
    }

    layout = calculate_layout(run)

    children = [n for n in layout["nodes"] if n["round"] == 2]
    assert children[0]["node_id"] == "c2"  # higher score first
    assert children[1]["node_id"] == "c1"
```

- [ ] **Step 2: Run failing tests**

```bash
python -m pytest tests/test_recursive_graph.py -k calculate_layout -v
```
Expected: FAIL `has no attribute 'calculate_layout'`

- [ ] **Step 3: Implement `calculate_layout`**

Append to `ui/components/recursive_graph.py`:

```python
COL_W = 220
COL_GAP = 80
COL_HEAD_H = 32
NODE_GAP = 14
KEYWORD_CHARS_PER_LINE = 12  # rough fit for 220-px column at 16px font


def _estimate_keyword_lines(keyword: str) -> int:
    """Wide CJK chars count as 2; ASCII as 1. Capped at 2 visible lines."""
    width = 0
    for ch in keyword:
        width += 2 if ord(ch) > 0x2E80 else 1
    chars_per_line_visual = KEYWORD_CHARS_PER_LINE * 2  # visual width budget per line
    lines = max(1, -(-width // chars_per_line_visual))
    return min(lines, 2)


def _node_height(keyword: str, has_extras: bool) -> int:
    lines = _estimate_keyword_lines(keyword)
    if lines == 1 and has_extras:
        return 72
    if lines == 1 and not has_extras:
        return 56
    if lines == 2 and has_extras:
        return 96
    return 80  # 2 lines, no extras


def _sort_round_nodes(parent_layout_y: dict[str, int], nodes: list[dict]) -> list[dict]:
    """Round-1: dictionary order. Round-N: by parent y asc, then score desc."""
    if not nodes:
        return nodes
    if all(not n.get("parent_id") for n in nodes):
        return sorted(nodes, key=lambda n: n.get("node_id", ""))

    def key(node: dict) -> tuple:
        py = parent_layout_y.get(node.get("parent_id", ""), 0)
        score = float((node.get("crawl_metrics", {}) or {}).get("score", 0) or 0)
        return (py, -score, node.get("node_id", ""))

    return sorted(nodes, key=key)


def calculate_layout(run: dict) -> dict:
    """Return {nodes: [...], edges: [...], svg_width, svg_height} for HTML rendering.

    Each node dict carries x, y, width, height, plus original keyword/status etc.
    Each edge dict carries `path` (SVG cubic bezier d-attr) and source/target ids.
    """
    nodes = list(run.get("nodes", []))
    edges_meta = list(run.get("edges", []))

    if not nodes:
        return {"nodes": [], "edges": [], "svg_width": 0, "svg_height": 0}

    rounds = sorted({int(n.get("round", 0) or 0) for n in nodes})
    layout_by_id: dict[str, dict] = {}
    parent_y: dict[str, int] = {}
    col_heights: list[int] = []

    for round_idx in rounds:
        round_nodes = [n for n in nodes if int(n.get("round", 0) or 0) == round_idx]
        ordered = _sort_round_nodes(parent_y, round_nodes)
        y_cursor = COL_HEAD_H
        x = (round_idx - 1) * (COL_W + COL_GAP) if round_idx > 0 else 0
        for node in ordered:
            crawl = node.get("crawl_metrics", {}) or {}
            cands = node.get("candidate_metrics", {}) or {}
            has_extras = int(cands.get("count", 0) or 0) > 0
            h = _node_height(node.get("keyword", ""), has_extras)
            laid = {
                "node_id": node.get("node_id"),
                "keyword": node.get("keyword", ""),
                "round": round_idx,
                "status": node.get("status", ""),
                "parent_id": node.get("parent_id", ""),
                "videos": int(crawl.get("videos", 0) or 0),
                "candidates_count": int(cands.get("count", 0) or 0),
                "x": x,
                "y": y_cursor,
                "width": COL_W,
                "height": h,
            }
            layout_by_id[node.get("node_id")] = laid
            parent_y[node.get("node_id")] = y_cursor
            y_cursor += h + NODE_GAP
        col_heights.append(y_cursor)

    edges_layout = []
    for edge in edges_meta:
        src = layout_by_id.get(edge.get("from"))
        dst = layout_by_id.get(edge.get("to"))
        if not src or not dst:
            continue
        sx = src["x"] + src["width"]
        sy = src["y"] + src["height"] / 2
        dx = dst["x"]
        dy = dst["y"] + dst["height"] / 2
        path = f"M{sx} {sy} C{sx + 40} {sy}, {dx - 40} {dy}, {dx} {dy}"
        edges_layout.append({
            "from_node_id": edge.get("from"),
            "to_node_id": edge.get("to"),
            "path": path,
            "status": dst["status"],
        })

    return {
        "nodes": list(layout_by_id.values()),
        "edges": edges_layout,
        "svg_width": (rounds[-1]) * (COL_W + COL_GAP) - COL_GAP if rounds else 0,
        "svg_height": max(col_heights) if col_heights else 0,
    }
```

- [ ] **Step 4: Run tests to verify pass**

```bash
python -m pytest tests/test_recursive_graph.py -k calculate_layout -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add ui/components/recursive_graph.py tests/test_recursive_graph.py
git commit -m "feat(recursive-graph): pure-function layout calculator with bezier edges"
```

---

## Task 5: `url_with` Helper

**Files:**
- Modify: `ui/components/recursive_graph.py`
- Test: `tests/test_recursive_graph.py`

- [ ] **Step 1: Write failing tests**

Append:

```python
def test_url_with_overrides_preserves_other_keys():
    from ui.components.recursive_graph import url_with

    assert url_with({"recursive_node": "n1", "recursive_panels": "open"},
                    recursive_node="n2") == "?recursive_node=n2&recursive_panels=open"


def test_url_with_drops_empty_values():
    from ui.components.recursive_graph import url_with

    assert url_with({"recursive_node": "n1"},
                    recursive_node=None) == "?"


def test_url_with_no_existing_params():
    from ui.components.recursive_graph import url_with

    assert url_with({}, recursive_panels="closed") == "?recursive_panels=closed"
```

- [ ] **Step 2: Run failing tests**

```bash
python -m pytest tests/test_recursive_graph.py -k url_with -v
```
Expected: FAIL `has no attribute 'url_with'`

- [ ] **Step 3: Implement**

Append to `ui/components/recursive_graph.py`:

```python
from urllib.parse import quote


def url_with(current: dict, **overrides) -> str:
    """Build a relative URL preserving current query, applying overrides.

    `None` value drops the key. Non-string values are coerced via str().
    """
    merged = {k: v for k, v in current.items() if v is not None and v != ""}
    for key, value in overrides.items():
        if value is None or value == "":
            merged.pop(key, None)
        else:
            merged[key] = str(value)
    if not merged:
        return "?"
    parts = [f"{quote(str(k))}={quote(str(v))}" for k, v in merged.items()]
    return "?" + "&".join(parts)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
python -m pytest tests/test_recursive_graph.py -k url_with -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add ui/components/recursive_graph.py tests/test_recursive_graph.py
git commit -m "feat(recursive-graph): url_with helper for query-param navigation"
```

---

## Task 6: `render_graph_scene` HTML

**Files:**
- Modify: `ui/components/recursive_graph.py`
- Test: `tests/test_recursive_graph.py`

- [ ] **Step 1: Write failing tests**

Append:

```python
def test_render_graph_scene_empty_run():
    from ui.components.recursive_graph import render_graph_scene

    html = render_graph_scene({"nodes": [], "edges": []}, selected_node_id=None, query={})

    assert "暂无递归任务" in html
    assert "recursive-graph-empty" in html


def test_render_graph_scene_marks_selected_node():
    from ui.components.recursive_graph import render_graph_scene

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "三国", "round": 1, "parent_id": "",
             "status": "success", "crawl_metrics": {"videos": 5},
             "candidate_metrics": {"count": 0}},
            {"node_id": "n2", "keyword": "蜀汉", "round": 2, "parent_id": "n1",
             "status": "running", "crawl_metrics": {"videos": 2},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [{"from": "n1", "to": "n2", "keyword": "蜀汉"}],
    }

    html = render_graph_scene(run, selected_node_id="n2", query={"recursive_panels": "open"})

    assert "is-selected" in html
    assert "recursive_node=n1" in html  # both nodes carry navigable links (incl. selected)
    assert "recursive_node=n2" in html
    assert "recursive_panels=open" in html  # query state preserved in node hrefs
    assert "is-success" in html
    assert "is-running" in html
    assert "ROUND 01" in html and "ROUND 02" in html
    assert "5 视频" in html and "2 视频" in html
    assert "<path" in html  # edge SVG path


def test_render_graph_scene_escapes_html_in_keyword():
    from ui.components.recursive_graph import render_graph_scene

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "<script>", "round": 1, "parent_id": "",
             "status": "success", "crawl_metrics": {"videos": 0},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [],
    }

    html = render_graph_scene(run, selected_node_id="n1", query={})

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
```

- [ ] **Step 2: Run failing tests**

```bash
python -m pytest tests/test_recursive_graph.py -k render_graph_scene -v
```
Expected: FAIL

- [ ] **Step 3: Implement**

Append:

```python
from html import escape as _escape

STATUS_TONE = {
    "success": "is-success",
    "running": "is-running",
    "paused": "is-paused",
    "error": "is-error",
}


def render_graph_scene(run: dict, *, selected_node_id: str | None, query: dict) -> str:
    """Render the center graph: columns with nodes + bezier edges. Empty-state safe."""
    layout = calculate_layout(run)
    if not layout["nodes"]:
        return (
            "<div class='recursive-graph-empty'>"
            "<strong>暂无递归任务</strong>"
            "<span>左上角『候选话题』启动一次 AI 探索，即可在这里看到搜索图</span>"
            "</div>"
        )

    rounds_present = sorted({n["round"] for n in layout["nodes"]})
    cols_html_parts: list[str] = []
    for round_idx in rounds_present:
        round_nodes = sorted(
            [n for n in layout["nodes"] if n["round"] == round_idx],
            key=lambda n: n["y"],
        )
        head_x = (round_idx - 1) * (COL_W + COL_GAP)
        head = (
            f"<div class='recursive-graph-col-head' "
            f"style='left:{head_x}px;'>ROUND {round_idx:02d}</div>"
        )
        node_parts: list[str] = []
        for node in round_nodes:
            tone = STATUS_TONE.get(node["status"], "")
            sel = " is-selected" if node["node_id"] == selected_node_id else ""
            href = url_with(query, recursive_node=node["node_id"])
            extras = ""
            if node["candidates_count"] > 0:
                extras = f"<div class='node-extras'>下一轮 {node['candidates_count']} 词</div>"
            keyword_html = _escape(node["keyword"])
            node_parts.append(
                f"<a class='recursive-graph-node {tone}{sel}' "
                f"href='{_escape(href)}' title='{keyword_html}' "
                f"style='left:{node['x']}px;top:{node['y']}px;"
                f"width:{node['width']}px;height:{node['height']}px;'>"
                f"<div class='node-status-dot'></div>"
                f"<div class='node-keyword'>{keyword_html}</div>"
                f"<div class='node-metric'>{node['videos']} 视频</div>"
                f"{extras}"
                "</a>"
            )
        cols_html_parts.append(head + "".join(node_parts))

    edges_html = "".join(
        f"<path d='{_escape(edge['path'])}' "
        f"class='recursive-graph-edge {STATUS_TONE.get(edge['status'], '')}' />"
        for edge in layout["edges"]
    )

    return (
        f"<div class='recursive-graph'>"
        f"<svg class='recursive-graph-edges' "
        f"viewBox='0 0 {layout['svg_width']} {layout['svg_height']}' "
        f"width='{layout['svg_width']}' height='{layout['svg_height']}'>"
        f"{edges_html}"
        f"</svg>"
        f"<div class='recursive-graph-cols' "
        f"style='width:{layout['svg_width']}px;height:{layout['svg_height']}px;'>"
        f"{''.join(cols_html_parts)}"
        f"</div>"
        f"</div>"
    )
```

- [ ] **Step 4: Run tests to verify pass**

```bash
python -m pytest tests/test_recursive_graph.py -k render_graph_scene -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add ui/components/recursive_graph.py tests/test_recursive_graph.py
git commit -m "feat(recursive-graph): render center scene with status-tinted nodes and edges"
```

---

## Task 7: `render_node_detail` HTML

**Files:**
- Modify: `ui/components/recursive_graph.py`
- Test: `tests/test_recursive_graph.py`

- [ ] **Step 1: Write failing tests**

Append:

```python
def test_render_node_detail_videos_and_candidates():
    from ui.components.recursive_graph import render_node_detail

    node = {
        "node_id": "n1", "keyword": "蜀汉将领",
        "round": 2, "status": "success",
        "crawl_metrics": {"videos": 9},
        "candidate_metrics": {
            "count": 2,
            "candidates": [
                {"keyword": "战棋玩法", "score": 6.2},
                {"keyword": "三国战略", "score": 4.1},
            ],
        },
    }
    videos = [
        {"title": "蜀汉开荒", "author": "Up1", "view_count": "12000",
         "publish_date": "2026-04-25", "url": "https://b/1", "fallback": False},
    ]

    html = render_node_detail(node, videos)

    assert "蜀汉将领" in html
    assert "第 2 轮" in html and "success" in html
    assert "9 视频" in html
    assert "蜀汉开荒" in html
    assert "1.2w" in html or "12000" in html  # tolerated formatting
    assert "战棋玩法" in html and "6.2" in html
    assert "data-status=\"success\"" in html


def test_render_node_detail_paused_with_empty_states():
    from ui.components.recursive_graph import render_node_detail

    node = {
        "node_id": "n1", "keyword": "三国",
        "round": 1, "status": "paused",
        "crawl_metrics": {"videos": 0},
        "candidate_metrics": {"count": 0, "candidates": []},
        "stop_reason": "B站搜索量无法获取",
    }

    html = render_node_detail(node, [])

    assert "data-status=\"paused\"" in html
    assert "未采集到视频" in html
    assert "未挖掘出新候选词" in html


def test_render_node_detail_fallback_hint():
    from ui.components.recursive_graph import render_node_detail

    node = {
        "node_id": "n1", "keyword": "三国",
        "round": 1, "status": "success",
        "crawl_metrics": {"videos": 1},
        "candidate_metrics": {"count": 0, "candidates": []},
    }
    videos = [{"title": "x", "author": "y", "view_count": "1",
               "publish_date": "2026-04-26", "url": "u", "fallback": True}]

    html = render_node_detail(node, videos)

    assert "估算结果" in html
```

- [ ] **Step 2: Run failing tests**

```bash
python -m pytest tests/test_recursive_graph.py -k render_node_detail -v
```
Expected: FAIL

- [ ] **Step 3: Implement**

Append:

```python
def _format_view(value: object) -> str:
    try:
        n = int(float(str(value)))
    except (TypeError, ValueError):
        return str(value or "—")
    if n >= 10_000:
        return f"{n/10_000:.1f}w"
    return str(n)


def render_node_detail(node: dict, videos: list[dict]) -> str:
    """Right-side panel: header + video list + candidate list."""
    status = node.get("status", "")
    keyword = _escape(node.get("keyword", ""))
    crawl = node.get("crawl_metrics", {}) or {}
    cands = node.get("candidate_metrics", {}) or {}
    videos_count = int(crawl.get("videos", 0) or 0)
    cand_count = int(cands.get("count", 0) or 0)

    fallback_hint = ""
    if any(v.get("fallback") for v in videos):
        fallback_hint = "<div class='recursive-detail-hint'>数据为旧版 run 估算结果</div>"

    if videos:
        items = []
        for v in videos:
            title = _escape(str(v.get("title") or "—"))
            author = _escape(str(v.get("author") or "—"))
            view = _format_view(v.get("view_count") or v.get("view") or 0)
            pubdate = _escape(str(v.get("publish_date") or v.get("pubdate") or ""))
            url = _escape(str(v.get("url") or "#"))
            items.append(
                f"<li><a href='{url}' target='_blank' rel='noopener'>"
                f"<div class='title'>{title}</div>"
                f"<div class='meta'>{author} · {view}播放 · {pubdate}</div>"
                f"</a></li>"
            )
        videos_block = f"<ul>{''.join(items)}</ul>"
        if videos_count > len(videos):
            videos_block += f"<div class='recursive-detail-more'>...还有 {videos_count - len(videos)} 条</div>"
    else:
        videos_block = "<div class='recursive-detail-empty'>该节点未采集到视频</div>"

    candidates = cands.get("candidates") or []
    if candidates:
        cand_items = []
        for c in candidates:
            ck = _escape(str(c.get("keyword") or ""))
            cs = c.get("score", 0)
            try:
                cs_text = f"{float(cs):.1f}"
            except (TypeError, ValueError):
                cs_text = str(cs)
            cand_items.append(
                f"<li><span>{ck}</span><b>★ {cs_text}</b></li>"
            )
        candidates_block = f"<ul>{''.join(cand_items)}</ul>"
    else:
        candidates_block = "<div class='recursive-detail-empty'>未挖掘出新候选词</div>"

    return (
        f"<aside class='recursive-node-detail' data-status=\"{_escape(status)}\">"
        f"<header>"
        f"<div class='kicker'>第 {int(node.get('round', 0) or 0)} 轮 · "
        f"{_escape(status)} · {videos_count} 视频</div>"
        f"<h3>{keyword}</h3>"
        f"</header>"
        f"<section class='videos'>"
        f"<div class='section-title'>视频列表 ({videos_count})</div>"
        f"{fallback_hint}"
        f"{videos_block}"
        f"</section>"
        f"<section class='candidates'>"
        f"<div class='section-title'>下一轮候选词 ({cand_count})</div>"
        f"{candidates_block}"
        f"</section>"
        f"</aside>"
    )
```

- [ ] **Step 4: Run tests to verify pass**

```bash
python -m pytest tests/test_recursive_graph.py -k render_node_detail -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add ui/components/recursive_graph.py tests/test_recursive_graph.py
git commit -m "feat(recursive-graph): node detail panel with videos + candidates + fallback hint"
```

---

## Task 8: 折叠 panels 包装 `render_panels_collapsible`

**Files:**
- Modify: `ui/components/recursive_graph.py`
- Test: `tests/test_recursive_graph.py`

- [ ] **Step 1: Write failing tests**

Append:

```python
def test_render_panels_collapsible_open_default():
    from ui.components.recursive_graph import render_panels_collapsible

    html = render_panels_collapsible(
        panels_html="<article>A</article><article>B</article><article>C</article>",
        collapsed=False,
        toggle_url="?recursive_panels=closed",
    )

    assert "<details" in html and " open" in html
    assert "状态报告 · 3" in html
    assert "?recursive_panels=closed" in html
    assert "<article>A</article>" in html


def test_render_panels_collapsible_when_collapsed():
    from ui.components.recursive_graph import render_panels_collapsible

    html = render_panels_collapsible(
        panels_html="<article>A</article>",
        collapsed=True,
        toggle_url="?",
    )

    assert "<details" in html
    assert "<details open" not in html and "open=" not in html
    assert "▴" in html or "▾" in html
```

- [ ] **Step 2: Run failing tests**

```bash
python -m pytest tests/test_recursive_graph.py -k panels_collapsible -v
```
Expected: FAIL

- [ ] **Step 3: Implement**

Append:

```python
def render_panels_collapsible(
    *,
    panels_html: str,
    collapsed: bool,
    toggle_url: str,
) -> str:
    """Wrap the three atlas panel cards in a <details> with summary toggle."""
    open_attr = "" if collapsed else " open"
    icon = "▴" if collapsed else "▾"
    return (
        f"<details class='atlas-shell-panels-wrap'{open_attr}>"
        f"<summary class='atlas-shell-panels-summary'>"
        f"<span>状态报告 · 3</span>"
        f"<a class='collapse-toggle' href='{_escape(toggle_url)}'>{icon}</a>"
        f"</summary>"
        f"<div class='atlas-shell-panels'>{panels_html}</div>"
        f"</details>"
    )
```

- [ ] **Step 4: Run tests to verify pass**

```bash
python -m pytest tests/test_recursive_graph.py -k panels_collapsible -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add ui/components/recursive_graph.py tests/test_recursive_graph.py
git commit -m "feat(recursive-graph): collapsible <details> wrapper for atlas panels"
```

---

## Task 9: TapTap 跨平台分支

**Files:**
- Modify: `ui/services/app_services.py::load_videos_for_node`
- Test: `tests/test_recursive_runs.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_recursive_runs.py`:

```python
def test_load_videos_for_node_taptap_returns_reviews(tmp_path, monkeypatch):
    from ui.services import app_services

    c_dir = tmp_path / "community_platforms" / "taptap" / "comments"
    c_dir.mkdir(parents=True)
    (c_dir / "2026-04-27_reviews.csv").write_text(
        "platform,review_id,author,star,playtime_minutes,content,snapshot_date\n"
        "taptap,r1,player1,4,300,\"非常硬核\",2026-04-27\n"
        "taptap,r2,player2,2,90,\"画面一般\",2026-04-27\n",
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    run = {"platform": "taptap"}
    node = {
        "keyword": "三国",
        "started_at": "2026-04-27T10:00:00",
        "crawl_metrics": {"comments": 2},
    }

    rows = app_services.load_videos_for_node(run, node)

    assert len(rows) == 2
    assert rows[0]["title"] in {"player1", "player2"}  # author becomes title
    assert "playtime" in rows[0]["meta"] or "★" in rows[0]["meta"]
```

- [ ] **Step 2: Run failing test**

```bash
python -m pytest tests/test_recursive_runs.py -k taptap_returns_reviews -v
```
Expected: FAIL (currently returns [])

- [ ] **Step 3: Update `load_videos_for_node` to dispatch TapTap**

In `ui/services/app_services.py`, modify `load_videos_for_node` — add at the very top:

```python
def load_videos_for_node(run: dict, node: dict, limit: int = 20) -> list[dict]:
    platform = run.get("platform", "")
    if platform == "taptap":
        return _load_reviews_for_node_taptap(node, limit)
    crawl = node.get("crawl_metrics", {}) or {}
    # ... rest unchanged
```

Then add the helper above it:

```python
def _load_reviews_for_node_taptap(node: dict, limit: int) -> list[dict]:
    c_dir = DATA_DIR / "community_platforms" / "taptap" / "comments"
    if not c_dir.exists():
        return []
    target_date = (node.get("started_at") or "")[:10]
    rows: list[dict] = []
    for csv_file in sorted(c_dir.glob("*.csv")):
        try:
            with open(csv_file, encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                for raw in reader:
                    if target_date and raw.get("snapshot_date") != target_date:
                        continue
                    star = raw.get("star", "")
                    playtime = raw.get("playtime_minutes", "")
                    rows.append({
                        "title": raw.get("author") or "—",
                        "author": raw.get("content", "")[:40],
                        "view_count": "",
                        "meta": f"★ {star} · playtime {playtime}min",
                        "publish_date": raw.get("snapshot_date", ""),
                        "url": raw.get("url", ""),
                        "fallback": True,
                    })
                    if len(rows) >= limit:
                        return rows
        except Exception:
            continue
    return rows
```

- [ ] **Step 4: Run all `load_videos_for_node` tests**

```bash
python -m pytest tests/test_recursive_runs.py -k load_videos_for_node -v
```
Expected: PASS (4 tests including new taptap)

- [ ] **Step 5: Commit**

```bash
git add ui/services/app_services.py tests/test_recursive_runs.py
git commit -m "feat(services): TapTap branch returns review rows for node detail"
```

---

## Task 10: 集成到 `render_recursive_crawl_page`

**Files:**
- Modify: `ui/pages/recursive_crawl.py:903-1062` (the `render_recursive_crawl_page` body and imports)

- [ ] **Step 1: Update imports at top of file**

Add to the existing import block (around line 9):

```python
from ui.components.recursive_graph import (
    render_graph_scene,
    render_node_detail,
    render_panels_collapsible,
    url_with,
)
from ui.services.app_services import load_videos_for_node, read_video_id_set
```

(Note: `read_video_id_set` was added in Task 3 — keep both imports together.)

- [ ] **Step 2: Replace the tail of `render_recursive_crawl_page`**

Replace the block from `run = st.session_state.get("recursive_last_run")` to the end of the function (originally lines 958–1062) with this version. The popovers (lines 926–956) stay untouched.

```python
    # ---- Bind to most recent run (incl. running) ----
    runs = list_recursive_runs()
    run = runs[0] if runs else None
    candidates = collect_candidates_from_run(run) if run else []
    summary = run.get("summary", {}) if run else {}
    rounds = run.get("rounds", []) if run else []
    nodes = run.get("nodes", []) if run else []
    status = run.get("status", "waiting") if run else "waiting"

    # ---- Resolve query state ----
    query = dict(st.query_params)
    selected_node_id = query.get("recursive_node") or (nodes[-1]["node_id"] if nodes else None)
    if selected_node_id and not any(n.get("node_id") == selected_node_id for n in nodes):
        selected_node_id = nodes[-1]["node_id"] if nodes else None
    panels_collapsed = query.get("recursive_panels") == "closed"

    # ---- Center graph ----
    scene_html = render_graph_scene(run or {}, selected_node_id=selected_node_id, query=query)

    # ---- Right-side panel (single block, replaces 4 drawers) ----
    if run and selected_node_id:
        selected_node = next(n for n in nodes if n.get("node_id") == selected_node_id)
        videos = load_videos_for_node(run, selected_node, limit=20)
        right_panel_html = render_node_detail(selected_node, videos)
    else:
        right_panel_html = ""

    # ---- Bottom-left three panel cards (collapsible wrapper) ----
    seed_preview = list(keyword_runtime.get("keywords", initial_keywords))[:18]
    node_rows = [
        (
            f"R{node.get('round')} · {node.get('keyword', '')}",
            f"{node.get('status', '')} · {node.get('candidate_metrics', {}).get('count', 0)}",
        )
        for node in nodes[:12]
    ]
    seed_body = atlas_chips(seed_preview) if seed_preview else atlas_empty(t("recursive.step_seed"), t("common.empty_first_action"))
    tree_body = render_atlas_list_editor(
        t('recursive.panel.tree'),
        node_rows,
        compact=True,
        empty_title=t('recursive.panel.no_tree'),
        empty_body=t("common.empty_first_action"),
    )
    panels = [
        render_atlas_panel(
            t('recursive.panel.state'),
            atlas_rows([
                (t('nav.mode'), t('label.expert') if is_expert else t('label.simple')),
                (t('crawl.row.platform'), PLATFORM_OPTIONS.get(config.get("platform"), config.get("platform", "bilibili"))),
                (t('crawl.row.status'), status),
            ], compact=True),
            kicker=t('crawl.kicker.route'),
        ),
        render_atlas_panel(t('recursive.panel.seeds'), seed_body, kicker=t('recursive.metric.seeds')),
        render_atlas_panel(t('recursive.panel.tree'), tree_body, kicker=t('recursive.metric.nodes')),
    ]
    panels_inner_html = "".join(
        f"<article class='atlas-shell-panel {p.get('tone', '')}'>"
        f"<div class='atlas-shell-panel-kicker'>{p['kicker']}</div>"
        f"<h3>{p['title']}</h3>"
        f"<div class='atlas-shell-panel-body'>{p['body']}</div>"
        f"</article>"
        for p in panels
    )
    toggle_url = url_with(query, recursive_panels=("open" if panels_collapsed else "closed"))
    panels_wrap_html = render_panels_collapsible(
        panels_html=panels_inner_html,
        collapsed=panels_collapsed,
        toggle_url=toggle_url,
    )

    # ---- Render the full atlas-shell-stage manually (so we can inject scene + replace drawers) ----
    metrics = [
        (t('recursive.metric.seeds'), str(len(keyword_runtime.get("keywords", initial_keywords)))),
        (t('recursive.metric.mode'), t('label.expert') if is_expert else t('label.simple')),
        (t('recursive.metric.rounds'), str(len(rounds))),
        (t('recursive.metric.nodes'), str(len(nodes))),
    ]
    metrics_html = "".join(
        f"<div class='atlas-shell-display-row'><span>{label}</span><b>{value}</b></div>"
        for label, value in metrics
    )
    stage_html = (
        "<div class='atlas-shell-stage atlas-shell-recursive' style='--atlas-accent:#9B7FD4;'>"
        f"<div class='atlas-shell-scene'>{scene_html}</div>"
        "<div class='atlas-shell-vignette'></div>"
        "<header class='atlas-shell-hero'>"
        "<div class='atlas-shell-kicker'>SLG SENTINEL · "
        f"{t('recursive.stage.mode')}</div>"
        f"<h1>{t('recursive.stage.title')}</h1>"
        "<div class='atlas-shell-title-line'></div>"
        f"<p>{t('recursive.subtitle')}</p>"
        "</header>"
        f"<aside class='atlas-shell-display'><div class='atlas-shell-display-title'>{t('stage.display')}</div>{metrics_html}</aside>"
        f"{panels_wrap_html}"
        f"<div class='atlas-shell-drawers'>{right_panel_html}</div>"
        "<footer class='atlas-shell-timeline'>"
        "<div class='atlas-shell-play'>▶</div>"
        "<div class='atlas-shell-era'>"
        f"<span>{t('recursive.stage.mode')}</span>"
        f"<strong>{t('recursive.stage.timeline')}</strong>"
        "</div>"
        "</footer>"
        "</div>"
    )
    st.markdown(stage_html, unsafe_allow_html=True)
```

- [ ] **Step 3: Manual smoke test**

```bash
source venv/bin/activate
streamlit run app.py
```

Open browser, navigate to Recursive 页面.
Expected:
- 中心区显示空态卡片或最近一次 run 的递归图
- 点击节点后 URL 变为 `?recursive_node=...`，右侧面板切换内容
- 点击左下角 ▾ 折叠三张报表卡

- [ ] **Step 4: Commit**

```bash
git add ui/pages/recursive_crawl.py
git commit -m "feat(recursive): wire graph scene + node detail + collapsible panels into page"
```

---

## Task 11: CSS

**Files:**
- Modify: `app.py` (append to existing CSS block; insert before the `@media` queries around line 2110)

- [ ] **Step 1: Append CSS block**

Insert after `.atlas-stage-map text {...}` block (around line 2013) and before the `@media` query (around line 2113):

```css
/* ===== Recursive Graph (center scene) ===== */
.recursive-graph {
    position: absolute;
    inset: 60px 380px 60px 24px;
    overflow: auto;
    z-index: 3;
}
.recursive-graph-empty {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 8px;
    color: rgba(232,228,220,.4);
    font-size: 13px;
    text-align: center;
}
.recursive-graph-empty strong {
    font-family: var(--wa-font-display);
    font-size: 18px;
    color: rgba(232,228,220,.7);
    letter-spacing: 2px;
}
.recursive-graph-edges {
    position: absolute;
    top: 0; left: 0;
    z-index: 1;
    pointer-events: none;
}
.recursive-graph-edge {
    fill: none;
    stroke: rgba(232,228,220,.32);
    stroke-width: 1.4;
    opacity: .6;
}
.recursive-graph-edge.is-success { stroke: #5B9A6E; }
.recursive-graph-edge.is-running { stroke: #6B8BDB; }
.recursive-graph-edge.is-paused  { stroke: #D4956B; }
.recursive-graph-edge.is-error   { stroke: #E85D4A; }
.recursive-graph-cols {
    position: relative;
    z-index: 2;
}
.recursive-graph-col-head {
    position: absolute;
    top: 0;
    width: 220px;
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.6px;
    color: rgba(232,228,220,.4);
    text-transform: uppercase;
    text-align: center;
    line-height: 32px;
}
.recursive-graph-node {
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 10px;
    border: 1px solid rgba(180,160,120,.18);
    border-left-width: 4px;
    border-radius: 6px;
    background: rgba(12,15,20,.82);
    color: rgba(232,228,220,.8);
    text-decoration: none !important;
    box-shadow: 0 8px 22px rgba(0,0,0,.36), inset 0 1px 0 rgba(255,255,255,.03);
    opacity: .85;
    transition: opacity .12s ease, box-shadow .12s ease;
}
.recursive-graph-node:hover { opacity: 1; }
.recursive-graph-node.is-success { border-left-color: #5B9A6E; }
.recursive-graph-node.is-running { border-left-color: #6B8BDB; }
.recursive-graph-node.is-paused  { border-left-color: #D4956B; }
.recursive-graph-node.is-error   { border-left-color: #E85D4A; }
.recursive-graph-node.is-selected {
    outline: 2px solid #d4af37;
    outline-offset: -2px;
    box-shadow: 0 0 0 4px rgba(212,175,55,.14), 0 8px 22px rgba(0,0,0,.4);
    opacity: 1;
}
.recursive-graph-node .node-keyword {
    font-family: var(--wa-font-display);
    font-size: 14px;
    font-weight: 700;
    letter-spacing: .4px;
    color: #e8e4dc;
    line-height: 1.2;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
.recursive-graph-node .node-metric {
    font-family: var(--wa-font-mono);
    font-size: 11px;
    color: rgba(232,228,220,.55);
}
.recursive-graph-node .node-extras {
    font-family: var(--wa-font-mono);
    font-size: 10px;
    color: var(--atlas-accent);
}
.recursive-graph-node .node-status-dot { display: none; }

/* ===== Right-side node detail panel ===== */
.atlas-shell-recursive .atlas-shell-drawers {
    display: block;
    padding: 0;
    background: transparent;
    border: 0;
    box-shadow: none;
    width: 360px;
    height: calc(100% - 200px);
}
.recursive-node-detail {
    display: flex;
    flex-direction: column;
    height: 100%;
    border: 1px solid rgba(180,160,120,.15);
    border-left-width: 4px;
    border-radius: 8px;
    background: rgba(12,15,20,.84);
    box-shadow: 0 16px 44px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter: blur(16px);
    overflow: hidden;
}
.recursive-node-detail[data-status="success"] { border-left-color: #5B9A6E; }
.recursive-node-detail[data-status="running"] { border-left-color: #6B8BDB; }
.recursive-node-detail[data-status="paused"]  { border-left-color: #D4956B; }
.recursive-node-detail[data-status="error"]   { border-left-color: #E85D4A; }
.recursive-node-detail header {
    padding: 14px 16px 10px;
    border-bottom: 1px solid rgba(180,160,120,.1);
}
.recursive-node-detail .kicker {
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.4px;
    color: rgba(232,228,220,.4);
    text-transform: uppercase;
    margin-bottom: 4px;
}
.recursive-node-detail h3 {
    margin: 0;
    color: #e8e4dc;
    font-family: var(--wa-font-display);
    font-size: 18px;
    letter-spacing: 1.2px;
    word-break: break-word;
}
.recursive-node-detail section {
    flex: 1 1 50%;
    display: flex;
    flex-direction: column;
    min-height: 0;
    border-bottom: 1px solid rgba(180,160,120,.08);
}
.recursive-node-detail section:last-child { border-bottom: 0; }
.recursive-node-detail .section-title {
    padding: 10px 16px 6px;
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.4px;
    color: rgba(232,228,220,.4);
    text-transform: uppercase;
}
.recursive-node-detail ul {
    list-style: none;
    margin: 0;
    padding: 0 8px 8px;
    overflow-y: auto;
    flex: 1;
}
.recursive-node-detail .videos li {
    border-bottom: 1px solid rgba(180,160,120,.06);
}
.recursive-node-detail .videos li a {
    display: block;
    padding: 8px 10px;
    color: rgba(232,228,220,.85);
    text-decoration: none;
}
.recursive-node-detail .videos .title {
    font-size: 12px;
    font-weight: 600;
    line-height: 1.35;
    margin-bottom: 4px;
}
.recursive-node-detail .videos .meta {
    font-family: var(--wa-font-mono);
    font-size: 10px;
    color: rgba(232,228,220,.45);
}
.recursive-node-detail .candidates li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 10px;
    border-bottom: 1px solid rgba(180,160,120,.06);
    font-size: 12px;
}
.recursive-node-detail .candidates li b {
    color: var(--atlas-accent);
    font-family: var(--wa-font-mono);
    font-weight: 500;
}
.recursive-detail-empty {
    padding: 12px 16px;
    color: rgba(232,228,220,.35);
    font-size: 11px;
    font-style: italic;
}
.recursive-detail-hint {
    padding: 4px 16px;
    color: #D4956B;
    font-family: var(--wa-font-mono);
    font-size: 10px;
}
.recursive-detail-more {
    padding: 6px 16px;
    color: var(--atlas-accent);
    font-size: 10px;
    text-align: right;
}

/* ===== Collapsible bottom-left panels ===== */
.atlas-shell-panels-wrap {
    position: absolute;
    z-index: 4;
    left: 22px;
    bottom: 54px;
    width: min(840px, calc(100% - 500px));
    border: 1px solid rgba(180,160,120,.14);
    border-radius: 8px;
    background: rgba(12,15,20,.78);
    box-shadow: 0 16px 44px rgba(0,0,0,.30);
    backdrop-filter: blur(14px);
    overflow: hidden;
}
.atlas-shell-recursive .atlas-shell-panels {
    position: static;
    width: 100%;
    box-shadow: none;
    background: transparent;
    border: 0;
    padding: 10px;
}
.atlas-shell-panels-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 32px;
    padding: 0 14px;
    cursor: pointer;
    color: rgba(232,228,220,.66);
    font-family: var(--wa-font-mono);
    font-size: 11px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    list-style: none;
}
.atlas-shell-panels-summary::-webkit-details-marker { display: none; }
.atlas-shell-panels-summary .collapse-toggle {
    color: var(--atlas-accent);
    text-decoration: none;
    font-size: 14px;
    line-height: 1;
}
```

- [ ] **Step 2: Manual smoke test**

```bash
streamlit run app.py
```

Verify visually on the recursive page:
- 节点状态色：绿/蓝/橙/红
- 选中节点金色 outline
- 右侧面板上下两区
- 折叠交互流畅

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "style(recursive): War Atlas-tinted graph + node detail + collapsible panels"
```

---

## Task 12: 边界场景验证

**Files:**
- 仅手动验证 + 必要时补 unit test

- [ ] **Step 1: 验证「无 run」场景**

清空（或重命名）`data/recursive_runs/`，重启 streamlit。
Expected: 中心显示"暂无递归任务"卡片；右侧面板不渲染；左下角三张卡仍显示。

- [ ] **Step 2: 验证「running 状态」**

启动一次 AI 话题探索（点击侧边 `候选话题` popover 里的"启动 AI 话题探索"）。在它跑的过程中刷新页面。
Expected: 当前正在执行的节点蓝色边框；其他节点状态色正确；右侧面板默认选中最后一个节点。

- [ ] **Step 3: 验证「URL 中 node_id 不存在」**

手动编辑浏览器 URL 加 `?recursive_node=does-not-exist`，Enter。
Expected: 静默回退到默认节点；URL 不被自动清理；下次点击其他节点时正常覆盖。

- [ ] **Step 4: 验证「TapTap 平台」**

在配置 popover 选 TapTap 平台启动一次探索（如有种子），刷新后查看右侧面板。
Expected: 视频列表区显示 TapTap 评论行（用户名 + 星级 + 游玩时长）。

- [ ] **Step 5: 验证「旧 run fallback」**

在 `data/recursive_runs/` 找一个旧 run JSON，确认其 `node.crawl_metrics.video_ids` 缺失。打开页面切到该 run（通过历史 popover 或暂时把它改为最新 run）。
Expected: 视频列表显示按 `snapshot_date` 估算的结果，附"数据为旧版 run 估算结果"米色提示。

- [ ] **Step 6: 验证「折叠持久化」**

折叠左下角三张卡 → 刷新页面。
Expected: 折叠状态保留；URL 含 `recursive_panels=closed`。

- [ ] **Step 7: 验证「跑全套测试」**

```bash
python -m pytest tests/ -v
```
Expected: 全绿。

- [ ] **Step 8: 提交（如有补丁）**

如有任何 bug 修复：

```bash
git add -p
git commit -m "fix(recursive): <具体修复>"
```

---

## 完成标准

- [ ] 全部 12 个 Task 都已 commit
- [ ] `python -m pytest tests/ -v` 全绿
- [ ] 手动验证 7 项场景都通过
- [ ] CSV 数据契约：新 run 在 `node.crawl_metrics.video_ids` 中持久化新增 video_id 列表；旧 run 不动
- [ ] 没有引入 `<script>` 标签或 `st.components.v1.html`，全部由 `st.markdown(unsafe_allow_html=True)` 渲染

