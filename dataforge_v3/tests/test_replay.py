from __future__ import annotations

from dataforge_v3.model import PatchVerdict, VerificationStatus
from dataforge_v3.replay.controller import (
    AcceptedChange,
    assess_post_state,
    decide_replay,
    parse_porcelain,
)


def test_patch_application_failure_cannot_be_authoritative():
    status, reasons = decide_replay(
        patch_verdict=PatchVerdict.VALID, apply_rc=1, accepted_count=7, post_state=None
    )
    assert status is VerificationStatus.PATCH_APPLICATION_ERROR
    assert reasons


def test_partial_application_is_rejected():
    accepted = [AcceptedChange("a.py"), AcceptedChange("b.py")]
    post = assess_post_state(accepted, " M a.py\n?? appendonlydir/x\n", {"appendonlydir/x"})
    assert not post.ok
    status, _ = decide_replay(
        patch_verdict=PatchVerdict.VALID, apply_rc=0, accepted_count=2, post_state=post
    )
    assert status is VerificationStatus.PATCH_APPLICATION_ERROR


def test_successful_application_is_valid():
    accepted = [AcceptedChange("a.py"), AcceptedChange("new.js", is_new=True)]
    post = assess_post_state(accepted, " M a.py\n?? new.js\n?? appendonlydir/x\n", {"appendonlydir/x"})
    assert post.ok
    status, reasons = decide_replay(
        patch_verdict=PatchVerdict.VALID, apply_rc=0, accepted_count=2, post_state=post
    )
    assert status is VerificationStatus.VALID
    assert reasons == []


def test_unexpected_touch_is_rejected():
    accepted = [AcceptedChange("a.py")]
    post = assess_post_state(accepted, " M a.py\n M evil.py\n", set())
    assert post.unexpected == ["evil.py"]
    status, _ = decide_replay(
        patch_verdict=PatchVerdict.VALID, apply_rc=0, accepted_count=1, post_state=post
    )
    assert status is VerificationStatus.PATCH_APPLICATION_ERROR


def test_contaminated_only_patch_never_replays():
    status, _ = decide_replay(
        patch_verdict=PatchVerdict.CONTAMINATED_ONLY, apply_rc=0, accepted_count=0, post_state=None
    )
    assert status is VerificationStatus.PATCH_INVALID


def test_empty_submission_has_explicit_semantics():
    status, reasons = decide_replay(
        patch_verdict=PatchVerdict.EMPTY, apply_rc=None, accepted_count=0, post_state=None
    )
    assert status is VerificationStatus.PATCH_EMPTY
    assert reasons


def test_porcelain_rename_parsing():
    assert parse_porcelain("R  a -> b") == ["a", "b"]
