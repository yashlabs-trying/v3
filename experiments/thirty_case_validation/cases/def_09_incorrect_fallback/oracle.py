from lookup import lookup


def test_df_primary_preferred():
    assert lookup({"a": 1}, {"a": 2}, "a") == 1


def test_df_fallback_used():
    assert lookup({"a": 1}, {"b": 2}, "b") == 2


def test_df_missing_both():
    assert lookup({}, {}, "z") is None
