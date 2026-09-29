from __future__ import annotations
import hashlib
from pathlib import Path

V2_ACTIONS={"insert_before","insert_after","append_once"}

def apply_mutation(target:Path,action:dict):
    raw=target.read_bytes()
    actual=hashlib.sha256(raw).hexdigest()
    expected=str(action["source_sha256"])
    text=raw.decode("utf-8")
    replacement=str(action["replacement"])
    kind=str(action["type"])
    anchor=action.get("anchor")

    if kind=="append_once" and replacement in text:
        return {"state":"ALREADY_APPLIED","final_sha256":actual}

    if anchor and (
        (kind=="insert_before" and replacement+anchor in text) or
        (kind=="insert_after" and anchor+replacement in text)
    ):
        return {"state":"ALREADY_APPLIED","final_sha256":actual}

    if actual!=expected:
        raise RuntimeError("SOURCE_SHA_MISMATCH")

    expected_count=int(action.get("expected_occurrences",1))

    if kind=="append_once":
        new=text+replacement
    else:
        count=text.count(anchor)
        if count!=expected_count:
            raise RuntimeError("ANCHOR_OCCURRENCE_MISMATCH")
        if kind=="insert_before":
            new=text.replace(anchor,replacement+anchor)
        elif kind=="insert_after":
            new=text.replace(anchor,anchor+replacement)
        else:
            raise RuntimeError("UNSUPPORTED_V2_ACTION")

    target.write_text(new,encoding="utf-8")
    return {
        "state":"APPLIED",
        "final_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
    }
