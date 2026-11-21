from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLIENT = (ROOT / "frontend/src/portal-inteligencia/api/client.js").read_text(encoding="utf-8")
CENTRAL = (ROOT / "frontend/src/lib/api.js").read_text(encoding="utf-8")


def test_portal_inteligencia_preserves_central_refresh_retry_for_internal_sessions():
    assert "import api, { getToken } from '../../lib/api';" in CLIENT
    assert "const client = getToken() ? api : intelApi;" in CLIENT
    assert "coordinatedRefresh" in CENTRAL


def test_portal_requests_restore_timeout_above_central_15s_regression():
    assert "const INTEL_REQUEST_TIMEOUT_MS = 60000;" in CLIENT
    assert "client.get(path, { params, timeout: INTEL_REQUEST_TIMEOUT_MS })" in CLIENT
    assert "axios.create({ baseURL: API_URL, withCredentials: true, timeout: INTEL_REQUEST_TIMEOUT_MS })" in CLIENT


def test_portal_post_default_timeout_allows_explicit_larger_override():
    assert "client.post(path, payload, { timeout: INTEL_REQUEST_TIMEOUT_MS, ...config })" in CLIENT
    assert "{ timeout: 120000 }" in (ROOT / "frontend/src/portal-inteligencia/pages/ReportesISCAMPage.jsx").read_text(encoding="utf-8")


def test_central_client_can_remain_15s_without_reintroducing_portal_timeout():
    assert "timeout: 15000" in CENTRAL
