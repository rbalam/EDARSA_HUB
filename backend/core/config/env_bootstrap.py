"""
Bootstrap canonico de variables de entorno de EDARSAHUB.

Responsabilidad exclusiva:
- cargar backend/.env cuando exista;
- no sobrescribir variables ya presentes en el entorno;
- no validar configuracion de negocio;
- no abrir conexiones;
- no imprimir secretos.

La resolucion y validacion de configuracion permanece en
core.config.edarsahub_config.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = BACKEND_ROOT / ".env"


def load_edarsahub_environment(
    env_file: Path | None = None,
) -> Path:
    """
    Carga el entorno base de EDARSAHUB de forma idempotente.

    Las variables ya definidas por el proceso tienen precedencia
    sobre el archivo .env.
    """
    path = Path(env_file) if env_file else DEFAULT_ENV_FILE

    if path.is_file():
        load_dotenv(
            dotenv_path=path,
            override=False,
        )

    return path
