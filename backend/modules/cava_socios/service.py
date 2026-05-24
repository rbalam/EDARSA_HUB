"""
EDARSA HUB - Cava de Socios Service
====================================
Servicio principal para gestión de cava de socios.

Funcionalidades:
- CRUD de socios
- Gestión de botellas en custodia
- Registro de movimientos (entradas, consumos, retiros)
- Cargos por servicios
- Reportes e historial
"""

import pymssql
import os
import logging
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CavaSociosService:
    """Servicio principal para el módulo Cava de Socios."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def _get_connection(self):
        return pymssql.connect(
            server=self.db_config.get('host'),
            port=self.db_config.get('port', 1433),
            database=self.db_config.get('database'),
            user=self.db_config.get('username'),
            password=self.db_config.get('password'),
            autocommit=False
        )
    
    # ==================== SOCIOS ====================
    
    def listar_socios(self, empresa_id: str, estatus: Optional[str] = None,
                      skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Lista socios de cava con paginación."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where = ["EmpresaID = %s"]
            params = [empresa_id]
            
            if estatus:
                where.append("Estatus = %s")
                params.append(estatus)
            
            # Count
            cursor.execute(f"""
                SELECT COUNT(*) as total FROM CavaSocios_Socios
                WHERE {' AND '.join(where)}
            """, params)
            total = cursor.fetchone()['total']
            
            # Data
            cursor.execute(f"""
                SELECT 
                    s.*,
                    (SELECT COUNT(*) FROM CavaSocios_Botellas b 
                     WHERE b.SocioID = s.SocioID AND b.EstatusBotella = 'EN_CAVA') as botellas_en_cava
                FROM CavaSocios_Socios s
                WHERE {' AND '.join(where)}
                ORDER BY s.NombreCompleto
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """, params + [skip, limit])
            
            socios = []
            for row in cursor.fetchall():
                socios.append({
                    "socio_id": str(row['SocioID']),
                    "numero_socio": row['NumeroSocio'],
                    "nombre_completo": row['NombreCompleto'],
                    "email": row['Email'],
                    "telefono": row['Telefono'],
                    "tipo_membresia": row['TipoMembresia'],
                    "fecha_vencimiento": row['FechaVencimientoMembresia'].isoformat() if row['FechaVencimientoMembresia'] else None,
                    "maximo_botellas": row['MaximoBotellas'],
                    "botellas_en_cava": row['botellas_en_cava'],
                    "estatus": row['Estatus'],
                    "cliente_crm_id": str(row['ClienteCRMID']) if row['ClienteCRMID'] else None
                })
            
            return {"socios": socios, "total": total, "skip": skip, "limit": limit}
            
        finally:
            conn.close()
    
    def obtener_socio(self, socio_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalle de un socio con sus botellas."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT * FROM CavaSocios_Socios WHERE SocioID = %s
            """, (socio_id,))
            
            socio = cursor.fetchone()
            if not socio:
                return None
            
            # Obtener botellas
            cursor.execute("""
                SELECT * FROM CavaSocios_Botellas 
                WHERE SocioID = %s
                ORDER BY FechaIngreso DESC
            """, (socio_id,))
            
            botellas = []
            valor_total = 0
            for b in cursor.fetchall():
                valor = float(b['ValorDeclarado'] or 0)
                valor_total += valor if b['EstatusBotella'] == 'EN_CAVA' else 0
                botellas.append({
                    "botella_id": str(b['BotellaID']),
                    "producto_nombre": b['ProductoNombre'],
                    "marca": b['Marca'],
                    "tipo_bebida": b['TipoBebida'],
                    "añada": b['Añada'],
                    "capacidad": b['Capacidad'],
                    "ubicacion": b['UbicacionCava'],
                    "valor_declarado": valor,
                    "nivel_actual": float(b['NivelActual'] or 100),
                    "estatus": b['EstatusBotella'],
                    "fecha_ingreso": b['FechaIngreso'].isoformat() if b['FechaIngreso'] else None
                })
            
            # Cargos pendientes
            cursor.execute("""
                SELECT SUM(Total) as total_pendiente
                FROM CavaSocios_Cargos 
                WHERE SocioID = %s AND EstatusCargo = 'PENDIENTE'
            """, (socio_id,))
            
            cargos = cursor.fetchone()
            
            return {
                "socio_id": str(socio['SocioID']),
                "empresa_id": str(socio['EmpresaID']),
                "numero_socio": socio['NumeroSocio'],
                "nombre_completo": socio['NombreCompleto'],
                "email": socio['Email'],
                "telefono": socio['Telefono'],
                "tipo_membresia": socio['TipoMembresia'],
                "fecha_alta": socio['FechaAltaMembresia'].isoformat() if socio['FechaAltaMembresia'] else None,
                "fecha_vencimiento": socio['FechaVencimientoMembresia'].isoformat() if socio['FechaVencimientoMembresia'] else None,
                "maximo_botellas": socio['MaximoBotellas'],
                "estatus": socio['Estatus'],
                "botellas": botellas,
                "total_botellas_en_cava": len([b for b in botellas if b['estatus'] == 'EN_CAVA']),
                "valor_total_declarado": valor_total,
                "saldo_pendiente": float(cargos['total_pendiente'] or 0),
                "observaciones": socio['Observaciones']
            }
            
        finally:
            conn.close()
    
    def crear_socio(self, empresa_id: str, data: Dict[str, Any], 
                    usuario_id: str) -> Dict[str, Any]:
        """Crea un nuevo socio de cava."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            socio_id = str(uuid.uuid4())
            numero_socio = data.get('numero_socio') or self._generar_numero_socio(cursor, empresa_id)
            
            cursor.execute("""
                INSERT INTO CavaSocios_Socios (
                    SocioID, EmpresaID, NumeroSocio, NombreCompleto,
                    Email, Telefono, ClienteCRMID, TipoMembresia,
                    FechaAltaMembresia, FechaVencimientoMembresia,
                    MaximoBotellas, Estatus, UsuarioCreacionID, Observaciones
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                socio_id, empresa_id, numero_socio, data['nombre_completo'],
                data.get('email'), data.get('telefono'), data.get('cliente_crm_id'),
                data.get('tipo_membresia', 'ESTANDAR'),
                data.get('fecha_alta') or date.today(),
                data.get('fecha_vencimiento'),
                data.get('maximo_botellas', 12),
                'ACTIVO', usuario_id, data.get('observaciones')
            ))
            
            conn.commit()
            
            logger.info(f"[CavaSocios] Socio {numero_socio} creado: {data['nombre_completo']}")
            
            return {
                "socio_id": socio_id,
                "numero_socio": numero_socio,
                "mensaje": "Socio creado exitosamente"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error creando socio: {e}")
            raise
        finally:
            conn.close()
    
    def _generar_numero_socio(self, cursor, empresa_id: str) -> str:
        """Genera número de socio secuencial."""
        cursor.execute("""
            SELECT MAX(CAST(SUBSTRING(NumeroSocio, 5, 10) AS INT)) as ultimo
            FROM CavaSocios_Socios
            WHERE EmpresaID = %s AND NumeroSocio LIKE 'SOC-%%'
        """, (empresa_id,))
        result = cursor.fetchone()
        siguiente = (result[0] or 0) + 1
        return f"SOC-{siguiente:05d}"
    
    # ==================== BOTELLAS ====================
    
    def registrar_botella(self, socio_id: str, empresa_id: str, 
                          data: Dict[str, Any], usuario_id: str) -> Dict[str, Any]:
        """Registra una botella nueva en la cava."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Verificar límite de botellas
            cursor.execute("""
                SELECT s.MaximoBotellas,
                       (SELECT COUNT(*) FROM CavaSocios_Botellas b 
                        WHERE b.SocioID = s.SocioID AND b.EstatusBotella = 'EN_CAVA') as actuales
                FROM CavaSocios_Socios s
                WHERE s.SocioID = %s
            """, (socio_id,))
            
            socio = cursor.fetchone()
            if not socio:
                raise ValueError("Socio no encontrado")
            
            if socio['actuales'] >= socio['MaximoBotellas']:
                raise ValueError(f"Límite de botellas alcanzado ({socio['MaximoBotellas']})")
            
            botella_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO CavaSocios_Botellas (
                    BotellaID, EmpresaID, SocioID, ProductoCodigo, ProductoNombre,
                    Marca, TipoBebida, Añada, Capacidad, UbicacionCava,
                    ValorDeclarado, EstatusBotella, NivelActual,
                    FotoIngresoURL, UsuarioCreacionID, Observaciones
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                botella_id, empresa_id, socio_id,
                data.get('producto_codigo'), data['producto_nombre'],
                data.get('marca'), data.get('tipo_bebida'),
                data.get('añada'), data.get('capacidad', 750),
                data.get('ubicacion'), data.get('valor_declarado', 0),
                'EN_CAVA', 100,
                data.get('foto_url'), usuario_id, data.get('observaciones')
            ))
            
            # Registrar movimiento de entrada
            mov_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO CavaSocios_Movimientos (
                    MovimientoID, EmpresaID, BotellaID, SocioID,
                    TipoMovimiento, NivelAnterior, NivelNuevo,
                    MotivoMovimiento, UsuarioCreacionID
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                mov_id, empresa_id, botella_id, socio_id,
                'ENTRADA', 0, 100, 'Ingreso de botella a cava', usuario_id
            ))
            
            conn.commit()
            
            logger.info(f"[CavaSocios] Botella registrada: {data['producto_nombre']} para socio {socio_id}")
            
            return {
                "botella_id": botella_id,
                "movimiento_id": mov_id,
                "mensaje": "Botella registrada exitosamente"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error registrando botella: {e}")
            raise
        finally:
            conn.close()
    
    def registrar_consumo(self, botella_id: str, data: Dict[str, Any],
                          usuario_id: str) -> Dict[str, Any]:
        """Registra un consumo parcial o total de botella."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener botella actual
            cursor.execute("""
                SELECT b.*, s.SocioID, s.EmpresaID 
                FROM CavaSocios_Botellas b
                INNER JOIN CavaSocios_Socios s ON b.SocioID = s.SocioID
                WHERE b.BotellaID = %s
            """, (botella_id,))
            
            botella = cursor.fetchone()
            if not botella:
                raise ValueError("Botella no encontrada")
            
            if botella['EstatusBotella'] != 'EN_CAVA':
                raise ValueError(f"Botella no disponible. Estado: {botella['EstatusBotella']}")
            
            nivel_anterior = float(botella['NivelActual'] or 100)
            porcentaje_consumido = float(data.get('porcentaje_consumido', 100))
            
            if porcentaje_consumido > nivel_anterior:
                raise ValueError(f"No hay suficiente contenido. Disponible: {nivel_anterior}%")
            
            nivel_nuevo = nivel_anterior - porcentaje_consumido
            es_consumo_total = nivel_nuevo <= 0
            
            tipo_movimiento = 'CONSUMO_TOTAL' if es_consumo_total else 'CONSUMO_PARCIAL'
            nuevo_estatus = 'CONSUMIDA' if es_consumo_total else 'EN_CAVA'
            
            # Actualizar botella
            cursor.execute("""
                UPDATE CavaSocios_Botellas SET
                    NivelActual = %s,
                    EstatusBotella = %s,
                    FechaConsumo = CASE WHEN %s = 1 THEN GETUTCDATE() ELSE FechaConsumo END,
                    FechaModificacion = GETUTCDATE(),
                    UsuarioModificacionID = %s
                WHERE BotellaID = %s
            """, (nivel_nuevo, nuevo_estatus, es_consumo_total, usuario_id, botella_id))
            
            # Registrar movimiento
            mov_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO CavaSocios_Movimientos (
                    MovimientoID, EmpresaID, BotellaID, SocioID,
                    TipoMovimiento, NivelAnterior, NivelNuevo,
                    MotivoMovimiento, ReservacionID, MeseroID,
                    FotoEvidenciaURL, UsuarioCreacionID, Observaciones
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                mov_id, botella['EmpresaID'], botella_id, botella['SocioID'],
                tipo_movimiento, nivel_anterior, nivel_nuevo,
                data.get('motivo', 'Consumo registrado'),
                data.get('reservacion_id'), data.get('mesero_id'),
                data.get('foto_evidencia'), usuario_id, data.get('observaciones')
            ))
            
            # Generar cargo por descorche si aplica
            cargo_id = None
            if data.get('generar_cargo_descorche'):
                cargo_id = self._crear_cargo(
                    cursor, botella['EmpresaID'], botella['SocioID'],
                    'SERVICIO_DESCORCHE', f"Descorche: {botella['ProductoNombre']}",
                    data.get('monto_descorche', 350), botella_id, mov_id, usuario_id
                )
            
            conn.commit()
            
            logger.info(f"[CavaSocios] Consumo registrado: {porcentaje_consumido}% de {botella['ProductoNombre']}")
            
            return {
                "movimiento_id": mov_id,
                "nivel_anterior": nivel_anterior,
                "nivel_nuevo": nivel_nuevo,
                "tipo_movimiento": tipo_movimiento,
                "cargo_id": cargo_id,
                "mensaje": f"{'Botella consumida totalmente' if es_consumo_total else f'Consumo de {porcentaje_consumido}% registrado'}"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error registrando consumo: {e}")
            raise
        finally:
            conn.close()
    
    def _crear_cargo(self, cursor, empresa_id: str, socio_id: str,
                     tipo: str, concepto: str, monto: float,
                     botella_id: str = None, movimiento_id: str = None,
                     usuario_id: str = None) -> str:
        """Crea un cargo para el socio."""
        cargo_id = str(uuid.uuid4())
        impuesto = monto * 0.16  # IVA
        total = monto + impuesto
        
        cursor.execute("""
            INSERT INTO CavaSocios_Cargos (
                CargoID, EmpresaID, SocioID, TipoCargo, ConceptoCargo,
                Monto, Impuesto, Total, BotellaID, MovimientoID,
                UsuarioCreacionID
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            cargo_id, empresa_id, socio_id, tipo, concepto,
            monto, impuesto, total, botella_id, movimiento_id, usuario_id
        ))
        
        return cargo_id
    
    # ==================== DASHBOARD / REPORTES ====================
    
    def obtener_dashboard(self, empresa_id: str) -> Dict[str, Any]:
        """Obtiene KPIs del módulo Cava de Socios."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # KPIs de socios
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_socios,
                    COUNT(CASE WHEN Estatus = 'ACTIVO' THEN 1 END) as activos,
                    COUNT(CASE WHEN Estatus = 'SUSPENDIDO' THEN 1 END) as suspendidos,
                    COUNT(CASE WHEN FechaVencimientoMembresia < GETDATE() AND Estatus = 'ACTIVO' THEN 1 END) as vencidos
                FROM CavaSocios_Socios
                WHERE EmpresaID = %s
            """, (empresa_id,))
            kpis_socios = cursor.fetchone()
            
            # KPIs de botellas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_botellas,
                    COUNT(CASE WHEN EstatusBotella = 'EN_CAVA' THEN 1 END) as en_cava,
                    COUNT(CASE WHEN EstatusBotella = 'CONSUMIDA' THEN 1 END) as consumidas,
                    SUM(ValorDeclarado) as valor_total_custodia
                FROM CavaSocios_Botellas
                WHERE EmpresaID = %s
            """, (empresa_id,))
            kpis_botellas = cursor.fetchone()
            
            # KPIs de cargos
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN EstatusCargo = 'PENDIENTE' THEN Total ELSE 0 END) as pendiente_cobro,
                    SUM(CASE WHEN EstatusCargo = 'PAGADO' THEN Total ELSE 0 END) as total_cobrado,
                    COUNT(CASE WHEN EstatusCargo = 'PENDIENTE' THEN 1 END) as cargos_pendientes
                FROM CavaSocios_Cargos
                WHERE EmpresaID = %s
            """, (empresa_id,))
            kpis_cargos = cursor.fetchone()
            
            # Últimos movimientos
            cursor.execute("""
                SELECT TOP 5
                    m.MovimientoID, m.TipoMovimiento, m.FechaMovimiento,
                    b.ProductoNombre, s.NombreCompleto
                FROM CavaSocios_Movimientos m
                INNER JOIN CavaSocios_Botellas b ON m.BotellaID = b.BotellaID
                INNER JOIN CavaSocios_Socios s ON m.SocioID = s.SocioID
                WHERE m.EmpresaID = %s
                ORDER BY m.FechaMovimiento DESC
            """, (empresa_id,))
            
            ultimos_movimientos = []
            for row in cursor.fetchall():
                ultimos_movimientos.append({
                    "tipo": row['TipoMovimiento'],
                    "fecha": row['FechaMovimiento'].strftime('%Y-%m-%d %H:%M') if row['FechaMovimiento'] else None,
                    "producto": row['ProductoNombre'],
                    "socio": row['NombreCompleto']
                })
            
            return {
                "socios": {
                    "total": kpis_socios['total_socios'] or 0,
                    "activos": kpis_socios['activos'] or 0,
                    "suspendidos": kpis_socios['suspendidos'] or 0,
                    "vencidos": kpis_socios['vencidos'] or 0
                },
                "botellas": {
                    "total": kpis_botellas['total_botellas'] or 0,
                    "en_cava": kpis_botellas['en_cava'] or 0,
                    "consumidas": kpis_botellas['consumidas'] or 0,
                    "valor_custodia": float(kpis_botellas['valor_total_custodia'] or 0)
                },
                "financiero": {
                    "pendiente_cobro": float(kpis_cargos['pendiente_cobro'] or 0),
                    "total_cobrado": float(kpis_cargos['total_cobrado'] or 0),
                    "cargos_pendientes": kpis_cargos['cargos_pendientes'] or 0
                },
                "ultimos_movimientos": ultimos_movimientos
            }
            
        finally:
            conn.close()


def get_cava_socios_service() -> CavaSociosService:
    """Factory para obtener instancia del servicio."""
    db_config = {
        'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
        'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        'password': os.environ.get('EDARSAHUB_PASSWORD', '')
    }
    return CavaSociosService(db_config)
