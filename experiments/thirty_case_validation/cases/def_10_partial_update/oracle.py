from patch import apply_patch


def test_df_all_changes_applied():
    s = {"a": 1, "b": 2, "c": 3}
    got = apply_patch(s, {"a": 10, "b": 20})
    assert got == {"a": 10, "b": 20, "c": 3}
    assert s == {"a": 1, "b": 2, "c": 3}


def test_df_none_removes():
    assert apply_patch({"a": 1}, {"a": None}) == {}
