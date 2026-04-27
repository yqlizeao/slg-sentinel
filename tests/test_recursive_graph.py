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
