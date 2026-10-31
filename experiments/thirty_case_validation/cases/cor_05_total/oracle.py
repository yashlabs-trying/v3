from total import total


def test_df_no_discount_preserved():
    assert total([10, 20, 30]) == 60


def test_df_discount_applied():
    assert total([10, 20, 30], discount=10) == 54


def test_df_empty():
    assert total([]) == 0
