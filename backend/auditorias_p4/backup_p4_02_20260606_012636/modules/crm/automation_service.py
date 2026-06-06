from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - CRM Pipeline Automation Service
=============================================
Servicio para automatizaciones y flujos avanzados del pipeline CRM.

Funcionalidades:
- Reglas de automatización (condición → acción)
- Triggers al cambiar de etapa
- Notificaciones automáticas
- SLA de oportunidades
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import pymssql
import os
import uuid
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)


class PipelineAutomationService:
    """Servicio de automatizaciones de pipeline CRM."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
    
    def _get_connection(self):
        """Obtiene conexión a SQL Server."""
        return pymssql.connect(
            server=self.db_config['host'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            port=self.db_config.get('port', 1433)
        )
    
    # ==================== REGLAS DE AUTOMATIZACIÓN ====================
    
    def obtener_reglas_activas(self, empresa_id: str, pipeline_id: Optional[int] = None) -> List[Dict]:
        """Obtiene las reglas de automatización activas."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT * FROM CRM_Automation_Reglas
                WHERE EmpresaID = %s AND Activa = 1
            """
            params = [empresa_id]
            
            if pipeline_id:
                query += " AND (PipelineID = %s OR PipelineID IS NULL)"
                params.append(pipeline_id)
            
            query += " ORDER BY Prioridad ASC, FechaCreacion ASC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall() or []
            
        finally:
            conn.close()
    
    def crear_regla(self, empresa_id: str, data: Dict[str, Any], usuario_id: str) -> Dict:
        """Crea una nueva regla de automatización."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            regla_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO CRM_Automation_Reglas (
                    ReglaID, EmpresaID, Nombre, Descripcion,
                    PipelineID, TipoTrigger, CondicionJSON, AccionJSON,
                    Prioridad, Activa, UsuarioCreacionID, FechaCreacion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, GETDATE()
                )
            """, (
                regla_id, empresa_id, data['nombre'], data.get('descripcion'),
                data.get('pipeline_id'), data['tipo_trigger'],
                data.get('condicion_json', '{}'), data['accion_json'],
                data.get('prioridad', 100), usuario_id
            ))
            
            conn.commit()
            logger.info(f"[CRM-Automation] Regla creada: {data['nombre']}")
            
            return {"regla_id": regla_id, "mensaje": "Regla creada exitosamente"}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM-Automation] Error creando regla: {e}")
            raise
        finally:
            conn.close()
    
    # ==================== EJECUCIÓN DE AUTOMATIZACIONES ====================
    
    def ejecutar_trigger_cambio_etapa(
        self, 
        oportunidad_id: str, 
        etapa_anterior_id: int, 
        etapa_nueva_id: int,
        empresa_id: str
    ) -> List[Dict]:
        """
        Ejecuta las automatizaciones al cambiar de etapa.
        
        Returns: Lista de acciones ejecutadas
        """
        acciones_ejecutadas = []
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener reglas que aplican al cambio de etapa
            cursor.execute("""
                SELECT r.*, pe.Nombre as EtapaNombre
                FROM CRM_Automation_Reglas r
                LEFT JOIN CRM_Config_PipelineEtapas pe ON pe.EtapaID = %s
                WHERE r.EmpresaID = %s 
                AND r.Activa = 1
                AND r.TipoTrigger = 'CAMBIO_ETAPA'
                ORDER BY r.Prioridad ASC
            """, (etapa_nueva_id, empresa_id))
            
            reglas = cursor.fetchall()
            
            for regla in reglas:
                # Verificar si la regla aplica a esta etapa
                condicion = regla.get('CondicionJSON', '{}')
                if self._evaluar_condicion_etapa(condicion, etapa_anterior_id, etapa_nueva_id):
                    # Ejecutar acción
                    resultado = self._ejecutar_accion(
                        cursor, conn, oportunidad_id, regla['AccionJSON'], empresa_id
                    )
                    acciones_ejecutadas.append({
                        "regla_id": regla['ReglaID'],
                        "regla_nombre": regla['Nombre'],
                        "resultado": resultado
                    })
            
            return acciones_ejecutadas
            
        finally:
            conn.close()
    
    def _evaluar_condicion_etapa(
        self, 
        condicion_json: str, 
        etapa_anterior: int, 
        etapa_nueva: int
    ) -> bool:
        """Evalúa si la condición de cambio de etapa se cumple."""
        import json
        
        try:
            condicion = json.loads(condicion_json) if condicion_json else {}
        except:
            condicion = {}
        
        # Si no hay condición específica, aplicar siempre
        if not condicion:
            return True
        
        # Verificar etapa específica
        if 'etapa_destino' in condicion:
            if condicion['etapa_destino'] != etapa_nueva:
                return False
        
        if 'etapa_origen' in condicion:
            if condicion['etapa_origen'] != etapa_anterior:
                return False
        
        return True
    
    def _ejecutar_accion(
        self, 
        cursor, 
        conn, 
        oportunidad_id: str, 
        accion_json: str,
        empresa_id: str
    ) -> Dict:
        """Ejecuta una acción de automatización."""
        import json
        
        try:
            accion = json.loads(accion_json) if accion_json else {}
        except:
            return {"error": "JSON de acción inválido"}
        
        tipo_accion = accion.get('tipo')
        
        if tipo_accion == 'CREAR_ACTIVIDAD':
            return self._accion_crear_actividad(cursor, conn, oportunidad_id, accion, empresa_id)
        
        elif tipo_accion == 'ACTUALIZAR_CAMPO':
            return self._accion_actualizar_campo(cursor, conn, oportunidad_id, accion)
        
        elif tipo_accion == 'ENVIAR_NOTIFICACION':
            return self._accion_notificacion(cursor, conn, oportunidad_id, accion, empresa_id)
        
        elif tipo_accion == 'ASIGNAR_RESPONSABLE':
            return self._accion_asignar_responsable(cursor, conn, oportunidad_id, accion)
        
        else:
            return {"error": f"Tipo de acción no soportado: {tipo_accion}"}
    
    def _accion_crear_actividad(
        self, cursor, conn, oportunidad_id: str, accion: Dict, empresa_id: str
    ) -> Dict:
        """Crea una actividad automáticamente."""
        actividad_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO CRM_Actividades (
                ActividadID, EmpresaID, OportunidadID, TipoActividadID,
                Titulo, Descripcion, FechaProgramada, EstatusID,
                AutoGenerada, FechaCreacion
            ) VALUES (
                %s, %s, %s, %s, %s, %s, DATEADD(day, %s, GETDATE()), 1, 1, GETDATE()
            )
        """, (
            actividad_id, empresa_id, oportunidad_id,
            accion.get('tipo_actividad_id', 1),
            accion.get('titulo', 'Seguimiento automático'),
            accion.get('descripcion', 'Actividad generada por automatización'),
            accion.get('dias_programar', 1)
        ))
        conn.commit()
        
        logger.info(f"[CRM-Automation] Actividad creada automáticamente: {actividad_id}")
        return {"success": True, "actividad_id": actividad_id}
    
    def _accion_actualizar_campo(self, cursor, conn, oportunidad_id: str, accion: Dict) -> Dict:
        """Actualiza un campo de la oportunidad."""
        campo = accion.get('campo')
        valor = accion.get('valor')
        
        if not campo:
            return {"error": "Campo no especificado"}
        
        # Lista de campos permitidos para actualizar automáticamente
        campos_permitidos = ['ProbabilidadCierre', 'Prioridad', 'ResponsableID']
        
        if campo not in campos_permitidos:
            return {"error": f"Campo {campo} no permitido para actualización automática"}
        
        cursor.execute(f"""
            UPDATE CRM_Oportunidades 
            SET {campo} = %s, FechaModificacion = GETDATE()
            WHERE OportunidadID = %s
        """, (valor, oportunidad_id))
        conn.commit()
        
        return {"success": True, "campo": campo, "valor": valor}
    
    def _accion_notificacion(
        self, cursor, conn, oportunidad_id: str, accion: Dict, empresa_id: str
    ) -> Dict:
        """Registra una notificación para enviar."""
        notif_id = str(uuid.uuid4())
        
        # Obtener datos de la oportunidad
        cursor.execute("""
            SELECT o.Nombre, o.ResponsableID, u.Nombre as ResponsableNombre, u.Email
            FROM CRM_Oportunidades o
            LEFT JOIN Usuarios u ON o.ResponsableID = u.UsuarioID
            WHERE o.OportunidadID = %s
        """, (oportunidad_id,))
        oportunidad = cursor.fetchone()
        
        if not oportunidad:
            return {"error": "Oportunidad no encontrada"}
        
        cursor.execute("""
            INSERT INTO Notificaciones (
                NotificacionID, EmpresaID, UsuarioDestinoID,
                Tipo, Titulo, Mensaje, EntidadTipo, EntidadID,
                Leida, FechaCreacion
            ) VALUES (
                %s, %s, %s, 'CRM_AUTOMATION', %s, %s, 'OPORTUNIDAD', %s, 0, GETDATE()
            )
        """, (
            notif_id, empresa_id, oportunidad['ResponsableID'],
            accion.get('titulo', 'Notificación CRM'),
            accion.get('mensaje', f'Actualización en oportunidad: {oportunidad["Nombre"]}'),
            oportunidad_id
        ))
        conn.commit()
        
        return {"success": True, "notificacion_id": notif_id}
    
    def _accion_asignar_responsable(self, cursor, conn, oportunidad_id: str, accion: Dict) -> Dict:
        """Asigna un responsable a la oportunidad."""
        responsable_id = accion.get('responsable_id')
        
        if not responsable_id:
            return {"error": "responsable_id no especificado"}
        
        cursor.execute("""
            UPDATE CRM_Oportunidades 
            SET ResponsableID = %s, FechaModificacion = GETDATE()
            WHERE OportunidadID = %s
        """, (responsable_id, oportunidad_id))
        conn.commit()
        
        return {"success": True, "responsable_id": responsable_id}
    
    # ==================== SLA DE OPORTUNIDADES ====================
    
    def verificar_sla_oportunidades(self, empresa_id: str) -> Dict:
        """
        Verifica SLAs de oportunidades y genera alertas.
        
        Returns: Resumen de oportunidades con SLA vencido/próximo a vencer
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Oportunidades que llevan mucho tiempo en la misma etapa
            cursor.execute("""
                SELECT 
                    o.OportunidadID, o.NombreOportunidad as Nombre, o.MontoEstimado,
                    o.EtapaActualID, pe.Nombre as EtapaNombre,
                    o.FechaUltimaActividad,
                    DATEDIFF(day, ISNULL(o.FechaUltimaActividad, o.CreatedAt), GETDATE()) as DiasEnEtapa,
                    pe.DiasSLAMaximo,
                    CASE 
                        WHEN pe.DiasSLAMaximo IS NULL THEN 'SIN_SLA'
                        WHEN DATEDIFF(day, ISNULL(o.FechaUltimaActividad, o.CreatedAt), GETDATE()) > pe.DiasSLAMaximo THEN 'VENCIDO'
                        WHEN DATEDIFF(day, ISNULL(o.FechaUltimaActividad, o.CreatedAt), GETDATE()) > (pe.DiasSLAMaximo * 0.8) THEN 'PROXIMO'
                        ELSE 'OK'
                    END as EstatusSLA
                FROM CRM_Oportunidades o
                LEFT JOIN CRM_Config_PipelineEtapas pe ON o.EtapaActualID = pe.EtapaID
                WHERE o.EmpresaID = %s 
                AND o.Activo = 1
                AND o.EstatusOportunidadID NOT IN (4, 5)  -- No cerradas ganadas/perdidas
                ORDER BY DiasEnEtapa DESC
            """, (empresa_id,))
            
            oportunidades = cursor.fetchall()
            
            vencidas = [o for o in oportunidades if o['EstatusSLA'] == 'VENCIDO']
            proximas = [o for o in oportunidades if o['EstatusSLA'] == 'PROXIMO']
            
            return {
                "total_revisadas": len(oportunidades),
                "vencidas": len(vencidas),
                "proximas_a_vencer": len(proximas),
                "detalle_vencidas": vencidas[:10],
                "detalle_proximas": proximas[:10]
            }
            
        finally:
            conn.close()
    
    # ==================== REPORTES DE AUTOMATIZACIÓN ====================
    
    def obtener_estadisticas_automatizaciones(
        self, empresa_id: str, fecha_desde: Optional[date] = None
    ) -> Dict:
        """Obtiene estadísticas de automatizaciones ejecutadas."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            fecha_desde = fecha_desde or (datetime.now() - timedelta(days=30)).date()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_ejecuciones,
                    SUM(CASE WHEN Exitoso = 1 THEN 1 ELSE 0 END) as exitosas,
                    SUM(CASE WHEN Exitoso = 0 THEN 1 ELSE 0 END) as fallidas
                FROM CRM_Automation_Log
                WHERE EmpresaID = %s AND FechaEjecucion >= %s
            """, (empresa_id, fecha_desde))
            
            stats = cursor.fetchone()
            
            # Reglas más ejecutadas
            cursor.execute("""
                SELECT TOP 5
                    r.Nombre, COUNT(*) as ejecuciones
                FROM CRM_Automation_Log l
                INNER JOIN CRM_Automation_Reglas r ON l.ReglaID = r.ReglaID
                WHERE l.EmpresaID = %s AND l.FechaEjecucion >= %s
                GROUP BY r.Nombre
                ORDER BY ejecuciones DESC
            """, (empresa_id, fecha_desde))
            
            top_reglas = cursor.fetchall()
            
            return {
                "periodo": f"Desde {fecha_desde}",
                "total_ejecuciones": stats['total_ejecuciones'] or 0,
                "exitosas": stats['exitosas'] or 0,
                "fallidas": stats['fallidas'] or 0,
                "tasa_exito": round((stats['exitosas'] or 0) / max(stats['total_ejecuciones'] or 1, 1) * 100, 1),
                "top_reglas": top_reglas or []
            }
            
        finally:
            conn.close()


def get_pipeline_automation_service() -> PipelineAutomationService:
    """Factory para obtener el servicio de automatización."""
    db_config = {
        'host': _edarsa_cfg.host,
        'user': _edarsa_cfg.user,
        'password': _edarsa_cfg.password,
        'database': _edarsa_cfg.database,
        'port': _edarsa_cfg.port
    }
    return PipelineAutomationService(db_config)
