from parse_int import parse_int


def test_df_parse_valid():
    assert parse_int(" 42 ") == 42
    assert parse_int("-7") == -7


def test_df_parse_malformed_returns_default():
    assert parse_int("abc", default=-1) == -1
    assert parse_int("", default=-1) == -1
    assert parse_int(None, default=-1) == -1


def test_df_parse_non_string():
    assert parse_int(3.5, default=0) == 0
