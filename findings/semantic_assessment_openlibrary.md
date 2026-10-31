# Semantic assessment — openlibrary

- **Submission:** `deepseek`
- **V2 reward:** 1.0
- **V3.1 classification:** PASS
- **Semantic verdict:** **CONFIRMED_CORRECT**
- **Confidence:** high

## Contract coverage

| Clause | Kind | Covered by official tests | Statement |
|---|---|---|---|
| find_keys.depth | POSTCONDITION | scripts/tests/test_new_solr_updater.py::TestParseLog::test_action_save, scripts/tests/test_new_solr_updater.py::TestParseLog::test_move_edition | find_keys(d) yields, in traversal order, every string value stored under a 'key' field at any nesting depth within a dict or list. |
| find_keys.types | INVARIANT | — | find_keys must not recurse into or emit values for non-dict/list types. |
| parse_log.one_key_per_doc | POSTCONDITION | scripts/tests/test_new_solr_updater.py::TestParseLog::test_action_save, scripts/tests/test_new_solr_updater.py::TestParseLog::test_move_edition, scripts/tests/test_new_solr_updater.py::TestParseLog::test_new_account | For 'save' and 'save_many', parse_log yields exactly one key per doc in changeset['docs']: that doc's own top-level 'key'. |
| parse_log.difference | POSTCONDITION | scripts/tests/test_new_solr_updater.py::TestParseLog::test_action_save, scripts/tests/test_new_solr_updater.py::TestParseLog::test_move_edition | When old_docs[i] is not None, additionally yield every key in find_keys(old_docs[i]) not in find_keys(docs[i]). |
| parse_log.none_old_doc | EDGE_CASE | scripts/tests/test_new_solr_updater.py::TestParseLog::test_new_account | If old_docs[i] is None, skip the set-difference for that pair and yield only the doc's top-level key. |
| parse_log.old_docs_length | EDGE_CASE | — | documents and old_docs are paired by index; a doc with no matching old_docs entry must be treated as having no previous version (top-level key only), and must not error. |

## Probe evidence

| Probe | Kind | Clauses | Result | Detail |
|---|---|---|---|---|
| deepseek:property[0] | property | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |
| deepseek:boundary[0] | boundary | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |
| deepseek:boundary[1] | boundary | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |
| deepseek:boundary[2] | boundary | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |
| deepseek:boundary[3] | boundary | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |
| deepseek:boundary[4] | boundary | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |
| deepseek:boundary[5] | boundary | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |
| deepseek:stateful[0] | stateful | find_keys.depth, find_keys.types, parse_log.one_key_per_doc, parse_log.difference, parse_log.none_old_doc, parse_log.old_docs_length | PASS | matches contract structure |

## Reproduce

```bash
python -m pytest dataforge_v3/tests/test_openlibrary_oracle.py -q
```

## Notes

- accepted submission satisfies every supported clause
