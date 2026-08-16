"""
Configuracion efectiva de Costos y Margenes.

Fuente unica:
- dbo.Comercial_CostosMargenesConfiguracion
- dbo.Comercial_CostosMargenesConfiguracionUsuario
- dbo.Unidades_Negocio
- dbo.Sistema_Empresas

Precedencia soportada por el esquema 027:
    usuario > unidad > empresa

Reglas:
- SQL EDARSAHUB solamente.
- Sin MongoDB.
- Sin POS live.
- Sin defaults funcionales inventados.
- Sin dependencia de Finanzas.
- La ausencia de configuracion permanece como None.
"""

from typing import Any, Dict, Optional

from core.sql_first.db import get_sql_connection
from core.connections.edarsahub_writer_connection import (
    open_validated_writer_connection,
)


CAMPOS_CONFIGURABLES = (
    "MargenMinimoPorcentaje",
    "MultiploRedondeo",
    "MetodoRedondeo",
)


def _fetchone(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    conn = get_sql_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def resolver_empresa_id_desde_unidad(
    unidad_negocio_pk: str,
) -> Optional[int]:
    """
    Resuelve EmpresaID desde Unidades_Negocio.id.

    La relacion existente y actualmente usada en EDARSAHUB es:
        Unidades_Negocio.codigo
            ->
        Sistema_Empresas.CodigoEmpresa

    No usa SucursalID, ServerID ni POS.
    """
    unidad_pk = str(unidad_negocio_pk or "").strip()
    if not unidad_pk:
        return None

    row = _fetchone(
        """
        SELECT TOP 1
            e.EmpresaID
        FROM dbo.Unidades_Negocio u
        INNER JOIN dbo.Sistema_Empresas e
            ON UPPER(LTRIM(RTRIM(e.CodigoEmpresa)))
             = UPPER(LTRIM(RTRIM(u.codigo)))
        WHERE CONVERT(varchar(36), u.id) = %s
          AND ISNULL(u.activo, 1) = 1
          AND ISNULL(e.Activo, 1) = 1
        """,
        (unidad_pk,),
    )

    if not row or row.get("EmpresaID") is None:
        return None

    return int(row["EmpresaID"])


def _leer_config_empresa(
    empresa_id: int,
) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT TOP 1
            ConfiguracionID,
            EmpresaID,
            UnidadNegocioID,
            MargenMinimoPorcentaje,
            MultiploRedondeo,
            MetodoRedondeo
        FROM dbo.Comercial_CostosMargenesConfiguracion
        WHERE EmpresaID = %s
          AND UnidadNegocioID IS NULL
          AND Activo = 1
        """,
        (empresa_id,),
    )


def _leer_config_unidad(
    empresa_id: int,
    unidad_negocio_pk: str,
) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT TOP 1
            ConfiguracionID,
            EmpresaID,
            UnidadNegocioID,
            MargenMinimoPorcentaje,
            MultiploRedondeo,
            MetodoRedondeo
        FROM dbo.Comercial_CostosMargenesConfiguracion
        WHERE EmpresaID = %s
          AND UnidadNegocioID = CONVERT(uniqueidentifier, %s)
          AND Activo = 1
        """,
        (empresa_id, unidad_negocio_pk),
    )


def _leer_config_usuario(
    usuario_id: int,
) -> Optional[Dict[str, Any]]:
    return _fetchone(
        """
        SELECT TOP 1
            ConfiguracionUsuarioID,
            UsuarioID,
            MargenMinimoPorcentaje,
            MultiploRedondeo,
            MetodoRedondeo
        FROM dbo.Comercial_CostosMargenesConfiguracionUsuario
        WHERE UsuarioID = %s
          AND Activo = 1
        """,
        (usuario_id,),
    )



