#!/usr/bin/env python3
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def main() -> int:
    try:
        import server
    except Exception as exc:
        print(f"BACKEND_IMPORT=FAIL:{type(exc).__name__}:{exc}")
        traceback.print_exc()
        return 1

    app = getattr(server, "app", None)

    if app is None:
        print("BACKEND_APP=FAIL:MISSING_APP")
        return 1

    try:
        schema = app.openapi()
    except Exception as exc:
        print(f"OPENAPI=FAIL:{type(exc).__name__}:{exc}")
        return 1

    paths = set((schema.get("paths") or {}).keys())

    required_exact = {
        "/api/auth/login",
    }

    missing = sorted(required_exact - paths)

    if missing:
        print("BACKEND_ROUTE_SMOKE=FAIL")
        for path in missing:
            print(f"MISSING_ROUTE={path}")
        return 1

    health_candidates = {
        "/api/health",
        "/health",
        "/api/healthz",
        "/healthz",
    }

    if not paths.intersection(health_candidates):
        print("BACKEND_ROUTE_SMOKE=FAIL")
        print("MISSING_HEALTH_ROUTE=YES")
        return 1

    print("BACKEND_IMPORT=PASS")
    print("OPENAPI=PASS")
    print("AUTH_LOGIN_ROUTE=PASS")
    print("HEALTH_ROUTE=PASS")
    print("BACKEND_ROUTE_SMOKE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
