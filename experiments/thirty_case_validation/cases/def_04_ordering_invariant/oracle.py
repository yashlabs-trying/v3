from rank import rank


def test_df_descending():
    got = rank([(1, "a"), (3, "b"), (2, "c")])
    assert [s for s, _ in got] == [3, 2, 1]


def test_df_stable_ties():
    # names are in reverse-alphabetical original order, so an implementation
    # that sorts on the name within a score group changes the order.
    got = rank([(1, "z"), (2, "y"), (1, "x"), (2, "w")])
    assert [n for _, n in got] == ["y", "w", "z", "x"]
