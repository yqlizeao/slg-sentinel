"""
SLG Sentinel — 采集执行服务
提供 CLI 调用、采集进度状态机、结果汇总。拆分自 app_services.py。
"""
from __future__ import annotations
import os, re, subprocess, sys
from datetime import datetime
from pathlib import Path
from ui.services.app_services import ROOT, DATA_DIR, count_csv_rows

def run_cli(args: list[str]) -> tuple[str, str, int]:
    cmd = [sys.executable, "-m", "src.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return result.stdout, result.stderr, result.returncode

def run_cli_stream(args: list[str], on_line=None) -> tuple[str, str, int]:
    cmd = [sys.executable, "-u", "-m", "src.cli"] + args
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(ROOT), env=env, bufsize=1)
    output_lines = []
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        output_lines.append(line)
        if on_line: on_line(line)
    return_code = proc.wait()
    return "\n".join(output_lines), "", return_code

def init_crawl_progress_state(platform: str, keyword_count: int, limit_val: int) -> dict:
    return {"platform": platform, "keyword_total": max(keyword_count, 1), "keyword_done": 0, "comment_done": 0,
            "search_metric_done": 0, "search_total_latest": None, "progress": 0.03,
            "stage": "准备启动", "detail": f"预计检索 {keyword_count} 个关键词，每词上限 {limit_val} 条",
            "started_at": datetime.now()}

def update_crawl_progress_state(state: dict, line: str) -> None:
    clean = line.strip()
    if not clean: return
    state["detail"] = clean
    kw_match = re.search(r"共\s+(\d+)\s+个关键词", clean)
    if kw_match:
        state["keyword_total"] = max(int(kw_match.group(1)), 1)
        state["stage"] = "正在检索关键词"; state["progress"] = max(state["progress"], 0.10); return
    if "关键词 '" in clean and ("搜索到" in clean or "搜索失败" in clean):
        state["keyword_done"] += 1
        tm = re.search(r"搜索结果(?:总量|池)\s*(≥)?\s*(\d+)", clean)
        if tm: state["search_total_latest"] = f"{'≥' if tm.group(1) else ''}{tm.group(2)}"
        total = max(state["keyword_total"], 1)
        state["stage"] = f"正在检索关键词（{min(state['keyword_done'], total)}/{total}）"
        state["progress"] = max(state["progress"], min(0.72, 0.10 + 0.62 * (state["keyword_done"] / total))); return
    if "已记录" in clean and "关键词搜索总量" in clean:
        state["search_metric_done"] += 1; state["stage"] = "正在记录关键词搜索总量"; state["progress"] = max(state["progress"], 0.84); return
    if "TapTap 搜索 '" in clean and ("找到" in clean or "失败" in clean):
        state["keyword_done"] += 1; total = max(state["keyword_total"], 1)
        state["stage"] = f"正在检索关键词（{min(state['keyword_done'], total)}/{total}）"
        state["progress"] = max(state["progress"], min(0.72, 0.10 + 0.62 * (state["keyword_done"] / total))); return
    if "游戏 '" in clean and "采集" in clean and "条评论" in clean:
        state["keyword_done"] += 1; total = max(state["keyword_total"], 1)
        state["stage"] = f"正在采集目标内容（{min(state['keyword_done'], total)}/{total}）"
        state["progress"] = max(state["progress"], min(0.72, 0.10 + 0.62 * (state["keyword_done"] / total))); return
    if "采集频道:" in clean or ("频道 '" in clean and "获取" in clean and "条视频" in clean):
        state["stage"] = "正在补充目标内容"; state["progress"] = max(state["progress"], 0.76); return
    if "获取热门视频" in clean: state["stage"] = "正在补充热门内容"; state["progress"] = max(state["progress"], 0.80); return
    if "已保存" in clean and ("视频快照" in clean or "游戏快照" in clean):
        state["stage"] = "正在写入视频结果"; state["progress"] = max(state["progress"], 0.88); return
    if "已保存" in clean and "评论" in clean:
        state["comment_done"] += 1; state["stage"] = "正在写入评论结果"
        state["progress"] = max(state["progress"], min(0.97, 0.90 + 0.025 * state["comment_done"])); return
    if "扫码授权" in clean or "[沙盒桥接]" in clean: state["stage"] = "等待本地授权"; state["progress"] = max(state["progress"], 0.20); return
    if "[收网作业]" in clean: state["stage"] = "正在导入本地结果"; state["progress"] = max(state["progress"], 0.78); return
    if "已从 MediaCrawler 导入" in clean: state["stage"] = "正在写入采集结果"; state["progress"] = max(state["progress"], 0.96)

def estimate_remaining_seconds(progress_state: dict) -> int | None:
    progress = progress_state.get("progress", 0.0)
    if progress <= 0.08: return None
    elapsed = max((datetime.now() - progress_state["started_at"]).total_seconds(), 1.0)
    return max(int(elapsed / progress - elapsed), 0)

def get_crawl_file_snapshot(platform: str) -> dict[str, dict]:
    snapshot = {}
    if not DATA_DIR.exists(): return snapshot
    for csv_file in DATA_DIR.rglob("*.csv"):
        try:
            if platform in csv_file.parts or ("summary" in csv_file.parts and csv_file.name.endswith("_summary.csv")):
                snapshot[str(csv_file)] = {"rows": count_csv_rows(csv_file), "mtime": csv_file.stat().st_mtime}
        except Exception: continue
    return snapshot

def summarize_crawl_result(platform, platform_label, before_snapshot, after_snapshot,
                           keyword_count, limit_val, started_at, return_code, stdout, stderr) -> dict:
    touched_files, added_videos, added_comments = [], 0, 0
    for path_str, after in after_snapshot.items():
        before = before_snapshot.get(path_str, {"rows": 0, "mtime": 0.0})
        row_delta = after["rows"] - before["rows"]
        if not (before["mtime"] == 0.0 or row_delta != 0 or after["mtime"] > before["mtime"]): continue
        path_obj = Path(path_str)
        try: rel_path = str(path_obj.relative_to(ROOT))
        except Exception: rel_path = path_str
        touched_files.append({"path": rel_path, "row_delta": row_delta})
        if platform in path_obj.parts and "videos" in path_obj.parts: added_videos += max(row_delta, 0)
        if platform in path_obj.parts and "comments" in path_obj.parts: added_comments += max(row_delta, 0)
    touched_files.sort(key=lambda x: x["path"])
    return {"platform": platform, "platform_label": platform_label,
            "status": "success" if return_code == 0 else "error",
            "duration_seconds": max((datetime.now() - started_at).total_seconds(), 0.1),
            "estimated_results": keyword_count * limit_val, "keyword_count": keyword_count, "limit_val": limit_val,
            "added_videos": added_videos, "added_comments": added_comments,
            "touched_files": touched_files, "stdout": stdout, "stderr": stderr}

def media_crawler_exists() -> bool:
    return (ROOT / "MediaCrawler").exists()
