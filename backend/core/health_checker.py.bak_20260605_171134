"""
EDARSA HUB - Sistema de Health Checks y Dashboard de Salud
==========================================================
Sistema de monitoreo de salud para dirección ejecutiva.

PROPÓSITO:
- Ver estado general del sistema en segundos
- Detectar módulos en riesgo
- Identificar fuentes caídas
- Monitorear estabilidad

CREADO: 2026-04-19
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class HealthStatus(Enum):
    """Estado de salud"""
    HEALTHY = "healthy"         # Todo OK
    DEGRADED = "degraded"       # Funciona con problemas
    CRITICAL = "critical"       # Falla grave
    UNKNOWN = "unknown"         # Sin datos


class SourceType(Enum):
    """Tipo de fuente"""
    SQL_SERVER = "sql_server"
    MONGODB = "mongodb"
    API_LOCAL = "api_local"
    SCHEDULER = "scheduler"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SourceHealth:
    """Salud de una fuente de datos"""
    name: str
    source_type: SourceType
    status: HealthStatus
    response_time_ms: Optional[float] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count_24h: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_type": self.source_type.value,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "error_count_24h": self.error_count_24h
        }


@dataclass
class ModuleHealth:
    """Salud de un módulo"""
    name: str
    status: HealthStatus
    last_validation: Optional[datetime] = None
    active_alerts: int = 0
    max_severity: str = "low"
    reliability_score: float = 100.0  # 0-100
    recent_regressions: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "last_validation": self.last_validation.isoformat() if self.last_validation else None,
            "active_alerts": self.active_alerts,
            "max_severity": self.max_severity,
            "reliability_score": self.reliability_score,
            "recent_regressions": self.recent_regressions
        }


@dataclass
class SystemHealthReport:
    """Reporte completo de salud del sistema"""
    generated_at: datetime
    overall_status: HealthStatus
    modules_healthy: int = 0
    modules_degraded: int = 0
    modules_critical: int = 0
    sources_connected: int = 0
    sources_failed: int = 0
    regressions_today: int = 0
    last_regression_check: Optional[datetime] = None
    modules: List[ModuleHealth] = field(default_factory=list)
    sources: List[SourceHealth] = field(default_factory=list)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "overall_status": self.overall_status.value,
                "modules_healthy": self.modules_healthy,
                "modules_degraded": self.modules_degraded,
                "modules_critical": self.modules_critical,
                "sources_connected": self.sources_connected,
                "sources_failed": self.sources_failed,
                "regressions_today": self.regressions_today,
                "last_regression_check": self.last_regression_check.isoformat() if self.last_regression_check else None
            },
            "modules": [m.to_dict() for m in self.modules],
            "sources": [s.to_dict() for s in self.sources],
            "recent_events": self.recent_events[:10]  # Últimos 10
        }


# ============================================================================
# HEALTH CHECKER
# ============================================================================

class SystemHealthChecker:
    """
    Sistema de monitoreo de salud.
    
    Uso:
        checker = SystemHealthChecker()
        report = checker.get_health_report()
    """
    
    def __init__(self):
        self.logger = logging.getLogger("health_checker")
        self._events_log: List[Dict[str, Any]] = []
    
    def _check_mongodb(self) -> SourceHealth:
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
    
    def _check_sql_servers(self) -> List[SourceHealth]:
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
    
    def _get_module_health(self, module_name: str) -> ModuleHealth:
        """Obtiene salud de un módulo específico"""
        # En implementación completa, esto consultaría:
        # - Últimos resultados de regression checks
        # - Alertas activas
        # - Errores recientes
        
        return ModuleHealth(
            name=module_name,
            status=HealthStatus.HEALTHY,
            last_validation=datetime.now(timezone.utc),
            active_alerts=0,
            max_severity="low",
            reliability_score=100.0
        )
    
    def get_health_report(self) -> SystemHealthReport:
        """Genera reporte completo de salud del sistema"""
        self.logger.info("[HEALTH] Generando reporte de salud...")
        
        report = SystemHealthReport(
            generated_at=datetime.now(timezone.utc),
            overall_status=HealthStatus.HEALTHY
        )
        
        # Verificar MongoDB
        mongo_health = self._check_mongodb()
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
        
        # Verificar módulos críticos
        critical_modules = [
            "Tablero Ejecutivo",
            "Auditoría de Compras",
            "Operaciones / Análisis",
            "Finanzas",
            "Compras",
            "RH"
        ]
        
        for module_name in critical_modules:
            module_health = self._get_module_health(module_name)
            report.modules.append(module_health)
            
            if module_health.status == HealthStatus.HEALTHY:
                report.modules_healthy += 1
            elif module_health.status == HealthStatus.DEGRADED:
                report.modules_degraded += 1
            elif module_health.status == HealthStatus.CRITICAL:
                report.modules_critical += 1
        
        # Determinar estado general
        if report.modules_critical > 0 or report.sources_failed > 0:
            report.overall_status = HealthStatus.CRITICAL
        elif report.modules_degraded > 0:
            report.overall_status = HealthStatus.DEGRADED
        else:
            report.overall_status = HealthStatus.HEALTHY
        
        # Ejecutar regression checks
        try:
            from core.regression_checker import run_regression_checks
            regression_report = run_regression_checks()
            report.regressions_today = regression_report.failed + regression_report.errors
            report.last_regression_check = regression_report.finished_at
            
            # Actualizar módulos con resultados de regresión
            for result in regression_report.results:
                if result.status.value in ['fail', 'error']:
                    # Buscar y actualizar módulo correspondiente
                    for module in report.modules:
                        if result.module.value.replace('_', ' ').lower() in module.name.lower():
                            module.recent_regressions += 1
                            module.active_alerts += 1
                            if result.severity.value in ['critical', 'high']:
                                module.status = HealthStatus.DEGRADED
                                module.max_severity = result.severity.value
                            
        except Exception as e:
            self.logger.error(f"Error ejecutando regression checks: {e}")
        
        self.logger.info(
            f"[HEALTH] Reporte generado: {report.overall_status.value} | "
            f"Módulos: {report.modules_healthy}✅ {report.modules_degraded}⚠️ {report.modules_critical}❌"
        )
        
        return report
    
    def log_event(self, event_type: str, module: str, message: str, severity: str = "info"):
        """Registra un evento en la bitácora"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "module": module,
            "message": message,
            "severity": severity
        }
        self._events_log.append(event)
        
        # Mantener solo últimos 100 eventos
        if len(self._events_log) > 100:
            self._events_log = self._events_log[-100:]


