from pathlib import Path


SERVER = Path(__file__).resolve().parents[1] / "server.py"


def test_root_health_alias_reuses_canonical_health_handler():
    source = SERVER.read_text(encoding="utf-8")
    canonical = '@app.get("/api/health")\n@app.get("/health")\nasync def health_check():'
    assert canonical in source
    assert source.count('async def health_check():') == 1
    assert source.count('@app.get("/api/health")') == 1
    assert source.count('@app.get("/health")') == 1
