#!/bin/bash
# Freeze checksums of all original (counted) results.
BASE=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/evidence_checksums.txt
: > "$OUT"
for j in final-nodebb final-flipt final-vuls final-openlibrary final-teleport final-ansible final-elementweb; do
  if [ -d "$BASE/$j" ]; then
    find "$BASE/$j" -type f -exec sha256sum {} \; >> "$OUT" 2>/dev/null
  fi
done
echo "checksummed files: $(wc -l < "$OUT")"
echo "--- nodebb files ---"
grep 'final-nodebb' "$OUT" | awk '{print $2}' | sed "s|$BASE/||"
