"""
Bootstrap minimo compartido para pytest de EDARSAHUB.

Responsabilidades:
- Cargar backend/.env antes de imports que resuelven SQL.
- Exponer constantes historicas requeridas por tests existentes.
- No contener credenciales literales.
- No restaurar MongoDB ni fixtures legacy.
"""

from pathlib import Path
import sys

from dotenv import load_dotenv


_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_ROOT / ".env"

# El repositorio tambien contiene /app/tests.
# Los tests del backend usan historicamente el contrato
# tests.test_config, por lo que backend debe tener precedencia.
_backend_root_text = str(_BACKEND_ROOT)
if sys.path[0] != _backend_root_text:
    if _backend_root_text in sys.path:
        sys.path.remove(_backend_root_text)
    sys.path.insert(0, _backend_root_text)

load_dotenv(_ENV_FILE, override=False)

from tests.test_config import TestConfig


TEST_ADMIN_EMAIL = TestConfig.TEST_ADMIN_EMAIL
TEST_ADMIN_PASSWORD = TestConfig.TEST_ADMIN_PASSWORD

TEST_SUPERADMIN_EMAIL = TestConfig.TEST_SUPERADMIN_EMAIL
TEST_SUPERADMIN_PASSWORD = TestConfig.TEST_SUPERADMIN_PASSWORD

TEST_USER_EMAIL = TestConfig.TEST_USER_EMAIL
TEST_USER_PASSWORD = TestConfig.TEST_USER_PASSWORD

TEST_SUPERVISOR_EMAIL = TestConfig.TEST_SUPERVISOR_EMAIL
TEST_SUPERVISOR_PASSWORD = TestConfig.TEST_SUPERVISOR_PASSWORD
