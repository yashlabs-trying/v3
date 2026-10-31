# Parser Integrity — DataForge V3.1 Phase 1A

## Method
For each task where the agent ran, the parser's `verifier/output.json` was compared against the raw
runner stdout (`run-script-stdout.txt`) and the required-test sets from `tests/config.json`.

## Results per parser family

### Go text parser (vuls)
- Raw: `--- FAIL: TestSortByConfident (0.00s)`; 66 `--- PASS`, 1 `--- FAIL`.
- `output.json`: `TestSortByConfident` recorded FAILED; all others PASSED.
- Verdict: reward 0.0 (67 required, 66 passed). **Consistent. No loss.**
- Residual risk: parser uses `split()[2]`; a test name containing whitespace would be misparsed. Not triggered.

### Go text parser with `|| true` masking (flipt)
- `go test ... || true` masks nonzero exit, but the verifier derives reward only from parsed names.
- 13/13 required PASSED recorded. **Consistent.**
- Residual risk: a build failure would produce zero parsed tests → reward 0 (fails safe but as a false FAIL).

### Go `-json` parser + `-shuffle on -race` (teleport)
- 3/3 required PASSED. Whitespace-warning lines present in apply output did not affect parsing.
- Residual risk: shuffle/race nondeterminism; not observed to change the verdict here.

### pytest triple-regex + name-dedup parser (openlibrary)
- 3/3 required PASSED; raw pytest `-v --tb=short` agreed.
- Residual risk: `export_to_json` dedups by name (last wins); a test appearing PASSED and FAILED would collapse. Not triggered.

### pytest per-file loop + `|| true` (ansible)
- 48/48 required PASSED; parametrized IDs (`test_methods[get-kwargs0]`) parsed correctly.
- Residual risk: identifiers containing spaces cannot match `[^\s]+\.py::[^\s]+`. Not triggered.

### jest Unicode-checkmark parser (elementweb)
- 163/163 required PASSED; checkmarks present in jest output; no glyph loss observed.
- Residual risk: if checkmarks were stripped/absent, all tests would drop → false FAIL. Not triggered.

### mocha JSON parser + `|| echo` masking (nodebb)
- Suite init failed ("before all" hook: `require(...).getOrCreate is not a function`) under the
  contaminated/broken run; `failures` had the hook entry, required tests absent → reward 0.
- For the recovery run (agent working), 2/2 required PASSED.
- **Consistent**, but see V2_RELIABILITY_AUDIT: the original run's premise was invalid.

## Conclusion
No confirmed parser defect in the 7 tasks. All residual risks are branches not exercised by these
outcomes; they should be probed with synthetic contradictory evidence before being dismissed.
