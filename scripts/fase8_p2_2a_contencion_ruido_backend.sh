#!/usr/bin/env bash
set -euo pipefail

# FASE 8 - P2-2A  Contención de ruido backend no bloqueante
# (validado por el agente: imports Dict/Any/datetime presentes en crm_sync_job;
#  replaces de cadena exacta -> fail-safe no-op si no calzan)

BACK_DIR="/app/backend"
OUT_DIR="/app/auditorias_p5"
TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE8_P2_2A_BACKEND_NOISE_${TS}.txt"

HEALTH_FILE="$BACK_DIR/core/health_checker.py"
CRM_FILE="$BACK_DIR/core/scheduler/jobs/crm_sync_job.py"
SLA_FILE="$BACK_DIR/modules/fase2_operativo/services/sla_service.py"

mkdir -p "$OUT_DIR" /app/scripts
cd /app || exit 1
for f in "$HEALTH_FILE" "$CRM_FILE" "$SLA_FILE"; do [ -f "$f" ] || { echo "ERROR: no existe $f"; exit 1; }; done

echo "FASE 8 - P2-2A  $(date)" | tee "$RAW"

echo "===== BACKUPS =====" | tee -a "$RAW"
for f in "$HEALTH_FILE" "$CRM_FILE" "$SLA_FILE"; do cp "$f" "${f}.bak_${TS}"; echo "BACKUP ${f}.bak_${TS}" | tee -a "$RAW"; done

echo "===== PARCHE health_checker.py =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
p = Path("/app/backend/core/health_checker.py")
txt = p.read_text(encoding="utf-8"); original = txt
old_mongo = '''    def _check_mongodb(self) -> SourceHealth:
        """Verifica conexión a MongoDB"""
        start = time.time()
        try:
            pass  # P2-07: MongoDB eliminado (MongoClient)
            import os
            
            mongo_url = None  # P2-07: MongoDB eliminado
            client = None  # P2-07: MongoDB eliminado
            client.admin.command('ping')
            
            response_time = (time.time() - start) * 1000
            
            return SourceHealth(
                name="MongoDB (EDARSA HUB)",
                source_type=SourceType.MONGODB,
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_success=datetime.now(timezone.utc)
            )
        except Exception as e:
            return SourceHealth(
                name="MongoDB (EDARSA HUB)",
                source_type=SourceType.MONGODB,
                status=HealthStatus.CRITICAL,
                last_error=str(e)[:200]
            )
'''
new_mongo = '''    def _check_mongodb(self) -> SourceHealth:
        """MongoDB eliminado del camino productivo. Se reporta solo como residual deshabilitado."""
        return SourceHealth(
            name="MongoDB (EDARSA HUB)",
            source_type=SourceType.MONGODB,
            status=HealthStatus.UNKNOWN,
            last_error="MongoDB eliminado del flujo productivo (SQL-First / NO-MONGO)"
        )
'''
txt = txt.replace(old_mongo, new_mongo)
old_sql = '''    def _check_sql_servers(self) -> List[SourceHealth]:
        """Verifica conexión a servidores SQL"""
        results = []
        try:
            pass  # P2-07: MongoDB eliminado (MongoClient)
            import os
            
            mongo_url = None  # P2-07: MongoDB eliminado
            client = None  # P2-07: MongoDB eliminado
            db = client['edarsa_hub']
            
            servers = list(db.servers.find(
                {"active": True, "visible_en_operaciones": True},
                {"_id": 0, "id": 1, "name": 1, "host": 1, "system_type": 1}
            ))
            
            for server in servers:
                # Por ahora solo verificamos que estén registrados
                # En producción aquí haríamos ping real
                results.append(SourceHealth(
                    name=f"{server.get('name')} ({server.get('system_type')})",
                    source_type=SourceType.SQL_SERVER,
                    status=HealthStatus.HEALTHY,  # Asumimos healthy si está en catálogo
                    last_success=datetime.now(timezone.utc)
                ))
                
        except Exception as e:
            self.logger.error(f"Error verificando SQL servers: {e}")
        
        return results
'''
new_sql = '''    def _check_sql_servers(self) -> List[SourceHealth]:
        """
        Catálogo legacy de servidores dependía de Mongo.
        En V1 estabilizada se omite para evitar ruido falso-crítico.
        """
        return []
'''
txt = txt.replace(old_sql, new_sql)
old_count = '''        mongo_health = self._check_mongodb()
        report.sources.append(mongo_health)
        if mongo_health.status == HealthStatus.HEALTHY:
            report.sources_connected += 1
        else:
            report.sources_failed += 1
        
        # Verificar SQL Servers
        sql_healths = self._check_sql_servers()
        for sql_health in sql_healths:
            report.sources.append(sql_health)
            if sql_health.status == HealthStatus.HEALTHY:
                report.sources_connected += 1
            else:
                report.sources_failed += 1
'''
new_count = '''        mongo_health = self._check_mongodb()
        report.sources.append(mongo_health)
        if mongo_health.status == HealthStatus.HEALTHY:
            report.sources_connected += 1
        elif mongo_health.status == HealthStatus.CRITICAL:
            report.sources_failed += 1
        
        # Verificar SQL Servers
        sql_healths = self._check_sql_servers()
        for sql_health in sql_healths:
            report.sources.append(sql_health)
            if sql_health.status == HealthStatus.HEALTHY:
                report.sources_connected += 1
            elif sql_health.status == HealthStatus.CRITICAL:
                report.sources_failed += 1
'''
txt = txt.replace(old_count, new_count)
if "P2_2A_NOISE_BACKEND" not in txt:
    txt = "# P2_2A_NOISE_BACKEND\n" + txt
