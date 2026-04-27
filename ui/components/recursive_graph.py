"""Recursive crawl graph rendering — pure HTML/SVG, no JS."""
from __future__ import annotations

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
