"""
SLG Sentinel — 候选词挖掘服务
从采集数据中提取关键词候选列表。拆分自 app_services.py。
"""
from __future__ import annotations
import csv, math, re, sys
from pathlib import Path
from ui.services.app_services import DATA_DIR, KEYWORD_STOPWORDS

def _get_platform_data_dirs(platform: str) -> tuple[Path, Path]:
    from src.core.csv_store import COMMUNITY_PLATFORMS, VIDEO_PLATFORMS
    if platform in VIDEO_PLATFORMS: category = "video_platforms"
    elif platform in COMMUNITY_PLATFORMS: category = "community_platforms"
    else: category = "misc_platforms"
    base_dir = DATA_DIR / category / platform
    return base_dir / "videos", base_dir / "comments"

def _read_recent_csv_rows(paths: list[Path], max_files: int, max_rows: int) -> list[dict]:
    rows: list[dict] = []
    recent_paths = sorted((p for p in paths if p.exists()), key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]
    for csv_path in recent_paths:
        try:
            with open(csv_path, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    row["_source_file"] = str(csv_path)
                    rows.append(row)
                    if len(rows) >= max_rows: return rows
        except Exception: continue
    return rows

def _tokenize_keyword_text(text: str) -> list[str]:
    normalized = re.sub(r"https?://\S+", " ", str(text or ""))
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", normalized)
    try:
        import jieba
        raw_tokens = list(jieba.cut(normalized))
    except Exception:
        raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,24}|[\u4e00-\u9fff]{2,12}", normalized)
    tokens = []
    for raw_token in raw_tokens:
        token = str(raw_token).strip().lower()
        token = re.sub(r"^\d+|\d+$", "", token)
        if not token or len(token) < 2 or len(token) > 18: continue
        if token.isdigit() or token in KEYWORD_STOPWORDS: continue
        tokens.append(token)
    return tokens

def extract_keywords_from_crawl_data(
    platform: str, existing_keywords: list[str],
    max_keywords: int = 24, min_score: float = 2.0,
    max_files: int = 8, max_rows: int = 1200,
) -> dict:
    videos_dir, comments_dir = _get_platform_data_dirs(platform)
    video_rows = _read_recent_csv_rows(list(videos_dir.glob("*.csv")) if videos_dir.exists() else [], max_files, max_rows)
    comment_rows = _read_recent_csv_rows(list(comments_dir.glob("*.csv")) if comments_dir.exists() else [], max_files, max_rows)
    existing = {kw.strip().lower() for kw in existing_keywords if str(kw).strip()}
    scores: dict[str, dict] = {}

    def add_token(token, weight, source, evidence):
        if token in existing: return
        if token not in scores:
            scores[token] = {"keyword": token, "score": 0.0, "frequency": 0, "sources": set(), "evidence": set(), "source_scores": {"标题": 0.0, "标签": 0.0, "高赞评论": 0.0}}
        scores[token]["score"] += weight
        scores[token]["frequency"] += 1
        scores[token]["sources"].add(source)
        scores[token]["source_scores"][source] = scores[token]["source_scores"].get(source, 0.0) + weight
        if evidence: scores[token]["evidence"].add(evidence[:42])

    for row in video_rows:
        eng = 1.0
        try: eng += min(math.log10(max(int(row.get("view_count", 0)), 1)), 6) / 5
        except Exception: pass
        for t in _tokenize_keyword_text(row.get("title", "")): add_token(t, 2.2 * eng, "标题", row.get("title", ""))
        for tag in re.split(r"[,，/、\s]+", str(row.get("tags", ""))):
            for t in _tokenize_keyword_text(tag.strip()): add_token(t, 2.8 * eng, "标签", tag.strip())

    for row in comment_rows:
        lb = 1.0
        try: lb += min(math.log10(max(int(row.get("like_count", 0)), 1)), 4) / 4
        except Exception: pass
        for t in _tokenize_keyword_text(row.get("content", "")): add_token(t, 1.25 * lb, "高赞评论", row.get("content", ""))

    candidates = []
    for item in scores.values():
        if item["score"] < min_score: continue
        ss = item["source_scores"]
        ts, tgs, cs = round(ss.get("标题",0),2), round(ss.get("标签",0),2), round(ss.get("高赞评论",0),2)
        srcs = sorted(item["sources"])
        candidates.append({
            "keyword": item["keyword"], "score": round(item["score"],2), "frequency": item["frequency"],
            "title_score": ts, "tag_score": tgs, "comment_score": cs, "sources": " / ".join(srcs),
            "formula": f"标题 {ts} + 标签 {tgs} + 高赞评论 {cs}",
            "reason": f"来自{'、'.join(srcs)}，可作为下一轮搜索触点",
            "evidence": "；".join(sorted(item["evidence"])[:2]),
        })
    candidates.sort(key=lambda x: (x["score"], x["frequency"]), reverse=True)
    return {"candidates": candidates[:max_keywords], "video_rows": len(video_rows), "comment_rows": len(comment_rows), "used_jieba": "jieba" in sys.modules}
