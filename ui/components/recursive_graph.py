"""Recursive crawl graph rendering — pure HTML/SVG, no JS."""
from __future__ import annotations

from html import escape as _escape
from urllib.parse import quote


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
        try:
            score = float((node.get("crawl_metrics", {}) or {}).get("score", 0) or 0)
        except (TypeError, ValueError):
            score = 0.0
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
