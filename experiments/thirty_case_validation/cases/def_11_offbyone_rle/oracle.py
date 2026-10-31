from rle import rle


def test_df_rle_basic():
    assert rle("aaabb") == [("a", 3), ("b", 2)]


def test_df_rle_singletons():
    assert rle("abc") == [("a", 1), ("b", 1), ("c", 1)]
    assert rle("") == []
