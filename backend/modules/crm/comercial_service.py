"""
EDARSA HUB - CRM Comercial Enterprise Service
==============================================
Servicio para gestión del CRM Comercial completo.

Incluye:
- Cuentas CRM
- Clientes (lectura de maestro)
- Solicitudes de alta de cliente
- Actividades
- Wrapper Cotizaciones
- Wrapper Pedidos
- Remisiones
"""

import logging
import pymssql
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)


class CRMComercialService:
    """Servicio CRM Comercial Enterprise"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        
    def _get_connection(self):
        return pymssql.connect(
            server=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password'],
            login_timeout=30,
            timeout=60,
            autocommit=False
        )
    
    def _now_utc(self) -> datetime:
        return datetime.utcnow()
    
    # ============================================================
    # CUENTAS CRM
    # ============================================================
    
    def listar_cuentas(
        self,
        empresa_id: Optional[str] = None,
        tipo_cuenta: Optional[str] = None,
        estatus: Optional[str] = None,
        ejecutivo_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista cuentas CRM con filtros"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    c.CuentaID, c.EmpresaID, c.ClienteID,
                    c.CodigoCuenta, c.TipoCuenta, c.NombreCuenta,
                    c.RazonSocialSnapshot, c.RFCSnapshot,
                    c.EjecutivoResponsableUserID,
                    c.ContactoPrincipalNombre, c.ContactoPrincipalEmail,
                    c.Ciudad, c.Estado,
                    c.EstatusCuenta, c.Activo, c.CreatedAt,
                    cl.CodigoCliente, cl.RazonSocial as ClienteRazonSocial
                FROM CRM_Cuentas c
                LEFT JOIN Cliente_Catalogo cl ON c.ClienteID = cl.ClienteID
                WHERE c.Activo = 1
            """
            params = []
            
            if empresa_id:
                query += " AND c.EmpresaID = %s"
                params.append(empresa_id)
            if tipo_cuenta:
                query += " AND c.TipoCuenta = %s"
                params.append(tipo_cuenta)
            if estatus:
                query += " AND c.EstatusCuenta = %s"
                params.append(estatus)
            if ejecutivo_id:
                query += " AND c.EjecutivoResponsableUserID = %s"
                params.append(ejecutivo_id)
            if search:
                query += " AND (c.NombreCuenta LIKE %s OR c.RFCSnapshot LIKE %s OR c.ContactoPrincipalEmail LIKE %s)"
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
            query += " ORDER BY c.CreatedAt DESC"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            cuentas = []
            for row in cursor.fetchall():
                cuenta = dict(row)
                cuenta['CuentaID'] = str(cuenta['CuentaID'])
                cuenta['EmpresaID'] = str(cuenta['EmpresaID'])
                if cuenta.get('EjecutivoResponsableUserID'):
                    cuenta['EjecutivoResponsableUserID'] = str(cuenta['EjecutivoResponsableUserID'])
                cuentas.append(cuenta)
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM CRM_Cuentas WHERE Activo = 1"
            cursor.execute(count_query)
            total = cursor.fetchone()['total']
            
            return {
                "cuentas": cuentas,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    def crear_cuenta(self, data: Dict, usuario_id: str) -> Dict[str, Any]:
        """Crea una nueva cuenta CRM"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cuenta_id = str(uuid.uuid4())
            now_utc = self._now_utc()
            
            # Generar código
            cursor.execute("""
                SELECT COUNT(*) + 1 as seq FROM CRM_Cuentas WHERE EmpresaID = %s
            """, (data['empresa_id'],))
            seq = cursor.fetchone()['seq']
            codigo = f"CTA-{seq:06d}"
            
            cursor.execute("""
                INSERT INTO CRM_Cuentas (
                    CuentaID, EmpresaID, SucursalID, ClienteID,
                    CodigoCuenta, TipoCuenta, NombreCuenta,
                    RazonSocialSnapshot, RFCSnapshot,
                    SectorID, TamanoClienteID,
                    EjecutivoResponsableUserID, CustomerSuccessUserID,
                    LeadOrigenID,
                    ContactoPrincipalNombre, ContactoPrincipalEmail, ContactoPrincipalTelefono,
                    Direccion, Ciudad, Estado, Pais, CodigoPostal,
                    SitioWeb, Descripcion,
                    EstatusCuenta, Activo, CreatedBy, CreatedAt
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                cuenta_id,
                data['empresa_id'],
                data.get('sucursal_id'),
                data.get('cliente_id'),
                codigo,
                data.get('tipo_cuenta', 'PROSPECTO'),
                data['nombre_cuenta'],
                data.get('razon_social'),
                data.get('rfc'),
                data.get('sector_id'),
                data.get('tamano_cliente_id'),
                data.get('ejecutivo_responsable_user_id'),
                data.get('customer_success_user_id'),
                data.get('lead_origen_id'),
                data.get('contacto_principal_nombre'),
                data.get('contacto_principal_email'),
                data.get('contacto_principal_telefono'),
                data.get('direccion'),
                data.get('ciudad'),
                data.get('estado'),
                data.get('pais', 'México'),
                data.get('codigo_postal'),
                data.get('sitio_web'),
                data.get('descripcion'),
                'ACTIVA',
                True,
                usuario_id,
                now_utc
            ))
            
            conn.commit()
            
            logger.info(f"[CRM] Cuenta creada: {codigo}")
            
            return {
                "cuenta_id": cuenta_id,
                "codigo_cuenta": codigo,
                "nombre_cuenta": data['nombre_cuenta'],
                "tipo_cuenta": data.get('tipo_cuenta', 'PROSPECTO')
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error creando cuenta: {e}")
            raise
        finally:
            conn.close()
    
    def obtener_cuenta(self, cuenta_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalle de una cuenta"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT c.*, 
                       cl.CodigoCliente, cl.RazonSocial as ClienteRazonSocial, cl.RFC as ClienteRFC
                FROM CRM_Cuentas c
                LEFT JOIN Cliente_Catalogo cl ON c.ClienteID = cl.ClienteID
                WHERE c.CuentaID = %s
            """, (cuenta_id,))
            
            cuenta = cursor.fetchone()
            if not cuenta:
                return None
            
            result = dict(cuenta)
            # Convertir UUIDs
            for field in ['CuentaID', 'EmpresaID', 'SucursalID', 'EjecutivoResponsableUserID', 
                          'CustomerSuccessUserID', 'LeadOrigenID', 'CreatedBy', 'UpdatedBy']:
                if result.get(field):
                    result[field] = str(result[field])
            
            # Obtener oportunidades de esta cuenta (si la tabla existe)
            try:
                cursor.execute("""
                    SELECT OportunidadID, NombreOportunidad, MontoEstimado, EtapaActualID
                    FROM CRM_Oportunidades
                    WHERE CuentaID = %s AND Activo = 1
                    ORDER BY CreatedAt DESC
                """, (cuenta_id,))
                result['oportunidades'] = [dict(r) for r in cursor.fetchall()]
            except Exception:
                result['oportunidades'] = []
            
            return result
            
        finally:
            conn.close()
    
    def ligar_cliente(self, cuenta_id: str, cliente_id: int, usuario_id: str) -> Dict[str, Any]:
        """Liga una cuenta CRM con un cliente del catálogo maestro"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Verificar cliente existe
            cursor.execute("SELECT ClienteID, RazonSocial, RFC FROM Cliente_Catalogo WHERE ClienteID = %s", (cliente_id,))
            cliente = cursor.fetchone()
            if not cliente:
                raise ValueError(f"Cliente {cliente_id} no encontrado")
            
            # Actualizar cuenta
            cursor.execute("""
                UPDATE CRM_Cuentas SET
                    ClienteID = %s,
                    TipoCuenta = 'CLIENTE',
                    RazonSocialSnapshot = %s,
                    RFCSnapshot = %s,
                    UpdatedBy = %s,
                    UpdatedAt = %s
                WHERE CuentaID = %s
            """, (
                cliente_id,
                cliente['RazonSocial'],
                cliente['RFC'],
                usuario_id,
                self._now_utc(),
                cuenta_id
            ))
            
            conn.commit()
            
            logger.info(f"[CRM] Cuenta {cuenta_id} ligada a Cliente {cliente_id}")
            
            return {
                "cuenta_id": cuenta_id,
                "cliente_id": cliente_id,
                "tipo_cuenta": "CLIENTE",
                "razon_social": cliente['RazonSocial']
            }
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # CLIENTES (LECTURA MAESTRO)
    # ============================================================
    
    def listar_clientes(
        self,
        search: Optional[str] = None,
        activo: Optional[bool] = True,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista clientes del catálogo maestro"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    ClienteID, CodigoCliente, RFC, RazonSocial, NombreComercial,
                    TipoPersona, MonedaID, LimiteCredito, DiasCredito,
                    EmailPrincipal, Activo
                FROM Cliente_Catalogo
                WHERE 1=1
            """
            params = []
            
            if activo is not None:
                query += " AND Activo = %s"
                params.append(activo)
            if search:
                query += " AND (RazonSocial LIKE %s OR RFC LIKE %s OR CodigoCliente LIKE %s OR NombreComercial LIKE %s)"
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'])
            
            query += " ORDER BY RazonSocial"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            clientes = [dict(row) for row in cursor.fetchall()]
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM Cliente_Catalogo WHERE 1=1"
            if activo is not None:
                count_query += f" AND Activo = {1 if activo else 0}"
            cursor.execute(count_query)
            total = cursor.fetchone()['total']
            
            return {
                "clientes": clientes,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    # ============================================================
    # SOLICITUDES ALTA CLIENTE
    # ============================================================
    
    def crear_solicitud_alta(self, data: Dict, usuario_id: str) -> Dict[str, Any]:
        """Crea solicitud de alta de cliente"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            solicitud_id = str(uuid.uuid4())
            now_utc = self._now_utc()
            
            # Generar folio
            cursor.execute("""
                SELECT COUNT(*) + 1 as seq FROM CRM_ClientesSolicitudesAlta WHERE EmpresaID = %s
            """, (data['empresa_id'],))
            seq = cursor.fetchone()['seq']
            folio = f"SOL-{seq:06d}"
            
            cursor.execute("""
                INSERT INTO CRM_ClientesSolicitudesAlta (
                    SolicitudID, EmpresaID, SucursalID, FolioSolicitud,
                    OrigenEntidad, OrigenEntidadID, CuentaID,
                    NombreComercial, RazonSocial, RFC, RegimenFiscal, UsoCFDI,
                    EmailFacturacion, TelefonoFacturacion,
                    Calle, NumeroExterior, NumeroInterior, Colonia, Municipio, Ciudad, Estado, Pais, CodigoPostal,
                    ContactoPrincipalNombre, ContactoPrincipalEmail, ContactoPrincipalTelefono, ContactoPrincipalPuesto,
                    RequiereCredito, LimiteCreditoSolicitado, DiasCreditoSolicitados, CondicionesPagoSolicitadas,
                    ObservacionesSolicitante,
                    EstatusSolicitud, SolicitadoPorUserID, FechaSolicitud,
                    CreatedBy, CreatedAt
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                solicitud_id,
                data['empresa_id'],
                data.get('sucursal_id'),
                folio,
                data.get('origen_entidad', 'DIRECTO'),
                data.get('origen_entidad_id'),
                data.get('cuenta_id'),
                data['nombre_comercial'],
                data['razon_social'],
                data['rfc'],
                data.get('regimen_fiscal'),
                data.get('uso_cfdi'),
                data.get('email_facturacion'),
                data.get('telefono_facturacion'),
                data.get('calle'),
                data.get('numero_exterior'),
                data.get('numero_interior'),
                data.get('colonia'),
                data.get('municipio'),
                data.get('ciudad'),
                data.get('estado'),
                data.get('pais', 'México'),
                data.get('codigo_postal'),
                data.get('contacto_principal_nombre'),
                data.get('contacto_principal_email'),
                data.get('contacto_principal_telefono'),
                data.get('contacto_principal_puesto'),
                data.get('requiere_credito', False),
                data.get('limite_credito_solicitado'),
                data.get('dias_credito_solicitados'),
                data.get('condiciones_pago_solicitadas'),
                data.get('observaciones_solicitante'),
                'BORRADOR',
                usuario_id,
                now_utc,
                usuario_id,
                now_utc
            ))
            
            # Registrar historial
            cursor.execute("""
                INSERT INTO CRM_ClientesSolicitudesAltaHistorial 
                (SolicitudID, EstatusAnterior, EstatusNuevo, Comentario, CambiadoPorUserID)
                VALUES (%s, NULL, 'BORRADOR', 'Solicitud creada', %s)
            """, (solicitud_id, usuario_id))
            
            conn.commit()
            
            logger.info(f"[CRM] Solicitud alta creada: {folio}")
            
            return {
                "solicitud_id": solicitud_id,
                "folio_solicitud": folio,
                "estatus": "BORRADOR"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error creando solicitud: {e}")
            raise
        finally:
            conn.close()
    
    def listar_solicitudes_alta(
        self,
        empresa_id: Optional[str] = None,
        estatus: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista solicitudes de alta de cliente"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    SolicitudID, FolioSolicitud, NombreComercial, RazonSocial, RFC,
                    EstatusSolicitud, RequiereCredito, LimiteCreditoSolicitado,
                    FechaSolicitud, FechaAutorizacion
                FROM CRM_ClientesSolicitudesAlta
                WHERE Activo = 1
            """
            params = []
            
            if empresa_id:
                query += " AND EmpresaID = %s"
                params.append(empresa_id)
            if estatus:
                query += " AND EstatusSolicitud = %s"
                params.append(estatus)
            
            query += " ORDER BY FechaSolicitud DESC"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            solicitudes = []
            for row in cursor.fetchall():
                sol = dict(row)
                sol['SolicitudID'] = str(sol['SolicitudID'])
                solicitudes.append(sol)
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM CRM_ClientesSolicitudesAlta WHERE Activo = 1"
            cursor.execute(count_query)
            total = cursor.fetchone()['total']
            
            return {
                "solicitudes": solicitudes,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    def enviar_solicitud(self, solicitud_id: str, usuario_id: str) -> Dict[str, Any]:
        """Envía solicitud para revisión"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT EstatusSolicitud, FolioSolicitud FROM CRM_ClientesSolicitudesAlta
                WHERE SolicitudID = %s AND Activo = 1
            """, (solicitud_id,))
            sol = cursor.fetchone()
            
            if not sol:
                raise ValueError("Solicitud no encontrada")
            if sol['EstatusSolicitud'] != 'BORRADOR':
                raise ValueError(f"Solo se pueden enviar solicitudes en BORRADOR. Actual: {sol['EstatusSolicitud']}")
            
            now_utc = self._now_utc()
            cursor.execute("""
                UPDATE CRM_ClientesSolicitudesAlta SET
                    EstatusSolicitud = 'ENVIADA',
                    FechaEnvio = %s,
                    UpdatedBy = %s,
                    UpdatedAt = %s
                WHERE SolicitudID = %s
            """, (now_utc, usuario_id, now_utc, solicitud_id))
            
            cursor.execute("""
                INSERT INTO CRM_ClientesSolicitudesAltaHistorial 
                (SolicitudID, EstatusAnterior, EstatusNuevo, Comentario, CambiadoPorUserID)
                VALUES (%s, 'BORRADOR', 'ENVIADA', 'Solicitud enviada para revisión', %s)
            """, (solicitud_id, usuario_id))
            
            conn.commit()
            
            return {"solicitud_id": solicitud_id, "folio": sol['FolioSolicitud'], "estatus": "ENVIADA"}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def autorizar_solicitud(self, solicitud_id: str, usuario_id: str, comentarios: Optional[str] = None) -> Dict[str, Any]:
        """Autoriza solicitud y crea cliente en catálogo maestro"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT * FROM CRM_ClientesSolicitudesAlta
                WHERE SolicitudID = %s AND Activo = 1
            """, (solicitud_id,))
            sol = cursor.fetchone()
            
            if not sol:
                raise ValueError("Solicitud no encontrada")
            if sol['EstatusSolicitud'] not in ('ENVIADA', 'EN_REVISION'):
                raise ValueError(f"Solo se pueden autorizar solicitudes ENVIADAS. Actual: {sol['EstatusSolicitud']}")
            
            now_utc = self._now_utc()
            
            # Crear cliente en catálogo maestro
            cursor.execute("""
                INSERT INTO Cliente_Catalogo (
                    RFC, RazonSocial, NombreComercial, TipoPersona,
                    RegimenFiscal, UsoCfdi, CorreoPrincipal,
                    DireccionCalle, DireccionNumeroExterior, DireccionNumeroInterior,
                    DireccionColonia, DireccionMunicipio, DireccionCiudad,
                    DireccionEstado, DireccionCodigoPostal, DireccionPais,
                    LimiteCredito, DiasCredito,
                    EmailPrincipal, Activo
                ) VALUES (
                    %s, %s, %s, 'MORAL', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1
                )
            """, (
                sol['RFC'],
                sol['RazonSocial'],
                sol['NombreComercial'],
                sol['RegimenFiscal'],
                sol['UsoCFDI'],
                sol['EmailFacturacion'],
                sol['Calle'],
                sol['NumeroExterior'],
                sol['NumeroInterior'],
                sol['Colonia'],
                sol['Municipio'],
                sol['Ciudad'],
                sol['Estado'],
                sol['CodigoPostal'],
                sol['Pais'],
                sol['LimiteCreditoSolicitado'] or 0,
                sol['DiasCreditoSolicitados'] or 0,
                sol['ContactoPrincipalEmail']
            ))
            
            # Obtener ID del cliente creado
            cursor.execute("SELECT SCOPE_IDENTITY() as cliente_id")
            cliente_id = cursor.fetchone()['cliente_id']
            
            # Actualizar solicitud
            cursor.execute("""
                UPDATE CRM_ClientesSolicitudesAlta SET
                    EstatusSolicitud = 'APROBADA',
                    ClienteIDGenerado = %s,
                    AutorizadoPorUserID = %s,
                    FechaAutorizacion = %s,
                    UpdatedBy = %s,
                    UpdatedAt = %s
                WHERE SolicitudID = %s
            """, (cliente_id, usuario_id, now_utc, usuario_id, now_utc, solicitud_id))
            
            # Si hay cuenta asociada, ligarla
            if sol['CuentaID']:
                cursor.execute("""
                    UPDATE CRM_Cuentas SET
                        ClienteID = %s,
                        TipoCuenta = 'CLIENTE',
                        RazonSocialSnapshot = %s,
                        RFCSnapshot = %s,
                        UpdatedBy = %s,
                        UpdatedAt = %s
                    WHERE CuentaID = %s
                """, (cliente_id, sol['RazonSocial'], sol['RFC'], usuario_id, now_utc, str(sol['CuentaID'])))
            
            cursor.execute("""
                INSERT INTO CRM_ClientesSolicitudesAltaHistorial 
                (SolicitudID, EstatusAnterior, EstatusNuevo, Comentario, CambiadoPorUserID)
                VALUES (%s, %s, 'APROBADA', %s, %s)
            """, (solicitud_id, sol['EstatusSolicitud'], comentarios or 'Solicitud aprobada', usuario_id))
            
            conn.commit()
            
            logger.info(f"[CRM] Solicitud {sol['FolioSolicitud']} aprobada -> Cliente ID {cliente_id}")
            
            return {
                "solicitud_id": solicitud_id,
                "folio": sol['FolioSolicitud'],
                "estatus": "APROBADA",
                "cliente_id": cliente_id,
                "razon_social": sol['RazonSocial']
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error autorizando solicitud: {e}")
            raise
        finally:
            conn.close()
    
    def rechazar_solicitud(self, solicitud_id: str, usuario_id: str, motivo: str) -> Dict[str, Any]:
        """Rechaza solicitud de alta"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT EstatusSolicitud, FolioSolicitud FROM CRM_ClientesSolicitudesAlta
                WHERE SolicitudID = %s AND Activo = 1
            """, (solicitud_id,))
            sol = cursor.fetchone()
            
            if not sol:
                raise ValueError("Solicitud no encontrada")
            
            now_utc = self._now_utc()
            cursor.execute("""
                UPDATE CRM_ClientesSolicitudesAlta SET
                    EstatusSolicitud = 'RECHAZADA',
                    RechazadoPorUserID = %s,
                    FechaRechazo = %s,
                    MotivoRechazo = %s,
                    UpdatedBy = %s,
                    UpdatedAt = %s
                WHERE SolicitudID = %s
            """, (usuario_id, now_utc, motivo, usuario_id, now_utc, solicitud_id))
            
            cursor.execute("""
                INSERT INTO CRM_ClientesSolicitudesAltaHistorial 
                (SolicitudID, EstatusAnterior, EstatusNuevo, Comentario, CambiadoPorUserID)
                VALUES (%s, %s, 'RECHAZADA', %s, %s)
            """, (solicitud_id, sol['EstatusSolicitud'], f'Rechazada: {motivo}', usuario_id))
            
            conn.commit()
            
            return {"solicitud_id": solicitud_id, "folio": sol['FolioSolicitud'], "estatus": "RECHAZADA", "motivo": motivo}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # ACTIVIDADES
    # ============================================================
    
    def crear_actividad(self, data: Dict, usuario_id: str) -> Dict[str, Any]:
        """Crea una actividad"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            actividad_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO CRM_Actividades (
                    ActividadID, EmpresaID, TipoActividadID,
                    EntidadTipo, EntidadID, Titulo, Descripcion, Prioridad,
                    FechaProgramada, FechaFin, Duracion, TodoElDia,
                    AsignadoAUserID, CreadoPorUserID,
                    EstatusActividadID, TieneRecordatorio, MinutosAntes
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                actividad_id,
                data['empresa_id'],
                data['tipo_actividad_id'],
                data['entidad_tipo'],
                data['entidad_id'],
                data['titulo'],
                data.get('descripcion'),
                data.get('prioridad', 2),
                data['fecha_programada'],
                data.get('fecha_fin'),
                data.get('duracion'),
                data.get('todo_el_dia', False),
                data.get('asignado_a_user_id', usuario_id),
                usuario_id,
                1,  # Pendiente
                data.get('tiene_recordatorio', False),
                data.get('minutos_antes')
            ))
            
            conn.commit()
            
            return {"actividad_id": actividad_id, "titulo": data['titulo'], "estatus": "Pendiente"}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def listar_actividades(
        self,
        empresa_id: Optional[str] = None,
        entidad_tipo: Optional[str] = None,
        entidad_id: Optional[str] = None,
        asignado_a: Optional[str] = None,
        estatus: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista actividades con filtros"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    a.ActividadID, a.TipoActividadID, t.Nombre as TipoNombre, t.Icono, t.Color,
                    a.EntidadTipo, a.EntidadID, a.Titulo, a.Prioridad,
                    a.FechaProgramada, a.FechaRealizacion,
                    a.AsignadoAUserID, a.EstatusActividadID, e.Nombre as EstatusNombre
                FROM CRM_Actividades a
                LEFT JOIN CRM_Cat_TiposActividad t ON a.TipoActividadID = t.TipoID
                LEFT JOIN CRM_Cat_EstatusActividad e ON a.EstatusActividadID = e.EstatusID
                WHERE a.Activo = 1
            """
            params = []
            
            if empresa_id:
                query += " AND a.EmpresaID = %s"
                params.append(empresa_id)
            if entidad_tipo:
                query += " AND a.EntidadTipo = %s"
                params.append(entidad_tipo)
            if entidad_id:
                query += " AND a.EntidadID = %s"
                params.append(entidad_id)
            if asignado_a:
                query += " AND a.AsignadoAUserID = %s"
                params.append(asignado_a)
            if estatus:
                query += " AND a.EstatusActividadID = %s"
                params.append(estatus)
            
            query += " ORDER BY a.FechaProgramada ASC"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            actividades = []
            for row in cursor.fetchall():
                act = dict(row)
                act['ActividadID'] = str(act['ActividadID'])
                act['EntidadID'] = str(act['EntidadID'])
                if act.get('AsignadoAUserID'):
                    act['AsignadoAUserID'] = str(act['AsignadoAUserID'])
                actividades.append(act)
            
            return {
                "actividades": actividades,
                "total": len(actividades),
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    def cerrar_actividad(self, actividad_id: str, usuario_id: str, resultado_id: Optional[int] = None, notas: Optional[str] = None) -> Dict[str, Any]:
        """Cierra una actividad"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            now_utc = self._now_utc()
            cursor.execute("""
                UPDATE CRM_Actividades SET
                    EstatusActividadID = 3,
                    FechaRealizacion = %s,
                    ResultadoID = %s,
                    Notas = %s,
                    UpdatedAt = %s
                WHERE ActividadID = %s
            """, (now_utc, resultado_id, notas, now_utc, actividad_id))
            
            conn.commit()
            
            return {"actividad_id": actividad_id, "estatus": "Completada"}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # COTIZACIONES (WRAPPER Venta_Cotizaciones)
    # ============================================================
    
    def listar_cotizaciones(
        self,
        cliente_id: Optional[int] = None,
        cuenta_id: Optional[str] = None,
        estatus_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista cotizaciones comerciales"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    c.CotizacionID, c.Serie, c.FolioCotizacion, c.FechaCotizacion,
                    c.FechaVigencia, c.ClienteID, cl.RazonSocial as ClienteRazonSocial,
                    c.MonedaID, c.TipoCambio, c.EstatusCotizacionID,
                    c.Subtotal, c.DescuentoTotal, c.ImpuestoTotal, c.Total,
                    c.AtencionA, c.EmailCliente, c.Observaciones,
                    c.PedidoID, c.Activo, c.CreatedAt,
                    c.CRM_OportunidadID, c.CRM_CuentaID, c.EstatusComercial
                FROM Venta_Cotizaciones c
                LEFT JOIN Cliente_Catalogo cl ON c.ClienteID = cl.ClienteID
                WHERE c.Activo = 1
            """
            params = []
            
            if cliente_id:
                query += " AND c.ClienteID = %s"
                params.append(cliente_id)
            if cuenta_id:
                query += " AND c.CRM_CuentaID = %s"
                params.append(cuenta_id)
            if estatus_id:
                query += " AND c.EstatusCotizacionID = %s"
                params.append(estatus_id)
            if fecha_desde:
                query += " AND c.FechaCotizacion >= %s"
                params.append(fecha_desde)
            if fecha_hasta:
                query += " AND c.FechaCotizacion <= %s"
                params.append(fecha_hasta)
            
            query += " ORDER BY c.FechaCotizacion DESC"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            cotizaciones = []
            for row in cursor.fetchall():
                cot = dict(row)
                if cot.get('CRM_OportunidadID'):
                    cot['CRM_OportunidadID'] = str(cot['CRM_OportunidadID'])
                if cot.get('CRM_CuentaID'):
                    cot['CRM_CuentaID'] = str(cot['CRM_CuentaID'])
                cotizaciones.append(cot)
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM Venta_Cotizaciones WHERE Activo = 1"
            cursor.execute(count_query)
            total = cursor.fetchone()['total']
            
            return {
                "cotizaciones": cotizaciones,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    def obtener_cotizacion(self, cotizacion_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene detalle de una cotización"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT c.*, cl.RazonSocial as ClienteRazonSocial, cl.RFC as ClienteRFC
                FROM Venta_Cotizaciones c
                LEFT JOIN Cliente_Catalogo cl ON c.ClienteID = cl.ClienteID
                WHERE c.CotizacionID = %s
            """, (cotizacion_id,))
            
            cot = cursor.fetchone()
            if not cot:
                return None
            
            result = dict(cot)
            for field in ['CRM_OportunidadID', 'CRM_CuentaID', 'CRM_LeadID', 'CreatedByUserID', 'UpdatedByUserID']:
                if result.get(field):
                    result[field] = str(result[field])
            
            # Obtener detalle
            cursor.execute("""
                SELECT * FROM Venta_CotizacionesDetalle WHERE CotizacionID = %s ORDER BY Renglon
            """, (cotizacion_id,))
            result['detalle'] = [dict(r) for r in cursor.fetchall()]
            
            return result
            
        finally:
            conn.close()
    
    def crear_cotizacion(self, data: Dict, usuario_id: str) -> Dict[str, Any]:
        """Crea una cotización comercial"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            now_utc = self._now_utc()
            
            # Generar folio
            cursor.execute("""
                SELECT COALESCE(MAX(CAST(SUBSTRING(FolioCotizacion, 5, 10) AS INT)), 0) + 1 as seq
                FROM Venta_Cotizaciones
                WHERE FolioCotizacion LIKE 'COT-%'
            """)
            seq = cursor.fetchone()['seq']
            folio = f"COT-{seq:06d}"
            
            cursor.execute("""
                INSERT INTO Venta_Cotizaciones (
                    Serie, FolioCotizacion, FechaCotizacion, FechaVigencia,
                    ClienteID, ClienteDireccionID, ListaPrecioID, CondicionPagoID,
                    MonedaID, TipoCambio, EstatusCotizacionID,
                    Subtotal, DescuentoTotal, ImpuestoTotal, Total,
                    AtencionA, EmailCliente, TelefonoCliente, Observaciones, TerminosCondiciones,
                    CRM_OportunidadID, CRM_CuentaID, CRM_LeadID,
                    CreatedByUserID, EstatusComercial,
                    Activo, CreatedAt, CreatedBy
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                data.get('serie', 'A'),
                folio,
                now_utc,
                data.get('fecha_vigencia'),
                data['cliente_id'],
                data.get('cliente_direccion_id'),
                data.get('lista_precio_id'),
                data.get('condicion_pago_id'),
                data.get('moneda_id', 1),
                data.get('tipo_cambio', 1),
                1,  # Borrador
                data.get('subtotal', 0),
                data.get('descuento_total', 0),
                data.get('impuesto_total', 0),
                data.get('total', 0),
                data.get('atencion_a'),
                data.get('email_cliente'),
                data.get('telefono_cliente'),
                data.get('observaciones'),
                data.get('terminos_condiciones'),
                data.get('oportunidad_id'),
                data.get('cuenta_id'),
                data.get('lead_id'),
                usuario_id,
                'BORRADOR',
                True,
                now_utc,
                usuario_id
            ))
            
            # Obtener ID generado
            cursor.execute("SELECT SCOPE_IDENTITY() as cotizacion_id")
            cotizacion_id = cursor.fetchone()['cotizacion_id']
            
            # Insertar detalle si viene
            if data.get('detalle'):
                for i, det in enumerate(data['detalle'], 1):
                    cursor.execute("""
                        INSERT INTO Venta_CotizacionesDetalle (
                            CotizacionID, Renglon, ProductoID, Descripcion, Cantidad,
                            PrecioUnitario, Descuento, Impuesto, Subtotal, Total
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        cotizacion_id, i, det['producto_id'], det.get('descripcion'),
                        det['cantidad'], det['precio_unitario'],
                        det.get('descuento', 0), det.get('impuesto', 0),
                        det.get('subtotal', 0), det.get('total', 0)
                    ))
            
            conn.commit()
            
            logger.info(f"[CRM] Cotización creada: {folio}")
            
            return {
                "cotizacion_id": cotizacion_id,
                "folio_cotizacion": folio,
                "estatus": "BORRADOR"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error creando cotización: {e}")
            raise
        finally:
            conn.close()
    
    def enviar_cotizacion(self, cotizacion_id: int, usuario_id: str) -> Dict[str, Any]:
        """Envía cotización al cliente"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                UPDATE Venta_Cotizaciones SET
                    EstatusCotizacionID = 2,
                    EstatusComercial = 'ENVIADA',
                    ModifiedAt = %s,
                    ModifiedBy = %s,
                    UpdatedByUserID = %s
                WHERE CotizacionID = %s AND EstatusCotizacionID = 1
            """, (self._now_utc(), usuario_id, usuario_id, cotizacion_id))
            
            if cursor.rowcount == 0:
                raise ValueError("Cotización no encontrada o no está en borrador")
            
            conn.commit()
            
            return {"cotizacion_id": cotizacion_id, "estatus": "ENVIADA"}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def aprobar_cotizacion(self, cotizacion_id: int, usuario_id: str) -> Dict[str, Any]:
        """Aprueba cotización (cliente acepta)"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                UPDATE Venta_Cotizaciones SET
                    EstatusCotizacionID = 3,
                    EstatusComercial = 'APROBADA',
                    ModifiedAt = %s,
                    ModifiedBy = %s,
                    UpdatedByUserID = %s
                WHERE CotizacionID = %s
            """, (self._now_utc(), usuario_id, usuario_id, cotizacion_id))
            
            conn.commit()
            
            return {"cotizacion_id": cotizacion_id, "estatus": "APROBADA"}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # PEDIDOS (WRAPPER Venta_Pedidos)
    # ============================================================
    
    def listar_pedidos(
        self,
        cliente_id: Optional[int] = None,
        cuenta_id: Optional[str] = None,
        estatus_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista pedidos de venta"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    p.PedidoID, p.Serie, p.FolioPedido, p.FechaPedido,
                    p.FechaCompromiso, p.ClienteID, cl.RazonSocial as ClienteRazonSocial,
                    p.MonedaID, p.TipoCambio, p.EstatusPedidoID,
                    p.Subtotal, p.DescuentoTotal, p.ImpuestoTotal, p.Total,
                    p.CotizacionID, p.VentaID, p.Observaciones,
                    p.Activo, p.CreatedAt,
                    p.CRM_OportunidadID, p.CRM_CuentaID, p.EstatusComercial
                FROM Venta_Pedidos p
                LEFT JOIN Cliente_Catalogo cl ON p.ClienteID = cl.ClienteID
                WHERE p.Activo = 1
            """
            params = []
            
            if cliente_id:
                query += " AND p.ClienteID = %s"
                params.append(cliente_id)
            if cuenta_id:
                query += " AND p.CRM_CuentaID = %s"
                params.append(cuenta_id)
            if estatus_id:
                query += " AND p.EstatusPedidoID = %s"
                params.append(estatus_id)
            if fecha_desde:
                query += " AND p.FechaPedido >= %s"
                params.append(fecha_desde)
            if fecha_hasta:
                query += " AND p.FechaPedido <= %s"
                params.append(fecha_hasta)
            
            query += " ORDER BY p.FechaPedido DESC"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            pedidos = []
            for row in cursor.fetchall():
                ped = dict(row)
                if ped.get('CRM_OportunidadID'):
                    ped['CRM_OportunidadID'] = str(ped['CRM_OportunidadID'])
                if ped.get('CRM_CuentaID'):
                    ped['CRM_CuentaID'] = str(ped['CRM_CuentaID'])
                pedidos.append(ped)
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM Venta_Pedidos WHERE Activo = 1"
            cursor.execute(count_query)
            total = cursor.fetchone()['total']
            
            return {
                "pedidos": pedidos,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    def obtener_pedido(self, pedido_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene detalle de un pedido"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT p.*, cl.RazonSocial as ClienteRazonSocial, cl.RFC as ClienteRFC
                FROM Venta_Pedidos p
                LEFT JOIN Cliente_Catalogo cl ON p.ClienteID = cl.ClienteID
                WHERE p.PedidoID = %s
            """, (pedido_id,))
            
            ped = cursor.fetchone()
            if not ped:
                return None
            
            result = dict(ped)
            for field in ['CRM_OportunidadID', 'CRM_CuentaID', 'CreatedByUserID', 'UpdatedByUserID']:
                if result.get(field):
                    result[field] = str(result[field])
            
            # Obtener detalle
            cursor.execute("""
                SELECT * FROM Venta_PedidosDetalle WHERE PedidoID = %s ORDER BY Renglon
            """, (pedido_id,))
            result['detalle'] = [dict(r) for r in cursor.fetchall()]
            
            return result
            
        finally:
            conn.close()
    
    def crear_pedido(self, data: Dict, usuario_id: str) -> Dict[str, Any]:
        """Crea un pedido de venta"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            now_utc = self._now_utc()
            
            # Generar folio
            cursor.execute("""
                SELECT COALESCE(MAX(CAST(SUBSTRING(FolioPedido, 5, 10) AS INT)), 0) + 1 as seq
                FROM Venta_Pedidos
                WHERE FolioPedido LIKE 'PED-%'
            """)
            seq = cursor.fetchone()['seq']
            folio = f"PED-{seq:06d}"
            
            cursor.execute("""
                INSERT INTO Venta_Pedidos (
                    Serie, FolioPedido, FechaPedido, FechaCompromiso,
                    ClienteID, ClienteDireccionID, ListaPrecioID, CondicionPagoID,
                    MonedaID, TipoCambio, EstatusPedidoID,
                    Subtotal, DescuentoTotal, ImpuestoTotal, Total,
                    CotizacionID, AtencionA, Observaciones, InstruccionesEntrega,
                    CRM_OportunidadID, CRM_CuentaID,
                    CreatedByUserID, EstatusComercial,
                    Activo, CreatedAt, CreatedBy
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                data.get('serie', 'A'),
                folio,
                now_utc,
                data.get('fecha_compromiso'),
                data['cliente_id'],
                data.get('cliente_direccion_id'),
                data.get('lista_precio_id'),
                data.get('condicion_pago_id'),
                data.get('moneda_id', 1),
                data.get('tipo_cambio', 1),
                1,  # Borrador
                data.get('subtotal', 0),
                data.get('descuento_total', 0),
                data.get('impuesto_total', 0),
                data.get('total', 0),
                data.get('cotizacion_id'),
                data.get('atencion_a'),
                data.get('observaciones'),
                data.get('instrucciones_entrega'),
                data.get('oportunidad_id'),
                data.get('cuenta_id'),
                usuario_id,
                'BORRADOR',
                True,
                now_utc,
                usuario_id
            ))
            
            # Obtener ID generado
            cursor.execute("SELECT SCOPE_IDENTITY() as pedido_id")
            pedido_id = cursor.fetchone()['pedido_id']
            
            # Si viene de cotización, actualizar referencia
            if data.get('cotizacion_id'):
                cursor.execute("""
                    UPDATE Venta_Cotizaciones SET PedidoID = %s WHERE CotizacionID = %s
                """, (pedido_id, data['cotizacion_id']))
            
            # Insertar detalle
            if data.get('detalle'):
                for i, det in enumerate(data['detalle'], 1):
                    cursor.execute("""
                        INSERT INTO Venta_PedidosDetalle (
                            PedidoID, Renglon, ProductoID, Descripcion, Cantidad,
                            PrecioUnitario, Descuento, Impuesto, Subtotal, Total
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        pedido_id, i, det['producto_id'], det.get('descripcion'),
                        det['cantidad'], det['precio_unitario'],
                        det.get('descuento', 0), det.get('impuesto', 0),
                        det.get('subtotal', 0), det.get('total', 0)
                    ))
            
            conn.commit()
            
            logger.info(f"[CRM] Pedido creado: {folio}")
            
            return {
                "pedido_id": pedido_id,
                "folio_pedido": folio,
                "estatus": "BORRADOR"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error creando pedido: {e}")
            raise
        finally:
            conn.close()
    
    def confirmar_pedido(self, pedido_id: int, usuario_id: str) -> Dict[str, Any]:
        """Confirma un pedido"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                UPDATE Venta_Pedidos SET
                    EstatusPedidoID = 2,
                    EstatusComercial = 'CONFIRMADO',
                    ModifiedAt = %s,
                    ModifiedBy = %s,
                    UpdatedByUserID = %s
                WHERE PedidoID = %s AND EstatusPedidoID = 1
            """, (self._now_utc(), usuario_id, usuario_id, pedido_id))
            
            if cursor.rowcount == 0:
                raise ValueError("Pedido no encontrado o no está en borrador")
            
            conn.commit()
            
            return {"pedido_id": pedido_id, "estatus": "CONFIRMADO"}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # REMISIONES (Venta_Remisiones)
    # ============================================================
    
    def listar_remisiones(
        self,
        empresa_id: Optional[str] = None,
        cliente_id: Optional[int] = None,
        cuenta_id: Optional[str] = None,
        estatus_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista remisiones de venta"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    r.RemisionID, r.EmpresaID, r.FolioRemision, r.FechaRemision,
                    r.FechaCompromisoEntrega, r.FechaEntregaReal,
                    r.PedidoID, r.ClienteID, cl.RazonSocial as ClienteRazonSocial,
                    r.DireccionEntrega, r.EntregadoA, r.RecibidoPor,
                    r.Subtotal, r.DescuentoTotal, r.ImpuestosTotal, r.Total,
                    r.EstatusRemisionID, r.FacturaID, r.Activo, r.CreatedAt,
                    r.CuentaID, r.OportunidadID
                FROM Venta_Remisiones r
                LEFT JOIN Cliente_Catalogo cl ON r.ClienteID = cl.ClienteID
                WHERE r.Activo = 1
            """
            params = []
            
            if empresa_id:
                query += " AND r.EmpresaID = %s"
                params.append(empresa_id)
            if cliente_id:
                query += " AND r.ClienteID = %s"
                params.append(cliente_id)
            if cuenta_id:
                query += " AND r.CuentaID = %s"
                params.append(cuenta_id)
            if estatus_id:
                query += " AND r.EstatusRemisionID = %s"
                params.append(estatus_id)
            if fecha_desde:
                query += " AND r.FechaRemision >= %s"
                params.append(fecha_desde)
            if fecha_hasta:
                query += " AND r.FechaRemision <= %s"
                params.append(fecha_hasta)
            
            query += " ORDER BY r.FechaRemision DESC"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            remisiones = []
            for row in cursor.fetchall():
                rem = dict(row)
                for field in ['EmpresaID', 'CuentaID', 'OportunidadID']:
                    if rem.get(field):
                        rem[field] = str(rem[field])
                remisiones.append(rem)
            
            # Contar total
            count_query = "SELECT COUNT(*) as total FROM Venta_Remisiones WHERE Activo = 1"
            cursor.execute(count_query)
            total = cursor.fetchone()['total']
            
            return {
                "remisiones": remisiones,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    def obtener_remision(self, remision_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene detalle de una remisión"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT r.*, cl.RazonSocial as ClienteRazonSocial, cl.RFC as ClienteRFC
                FROM Venta_Remisiones r
                LEFT JOIN Cliente_Catalogo cl ON r.ClienteID = cl.ClienteID
                WHERE r.RemisionID = %s
            """, (remision_id,))
            
            rem = cursor.fetchone()
            if not rem:
                return None
            
            result = dict(rem)
            for field in ['EmpresaID', 'SucursalID', 'CuentaID', 'OportunidadID', 'DocumentoID', 'CreatedBy', 'UpdatedBy']:
                if result.get(field):
                    result[field] = str(result[field])
            
            # Obtener detalle
            cursor.execute("""
                SELECT * FROM Venta_RemisionesDetalle WHERE RemisionID = %s ORDER BY Renglon
            """, (remision_id,))
            result['detalle'] = [dict(r) for r in cursor.fetchall()]
            
            return result
            
        finally:
            conn.close()
    
    def crear_remision(self, data: Dict, usuario_id: str) -> Dict[str, Any]:
        """Crea una remisión de venta"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            now_utc = self._now_utc()
            today = date.today()
            
            # Generar folio
            cursor.execute("""
                SELECT COALESCE(MAX(CAST(SUBSTRING(FolioRemision, 5, 10) AS INT)), 0) + 1 as seq
                FROM Venta_Remisiones
                WHERE FolioRemision LIKE 'REM-%'
            """)
            seq = cursor.fetchone()['seq']
            folio = f"REM-{seq:06d}"
            
            cursor.execute("""
                INSERT INTO Venta_Remisiones (
                    EmpresaID, SucursalID, AlmacenID, FolioRemision,
                    PedidoID, CotizacionID, OportunidadID, CuentaID,
                    ClienteID, ContactoID, FechaRemision, FechaCompromisoEntrega,
                    DireccionEntrega, MonedaID, TipoCambio,
                    Subtotal, DescuentoTotal, ImpuestosTotal, Total,
                    EstatusRemisionID, Observaciones, ObservacionesInternas,
                    Activo, CreatedBy, CreatedAt
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                data['empresa_id'],
                data.get('sucursal_id'),
                data.get('almacen_id'),
                folio,
                data.get('pedido_id'),
                data.get('cotizacion_id'),
                data.get('oportunidad_id'),
                data.get('cuenta_id'),
                data['cliente_id'],
                data.get('contacto_id'),
                today,
                data.get('fecha_compromiso_entrega'),
                data.get('direccion_entrega'),
                data.get('moneda_id', 1),
                data.get('tipo_cambio', 1),
                data.get('subtotal', 0),
                data.get('descuento_total', 0),
                data.get('impuestos_total', 0),
                data.get('total', 0),
                1,  # Pendiente
                data.get('observaciones'),
                data.get('observaciones_internas'),
                True,
                usuario_id,
                now_utc
            ))
            
            # Obtener ID generado
            cursor.execute("SELECT SCOPE_IDENTITY() as remision_id")
            remision_id = cursor.fetchone()['remision_id']
            
            # Insertar detalle
            if data.get('detalle'):
                for i, det in enumerate(data['detalle'], 1):
                    cursor.execute("""
                        INSERT INTO Venta_RemisionesDetalle (
                            RemisionID, Renglon, ProductoID, Descripcion, Cantidad,
                            PrecioUnitario, Descuento, Impuesto, Subtotal, Total
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        remision_id, i, det['producto_id'], det.get('descripcion'),
                        det['cantidad'], det['precio_unitario'],
                        det.get('descuento', 0), det.get('impuesto', 0),
                        det.get('subtotal', 0), det.get('total', 0)
                    ))
            
            conn.commit()
            
            logger.info(f"[CRM] Remisión creada: {folio}")
            
            return {
                "remision_id": remision_id,
                "folio_remision": folio,
                "estatus": "PENDIENTE"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM] Error creando remisión: {e}")
            raise
        finally:
            conn.close()
    
    def registrar_entrega(self, remision_id: int, usuario_id: str, entregado_a: str, recibido_por: str) -> Dict[str, Any]:
        """Registra entrega de una remisión"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            now_utc = self._now_utc()
            cursor.execute("""
                UPDATE Venta_Remisiones SET
                    EstatusRemisionID = 2,
                    FechaEntregaReal = %s,
                    EntregadoA = %s,
                    RecibidoPor = %s,
                    UpdatedBy = %s,
                    UpdatedAt = %s
                WHERE RemisionID = %s
            """, (now_utc, entregado_a, recibido_por, usuario_id, now_utc, remision_id))
            
            conn.commit()
            
            return {"remision_id": remision_id, "estatus": "ENTREGADA", "fecha_entrega": str(now_utc)}
            
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
