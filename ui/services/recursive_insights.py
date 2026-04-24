from __future__ import annotations

from collections import OrderedDict
from typing import Any


TOPIC_GROUPS = OrderedDict(
    [
        ("strong", {"label": "强推荐话题", "description": "推荐指数高，且不是过宽泛的话题，适合进入下一轮探索。"}),
        ("review", {"label": "待确认话题", "description": "有热度，但可能偏泛或搜索池封顶，建议人工看一眼证据。"}),
        ("long_tail", {"label": "长尾机会", "description": "热度不算最高，但指向更具体的内容机会。"}),
        ("weak", {"label": "不建议继续话题", "description": "信号较弱或过于泛化，继续采集的投入产出比较低。"}),
    ]
)

GENERIC_TOPIC_TERMS = {
    "游戏",
    "手游",
    "推荐",
    "攻略",
    "教程",
    "新手",
    "视频",
    "直播",
    "官方",
    "下载",
    "上线",
    "玩法",
    "活动",
    "版本",
    "玩家",
    "解说",
    "热门",
    "合集",
    "三国",
    "slg",
}


def topic_score(candidate: dict[str, Any]) -> float:
    try:
        return float(candidate.get("score", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def format_score(value: Any) -> str:
    try:
        return str(int(round(float(value or 0))))
    except (TypeError, ValueError):
        return "0"


def is_generic_topic(keyword: str) -> bool:
    normalized = str(keyword or "").strip().lower()
    if not normalized:
        return True
    if normalized in GENERIC_TOPIC_TERMS:
        return True
    if len(normalized) <= 1:
        return True
    return False


def _is_capped(candidate: dict[str, Any]) -> bool:
    search_metrics = candidate.get("search_metrics") or {}
    if isinstance(search_metrics, dict) and search_metrics.get("is_capped"):
        return True
    display = str(candidate.get("search_scale") or search_metrics.get("total_results_display") or "")
    return display.startswith(">=")


def search_scale_label(candidate: dict[str, Any]) -> str:
    search_metrics = candidate.get("search_metrics") or {}
    if isinstance(search_metrics, dict):
        display = search_metrics.get("total_results_display") or search_metrics.get("total_results")
        if display not in (None, ""):
            return str(display)
    display = candidate.get("search_scale") or candidate.get("total_results_display") or candidate.get("total_results")
    return str(display) if display not in (None, "") else "待采集"


def classify_topic_candidate(candidate: dict[str, Any]) -> str:
    keyword = str(candidate.get("keyword", "")).strip()
    score = topic_score(candidate)
    generic = is_generic_topic(keyword)
    capped = _is_capped(candidate)

    if score >= 80 and not generic and not capped:
        return "strong"
    if score >= 50 and (generic or capped):
        return "review"
    if score >= 12 and not generic:
        return "long_tail"
    return "weak"


def group_topic_candidates(candidates: list[dict[str, Any]], limit_per_group: int = 5) -> dict[str, list[dict[str, Any]]]:
    groups = {key: [] for key in TOPIC_GROUPS}
    seen: set[str] = set()
    for candidate in sorted(candidates, key=topic_score, reverse=True):
        keyword = str(candidate.get("keyword", "")).strip()
        if not keyword or keyword.lower() in seen:
            continue
        seen.add(keyword.lower())
        group_key = classify_topic_candidate(candidate)
        groups[group_key].append(candidate)

    return {key: value[:limit_per_group] for key, value in groups.items()}


def collect_candidates_from_run(run: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for node in run.get("nodes", []) or []:
        node_candidates = (node.get("candidate_metrics") or {}).get("candidates", []) or []
        for candidate in node_candidates:
            item = dict(candidate)
            item.setdefault("parent_keyword", node.get("keyword", ""))
            item.setdefault("parent_node_id", node.get("node_id", ""))
            item.setdefault("round", node.get("round", 0))
            candidates.append(item)
    return candidates


def build_exploration_summary(run: dict[str, Any], candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    summary = run.get("summary", {}) or {}
    candidates = candidates if candidates is not None else collect_candidates_from_run(run)
    grouped = group_topic_candidates(candidates)
    abnormal_nodes = [
        node
        for node in run.get("nodes", []) or []
        if node.get("status") in {"paused", "error"} or bool(node.get("stop_reason"))
    ]
    total_topics = len({str(item.get("keyword", "")).strip().lower() for item in candidates if item.get("keyword")})
    recommended_count = len(grouped["strong"])
    status = run.get("status", "")
    if status in {"paused", "error"}:
        next_action = "需要专家处理异常后再继续"
    elif recommended_count > 0:
        next_action = "建议优先推进强推荐话题"
    elif grouped["long_tail"]:
        next_action = "可小规模验证长尾机会"
    else:
        next_action = "本轮信号偏弱，建议换起始话题或放宽策略"

    return {
        "seed_keywords": run.get("seed_keywords", []),
        "status": status,
        "started_at": run.get("started_at") or run.get("created_at", ""),
        "ended_at": run.get("ended_at", ""),
        "total_videos": int(summary.get("total_videos", 0) or 0),
        "total_comments": int(summary.get("total_comments", 0) or 0),
        "discovered_topics": total_topics,
        "recommended_topics": recommended_count,
        "abnormal_count": len(abnormal_nodes),
        "next_action": next_action,
        "groups": grouped,
    }


def business_progress_events(run: dict[str, Any], limit: int = 12) -> list[str]:
    messages: list[str] = []
    for node in run.get("nodes", []) or []:
        keyword = node.get("keyword", "")
        search = node.get("search_metrics") or {}
        crawl = node.get("crawl_metrics") or {}
        candidate_metrics = node.get("candidate_metrics") or {}
        search_label = search.get("total_results_display") or search.get("total_results") or "未记录"
        messages.append(
            f"第 {node.get('round', 0)} 轮：探索「{keyword}」，B站搜索规模 {search_label}，采集视频 {crawl.get('videos', 0)} 条，发现新话题 {candidate_metrics.get('count', 0)} 个。"
        )
        if node.get("stop_reason"):
            messages.append(f"「{keyword}」触发暂停/停止：{node.get('stop_reason')}")

    if not messages:
        for event in run.get("events", []) or []:
            message = str(event.get("message", "")).strip()
            if message:
                messages.append(message)
    return messages[-limit:]
