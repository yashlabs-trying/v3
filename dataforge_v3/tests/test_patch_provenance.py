from __future__ import annotations

from dataforge_v3.model import PatchVerdict
from dataforge_v3.patch.provenance import BaselineState, analyze_provenance
from dataforge_v3.patch.validation import parse_patch, patch_identity, sha256_bytes, sha256_text

REDIS = """diff --git a/appendonlydir/appendonly.aof.1.incr.aof b/appendonlydir/appendonly.aof.1.incr.aof
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/appendonlydir/appendonly.aof.1.incr.aof
@@ -0,0 +1,2 @@
+*2
+$6
"""

NEW_FILE = """diff --git a/src/posts/cache.js b/src/posts/cache.js
new file mode 100644
index 0000000..2222222
--- /dev/null
+++ b/src/posts/cache.js
@@ -0,0 +1 @@
+module.exports = {};
"""

MODIFY = """diff --git a/src/meta/index.js b/src/meta/index.js
index 3333333..4444444 100644
--- a/src/meta/index.js
+++ b/src/meta/index.js
@@ -1,2 +1,2 @@
-old
+new
 keep
"""

DELETE = """diff --git a/src/old.js b/src/old.js
deleted file mode 100644
index 5555555..0000000
--- a/src/old.js
+++ /dev/null
@@ -1 +0,0 @@
-gone
"""

RENAME = """diff --git a/src/a.js b/src/b.js
similarity index 100%
rename from src/a.js
rename to src/b.js
"""

BINARY_NEW = """diff --git a/assets/logo.png b/assets/logo.png
new file mode 100644
index 0000000..6666666
Binary files /dev/null and b/assets/logo.png differ
"""

TEST_FILE = """diff --git a/models/vulninfos_test.go b/models/vulninfos_test.go
index 7777777..8888888 100644
--- a/models/vulninfos_test.go
+++ b/models/vulninfos_test.go
@@ -1 +1 @@
-x
+y
"""


def test_preexisting_redis_artifacts_are_detected_and_excluded():
    baseline = BaselineState(untracked={"appendonlydir/appendonly.aof.1.incr.aof"})
    analysis = parse_patch(REDIS)
    record, provenance, filtered, accepted = analyze_provenance(analysis, baseline)
    assert record.verdict is PatchVerdict.CONTAMINATED_ONLY
    assert accepted == []
    assert filtered == ""
    assert provenance["excluded"][0]["kind"] == "PREEXISTING_UNTRACKED"


def test_legitimate_new_file_is_accepted():
    analysis = parse_patch(NEW_FILE)
    record, _, filtered, accepted = analyze_provenance(analysis, BaselineState())
    assert record.verdict is PatchVerdict.VALID
    assert accepted == ["src/posts/cache.js"]
    assert "new file mode" in filtered


def test_existing_file_modification_is_accepted():
    record, _, _, accepted = analyze_provenance(parse_patch(MODIFY), BaselineState(tracked={"src/meta/index.js"}))
    assert record.verdict is PatchVerdict.VALID
    assert accepted == ["src/meta/index.js"]


def test_deletion_and_rename_are_accepted():
    record, _, _, accepted = analyze_provenance(parse_patch(DELETE), BaselineState(tracked={"src/old.js"}))
    assert record.verdict is PatchVerdict.VALID
    assert accepted == ["src/old.js"]
    record, _, _, accepted = analyze_provenance(parse_patch(RENAME), BaselineState(tracked={"src/a.js"}))
    assert record.verdict is PatchVerdict.VALID
    assert accepted == ["src/b.js"]


def test_malformed_patch_is_invalid():
    record, _, _, _ = analyze_provenance(parse_patch("this is not a patch\n"), BaselineState())
    assert record.verdict is PatchVerdict.INVALID


def test_path_escape_is_invalid():
    bad = """diff --git a/../etc/passwd b/../etc/passwd
--- a/../etc/passwd
+++ b/../etc/passwd
@@ -1 +1 @@
-x
+y
"""
    record, _, _, _ = analyze_provenance(parse_patch(bad), BaselineState())
    assert record.verdict is PatchVerdict.INVALID


def test_symlink_is_invalid():
    link = """diff --git a/link b/link
new file mode 120000
index 0000000..9999999
--- /dev/null
+++ b/link
@@ -0,0 +1 @@
+/etc/passwd
"""
    record, _, _, _ = analyze_provenance(parse_patch(link), BaselineState())
    assert record.verdict is PatchVerdict.INVALID
    assert any("symlink" in r for r in record.reasons)


def test_duplicate_paths_are_invalid():
    twice = NEW_FILE + NEW_FILE
    record, _, _, _ = analyze_provenance(parse_patch(twice), BaselineState())
    assert record.verdict is PatchVerdict.INVALID


def test_binary_preexisting_is_contamination_not_review():
    data = """diff --git a/state.db b/state.db
new file mode 100644
index 0000000..abcdef0
Binary files /dev/null and b/state.db differ
"""
    record, provenance, _, accepted = analyze_provenance(parse_patch(data), BaselineState(untracked={"state.db"}))
    assert record.verdict is PatchVerdict.CONTAMINATED_ONLY
    assert accepted == []


def test_binary_new_addition_requires_review():
    record, provenance, _, _ = analyze_provenance(parse_patch(BINARY_NEW), BaselineState())
    assert record.verdict is PatchVerdict.REVIEW_REQUIRED
    assert provenance["review_required"] == ["assets/logo.png"]


def test_filtered_patch_removes_contaminants_only():
    combined = REDIS + NEW_FILE + MODIFY
    baseline = BaselineState(
        tracked={"src/meta/index.js"},
        untracked={"appendonlydir/appendonly.aof.1.incr.aof"},
    )
    record, _, filtered, accepted = analyze_provenance(parse_patch(combined), baseline)
    assert record.verdict is PatchVerdict.VALID
    assert set(accepted) == {"src/posts/cache.js", "src/meta/index.js"}
    assert "appendonlydir" not in filtered
    assert "src/posts/cache.js" in filtered


def test_test_file_touch_is_flagged_but_scoped():
    record, provenance, _, accepted = analyze_provenance(parse_patch(TEST_FILE), BaselineState(tracked={"models/vulninfos_test.go"}))
    assert record.verdict is PatchVerdict.VALID
    assert accepted == ["models/vulninfos_test.go"]
    assert provenance["test_files_touched"] == ["models/vulninfos_test.go"]


def test_crlf_patch_normalizes_to_identical_hash():
    lf = parse_patch(MODIFY)
    crlf = parse_patch(MODIFY.replace("\n", "\r\n"))
    assert crlf.sha256 == lf.sha256
    assert "\r" not in crlf.raw
    assert crlf.entries[0].path == "src/meta/index.js"


def test_patch_identity_prefers_lf_for_pure_crlf_checkout():
    raw = MODIFY.replace("\n", "\r\n").encode("utf-8")
    identity = patch_identity(raw)
    assert identity.eol == "crlf"
    assert identity.raw_sha256 != identity.lf_sha256
    assert identity.canonical_sha256 == sha256_text(MODIFY)


def test_patch_identity_keeps_raw_for_genuine_mixed_content():
    raw = ("line one\r\nline two\nline three\r\n").encode("utf-8")
    identity = patch_identity(raw)
    assert identity.eol == "mixed"
    assert identity.canonical_sha256 == sha256_bytes(raw)
