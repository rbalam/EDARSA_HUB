from __future__ import annotations

import hashlib

import pytest

from tools.mirror_sync.worker_mutation_materializer import apply_mutation


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_insert_after_positive_and_replay(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("a\nanchor\nz\n", encoding="utf-8")

    action = {
        "type": "insert_after",
        "source_sha256": sha(p),
        "anchor": "anchor\n",
        "expected_occurrences": 1,
        "replacement": "new\n",
    }

    first = apply_mutation(p, action)
    second = apply_mutation(p, action)

    assert first["state"] == "APPLIED"
    assert first["source_integrity_valid"] is True
    assert first["transformation_applied"] is True
    assert first["final_sha256"] == sha(p)

    assert second["state"] == "ALREADY_APPLIED"
    assert second["transformation_applied"] is False
    assert second["duplicate_mutation"] is False

    assert p.read_text(encoding="utf-8") == (
        "a\nanchor\nnew\nz\n"
    )


def test_bad_sha_fail_closed(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("anchor\n", encoding="utf-8")
    before = p.read_bytes()

    with pytest.raises(RuntimeError, match="SOURCE_SHA_MISMATCH"):
        apply_mutation(
            p,
            {
                "type": "insert_after",
                "source_sha256": "0" * 64,
                "anchor": "anchor\n",
                "expected_occurrences": 1,
                "replacement": "new\n",
            },
        )

    assert p.read_bytes() == before


def test_anchor_not_found(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("a\nz\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="ANCHOR_NOT_FOUND"):
        apply_mutation(
            p,
            {
                "type": "insert_before",
                "source_sha256": sha(p),
                "anchor": "missing\n",
                "expected_occurrences": 1,
                "replacement": "new\n",
            },
        )


def test_occurrence_mismatch(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("anchor\nanchor\n", encoding="utf-8")

    with pytest.raises(
        RuntimeError, match="ANCHOR_OCCURRENCE_MISMATCH"
    ):
        apply_mutation(
            p,
            {
                "type": "insert_after",
                "source_sha256": sha(p),
                "anchor": "anchor\n",
                "expected_occurrences": 1,
                "replacement": "new\n",
            },
        )


def test_append_once(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("a\n", encoding="utf-8")

    action = {
        "type": "append_once",
        "source_sha256": sha(p),
        "expected_occurrences": 1,
        "replacement": "z\n",
    }

    assert apply_mutation(p, action)["state"] == "APPLIED"
    assert apply_mutation(p, action)["state"] == "ALREADY_APPLIED"
    assert p.read_text(encoding="utf-8") == "a\nz\n"


def test_replace_text(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("alpha old omega\n", encoding="utf-8")

    result = apply_mutation(
        p,
        {
            "type": "replace_text",
            "source_sha256": sha(p),
            "old_text": "old",
            "expected_occurrences": 1,
            "replacement": "new",
        },
    )

    assert result["state"] == "APPLIED"
    assert result["operation"] == "replace_text"
    assert p.read_text(encoding="utf-8") == "alpha new omega\n"
