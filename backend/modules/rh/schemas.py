"""
EDARSA HUB - RH Schemas
=======================
Modelos Pydantic para recursos humanos.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class TipoIncidencia(str, Enum):
    FALTA = "falta"
    RETARDO = "retardo"
    PERMISO = "permiso"
    VACACIONES = "vacaciones"
    INCAPACIDAD = "incapacidad"