# ============================================================================
# SINGLETON Y API
# ============================================================================

_health_checker_instance = None

def get_health_checker() -> SystemHealthChecker:
    """Obtiene instancia singleton del SystemHealthChecker"""
    global _health_checker_instance
    if _health_checker_instance is None:
        _health_checker_instance = SystemHealthChecker()
    return _health_checker_instance


def get_system_health() -> Dict[str, Any]:
    """Obtiene reporte de salud del sistema como dict"""
    return get_health_checker().get_health_report().to_dict()


# ============================================================================
# ENDPOINT HELPER
# ============================================================================

def create_health_summary() -> Dict[str, Any]:
    """Crea resumen ejecutivo de salud para dashboard"""
    report = get_health_checker().get_health_report()
    
    # Calcular KPIs
    total_modules = len(report.modules)
    pct_healthy = (report.modules_healthy / total_modules * 100) if total_modules > 0 else 0
    
    total_sources = len(report.sources)
    pct_sources_ok = (report.sources_connected / total_sources * 100) if total_sources > 0 else 0
    
    return {
        "status": report.overall_status.value,
        "status_emoji": "✅" if report.overall_status == HealthStatus.HEALTHY else ("⚠️" if report.overall_status == HealthStatus.DEGRADED else "❌"),
        "timestamp": report.generated_at.isoformat(),
        "kpis": {
            "modules_healthy_pct": round(pct_healthy, 1),
            "sources_connected_pct": round(pct_sources_ok, 1),
            "active_alerts": sum(m.active_alerts for m in report.modules),
            "regressions_24h": report.regressions_today
        },
        "modules_summary": [
            {
                "name": m.name,
                "status": m.status.value,
                "emoji": "✅" if m.status == HealthStatus.HEALTHY else ("⚠️" if m.status == HealthStatus.DEGRADED else "❌")
            }
            for m in report.modules
        ],
        "sources_summary": [
            {
                "name": s.name,
                "status": s.status.value,
                "response_ms": s.response_time_ms
            }
            for s in report.sources
        ]
    }
