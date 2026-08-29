import os
import json
import argparse
from datetime import datetime
from typing import Any, Dict, Optional

import pymssql
# from pymongo import MongoClient  # P5: legacy migration only


def env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Falta variable de entorno requerida: {name}")
    return value


def get_mongo_client() -> MongoClient:  # noqa: F821
    mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or os.getenv("MONGO_URL")
    if not mongo_uri:
        raise RuntimeError("No existe MONGO_URI, MONGODB_URI ni MONGO_URL para migración controlada")
    return MongoClient(mongo_uri)  # noqa: F821


def get_sql_conn():
    host = env("EDARSAHUB_SQL_HOST")
    port = int(os.getenv("EDARSAHUB_SQL_PORT", "1433"))
    db = env("EDARSAHUB_SQL_DATABASE")
    user = env("EDARSAHUB_SQL_USER")
    password = env("EDARSAHUB_SQL_PASSWORD")

    return pymssql.connect(
        server=host,
        port=port,
        user=user,
        password=password,
        database=db,
        charset='UTF-8'
    )


def safe_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps({"_raw": str(value)}, ensure_ascii=False)


def str_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def parse_dt(value: Any):
    if value in (None, "", "null"):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def upsert_consulta(cur, collection_name: str, doc: Dict[str, Any], dry_run: bool):
    legacy_id = str(doc.get("_id"))
    tipo = "QUERY" if collection_name == "queries" else "CUSTOM"

    nombre = (
        doc.get("nombre")
        or doc.get("name")
        or doc.get("titulo")
        or f"{tipo}_{legacy_id}"
    )

    codigo = doc.get("codigo") or doc.get("code")
    descripcion = doc.get("descripcion") or doc.get("description")
    categoria = doc.get("categoria")
    modulo = doc.get("modulo")
    system_type = doc.get("system_type") or doc.get("sistema")
    empresa_id = doc.get("empresa_id")
    unidad_negocio_id = doc.get("unidad_negocio_id")
    sucursal_id = doc.get("sucursal_id")
    server_id = doc.get("server_id")
    query_sql = doc.get("sql") or doc.get("query") or doc.get("query_sql")
    parametros_json = safe_json(doc.get("parametros") or doc.get("params") or doc.get("parametros_json"))
    configuracion_json = safe_json(doc)
    es_publica = 1 if doc.get("es_publica") or doc.get("publica") else 0
    activa = 0 if doc.get("deleted") or doc.get("activo") is False else 1
    created_by = str_or_none(doc.get("created_by") or doc.get("usuario") or "MIGRACION_MONGO")
    created_at = parse_dt(doc.get("created_at") or doc.get("fecha_creacion")) or datetime.now()

    if not query_sql:
        return False, f"Consulta sin SQL real: {legacy_id}"

    sql_exists = "SELECT ConsultaSQLID FROM Sistema_ConsultasSQL WHERE LegacyMongoID = ?"
    cur.execute(sql_exists, legacy_id)
    row = cur.fetchone()

    if row:
        if not dry_run:
            cur.execute(
                """
                UPDATE Sistema_ConsultasSQL
                SET TipoConsulta = ?, NombreConsulta = ?, CodigoConsulta = ?, Descripcion = ?,
                    Categoria = ?, Modulo = ?, SystemType = ?, EmpresaID = ?, UnidadNegocioID = ?,
                    SucursalID = ?, ServerID = ?, QuerySQL = ?, ParametrosJSON = ?, ConfiguracionJSON = ?,
                    EsPublica = ?, Activa = ?, LegacyCollection = ?, MigratedAt = SYSDATETIME(),
                    UpdatedAt = SYSDATETIME(), UpdatedBy = ?
                WHERE LegacyMongoID = ?
                """,
                tipo, nombre, codigo, descripcion,
                categoria, modulo, system_type, empresa_id, unidad_negocio_id,
                sucursal_id, server_id, query_sql, parametros_json, configuracion_json,
                es_publica, activa, collection_name, "MIGRACION_MONGO", legacy_id
            )
        return True, f"UPDATED consulta {legacy_id}"

    if not dry_run:
        cur.execute(
            """
            INSERT INTO Sistema_ConsultasSQL (
                TipoConsulta, NombreConsulta, CodigoConsulta, Descripcion, Categoria, Modulo,
                SystemType, EmpresaID, UnidadNegocioID, SucursalID, ServerID,
                QuerySQL, ParametrosJSON, ConfiguracionJSON, EsPublica, Activa,
                CreatedAt, CreatedBy, LegacyMongoID, LegacyCollection, MigratedAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME())
            """,
            tipo, nombre, codigo, descripcion, categoria, modulo,
            system_type, empresa_id, unidad_negocio_id, sucursal_id, server_id,
            query_sql, parametros_json, configuracion_json, es_publica, activa,
            created_at, created_by, legacy_id, collection_name
        )
    return True, f"INSERTED consulta {legacy_id}"


