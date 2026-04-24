from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from ui.services.app_services import DATA_DIR, ROOT

RUN_STATUSES = {"running", "paused", "success", "stopped", "error"}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_recursive_runs_dir(data_dir: Path | None = None) -> Path:
    return (data_dir or DATA_DIR) / "recursive_runs"


def generate_run_id(platform: str) -> str:
    safe_platform = re.sub(r"[^a-zA-Z0-9_-]+", "_", platform).strip("_") or "platform"
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_platform}_{uuid4().hex[:8]}"


def get_run_path(run_id: str, data_dir: Path | None = None) -> Path:
    return get_recursive_runs_dir(data_dir) / f"{run_id}.json"


def save_recursive_run(run: dict, data_dir: Path | None = None) -> Path:
    if run.get("status") not in RUN_STATUSES:
        raise ValueError(f"invalid recursive run status: {run.get('status')}")

    run_dir = get_recursive_runs_dir(data_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    run["updated_at"] = now_iso()
    path = get_run_path(run["run_id"], data_dir)
    path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def create_recursive_run(config: dict, seed_keywords: list[str], data_dir: Path | None = None) -> dict:
    run = {
        "run_id": generate_run_id(config.get("platform", "platform")),
        "status": "running",
        "platform": config.get("platform", ""),
        "created_at": now_iso(),
        "started_at": now_iso(),
        "ended_at": "",
        "updated_at": "",
        "config": dict(config),
        "seed_keywords": list(seed_keywords),
        "rounds": [],
        "nodes": [],
        "edges": [],
        "events": [],
        "output_files": [],
        "pending_queue": [],
        "paused_node_id": "",
        "summary": {
            "total_nodes": 0,
            "success_nodes": 0,
            "paused_nodes": 0,
            "error_nodes": 0,
            "total_videos": 0,
            "total_comments": 0,
        },
    }
    save_recursive_run(run, data_dir)
    return run


def load_recursive_run(run_id: str, data_dir: Path | None = None) -> dict | None:
    path = get_run_path(run_id, data_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_recursive_runs(
    data_dir: Path | None = None,
    platform: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    run_dir = get_recursive_runs_dir(data_dir)
    if not run_dir.exists():
        return []

    keyword_norm = (keyword or "").strip().lower()
    runs = []
    for path in sorted(run_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if platform and run.get("platform") != platform:
            continue
        if status and run.get("status") != status:
            continue
        run_date = str(run.get("started_at") or run.get("created_at") or "")[:10]
        if date_from and run_date and run_date < date_from:
            continue
        if date_to and run_date and run_date > date_to:
            continue
        if keyword_norm:
            haystack = " ".join(
                [str(item) for item in run.get("seed_keywords", [])]
                + [str(node.get("keyword", "")) for node in run.get("nodes", [])]
            ).lower()
            if keyword_norm not in haystack:
                continue
        runs.append(run)
    return runs


def append_run_event(run: dict, event_type: str, message: str, payload: dict | None = None) -> None:
    run.setdefault("events", []).append(
        {
            "time": now_iso(),
            "type": event_type,
            "message": message,
            "payload": payload or {},
        }
    )


def append_round(run: dict, round_index: int, keywords: list[str]) -> None:
    run.setdefault("rounds", []).append(
        {
            "round": round_index,
            "keywords": list(keywords),
            "started_at": now_iso(),
            "ended_at": "",
            "status": "running",
        }
    )


def finish_latest_round(run: dict, status: str, stop_reason: str = "") -> None:
    if not run.get("rounds"):
        return
    run["rounds"][-1]["status"] = status
    run["rounds"][-1]["stop_reason"] = stop_reason
    run["rounds"][-1]["ended_at"] = now_iso()


def make_node_id(round_index: int, keyword: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff_-]+", "_", keyword).strip("_")[:24] or "keyword"
    return f"r{round_index}_{slug}_{uuid4().hex[:6]}"


def append_keyword_node(run: dict, keyword: str, parent_id: str | None, round_index: int) -> dict:
    node = {
        "node_id": make_node_id(round_index, keyword),
        "keyword": keyword,
        "parent_id": parent_id or "",
        "round": round_index,
        "status": "running",
        "search_metrics": {},
        "crawl_metrics": {"videos": 0, "comments": 0, "touched_files": []},
        "candidate_metrics": {"count": 0, "top_score": 0, "candidates": []},
        "evidence": [],
        "stop_reason": "",
        "started_at": now_iso(),
        "ended_at": "",
    }
    run.setdefault("nodes", []).append(node)
    if parent_id:
        run.setdefault("edges", []).append({"from": parent_id, "to": node["node_id"], "keyword": keyword})
    recalculate_summary(run)
    return node


def update_keyword_node(run: dict, node_id: str, **updates) -> dict:
    for node in run.get("nodes", []):
        if node.get("node_id") == node_id:
            node.update(updates)
            if updates.get("status") and updates["status"] != "running":
                node["ended_at"] = now_iso()
            recalculate_summary(run)
            return node
    raise ValueError(f"node not found: {node_id}")


def finish_recursive_run(run: dict, status: str, stop_reason: str = "") -> None:
    if status not in RUN_STATUSES:
        raise ValueError(f"invalid recursive run status: {status}")
    run["status"] = status
    run["ended_at"] = now_iso()
    run["stop_reason"] = stop_reason
    recalculate_summary(run)


def recalculate_summary(run: dict) -> None:
    nodes = run.get("nodes", [])
    run["summary"] = {
        "total_nodes": len(nodes),
        "success_nodes": sum(1 for node in nodes if node.get("status") == "success"),
        "paused_nodes": sum(1 for node in nodes if node.get("status") == "paused"),
        "error_nodes": sum(1 for node in nodes if node.get("status") == "error"),
        "total_videos": sum(int(node.get("crawl_metrics", {}).get("videos", 0) or 0) for node in nodes),
        "total_comments": sum(int(node.get("crawl_metrics", {}).get("comments", 0) or 0) for node in nodes),
    }


def relative_output_files(touched_files: list[dict]) -> list[str]:
    files = []
    for item in touched_files:
        path = str(item.get("path", ""))
        if not path:
            continue
        try:
            files.append(str(Path(path).resolve().relative_to(ROOT)))
        except Exception:
            files.append(path)
    return files
