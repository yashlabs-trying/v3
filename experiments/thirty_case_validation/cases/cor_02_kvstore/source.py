class KvStore:
    """A small key/value store with an auxiliary index kept in sync."""

    def __init__(self):
        self._data = {}
        self._order = []

    def set(self, key, value):
        if key not in self._data:
            self._order.append(key)
        self._data[key] = value

    def delete(self, key):
        if key not in self._data:
            return False
        del self._data[key]
        self._order.remove(key)
        return True

    def keys(self):
        return list(self._order)

    def __len__(self):
        return len(self._data)
