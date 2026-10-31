#!/bin/bash
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks
for T in \
  instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan \
  instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f \
  instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed ; do
  echo "=== $T ==="
  wc -c "$MIR/$T/instruction.md"
  # check for non-ascii / unusual chars
  python3 -c "
d=open('$MIR/$T/instruction.md','rb').read()
nonascii=set(b for b in d if b>127)
print('non-ascii byte values:', sorted(nonascii)[:20])
print('has backticks:', d.count(b'\`'), 'has \$(', d.count(b'\$('))
"
done