if txt != original:
    p.write_text(txt, encoding="utf-8"); print("PATCHED health_checker.py")
else:
    print("NO CHANGE health_checker.py")
PY

echo "===== PARCHE crm_sync_job.py =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
p = Path("/app/backend/core/scheduler/jobs/crm_sync_job.py")
txt = p.read_text(encoding="utf-8"); original = txt
if "def _is_missing_schema_error(" not in txt:
    anchor = "logger = logging.getLogger(__name__)\n\n\n"
    helper = '''logger = logging.getLogger(__name__)\n\n\ndef _is_missing_schema_error(exc: Exception) -> bool:\n    msg = str(exc or "").lower()\n    return (\n        "invalid column name" in msg\n        or "oportunidadid" in msg\n        or "fecha notificacion" in msg\n        or "notificacionenviada" in msg\n    )\n\n\ndef _skip_result(kind: str, inicio: datetime, reason: str) -> Dict[str, Any]:\n    return {\n        "estatus_general": "SKIP",\n        "mensaje": reason,\n        "duracion_ms": int((datetime.now() - inicio).total_seconds() * 1000),\n        "fecha_ejecucion": inicio.isoformat(),\n        "errores": []\n    }\n\n\n'''
    txt = txt.replace(anchor, helper)
old1 = '''    except Exception as e:
        logger.error(f"[CRM-SLA] Error verificando SLAs: {e}")
    finally:
        conn.close()
'''
new1 = '''    except Exception as e:
        if _is_missing_schema_error(e):
            logger.warning(f"[CRM-SLA] SKIP por esquema CRM incompleto: {e}")
            conn.close()
            return _skip_result("crm_sla", inicio, f"CRM schema incompleto: {str(e)[:160]}")
        logger.error(f"[CRM-SLA] Error verificando SLAs: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
'''
txt = txt.replace(old1, new1)
old2 = '''    except Exception as e:
        logger.error(f"[CRM-ACT] Error general: {e}")
    finally:
        conn.close()
'''
new2 = '''    except Exception as e:
        if _is_missing_schema_error(e):
            logger.warning(f"[CRM-ACT] SKIP por esquema CRM incompleto: {e}")
            conn.close()
            return _skip_result("crm_actividades", inicio, f"CRM schema incompleto: {str(e)[:160]}")
        logger.error(f"[CRM-ACT] Error general: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
'''
txt = txt.replace(old2, new2)
if "P2_2A_NOISE_BACKEND" not in txt:
    txt = "# P2_2A_NOISE_BACKEND\n" + txt
if txt != original:
    p.write_text(txt, encoding="utf-8"); print("PATCHED crm_sync_job.py")
else:
    print("NO CHANGE crm_sync_job.py")
PY

