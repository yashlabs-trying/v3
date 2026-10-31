from cache import Memo


def test_df_memoises():
    m = Memo(lambda x: x * 2)
    assert m(2) == 4
    assert m(2) == 4
    assert m.calls == 1


def test_df_invalidate_forces_recompute():
    state = {"v": 1}
    m = Memo(lambda x: state["v"] + x)
    assert m(0) == 1
    state["v"] = 10
    assert m(0) == 1  # cached
    m.invalidate()
    assert m(0) == 10  # recomputed
