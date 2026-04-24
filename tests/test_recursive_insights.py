from ui.services.recursive_insights import (
    build_exploration_summary,
    business_progress_events,
    classify_topic_candidate,
    group_topic_candidates,
    is_generic_topic,
)


def test_topic_candidate_grouping_rules():
    candidates = [
        {"keyword": "赛季开荒阵容", "score": 180, "sources": "标题"},
        {"keyword": "手游", "score": 120, "sources": "标签"},
        {"keyword": "平民配将", "score": 35, "sources": "评论"},
        {"keyword": "x", "score": 4, "sources": "标题"},
    ]

    grouped = group_topic_candidates(candidates)

    assert grouped["strong"][0]["keyword"] == "赛季开荒阵容"
    assert grouped["review"][0]["keyword"] == "手游"
    assert grouped["long_tail"][0]["keyword"] == "平民配将"
    assert grouped["weak"][0]["keyword"] == "x"


def test_capped_search_topic_needs_review():
    candidate = {
        "keyword": "开荒攻略",
        "score": 120,
        "search_metrics": {"total_results_display": ">=1000", "is_capped": True},
    }

    assert classify_topic_candidate(candidate) == "review"


def test_generic_topic_detection():
    assert is_generic_topic("手游") is True
    assert is_generic_topic("赛季开荒阵容") is False


def test_exploration_summary_aggregates_run_metrics():
    run = {
        "status": "success",
        "seed_keywords": ["三国"],
        "summary": {"total_videos": 12, "total_comments": 34},
        "nodes": [
            {
                "keyword": "三国",
                "status": "success",
                "candidate_metrics": {
                    "candidates": [
                        {"keyword": "赛季开荒阵容", "score": 180},
                        {"keyword": "平民配将", "score": 35},
                    ]
                },
            },
            {"keyword": "手游", "status": "paused", "stop_reason": "B站搜索量无法获取", "candidate_metrics": {"candidates": []}},
        ],
    }

    summary = build_exploration_summary(run)

    assert summary["total_videos"] == 12
    assert summary["total_comments"] == 34
    assert summary["discovered_topics"] == 2
    assert summary["recommended_topics"] == 1
    assert summary["abnormal_count"] == 1
    assert summary["next_action"] == "建议优先推进强推荐话题"


def test_business_progress_events_are_readable():
    run = {
        "nodes": [
            {
                "round": 1,
                "keyword": "三国",
                "search_metrics": {"total_results_display": ">=1000"},
                "crawl_metrics": {"videos": 10},
                "candidate_metrics": {"count": 3},
            }
        ]
    }

    events = business_progress_events(run)

    assert "探索「三国」" in events[0]
    assert "发现新话题 3 个" in events[0]
