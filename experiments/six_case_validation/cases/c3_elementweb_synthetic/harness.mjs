// Independent reproduction of the element-web LruCache semantic oracle probes
// (dataforge_v3/semantic/tasks/elementweb.py -> JEST_TEST) in plain Node.js.
// No jest dependency: the Map.prototype.set spy is reproduced with a one-shot
// monkey-patch, exercising the same observable behaviour the jest oracle checks.
//
// Usage: node harness.mjs <path-to-lru-cache.mjs-exporting-LruCache>
import { pathToFileURL } from "node:url";

const target = process.argv[2];
if (!target) {
  console.error("usage: node harness.mjs <lru-module>");
  process.exit(2);
}

const mod = await import(pathToFileURL(target).href);
const LruCache = mod.LruCache;

const results = [];
function probe(name, fn) {
  try {
    fn();
    results.push([name, "PASS"]);
  } catch (e) {
    results.push([name, "FAIL", String(e && e.message ? e.message : e)]);
  }
}

// df_capacity: rejects < 1
probe("df_capacity", () => {
  let threw0 = false, threwNeg = false;
  try { new LruCache(0); } catch { threw0 = true; }
  try { new LruCache(-1); } catch { threwNeg = true; }
  if (!threw0 || !threwNeg) throw new Error("capacity<1 must throw");
});

// df_recency_evict: has/get refresh recency
probe("df_recency_evict", () => {
  const cache = new LruCache(2);
  cache.set("a", 1);
  cache.set("b", 2);
  cache.get("a");
  cache.set("c", 3);
  if (cache.has("a") !== true) throw new Error("a should survive");
  if (cache.has("b") !== false) throw new Error("b should be evicted");
  if (cache.has("c") !== true) throw new Error("c should be present");
});

// df_values_order: insertion order preserved across reads and updates
probe("df_values_order", () => {
  const cache = new LruCache(3);
  cache.set("a", 1);
  cache.set("b", 2);
  cache.set("c", 3);
  cache.get("a");
  cache.set("b", 20);
  const got = [...cache.values()];
  if (JSON.stringify(got) !== JSON.stringify([1, 20, 3])) {
    throw new Error("values order changed: " + JSON.stringify(got));
  }
});

// df_delete: missing delete no-throw; delete middle keeps order
probe("df_delete", () => {
  const cache = new LruCache(5);
  cache.set("a", 1); cache.set("b", 2); cache.set("c", 3);
  try { cache.delete("zzz"); } catch (e) { throw new Error("delete missing threw"); }
  cache.delete("b");
  if (JSON.stringify([...cache.values()]) !== JSON.stringify([1, 3])) {
    throw new Error("delete middle order wrong");
  }
  cache.set("d", 4);
  if (JSON.stringify([...cache.values()]) !== JSON.stringify([1, 3, 4])) {
    throw new Error("post-delete insertion wrong");
  }
});

// df_replace: replace updates value and recency
probe("df_replace", () => {
  const cache = new LruCache(2);
  cache.set("a", 1); cache.set("b", 2);
  cache.set("a", 10);
  cache.set("c", 3);
  if (cache.has("a") !== true) throw new Error("a should survive");
  if (cache.has("b") !== false) throw new Error("b should be evicted");
  if (JSON.stringify([...cache.values()]) !== JSON.stringify([10, 3])) {
    throw new Error("replace order wrong");
  }
});

// df_set_then_clear_on_error: error not propagated and cache is cleared
probe("df_set_then_clear_on_error", () => {
  const cache = new LruCache(3);
  cache.set("a", 1);
  const origSet = Map.prototype.set;
  let fired = false;
  Map.prototype.set = function (...args) {
    if (!fired) { fired = true; throw new Error("boom"); }
    return origSet.apply(this, args);
  };
  try {
    let threw = false;
    try { cache.set("b", 2); } catch (e) { threw = true; }
    if (threw) throw new Error("error must not propagate");
  } finally {
    Map.prototype.set = origSet;
  }
  const vals = [...cache.values()];
  if (vals.length !== 0) throw new Error("cache must be cleared, got " + JSON.stringify(vals));
});

for (const r of results) {
  console.log(`--- ${r[1]}: ${r[0]}${r[2] ? " :: " + r[2] : ""}`);
}
const anyFail = results.some((r) => r[1] === "FAIL");
process.exit(anyFail ? 1 : 0);
