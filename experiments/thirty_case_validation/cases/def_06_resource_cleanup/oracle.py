import io
from resource import GuardedFile


class Boom(io.BytesIO):
    def read(self, *a):
        raise RuntimeError("read failed")


def test_df_closes_on_success():
    fh = io.BytesIO(b"data")
    g = GuardedFile(fh)
    assert g.use() == b"data"
    assert g.closed and fh.closed


def test_df_closes_on_error():
    fh = Boom(b"x")
    g = GuardedFile(fh)
    try:
        g.use()
    except RuntimeError:
        pass
    assert g.closed, "file must be closed even when read() raises"
