import json
import uuid
from datetime import date, datetime
from decimal import Decimal


ALLOWED_FECHA_OPERATIVA_TARGETS = {
    "Finanzas_AdquirenteTransacciones": {
        "table": "Finanzas_AdquirenteTransacciones",
        "pk": "TransaccionID",
        "field": "FechaOperativa",
        "module": "finanzas",
        "source_date": "FechaTrx",
        "select_cols": [
            "TransaccionID",
            "FechaOperativa",
            "FechaTrx",
            "HoraTrx",
            "UnidadNegocioID",
            "AdquirenteID",
            "StoreID",
            "OrderID",
            "Sucursal",
            "MontoTrx",
            "Propina",
            "Estatus",
        ],
    }
}


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    return str(value)


def json_dumps(value):
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def json_loads(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}


def current_user_email(current_user):
    return current_user.get("email") or current_user.get("Email") or str(current_user.get("id") or "")


def ensure_sql_user_id(cur, current_user):
    for key in ("UsuarioID", "_sql_usuario_id", "usuario_id", "user_id"):
        value = current_user.get(key)
        if value not in (None, ""):
            try:
                return int(value)
            except Exception:
                pass

    raw = current_user.get("id")
    try:
        return int(raw)
    except Exception:
        pass

    email = current_user.get("email") or current_user.get("Email")
    if email:
        cur.execute("""
            SELECT TOP 1 UsuarioID
            FROM dbo.Usuario_Catalogo WITH (NOLOCK)
            WHERE Email = %s
              AND Activo = 1
            ORDER BY UsuarioID
        """, (email,))
        row = cur.fetchone()
        if row:
            current_user["_sql_usuario_id"] = int(row[0])
            return int(row[0])

    return None


def is_fecha_operativa_payload(body):
    payload = json_loads(body.get("datos_solicitud_json"))
    return (
        body.get("codigo_catalogo") == "FECHA_OPERATIVA"
        or payload.get("tipo") == "CAMBIO_FECHA_OPERATIVA"
    )


def get_flow_permissions(cur, user_id):
    cur.execute("""
        SELECT TOP 1 PuedeSolicitar, PuedeAutorizar, PuedeLiberar
        FROM dbo.Usuario_PermisosCatalogosFlujo WITH (NOLOCK)
        WHERE UsuarioID = %s
          AND Activo = 1
    """, (user_id,))
    row = cur.fetchone()
    if not row:
        return {"PuedeSolicitar": False, "PuedeAutorizar": False, "PuedeLiberar": False}
    return {
        "PuedeSolicitar": bool(row[0]),
        "PuedeAutorizar": bool(row[1]),
        "PuedeLiberar": bool(row[2]),
    }


def has_rbac_action(cur, user_id, module_code, action_code):
    cur.execute("""
        SELECT TOP 1 1
        FROM dbo.Usuario_RolesAsignacion ura WITH (NOLOCK)
        JOIN dbo.Usuario_Roles r WITH (NOLOCK)
            ON r.RolID = ura.RolID
           AND r.Activo = 1
        JOIN dbo.Usuario_PermisosRolModulo prm WITH (NOLOCK)
            ON prm.RolID = r.RolID
           AND prm.Permitido = 1
           AND prm.Activo = 1
        JOIN dbo.Usuario_Modulos m WITH (NOLOCK)
            ON m.ModuloID = prm.ModuloID
           AND m.Activo = 1
        JOIN dbo.Usuario_Acciones a WITH (NOLOCK)
            ON a.AccionID = prm.AccionID
           AND a.Activo = 1
        WHERE ura.UsuarioID = %s
          AND ura.Activo = 1
          AND m.CodigoModulo = %s
          AND a.CodigoAccion = %s
          AND (ura.FechaInicio IS NULL OR ura.FechaInicio <= GETDATE())
          AND (ura.FechaFin IS NULL OR ura.FechaFin >= GETDATE())
    """, (user_id, module_code, action_code))
    return cur.fetchone() is not None


def has_any_rbac_action(cur, user_id, module_code, actions):
    return any(has_rbac_action(cur, user_id, module_code, action) for action in actions)


def get_target_from_payload(payload):
    table = payload.get("tabla_origen")
    target = ALLOWED_FECHA_OPERATIVA_TARGETS.get(table)
    if not target:
        raise ValueError(f"Target de fecha operativa no permitido: {table}")
    return target


def get_fecha_operativa_record(cur, target, registro_id):
    cols = ", ".join(target["select_cols"])
    sql = f"""
        SELECT {cols}
        FROM dbo.{target["table"]} WITH (NOLOCK)
        WHERE {target["pk"]} = %s
    """
    cur.execute(sql, (registro_id,))
    row = cur.fetchone()
    if not row:
        return None
    return dict(zip(target["select_cols"], row))


