"""Offline tests for the expansion task oracles (teleport, ansible, element-web)."""

from __future__ import annotations

from dataforge_v3.semantic.contract import audit_contract
from dataforge_v3.semantic.executors import (
    parse_ansible_probe_output,
    parse_elementweb_probe_output,
    parse_teleport_probe_output,
)
from dataforge_v3.semantic.tasks import ansible, elementweb, teleport


def test_teleport_parse_maps_properties():
    out = (
        "=== RUN   TestDataForgeTeleportTruncation\n"
        "--- PASS: TestDataForgeTeleportTruncation/truncate.format (0.00s)\n"
        "--- FAIL: TestDataForgeTeleportTruncation/footnote.section (0.00s)\n"
    )
    res = parse_teleport_probe_output(out)
    by = {r.name: r for r in res}
    assert by["teleport:truncate.format"].passed is True
    assert by["teleport:footnote.section"].passed is False
    assert by["teleport:footnote.section"].clauses == ["footnote.section"]


def test_teleport_contract_has_clauses():
    audit = audit_contract(teleport.CONTRACT, teleport.REQUIRED_TESTS)
    assert audit.total_clauses >= 5


def test_ansible_parse_maps_tests():
    out = "test/units/module_utils/urls/zz.py::test_df_gzip_decode PASSED\ntest/units/module_utils/urls/zz.py::test_df_reader_close_closes_fp FAILED\n"
    res = parse_ansible_probe_output(out)
    by = {r.name: r for r in res}
    assert by["ansible:test_df_gzip_decode"].passed is True
    assert by["ansible:test_df_reader_close_closes_fp"].passed is False


def test_ansible_oracle_files():
    files = ansible.generate_oracle()
    assert "zz_df_ansible_oracle_test.py" in files
    assert "HAS_GZIP" in files["zz_df_ansible_hasgzip_test.py"]


def test_elementweb_parse_maps_tests():
    out = "    \u2713 df_capacity (5 ms)\n    \u2717 df_recency_evict (2 ms)\n"
    res = parse_elementweb_probe_output(out)
    by = {r.name: r for r in res}
    assert by["element-web:df_capacity"].passed is True
    assert by["element-web:df_recency_evict"].passed is False


def test_elementweb_contract_and_test_source():
    audit = audit_contract(elementweb.CONTRACT, elementweb.REQUIRED_TESTS)
    assert audit.total_clauses >= 6
    src = elementweb.generate_jest_test()
    assert "df_values_order" in src and "LruCache" in src