def guardar_configuracion_usuario(
    usuario_id: int,
    cambios: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Persiste overrides personales de Costos/Márgenes.

    Semántica PATCH atómica:
    - clave ausente: conserva el valor persistido;
    - clave presente con None: elimina ese override;
    - clave presente con valor: sustituye ese override.

    La lectura del estado actual y la escritura ocurren sobre la
    misma conexión/transacción para evitar lost updates derivados
    de una lectura previa en otra conexión.
    """
    if (
        not isinstance(usuario_id, int)
        or isinstance(usuario_id, bool)
        or usuario_id <= 0
    ):
        raise ValueError("USUARIO_ID_INVALIDO")

    permitidos = set(CAMPOS_CONFIGURABLES)
    recibidos = set(cambios)

    desconocidos = recibidos - permitidos
    if desconocidos:
        raise ValueError(
            "CAMPOS_CONFIGURACION_NO_PERMITIDOS:"
            + ",".join(sorted(desconocidos))
        )

    if not recibidos:
        raise ValueError("SIN_CAMBIOS_CONFIGURACION")

    conn, writer_identity = (
        open_validated_writer_connection()
    )

    try:
        cur = conn.cursor(as_dict=True)

        cur.execute(
            """
            SELECT TOP 1
                ConfiguracionUsuarioID,
                MargenMinimoPorcentaje,
                MultiploRedondeo,
                MetodoRedondeo
            FROM dbo.Comercial_CostosMargenesConfiguracionUsuario
            WITH (UPDLOCK, HOLDLOCK)
            WHERE UsuarioID = %s
              AND Activo = 1
            """,
            (usuario_id,),
        )

        existente = cur.fetchone()
        actual = dict(existente) if existente else {}

        valores = {
            campo: (
                cambios[campo]
                if campo in cambios
                else actual.get(campo)
            )
            for campo in CAMPOS_CONFIGURABLES
        }

        if existente:
            cur.execute(
                """
                UPDATE dbo.Comercial_CostosMargenesConfiguracionUsuario
                SET
                    MargenMinimoPorcentaje = %s,
                    MultiploRedondeo = %s,
                    MetodoRedondeo = %s,
                    FechaModificacion = SYSDATETIME()
                WHERE ConfiguracionUsuarioID = %s
                  AND UsuarioID = %s
                  AND Activo = 1
                """,
                (
                    valores["MargenMinimoPorcentaje"],
                    valores["MultiploRedondeo"],
                    valores["MetodoRedondeo"],
                    existente["ConfiguracionUsuarioID"],
                    usuario_id,
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO dbo.Comercial_CostosMargenesConfiguracionUsuario (
                    UsuarioID,
                    MargenMinimoPorcentaje,
                    MultiploRedondeo,
                    MetodoRedondeo,
                    Activo
                )
                VALUES (%s, %s, %s, %s, 1)
                """,
                (
                    usuario_id,
                    valores["MargenMinimoPorcentaje"],
                    valores["MultiploRedondeo"],
                    valores["MetodoRedondeo"],
                ),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return _leer_config_usuario(usuario_id)

def resolver_configuracion_efectiva(
    unidad_negocio_pk: str,
    usuario_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Resuelve configuracion efectiva con precedencia por campo:

        usuario > unidad > empresa

    Un NULL no pisa un valor heredado.

    Si ningun nivel define un campo, el resultado permanece None.
    No existen fallbacks funcionales hardcodeados.
    """
    unidad_pk = str(unidad_negocio_pk or "").strip()

    if not unidad_pk:
        raise ValueError("UNIDAD_NEGOCIO_PK_REQUERIDA")

    empresa_id = resolver_empresa_id_desde_unidad(unidad_pk)

    if empresa_id is None:
        raise ValueError("EMPRESA_NO_RESUELTA_DESDE_UNIDAD")

    config_empresa = _leer_config_empresa(empresa_id)
    config_unidad = _leer_config_unidad(empresa_id, unidad_pk)
    config_usuario = (
        _leer_config_usuario(int(usuario_id))
        if usuario_id is not None
        else None
    )

    niveles = (
        ("EMPRESA", config_empresa),
        ("UNIDAD", config_unidad),
        ("USUARIO", config_usuario),
    )

    valores: Dict[str, Any] = {
        campo: None
        for campo in CAMPOS_CONFIGURABLES
    }

    fuentes: Dict[str, Optional[str]] = {
        campo: None
        for campo in CAMPOS_CONFIGURABLES
    }

    for nivel, config in niveles:
        if not config:
            continue

        for campo in CAMPOS_CONFIGURABLES:
            valor = config.get(campo)

            if valor is not None:
                valores[campo] = valor
                fuentes[campo] = nivel

    return {
        "empresa_id": empresa_id,
        "unidad_negocio_pk": unidad_pk,
        "usuario_id": usuario_id,
        "margen_minimo_porcentaje": valores["MargenMinimoPorcentaje"],
        "multiplo_redondeo": valores["MultiploRedondeo"],
        "metodo_redondeo": valores["MetodoRedondeo"],
        "fuentes": {
            "margen_minimo_porcentaje": fuentes["MargenMinimoPorcentaje"],
            "multiplo_redondeo": fuentes["MultiploRedondeo"],
            "metodo_redondeo": fuentes["MetodoRedondeo"],
        },
    }
