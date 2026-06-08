"""
UnidadesService - Servicio centralizado de Unidades de Negocio
=============================================================
P1 (2026-06-05): Actualizado para usar unidad_negocio_pk real (UNIQUEIDENTIFIER)

Proporciona:
- get_all(): Lista completa con PK, código y nombre
- get_pks(): Lista de PKs reales (UNIQUEIDENTIFIER)
- get_codigos(): Lista de códigos (para compatibilidad legacy)
- get_by_pk(): Buscar por PK real
- get_by_codigo(): Buscar por código
- resolver_pk(): Resolver PK desde cualquier valor (PK, código o nombre)
- resolver_codigo(): Resolver código desde cualquier valor
"""
import os
import time
import logging

logger = logging.getLogger(__name__)

_CACHE = {
    "ts": 0,
    "ttl": 300,
    "data": None
}

class UnidadesService:
    # Variantes legacy para compatibilidad con datos históricos
    _VARIANTES_MAP = {
        # Mérida
        '130-MER': '130MID', '130-MID': '130MID', '130MER': '130MID',
        '130 MERIDA': '130MID', '130 MÉRIDA': '130MID',
        '130° MERIDA': '130MID', '130° MÉRIDA': '130MID',
        'MERIDA': '130MID', 'MÉRIDA': '130MID', '130MID': '130MID',
        # Querétaro
        '130-QRO': '130QRO', '130 QRO': '130QRO',
        '130 QUERETARO': '130QRO', '130 QUERÉTARO': '130QRO',
        '130° QUERETARO': '130QRO', '130° QUERÉTARO': '130QRO',
        'QUERETARO': '130QRO', 'QUERÉTARO': '130QRO', '130QRO': '130QRO',
        # Cienfuegos
        'CIENFUEGOS': 'CIENFUEGOS',
        # Estelar
        'LA-ESTELAR': 'ESTELAR', 'LA ESTELAR': 'ESTELAR',
        'ESTELAR': 'ESTELAR',
        # Origen
        'ORIGEN': 'ORIGEN',
    }
    @staticmethod
    def _get_connection():
        """Obtiene conexión usando el pool del backend"""
        from modules.comercial_v2.repository_comercial_edarsahub import EDARSAHUB_CONFIG
        from core.db import execute_sql_query
        return EDARSAHUB_CONFIG, execute_sql_query

    @classmethod
    def clear_cache(cls):
        _CACHE["data"] = None
        _CACHE["ts"] = 0

    @classmethod
    def get_all(cls):
        """Retorna todas las unidades activas con PK real"""
        now = time.time()
        if _CACHE["data"] is not None and now - _CACHE["ts"] < _CACHE["ttl"]:
            return _CACHE["data"]

        try:
            config, execute_sql = cls._get_connection()
            sql = """
                SELECT
                    CONVERT(varchar(36), id) AS unidad_negocio_pk,
                    CONVERT(varchar(36), id) AS unidad_negocio_pk_real,
                    codigo AS unidad_negocio_codigo,
                    codigo,
                    nombre AS unidad_negocio_nombre,
                    nombre,
                    CONVERT(varchar(36), server_id) AS server_id,
                    system_type,
                    system_type AS sistema,
                    sucursal_origen_id,
                    activo
                FROM dbo.Unidades_Negocio
                WHERE ISNULL(activo, 1) = 1
                ORDER BY nombre
            """
            rows = execute_sql(
                config['host'],
                config['port'],
                config['database'],
                config['username'],
                config['password'],
                sql
            )
            _CACHE["data"] = rows
            _CACHE["ts"] = now
            return rows
        except Exception as e:
            logger.error(f"[UNIDADES_SERVICE] Error cargando unidades: {e}")
            # Fallback a caché si existe
            if _CACHE["data"]:
                return _CACHE["data"]
            return []

    @classmethod
    def get_pks(cls):
        """Retorna lista de PKs reales (UNIQUEIDENTIFIER como string)"""
        return [u.get("unidad_negocio_pk") for u in cls.get_all() if u.get("unidad_negocio_pk")]

    @classmethod
    def get_ids(cls):
        """Compatibilidad: devuelve PKs reales"""
        return cls.get_pks()

    @classmethod
    def get_codigos(cls):
        """Retorna lista de códigos (para compatibilidad legacy)"""
        return [u.get("codigo") for u in cls.get_all() if u.get("codigo")]

    @classmethod
    def get_codigos_set(cls):
        """Retorna set de códigos en mayúsculas para búsqueda rápida"""
        return {u.get("codigo", "").upper().strip() for u in cls.get_all() if u.get("codigo")}

    @classmethod
    def get_by_pk(cls, unidad_negocio_pk):
        """Buscar unidad por PK real"""
        if not unidad_negocio_pk:
            return None
        uid = str(unidad_negocio_pk).strip()
        return next((u for u in cls.get_all() if str(u.get("unidad_negocio_pk", "")).strip() == uid), None)

    @classmethod
    def get_by_id(cls, unidad_negocio_pk):
        """Compatibilidad: acepta PK real"""
        return cls.get_by_pk(unidad_negocio_pk)

    @classmethod
    def get_by_codigo(cls, codigo):
        """Buscar unidad por código"""
        if not codigo:
            return None
        c = str(codigo).strip().upper()
        return next((u for u in cls.get_all() if str(u.get("codigo", "")).strip().upper() == c), None)

    @classmethod
    def resolver_pk(cls, valor):
        """Resolver PK desde cualquier valor (PK, código o nombre)"""
        if valor is None:
            return None
        v = str(valor).strip()
        vu = v.upper()
        for u in cls.get_all():
            if str(u.get("unidad_negocio_pk", "")).strip() == v:
                return u["unidad_negocio_pk"]
            if str(u.get("codigo", "")).strip().upper() == vu:
                return u["unidad_negocio_pk"]
            if str(u.get("nombre", "")).strip().upper() == vu:
                return u["unidad_negocio_pk"]
        return None

    @classmethod
    def resolver_codigo(cls, valor):
        """Resolver código desde cualquier valor"""
        if valor is None:
            return None
        v = str(valor).strip()
        vu = v.upper()
        for u in cls.get_all():
            if str(u.get("unidad_negocio_pk", "")).strip() == v:
                return u["codigo"]
            if str(u.get("codigo", "")).strip().upper() == vu:
                return u["codigo"]
            if str(u.get("nombre", "")).strip().upper() == vu:
                return u["codigo"]
        return None

    @classmethod
    def get_nombre(cls, valor):
        """Obtener nombre legible desde cualquier valor"""
        if valor is None:
            return None
        v = str(valor).strip()
        vu = v.upper()
        for u in cls.get_all():
            if str(u.get("unidad_negocio_pk", "")).strip() == v:
                return u["nombre"]
            if str(u.get("codigo", "")).strip().upper() == vu:
                return u["nombre"]
            if str(u.get("nombre", "")).strip().upper() == vu:
                return u["nombre"]
        return v  # Retornar valor original si no encuentra
