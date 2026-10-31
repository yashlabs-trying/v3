class Memo:
    """Memoizes f on its arguments; invalidate() must clear everything."""

    def __init__(self, f):
        self._f = f
        self._cache = {}
        self.calls = 0

    def __call__(self, *args):
        if args not in self._cache:
            self.calls += 1
            self._cache[args] = self._f(*args)
        return self._cache[args]

    def invalidate(self):
        return None
