from normalize import normalize


def test_df_key_normalisation():
    got = normalize([{"ID": 1, " Name ": " Bob "}])
    assert got == [{"id": 1, "name": "Bob"}]


def test_df_drops_missing_id():
    assert normalize([{"name": "x"}, {"id": 2}]) == [{"id": 2}]


def test_df_no_mutation():
    src = [{"ID": 1, "Name": "a"}]
    normalize(src)
    assert src == [{"ID": 1, "Name": "a"}]
