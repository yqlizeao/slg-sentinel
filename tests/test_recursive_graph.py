def test_video_id_diff_helper():
    """Diff between two read_video_id_set snapshots returns added IDs only."""
    from ui.components.recursive_graph import diff_video_ids

    before = {"a.csv": {"BV1", "BV2"}}
    after = {"a.csv": {"BV1", "BV2", "BV3"}, "b.csv": {"BV9"}}

    added = diff_video_ids(before, after)

    assert sorted(added) == ["BV3", "BV9"]


def test_video_id_diff_empty_when_no_change():
    from ui.components.recursive_graph import diff_video_ids

    before = {"a.csv": {"BV1"}}
    after = {"a.csv": {"BV1"}}

    assert diff_video_ids(before, after) == []


def test_calculate_layout_single_round_single_node():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "三国", "round": 1, "parent_id": "",
             "status": "success",
             "crawl_metrics": {"videos": 12},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [],
    }

    layout = calculate_layout(run)

    assert len(layout["nodes"]) == 1
    n = layout["nodes"][0]
    assert n["x"] == 0
    assert n["y"] == 32  # COL_HEAD_H
    assert n["height"] == 56  # 1-line keyword + no extras
    assert n["width"] == 220
    assert layout["edges"] == []
    assert layout["svg_height"] >= n["y"] + n["height"]
    assert layout["svg_width"] == 220


def test_calculate_layout_two_rounds_with_edge():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "三国", "round": 1, "parent_id": "",
             "status": "success", "crawl_metrics": {"videos": 5},
             "candidate_metrics": {"count": 3}},
            {"node_id": "n2", "keyword": "蜀汉", "round": 2, "parent_id": "n1",
             "status": "success", "crawl_metrics": {"videos": 9},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [{"from": "n1", "to": "n2", "keyword": "蜀汉"}],
    }

    layout = calculate_layout(run)

    n1 = next(n for n in layout["nodes"] if n["node_id"] == "n1")
    n2 = next(n for n in layout["nodes"] if n["node_id"] == "n2")
    assert n1["x"] == 0
    assert n2["x"] == 220 + 80  # COL_W + COL_GAP
    assert n1["height"] == 72  # 1-line keyword + extras
    assert n2["height"] == 56  # 1-line keyword + no extras
    assert len(layout["edges"]) == 1
    edge = layout["edges"][0]
    assert edge["from_node_id"] == "n1"
    assert edge["to_node_id"] == "n2"
    assert "M" in edge["path"] and "C" in edge["path"]


def test_calculate_layout_long_keyword_grows_height():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "n1", "keyword": "三国群英战棋无双版本测评首发",
             "round": 1, "parent_id": "", "status": "success",
             "crawl_metrics": {"videos": 1}, "candidate_metrics": {"count": 0}},
        ],
        "edges": [],
    }

    layout = calculate_layout(run)

    assert layout["nodes"][0]["height"] == 80  # 2-line keyword + no extras


def test_calculate_layout_sorts_children_by_score():
    from ui.components.recursive_graph import calculate_layout

    run = {
        "nodes": [
            {"node_id": "p", "keyword": "三国", "round": 1, "parent_id": "",
             "status": "success", "crawl_metrics": {"videos": 1},
             "candidate_metrics": {"count": 0}},
            {"node_id": "c1", "keyword": "弱", "round": 2, "parent_id": "p",
             "status": "success", "crawl_metrics": {"videos": 1, "score": 1.0},
             "candidate_metrics": {"count": 0}},
            {"node_id": "c2", "keyword": "强", "round": 2, "parent_id": "p",
             "status": "success", "crawl_metrics": {"videos": 1, "score": 9.0},
             "candidate_metrics": {"count": 0}},
        ],
        "edges": [
            {"from": "p", "to": "c1", "keyword": "弱"},
            {"from": "p", "to": "c2", "keyword": "强"},
        ],
    }

    layout = calculate_layout(run)

    children = [n for n in layout["nodes"] if n["round"] == 2]
    assert children[0]["node_id"] == "c2"  # higher score first
    assert children[1]["node_id"] == "c1"


def test_url_with_overrides_preserves_other_keys():
    from ui.components.recursive_graph import url_with

    assert url_with({"recursive_node": "n1", "recursive_panels": "open"},
                    recursive_node="n2") == "?recursive_node=n2&recursive_panels=open"


def test_url_with_drops_empty_values():
    from ui.components.recursive_graph import url_with

    assert url_with({"recursive_node": "n1"},
                    recursive_node=None) == "?"


def test_url_with_no_existing_params():
    from ui.components.recursive_graph import url_with

    assert url_with({}, recursive_panels="closed") == "?recursive_panels=closed"
