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


def get_empresa_configuracion(empresa_id: int):
    return fetch_one_dict("SELECT EmpresaID,CatalogoLegalAmpliadoActivo,DiasAlertaDefault,Activo,FechaAlta,FechaActualizacion,UsuarioActualizacionID FROM dbo.Gobierno_EmpresaConfiguracion WHERE EmpresaID=%s", [empresa_id])


def empresa_existe(empresa_id: int) -> bool:
    return fetch_one_dict("SELECT EmpresaID FROM dbo.Sistema_Empresas WHERE EmpresaID=%s", [empresa_id]) is not None


def upsert_empresa_configuracion(empresa_id: int, activo: bool, dias: int | None, usuario_id: int):
    with sql_connection() as conn:
        cur=conn.cursor(); cur.execute("""UPDATE dbo.Gobierno_EmpresaConfiguracion SET CatalogoLegalAmpliadoActivo=%s,DiasAlertaDefault=%s,Activo=1,FechaActualizacion=SYSUTCDATETIME(),UsuarioActualizacionID=%s WHERE EmpresaID=%s; IF @@ROWCOUNT=0 INSERT INTO dbo.Gobierno_EmpresaConfiguracion(EmpresaID,CatalogoLegalAmpliadoActivo,DiasAlertaDefault,UsuarioActualizacionID) VALUES(%s,%s,%s,%s);""", [activo,dias,usuario_id,empresa_id,empresa_id,activo,dias,usuario_id]); conn.commit()
    return get_empresa_configuracion(empresa_id)


def list_personas(empresa_id: int | None=None):
    if empresa_id is None:
        return fetch_all_dict("SELECT * FROM dbo.Gobierno_Persona WHERE Activo=1 ORDER BY Nombre,ApellidoPaterno,PersonaID")
    return fetch_all_dict("""SELECT DISTINCT p.* FROM dbo.Gobierno_Persona p JOIN dbo.Gobierno_PersonaEmpresaRol r ON r.PersonaID=p.PersonaID AND r.Activo=1 WHERE p.Activo=1 AND r.EmpresaID=%s ORDER BY p.Nombre,p.ApellidoPaterno,p.PersonaID""", [empresa_id])


def create_persona(data, usuario_id: int):
    return _insert_one("""INSERT INTO dbo.Gobierno_Persona(Nombre,ApellidoPaterno,ApellidoMaterno,RFC,CURP,FechaNacimiento,Nacionalidad,UsuarioActualizacionID) OUTPUT INSERTED.* VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""", [data.get('nombre'),data.get('apellido_paterno'),data.get('apellido_materno'),data.get('rfc'),data.get('curp'),data.get('fecha_nacimiento'),data.get('nacionalidad'),usuario_id])


def create_vinculo(persona_id: int, data, usuario_id: int):
    return _insert_one("""INSERT INTO dbo.Gobierno_PersonaVinculo(PersonaID,UsuarioID,ClienteID,ProveedorID,ContactoClienteID,ContactoProveedorID,EsPrincipal,UsuarioAltaID) OUTPUT INSERTED.* VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""", [persona_id,data.get('usuario_id'),data.get('cliente_id'),data.get('proveedor_id'),data.get('contacto_cliente_id'),data.get('contacto_proveedor_id'),data.get('es_principal',False),usuario_id])


def list_roles_catalogo():
    return fetch_all_dict("SELECT * FROM dbo.Gobierno_RolCorporativoCatalogo WHERE Activo=1 ORDER BY Nombre,RolCorporativoID")


def create_empresa_rol(empresa_id: int, data, usuario_id: int):
    return _insert_one("""INSERT INTO dbo.Gobierno_PersonaEmpresaRol(PersonaID,EmpresaID,RolCorporativoID,CargoDetalle,ParticipacionPct,Facultades,VigenteDesde,VigenteHasta,UsuarioAltaID) OUTPUT INSERTED.* VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""", [data['persona_id'],empresa_id,data['rol_corporativo_id'],data.get('cargo_detalle'),data.get('participacion_pct'),data.get('facultades'),data.get('vigente_desde'),data.get('vigente_hasta'),usuario_id])


def list_tipos_documento():
    return fetch_all_dict("SELECT * FROM dbo.Gobierno_TipoDocumento WHERE Activo=1 ORDER BY Nombre,TipoDocumentoID")


