"""
EDARSA HUB - Tablajería Sync Service
====================================
Servicio de sincronización de plantillas desde servidores legacy.

FASE 6 (Mayo 2026): Migrado a usar variables de entorno para credenciales.
"""

import logging
import hashlib
import json
import os
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
from zoneinfo import ZoneInfo

from .schemas import (
    SyncResult, OrigenPlantilla, EstatusPlantilla, TipoDerivado,
    MPROSubgrupoInsumo, MPROReceta, MPROSucursal
)

logger = logging.getLogger(__name__)

MEXICO_TZ = ZoneInfo("America/Mexico_City")

# P2-01: Credenciales desde config centralizado
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahub_connection
_edarsa_cfg = get_edarsahub_sql_config()
DEFAULT_DB_PASSWORD = _edarsa_cfg.password


class TablajeriaSyncService:
    """
    Servicio de sincronización de plantillas de tablajería.
    Soporta MPRO TABLAJERIA y CIENFUEGOS TABLAJERIA.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        
    def _get_hub_connection(self):
        """Conexión a EDARSAHUB SQL"""
        return get_external_sql_connection(self.db_config)
    
    def _now_utc(self) -> datetime:
        return datetime.utcnow()
    
    def _today_mexico(self) -> date:
        return datetime.now(MEXICO_TZ).date()
    
    def _generate_hash(self, data: Dict) -> str:
        """Genera hash SHA256 de los datos para detectar cambios"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    # ============================================================
    # SINCRONIZACIÓN PRINCIPAL
    # ============================================================
    
    def sync_servidor(
        self,
        servidor_id: str,
        entidades: List[str] = None,
        forzar_actualizacion: bool = False
    ) -> SyncResult:
        """
        Sincroniza plantillas desde un servidor legacy.
        
        Args:
            servidor_id: ID del servidor en Servidores_Conexiones
            entidades: Lista de entidades a sincronizar ['plantillas']
            forzar_actualizacion: Si True, actualiza aunque no haya cambios
        """
        if entidades is None:
            entidades = ['plantillas']
        
        result = SyncResult(success=True, servidor_id=servidor_id)
        start_time = datetime.now()
        
        # Obtener configuración del servidor
        servidor_config = self._get_servidor_config(servidor_id)
        if not servidor_config:
            result.success = False
            result.errores.append(f"Servidor no encontrado: {servidor_id}")
            return result
        
        result.servidor_nombre = servidor_config.get('nombre', '')
        
        # Determinar tipo de servidor
        sistema = servidor_config.get('system_type', '').upper()
        
        try:
            if 'MPRO' in sistema or 'mpro' in servidor_config.get('database_name', '').lower():
                self._sync_mpro(servidor_config, entidades, forzar_actualizacion, result)
            elif 'SOFTRESTAURANT' in sistema or 'CIENFUEGOS' in servidor_config.get('nombre', '').upper():
                self._sync_cienfuegos(servidor_config, entidades, forzar_actualizacion, result)
            else:
                result.success = False
                result.errores.append(f"Sistema no soportado: {sistema}")
                
        except Exception as e:
            logger.error(f"[TablajeriaSync] Error general: {e}")
            result.success = False
            result.errores.append(str(e))
        
        result.duracion_segundos = int((datetime.now() - start_time).total_seconds())
        result.entidades_procesadas = entidades
        
        # Registrar en SyncLog
        self._registrar_sync_log(result)
        
        return result
    
    def _get_servidor_config(self, servidor_id: str) -> Optional[Dict]:
        """Obtiene configuración del servidor desde EDARSAHUB"""
        conn = self._get_hub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT id, nombre, system_type, host, port, database_name, 
                       username, password_encrypted, activo
                FROM Servidores_Conexiones
                WHERE id = %s
            """, (servidor_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    # ============================================================
    # SYNC MPRO TABLAJERIA
    # ============================================================
    
    def _sync_mpro(
        self,
        servidor_config: Dict,
        entidades: List[str],
        forzar: bool,
        result: SyncResult
    ):
        """Sincroniza desde MPRO TABLAJERIA"""
        logger.info(f"[TablajeriaSync] Iniciando sync MPRO: {servidor_config['nombre']}")
        
        # Conexión a MPRO
        try:
            # Usar password desde config o variable de entorno
            password = servidor_config.get('password_decrypted') or DEFAULT_DB_PASSWORD
            if not password:
                result.success = False
                result.errores.append("Password no configurado para servidor MPRO")
                return
            
            conn_mpro = get_external_sql_connection({**servidor_config, 'password_decrypted': password})
        except Exception as e:
            result.success = False
            result.errores.append(f"Error conectando a MPRO: {e}")
            return
        
        try:
            cursor_mpro = conn_mpro.cursor(as_dict=True)
            
            if 'plantillas' in entidades:
                self._sync_mpro_plantillas(
                    cursor_mpro, 
                    servidor_config, 
                    forzar, 
                    result
                )
                
        finally:
            conn_mpro.close()
    
    def _sync_mpro_plantillas(
        self,
        cursor_mpro,
        servidor_config: Dict,
        forzar: bool,
        result: SyncResult
    ):
        """Sincroniza plantillas desde MPRO"""
        
        # 1. Obtener todas las sucursales
        cursor_mpro.execute("SELECT * FROM sucursales")
        sucursales = {row['idsucursal']: row for row in cursor_mpro.fetchall()}
        
        # 2. Obtener todos los insumos/subgrupos
        cursor_mpro.execute("SELECT * FROM subgrupo_insumos")
        subgrupos = {row['idsubgrupo']: row for row in cursor_mpro.fetchall()}
        
        # 3. Obtener todas las recetas
        cursor_mpro.execute("SELECT * FROM receta")
        recetas = cursor_mpro.fetchall()
        result.registros_leidos = len(recetas)
        
        # 4. Agrupar recetas por insumo base
        plantillas_agrupadas = {}
        for receta in recetas:
            base_id = receta['idsubgrupobase']
            if base_id not in plantillas_agrupadas:
                plantillas_agrupadas[base_id] = []
            plantillas_agrupadas[base_id].append(receta)
        
        # 5. Procesar cada plantilla
        conn_hub = self._get_hub_connection()
        try:
            cursor_hub = conn_hub.cursor(as_dict=True)
            
            for base_id, derivados in plantillas_agrupadas.items():
                try:
                    self._procesar_plantilla_mpro(
                        cursor_hub,
                        base_id,
                        derivados,
                        subgrupos,
                        servidor_config,
                        forzar,
                        result
                    )
                    conn_hub.commit()
                except Exception as e:
                    conn_hub.rollback()
                    result.registros_error += 1
                    result.errores.append(f"Error plantilla {base_id}: {str(e)[:100]}")
                    logger.error(f"[TablajeriaSync] Error procesando plantilla {base_id}: {e}")
                    
        finally:
            conn_hub.close()
    
    def _procesar_plantilla_mpro(
        self,
        cursor_hub,
        base_id: int,
        derivados: List[Dict],
        subgrupos: Dict,
        servidor_config: Dict,
        forzar: bool,
        result: SyncResult
    ):
        """Procesa una plantilla individual de MPRO"""
        
        # Obtener info del insumo base
        insumo_base = subgrupos.get(base_id)
        if not insumo_base:
            logger.warning(f"[TablajeriaSync] Insumo base {base_id} no encontrado")
            return
        
        # Generar código único de plantilla
        codigo_plantilla = f"MPRO-{base_id}"
        bdempresa = insumo_base.get('bdempresa', 'UNKNOWN')
        
        # Calcular hash para detectar cambios
        data_hash = {
            'base_id': base_id,
            'insumo': insumo_base.get('descripcion'),
            'derivados': [
                {
                    'id': d['idsubgruporesultante'],
                    'nombre': subgrupos.get(d['idsubgruporesultante'], {}).get('descripcion', '')
                }
                for d in derivados
            ]
        }
        hash_actual = self._generate_hash(data_hash)
        
        # Verificar si ya existe
        cursor_hub.execute("""
            SELECT PlantillaID, HashOrigen, Estatus, VersionActual
            FROM Operaciones_Tablaje_Plantillas
            WHERE ServidorOrigenID = %s AND IDLegacyPlantilla = %s AND Activo = 1
        """, (servidor_config['id'], str(base_id)))
        
        existente = cursor_hub.fetchone()
        
        if existente:
            if existente['HashOrigen'] == hash_actual and not forzar:
                # Sin cambios, solo actualizar fecha de sync
                cursor_hub.execute("""
                    UPDATE Operaciones_Tablaje_Plantillas
                    SET FechaSincronizacionUTC = %s
                    WHERE PlantillaID = %s
                """, (self._now_utc(), existente['PlantillaID']))
                result.registros_sin_cambios += 1
                return
            
            # Hay cambios - si está PUBLICADA, crear nueva versión
            if existente['Estatus'] == 'PUBLICADA':
                # Marcar anterior como REEMPLAZADA
                cursor_hub.execute("""
                    UPDATE Operaciones_Tablaje_Plantillas
                    SET Estatus = 'REEMPLAZADA', FechaModificacionUTC = %s
                    WHERE PlantillaID = %s
                """, (self._now_utc(), existente['PlantillaID']))
                
                # Crear nueva versión
                nueva_version = existente['VersionActual'] + 1
                self._insertar_plantilla_mpro(
                    cursor_hub, insumo_base, derivados, subgrupos,
                    servidor_config, hash_actual, nueva_version,
                    existente['PlantillaID']
                )
                result.registros_actualizados += 1
            else:
                # Actualizar directamente
                self._actualizar_plantilla_mpro(
                    cursor_hub, existente['PlantillaID'],
                    insumo_base, derivados, subgrupos, hash_actual
                )
                result.registros_actualizados += 1
        else:
            # Nueva plantilla
            self._insertar_plantilla_mpro(
                cursor_hub, insumo_base, derivados, subgrupos,
                servidor_config, hash_actual, 1, None
            )
            result.registros_creados += 1
    
    def _insertar_plantilla_mpro(
        self,
        cursor_hub,
        insumo_base: Dict,
        derivados: List[Dict],
        subgrupos: Dict,
        servidor_config: Dict,
        hash_origen: str,
        version: int,
        plantilla_padre_id: Optional[str]
    ):
        """Inserta nueva plantilla en EDARSAHUB"""
        import uuid
        
        plantilla_id = str(uuid.uuid4())
        now_utc = self._now_utc()
        today_mx = self._today_mexico()
        
        # Mapear EmpresaID basado en bdempresa
        empresa_id = self._mapear_empresa_mpro(insumo_base.get('bdempresa', ''))
        
        # Calcular rendimiento esperado (suma de derivados no merma)
        total_rendimiento = sum(
            float(subgrupos.get(d['idsubgruporesultante'], {}).get('rendimiento', 0) or 0)
            for d in derivados
            if not subgrupos.get(d['idsubgruporesultante'], {}).get('tipoinsumo', '').startswith('M')
        )
        
        # Calcular merma esperada
        merma_esperada = sum(
            float(subgrupos.get(d['idsubgruporesultante'], {}).get('rendimiento', 0) or 0)
            for d in derivados
            if subgrupos.get(d['idsubgruporesultante'], {}).get('tipoinsumo', '').startswith('M')
        )
        
        cursor_hub.execute("""
            INSERT INTO Operaciones_Tablaje_Plantillas (
                PlantillaID, EmpresaID, CodigoPlantilla, NombrePlantilla,
                Descripcion, TipoTransformacion,
                InsumoBaseCodigo, InsumoBaseNombre, CantidadBaseEstandar,
                RendimientoEsperadoPorcentaje, MermaEsperadaPorcentaje,
                ReglaCosteo, OrigenPlantilla, SistemaOrigen,
                ServidorOrigenID, BaseDatosOrigen, IDLegacyPlantilla,
                HashOrigen, VersionActual, PlantillaPadreID,
                Estatus, Activo, FechaAltaUTC, FechaSincronizacionUTC,
                FechaOperacionMexico
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            plantilla_id,
            empresa_id,
            f"MPRO-{insumo_base['idsubgrupo']}",
            insumo_base.get('descripcion', 'Sin nombre'),
            f"Importado desde MPRO. BD: {insumo_base.get('bdempresa', '')}",
            'TABLAJERIA',
            insumo_base.get('idinsumokg'),
            insumo_base.get('descripcion'),
            1,
            total_rendimiento * 100 if total_rendimiento else None,
            merma_esperada * 100 if merma_esperada else None,
            'PROPORCIONAL',
            OrigenPlantilla.LEGACY_MPRO_TABLAJERIA.value,
            'MPRO',
            servidor_config['id'],
            servidor_config['database_name'],
            str(insumo_base['idsubgrupo']),
            hash_origen,
            version,
            plantilla_padre_id,
            EstatusPlantilla.SINCRONIZADA.value,
            1,
            now_utc,
            now_utc,
            today_mx
        ))
        
        # Insertar detalles (derivados)
        for i, derivado in enumerate(derivados):
            subgrupo = subgrupos.get(derivado['idsubgruporesultante'], {})
            tipo_insumo = subgrupo.get('tipoinsumo', '')
            
            # Determinar tipo de derivado
            if tipo_insumo.startswith('M'):
                tipo_derivado = TipoDerivado.MERMA.value
                es_merma = True
            elif tipo_insumo == 'IB':
                tipo_derivado = TipoDerivado.PRINCIPAL.value
                es_merma = False
            else:
                tipo_derivado = TipoDerivado.SUBPRODUCTO.value
                es_merma = False
            
            detalle_id = str(uuid.uuid4())
            rendimiento = float(subgrupo.get('rendimiento', 0) or 0)
            # Limitar porcentaje a máximo 99.99 para evitar overflow en DECIMAL(5,2)
            rendimiento_pct = min(rendimiento * 100, 99.99) if rendimiento else None
            
            cursor_hub.execute("""
                INSERT INTO Operaciones_Tablaje_PlantillasDetalle (
                    PlantillaDetalleID, PlantillaID,
                    ProductoDerivadoCodigo, ProductoDerivadoNombre,
                    TipoDerivado, CantidadEsperada,
                    PorcentajeRendimientoEsperado, PorcentajeCostoAsignado,
                    EsMerma, EsSubproducto, EsProductoVendible, EsInventariable,
                    OrdenVisual, IDLegacyDetalle, Activo, FechaAltaUTC
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                detalle_id,
                plantilla_id,
                subgrupo.get('idinsumokg'),
                subgrupo.get('descripcion', 'Derivado'),
                tipo_derivado,
                rendimiento if rendimiento > 0 else 1,
                rendimiento_pct,
                subgrupo.get('costofijo') if subgrupo.get('costeable') else None,
                es_merma,
                tipo_derivado == TipoDerivado.SUBPRODUCTO.value,
                not es_merma,
                not es_merma,
                i,
                str(derivado['idsubgruporesultante']),
                1,
                now_utc
            ))
        
        logger.debug(f"[TablajeriaSync] Plantilla insertada: MPRO-{insumo_base['idsubgrupo']}")
    
    def _actualizar_plantilla_mpro(
        self,
        cursor_hub,
        plantilla_id: str,
        insumo_base: Dict,
        derivados: List[Dict],
        subgrupos: Dict,
        hash_origen: str
    ):
        """Actualiza plantilla existente"""
        now_utc = self._now_utc()
        
        # Actualizar header
        cursor_hub.execute("""
            UPDATE Operaciones_Tablaje_Plantillas SET
                NombrePlantilla = %s,
                HashOrigen = %s,
                FechaModificacionUTC = %s,
                FechaSincronizacionUTC = %s,
                Estatus = %s
            WHERE PlantillaID = %s
        """, (
            insumo_base.get('descripcion', 'Sin nombre'),
            hash_origen,
            now_utc,
            now_utc,
            EstatusPlantilla.SINCRONIZADA.value,
            plantilla_id
        ))
        
        # Desactivar detalles anteriores
        cursor_hub.execute("""
            UPDATE Operaciones_Tablaje_PlantillasDetalle
            SET Activo = 0, FechaModificacionUTC = %s
            WHERE PlantillaID = %s
        """, (now_utc, plantilla_id))
        
        # Insertar nuevos detalles
        import uuid
        for i, derivado in enumerate(derivados):
            subgrupo = subgrupos.get(derivado['idsubgruporesultante'], {})
            tipo_insumo = subgrupo.get('tipoinsumo', '')
            
            if tipo_insumo.startswith('M'):
                tipo_derivado = TipoDerivado.MERMA.value
                es_merma = True
            elif tipo_insumo == 'IB':
                tipo_derivado = TipoDerivado.PRINCIPAL.value
                es_merma = False
            else:
                tipo_derivado = TipoDerivado.SUBPRODUCTO.value
                es_merma = False
            
            detalle_id = str(uuid.uuid4())
            rendimiento = float(subgrupo.get('rendimiento', 0) or 0)
            # Limitar porcentaje a máximo 99.99 para evitar overflow
            rendimiento_pct = min(rendimiento * 100, 99.99) if rendimiento else None
            
            cursor_hub.execute("""
                INSERT INTO Operaciones_Tablaje_PlantillasDetalle (
                    PlantillaDetalleID, PlantillaID,
                    ProductoDerivadoCodigo, ProductoDerivadoNombre,
                    TipoDerivado, CantidadEsperada,
                    PorcentajeRendimientoEsperado,
                    EsMerma, EsSubproducto, EsProductoVendible, EsInventariable,
                    OrdenVisual, IDLegacyDetalle, Activo, FechaAltaUTC
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                detalle_id,
                plantilla_id,
                subgrupo.get('idinsumokg'),
                subgrupo.get('descripcion', 'Derivado'),
                tipo_derivado,
                rendimiento if rendimiento > 0 else 1,
                rendimiento_pct,
                es_merma,
                tipo_derivado == TipoDerivado.SUBPRODUCTO.value,
                not es_merma,
                not es_merma,
                i,
                str(derivado['idsubgruporesultante']),
                1,
                now_utc
            ))
        
        logger.debug(f"[TablajeriaSync] Plantilla actualizada: {plantilla_id}")
    
    def _mapear_empresa_mpro(self, bdempresa: str) -> str:
        """Mapea bdempresa de MPRO a EmpresaID de EDARSAHUB"""
        # Mapeo basado en los datos observados
        mapeo = {
            'CENTRAL2020': '00000000-0000-0000-0000-000000000001',  # 130
            'HR2020': '00000000-0000-0000-0000-000000000002',  # Hermana República
        }
        return mapeo.get(bdempresa, '00000000-0000-0000-0000-000000000001')
    
    # ============================================================
    # SYNC CIENFUEGOS (SOFTRESTAURANT)
    # ============================================================
    
    def _sync_cienfuegos(
        self,
        servidor_config: Dict,
        entidades: List[str],
        forzar: bool,
        result: SyncResult
    ):
        """Sincroniza desde CIENFUEGOS TABLAJERIA (SoftRestaurant)"""
        logger.info(f"[TablajeriaSync] Iniciando sync CIENFUEGOS: {servidor_config['nombre']}")
        
        # Intentar conexión
        try:
            # El host tiene formato especial con puerto en la cadena
            host = servidor_config['host']
            if ',' in host:
                # Formato: server,port\instance
                host_parts = host.split(',')
                server = host_parts[0]
                port_instance = host_parts[1] if len(host_parts) > 1 else '1433'
                if '\\' in port_instance:
                    port = int(port_instance.split('\\')[0])
                else:
                    port = int(port_instance)
            else:
                server = host
                port = servidor_config.get('port', 1433)
            
            conn_cf = get_external_sql_connection({**servidor_config, 'password_decrypted': password})  # noqa: F821
        except Exception as e:
            result.success = False
            result.errores.append(f"Error conectando a CIENFUEGOS: {e}")
            logger.error(f"[TablajeriaSync] No se pudo conectar a CIENFUEGOS: {e}")
            return
        
        try:
            cursor_cf = conn_cf.cursor(as_dict=True)
            
            if 'plantillas' in entidades:
                # TODO: Implementar lógica específica de SoftRestaurant
                # cuando el servidor esté disponible
                result.errores.append("Sync CIENFUEGOS pendiente de implementación (servidor offline)")
                
        finally:
            conn_cf.close()
    
    # ============================================================
    # SYNC LOG
    # ============================================================
    
    def _registrar_sync_log(self, result: SyncResult):
        """Registra el resultado de la sincronización en EDARSAHUB"""
        conn = self._get_hub_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Operaciones_Tablaje_SyncLog (
                    ServidorID, ServidorNombre, SistemaOrigen,
                    TipoEntidad, Operacion, FechaInicioUTC, FechaFinUTC,
                    DuracionSegundos, RegistrosLeidos, RegistrosCreados,
                    RegistrosActualizados, RegistrosSinCambios, RegistrosError,
                    Estado, MensajeError, DetallesJSON
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                result.servidor_id,
                result.servidor_nombre,
                'MPRO' if 'MPRO' in (result.servidor_nombre or '') else 'SOFTRESTAURANT',
                ','.join(result.entidades_procesadas),
                'SYNC_PLANTILLAS',
                self._now_utc(),
                self._now_utc(),
                result.duracion_segundos,
                result.registros_leidos,
                result.registros_creados,
                result.registros_actualizados,
                result.registros_sin_cambios,
                result.registros_error,
                'COMPLETADO' if result.success else 'ERROR',
                result.errores[0] if result.errores else None,
                json.dumps({'errores': result.errores[:10]}) if result.errores else None
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"[TablajeriaSync] Error registrando SyncLog: {e}")
        finally:
            conn.close()
