"""
EDARSA HUB - CRM Trigger Service
=================================
Sistema de triggers avanzados para eventos del CRM.

Eventos soportados:
- OPORTUNIDAD_CREADA
- OPORTUNIDAD_ACTUALIZADA
- ETAPA_CAMBIADA
- OPORTUNIDAD_GANADA
- OPORTUNIDAD_PERDIDA
- ACTIVIDAD_VENCIDA
- SLA_VENCIDO
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import pymssql
import os
import uuid

logger = logging.getLogger(__name__)


class TriggerEvent(str, Enum):
    """Tipos de eventos que disparan triggers."""
    OPORTUNIDAD_CREADA = "OPORTUNIDAD_CREADA"
    OPORTUNIDAD_ACTUALIZADA = "OPORTUNIDAD_ACTUALIZADA"
    ETAPA_CAMBIADA = "ETAPA_CAMBIADA"
    OPORTUNIDAD_GANADA = "OPORTUNIDAD_GANADA"
    OPORTUNIDAD_PERDIDA = "OPORTUNIDAD_PERDIDA"
    ACTIVIDAD_VENCIDA = "ACTIVIDAD_VENCIDA"
    SLA_VENCIDO = "SLA_VENCIDO"
    MONTO_ACTUALIZADO = "MONTO_ACTUALIZADO"
    RESPONSABLE_CAMBIADO = "RESPONSABLE_CAMBIADO"


class TriggerAction(str, Enum):
    """Tipos de acciones que pueden ejecutar los triggers."""
    CREAR_ACTIVIDAD = "CREAR_ACTIVIDAD"
    ENVIAR_EMAIL = "ENVIAR_EMAIL"
    ENVIAR_WHATSAPP = "ENVIAR_WHATSAPP"
    CREAR_NOTIFICACION = "CREAR_NOTIFICACION"
    ACTUALIZAR_CAMPO = "ACTUALIZAR_CAMPO"
    ASIGNAR_RESPONSABLE = "ASIGNAR_RESPONSABLE"
    WEBHOOK = "WEBHOOK"
    CREAR_TAREA_SEGUIMIENTO = "CREAR_TAREA_SEGUIMIENTO"


class CRMTriggerService:
    """
    Servicio de triggers avanzados para CRM.
    Ejecuta acciones automáticas basadas en eventos del pipeline.
    """
    
    def __init__(self, db_config: Dict[str, Any] = None):
        self.db_config = db_config or self._default_config()
        self._notification_service = None
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
            'user': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
            'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
            'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
            'port': int(os.environ.get('EDARSAHUB_PORT', 1433))
        }
    
    def _get_connection(self):
        return pymssql.connect(
            server=self.db_config['host'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            port=self.db_config.get('port', 1433)
        )
    
    @property
    def notification_service(self):
        """Lazy load del servicio de notificaciones."""
        if self._notification_service is None:
            try:
                from modules.cava_socios.notification_service import get_notification_service
                self._notification_service = get_notification_service()
            except ImportError:
                logger.warning("[CRM-Trigger] Servicio de notificaciones no disponible")
        return self._notification_service
    
    # ==================== DISPATCH DE EVENTOS ====================
    
    def dispatch_event(
        self,
        evento: TriggerEvent,
        empresa_id: str,
        entidad_id: str,
        datos_evento: Dict[str, Any],
        usuario_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Despacha un evento y ejecuta todos los triggers asociados.
        
        Args:
            evento: Tipo de evento
            empresa_id: ID de la empresa
            entidad_id: ID de la entidad afectada (oportunidad, lead, etc.)
            datos_evento: Datos adicionales del evento
            usuario_id: Usuario que generó el evento
        
        Returns:
            Lista de resultados de cada trigger ejecutado
        """
        logger.info(f"[CRM-Trigger] Evento {evento.value} en entidad {entidad_id}")
        
        resultados = []
        
        # Obtener triggers activos para este evento
        triggers = self._obtener_triggers_activos(empresa_id, evento)
        
        for trigger in triggers:
            try:
                # Evaluar condiciones
                if not self._evaluar_condiciones(trigger, datos_evento):
                    continue
                
                # Ejecutar acciones
                resultado = self._ejecutar_acciones(
                    trigger=trigger,
                    entidad_id=entidad_id,
                    empresa_id=empresa_id,
                    datos_evento=datos_evento,
                    usuario_id=usuario_id
                )
                
                # Registrar ejecución
                self._registrar_ejecucion(
                    trigger_id=trigger['TriggerID'],
                    entidad_id=entidad_id,
                    empresa_id=empresa_id,
                    resultado=resultado
                )
                
                resultados.append({
                    "trigger_id": trigger['TriggerID'],
                    "trigger_nombre": trigger['Nombre'],
                    "resultado": resultado
                })
                
            except Exception as e:
                logger.error(f"[CRM-Trigger] Error ejecutando trigger {trigger.get('TriggerID')}: {e}")
                resultados.append({
                    "trigger_id": trigger.get('TriggerID'),
                    "error": str(e)
                })
        
        return resultados
    
    def _obtener_triggers_activos(
        self, empresa_id: str, evento: TriggerEvent
    ) -> List[Dict[str, Any]]:
        """Obtiene triggers activos para un evento específico."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT * FROM CRM_Triggers
                WHERE EmpresaID = %s
                AND TipoEvento = %s
                AND Activo = 1
                ORDER BY Prioridad ASC
            """, (empresa_id, evento.value))
            
            return cursor.fetchall() or []
            
        finally:
            conn.close()
    
    def _evaluar_condiciones(
        self, trigger: Dict[str, Any], datos_evento: Dict[str, Any]
    ) -> bool:
        """Evalúa si las condiciones del trigger se cumplen."""
        condiciones_json = trigger.get('CondicionesJSON', '{}')
        
        try:
            condiciones = json.loads(condiciones_json) if condiciones_json else {}
        except json.JSONDecodeError:
            return True  # Si no hay condiciones válidas, ejecutar siempre
        
        if not condiciones:
            return True
        
        # Evaluar cada condición
        for campo, valor_esperado in condiciones.items():
            valor_actual = datos_evento.get(campo)
            
            if isinstance(valor_esperado, dict):
                # Condiciones complejas: {"$gt": 10000}, {"$in": [1,2,3]}
                if not self._evaluar_condicion_compleja(valor_actual, valor_esperado):
                    return False
            else:
                # Condición simple de igualdad
                if valor_actual != valor_esperado:
                    return False
        
        return True
    
    def _evaluar_condicion_compleja(
        self, valor_actual: Any, condicion: Dict[str, Any]
    ) -> bool:
        """Evalúa condiciones complejas ($gt, $lt, $in, etc.)."""
        for operador, valor_esperado in condicion.items():
            if operador == '$gt' and not (valor_actual and valor_actual > valor_esperado):
                return False
            elif operador == '$gte' and not (valor_actual and valor_actual >= valor_esperado):
                return False
            elif operador == '$lt' and not (valor_actual and valor_actual < valor_esperado):
                return False
            elif operador == '$lte' and not (valor_actual and valor_actual <= valor_esperado):
                return False
            elif operador == '$in' and valor_actual not in valor_esperado:
                return False
            elif operador == '$nin' and valor_actual in valor_esperado:
                return False
            elif operador == '$ne' and valor_actual == valor_esperado:
                return False
        
        return True
    
    # ==================== EJECUCIÓN DE ACCIONES ====================
    
    def _ejecutar_acciones(
        self,
        trigger: Dict[str, Any],
        entidad_id: str,
        empresa_id: str,
        datos_evento: Dict[str, Any],
        usuario_id: Optional[str]
    ) -> Dict[str, Any]:
        """Ejecuta las acciones definidas en el trigger."""
        acciones_json = trigger.get('AccionesJSON', '[]')
        
        try:
            acciones = json.loads(acciones_json) if acciones_json else []
        except json.JSONDecodeError:
            return {"error": "JSON de acciones inválido"}
        
        resultados = []
        
        for accion in acciones:
            tipo_accion = accion.get('tipo')
            
            if tipo_accion == TriggerAction.CREAR_ACTIVIDAD.value:
                res = self._accion_crear_actividad(entidad_id, empresa_id, accion, datos_evento)
            elif tipo_accion == TriggerAction.ENVIAR_EMAIL.value:
                res = self._accion_enviar_email(entidad_id, empresa_id, accion, datos_evento)
            elif tipo_accion == TriggerAction.ENVIAR_WHATSAPP.value:
                res = self._accion_enviar_whatsapp(entidad_id, empresa_id, accion, datos_evento)
            elif tipo_accion == TriggerAction.CREAR_NOTIFICACION.value:
                res = self._accion_crear_notificacion(entidad_id, empresa_id, accion, datos_evento)
            elif tipo_accion == TriggerAction.ACTUALIZAR_CAMPO.value:
                res = self._accion_actualizar_campo(entidad_id, accion)
            elif tipo_accion == TriggerAction.WEBHOOK.value:
                res = self._accion_webhook(entidad_id, empresa_id, accion, datos_evento)
            elif tipo_accion == TriggerAction.CREAR_TAREA_SEGUIMIENTO.value:
                res = self._accion_crear_tarea_seguimiento(entidad_id, empresa_id, accion, datos_evento)
            else:
                res = {"error": f"Tipo de acción no soportado: {tipo_accion}"}
            
            resultados.append({"tipo": tipo_accion, "resultado": res})
        
        return {
            "acciones_ejecutadas": len(resultados),
            "detalle": resultados
        }
    
    def _accion_crear_actividad(
        self, oportunidad_id: str, empresa_id: str, accion: Dict, datos: Dict
    ) -> Dict:
        """Crea una actividad de seguimiento."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            actividad_id = str(uuid.uuid4())
            
            dias = accion.get('dias_programar', 1)
            titulo = accion.get('titulo', 'Seguimiento automático')
            descripcion = accion.get('descripcion', 'Actividad generada por trigger')
            
            # Reemplazar variables en titulo/descripcion
            titulo = self._reemplazar_variables(titulo, datos)
            descripcion = self._reemplazar_variables(descripcion, datos)
            
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
                titulo, descripcion, dias
            ))
            conn.commit()
            
            logger.info(f"[CRM-Trigger] Actividad creada: {actividad_id}")
            return {"success": True, "actividad_id": actividad_id}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def _accion_enviar_email(
        self, oportunidad_id: str, empresa_id: str, accion: Dict, datos: Dict
    ) -> Dict:
        """Envía un email usando el servicio de notificaciones."""
        if not self.notification_service:
            return {"success": False, "error": "Servicio de email no disponible"}
        
        # Obtener datos del responsable/contacto
        destinatario = accion.get('destinatario_email') or datos.get('email_contacto')
        if not destinatario:
            return {"success": False, "error": "No hay destinatario de email"}
        
        asunto = self._reemplazar_variables(accion.get('asunto', 'Notificación CRM'), datos)
        cuerpo = self._reemplazar_variables(accion.get('cuerpo_html', ''), datos)
        
        resultado = self.notification_service.enviar_email(
            destinatario=destinatario,
            asunto=asunto,
            cuerpo_html=cuerpo
        )
        
        return resultado
    
    def _accion_enviar_whatsapp(
        self, oportunidad_id: str, empresa_id: str, accion: Dict, datos: Dict
    ) -> Dict:
        """Envía un WhatsApp usando el servicio de notificaciones."""
        if not self.notification_service:
            return {"success": False, "error": "Servicio de WhatsApp no disponible"}
        
        telefono = accion.get('telefono') or datos.get('telefono_contacto')
        if not telefono:
            return {"success": False, "error": "No hay teléfono de destino"}
        
        mensaje = self._reemplazar_variables(accion.get('mensaje', ''), datos)
        
        resultado = self.notification_service.enviar_whatsapp(
            telefono=telefono,
            mensaje=mensaje
        )
        
        return resultado
    
    def _accion_crear_notificacion(
        self, oportunidad_id: str, empresa_id: str, accion: Dict, datos: Dict
    ) -> Dict:
        """Crea una notificación interna."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            notif_id = str(uuid.uuid4())
            
            # Determinar destinatario
            usuario_destino = accion.get('usuario_destino_id') or datos.get('responsable_id')
            
            if not usuario_destino:
                return {"success": False, "error": "No hay usuario destino"}
            
            titulo = self._reemplazar_variables(accion.get('titulo', 'Notificación CRM'), datos)
            mensaje = self._reemplazar_variables(accion.get('mensaje', ''), datos)
            
            cursor.execute("""
                INSERT INTO Notificaciones (
                    NotificacionID, EmpresaID, UsuarioDestinoID,
                    Tipo, Titulo, Mensaje, EntidadTipo, EntidadID,
                    Leida, FechaCreacion
                ) VALUES (
                    %s, %s, %s, 'CRM_TRIGGER', %s, %s, 'OPORTUNIDAD', %s, 0, GETDATE()
                )
            """, (notif_id, empresa_id, usuario_destino, titulo, mensaje, oportunidad_id))
            
            conn.commit()
            return {"success": True, "notificacion_id": notif_id}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def _accion_actualizar_campo(self, oportunidad_id: str, accion: Dict) -> Dict:
        """Actualiza un campo de la oportunidad."""
        campo = accion.get('campo')
        valor = accion.get('valor')
        
        campos_permitidos = [
            'ProbabilidadCierre', 'Prioridad', 'ResponsableID',
            'EstatusOportunidadID', 'MontoEstimado'
        ]
        
        if campo not in campos_permitidos:
            return {"success": False, "error": f"Campo no permitido: {campo}"}
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE CRM_Oportunidades
                SET {campo} = %s, FechaModificacion = GETDATE()
                WHERE OportunidadID = %s
            """, (valor, oportunidad_id))
            
            conn.commit()
            return {"success": True, "campo": campo, "nuevo_valor": valor}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def _accion_webhook(
        self, oportunidad_id: str, empresa_id: str, accion: Dict, datos: Dict
    ) -> Dict:
        """Envía datos a un webhook externo."""
        import requests
        
        url = accion.get('url')
        if not url:
            return {"success": False, "error": "URL de webhook no especificada"}
        
        payload = {
            "evento": datos.get('evento'),
            "oportunidad_id": oportunidad_id,
            "empresa_id": empresa_id,
            "timestamp": datetime.now().isoformat(),
            "datos": datos
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=accion.get('headers', {}),
                timeout=10
            )
            
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "response": response.text[:500]  # Limitar respuesta
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _accion_crear_tarea_seguimiento(
        self, oportunidad_id: str, empresa_id: str, accion: Dict, datos: Dict
    ) -> Dict:
        """Crea una tarea de seguimiento con recordatorio."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            tarea_id = str(uuid.uuid4())
            
            dias = accion.get('dias_programar', 3)
            prioridad = accion.get('prioridad', 'MEDIA')
            titulo = self._reemplazar_variables(
                accion.get('titulo', 'Seguimiento pendiente: {nombre_oportunidad}'), 
                datos
            )
            
            cursor.execute("""
                INSERT INTO CRM_Tareas (
                    TareaID, EmpresaID, OportunidadID, ResponsableID,
                    Titulo, Descripcion, FechaVencimiento, Prioridad,
                    EstatusID, AutoGenerada, FechaCreacion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, DATEADD(day, %s, GETDATE()), %s,
                    1, 1, GETDATE()
                )
            """, (
                tarea_id, empresa_id, oportunidad_id,
                datos.get('responsable_id'),
                titulo,
                accion.get('descripcion', 'Tarea generada automáticamente'),
                dias, prioridad
            ))
            
            conn.commit()
            return {"success": True, "tarea_id": tarea_id}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def _reemplazar_variables(self, texto: str, datos: Dict[str, Any]) -> str:
        """Reemplaza variables {variable} en el texto con datos reales."""
        if not texto:
            return texto
        
        for key, value in datos.items():
            texto = texto.replace(f"{{{key}}}", str(value) if value else '')
        
        return texto
    
    def _registrar_ejecucion(
        self,
        trigger_id: str,
        entidad_id: str,
        empresa_id: str,
        resultado: Dict[str, Any]
    ):
        """Registra la ejecución de un trigger en el log."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            log_id = str(uuid.uuid4())
            
            exitoso = resultado.get('acciones_ejecutadas', 0) > 0
            
            cursor.execute("""
                INSERT INTO CRM_Trigger_Log (
                    LogID, TriggerID, EntidadID, EmpresaID,
                    Exitoso, ResultadoJSON, FechaEjecucion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, GETDATE()
                )
            """, (
                log_id, trigger_id, entidad_id, empresa_id,
                1 if exitoso else 0, json.dumps(resultado)
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"[CRM-Trigger] Error registrando ejecución: {e}")
        finally:
            conn.close()
    
    # ==================== GESTIÓN DE TRIGGERS ====================
    
    def crear_trigger(
        self,
        empresa_id: str,
        nombre: str,
        tipo_evento: TriggerEvent,
        acciones: List[Dict[str, Any]],
        condiciones: Dict[str, Any] = None,
        prioridad: int = 100,
        usuario_id: str = None
    ) -> Dict[str, Any]:
        """Crea un nuevo trigger."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            trigger_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO CRM_Triggers (
                    TriggerID, EmpresaID, Nombre, TipoEvento,
                    CondicionesJSON, AccionesJSON, Prioridad,
                    Activo, UsuarioCreacionID, FechaCreacion
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, 1, %s, GETDATE()
                )
            """, (
                trigger_id, empresa_id, nombre, tipo_evento.value,
                json.dumps(condiciones or {}),
                json.dumps(acciones),
                prioridad, usuario_id
            ))
            
            conn.commit()
            
            logger.info(f"[CRM-Trigger] Trigger creado: {nombre} ({trigger_id})")
            return {"success": True, "trigger_id": trigger_id}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[CRM-Trigger] Error creando trigger: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def listar_triggers(self, empresa_id: str, activos_solo: bool = True) -> List[Dict]:
        """Lista todos los triggers de una empresa."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    TriggerID, Nombre, TipoEvento, CondicionesJSON,
                    AccionesJSON, Prioridad, Activo, FechaCreacion
                FROM CRM_Triggers
                WHERE EmpresaID = %s
            """
            
            if activos_solo:
                query += " AND Activo = 1"
            
            query += " ORDER BY Prioridad ASC, FechaCreacion DESC"
            
            cursor.execute(query, (empresa_id,))
            return cursor.fetchall() or []
            
        finally:
            conn.close()
    
    def activar_desactivar_trigger(
        self, trigger_id: str, activo: bool
    ) -> Dict[str, Any]:
        """Activa o desactiva un trigger."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE CRM_Triggers
                SET Activo = %s, FechaModificacion = GETDATE()
                WHERE TriggerID = %s
            """, (1 if activo else 0, trigger_id))
            
            conn.commit()
            return {"success": True, "activo": activo}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()


# Singleton
_trigger_service = None

def get_crm_trigger_service() -> CRMTriggerService:
    """Factory para obtener el servicio de triggers."""
    global _trigger_service
    if _trigger_service is None:
        _trigger_service = CRMTriggerService()
    return _trigger_service
