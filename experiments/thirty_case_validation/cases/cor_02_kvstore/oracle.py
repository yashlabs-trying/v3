from kvstore import KvStore


def test_df_set_and_keys():
    s = KvStore()
    s.set("a", 1)
    s.set("b", 2)
    s.set("a", 3)
    assert s.keys() == ["a", "b"]
    assert len(s) == 2


def test_df_delete_keeps_index_consistent():
    s = KvStore()
    s.set("a", 1)
    s.set("b", 2)
    assert s.delete("a") is True
    assert s.keys() == ["b"]
    assert len(s) == 1
    assert s.delete("a") is False
    s.set("a", 9)
    assert s.keys() == ["b", "a"]


def test_df_delete_missing():
    s = KvStore()
    assert s.delete("zzz") is False
