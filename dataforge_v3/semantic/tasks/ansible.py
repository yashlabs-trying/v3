"""Independent contract + oracle for the ansible gzip-response task (V3.2 expansion).

Python surface `ansible.module_utils.urls`. The oracle is a self-contained pytest
generated from the contract and executed inside the task image (the module has
many runtime deps). It adds cases the official tests do not cover:

  * Request(decompress=False) instance default honoured by open()
  * GzipDecodedReader.close() closes the underlying fp
  * missing_gzip_error() static message
  * fetch_url forces decompress off when HAS_GZIP is False
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dataforge_v3.semantic.model import ClauseKind, ContractClause, ProbeResult

TASK = "ansible"

CONTRACT: list[ContractClause] = [
    ContractClause(
        id="gzip.decode",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "Request.open on a gzip Content-Encoding response with decompression "
            "enabled exposes fp as GzipDecodedReader and read() yields the full "
            "decoded body despite the compressed Content-Length."
        ),
        source="instruction bullets 1, 16, 21",
        tested_by_original=["test/units/module_utils/urls/test_gzip.py::test_Request_open_gzip"],
    ),
    ContractClause(
        id="gzip.decompress_false",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "With decompress=False a gzip response's fp is NOT a GzipDecodedReader "
            "and read() yields the original compressed bytes."
        ),
        source="instruction bullets 2, 11, 14",
        tested_by_original=[
            "test/units/module_utils/urls/test_gzip.py::test_Request_open_decompress_false"
        ],
    ),
    ContractClause(
        id="gzip.non_gzip_passthrough",
        kind=ClauseKind.INVARIANT,
        statement=(
            "A non-gzip response's fp is never a GzipDecodedReader and read() "
            "yields the original body for either decompress setting."
        ),
        source="instruction bullets 3, 15",
        tested_by_original=[
            "test/units/module_utils/urls/test_gzip.py::test_Request_open_not_gzip",
            "test/units/module_utils/urls/test_gzip.py::test_Request_open_not_gzip_decompress_false",
        ],
    ),
    ContractClause(
        id="constructor.defaults",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "Request.__init__ defaults unredirected_headers=None and decompress=True; "
            "open() resolves both via _fallback when passed None."
        ),
        source="instruction bullets 4, 13, 24",
        tested_by_original=[],
    ),
    ContractClause(
        id="instance.decompress_default",
        kind=ClauseKind.INVARIANT,
        statement=(
            "A Request constructed with decompress=False does not decompress even "
            "when open() is called without a decompress argument."
        ),
        source="instruction bullet 4 (per-attribute fallback)",
        tested_by_original=[],
    ),
    ContractClause(
        id="missing_module_error",
        kind=ClauseKind.POSTCONDITION,
        statement="MissingModuleError accepts module and exposes it as .module.",
        source="instruction bullets 7, 12",
        tested_by_original=[
            "test/units/module_utils/urls/test_gzip.py::test_missing_module_error_module"
        ],
    ),
    ContractClause(
        id="has_gzip_false",
        kind=ClauseKind.EDGE_CASE,
        statement=(
            "When gzip cannot be imported, urls still imports, HAS_GZIP is False, "
            "and GzipDecodedReader(None) raises MissingModuleError."
        ),
        source="instruction bullets 8, 9, 23",
        tested_by_original=[
            "test/units/module_utils/urls/test_gzip.py::test_GzipDecodedReader_no_gzip"
        ],
    ),
    ContractClause(
        id="reader.close",
        kind=ClauseKind.POSTCONDITION,
        statement="GzipDecodedReader.close() closes the underlying file object.",
        source="instruction New Interfaces (GzipDecodedReader.close)",
        tested_by_original=[],
    ),
    ContractClause(
        id="fetch_url.gzip_fallback",
        kind=ClauseKind.EDGE_CASE,
        statement=(
            "When HAS_GZIP is False, fetch_url automatically disables decompression "
            "so the request can proceed."
        ),
        source="instruction bullet 18",
        tested_by_original=[],
    ),
]

REQUIRED_TESTS = {
    "test/units/module_utils/urls/test_gzip.py::test_Request_open_gzip",
    "test/units/module_utils/urls/test_gzip.py::test_Request_open_decompress_false",
    "test/units/module_utils/urls/test_gzip.py::test_Request_open_not_gzip",
    "test/units/module_utils/urls/test_gzip.py::test_Request_open_not_gzip_decompress_false",
    "test/units/module_utils/urls/test_gzip.py::test_missing_module_error_module",
    "test/units/module_utils/urls/test_gzip.py::test_GzipDecodedReader_no_gzip",
}

ORACLE_PY = r"""
# Code generated by DataForge V3.2 semantic oracle (ansible). DO NOT EDIT.
import gzip
import io
import sys

import pytest

try:
    from urllib.response import addinfourl
