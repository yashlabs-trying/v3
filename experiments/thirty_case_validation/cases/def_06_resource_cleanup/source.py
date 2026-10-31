class GuardedFile:
    def __init__(self, fh):
        self._fh = fh
        self.closed = False

    def use(self):
        data = self._fh.read()
        self.close()
        return data

    def close(self):
        if not self.closed:
            self._fh.close()
            self.closed = True