echo "===== PARCHE sla_service.py =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
p = Path("/app/backend/modules/fase2_operativo/services/sla_service.py")
txt = p.read_text(encoding="utf-8"); original = txt
needle_calc = '''    def calcular_estado_sla(self, tarea: Dict) -> Dict[str, Any]:
        """
        Calcula el estado SLA de una tarea.
        
        Args:
            tarea: Datos de la tarea
            
        Returns:
            Dict con estado_sla y métricas calculadas
        """
        ahora = datetime.now(timezone.utc)
'''
repl_calc = '''    def calcular_estado_sla(self, tarea: Dict) -> Dict[str, Any]:
        """
        Calcula el estado SLA de una tarea.
        
        Args:
            tarea: Datos de la tarea
            
        Returns:
            Dict con estado_sla y métricas calculadas
        """
        if not tarea or not isinstance(tarea, dict):
            return {
                "estado_sla": EstadoSLA.EN_TIEMPO.value,
                "tiempo_respuesta_horas": None,
                "tiempo_resolucion_horas": None,
                "porcentaje_tiempo_consumido": 0,
                "horas_restantes": 0,
                "limite_horas": 0,
                "cumple_sla": None
            }

        ahora = datetime.now(timezone.utc)
'''
txt = txt.replace(needle_calc, repl_calc)
txt = txt.replace('''        for tarea in tareas:
            try:
                calculo = self.calcular_estado_sla(tarea)
''','''        for tarea in tareas:
            try:
                if not tarea or not isinstance(tarea, dict):
                    continue
                calculo = self.calcular_estado_sla(tarea)
''')
txt = txt.replace('''        for tarea in completadas:
            calculo = self.calcular_estado_sla(tarea)
''','''        for tarea in completadas:
            if not tarea or not isinstance(tarea, dict):
                continue
            calculo = self.calcular_estado_sla(tarea)
''')
txt = txt.replace('''        for tarea in activas:
            calculo = self.calcular_estado_sla(tarea)
''','''        for tarea in activas:
            if not tarea or not isinstance(tarea, dict):
                continue
            calculo = self.calcular_estado_sla(tarea)
''')
txt = txt.replace('''        for tarea in tareas[:limite * 2]:
            calculo = self.calcular_estado_sla(tarea)
''','''        for tarea in tareas[:limite * 2]:
            if not tarea or not isinstance(tarea, dict):
                continue
            calculo = self.calcular_estado_sla(tarea)
''')
txt = txt.replace('''        for tarea in tareas:
            if tarea.get("vencida") or tarea.get("estado_sla") == EstadoSLA.VENCIDA.value:
''','''        for tarea in tareas:
            if not tarea or not isinstance(tarea, dict):
                continue
            if tarea.get("vencida") or tarea.get("estado_sla") == EstadoSLA.VENCIDA.value:
''')
txt = txt.replace('''    async def notify_sla_warning(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica que un SLA está por vencer (80% consumido).
        """
        notifier = self._get_notification_service()
''','''    async def notify_sla_warning(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica que un SLA está por vencer (80% consumido).
        """
        if not tarea or not isinstance(tarea, dict):
            return False

        notifier = self._get_notification_service()
''')
txt = txt.replace('''    async def notify_sla_expired(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica que un SLA venció (100% consumido).
        """
        notifier = self._get_notification_service()
''','''    async def notify_sla_expired(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica que un SLA venció (100% consumido).
        """
        if not tarea or not isinstance(tarea, dict):
            return False

        notifier = self._get_notification_service()
''')
txt = txt.replace('''    async def notify_sla_escalated(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica escalamiento de SLA (150% consumido).
        """
        notifier = self._get_notification_service()
''','''    async def notify_sla_escalated(
        self,
        tarea: Dict,
        workflow: Optional[Dict] = None
    ) -> bool:
        """
        Notifica escalamiento de SLA (150% consumido).
        """
        if not tarea or not isinstance(tarea, dict):
            return False

        notifier = self._get_notification_service()
''')
if "P2_2A_NOISE_BACKEND" not in txt:
    txt = "# P2_2A_NOISE_BACKEND\n" + txt
if txt != original:
    p.write_text(txt, encoding="utf-8"); print("PATCHED sla_service.py")
else:
    print("NO CHANGE sla_service.py")
PY

echo "===== VALIDACION SINTACTICA =====" | tee -a "$RAW"
python3 -m py_compile "$HEALTH_FILE" && echo "COMPILE health OK" | tee -a "$RAW"
python3 -m py_compile "$CRM_FILE" && echo "COMPILE crm OK" | tee -a "$RAW"
python3 -m py_compile "$SLA_FILE" && echo "COMPILE sla OK" | tee -a "$RAW"

echo "===== REINICIO BACKEND =====" | tee -a "$RAW"
sudo supervisorctl restart backend || true
sleep 9
sudo supervisorctl status backend | head -1 | tee -a "$RAW"

echo "===== SMOKE health/v1 =====" | tee -a "$RAW"
curl -sS --max-time 20 -o /tmp/f8_hv1.json -w "HTTP=%{http_code}\n" "http://127.0.0.1:8001/api/health/v1" | tee -a "$RAW" || true

echo "===== SMOKE health_checker =====" | tee -a "$RAW"
cd "$BACK_DIR"
python3 - <<'PY' | tee -a "$RAW"
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
from core.health_checker import get_system_health
rep = get_system_health()
s = rep.get("summary", {}) if isinstance(rep, dict) else {}
print("OVERALL=", s.get("overall_status"), "FAILED=", s.get("sources_failed"), "CONNECTED=", s.get("sources_connected"))
PY

echo "===== SMOKE crm_sync_job =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
import asyncio
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
from core.scheduler.jobs.crm_sync_job import execute_crm_sla_check, execute_crm_actividades_vencidas
async def main():
    print("CRM_SLA=", (await execute_crm_sla_check(None)).get("estatus_general"))
    print("CRM_ACT=", (await execute_crm_actividades_vencidas(None)).get("estatus_general"))
asyncio.run(main())
PY

echo "===== SMOKE sla_service =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
import asyncio
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
from modules.fase2_operativo.services.sla_service import get_sla_service
svc = get_sla_service(None)
print("CALC_NONE_estado=", svc.calcular_estado_sla(None).get("estado_sla"))
async def main():
    print("WARN_NONE=", await svc.notify_sla_warning(None))
    print("EXP_NONE=", await svc.notify_sla_expired(None))
    print("ESC_NONE=", await svc.notify_sla_escalated(None))
asyncio.run(main())
PY

echo "RAW_REPORT=$RAW" | tee -a "$RAW"
echo "OK - FASE 8 ejecutado" | tee -a "$RAW"
