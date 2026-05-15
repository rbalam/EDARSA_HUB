#!/usr/bin/env python3
"""
EDARSA HUB - Script de Validación: FASE 1B Sanitización SQL
============================================================
Valida que todas las protecciones de SQL Injection estén funcionando.

TESTS:
1-9: Validaciones de palabras clave y patrones
10-18: Validaciones de comentarios y múltiples statements
19-22: Validaciones de endpoints específicos

USO:
    python validate_sql_sanitization_fase_1b.py
    python validate_sql_sanitization_fase_1b.py --json
    python validate_sql_sanitization_fase_1b.py -v

AUTOR: E1 Agent
FECHA: Mayo 2026
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List

# Agregar path del backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import (
    SQLSanitizer, 
    SQLValidationResult,
    validate_sql_safe,
    validate_sql_detailed,
    DANGEROUS_SQL_KEYWORDS,
    DANGEROUS_SQL_PREFIXES,
)


class TestResult:
    def __init__(self, name: str, passed: bool, message: str, details: Any = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details
    
    def to_dict(self):
        return {
            'name': self.name,
            'passed': self.passed,
            'message': self.message,
            'details': self.details,
        }


class ValidationReport:
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.tests: List[TestResult] = []
        self.passed = 0
        self.failed = 0
    
    def add_test(self, name: str, passed: bool, message: str, details: Any = None):
        test = TestResult(name, passed, message, details)
        self.tests.append(test)
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'summary': {
                'passed': self.passed,
                'failed': self.failed,
                'total': len(self.tests),
                'success': self.failed == 0,
            },
            'tests': [t.to_dict() for t in self.tests],
        }
    
    def print_report(self, verbose: bool = False):
        print("\n" + "=" * 70)
        print("FASE 1B - VALIDACIÓN DE SANITIZACIÓN SQL")
        print("=" * 70)
        print(f"Timestamp: {self.timestamp}")
        print()
        
        for i, test in enumerate(self.tests, 1):
            status = "✅ PASS" if test.passed else "❌ FAIL"
            print(f"{i:2}. {status} | {test.name}")
            print(f"         {test.message}")
            if verbose and test.details:
                print(f"         Detalles: {test.details}")
            print()
        
        print("-" * 70)
        print(f"RESUMEN: {self.passed}/{len(self.tests)} tests pasados")
        if self.failed == 0:
            print("🎉 TODAS LAS VALIDACIONES EXITOSAS")
        else:
            print(f"⛔ {self.failed} TESTS FALLIDOS - REVISAR")
        print("=" * 70)


def run_tests() -> ValidationReport:
    report = ValidationReport()
    
    # ========================================================================
    # TESTS DE PALABRAS CLAVE PERMITIDAS
    # ========================================================================
    
    # 1. SELECT simple permitido
    sql = "SELECT * FROM tabla WHERE id = 1"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="SELECT simple permitido",
        passed=result.is_safe,
        message="SELECT * FROM tabla WHERE id = 1" if result.is_safe else f"Bloqueado: {result.blocked_reason}",
        details=result.to_dict()
    )
    
    # 2. WITH (CTE) permitido
    sql = "WITH cte AS (SELECT 1 AS n) SELECT * FROM cte"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="WITH (CTE) permitido",
        passed=result.is_safe,
        message="CTE permitido" if result.is_safe else f"Bloqueado: {result.blocked_reason}",
    )
    
    # 3. SELECT con JOINs permitido
    sql = "SELECT a.*, b.nombre FROM tabla a INNER JOIN otra b ON a.id = b.id"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="SELECT con JOINs permitido",
        passed=result.is_safe,
        message="JOINs permitidos",
    )
    
    # ========================================================================
    # TESTS DE PALABRAS CLAVE PELIGROSAS
    # ========================================================================
    
    # 4. DELETE bloqueado
    sql = "DELETE FROM tabla WHERE id = 1"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="DELETE bloqueado",
        passed=not result.is_safe and 'DELETE' in str(result.blocked_reason).upper(),
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 5. UPDATE bloqueado
    sql = "UPDATE tabla SET nombre = 'test' WHERE id = 1"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="UPDATE bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 6. INSERT bloqueado
    sql = "INSERT INTO tabla (nombre) VALUES ('test')"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="INSERT bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 7. DROP bloqueado
    sql = "DROP TABLE tabla"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="DROP bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 8. ALTER bloqueado
    sql = "ALTER TABLE tabla ADD columna INT"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="ALTER bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 9. TRUNCATE bloqueado
    sql = "TRUNCATE TABLE tabla"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="TRUNCATE bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 10. EXEC bloqueado
    sql = "EXEC sp_executesql @sql"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="EXEC bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 11. xp_ bloqueado
    sql = "SELECT xp_cmdshell('dir')"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="xp_ (procedimientos sistema) bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 12. sp_ bloqueado
    sql = "SELECT sp_helptext('tabla')"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="sp_ (stored procedures) bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # ========================================================================
    # TESTS DE MÚLTIPLES STATEMENTS Y COMENTARIOS
    # ========================================================================
    
    # 13. Múltiples statements bloqueados
    sql = "SELECT * FROM tabla; DROP TABLE otra"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="Múltiples statements bloqueados",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 14. Comentario -- bloqueado
    sql = "SELECT * FROM tabla -- comentario malicioso"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="Comentario -- bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 15. Comentario /* */ bloqueado
    sql = "SELECT * FROM tabla /* comentario */"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="Comentario /* */ bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 16. Consulta vacía bloqueada
    sql = ""
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="Consulta vacía bloqueada",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 17. Consulta que no inicia con SELECT/WITH bloqueada
    sql = "DECLARE @x INT; SELECT @x"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="DECLARE no permitido (no inicia con SELECT/WITH)",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 18. CREATE bloqueado
    sql = "CREATE TABLE nueva (id INT)"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="CREATE bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # ========================================================================
    # TESTS DE VALIDACIONES ESPECÍFICAS
    # ========================================================================
    
    # 19. Validación para catálogo con parámetros
    sql = "SELECT * FROM ventas WHERE fecha BETWEEN '{fecha_ini}' AND '{fecha_fin}'"
    result = SQLSanitizer.validate_for_catalog(sql)
    report.add_test(
        name="Consulta catálogo con parámetros {param} permitida",
        passed=result.is_safe,
        message="Placeholders detectados" if result.is_safe else f"Bloqueado: {result.blocked_reason}",
        details={'warnings': result.warnings}
    )
    
    # 20. Validación rápida funciona
    is_safe = validate_sql_safe("SELECT * FROM tabla")
    report.add_test(
        name="validate_sql_safe() funciona",
        passed=is_safe == True,
        message="Función helper operativa",
    )
    
    # 21. Validación rápida bloquea DELETE
    is_safe = validate_sql_safe("DELETE FROM tabla")
    report.add_test(
        name="validate_sql_safe() bloquea DELETE",
        passed=is_safe == False,
        message="DELETE correctamente bloqueado por helper",
    )
    
    # 22. Validación detallada retorna objeto completo
    result = validate_sql_detailed("SELECT 1")
    report.add_test(
        name="validate_sql_detailed() retorna objeto completo",
        passed=isinstance(result, SQLValidationResult) and result.is_safe,
        message="Objeto SQLValidationResult retornado",
    )
    
    # ========================================================================
    # TESTS DE CASOS EDGE
    # ========================================================================
    
    # 23. SELECT con subquery permitido
    sql = "SELECT * FROM (SELECT id FROM tabla) t"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="SELECT con subquery permitido",
        passed=result.is_safe,
        message="Subqueries permitidos" if result.is_safe else f"Bloqueado: {result.blocked_reason}",
    )
    
    # 24. UNION permitido
    sql = "SELECT id FROM tabla1 UNION SELECT id FROM tabla2"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="SELECT con UNION permitido",
        passed=result.is_safe,
        message="UNION permitido" if result.is_safe else f"Bloqueado: {result.blocked_reason}",
    )
    
    # 25. MERGE bloqueado
    sql = "MERGE INTO tabla USING otra ON tabla.id = otra.id"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="MERGE bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 26. GRANT bloqueado
    sql = "GRANT SELECT ON tabla TO usuario"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="GRANT bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    # 27. BACKUP bloqueado
    sql = "BACKUP DATABASE test TO DISK = 'test.bak'"
    result = SQLSanitizer.validate(sql)
    report.add_test(
        name="BACKUP bloqueado",
        passed=not result.is_safe,
        message=result.blocked_reason or "ERROR: No fue bloqueado",
    )
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Valida sanitización SQL FASE 1B')
    parser.add_argument('--json', action='store_true', help='Salida JSON')
    parser.add_argument('-v', '--verbose', action='store_true', help='Modo verbose')
    args = parser.parse_args()
    
    try:
        report = run_tests()
        
        if args.json:
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            report.print_report(verbose=args.verbose)
        
        sys.exit(0 if report.failed == 0 else 1)
        
    except Exception as e:
        if args.json:
            print(json.dumps({'error': str(e), 'success': False}))
        else:
            print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
