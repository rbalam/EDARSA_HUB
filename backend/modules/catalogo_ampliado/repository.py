from typing import Any

from core.sql_first.db import fetch_all_dict, fetch_one_dict, sql_connection


def _insert_one(sql: str, params: list[Any]) -> dict[str, Any]:
    with sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
        conn.commit()
        return dict(zip(cols, row)) if row else {}


def _execute(sql: str, params: list[Any]) -> int:
    with sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        affected = cur.rowcount
        conn.commit()
        return affected


def get_empresa_configuracion(empresa_id: int) -> dict[str, Any] | None:
    return fetch_one_dict(
        """
        SELECT EmpresaID, CatalogoLegalAmpliadoActivo, DiasAlertaDefault, Activo,
               FechaAlta, FechaActualizacion, UsuarioActualizacion
        FROM dbo.Gobierno_EmpresaConfiguracion
        WHERE EmpresaID = ?
        """,
        [empresa_id],
    )


def upsert_empresa_configuracion(empresa_id: int, activo: bool, dias: int | None, usuario: str) -> dict[str, Any]:
    with sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE dbo.Gobierno_EmpresaConfiguracion
               SET CatalogoLegalAmpliadoActivo=?, DiasAlertaDefault=?, Activo=1,
                   FechaActualizacion=SYSUTCDATETIME(), UsuarioActualizacion=?
             WHERE EmpresaID=?;
            IF @@ROWCOUNT=0
              INSERT INTO dbo.Gobierno_EmpresaConfiguracion
                (EmpresaID,CatalogoLegalAmpliadoActivo,DiasAlertaDefault,UsuarioActualizacion)
              VALUES (?,?,?,?);
            """,
            [activo, dias, usuario, empresa_id, empresa_id, activo, dias, usuario],
        )
        conn.commit()
    return get_empresa_configuracion(empresa_id) or {}


def list_personas(empresa_id: int | None = None) -> list[dict[str, Any]]:
    if empresa_id is None:
        return fetch_all_dict("SELECT * FROM dbo.Gobierno_Persona WHERE Activo=1 ORDER BY Nombre,ApellidoPaterno")
    return fetch_all_dict(
        """
        SELECT DISTINCT p.*
        FROM dbo.Gobierno_Persona p
        JOIN dbo.Gobierno_PersonaEmpresaRol r ON r.PersonaID=p.PersonaID AND r.Activo=1
        WHERE p.Activo=1 AND r.EmpresaID=?
        ORDER BY p.Nombre,p.ApellidoPaterno
        """,
        [empresa_id],
    )


def create_persona(data: dict[str, Any], usuario: str) -> dict[str, Any]:
    return _insert_one(
        """
        INSERT INTO dbo.Gobierno_Persona
          (Nombre,ApellidoPaterno,ApellidoMaterno,RFC,CURP,FechaNacimiento,Nacionalidad,UsuarioActualizacion)
        OUTPUT INSERTED.*
        VALUES (?,?,?,?,?,?,?,?)
        """,
        [data.get("nombre"), data.get("apellido_paterno"), data.get("apellido_materno"),
         data.get("rfc"), data.get("curp"), data.get("fecha_nacimiento"), data.get("nacionalidad"), usuario],
    )


def create_vinculo(persona_id: int, data: dict[str, Any], usuario: str) -> dict[str, Any]:
    return _insert_one(
        """
        INSERT INTO dbo.Gobierno_PersonaVinculo(PersonaID,TipoEntidad,EntidadClave,EsPrincipal,UsuarioAlta)
        OUTPUT INSERTED.* VALUES (?,?,?,?,?)
        """,
        [persona_id, data["tipo_entidad"], data["entidad_clave"], data.get("es_principal", False), usuario],
    )


def list_roles_catalogo() -> list[dict[str, Any]]:
    return fetch_all_dict("SELECT * FROM dbo.Gobierno_RolCorporativoCatalogo WHERE Activo=1 ORDER BY Nombre")


def create_empresa_rol(empresa_id: int, data: dict[str, Any], usuario: str) -> dict[str, Any]:
    return _insert_one(
        """
        INSERT INTO dbo.Gobierno_PersonaEmpresaRol
          (PersonaID,EmpresaID,RolCorporativoID,CargoDetalle,ParticipacionPct,Facultades,VigenteDesde,VigenteHasta,UsuarioAlta)
        OUTPUT INSERTED.* VALUES (?,?,?,?,?,?,?,?,?)
        """,
        [data["persona_id"], empresa_id, data["rol_corporativo_id"], data.get("cargo_detalle"),
         data.get("participacion_pct"), data.get("facultades"), data.get("vigente_desde"), data.get("vigente_hasta"), usuario],
    )


def list_documentos(empresa_id: int) -> list[dict[str, Any]]:
    return fetch_all_dict(
        """
        SELECT d.*, td.Codigo AS TipoDocumentoCodigo, td.Nombre AS TipoDocumentoNombre,
               v.DocumentoVersionID, v.NumeroVersion, v.FechaEmision, v.FechaVencimiento,
               v.FechaVencimientoFuente, v.EstadoRevision, v.OCRConfianza
        FROM dbo.Gobierno_Documento d
        JOIN dbo.Gobierno_TipoDocumento td ON td.TipoDocumentoID=d.TipoDocumentoID
        OUTER APPLY (
          SELECT TOP 1 dv.* FROM dbo.Gobierno_DocumentoVersion dv
          WHERE dv.DocumentoID=d.DocumentoID ORDER BY dv.NumeroVersion DESC
        ) v
        LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID
        WHERE d.Activo=1 AND (d.EmpresaID=? OR pr.EmpresaID=?)
        ORDER BY d.Titulo
        """,
        [empresa_id, empresa_id],
    )


def create_documento(data: dict[str, Any], usuario: str) -> dict[str, Any]:
    return _insert_one(
        """
        INSERT INTO dbo.Gobierno_Documento
          (TipoDocumentoID,PropietarioTipo,PersonaID,EmpresaID,PersonaEmpresaRolID,Titulo,UsuarioAlta)
        OUTPUT INSERTED.* VALUES (?,?,?,?,?,?,?)
        """,
        [data["tipo_documento_id"], data["propietario_tipo"], data.get("persona_id"), data.get("empresa_id"),
         data.get("persona_empresa_rol_id"), data["titulo"], usuario],
    )


def get_kardex(documento_id: int) -> list[dict[str, Any]]:
    return fetch_all_dict(
        "SELECT * FROM dbo.Gobierno_DocumentoMovimiento WHERE DocumentoID=? ORDER BY FechaUTC DESC,MovimientoID DESC",
        [documento_id],
    )


def list_vencimientos(empresa_id: int, dias: int) -> list[dict[str, Any]]:
    return fetch_all_dict(
        """
        SELECT d.DocumentoID,d.Titulo,td.Nombre AS TipoDocumento,v.DocumentoVersionID,v.FechaVencimiento,
               DATEDIFF(DAY,CAST(GETDATE() AS date),v.FechaVencimiento) AS DiasRestantes
        FROM dbo.Gobierno_Documento d
        JOIN dbo.Gobierno_TipoDocumento td ON td.TipoDocumentoID=d.TipoDocumentoID
        JOIN dbo.Gobierno_DocumentoVersion v ON v.DocumentoID=d.DocumentoID
        LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID
        WHERE d.Activo=1 AND v.EstadoRevision='VALIDADO'
          AND v.NumeroVersion=(SELECT MAX(v2.NumeroVersion) FROM dbo.Gobierno_DocumentoVersion v2 WHERE v2.DocumentoID=d.DocumentoID)
          AND (d.EmpresaID=? OR pr.EmpresaID=?)
          AND v.FechaVencimiento>=CAST(GETDATE() AS date)
          AND v.FechaVencimiento<=DATEADD(DAY,?,CAST(GETDATE() AS date))
        ORDER BY v.FechaVencimiento
        """,
        [empresa_id, empresa_id, dias],
    )
