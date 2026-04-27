from ui.services.recursive_runs import (
    append_keyword_node,
    append_round,
    append_run_event,
    create_recursive_run,
    finish_recursive_run,
    list_recursive_runs,
    load_recursive_run,
    save_recursive_run,
    update_keyword_node,
)


def test_search_metrics_capped_display(tmp_path, monkeypatch):
    from ui.services import app_services

    metrics_dir = tmp_path / "search_metrics" / "bilibili"
    metrics_dir.mkdir(parents=True)
    metrics_file = metrics_dir / "2026-04-24_search_metrics.csv"
    metrics_file.write_text(
        "snapshot_date,platform,keyword,order,limit,total_results,fetched_count,pages,error,created_at\n"
        "2026-04-24,bilibili,三国,totalrank,10,1000,10,1,,2026-04-24T10:00:00\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    df = app_services.load_latest_search_metrics("bilibili")

    assert df.iloc[0]["total_results_display"] == ">=1000"
    assert bool(df.iloc[0]["is_capped"]) is True


def test_find_latest_search_metric_since(tmp_path, monkeypatch):
    from datetime import datetime
    from ui.services import app_services

    metrics_dir = tmp_path / "search_metrics" / "bilibili"
    metrics_dir.mkdir(parents=True)
    metrics_file = metrics_dir / "2026-04-24_search_metrics.csv"
    metrics_file.write_text(
        "snapshot_date,platform,keyword,order,limit,total_results,total_results_display,is_capped,num_pages,page_size,fetched_count,pages,error,created_at\n"
        "2026-04-24,bilibili,三国,totalrank,10,42,42,False,1,42,10,1,,2026-04-24T09:00:00\n"
        "2026-04-24,bilibili,三国,totalrank,10,1000,>=1000,True,24,42,10,1,,2026-04-24T11:00:00\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    metric = app_services.find_latest_search_metric("bilibili", "三国", started_at=datetime.fromisoformat("2026-04-24T10:00:00"))

    assert metric["total_results_display"] == ">=1000"


def test_search_metrics_reader_handles_mixed_legacy_and_new_rows(tmp_path, monkeypatch):
    from datetime import datetime
    from ui.services import app_services

    metrics_dir = tmp_path / "search_metrics" / "bilibili"
    metrics_dir.mkdir(parents=True)
    metrics_file = metrics_dir / "2026-04-24_search_metrics.csv"
    metrics_file.write_text(
        "snapshot_date,platform,keyword,order,limit,total_results,fetched_count,pages,error,created_at\n"
        "2026-04-24,bilibili,旧词,totalrank,10,1000,10,1,,2026-04-24T10:00:00\n"
        "2026-04-24,bilibili,三国志战略版,totalrank,10,1000,>=1000,True,24,42,10,1,,2026-04-24T23:12:21\n",
        encoding="utf-8-sig",
    )
    monkeypatch.setattr(app_services, "DATA_DIR", tmp_path)

    metric = app_services.find_latest_search_metric(
        "bilibili",
        "三国志战略版",
        started_at=datetime.fromisoformat("2026-04-24T23:12:20"),
    )
    df = app_services.load_latest_search_metrics("bilibili", limit=10)

    assert metric["total_results_display"] == ">=1000"
    assert bool(df[df["keyword"] == "旧词"].iloc[0]["is_capped"]) is True


def test_save_search_metrics_migrates_legacy_header(tmp_path, monkeypatch):
    from src.services import crawl_service

    monkeypatch.chdir(tmp_path)
    metrics_dir = tmp_path / "data" / "search_metrics" / "bilibili"
    metrics_dir.mkdir(parents=True)
    metrics_file = metrics_dir / "2026-04-24_search_metrics.csv"
    metrics_file.write_text(
        "snapshot_date,platform,keyword,order,limit,total_results,fetched_count,pages,error,created_at\n"
        "2026-04-24,bilibili,旧词,totalrank,10,42,10,1,,2026-04-24T10:00:00\n",
        encoding="utf-8-sig",
    )

    crawl_service.save_search_metrics(
        "bilibili",
        [
            {
                "keyword": "新词",
                "order": "totalrank",
                "limit": 10,
                "total_results": 1000,
                "total_results_display": ">=1000",
                "is_capped": True,
                "num_pages": 24,
                "page_size": 42,
                "fetched_count": 10,
                "pages": 1,
            }
        ],
        "2026-04-24",
    )

    lines = metrics_file.read_text(encoding="utf-8-sig").splitlines()

    assert lines[0].split(",") == crawl_service.SEARCH_METRIC_COLUMNS
    assert len(lines) == 3
    assert "新词" in lines[-1]


def test_recursive_run_create_save_load(tmp_path):
    run = create_recursive_run({"platform": "bilibili", "max_depth": 2}, ["率土之滨"], data_dir=tmp_path)

    loaded = load_recursive_run(run["run_id"], data_dir=tmp_path)

    assert loaded is not None
    assert loaded["status"] == "running"
    assert loaded["platform"] == "bilibili"
    assert loaded["seed_keywords"] == ["率土之滨"]


def test_recursive_node_parent_child_and_summary(tmp_path):
    run = create_recursive_run({"platform": "bilibili"}, ["率土之滨"], data_dir=tmp_path)
    parent = append_keyword_node(run, "率土之滨", parent_id=None, round_index=1)
    child = append_keyword_node(run, "开荒", parent_id=parent["node_id"], round_index=2)
    update_keyword_node(
        run,
        child["node_id"],
        status="success",
        crawl_metrics={"videos": 3, "comments": 1, "touched_files": []},
    )
    save_recursive_run(run, data_dir=tmp_path)

    loaded = load_recursive_run(run["run_id"], data_dir=tmp_path)

    assert loaded["edges"] == [{"from": parent["node_id"], "to": child["node_id"], "keyword": "开荒"}]
    assert loaded["summary"]["total_nodes"] == 2
    assert loaded["summary"]["success_nodes"] == 1
    assert loaded["summary"]["total_videos"] == 3


def test_recursive_run_paused_status_and_history_filter(tmp_path):
    run = create_recursive_run({"platform": "bilibili"}, ["率土之滨"], data_dir=tmp_path)
    node = append_keyword_node(run, "率土之滨", parent_id=None, round_index=1)
    update_keyword_node(run, node["node_id"], status="paused", stop_reason="B站搜索量无法获取")
    append_run_event(run, "pause", "B站搜索量无法获取", {"node_id": node["node_id"]})
    finish_recursive_run(run, "paused", "B站搜索量无法获取")
    save_recursive_run(run, data_dir=tmp_path)

    runs = list_recursive_runs(data_dir=tmp_path, platform="bilibili", status="paused", keyword="率土")

    assert len(runs) == 1
    assert runs[0]["status"] == "paused"
    assert runs[0]["events"][0]["type"] == "pause"


def test_recursive_history_date_filter(tmp_path):
    old_run = create_recursive_run({"platform": "bilibili"}, ["旧词"], data_dir=tmp_path)
    old_run["started_at"] = "2026-04-20T10:00:00"
    save_recursive_run(old_run, data_dir=tmp_path)
    new_run = create_recursive_run({"platform": "bilibili"}, ["新词"], data_dir=tmp_path)
    new_run["started_at"] = "2026-04-24T10:00:00"
    save_recursive_run(new_run, data_dir=tmp_path)

    runs = list_recursive_runs(data_dir=tmp_path, date_from="2026-04-24", date_to="2026-04-24")

    assert [run["run_id"] for run in runs] == [new_run["run_id"]]


def test_recursive_round_event_persistence(tmp_path):
    run = create_recursive_run({"platform": "youtube"}, ["slg"], data_dir=tmp_path)
    append_round(run, 1, ["slg"])
    append_run_event(run, "info", "round started")
    finish_recursive_run(run, "success", "达到最大轮数")
    save_recursive_run(run, data_dir=tmp_path)

    loaded = load_recursive_run(run["run_id"], data_dir=tmp_path)

    assert loaded["rounds"][0]["round"] == 1
    assert loaded["events"][0]["message"] == "round started"
    assert loaded["status"] == "success"


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
