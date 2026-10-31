import pytest
from paginate import paginate


def test_df_page_boundaries():
    items = list(range(10))
    assert paginate(items, 1, 3) == [0, 1, 2]
    assert paginate(items, 4, 3) == [9]
    assert paginate(items, 5, 3) == []


def test_df_first_page_offbyone():
    items = list(range(10))
    assert paginate(items, 2, 3) == [3, 4, 5]


def test_df_invalid_page():
    with pytest.raises(ValueError):
        paginate(list(range(10)), 0, 3)