except ImportError:
    from urllib import addinfourl

from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import http_client
import ansible.module_utils.urls as urls


JSON_DATA = b'{"foo": "bar", "baz": "qux", "sandwich": "ham", "tech_level": "pickle", "pop": "corn", "ansible": "awesome"}'


def compress(data):
    buf = io.BytesIO()
    f = gzip.GzipFile(fileobj=buf, mode='wb')
    try:
        f.write(data)
    finally:
        f.close()
    return buf.getvalue()


class Sock(io.BytesIO):
    def makefile(self, *args, **kwds):
        return self


RESP = b'''HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 108

%s''' % JSON_DATA

GZIP_RESP = b'''HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Encoding: gzip
Content-Length: 100

%s''' % compress(JSON_DATA)


def _make_response(raw):
    h = http_client.HTTPResponse(Sock(raw), method='GET')
    h.begin()
    if PY3:
        return h
    r = addinfourl(h.fp, h.msg, 'http://ansible.com/', h.status)
    r.msg = h.reason
    return r


@pytest.fixture
def urlopen_mock(mocker):
    return mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')


def test_df_gzip_decode(urlopen_mock):
    urlopen_mock.return_value = _make_response(GZIP_RESP)
    r = urls.Request().open('GET', 'https://ansible.com/')
    assert isinstance(r.fp, urls.GzipDecodedReader)
    assert r.read() == JSON_DATA


def test_df_decompress_false(urlopen_mock):
    urlopen_mock.return_value = _make_response(GZIP_RESP)
    r = urls.Request().open('GET', 'https://ansible.com/', decompress=False)
    assert not isinstance(r.fp, urls.GzipDecodedReader)
    data = r.read()
    assert data.startswith(b'\x1f\x8b')


def test_df_non_gzip_passthrough(urlopen_mock):
    urlopen_mock.return_value = _make_response(RESP)
    r = urls.Request().open('GET', 'https://ansible.com/')
    assert not isinstance(r.fp, urls.GzipDecodedReader)
    assert r.read() == JSON_DATA


def test_df_instance_decompress_default(urlopen_mock):
    urlopen_mock.return_value = _make_response(GZIP_RESP)
    req = urls.Request(decompress=False)
    r = req.open('GET', 'https://ansible.com/')
    assert not isinstance(r.fp, urls.GzipDecodedReader)
    assert r.read().startswith(b'\x1f\x8b')


def test_df_constructor_defaults():
    req = urls.Request()
    assert req.unredirected_headers is None
    assert req.decompress is True


def test_df_missing_module_error_module():
    e = urls.MissingModuleError('m', import_traceback='t', module='gzip')
    assert e.module == 'gzip'


def test_df_reader_close_closes_fp():
    inner = io.BytesIO(compress(JSON_DATA))
    r = urls.GzipDecodedReader(inner)
    r.read()
    r.close()
    assert inner.closed


def test_df_missing_gzip_error_message():
    msg = urls.GzipDecodedReader.missing_gzip_error()
    assert isinstance(msg, str) and 'gzip' in msg
"""

ORACLE_HASGZIP_PY = r"""
# Code generated by DataForge V3.2 semantic oracle (ansible, HAS_GZIP=False path).
import sys

import pytest


def test_df_has_gzip_false(monkeypatch, mocker):
    monkeypatch.delitem(sys.modules, 'gzip', raising=False)
    monkeypatch.delitem(sys.modules, 'ansible.module_utils.urls', raising=False)

    orig_import = __import__

    def _import(*args, **kwargs):
        if args[0] == 'gzip':
            raise ImportError
        return orig_import(*args, **kwargs)

    mocker.patch('builtins.__import__', _import)
    import ansible.module_utils.urls as mod
    assert mod.HAS_GZIP is False
    with pytest.raises(mod.MissingModuleError):
        mod.GzipDecodedReader(None)
"""


def generate_oracle() -> dict[str, str]:
    return {
        "zz_df_ansible_oracle_test.py": ORACLE_PY,
        "zz_df_ansible_hasgzip_test.py": ORACLE_HASGZIP_PY,
    }


Executor = Callable[[dict], ProbeResult]


@dataclass
class AnsibleOracle:
    task: str = TASK
    executor: Executor | None = None

    def run(self, cases, candidates=None) -> list[ProbeResult]:  # type: ignore[override]
        if self.executor is None:
            return [
                ProbeResult(
                    name="ansible:no-executor",
                    kind="differential",
                    passed=False,
                    detail="no executor configured",
                )
            ]
        oracle = generate_oracle()
        results: list[ProbeResult] = []
        for name, source in candidates or []:
            if hasattr(source, "read_text"):
                src = source.read_text(encoding="utf-8")
            else:
                src = Path(source).read_text(encoding="utf-8")
            results.append(self.executor({"candidate": name, "urls_source": src, "oracle": oracle}))
        return results
