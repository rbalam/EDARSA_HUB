"""
Regresión AUTH-REFRESH (2026-06-09)
===================================
Blinda el flujo de refresco silencioso de sesión (E2E contra el backend vivo):
- login setea cookies (access + refresh)
- POST /auth/refresh con la cookie devuelve {token,...} (200) y el token es usable en /auth/me
- la rotación invalida el refresh anterior → reusar el token viejo da 401 (replay)

Si el backend no está accesible, los tests se omiten.
"""
import os
import pytest
import requests


# Las cookies de refresh son httpOnly + Secure → deben viajar por HTTPS.
# Usamos el URL externo (REACT_APP_BACKEND_URL), igual que el frontend real.
BACKEND = (os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")
EMAIL = os.environ.get("EDARSAHUB_TEST_AUTH_EMAIL")
PASSWORD = os.environ.get("EDARSAHUB_TEST_AUTH_PASSWORD")

if not EMAIL or not PASSWORD:
    pytest.skip(
        "E2E omitido: faltan EDARSAHUB_TEST_AUTH_EMAIL y "
        "EDARSAHUB_TEST_AUTH_PASSWORD",
        allow_module_level=True,
    )
def _login_session():
    s = requests.Session()
    try:
        r = s.post(f"{BACKEND}/api/auth/login",
                   json={"email": EMAIL, "password": PASSWORD}, timeout=15)
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Backend no disponible: {e}")
    if r.status_code != 200:
        pytest.skip(f"Login no disponible ({r.status_code})")
    assert "edarsa_refresh_token" in s.cookies.get_dict()
    return s


def test_refresh_devuelve_token_en_body():
    s = _login_session()
    r = s.post(f"{BACKEND}/api/auth/refresh", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("token"), "refresh debe devolver el nuevo access token en el body"
    assert body.get("expires_in")


def test_token_refrescado_es_valido_en_me():
    s = _login_session()
    tok = s.post(f"{BACKEND}/api/auth/refresh", timeout=15).json().get("token")
    me = requests.get(f"{BACKEND}/api/auth/me",
                      headers={"Authorization": f"Bearer {tok}"}, timeout=15)
    assert me.status_code == 200, me.text
    assert me.json().get("email") == EMAIL


def test_replay_del_refresh_token_viejo_es_rechazado():
    # cookies "viejas" tras una rotación deben quedar inválidas
    s = _login_session()
    old_cookies = s.cookies.copy()
    r1 = s.post(f"{BACKEND}/api/auth/refresh", timeout=15)  # rota (s ahora tiene cookie nueva)
    assert r1.status_code == 200
    # Reusar las cookies viejas en una sesión limpia → replay
    s2 = requests.Session()
    s2.cookies.update(old_cookies)
    r2 = s2.post(f"{BACKEND}/api/auth/refresh", timeout=15)
    assert r2.status_code == 401, "el refresh token rotado no debe seguir siendo válido"