def normalize_fecha_operativa_request(cur, body, current_user):
    if not is_fecha_operativa_payload(body):
        return body

    user_id = ensure_sql_user_id(cur, current_user)
    if not user_id:
        raise PermissionError("No se pudo resolver UsuarioID SQL para validar la solicitud.")

    payload = json_loads(body.get("datos_solicitud_json"))
    payload["tipo"] = "CAMBIO_FECHA_OPERATIVA"
    payload.setdefault("dominio", "finanzas")
    payload.setdefault("modulo", "finanzas")
    payload.setdefault("tabla_origen", "Finanzas_AdquirenteTransacciones")
    payload.setdefault("pk", "TransaccionID")
    payload.setdefault("campo", "FechaOperativa")

    target = get_target_from_payload(payload)
    registro_id = payload.get("registro_objetivo_id") or body.get("registro_objetivo_id")
    if registro_id in (None, ""):
        raise ValueError("registro_objetivo_id es obligatorio.")

    flow = get_flow_permissions(cur, user_id)
    if not flow["PuedeSolicitar"]:
        raise PermissionError("El usuario no tiene PuedeSolicitar activo.")

    if not has_any_rbac_action(cur, user_id, target["module"], ("PROPONER", "VER")):
        raise PermissionError("El usuario no tiene permiso RBAC para solicitar cambio de fecha operativa.")

    record = get_fecha_operativa_record(cur, target, registro_id)
    if not record:
        raise ValueError("Registro objetivo no existe o no está permitido.")

    valor_propuesto = payload.get("valor_propuesto")
    if not valor_propuesto:
        raise ValueError("valor_propuesto es obligatorio.")

    payload["registro_objetivo_id"] = int(registro_id)
    payload["valor_anterior"] = record.get(target["field"])
    payload["fecha_fuente_tipo"] = target["source_date"]
    payload["fecha_fuente_valor"] = record.get(target["source_date"])
    payload["snapshot_origen"] = record

    body["codigo_catalogo"] = "FECHA_OPERATIVA"
    body["tipo_solicitud"] = "CAMBIO"
    body["registro_objetivo_id"] = str(registro_id)
    body["datos_solicitud_json"] = json_dumps(payload)
    body.setdefault("estado_solicitud", "PENDIENTE")
    body.setdefault("prioridad", "MEDIA")
    body.setdefault("nivel_aprobacion_actual", 0)
    body.setdefault("total_niveles_aprobacion", 1)
    body.setdefault("comentarios", payload.get("motivo") or "Solicitud de cambio de fecha operativa")
    return body


def apply_fecha_operativa(cur, payload):
    target = get_target_from_payload(payload)
    registro_id = payload.get("registro_objetivo_id")
    nuevo_valor = payload.get("valor_propuesto")

    if registro_id in (None, ""):
        raise ValueError("registro_objetivo_id es obligatorio para aplicar.")
    if not nuevo_valor:
        raise ValueError("valor_propuesto es obligatorio para aplicar.")

    before = get_fecha_operativa_record(cur, target, registro_id)
    if not before:
        raise ValueError("Registro objetivo no existe al aplicar.")

    expected = payload.get("valor_anterior")
    current_value = before.get(target["field"])
    if expected not in (None, "") and str(current_value) != str(expected):
        raise ValueError(
            f"FechaOperativa cambió desde la solicitud. Actual={current_value}, esperado={expected}"
        )

    sql = f"""
        UPDATE dbo.{target["table"]}
        SET {target["field"]} = %s
        WHERE {target["pk"]} = %s
    """
    cur.execute(sql, (nuevo_valor, registro_id))

    after = get_fecha_operativa_record(cur, target, registro_id)
    return before, after


def insert_rbac_bitacora(cur, current_user, accion, resultado, descripcion, detalles, usuario_afectado_id=None):
    admin_id = ensure_sql_user_id(cur, current_user)
    admin_email = current_user_email(current_user)
    cur.execute("""
        INSERT INTO dbo.Usuario_RBAC_Bitacora (
            EventoUUID,
            FechaEvento,
            UsuarioAfectadoID,
            UsuarioAfectadoEmail,
            Tipo,
            Accion,
            Resultado,
            Descripcion,
            Detalles,
            AdministradorID,
            AdministradorEmail
        )
        VALUES (%s, SYSDATETIME(), %s, NULL, %s, %s, %s, %s, %s, %s, %s)
    """, (
        str(uuid.uuid4()),
        usuario_afectado_id,
        "FECHA_OPERATIVA",
        accion,
        resultado,
        descripcion[:500],
        json_dumps(detalles),
        admin_id,
        admin_email,
    ))


def can_authorize_fecha_operativa(cur, current_user, module_code):
    user_id = ensure_sql_user_id(cur, current_user)
    if not user_id:
        return False
    flow = get_flow_permissions(cur, user_id)
    return bool(flow["PuedeAutorizar"]) and has_any_rbac_action(
        cur,
        user_id,
        module_code,
        ("AUTORIZAR", "APROBAR", "GESTIONAR"),
    )


def can_release_fecha_operativa(cur, current_user, module_code):
    user_id = ensure_sql_user_id(cur, current_user)
    if not user_id:
        return False
    flow = get_flow_permissions(cur, user_id)
    return bool(flow["PuedeLiberar"]) and has_any_rbac_action(
        cur,
        user_id,
        module_code,
        ("AUTORIZAR", "APROBAR", "GESTIONAR", "EDITAR"),
    )
