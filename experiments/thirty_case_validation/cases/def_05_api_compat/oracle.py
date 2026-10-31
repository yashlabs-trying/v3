from fetch import fetch


def test_df_defaults():
    assert fetch("u") == {"url": "u", "timeout": 30, "verify": True}


def test_df_legacy_confirm_accepted():
    assert fetch("u", confirm=False)["verify"] is False
    assert fetch("u", confirm=True)["verify"] is True


def test_df_explicit_verify():
    assert fetch("u", verify=False)["verify"] is False
