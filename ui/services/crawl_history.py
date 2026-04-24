"""
SLG Sentinel — 采集任务历史追溯

为每次采集生成 JSON 记录，支持历史查询和采集日历。
"""
from __future__ import annotations
import json, logging, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
HISTORY_DIR = Path(__file__).resolve().parents[2] / "data" / "crawl_history"

@dataclass
class CrawlRecord:
    record_id: str = ""
    platform: str = ""
    mode: str = ""
    depth: str = ""
    order: str = ""
    limit: int = 0
    keyword_count: int = 0
    started_at: str = ""
    finished_at: str = ""
    status: str = ""  # success / failed / partial
    videos_added: int = 0
    comments_added: int = 0
    files_touched: list[str] = field(default_factory=list)
    error_log: str = ""

def create_crawl_record(platform: str, mode: str, depth: str, order: str, limit: int, keyword_count: int) -> CrawlRecord:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rid = f"{ts}_{platform}_{uuid.uuid4().hex[:6]}"
    return CrawlRecord(record_id=rid, platform=platform, mode=mode, depth=depth,
                       order=order, limit=limit, keyword_count=keyword_count,
                       started_at=datetime.now().isoformat(timespec="seconds"))

def save_crawl_record(record: CrawlRecord) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    record.finished_at = datetime.now().isoformat(timespec="seconds")
    path = HISTORY_DIR / f"{record.record_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(record), f, ensure_ascii=False, indent=2)
    logger.info(f"采集记录已保存: {path}")
    return path

def load_crawl_records(platform: str | None = None, limit: int = 50) -> list[dict]:
    if not HISTORY_DIR.exists(): return []
    records = []
    for f in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if platform and data.get("platform") != platform: continue
                records.append(data)
                if len(records) >= limit: break
        except Exception: continue
    return records

def get_crawl_calendar(days: int = 30) -> dict[str, int]:
    """返回近 N 天每天的采集次数 {date_str: count}"""
    records = load_crawl_records(limit=500)
    calendar: dict[str, int] = {}
    for r in records:
        date = r.get("started_at", "")[:10]
        if date: calendar[date] = calendar.get(date, 0) + 1
    return calendar
