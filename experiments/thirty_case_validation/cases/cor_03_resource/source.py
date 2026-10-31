class GuardedFile:
    """Wraps a file-like object; close() must always release it, even on error."""

    def __init__(self, fh):
        self._fh = fh
        self.closed = False

    def use(self):
        try:
            return self._fh.read()
        finally:
            self.close()

    def close(self):
        if not self.closed:
            self._fh.close()
            self.closed = True
