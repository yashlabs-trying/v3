"""Controlled-defect domain library for the 30-case validation.

Each entry is a small, self-contained Python module that models one real
software mechanism. For every mechanism we provide:

  * ``NAME``        - the module name.
  * ``SOURCE``      - the correct implementation.
  * ``ORACLE``      - a real pytest file that asserts the behavioural contract.
  * ``MUTANTS``     - named defects, each a full source body, tagged with the
                      failure mechanism and the contract clause it violates.

The mutants are executed by the *real pytest runner* against the corresponding
oracle before they are accepted as confirmed defects. Running the oracle is the
ground truth; the engine's own tests are never used for that.

The functions are deliberately non-trivial (multiple branches, state) so the
defects are not all trivial one-line mutations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Domain:
    name: str
    source: str
    oracle: str
    mutants: dict[str, str] = field(default_factory=dict)
    # probe name -> clause id (the oracle test functions and the clauses they pin)
    probe_clauses: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 1. boundary / off-by-one : windowed pagination
# ---------------------------------------------------------------------------

PAGINATE = '''\
def paginate(items, page, per_page):
    """Return the slice of items for a 1-based page number.

    Contract:
      * page is 1-based; page < 1 raises ValueError.
      * a page beyond the end returns an empty list (never an exception).
      * exactly `per_page` items are returned except on the final short page.
    """
    if page < 1:
        raise ValueError("page must be >= 1")
    if per_page < 1:
        raise ValueError("per_page must be >= 1")
    start = (page - 1) * per_page
    return items[start:start + per_page]
'''

PAGINATE_ORACLE = '''\
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
'''

# defect: start = (page-1)*per_page - 1  (off-by-one on the window)
PAGINATE_MUT_OFFBYONE = PAGINATE.replace(
    "    start = (page - 1) * per_page\n    return items[start:start + per_page]",
    "    start = (page - 1) * per_page - 1\n    return items[start:start + per_page]",
)

# defect: beyond-end raises instead of returning []
PAGINATE_MUT_RAISE = PAGINATE.replace(
    "    start = (page - 1) * per_page\n    return items[start:start + per_page]",
    "    start = (page - 1) * per_page\n"
    "    if start >= len(items):\n"
    "        raise IndexError('page out of range')\n"
    "    return items[start:start + per_page]",
)


# ---------------------------------------------------------------------------
# 2. error handling : safe integer parse with default
# ---------------------------------------------------------------------------

PARSE_INT = '''\
def parse_int(text, default=None):
    """Parse an integer, returning `default` for malformed input.

    Contract:
      * None and non-string inputs return `default` (no exception).
      * whitespace is stripped and valid integers parse.
      * a malformed non-empty string returns `default`, it never raises.
    """
    if text is None:
        return default
    if not isinstance(text, str):
        return default
    text = text.strip()
    if text == "":
        return default
    try:
        return int(text)
    except ValueError:
        return default
'''

PARSE_INT_ORACLE = '''\
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
'''

# defect: removes the try/except -> malformed input raises
PARSE_INT_MUT_RAISE = PARSE_INT.replace(
    "    try:\n        return int(text)\n    except ValueError:\n        return default",
    "    return int(text)",
)

# defect: over-eager sign handling - rejects negative integers as "malformed"
PARSE_INT_MUT_NEGATIVES = PARSE_INT.replace(
    "    try:\n        return int(text)\n    except ValueError:\n        return default",
    "    if text.startswith('-'):\n        return default\n    try:\n        return int(text)\n    except ValueError:\n        return default",
)


# ---------------------------------------------------------------------------
# 3. state consistency : key-value store with delete + length
# ---------------------------------------------------------------------------

KVSTORE = '''\
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
'''

KVSTORE_ORACLE = '''\
from kvstore import KvStore


def test_df_set_and_keys():
    s = KvStore()
    s.set("a", 1)
    s.set("b", 2)
    s.set("a", 3)
    assert s.keys() == ["a", "b"]
    assert len(s) == 2


def test_df_delete_keeps_index_consistent():
    s = KvStore()
    s.set("a", 1)
    s.set("b", 2)
    assert s.delete("a") is True
    assert s.keys() == ["b"]
    assert len(s) == 1
    assert s.delete("a") is False
    s.set("a", 9)
    assert s.keys() == ["b", "a"]


def test_df_delete_missing():
    s = KvStore()
    assert s.delete("zzz") is False
'''

# defect: delete removes from data but not from the order index
KVSTORE_MUT_STALE_INDEX = KVSTORE.replace(
    "        del self._data[key]\n        self._order.remove(key)\n        return True",
    "        del self._data[key]\n        return True",
)

# defect: set does not append to the index for new keys
KVSTORE_MUT_MISSING_INDEX = KVSTORE.replace(
    "        if key not in self._data:\n            self._order.append(key)\n",
    "",
)


# ---------------------------------------------------------------------------
# 4. ordering invariant : stable sort by score with tie preservation
# ---------------------------------------------------------------------------

RANK = '''\
def rank(items):
    """Sort (score, name) pairs by descending score, stable on ties.

    Contract:
      * results are non-increasing in score.
      * items with equal scores keep their original relative order.
    """
    return sorted(items, key=lambda p: -p[0])
'''

RANK_ORACLE = '''\
from rank import rank


def test_df_descending():
    got = rank([(1, "a"), (3, "b"), (2, "c")])
    assert [s for s, _ in got] == [3, 2, 1]


def test_df_stable_ties():
    # names are in reverse-alphabetical original order, so an implementation
    # that sorts on the name within a score group changes the order.
    got = rank([(1, "z"), (2, "y"), (1, "x"), (2, "w")])
    assert [n for _, n in got] == ["y", "w", "z", "x"]
'''

# defect: breaks the stability invariant by additionally sorting on the name,
# so equal scores are no longer in their original relative order.
RANK_MUT_UNSTABLE = '''\
def rank(items):
    return sorted(items, key=lambda p: (-p[0], p[1]))
'''


# ---------------------------------------------------------------------------
# 5. API compatibility : function that must keep an old keyword working
# ---------------------------------------------------------------------------

FETCH = '''\
def fetch(url, timeout=30, verify=True):
    """Return a request descriptor.

    Contract (backwards compatibility):
      * the legacy keyword ``confirm`` must still be accepted.
      * ``confirm=False`` is an alias for ``verify=False``.
      * default verify is True.
    """
    if confirm is not None:  # noqa: F821  (injected at call time)
        verify = confirm
    return {"url": url, "timeout": timeout, "verify": verify}
'''

# The correct version accepts the legacy alias via **kwargs.
FETCH_CORRECT = '''\
def fetch(url, timeout=30, verify=True, **kwargs):
    """Return a request descriptor."""
    if "confirm" in kwargs:
        verify = kwargs["confirm"]
    return {"url": url, "timeout": timeout, "verify": verify}
'''

FETCH_ORACLE = '''\
from fetch import fetch


def test_df_defaults():
    assert fetch("u") == {"url": "u", "timeout": 30, "verify": True}


def test_df_legacy_confirm_accepted():
    assert fetch("u", confirm=False)["verify"] is False
    assert fetch("u", confirm=True)["verify"] is True


def test_df_explicit_verify():
    assert fetch("u", verify=False)["verify"] is False
'''

# defect: drops the legacy keyword -> TypeError on confirm=
FETCH_MUT_DROP_LEGACY = '''\
def fetch(url, timeout=30, verify=True):
    return {"url": url, "timeout": timeout, "verify": verify}
'''


# ---------------------------------------------------------------------------
# 6. resource cleanup : context manager that must close on error
# ---------------------------------------------------------------------------

RESOURCE = '''\
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
'''

RESOURCE_ORACLE = '''\
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
'''

# defect: no finally -> resource leaks on error path
RESOURCE_MUT_LEAK = '''\
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
'''


# ---------------------------------------------------------------------------
# 7. data transformation : normalize records
# ---------------------------------------------------------------------------

NORMALIZE = '''\
def normalize(records):
    """Normalize a list of raw records.

    Contract:
      * keys are lower-cased and whitespace-stripped.
      * values that are strings are whitespace-stripped.
      * records missing 'id' are dropped.
      * the input is not mutated.
    """
    out = []
    for rec in records:
        if not any(str(k).strip().lower() == "id" for k in rec):
            continue
        out.append({str(k).strip().lower(): (v.strip() if isinstance(v, str) else v)
                    for k, v in rec.items()})
    return out
'''

NORMALIZE_ORACLE = '''\
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
'''

# defect: mutates the input dict in place
NORMALIZE_MUT_INPLACE = '''\
def normalize(records):
    out = []
    for rec in records:
        if not any(str(k).strip().lower() == "id" for k in rec):
            continue
        for k in list(rec.keys()):
            v = rec.pop(k)
            rec[str(k).strip().lower()] = v.strip() if isinstance(v, str) else v
        out.append(rec)
    return out
'''


# ---------------------------------------------------------------------------
# 8. cache invalidation : memoized compute keyed on inputs
# ---------------------------------------------------------------------------

CACHE = '''\
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
        self._cache.clear()
'''

CACHE_ORACLE = '''\
from cache import Memo


def test_df_memoises():
    m = Memo(lambda x: x * 2)
    assert m(2) == 4
    assert m(2) == 4
    assert m.calls == 1


def test_df_invalidate_forces_recompute():
    state = {"v": 1}
    m = Memo(lambda x: state["v"] + x)
    assert m(0) == 1
    state["v"] = 10
    assert m(0) == 1  # cached
    m.invalidate()
    assert m(0) == 10  # recomputed
'''

# defect: invalidate does not clear the cache
CACHE_MUT_NO_INVALIDATE = CACHE.replace(
    "    def invalidate(self):\n        self._cache.clear()",
    "    def invalidate(self):\n        return None",
)


# ---------------------------------------------------------------------------
# 9. incorrect fallback : primary source with fallback
# ---------------------------------------------------------------------------

LOOKUP = '''\
def lookup(primary, fallback, key):
    """Return primary[key], else fallback[key], else None.

    Contract:
      * value from the primary source is preferred when the key is present.
      * the fallback is used only when the primary lacks the key.
      * a missing key in both returns None.
    """
    if key in primary:
        return primary[key]
    if key in fallback:
        return fallback[key]
    return None
'''

LOOKUP_ORACLE = '''\
from lookup import lookup


def test_df_primary_preferred():
    assert lookup({"a": 1}, {"a": 2}, "a") == 1


def test_df_fallback_used():
    assert lookup({"a": 1}, {"b": 2}, "b") == 2


def test_df_missing_both():
    assert lookup({}, {}, "z") is None
'''

# defect: fallback always wins
LOOKUP_MUT_FALLBACK_WINS = LOOKUP.replace(
    "    if key in primary:\n        return primary[key]\n    if key in fallback:\n        return fallback[key]\n    return None",
    "    if key in fallback:\n        return fallback[key]\n    if key in primary:\n        return primary[key]\n    return None",
)


# ---------------------------------------------------------------------------
# 10. partial update : patch application
# ---------------------------------------------------------------------------

PATCH = '''\
def apply_patch(state, changes):
    """Apply changes and return a NEW state dict.

    Contract:
      * every change in `changes` is applied.
      * keys set to None are removed.
      * the original `state` is never mutated.
    """
    out = dict(state)
    for k, v in changes.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = v
    return out
'''

PATCH_ORACLE = '''\
from patch import apply_patch


def test_df_all_changes_applied():
    s = {"a": 1, "b": 2, "c": 3}
    got = apply_patch(s, {"a": 10, "b": 20})
    assert got == {"a": 10, "b": 20, "c": 3}
    assert s == {"a": 1, "b": 2, "c": 3}


def test_df_none_removes():
    assert apply_patch({"a": 1}, {"a": None}) == {}
'''

# defect: returns after the first change (partial application) and mutates input
PATCH_MUT_PARTIAL = '''\
def apply_patch(state, changes):
    out = state
    for k, v in changes.items():
        if v is None:
            out.pop(k, None)
        else:
            out[k] = v
        break
    return out
'''


# ---------------------------------------------------------------------------
# 11. off-by-one (distinct function) : run-length encoding
# ---------------------------------------------------------------------------

RLE = '''\
def rle(data):
    """Run-length encode a string into (char, count) pairs.

    Contract:
      * every character is emitted exactly once, with its run count.
      * 'aaabb' -> [('a',3),('b',2)].
    """
    out = []
    i = 0
    n = len(data)
    while i < n:
        j = i
        while j < n and data[j] == data[i]:
            j += 1
        out.append((data[i], j - i))
        i = j
    return out
'''

RLE_ORACLE = '''\
from rle import rle


def test_df_rle_basic():
    assert rle("aaabb") == [("a", 3), ("b", 2)]


def test_df_rle_singletons():
    assert rle("abc") == [("a", 1), ("b", 1), ("c", 1)]
    assert rle("") == []
'''

# defect: count computed with j-i+1 (off-by-one on run length)
RLE_MUT_OFFBYONE = RLE.replace("out.append((data[i], j - i))", "out.append((data[i], j - i + 1))")


# ---------------------------------------------------------------------------
# 12. regression preservation : total with discount, must keep old behaviour
# ---------------------------------------------------------------------------

TOTAL = '''\
def total(prices, discount=0.0):
    """Sum prices, applying a discount percentage in [0, 100].

    Contract:
      * no discount (the historical behaviour) returns the plain sum.
      * a discount of d percent returns sum * (1 - d/100).
      * an empty list returns 0.0.
    """
    base = sum(prices)
    return base * (1.0 - discount / 100.0)
'''

TOTAL_ORACLE = '''\
from total import total


def test_df_no_discount_preserved():
    assert total([10, 20, 30]) == 60


def test_df_discount_applied():
    assert total([10, 20, 30], discount=10) == 54


def test_df_empty():
    assert total([]) == 0
'''

# defect: discount applied as a flat subtraction -> breaks both old and new
TOTAL_MUT_BREAKS_BASE = TOTAL.replace(
    "    base = sum(prices)\n    return base * (1.0 - discount / 100.0)",
    "    base = sum(prices)\n    return base - discount",
)


DOMAINS: list[Domain] = [
    Domain("paginate", PAGINATE, PAGINATE_ORACLE,
           {"mut_offbyone_window": PAGINATE_MUT_OFFBYONE, "mut_raise_past_end": PAGINATE_MUT_RAISE},
           {"test_df_page_boundaries": "paginate.boundary",
            "test_df_first_page_offbyone": "paginate.window",
            "test_df_invalid_page": "paginate.precondition"}),
    Domain("parse_int", PARSE_INT, PARSE_INT_ORACLE,
           {"mut_raises_on_malformed": PARSE_INT_MUT_RAISE, "mut_rejects_negatives": PARSE_INT_MUT_NEGATIVES},
           {"test_df_parse_valid": "parse.valid",
            "test_df_parse_malformed_returns_default": "parse.error_handling",
            "test_df_parse_non_string": "parse.type_guard"}),
    Domain("kvstore", KVSTORE, KVSTORE_ORACLE,
           {"mut_stale_index": KVSTORE_MUT_STALE_INDEX, "mut_missing_index": KVSTORE_MUT_MISSING_INDEX},
           {"test_df_set_and_keys": "kv.index_consistency",
            "test_df_delete_keeps_index_consistent": "kv.delete_consistency",
            "test_df_delete_missing": "kv.delete_missing"}),
    Domain("rank", RANK, RANK_ORACLE,
           {"mut_unstable_tie": RANK_MUT_UNSTABLE},
           {"test_df_descending": "rank.descending",
            "test_df_stable_ties": "rank.stable_ties"}),
    Domain("fetch", FETCH_CORRECT, FETCH_ORACLE,
           {"mut_drop_legacy_kwarg": FETCH_MUT_DROP_LEGACY},
           {"test_df_defaults": "fetch.defaults",
            "test_df_legacy_confirm_accepted": "fetch.legacy_compat",
            "test_df_explicit_verify": "fetch.verify"}),
    Domain("resource", RESOURCE, RESOURCE_ORACLE,
           {"mut_leak_on_error": RESOURCE_MUT_LEAK},
           {"test_df_closes_on_success": "resource.cleanup_success",
            "test_df_closes_on_error": "resource.cleanup_on_error"}),
    Domain("normalize", NORMALIZE, NORMALIZE_ORACLE,
           {"mut_inplace_mutation": NORMALIZE_MUT_INPLACE},
           {"test_df_key_normalisation": "normalize.keys",
            "test_df_drops_missing_id": "normalize.drop",
            "test_df_no_mutation": "normalize.purity"}),
    Domain("cache", CACHE, CACHE_ORACLE,
           {"mut_no_invalidate": CACHE_MUT_NO_INVALIDATE},
           {"test_df_memoises": "cache.memo",
            "test_df_invalidate_forces_recompute": "cache.invalidation"}),
    Domain("lookup", LOOKUP, LOOKUP_ORACLE,
           {"mut_fallback_wins": LOOKUP_MUT_FALLBACK_WINS},
           {"test_df_primary_preferred": "lookup.primary",
            "test_df_fallback_used": "lookup.fallback",
            "test_df_missing_both": "lookup.missing"}),
    Domain("patch", PATCH, PATCH_ORACLE,
           {"mut_partial_update": PATCH_MUT_PARTIAL},
           {"test_df_all_changes_applied": "patch.complete",
            "test_df_none_removes": "patch.remove"}),
    Domain("rle", RLE, RLE_ORACLE,
           {"mut_offbyone_count": RLE_MUT_OFFBYONE},
           {"test_df_rle_basic": "rle.count",
            "test_df_rle_singletons": "rle.boundary"}),
    Domain("total", TOTAL, TOTAL_ORACLE,
           {"mut_breaks_base": TOTAL_MUT_BREAKS_BASE},
           {"test_df_no_discount_preserved": "total.regression",
            "test_df_discount_applied": "total.discount",
            "test_df_empty": "total.empty"}),
]
