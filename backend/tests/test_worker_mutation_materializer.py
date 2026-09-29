import hashlib
import pytest
from tools.mirror_sync.worker_mutation_materializer import apply_mutation

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def test_positive_and_replay(tmp_path):
    p=tmp_path/"a.py"
    p.write_text("a\\nanchor\\nz\\n")
    action={
        "type":"insert_after",
        "source_sha256":sha(p),
        "anchor":"anchor\\n",
        "expected_occurrences":1,
        "replacement":"new\\n",
    }
    assert apply_mutation(p,action)["state"]=="APPLIED"
    assert apply_mutation(p,action)["state"]=="ALREADY_APPLIED"
    assert p.read_text().count("new\\n")==1

def test_bad_sha_fail_closed(tmp_path):
    p=tmp_path/"a.py"
    p.write_text("anchor\\n")
    before=p.read_bytes()
    with pytest.raises(RuntimeError,match="SOURCE_SHA_MISMATCH"):
        apply_mutation(p,{
            "type":"insert_after",
            "source_sha256":"0"*64,
            "anchor":"anchor\\n",
            "replacement":"new\\n",
        })
    assert p.read_bytes()==before
