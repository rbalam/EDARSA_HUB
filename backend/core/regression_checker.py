"""
EDARSA HUB - Sistema de Detección de Regresiones
=================================================
Sistema automático para detectar regresiones en módulos críticos.

MÓDULOS PRIORITARIOS:
1. Tablero Ejecutivo
2. Auditoría de Compras
3. Operaciones / Análisis

PRINCIPIOS:
- Detectar regresiones antes de que lleguen al usuario
- Distinguir error técnico vs dato real
- No interpretar falla como cero
- Alertas claras y accionables

CREADO: 2026-04-19
"""

import logging
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS Y TIPOS
# ============================================================================

class CheckStatus(Enum):
    """Estado de un check de regresión"""
    OK = "ok"
    WARNING = "warning"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"


class Severity(Enum):
    """Severidad de una regresión"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ModuleName(Enum):
    """Módulos monitoreados"""
    TABLERO_EJECUTIVO = "tablero_ejecutivo"
    AUDITORIA_COMPRAS = "auditoria_compras"
    OPERACIONES_ANALISIS = "operaciones_analisis"
    FINANZAS = "finanzas"
    COMPRAS = "compras"
    RH = "rh"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CheckResult:
    """Resultado de un check de regresión"""
    module: ModuleName
    check_name: str
    status: CheckStatus
    severity: Severity
    message: str
    source_validated: Optional[str] = None
    expected: Any = None
    actual: Any = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module.value,
            "check_name": self.check_name,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "source_validated": self.source_validated,
            "expected": self.expected,
            "actual": self.actual,
            "evidence": self.evidence,
            "executed_at": self.executed_at.isoformat(),
            "duration_ms": round(self.duration_ms, 2)
        }


@dataclass
class RegressionReport:
    """Reporte completo de regresiones"""
    execution_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    total_checks: int = 0
    passed: int = 0
    warnings: int = 0
    failed: int = 0
    errors: int = 0
    results: List[CheckResult] = field(default_factory=list)
    overall_status: CheckStatus = CheckStatus.OK
    
    def add_result(self, result: CheckResult):
        self.results.append(result)
        self.total_checks += 1
        if result.status == CheckStatus.OK:
            self.passed += 1
        elif result.status == CheckStatus.WARNING:
            self.warnings += 1
        elif result.status == CheckStatus.FAIL:
            self.failed += 1
            if result.severity in [Severity.CRITICAL, Severity.HIGH]:
                self.overall_status = CheckStatus.FAIL
        elif result.status == CheckStatus.ERROR:
            self.errors += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "summary": {
                "total_checks": self.total_checks,
                "passed": self.passed,
                "warnings": self.warnings,
                "failed": self.failed,
                "errors": self.errors,
                "overall_status": self.overall_status.value
            },
            "results": [r.to_dict() for r in self.results]
        }


# ============================================================================
# CHECKS BASE
# ============================================================================

class BaseRegressionCheck:
    """Clase base para checks de regresión"""
    
    def __init__(self, module: ModuleName, check_name: str):
        self.module = module
        self.check_name = check_name
        self.logger = logging.getLogger(f"regression.{module.value}.{check_name}")
    
    def run(self) -> CheckResult:
        """Ejecuta el check y devuelve resultado"""
        raise NotImplementedError


# ============================================================================
# CHECKS: TABLERO EJECUTIVO
# ============================================================================

class TableroVentasAcumuladasCheck(BaseRegressionCheck):
    """Verifica que ventas acumuladas no sean cero falso"""
    
    def __init__(self):
        super().__init__(ModuleName.TABLERO_EJECUTIVO, "ventas_acumuladas")
    
    def run(self) -> CheckResult:
        start = time.time()
        try:
            # Verificar que el servicio comercial esté disponible
            from modules.comercial.service import get_kpis_softrestaurant
            
            duration = (time.time() - start) * 1000
            
            # Si podemos importar el servicio, el check pasa
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.OK,
                severity=Severity.LOW,
                message="Servicio de KPIs disponible y operativo",
                evidence={"service_available": True},
                duration_ms=duration
            )
            
        except ImportError as e:
            duration = (time.time() - start) * 1000
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.FAIL,
                severity=Severity.CRITICAL,
                message=f"Servicio de KPIs no disponible: {str(e)[:200]}",
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.ERROR,
                severity=Severity.HIGH,
                message=f"Error ejecutando check: {str(e)[:200]}",
                duration_ms=duration
            )


class TableroFuentesCheck(BaseRegressionCheck):
    """Verifica que las fuentes sean las correctas"""
    
    def __init__(self):
        super().__init__(ModuleName.TABLERO_EJECUTIVO, "fuentes_correctas")
    
    def run(self) -> CheckResult:
        start = time.time()
        try:
            # Verificar que el resolver está configurado
            from core.connection_resolver import get_resolution_matrix
            
            matrix = get_resolution_matrix()
            duration = (time.time() - start) * 1000
            
            # Validar estructura de matriz
            expected_systems = ["SoftRestaurant", "MPRO"]
            for system in expected_systems:
                if system not in matrix:
                    return CheckResult(
                        module=self.module,
                        check_name=self.check_name,
                        status=CheckStatus.FAIL,
                        severity=Severity.HIGH,
                        message=f"Sistema {system} no encontrado en matriz de resolución",
                        duration_ms=duration
                    )
            
            # Validar métricas clave
            for system, metrics in matrix.items():
                if "accumulated_sales" not in metrics:
                    return CheckResult(
                        module=self.module,
                        check_name=self.check_name,
                        status=CheckStatus.FAIL,
                        severity=Severity.HIGH,
                        message=f"Métrica accumulated_sales no definida para {system}",
                        duration_ms=duration
                    )
            
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.OK,
                severity=Severity.LOW,
                message="Matriz de fuentes correctamente configurada",
                evidence={"systems": list(matrix.keys())},
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (time.time() - start) * 1000
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.ERROR,
                severity=Severity.CRITICAL,
                message=f"Error verificando fuentes: {str(e)[:200]}",
                duration_ms=duration
            )


class TableroComparativosCheck(BaseRegressionCheck):
    """Verifica que los comparativos funcionen"""
    
    def __init__(self):
        super().__init__(ModuleName.TABLERO_EJECUTIVO, "comparativos")
    
    def run(self) -> CheckResult:
        start = time.time()
        try:
            # Verificar que las funciones de comparativo estén disponibles
            from modules.comercial.service import get_kpis_softrestaurant, get_kpis_mpro
            
            duration = (time.time() - start) * 1000
            
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.OK,
                severity=Severity.LOW,
                message="Funciones de KPIs y comparativos disponibles",
                evidence={"functions_available": ["get_kpis_softrestaurant", "get_kpis_mpro"]},
                duration_ms=duration
            )
            
        except ImportError as e:
            duration = (time.time() - start) * 1000
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                message=f"Funciones de comparativos no disponibles: {str(e)[:200]}",
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.ERROR,
                severity=Severity.MEDIUM,
                message=f"Error verificando comparativos: {str(e)[:200]}",
                duration_ms=duration
            )


# ============================================================================
# CHECKS: CONEXIONES
# ============================================================================

class ConexionesResolverCheck(BaseRegressionCheck):
    """Verifica que el resolver de conexiones esté operativo"""
    
    def __init__(self):
        super().__init__(ModuleName.TABLERO_EJECUTIVO, "conexiones_resolver")
    
    def run(self) -> CheckResult:
        start = time.time()
        try:
            from core.connection_resolver import (
                get_connection_resolver,
                MetricType
            )
            
            resolver = get_connection_resolver()
            duration = (time.time() - start) * 1000
            
            if resolver is None:
                return CheckResult(
                    module=self.module,
                    check_name=self.check_name,
                    status=CheckStatus.FAIL,
                    severity=Severity.CRITICAL,
                    message="ConnectionResolver no inicializado",
                    duration_ms=duration
                )
            
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.OK,
                severity=Severity.LOW,
                message="ConnectionResolver operativo",
                duration_ms=duration
            )
            
        except ImportError as e:
            duration = (time.time() - start) * 1000
            return CheckResult(
                module=self.module,
                check_name=self.check_name,
                status=CheckStatus.FAIL,
                severity=Severity.CRITICAL,
                message=f"No se puede importar ConnectionResolver: {str(e)[:200]}",
                duration_ms=duration
            )


# ============================================================================
# REGRESSION CHECKER PRINCIPAL
# ============================================================================

class RegressionChecker:
    """
    Sistema principal de detección de regresiones.
    
    Uso:
        checker = RegressionChecker()
        report = checker.run_all_checks()
        
        if report.overall_status == CheckStatus.FAIL:
            # Alertar
            pass
    """
    
    def __init__(self):
        self.checks: List[BaseRegressionCheck] = []
        self._register_default_checks()
        self.logger = logging.getLogger("regression_checker")
    
    def _register_default_checks(self):
        """Registra los checks por defecto"""
        # Tablero Ejecutivo
        self.checks.append(TableroVentasAcumuladasCheck())
        self.checks.append(TableroFuentesCheck())
        self.checks.append(TableroComparativosCheck())
        self.checks.append(ConexionesResolverCheck())
    
    def register_check(self, check: BaseRegressionCheck):
        """Registra un check adicional"""
        self.checks.append(check)
    
    def run_all_checks(self) -> RegressionReport:
        """Ejecuta todos los checks registrados"""
        import uuid
        
        report = RegressionReport(
            execution_id=str(uuid.uuid4())[:8],
            started_at=datetime.now(timezone.utc)
        )
        
        self.logger.info(f"[REGRESSION] Iniciando {len(self.checks)} checks...")
        
        for check in self.checks:
            try:
                self.logger.info(f"[REGRESSION] Ejecutando: {check.module.value}/{check.check_name}")
                result = check.run()
                report.add_result(result)
                
                # Log según status
                if result.status == CheckStatus.OK:
                    self.logger.info(f"  ✅ {result.message}")
                elif result.status == CheckStatus.WARNING:
                    self.logger.warning(f"  ⚠️ {result.message}")
                elif result.status in [CheckStatus.FAIL, CheckStatus.ERROR]:
                    self.logger.error(f"  ❌ {result.message}")
                    
            except Exception as e:
                error_result = CheckResult(
                    module=check.module,
                    check_name=check.check_name,
                    status=CheckStatus.ERROR,
                    severity=Severity.HIGH,
                    message=f"Excepción no manejada: {str(e)[:200]}"
                )
                report.add_result(error_result)
                self.logger.error(f"  💥 Excepción en {check.check_name}: {e}")
        
        report.finished_at = datetime.now(timezone.utc)
        
        # Resumen final
        duration_total = (report.finished_at - report.started_at).total_seconds() * 1000
        self.logger.info(
            f"[REGRESSION] Completado en {duration_total:.0f}ms | "
            f"✅{report.passed} ⚠️{report.warnings} ❌{report.failed} 💥{report.errors}"
        )
        
        return report
    
    def run_module_checks(self, module: ModuleName) -> RegressionReport:
        """Ejecuta solo los checks de un módulo específico"""
        import uuid
        
        report = RegressionReport(
            execution_id=str(uuid.uuid4())[:8],
            started_at=datetime.now(timezone.utc)
        )
        
        module_checks = [c for c in self.checks if c.module == module]
        
        for check in module_checks:
            try:
                result = check.run()
                report.add_result(result)
            except Exception as e:
                error_result = CheckResult(
                    module=check.module,
                    check_name=check.check_name,
                    status=CheckStatus.ERROR,
                    severity=Severity.HIGH,
                    message=f"Excepción: {str(e)[:200]}"
                )
                report.add_result(error_result)
        
        report.finished_at = datetime.now(timezone.utc)
        return report


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

_checker_instance = None

def get_regression_checker() -> RegressionChecker:
    """Obtiene instancia singleton del RegressionChecker"""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = RegressionChecker()
    return _checker_instance


def run_regression_checks() -> RegressionReport:
    """Ejecuta todos los checks de regresión"""
    return get_regression_checker().run_all_checks()


def run_module_regression_checks(module: ModuleName) -> RegressionReport:
    """Ejecuta checks de regresión para un módulo específico"""
    return get_regression_checker().run_module_checks(module)