def upsert_script(cur, doc: Dict[str, Any], dry_run: bool):
    legacy_id = str(doc.get("_id"))
    nombre = doc.get("titulo") or doc.get("nombre") or f"SCRIPT_{legacy_id}"
    descripcion = doc.get("descripcion") or nombre
    tipo_script = doc.get("tipo_script") or "SQL"
    estado = doc.get("estado") or doc.get("status") or "PENDIENTE"
    prioridad = doc.get("prioridad") or "MEDIA"
    modulo = doc.get("modulo") or "EXPLORADOR_BD"
    empresa_id = doc.get("empresa_id")
    unidad_negocio_id = doc.get("unidad_negocio_id")
    sucursal_id = doc.get("sucursal_id")
    server_id = doc.get("server_id")
    contenido = doc.get("script") or doc.get("contenido_script")
    parametros_json = safe_json(doc.get("parametros") or doc.get("parametros_json"))
    resultado_json = safe_json(doc.get("resultado") or doc.get("resultado_json"))
    error_texto = str_or_none(doc.get("error") or doc.get("error_texto"))
    fecha_programada = parse_dt(doc.get("fecha_programada"))
    fecha_ejecucion = parse_dt(doc.get("fecha_ejecucion"))
    solicitado_por = doc.get("solicitado_por_usuario_id")
    asignado_a = doc.get("asignado_a_usuario_id")
    created_by = str_or_none(doc.get("created_by") or "MIGRACION_MONGO")
    created_at = parse_dt(doc.get("created_at")) or datetime.now()

    sql_exists = "SELECT ScriptPendienteID FROM Sistema_ScriptsPendientes WHERE LegacyMongoID = ?"
    cur.execute(sql_exists, legacy_id)
    row = cur.fetchone()

    if row:
        if not dry_run:
            cur.execute(
                """
                UPDATE Sistema_ScriptsPendientes
                SET TipoScript = ?, NombreScript = ?, Descripcion = ?, EstadoScript = ?, Prioridad = ?,
                    Modulo = ?, EmpresaID = ?, UnidadNegocioID = ?, SucursalID = ?, ServerID = ?,
                    ContenidoScript = ?, ParametrosJSON = ?, ResultadoJSON = ?, ErrorTexto = ?,
                    FechaProgramada = ?, FechaEjecucion = ?, SolicitadoPorUsuarioID = ?, AsignadoAUsuarioID = ?,
                    LegacyCollection = ?, MigratedAt = SYSDATETIME(),
                    UpdatedAt = SYSDATETIME(), UpdatedBy = ?
                WHERE LegacyMongoID = ?
                """,
                tipo_script, nombre, descripcion, estado, prioridad,
                modulo, empresa_id, unidad_negocio_id, sucursal_id, server_id,
                contenido, parametros_json, resultado_json, error_texto,
                fecha_programada, fecha_ejecucion, solicitado_por, asignado_a,
                "scripts_pendientes", "MIGRACION_MONGO", legacy_id
            )
        return True, f"UPDATED script {legacy_id}"

    if not dry_run:
        cur.execute(
            """
            INSERT INTO Sistema_ScriptsPendientes (
                TipoScript, NombreScript, Descripcion, EstadoScript, Prioridad, Modulo,
                EmpresaID, UnidadNegocioID, SucursalID, ServerID,
                ContenidoScript, ParametrosJSON, ResultadoJSON, ErrorTexto,
                FechaProgramada, FechaEjecucion, SolicitadoPorUsuarioID, AsignadoAUsuarioID,
                CreatedAt, CreatedBy, LegacyMongoID, LegacyCollection, MigratedAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME())
            """,
            tipo_script, nombre, descripcion, estado, prioridad, modulo,
            empresa_id, unidad_negocio_id, sucursal_id, server_id,
            contenido, parametros_json, resultado_json, error_texto,
            fecha_programada, fecha_ejecucion, solicitado_por, asignado_a,
            created_at, created_by, legacy_id, "scripts_pendientes"
        )
    return True, f"INSERTED script {legacy_id}"


