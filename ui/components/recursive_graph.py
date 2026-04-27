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
