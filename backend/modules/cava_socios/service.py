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

import logging
import uuid
from datetime import date
from typing import Dict, List, Optional, Any

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

logger = logging.getLogger(__name__)


class CavaSociosService:
    """Servicio principal para el módulo Cava de Socios."""

    def _get_connection(self):
        """Abre exclusivamente la conexión SQL canónica de EDARSAHUB."""
        return get_edarsahub_pymssql_connection(
            timeout=30,
            login_timeout=10,
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
                    "cliente_crm_id": str(row['ClienteCRMID']) if row['ClienteCRMID'] else None,
                    "persona_id": int(row['PersonaID']) if row.get('PersonaID') is not None else None
                })

            return {"socios": socios, "total": total, "skip": skip, "limit": limit}

        finally:
            conn.close()

    def obtener_socio(self, socio_id: str, empresa_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalle de un socio con sus botellas."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            cursor.execute("""
                SELECT * FROM CavaSocios_Socios
                WHERE SocioID = %s AND EmpresaID = %s
            """, (socio_id, empresa_id))

            socio = cursor.fetchone()
            if not socio:
                return None

            # Obtener botellas
            cursor.execute("""
                SELECT * FROM CavaSocios_Botellas
                WHERE SocioID = %s AND EmpresaID = %s
                ORDER BY FechaIngreso DESC
            """, (socio_id, empresa_id))

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
                WHERE SocioID = %s
                  AND EmpresaID = %s
                  AND EstatusCargo = 'PENDIENTE'
            """, (socio_id, empresa_id))

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
                "observaciones": socio['Observaciones'],
                "persona_id": int(socio['PersonaID']) if socio.get('PersonaID') is not None else None
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

    def actualizar_socio(self, socio_id: str, empresa_id: str, data: Dict[str, Any],
                         usuario_id: str) -> Dict[str, Any]:
        """Actualiza un socio de cava existente."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Verificar existencia y pertenecia a la empresa
            cursor.execute("""
                SELECT SocioID FROM CavaSocios_Socios
                WHERE SocioID = %s AND EmpresaID = %s
            """, (socio_id, empresa_id))
            if not cursor.fetchone():
                raise ValueError("Socio no encontrado o no pertenece a esta empresa")

            cursor.execute("""
                UPDATE CavaSocios_Socios
                SET NombreCompleto = %s,
                    NumeroSocio = COALESCE(%s, NumeroSocio),
                    Email = %s,
                    Telefono = %s,
                    TipoMembresia = COALESCE(%s, TipoMembresia),
                    MaximoBotellas = COALESCE(%s, MaximoBotellas),
                    FechaVencimientoMembresia = %s,
                    Observaciones = %s,
                    Estatus = COALESCE(%s, Estatus),
                    FechaModificacion = GETUTCDATE(),
                    UsuarioModificacionID = %s
                WHERE SocioID = %s AND EmpresaID = %s
            """, (
                data['nombre_completo'],
                data.get('numero_socio'),
                data.get('email'),
                data.get('telefono'),
                data.get('tipo_membresia'),
                data.get('maximo_botellas'),
                data.get('fecha_vencimiento') or None,
                data.get('observaciones'),
                data.get('estatus'),
                usuario_id,
                socio_id,
                empresa_id
            ))

            conn.commit()
            logger.info(f"[CavaSocios] Socio {socio_id} actualizado por usuario {usuario_id}")

            return {
                "socio_id": socio_id,
                "mensaje": "Socio actualizado exitosamente"
            }

        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error actualizando socio: {e}")
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
                data.get('añada'), data.get('capacidad', 1.0),
                data.get('ubicacion'), data.get('valor_declarado', 0),
                'EN_CAVA', data.get('nivel_actual', 100),
                data.get('foto_url'), usuario_id, data.get('observaciones')
            ))

            # Registrar movimiento de entrada
            mov_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO CavaSocios_Movimientos (
                    MovimientoID, EmpresaID, BotellaID, SocioID,
                    TipoMovimiento, NivelAnterior, NivelNuevo, CantidadConsumida,
                    MotivoMovimiento, UsuarioCreacionID
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                mov_id, empresa_id, botella_id, socio_id,
                'ENTRADA', 0, data.get('nivel_actual', 100), 0,
                'Ingreso de botella a cava (PZ)', usuario_id
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

    def registrar_consumo(self, botella_id: str, empresa_id: str,
                          data: Dict[str, Any], usuario_id: str) -> Dict[str, Any]:
        """Registra un consumo en puntaje/porcentaje de botella (PZ)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            # Obtener botella actual
            cursor.execute("""
                SELECT b.*, s.SocioID, s.EmpresaID
                FROM CavaSocios_Botellas b
                INNER JOIN CavaSocios_Socios s ON b.SocioID = s.SocioID
                WHERE b.BotellaID = %s AND s.EmpresaID = %s
            """, (botella_id, empresa_id))

            botella = cursor.fetchone()
            if not botella:
                raise ValueError("Botella no encontrada")

            if botella['EstatusBotella'] != 'EN_CAVA':
                raise ValueError(f"Botella no disponible. Estado: {botella['EstatusBotella']}")

            nivel_anterior = float(botella['NivelActual'] or 100)
            porcentaje_consumido = float(data.get('porcentaje_consumido', 100))

            if porcentaje_consumido > nivel_anterior:
                raise ValueError(f"No hay suficiente contenido. Disponible: {nivel_anterior}% ({nivel_anterior / 100.0:.2f} PZ)")

            nivel_nuevo = max(0.0, nivel_anterior - porcentaje_consumido)
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
                    TipoMovimiento, NivelAnterior, NivelNuevo, CantidadConsumida,
                    MotivoMovimiento, ReservacionID, MeseroID,
                    FotoEvidenciaURL, UsuarioCreacionID, Observaciones
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                mov_id, botella['EmpresaID'], botella_id, botella['SocioID'],
                tipo_movimiento, nivel_anterior, nivel_nuevo, porcentaje_consumido,
                data.get('motivo', 'Consumo registrado por puntaje de botella'),
                data.get('reservacion_id'), data.get('mesero_id'),
                data.get('foto_evidencia'), usuario_id, data.get('observaciones')
            ))

            # Generar cargo por descorche si aplica y reflejarlo en el movimiento.
            cargo_id = None
            monto_descorche = float(data.get('monto_descorche', 350) or 0)
            if data.get('generar_cargo_descorche'):
                cargo_id = self._crear_cargo(
                    cursor, botella['EmpresaID'], botella['SocioID'],
                    'SERVICIO_DESCORCHE', f"Descorche: {botella['ProductoNombre']}",
                    monto_descorche, botella_id, mov_id, usuario_id
                )
                cursor.execute("""
                    UPDATE CavaSocios_Movimientos
                       SET GeneroCargo = 1,
                           MontoCargo = %s
                     WHERE MovimientoID = %s
                       AND EmpresaID = %s
                """, (monto_descorche, mov_id, botella['EmpresaID']))

            conn.commit()

            logger.info(f"[CavaSocios] Consumo registrado: {porcentaje_consumido}% ({porcentaje_consumido / 100.0:.2f} PZ) de {botella['ProductoNombre']}")

            return {
                "movimiento_id": mov_id,
                "nivel_anterior": nivel_anterior,
                "nivel_nuevo": nivel_nuevo,
                "nivel_anterior_pz": round(nivel_anterior / 100.0, 3),
                "nivel_nuevo_pz": round(nivel_nuevo / 100.0, 3),
                "tipo_movimiento": tipo_movimiento,
                "cargo_id": cargo_id,
                "mensaje": f"{'Botella consumida totalmente' if es_consumo_total else f'Consumo de {porcentaje_consumido}% ({porcentaje_consumido / 100.0:.2f} PZ) registrado'}"
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

    # ==================== MÉTODOS PARA REPORTES ====================

    def obtener_movimientos_socio(self, socio_id: str, empresa_id: str) -> List[Dict]:
        """Obtiene todos los movimientos (consumos) de un socio."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            cursor.execute("""
                SELECT
                    m.MovimientoID,
                    m.BotellaID,
                    m.TipoMovimiento as tipo_movimiento,
                    m.CantidadConsumida as porcentaje,
                    m.MotivoMovimiento as motivo,
                    m.FechaMovimiento as fecha_movimiento,
                    m.Observaciones,
                    m.MontoCargo as monto_descorche,
                    b.ProductoNombre as producto_nombre,
                    b.Marca
                FROM CavaSocios_Movimientos m
                INNER JOIN CavaSocios_Botellas b ON m.BotellaID = b.BotellaID
                WHERE m.SocioID = %s AND m.EmpresaID = %s
                ORDER BY m.FechaMovimiento DESC
            """, (socio_id, empresa_id))

            return cursor.fetchall() or []

        finally:
            conn.close()

    def obtener_cargos_socio(self, socio_id: str, empresa_id: str) -> List[Dict]:
        """Obtiene todos los cargos de un socio."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            cursor.execute("""
                SELECT
                    c.CargoID,
                    c.ConceptoCargo as concepto,
                    c.Monto as monto_base,
                    c.Impuesto as iva,
                    c.Total as monto_total,
                    0 as monto_pagado,
                    c.EstatusCargo as estatus,
                    c.FechaCargo as fecha_cargo,
                    c.FechaPago as fecha_pago
                FROM CavaSocios_Cargos c
                WHERE c.SocioID = %s AND c.EmpresaID = %s
                ORDER BY c.FechaCargo DESC
            """, (socio_id, empresa_id))

            return cursor.fetchall() or []

        finally:
            conn.close()

    # ==================== OPERACIONES AMPLIADAS ====================

    def listar_clientes_canonicos(self, empresa_id: str, search: Optional[str] = None,
                                   skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Consulta clientes del catálogo canónico/maestro (dbo.Cliente_Catalogo) disponibles para promover a Cava de Socios."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            where = ["cc.Activo = 1"]
            params = [empresa_id]

            if search:
                where.append("(cc.RazonSocial LIKE %s OR cc.RFC LIKE %s OR cc.CodigoCliente LIKE %s OR cc.NombreComercial LIKE %s)")
                p_search = f"%{search}%"
                params.extend([p_search, p_search, p_search, p_search])

            where_clause = " AND ".join(where)

            cursor.execute(f"""
                SELECT
                    cc.ClienteID as cliente_id,
                    cc.CodigoCliente as codigo_cliente,
                    COALESCE(NULLIF(cc.NombreComercial, ''), cc.RazonSocial) as nombre_completo,
                    cc.RazonSocial as razon_social,
                    cc.NombreComercial as nombre_comercial,
                    cc.EmailPrincipal as email,
                    cc.TelefonoPrincipal as telefono,
                    cc.RFC as rfc,
                    CAST(cc.PublicUUID AS VARCHAR(36)) as cliente_crm_id,
                    s.NumeroSocio as ya_afiliado_numero_socio,
                    CAST(s.SocioID AS VARCHAR(36)) as ya_afiliado_socio_id
                FROM dbo.Cliente_Catalogo cc
                LEFT JOIN dbo.CavaSocios_Socios s
                    ON (s.ClienteCRMID = cc.PublicUUID OR (s.Email = cc.EmailPrincipal AND cc.EmailPrincipal <> ''))
                    AND s.EmpresaID = %s
                WHERE {where_clause}
                ORDER BY cc.RazonSocial
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """, tuple(params + [skip, limit]))

            clientes = cursor.fetchall() or []

            # Conteo
            cursor.execute(f"""
                SELECT COUNT(*) as total
                FROM dbo.Cliente_Catalogo cc
                WHERE {where_clause}
            """, tuple(params[1:]))
            total_row = cursor.fetchone()
            total = total_row['total'] if total_row else len(clientes)

            return {"clientes": clientes, "total": total, "skip": skip, "limit": limit}
        except Exception as e:
            logger.error(f"[CavaSocios] Error al consultar Cliente_Catalogo: {e}")
            raise
        finally:
            conn.close()

    def sincronizar_clientes_canonicos(self, empresa_id: str, cliente_ids: Optional[List[int]],
                                       usuario_id: str) -> Dict[str, Any]:
        """Sincroniza masiva o selectivamente clientes activos desde Cliente_Catalogo a CavaSocios_Socios."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            where = ["cc.Activo = 1", "s.SocioID IS NULL"]
            params = [empresa_id]

            if cliente_ids:
                placeholders = ','.join(['%s'] * len(cliente_ids))
                where.append(f"cc.ClienteID IN ({placeholders})")
                params.extend(cliente_ids)

            where_clause = " AND ".join(where)

            cursor.execute(f"""
                SELECT
                    cc.ClienteID,
                    cc.CodigoCliente,
                    COALESCE(NULLIF(cc.NombreComercial, ''), cc.RazonSocial) as NombreCompleto,
                    cc.EmailPrincipal as Email,
                    cc.TelefonoPrincipal as Telefono,
                    cc.PublicUUID
                FROM dbo.Cliente_Catalogo cc
                LEFT JOIN dbo.CavaSocios_Socios s
                    ON (s.ClienteCRMID = cc.PublicUUID OR (s.Email = cc.EmailPrincipal AND cc.EmailPrincipal <> ''))
                    AND s.EmpresaID = %s
                WHERE {where_clause}
                ORDER BY cc.ClienteID
            """, tuple(params))

            pendientes = cursor.fetchall() or []
            socios_creados = []

            for row in pendientes:
                socio_id = str(uuid.uuid4())
                cursor_seq = conn.cursor()
                numero_socio = self._generar_numero_socio(cursor_seq, empresa_id)

                cursor_ins = conn.cursor()
                cursor_ins.execute("""
                    INSERT INTO CavaSocios_Socios (
                        SocioID, EmpresaID, NumeroSocio, NombreCompleto,
                        Email, Telefono, ClienteCRMID, TipoMembresia,
                        FechaAltaMembresia, MaximoBotellas, Estatus,
                        Activo, UsuarioCreacionID, Observaciones
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    socio_id, empresa_id, numero_socio, row['NombreCompleto'],
                    row['Email'] or None, row['Telefono'] or None,
                    str(row['PublicUUID']) if row['PublicUUID'] else None,
                    'ESTANDAR', date.today(), 12, 'ACTIVO', 1, usuario_id,
                    f"Sincronizado automáticamente desde Catálogo Canónico (Cliente #{row['ClienteID']} - {row['CodigoCliente']})"
                ))

                socios_creados.append({
                    "socio_id": socio_id,
                    "numero_socio": numero_socio,
                    "nombre_completo": row['NombreCompleto'],
                    "cliente_id": row['ClienteID']
                })

            conn.commit()
            logger.info(f"[CavaSocios] Sincronizados {len(socios_creados)} clientes canónicos para empresa {empresa_id}")
            return {
                "sincronizados": len(socios_creados),
                "socios_creados": socios_creados,
                "mensaje": f"Se sincronizaron exitosamente {len(socios_creados)} clientes del catálogo canónico"
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error sincronizando clientes canónicos: {e}")
            raise
        finally:
            conn.close()

    def promover_cliente_canonico(self, empresa_id: str, data: Dict[str, Any], usuario_id: str) -> Dict[str, Any]:
        """Promueve/convierte un cliente del catálogo canónico en Socio de Cava."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cliente_crm_id = data.get('cliente_crm_id') or data.get('cliente_id')
            nombre_completo = data.get('nombre_completo', '')
            email = data.get('email')
            telefono = data.get('telefono')
            tipo_membresia = data.get('tipo_membresia', 'ESTANDAR')
            maximo_botellas = data.get('maximo_botellas', 12)

            # Verificar si ya está registrado como socio
            if cliente_crm_id:
                try:
                    uuid_val = uuid.UUID(str(cliente_crm_id))
                    cursor.execute("""
                        SELECT SocioID, NumeroSocio FROM CavaSocios_Socios
                        WHERE ClienteCRMID = %s AND EmpresaID = %s
                    """, (str(uuid_val), empresa_id))
                    existente = cursor.fetchone()
                    if existente:
                        raise ValueError(f"El cliente ya es socio de Cava con número #{existente[1]}")
                except (ValueError, TypeError):
                    pass

            socio_id = str(uuid.uuid4())
            numero_socio = data.get('numero_socio') or self._generar_numero_socio(cursor, empresa_id)

            cursor.execute("""
                INSERT INTO CavaSocios_Socios (
                    SocioID, EmpresaID, NumeroSocio, NombreCompleto,
                    Email, Telefono, ClienteCRMID, TipoMembresia,
                    FechaAltaMembresia, FechaVencimientoMembresia,
                    MaximoBotellas, Estatus, Activo, UsuarioCreacionID, Observaciones
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                socio_id, empresa_id, numero_socio, nombre_completo,
                email, telefono, cliente_crm_id, tipo_membresia,
                data.get('fecha_alta') or date.today(),
                data.get('fecha_vencimiento'),
                maximo_botellas, 'ACTIVO', 1, usuario_id,
                data.get('observaciones', 'Promovido desde catálogo canónico')
            ))

            conn.commit()
            logger.info(f"[CavaSocios] Cliente canónico promovido a socio {numero_socio}: {nombre_completo}")
            return {
                "socio_id": socio_id,
                "numero_socio": numero_socio,
                "mensaje": "Cliente promovido a Socio de Cava exitosamente"
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error promoviendo cliente a socio: {e}")
            raise
        finally:
            conn.close()

    def registrar_inventario_inicial(self, empresa_id: str, socio_id: str,
                                     botellas: List[Dict[str, Any]], usuario_id: str) -> Dict[str, Any]:
        """Registra el inventario inicial de botellas en custodia para un socio (en PZ / puntaje de botella)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            cursor.execute("""
                SELECT SocioID, NombreCompleto, NumeroSocio, MaximoBotellas,
                       (SELECT COUNT(*) FROM CavaSocios_Botellas b WHERE b.SocioID = s.SocioID AND b.EstatusBotella = 'EN_CAVA') as actuales
                FROM CavaSocios_Socios s
                WHERE s.SocioID = %s AND s.EmpresaID = %s
            """, (socio_id, empresa_id))
            socio = cursor.fetchone()
            if not socio:
                raise ValueError("Socio no encontrado")

            total_a_insertar = sum(int(b.get('cantidad_piezas', 1) or 1) for b in botellas)
            if (socio['actuales'] + total_a_insertar) > socio['MaximoBotellas']:
                raise ValueError(
                    f"Excede el límite de botellas del socio. Capacidad máxima: {socio['MaximoBotellas']}, actuales: {socio['actuales']}, a ingresar: {total_a_insertar}"
                )

            botellas_registradas = []

            for item in botellas:
                cantidad_pzs = int(item.get('cantidad_piezas', 1) or 1)
                puntaje_inicial_pct = float(item.get('puntaje_inicial_pct', 100.0) or 100.0)

                for _ in range(cantidad_pzs):
                    botella_id = str(uuid.uuid4())
                    cursor_ins = conn.cursor()
                    cursor_ins.execute("""
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
                        item.get('producto_codigo'), item['producto_nombre'],
                        item.get('marca'), item.get('tipo_bebida'),
                        item.get('añada'), 1.0,
                        item.get('ubicacion'), item.get('valor_declarado', 0),
                        'EN_CAVA', puntaje_inicial_pct,
                        item.get('foto_url'), usuario_id,
                        item.get('observaciones', 'Inventario inicial de apertura')
                    ))

                    # Kardex: Movimiento de Inventario Inicial
                    mov_id = str(uuid.uuid4())
                    cursor_ins.execute("""
                        INSERT INTO CavaSocios_Movimientos (
                            MovimientoID, EmpresaID, BotellaID, SocioID,
                            TipoMovimiento, NivelAnterior, NivelNuevo, CantidadConsumida,
                            MotivoMovimiento, UsuarioCreacionID, Observaciones
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        mov_id, empresa_id, botella_id, socio_id,
                        'INVENTARIO_INICIAL', 0, puntaje_inicial_pct, 0,
                        'Inventario Inicial de Cava (PZ)', usuario_id,
                        f"Apertura de inventario: {item['producto_nombre']} ({puntaje_inicial_pct}% / {puntaje_inicial_pct/100.0:.2f} PZ)"
                    ))

                    botellas_registradas.append({
                        "botella_id": botella_id,
                        "producto_nombre": item['producto_nombre'],
                        "puntaje_pz": round(puntaje_inicial_pct / 100.0, 3)
                    })

            conn.commit()
            logger.info(f"[CavaSocios] Inventario inicial registrado: {len(botellas_registradas)} botellas (PZ) para socio {socio['NumeroSocio']}")
            return {
                "socio_id": socio_id,
                "numero_socio": socio['NumeroSocio'],
                "botellas_registradas": len(botellas_registradas),
                "detalle": botellas_registradas,
                "mensaje": f"Se registraron exitosamente {len(botellas_registradas)} botellas en inventario inicial (PZ)"
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error registrando inventario inicial: {e}")
            raise
        finally:
            conn.close()

    def obtener_inventario_global(self, empresa_id: str, ubicacion: Optional[str] = None,
                                  tipo_bebida: Optional[str] = None, estatus: Optional[str] = None,
                                  socio_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Obtiene inventario global de botellas en resguardo por cava y ubicación en PZ / puntaje."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            where = ["b.EmpresaID = %s"]
            params = [empresa_id]

            if ubicacion:
                where.append("b.UbicacionCava LIKE %s")
                params.append(f"%{ubicacion}%")
            if tipo_bebida and tipo_bebida != 'todos':
                where.append("b.TipoBebida = %s")
                params.append(tipo_bebida)
            if estatus and estatus != 'todos':
                where.append("b.EstatusBotella = %s")
                params.append(estatus)
            if socio_id:
                where.append("b.SocioID = %s")
                params.append(socio_id)

            where_clause = " AND ".join(where)

            cursor.execute(f"""
                SELECT
                    b.BotellaID as botella_id,
                    b.SocioID as socio_id,
                    s.NombreCompleto as socio_nombre,
                    s.NumeroSocio as numero_socio,
                    b.ProductoNombre as producto_nombre,
                    b.Marca as marca,
                    b.TipoBebida as tipo_bebida,
                    b.Añada as añada,
                    b.Capacidad as capacidad,
                    b.UbicacionCava as ubicacion,
                    b.ValorDeclarado as valor_declarado,
                    b.EstatusBotella as estatus,
                    b.NivelActual as porcentaje_restante,
                    ROUND(b.NivelActual / 100.0, 3) as nivel_pz,
                    b.FechaIngreso as fecha_ingreso
                FROM CavaSocios_Botellas b
                INNER JOIN CavaSocios_Socios s ON b.SocioID = s.SocioID
                WHERE {where_clause}
                ORDER BY b.FechaIngreso DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """, tuple(params + [skip, limit]))

            botellas = cursor.fetchall() or []

            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       SUM(b.ValorDeclarado) as valor_total,
                       SUM(b.NivelActual / 100.0) as total_volumen_pz
                FROM CavaSocios_Botellas b
                WHERE {where_clause}
            """, tuple(params))
            resumen = cursor.fetchone() or {"total": len(botellas), "valor_total": 0, "total_volumen_pz": 0}

            return {
                "botellas": botellas,
                "total": resumen['total'] or 0,
                "valor_custodia_total": float(resumen['valor_total'] or 0),
                "total_piezas_pz": float(resumen['total_volumen_pz'] or 0),
                "skip": skip,
                "limit": limit
            }
        finally:
            conn.close()

    def obtener_historial_consumos_global(self, empresa_id: str, socio_id: Optional[str] = None,
                                          skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Obtiene historial general de consumos y movimientos de cava en PZ / puntaje de botella."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            where = ["m.EmpresaID = %s"]
            params = [empresa_id]
            if socio_id:
                where.append("m.SocioID = %s")
                params.append(socio_id)

            where_clause = " AND ".join(where)

            cursor.execute(f"""
                SELECT
                    m.MovimientoID as movimiento_id,
                    m.FechaMovimiento as fecha,
                    m.TipoMovimiento as tipo,
                    COALESCE(m.CantidadConsumida, m.NivelAnterior - m.NivelNuevo, 0) as porcentaje_consumido,
                    ROUND(COALESCE(m.CantidadConsumida, m.NivelAnterior - m.NivelNuevo, 0) / 100.0, 3) as consumo_pz,
                    m.NivelAnterior as nivel_anterior_pct,
                    m.NivelNuevo as nivel_nuevo_pct,
                    m.MontoCargo as monto_descorche,
                    m.MotivoMovimiento as motivo,
                    b.ProductoNombre as producto,
                    b.UbicacionCava as ubicacion,
                    s.NombreCompleto as socio,
                    s.NumeroSocio as numero_socio
                FROM CavaSocios_Movimientos m
                INNER JOIN CavaSocios_Botellas b ON m.BotellaID = b.BotellaID
                INNER JOIN CavaSocios_Socios s ON m.SocioID = s.SocioID
                WHERE {where_clause}
                ORDER BY m.FechaMovimiento DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """, tuple(params + [skip, limit]))

            movimientos = cursor.fetchall() or []

            cursor.execute(f"SELECT COUNT(*) as total FROM CavaSocios_Movimientos m WHERE {where_clause}", tuple(params))
            total_row = cursor.fetchone()

            return {
                "movimientos": movimientos,
                "total": total_row['total'] if total_row else len(movimientos),
                "skip": skip,
                "limit": limit
            }
        finally:
            conn.close()

    def obtener_kardex(self, empresa_id: str, socio_id: Optional[str] = None,
                       botella_id: Optional[str] = None, fecha_inicio: Optional[str] = None,
                       fecha_fin: Optional[str] = None, tipo_movimiento: Optional[str] = None,
                       skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Obtiene el Kardex general de Cavas con ecuación de balance en PZ (Inv. Inicial + Entradas - Consumos +/- Ajustes)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)

            where = ["m.EmpresaID = %s"]
            params = [empresa_id]

            if socio_id:
                where.append("m.SocioID = %s")
                params.append(socio_id)
            if botella_id:
                where.append("m.BotellaID = %s")
                params.append(botella_id)
            if fecha_inicio:
                where.append("m.FechaMovimiento >= %s")
                params.append(fecha_inicio)
            if fecha_fin:
                where.append("m.FechaMovimiento <= %s")
                params.append(fecha_fin)
            if tipo_movimiento and tipo_movimiento != 'todos':
                where.append("m.TipoMovimiento = %s")
                params.append(tipo_movimiento)

            where_clause = " AND ".join(where)

            cursor.execute(f"""
                SELECT
                    m.MovimientoID as movimiento_id,
                    m.FechaMovimiento as fecha,
                    m.TipoMovimiento as tipo_movimiento,
                    m.SocioID as socio_id,
                    s.NombreCompleto as socio_nombre,
                    s.NumeroSocio as numero_socio,
                    m.BotellaID as botella_id,
                    b.ProductoNombre as producto_nombre,
                    b.Marca as marca,
                    b.UbicacionCava as ubicacion,
                    m.NivelAnterior as nivel_anterior_pct,
                    ROUND(m.NivelAnterior / 100.0, 3) as nivel_anterior_pz,
                    m.NivelNuevo as nivel_nuevo_pct,
                    ROUND(m.NivelNuevo / 100.0, 3) as nivel_nuevo_pz,
                    COALESCE(m.CantidadConsumida, 0) as cantidad_consumida_pct,
                    ROUND(COALESCE(m.CantidadConsumida, 0) / 100.0, 3) as cantidad_consumida_pz,
                    m.MotivoMovimiento as motivo,
                    m.MontoCargo as monto_descorche,
                    m.Observaciones as observaciones
                FROM CavaSocios_Movimientos m
                INNER JOIN CavaSocios_Botellas b ON m.BotellaID = b.BotellaID
                INNER JOIN CavaSocios_Socios s ON m.SocioID = s.SocioID
                WHERE {where_clause}
                ORDER BY m.FechaMovimiento DESC, m.MovimientoID DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """, tuple(params + [skip, limit]))

            movimientos = cursor.fetchall() or []

            cursor.execute(f"""
                SELECT COUNT(*) as total FROM CavaSocios_Movimientos m WHERE {where_clause}
            """, tuple(params))
            total_count = cursor.fetchone()['total']

            # Balance global Kardex en PZ
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN m.TipoMovimiento = 'INVENTARIO_INICIAL' THEN COALESCE(m.NivelNuevo, 100) / 100.0 ELSE 0 END) as inv_inicial_pz,
                    SUM(CASE WHEN m.TipoMovimiento = 'ENTRADA' THEN COALESCE(m.NivelNuevo, 100) / 100.0 ELSE 0 END) as entradas_pz,
                    SUM(CASE WHEN m.TipoMovimiento LIKE 'CONSUMO%' THEN (COALESCE(m.NivelAnterior, 100) - COALESCE(m.NivelNuevo, 0)) / 100.0 ELSE 0 END) as consumos_pz,
                    SUM(CASE WHEN m.TipoMovimiento = 'AJUSTE_FISICO_SOBRANTE' THEN (COALESCE(m.NivelNuevo, 0) - COALESCE(m.NivelAnterior, 0)) / 100.0
                             WHEN m.TipoMovimiento = 'AJUSTE_FISICO_FALTANTE' THEN -1.0 * (COALESCE(m.NivelAnterior, 0) - COALESCE(m.NivelNuevo, 0)) / 100.0
                             ELSE 0 END) as ajustes_pz
                FROM CavaSocios_Movimientos m
                WHERE m.EmpresaID = %s
            """, (empresa_id,))
            res_kardex = cursor.fetchone() or {}

            inv_inicial_pz = float(res_kardex.get('inv_inicial_pz') or 0.0)
            entradas_pz = float(res_kardex.get('entradas_pz') or 0.0)
            consumos_pz = float(res_kardex.get('consumos_pz') or 0.0)
            ajustes_pz = float(res_kardex.get('ajustes_pz') or 0.0)
            stock_teorico_pz = round(inv_inicial_pz + entradas_pz - consumos_pz + ajustes_pz, 3)

            # Stock real en resguardo
            cursor.execute("""
                SELECT COUNT(*) as total_botellas_activas,
                       SUM(NivelActual / 100.0) as stock_real_pz
                FROM CavaSocios_Botellas
                WHERE EmpresaID = %s AND EstatusBotella = 'EN_CAVA'
            """, (empresa_id,))
            res_real = cursor.fetchone() or {}
            stock_real_pz = float(res_real.get('stock_real_pz') or 0.0)
            total_botellas_activas = int(res_real.get('total_botellas_activas') or 0)

            return {
                "movimientos": movimientos,
                "total": total_count,
                "resumen": {
                    "inv_inicial_pz": round(inv_inicial_pz, 3),
                    "entradas_pz": round(entradas_pz, 3),
                    "consumos_pz": round(consumos_pz, 3),
                    "ajustes_pz": round(ajustes_pz, 3),
                    "stock_teorico_pz": stock_teorico_pz,
                    "stock_real_pz": round(stock_real_pz, 3),
                    "total_botellas_en_cava": total_botellas_activas
                },
                "skip": skip,
                "limit": limit
            }
        finally:
            conn.close()

    def obtener_hoja_inventario_fisico(self, empresa_id: str, ubicacion: Optional[str] = None,
                                        socio_id: Optional[str] = None) -> Dict[str, Any]:
        """Genera hoja de conteo para auditoría física con stock teórico esperado."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            where = ["b.EmpresaID = %s", "b.EstatusBotella = 'EN_CAVA'"]
            params = [empresa_id]

            if ubicacion:
                where.append("b.UbicacionCava LIKE %s")
                params.append(f"%{ubicacion}%")
            if socio_id:
                where.append("b.SocioID = %s")
                params.append(socio_id)

            where_clause = " AND ".join(where)

            cursor.execute(f"""
                SELECT
                    b.BotellaID as botella_id,
                    b.SocioID as socio_id,
                    s.NombreCompleto as socio_nombre,
                    s.NumeroSocio as numero_socio,
                    b.ProductoNombre as producto_nombre,
                    b.Marca as marca,
                    b.TipoBebida as tipo_bebida,
                    b.Añada as añada,
                    b.UbicacionCava as ubicacion,
                    b.NivelActual as nivel_teorico_pct,
                    ROUND(b.NivelActual / 100.0, 3) as nivel_teorico_pz,
                    b.ValorDeclarado as valor_declarado,
                    b.FechaIngreso as fecha_ingreso
                FROM CavaSocios_Botellas b
                INNER JOIN CavaSocios_Socios s ON b.SocioID = s.SocioID
                WHERE {where_clause}
                ORDER BY b.UbicacionCava, s.NombreCompleto, b.ProductoNombre
            """, tuple(params))

            hoja = cursor.fetchall() or []
            total_teorico_pz = sum(float(r['nivel_teorico_pz'] or 0) for r in hoja)

            return {
                "hoja_conteo": hoja,
                "total_botellas": len(hoja),
                "total_teorico_pz": round(total_teorico_pz, 3),
                "fecha_generacion": date.today().isoformat()
            }
        finally:
            conn.close()

    def aplicar_ajustes_inventario_fisico(self, empresa_id: str, conteos: List[Dict[str, Any]],
                                          observaciones_generales: str, usuario_id: str) -> Dict[str, Any]:
        """Aplica conciliación física vs teórica y registra movimientos de ajuste en el Kardex."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            ajustes_realizados = []

            for item in conteos:
                botella_id = item['botella_id']
                nivel_fisico_pct = float(item.get('nivel_fisico_pct', 100.0) or 0.0)
                encontrada = item.get('encontrada', True)
                obs_item = item.get('observaciones', '')

                cursor.execute("""
                    SELECT b.*, s.SocioID, s.NombreCompleto
                    FROM CavaSocios_Botellas b
                    INNER JOIN CavaSocios_Socios s ON b.SocioID = s.SocioID
                    WHERE b.BotellaID = %s AND b.EmpresaID = %s
                """, (botella_id, empresa_id))
                botella = cursor.fetchone()
                if not botella:
                    continue

                nivel_teorico = float(botella['NivelActual'] or 100.0)

                if not encontrada or nivel_fisico_pct <= 0:
                    # Botella consumida o no encontrada
                    diferencia = 0.0 - nivel_teorico
                    cursor_upd = conn.cursor()
                    cursor_upd.execute("""
                        UPDATE CavaSocios_Botellas SET
                            NivelActual = 0,
                            EstatusBotella = %s,
                            FechaConsumo = GETUTCDATE(),
                            FechaModificacion = GETUTCDATE(),
                            UsuarioModificacionID = %s
                        WHERE BotellaID = %s
                    """, ('CONSUMIDA' if encontrada else 'EXTRAVIADA', usuario_id, botella_id))

                    mov_id = str(uuid.uuid4())
                    cursor_upd.execute("""
                        INSERT INTO CavaSocios_Movimientos (
                            MovimientoID, EmpresaID, BotellaID, SocioID,
                            TipoMovimiento, NivelAnterior, NivelNuevo, CantidadConsumida,
                            MotivoMovimiento, UsuarioCreacionID, Observaciones
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        mov_id, empresa_id, botella_id, botella['SocioID'],
                        'AJUSTE_FISICO_FALTANTE', nivel_teorico, 0, nivel_teorico,
                        'Ajuste físico: Botella agotada o no encontrada en auditoría',
                        usuario_id, f"{observaciones_generales}. {obs_item}".strip()
                    ))

                    ajustes_realizados.append({
                        "botella_id": botella_id,
                        "producto_nombre": botella['ProductoNombre'],
                        "tipo": "FALTANTE_TOTAL",
                        "diferencia_pz": round(diferencia / 100.0, 3)
                    })

                elif nivel_fisico_pct < nivel_teorico:
                    # Faltante parcial
                    diferencia = nivel_fisico_pct - nivel_teorico
                    cursor_upd = conn.cursor()
                    cursor_upd.execute("""
                        UPDATE CavaSocios_Botellas SET
                            NivelActual = %s,
                            FechaModificacion = GETUTCDATE(),
                            UsuarioModificacionID = %s
                        WHERE BotellaID = %s
                    """, (nivel_fisico_pct, usuario_id, botella_id))

                    mov_id = str(uuid.uuid4())
                    cursor_upd.execute("""
                        INSERT INTO CavaSocios_Movimientos (
                            MovimientoID, EmpresaID, BotellaID, SocioID,
                            TipoMovimiento, NivelAnterior, NivelNuevo, CantidadConsumida,
                            MotivoMovimiento, UsuarioCreacionID, Observaciones
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        mov_id, empresa_id, botella_id, botella['SocioID'],
                        'AJUSTE_FISICO_FALTANTE', nivel_teorico, nivel_fisico_pct, abs(diferencia),
                        f"Ajuste físico faltante: Disminución de {abs(diferencia):.1f}% (PZ)",
                        usuario_id, f"{observaciones_generales}. {obs_item}".strip()
                    ))

                    ajustes_realizados.append({
                        "botella_id": botella_id,
                        "producto_nombre": botella['ProductoNombre'],
                        "tipo": "FALTANTE_PARCIAL",
                        "diferencia_pz": round(diferencia / 100.0, 3)
                    })

                elif nivel_fisico_pct > nivel_teorico:
                    # Sobrante parcial
                    diferencia = nivel_fisico_pct - nivel_teorico
                    cursor_upd = conn.cursor()
                    cursor_upd.execute("""
                        UPDATE CavaSocios_Botellas SET
                            NivelActual = %s,
                            FechaModificacion = GETUTCDATE(),
                            UsuarioModificacionID = %s
                        WHERE BotellaID = %s
                    """, (nivel_fisico_pct, usuario_id, botella_id))

                    mov_id = str(uuid.uuid4())
                    cursor_upd.execute("""
                        INSERT INTO CavaSocios_Movimientos (
                            MovimientoID, EmpresaID, BotellaID, SocioID,
                            TipoMovimiento, NivelAnterior, NivelNuevo, CantidadConsumida,
                            MotivoMovimiento, UsuarioCreacionID, Observaciones
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        mov_id, empresa_id, botella_id, botella['SocioID'],
                        'AJUSTE_FISICO_SOBRANTE', nivel_teorico, nivel_fisico_pct, 0,
                        f"Ajuste físico sobrante: Incremento de {diferencia:.1f}% (PZ)",
                        usuario_id, f"{observaciones_generales}. {obs_item}".strip()
                    ))

                    ajustes_realizados.append({
                        "botella_id": botella_id,
                        "producto_nombre": botella['ProductoNombre'],
                        "tipo": "SOBRANTE_PARCIAL",
                        "diferencia_pz": round(diferencia / 100.0, 3)
                    })

            conn.commit()
            logger.info(f"[CavaSocios] Auditoría de inventario físico aplicada: {len(ajustes_realizados)} discrepancias ajustadas")
            return {
                "total_revisadas": len(conteos),
                "total_ajustes": len(ajustes_realizados),
                "ajustes": ajustes_realizados,
                "mensaje": f"Se aplicaron {len(ajustes_realizados)} ajustes físicos al Kardex satisfactoriamente"
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"[CavaSocios] Error aplicando ajustes físicos: {e}")
            raise
        finally:
            conn.close()

    def obtener_etiqueta_botella(self, botella_id: str, empresa_id: str) -> Dict[str, Any]:
        """Obtiene información resumida de una botella para generar su etiqueta de resguardo."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT
                    b.BotellaID as botella_id,
                    b.ProductoNombre as producto_nombre,
                    b.Marca as marca,
                    b.TipoBebida as tipo_bebida,
                    b.Añada as añada,
                    b.UbicacionCava as ubicacion,
                    b.ValorDeclarado as valor_declarado,
                    b.FechaIngreso as fecha_ingreso,
                    b.NivelActual as nivel_actual_pct,
                    ROUND(b.NivelActual / 100.0, 3) as nivel_actual_pz,
                    s.NumeroSocio as numero_socio,
                    s.NombreCompleto as socio_nombre
                FROM CavaSocios_Botellas b
                INNER JOIN CavaSocios_Socios s ON b.SocioID = s.SocioID
                WHERE b.BotellaID = %s AND b.EmpresaID = %s
            """, (botella_id, empresa_id))
            botella = cursor.fetchone()
            if not botella:
                raise ValueError("Botella no encontrada")
            return botella
        finally:
            conn.close()


def get_cava_socios_service() -> CavaSociosService:
    """Factory del dominio integrado Cavas sobre EDARSAHUB SQL."""
    return CavaSociosService()