def upsert_informe(cur, doc: Dict[str, Any], dry_run: bool):
    legacy_id = str(doc.get("_id"))
    tipo = doc.get("tipo_informe") or doc.get("tipo") or "AUDITORIA"
    titulo = doc.get("titulo_informe") or doc.get("titulo") or f"INFORME_{legacy_id}"
    folio = doc.get("folio_referencia") or doc.get("folio")
    empresa_id = doc.get("empresa_id")
    unidad_negocio_id = doc.get("unidad_negocio_id")
    sucursal_id = doc.get("sucursal_id")
    area = doc.get("area_auditada") or doc.get("area")
    fecha_auditoria = parse_dt(doc.get("fecha_auditoria"))
    fecha_informe = parse_dt(doc.get("fecha_informe")) or datetime.now()
    estado = doc.get("estado_informe") or doc.get("estado") or "BORRADOR"
    resumen = doc.get("resumen_ejecutivo")
    contenido_json = safe_json(doc.get("contenido_json") or doc.get("contenido") or doc)
    observaciones = doc.get("observaciones")
    dictamen = doc.get("dictamen")
    documento_url = doc.get("documento_url")
    documento_path = doc.get("documento_path")
    elaborado = doc.get("elaborado_por_usuario_id")
    revisado = doc.get("revisado_por_usuario_id")
    aprobado = doc.get("aprobado_por_usuario_id")
    created_by = str_or_none(doc.get("created_by") or "MIGRACION_MONGO")
    created_at = parse_dt(doc.get("created_at")) or datetime.now()

    sql_exists = "SELECT InformeAuditoriaID FROM Auditoria_Informes WHERE LegacyMongoID = ?"
    cur.execute(sql_exists, legacy_id)
    row = cur.fetchone()

    if row:
        if not dry_run:
            cur.execute(
                """
                UPDATE Auditoria_Informes
                SET TipoInforme = ?, TituloInforme = ?, FolioReferencia = ?, EmpresaID = ?,
                    UnidadNegocioID = ?, SucursalID = ?, AreaAuditada = ?, FechaAuditoria = ?,
                    FechaInforme = ?, EstadoInforme = ?, ResumenEjecutivo = ?, ContenidoJSON = ?,
                    Observaciones = ?, Dictamen = ?, DocumentoURL = ?, DocumentoPath = ?,
                    ElaboradoPorUsuarioID = ?, RevisadoPorUsuarioID = ?, AprobadoPorUsuarioID = ?,
                    LegacyCollection = ?, MigratedAt = SYSDATETIME(),
                    UpdatedAt = SYSDATETIME(), UpdatedBy = ?
                WHERE LegacyMongoID = ?
                """,
                tipo, titulo, folio, empresa_id,
                unidad_negocio_id, sucursal_id, area, fecha_auditoria,
                fecha_informe, estado, resumen, contenido_json,
                observaciones, dictamen, documento_url, documento_path,
                elaborado, revisado, aprobado,
                "informes_auditoria", "MIGRACION_MONGO", legacy_id
            )
        return True, f"UPDATED informe {legacy_id}"

    if not dry_run:
        cur.execute(
            """
            INSERT INTO Auditoria_Informes (
                TipoInforme, TituloInforme, FolioReferencia, EmpresaID, UnidadNegocioID, SucursalID,
                AreaAuditada, FechaAuditoria, FechaInforme, EstadoInforme,
                ResumenEjecutivo, ContenidoJSON, Observaciones, Dictamen,
                DocumentoURL, DocumentoPath, ElaboradoPorUsuarioID, RevisadoPorUsuarioID, AprobadoPorUsuarioID,
                CreatedAt, CreatedBy, LegacyMongoID, LegacyCollection, MigratedAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSDATETIME())
            """,
            tipo, titulo, folio, empresa_id, unidad_negocio_id, sucursal_id,
            area, fecha_auditoria, fecha_informe, estado,
            resumen, contenido_json, observaciones, dictamen,
            documento_url, documento_path, elaborado, revisado, aprobado,
            created_at, created_by, legacy_id, "informes_auditoria"
        )
    return True, f"INSERTED informe {legacy_id}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", choices=["queries", "consultas_custom", "scripts_pendientes", "informes_auditoria", "all"], default="all")
    args = parser.parse_args()

    mongo = get_mongo_client()
    mongo_db_name = env("MONGO_DB_NAME", "edarsahub")
    mdb = mongo[mongo_db_name]

    conn = get_sql_conn()
    cur = conn.cursor()

    stats = {
        "ok": 0,
        "skip": 0,
        "error": 0,
    }

    collections = []
    if args.only in ("queries", "all"):
        collections.append("queries")
    if args.only in ("consultas_custom", "all"):
        collections.append("consultas_custom")
    if args.only in ("scripts_pendientes", "all"):
        collections.append("scripts_pendientes")
    if args.only in ("informes_auditoria", "all"):
        collections.append("informes_auditoria")

    try:
        for collection_name in collections:
            for doc in mdb[collection_name].find({}):
                try:
                    if collection_name in ("queries", "consultas_custom"):
                        ok, msg = upsert_consulta(cur, collection_name, doc, args.dry_run)
                    elif collection_name == "scripts_pendientes":
                        ok, msg = upsert_script(cur, doc, args.dry_run)
                    elif collection_name == "informes_auditoria":
                        ok, msg = upsert_informe(cur, doc, args.dry_run)
                    else:
                        ok, msg = False, "colección no soportada"

                    if ok:
                        stats["ok"] += 1
                    else:
                        stats["skip"] += 1
                    print(msg)
                except Exception as ex:
                    stats["error"] += 1
                    print(f"ERROR {collection_name} {doc.get('_id')}: {ex}")

        if args.dry_run:
            conn.rollback()
            print("DRY RUN: rollback ejecutado")
        else:
            conn.commit()
            print("COMMIT ejecutado")

        print(json.dumps(stats, ensure_ascii=False, indent=2))
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
        mongo.close()


if __name__ == "__main__":
    main()
