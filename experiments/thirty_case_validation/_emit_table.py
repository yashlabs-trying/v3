import json
from pathlib import Path

c = json.load(open("experiments/thirty_case_validation/postfix_comparison.json"))
for r in c["rows"]:
    eng = ", ".join(f"{f['clause'] or '-'}:{f['category']}" for f in r["engine_authored"]) or "none"
    print(f"| {r['case_id']} | {r['category']} | {r['origin']} | {r['expected']} | {eng} | "
          f"{'yes' if r['correct'] else 'NO'} | {'yes' if r['evidence_valid'] else 'NO'} | {r['median_latency_ms']} |")
