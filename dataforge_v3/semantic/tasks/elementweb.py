"""Independent contract + oracle for the element-web LRU-cache surface (V3.2 expansion).

element-web is a large TS/Jest task. Only the pure, deterministic `LruCache`
class is oracle-audited here; the `UserProfilesStore` / SDK-context portion is
covered by the specification audit but not by an executable oracle in this
expansion (documented limitation). This keeps the oracle lightweight and honest.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dataforge_v3.semantic.model import ClauseKind, ContractClause, ProbeResult

TASK = "element-web"

CONTRACT: list[ContractClause] = [
    ContractClause(
        id="lru.capacity",
        kind=ClauseKind.POSTCONDITION,
        statement="LruCache rejects capacity < 1 with 'Cache capacity must be at least 1'.",
        source="instruction bullet 13",
        tested_by_original=[
            "test/utils/LruCache-test.ts | LruCache | when creating a cache with negative capacity it should raise an error",
            "test/utils/LruCache-test.ts | LruCache | when creating a cache with 0 capacity it should raise an error",
        ],
    ),
    ContractClause(
        id="lru.recency_evict",
        kind=ClauseKind.INVARIANT,
        statement="has()/get() mark recency; adding over capacity evicts the least recently used.",
        source="instruction bullet 14",
        tested_by_original=[
            "test/utils/LruCache-test.ts | and accesing the first added item and adding another item | should not contain the least recently accessed items",
        ],
    ),
    ContractClause(
        id="lru.values_insertion_order",
        kind=ClauseKind.INVARIANT,
        statement=(
            "values() yields surviving keys in insertion order; reading/updating a "
            "key affects recency but must not reorder it in values()."
        ),
        source="instruction bullets 15 and 16",
        tested_by_original=[
            "test/utils/LruCache-test.ts | when the cache contains 2 items | values() should return the items in the cache",
        ],
    ),
    ContractClause(
        id="lru.delete",
        kind=ClauseKind.EDGE_CASE,
        statement=(
            "Deleting a missing key does not throw; deleting first/middle/last/all "
            "leaves remaining values and future insertions consistent."
        ),
        source="instruction bullet 17",
        tested_by_original=[
            "test/utils/LruCache-test.ts | and adding another item | deleting an unkonwn item should not raise an error",
            "test/utils/LruCache-test.ts | and adding another item | deleting all items should work",
        ],
    ),
    ContractClause(
        id="lru.replace",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "Replacing a key updates its value and recency while preserving "
            "values() order for surviving keys."
        ),
        source="instruction bullet 18",
        tested_by_original=[
            "test/utils/LruCache-test.ts | when the cache contains some items where one of them is a replacement | should contain the last recently set items",
        ],
    ),
    ContractClause(
        id="lru.map_key",
        kind=ClauseKind.INVARIANT,
        statement="Entries are stored in a native Map keyed by the raw cache key (Map.prototype.set(key, value)).",
        source="instruction bullet 19",
        tested_by_original=[
            "test/utils/LruCache-test.ts | when there is a cache with a capacity of 3 | has() should return false",
        ],
    ),
    ContractClause(
        id="lru.set_error",
        kind=ClauseKind.ERROR_BEHAVIOR,
        statement=(
            "If storing throws, LruCache logs 'LruCache error' with the error, "
            "clears the cache, and does not propagate."
        ),
        source="instruction bullet 20",
        tested_by_original=[
            "test/utils/LruCache-test.ts | when the cache contains 2 items | when an error occurs while setting an item the cache should be cleard",
        ],
    ),
]

REQUIRED_TESTS = {
    "test/utils/LruCache-test.ts | LruCache | when creating a cache with negative capacity it should raise an error",
    "test/utils/LruCache-test.ts | LruCache | when creating a cache with 0 capacity it should raise an error",
    "test/utils/LruCache-test.ts | and accesing the first added item and adding another item | should not contain the least recently accessed items",
    "test/utils/LruCache-test.ts | when the cache contains 2 items | values() should return the items in the cache",
    "test/utils/LruCache-test.ts | and adding another item | deleting all items should work",
    "test/utils/LruCache-test.ts | when the cache contains some items where one of them is a replacement | should contain the last recently set items",
    "test/utils/LruCache-test.ts | when the cache contains 2 items | when an error occurs while setting an item the cache should be cleard",
}

JEST_TEST = r'''
/* Code generated by DataForge V3.2 semantic oracle (element-web). DO NOT EDIT. */
import { LruCache } from "../../src/utils/LruCache";

describe("DataForge LruCache oracle", () => {
    it("df_capacity: rejects < 1", () => {
        expect(() => new LruCache(0)).toThrow("Cache capacity must be at least 1");
        expect(() => new LruCache(-1)).toThrow("Cache capacity must be at least 1");
    });

    it("df_recency_evict: has/get refresh recency", () => {
        const cache = new LruCache<string, number>(2);
        cache.set("a", 1);
        cache.set("b", 2);
        cache.get("a"); // a is now most recent
        cache.set("c", 3); // evicts b
        expect(cache.has("a")).toBe(true);
        expect(cache.has("b")).toBe(false);
        expect(cache.has("c")).toBe(true);
    });

    it("df_values_order: insertion order preserved across reads and updates", () => {
        const cache = new LruCache<string, number>(3);
        cache.set("a", 1);
        cache.set("b", 2);
        cache.set("c", 3);
        cache.get("a"); // must not reorder
        cache.set("b", 20); // update must not reorder
        expect([...cache.values()]).toEqual([1, 20, 3]);
    });

    it("df_delete: missing delete no-throw; delete middle keeps order", () => {
        const cache = new LruCache<string, number>(5);
        cache.set("a", 1);
        cache.set("b", 2);
        cache.set("c", 3);
        expect(() => cache.delete("zzz")).not.toThrow();
        cache.delete("b");
        expect([...cache.values()]).toEqual([1, 3]);
        cache.set("d", 4);
        expect([...cache.values()]).toEqual([1, 3, 4]);
    });

    it("df_replace: replace updates value and recency", () => {
        const cache = new LruCache<string, number>(2);
        cache.set("a", 1);
        cache.set("b", 2);
        cache.set("a", 10); // a now most recent
        cache.set("c", 3); // evicts b
        expect(cache.has("a")).toBe(true);
        expect(cache.has("b")).toBe(false);
        expect([...cache.values()]).toEqual([10, 3]);
    });

    it("df_set_then_clear_on_error: error is not propagated and cache is cleared", () => {
        const cache = new LruCache<string, number>(3);
        cache.set("a", 1);
        const spy = jest.spyOn(Map.prototype, "set").mockImplementationOnce(() => {
            throw new Error("boom");
        });
        expect(() => cache.set("b", 2)).not.toThrow();
        spy.mockRestore();
        expect([...cache.values()]).toEqual([]);
    });
});
'''


def generate_jest_test() -> str:
    return JEST_TEST


Executor = Callable[[dict], ProbeResult]

_DF_TESTS = {
    "df_capacity": "lru.capacity",
    "df_recency_evict": "lru.recency_evict",
    "df_values_order": "lru.values_insertion_order",
    "df_delete": "lru.delete",
    "df_replace": "lru.replace",
    "df_set_then_clear_on_error": "lru.set_error",
}


@dataclass
class ElementWebOracle:
    task: str = TASK
    executor: Executor | None = None

    def run(self, cases, candidates=None) -> list[ProbeResult]:  # type: ignore[override]
        if self.executor is None:
            return [
                ProbeResult(
                    name="element-web:no-executor",
                    kind="differential",
                    passed=False,
                    detail="no executor configured",
                )
            ]
        test_src = generate_jest_test()
        results: list[ProbeResult] = []
        for name, source in candidates or []:
            if hasattr(source, "read_text"):
                src = source.read_text(encoding="utf-8")
            else:
                src = Path(source).read_text(encoding="utf-8")
            results.append(
                self.executor({"candidate": name, "lru_source": src, "test_source": test_src})
            )
        return results