def list_documentos(empresa_id: int):
    return fetch_all_dict("""SELECT d.*,td.Codigo TipoDocumentoCodigo,td.Nombre TipoDocumentoNombre,v.DocumentoVersionID,v.NumeroVersion,v.FechaEmision,v.FechaVencimiento,v.FechaVencimientoFuente,v.EstadoRevision,v.OCRConfianza FROM dbo.Gobierno_Documento d JOIN dbo.Gobierno_TipoDocumento td ON td.TipoDocumentoID=d.TipoDocumentoID OUTER APPLY(SELECT TOP 1 dv.* FROM dbo.Gobierno_DocumentoVersion dv WHERE dv.DocumentoID=d.DocumentoID ORDER BY dv.NumeroVersion DESC) v LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID WHERE d.Activo=1 AND (d.EmpresaID=%s OR pr.EmpresaID=%s) ORDER BY d.Titulo,d.DocumentoID""", [empresa_id,empresa_id])


def create_documento(data, usuario_id: int):
    with sql_connection() as conn:
        cur=conn.cursor(); cur.execute("""INSERT INTO dbo.Gobierno_Documento(TipoDocumentoID,PropietarioTipo,PersonaID,EmpresaID,PersonaEmpresaRolID,Titulo,UsuarioAltaID) OUTPUT INSERTED.* VALUES(%s,%s,%s,%s,%s,%s,%s)""", [data['tipo_documento_id'],data['propietario_tipo'],data.get('persona_id'),data.get('empresa_id'),data.get('persona_empresa_rol_id'),data['titulo'],usuario_id]); row=cur.fetchone(); cols=[d[0] for d in cur.description]; doc=dict(zip(cols,row)); cur.execute("INSERT INTO dbo.Gobierno_DocumentoMovimiento(DocumentoID,TipoMovimiento,UsuarioID) VALUES(%s,%s,%s)", [doc['DocumentoID'],'CREACION',usuario_id]); conn.commit(); return doc


