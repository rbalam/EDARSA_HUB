from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from datetime import date
from pathlib import Path


class ReportType(str, Enum):
    DETALLE_TRANSACCIONES = 'DETALLE_TRANSACCIONES'
    DETALLE_DEPOSITOS_MOVIMIENTOS = 'DETALLE_DEPOSITOS_MOVIMIENTOS'


class ExecutionStatus(str, Enum):
    INICIADO = 'INICIADO'
    LOGIN_OK = 'LOGIN_OK'
    LOGIN_FALLIDO = 'LOGIN_FALLIDO'
    MFA_REQUERIDO = 'MFA_REQUERIDO'
    CAPTCHA_DETECTADO = 'CAPTCHA_DETECTADO'
    EMPRESA_NO_COINCIDE = 'EMPRESA_NO_COINCIDE'
    NAVEGACION_OK = 'NAVEGACION_OK'
    GENERANDO_REPORTE = 'GENERANDO_REPORTE'
    DESCARGANDO = 'DESCARGANDO'
    DESCARGADO = 'DESCARGADO'
    VALIDANDO_LAYOUT = 'VALIDANDO_LAYOUT'
    LAYOUT_INVALIDO = 'LAYOUT_INVALIDO'
    IMPORTANDO_STAGING = 'IMPORTANDO_STAGING'
    NORMALIZANDO = 'NORMALIZANDO'
    COMPLETADO = 'COMPLETADO'
    COMPLETADO_CON_ALERTAS = 'COMPLETADO_CON_ALERTAS'
    FALLIDO = 'FALLIDO'


@dataclass
class DownloadResult:
    report_type: ReportType
    date_from: date
    date_to: date
    file_path: Path
    sha256: str
    original_name: str