def create_documento_version(documento_id: int, data, usuario_id: int):
    with sql_connection() as conn:
        cur=conn.cursor(); cur.execute("SELECT ISNULL(MAX(NumeroVersion),0)+1 FROM dbo.Gobierno_DocumentoVersion WITH (UPDLOCK,HOLDLOCK) WHERE DocumentoID=%s", [documento_id]); numero=int(cur.fetchone()[0]); cur.execute("""INSERT INTO dbo.Gobierno_DocumentoVersion(DocumentoID,NumeroVersion,NombreArchivo,StorageKey,MimeType,TamanioBytes,SHA256,FechaEmision,FechaVencimiento,FechaVencimientoFuente,OCRTexto,OCRMetadataJSON,OCRConfianza,UsuarioAltaID) OUTPUT INSERTED.* VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", [documento_id,numero,data['nombre_archivo'],data['storage_key'],data.get('mime_type'),data.get('tamanio_bytes'),data['sha256'].lower(),data.get('fecha_emision'),data.get('fecha_vencimiento'),data.get('fecha_vencimiento_fuente'),data.get('ocr_texto'),data.get('ocr_metadata_json'),data.get('ocr_confianza'),usuario_id]); row=cur.fetchone(); cols=[d[0] for d in cur.description]; version=dict(zip(cols,row)); cur.execute("INSERT INTO dbo.Gobierno_DocumentoMovimiento(DocumentoID,DocumentoVersionID,TipoMovimiento,UsuarioID) VALUES(%s,%s,%s,%s)", [documento_id,version['DocumentoVersionID'],'NUEVA_VERSION',usuario_id]); conn.commit(); return version


def get_kardex(documento_id: int):
    return fetch_all_dict("SELECT * FROM dbo.Gobierno_DocumentoMovimiento WHERE DocumentoID=%s ORDER BY FechaUTC DESC,MovimientoID DESC", [documento_id])


def list_vencimientos(empresa_id: int, dias: int):
    return fetch_all_dict("""SELECT d.DocumentoID,d.Titulo,td.Nombre TipoDocumento,v.DocumentoVersionID,v.FechaVencimiento,DATEDIFF(DAY,CAST(GETDATE() AS date),v.FechaVencimiento) DiasRestantes FROM dbo.Gobierno_Documento d JOIN dbo.Gobierno_TipoDocumento td ON td.TipoDocumentoID=d.TipoDocumentoID JOIN dbo.Gobierno_DocumentoVersion v ON v.DocumentoID=d.DocumentoID LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID WHERE d.Activo=1 AND v.EstadoRevision='VALIDADO' AND v.NumeroVersion=(SELECT MAX(v2.NumeroVersion) FROM dbo.Gobierno_DocumentoVersion v2 WHERE v2.DocumentoID=d.DocumentoID) AND (d.EmpresaID=%s OR pr.EmpresaID=%s) AND v.FechaVencimiento>=CAST(GETDATE() AS date) AND v.FechaVencimiento<=DATEADD(DAY,%s,CAST(GETDATE() AS date)) ORDER BY v.FechaVencimiento,d.DocumentoID""", [empresa_id,empresa_id,dias])


def list_alerta_reglas(empresa_id: int):
    return fetch_all_dict("SELECT * FROM dbo.Gobierno_AlertaRegla WHERE Activo=1 AND (EmpresaID=%s OR EmpresaID IS NULL) ORDER BY DiasAntes DESC,AlertaReglaID", [empresa_id])


def create_alerta_regla(empresa_id: int, data, usuario_id: int):
    return _insert_one("""INSERT INTO dbo.Gobierno_AlertaRegla(EmpresaID,TipoDocumentoID,UsuarioObjetivoID,DiasAntes,Canal,UsuarioAltaID) OUTPUT INSERTED.* VALUES(%s,%s,%s,%s,%s,%s)""", [empresa_id,data.get('tipo_documento_id'),data.get('usuario_objetivo_id'),data['dias_antes'],data['canal'],usuario_id])


def list_alerta_eventos(empresa_id: int, limit: int = 200):
    limit=max(1,min(int(limit),500))
    return fetch_all_dict(f"""SELECT TOP {limit} e.*,r.Canal,r.DiasAntes,r.UsuarioObjetivoID,d.DocumentoID,d.Titulo,v.FechaVencimiento,COALESCE(d.EmpresaID,pr.EmpresaID) EmpresaID FROM dbo.Gobierno_AlertaEvento e JOIN dbo.Gobierno_AlertaRegla r ON r.AlertaReglaID=e.AlertaReglaID JOIN dbo.Gobierno_DocumentoVersion v ON v.DocumentoVersionID=e.DocumentoVersionID JOIN dbo.Gobierno_Documento d ON d.DocumentoID=v.DocumentoID LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID WHERE COALESCE(d.EmpresaID,pr.EmpresaID)=%s ORDER BY e.FechaProgramada DESC,e.AlertaEventoID DESC""", [empresa_id])


def plan_alerta_eventos() -> int:
    with sql_connection() as conn:
        cur=conn.cursor()
        cur.execute("""
        INSERT INTO dbo.Gobierno_AlertaEvento(DocumentoVersionID,AlertaReglaID,FechaObjetivo,FechaProgramada)
        SELECT v.DocumentoVersionID,r.AlertaReglaID,v.FechaVencimiento,DATEADD(DAY,-r.DiasAntes,v.FechaVencimiento)
        FROM dbo.Gobierno_Documento d
        JOIN dbo.Gobierno_DocumentoVersion v ON v.DocumentoID=d.DocumentoID
        LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID
        JOIN dbo.Gobierno_EmpresaConfiguracion cfg ON cfg.EmpresaID=COALESCE(d.EmpresaID,pr.EmpresaID) AND cfg.Activo=1 AND cfg.CatalogoLegalAmpliadoActivo=1
        JOIN dbo.Gobierno_AlertaRegla r ON r.Activo=1 AND (r.EmpresaID=COALESCE(d.EmpresaID,pr.EmpresaID) OR r.EmpresaID IS NULL) AND (r.TipoDocumentoID=d.TipoDocumentoID OR r.TipoDocumentoID IS NULL)
        WHERE d.Activo=1 AND d.Estado='VIGENTE' AND v.EstadoRevision='VALIDADO' AND v.FechaVencimiento IS NOT NULL
          AND v.NumeroVersion=(SELECT MAX(v2.NumeroVersion) FROM dbo.Gobierno_DocumentoVersion v2 WHERE v2.DocumentoID=d.DocumentoID)
          AND NOT EXISTS(SELECT 1 FROM dbo.Gobierno_AlertaEvento e WITH (UPDLOCK,HOLDLOCK) WHERE e.DocumentoVersionID=v.DocumentoVersionID AND e.AlertaReglaID=r.AlertaReglaID AND e.FechaObjetivo=v.FechaVencimiento);
        SELECT @@ROWCOUNT;
        """)
        row=cur.fetchone(); conn.commit(); return int(row[0] if row else 0)


def list_due_alert_events(limit: int = 50):
    limit=max(1,min(int(limit),200))
    return fetch_all_dict(f"""SELECT TOP {limit} e.AlertaEventoID,e.Estado,e.TareaReferencia,e.NotificacionReferencia,e.FechaObjetivo,e.FechaProgramada,r.Canal,r.UsuarioObjetivoID,d.DocumentoID,d.Titulo,COALESCE(d.EmpresaID,pr.EmpresaID) EmpresaID FROM dbo.Gobierno_AlertaEvento e JOIN dbo.Gobierno_AlertaRegla r ON r.AlertaReglaID=e.AlertaReglaID JOIN dbo.Gobierno_DocumentoVersion v ON v.DocumentoVersionID=e.DocumentoVersionID JOIN dbo.Gobierno_Documento d ON d.DocumentoID=v.DocumentoID LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID WHERE e.Estado='PENDIENTE' AND e.FechaProgramada<=CAST(GETDATE() AS date) AND r.Activo=1 AND d.Activo=1 AND d.Estado='VIGENTE' AND v.EstadoRevision='VALIDADO' ORDER BY e.FechaProgramada,e.AlertaEventoID""")


def ensure_canonical_task_for_alert(alerta_evento_id: int):
    with sql_connection() as conn:
        cur=conn.cursor()
        cur.execute("""SELECT e.AlertaEventoID,e.Estado,e.TareaReferencia,r.Canal,r.UsuarioObjetivoID,d.Titulo,COALESCE(d.EmpresaID,pr.EmpresaID) EmpresaID,e.FechaObjetivo FROM dbo.Gobierno_AlertaEvento e WITH (UPDLOCK,HOLDLOCK) JOIN dbo.Gobierno_AlertaRegla r ON r.AlertaReglaID=e.AlertaReglaID JOIN dbo.Gobierno_DocumentoVersion v ON v.DocumentoVersionID=e.DocumentoVersionID JOIN dbo.Gobierno_Documento d ON d.DocumentoID=v.DocumentoID LEFT JOIN dbo.Gobierno_PersonaEmpresaRol pr ON pr.PersonaEmpresaRolID=d.PersonaEmpresaRolID WHERE e.AlertaEventoID=%s AND e.Estado IN('PENDIENTE','GENERADA') AND r.Activo=1 AND r.Canal='TAREA' AND d.Activo=1 AND d.Estado='VIGENTE' AND v.EstadoRevision='VALIDADO'""", [alerta_evento_id])
        row=cur.fetchone()
        if not row: raise RuntimeError('ALERTA_EVENTO_NO_EJECUTABLE')
        cols=[d[0] for d in cur.description]; event=dict(zip(cols,row))
        if event.get('TareaReferencia'):
            cur.execute("SELECT TOP 1 * FROM dbo.Sistema_Tareas WHERE TareaSistemaID=%s", [int(event['TareaReferencia'])]); task=cur.fetchone(); task_cols=[d[0] for d in cur.description] if cur.description else []; conn.commit(); return dict(zip(task_cols,task)) if task else {'TareaSistemaID':int(event['TareaReferencia'])}
        cur.execute("SELECT TOP 1 * FROM dbo.Sistema_Tareas WHERE Modulo='CATALOGO_AMPLIADO' AND EntidadTipo='GOBIERNO_ALERTA_EVENTO' AND EntidadID=%s ORDER BY TareaSistemaID", [str(alerta_evento_id)])
        task=cur.fetchone()
        if task:
            task_cols=[d[0] for d in cur.description]; task_dict=dict(zip(task_cols,task))
        else:
            codigo=f'GOB-ALERTA-{alerta_evento_id}'
            cur.execute("""INSERT INTO dbo.Sistema_Tareas(CodigoTarea,TipoTarea,EstadoTarea,Prioridad,TituloTarea,Descripcion,Modulo,EntidadTipo,EntidadID,EmpresaID,AsignadoAUsuarioID,CreadoPorUsuarioID,FechaLimite,MetadataJSON,CreatedAt,CreatedBy) OUTPUT INSERTED.* VALUES(%s,'CUMPLIMIENTO_DOCUMENTAL','PENDIENTE','MEDIA',%s,%s,'CATALOGO_AMPLIADO','GOBIERNO_ALERTA_EVENTO',%s,%s,%s,%s,%s,%s,GETDATE(),%s)""", [codigo,f"Cumplimiento documental: {event['Titulo']}",f"Revisar documento con fecha objetivo {event['FechaObjetivo']}",str(alerta_evento_id),event['EmpresaID'],event['UsuarioObjetivoID'],event['UsuarioObjetivoID'],event['FechaObjetivo'],f'{{"alerta_evento_id":{alerta_evento_id}}}',str(event['UsuarioObjetivoID'])])
            task_row=cur.fetchone(); task_cols=[d[0] for d in cur.description]; task_dict=dict(zip(task_cols,task_row))
        tarea_id=int(task_dict['TareaSistemaID'])
        cur.execute("UPDATE dbo.Gobierno_AlertaEvento SET TareaReferencia=%s,Estado='GENERADA',FechaEjecucion=SYSUTCDATETIME(),ErrorMensaje=NULL WHERE AlertaEventoID=%s", [str(tarea_id),alerta_evento_id])
        conn.commit(); return task_dict
