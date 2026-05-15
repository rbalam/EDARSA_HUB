#!/usr/bin/env python3
"""
EDARSA HUB - Script de Validación: Consultas SQL Repository
===========================================================
FASE 3: Valida el módulo consultas_sql contra EDARSAHUB.

PROPÓSITO:
1. Conectarse a EDARSAHUB SQL usando configuración existente
2. Listar y contar consultas
3. Validar conteos esperados (20 consultas, 38 parámetros)
4. Validar cada ConsultaSQL con validator.py
5. Confirmar integridad del catálogo
6. NO ejecutar consultas contra servidores LIVE
7. NO escribir datos

USO:
    python validate_consultas_sql_repository.py
    
    # Con salida JSON
    python validate_consultas_sql_repository.py --json
    
    # Verbose
    python validate_consultas_sql_repository.py -v

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

from modules.consultas_sql import (
    ConsultasSQLRepository,
    ConsultasSQLService,
    SQLValidator,
    ConsultaSQLFilter,
)


class ValidationReport:
    """Genera reporte de validación."""
    
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.checks: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.summary: Dict[str, Any] = {}
    
    def add_check(self, name: str, passed: bool, message: str, details: Any = None):
        """Agrega un check al reporte."""
        check = {
            'name': name,
            'passed': passed,
            'message': message,
            'details': details,
        }
        self.checks.append(check)
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def add_warning(self, name: str, message: str, details: Any = None):
        """Agrega un warning al reporte."""
        self.warnings += 1
        self.checks.append({
            'name': name,
            'passed': True,
            'warning': True,
            'message': message,
            'details': details,
        })
    
    def add_error(self, error: str, context: str = None):
        """Agrega un error fatal."""
        self.errors.append({
            'error': error,
            'context': context,
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'timestamp': self.timestamp,
            'summary': {
                'passed': self.passed,
                'failed': self.failed,
                'warnings': self.warnings,
                'total_checks': len(self.checks),
                'success': self.failed == 0 and len(self.errors) == 0,
            },
            'checks': self.checks,
            'errors': self.errors,
        }
    
    def print_report(self, verbose: bool = False):
        """Imprime el reporte."""
        print("\n" + "=" * 70)
        print("REPORTE DE VALIDACIÓN - CONSULTAS SQL REPOSITORY")
        print("=" * 70)
        print(f"Timestamp: {self.timestamp}")
        print()
        
        # Checks
        for check in self.checks:
            status = "✅ PASS" if check['passed'] else "❌ FAIL"
            if check.get('warning'):
                status = "⚠️ WARN"
            
            print(f"{status} | {check['name']}")
            print(f"       {check['message']}")
            
            if verbose and check.get('details'):
                print(f"       Detalles: {json.dumps(check['details'], indent=8, ensure_ascii=False)[:500]}")
            print()
        
        # Errores
        if self.errors:
            print("\n❌ ERRORES FATALES:")
            for err in self.errors:
                print(f"   - {err['error']}")
                if err.get('context'):
                    print(f"     Contexto: {err['context']}")
        
        # Resumen
        print("\n" + "-" * 70)
        print("RESUMEN:")
        print(f"   Checks pasados:  {self.passed}")
        print(f"   Checks fallidos: {self.failed}")
        print(f"   Warnings:        {self.warnings}")
        print(f"   Total checks:    {len(self.checks)}")
        print()
        
        if self.failed == 0 and len(self.errors) == 0:
            print("🎉 VALIDACIÓN EXITOSA - Catálogo SQL-First operativo")
        else:
            print("⛔ VALIDACIÓN FALLIDA - Revisar errores arriba")
        
        print("=" * 70)


def run_validation(verbose: bool = False) -> ValidationReport:
    """Ejecuta la validación completa."""
    report = ValidationReport()
    
    print("Iniciando validación del módulo consultas_sql...")
    print()
    
    # ========================================================================
    # 1. CONEXIÓN Y REPOSITORY
    # ========================================================================
    try:
        repo = ConsultasSQLRepository()
        report.add_check(
            name="Repository instanciado",
            passed=True,
            message="ConsultasSQLRepository creado correctamente"
        )
    except Exception as e:
        report.add_error(f"Error creando repository: {e}", "Inicialización")
        return report
    
    # ========================================================================
    # 2. CONTEOS BÁSICOS
    # ========================================================================
    try:
        counts = repo.get_counts()
        report.add_check(
            name="Conteos obtenidos",
            passed=len(counts) > 0,
            message=f"Obtenidos {len(counts)} métricas de conteo",
            details=counts
        )
        
        # Validar 20 consultas
        total_consultas = counts.get('total_consultas', 0)
        report.add_check(
            name="Total consultas = 20",
            passed=total_consultas == 20,
            message=f"Encontradas {total_consultas} consultas (esperadas: 20)",
            details={'actual': total_consultas, 'expected': 20}
        )
        
        # Validar 38 parámetros
        total_parametros = counts.get('total_parametros', 0)
        report.add_check(
            name="Total parámetros = 38",
            passed=total_parametros == 38,
            message=f"Encontrados {total_parametros} parámetros (esperados: 38)",
            details={'actual': total_parametros, 'expected': 38}
        )
        
        # Validar SoftRestaurant = 14
        sr_count = counts.get('consultas_softrestaurant', 0)
        report.add_check(
            name="Consultas SoftRestaurant = 14",
            passed=sr_count == 14,
            message=f"Encontradas {sr_count} consultas SoftRestaurant (esperadas: 14)",
            details={'actual': sr_count, 'expected': 14}
        )
        
        # Validar MPRO = 6
        mpro_count = counts.get('consultas_mpro', 0)
        report.add_check(
            name="Consultas MPRO = 6",
            passed=mpro_count == 6,
            message=f"Encontradas {mpro_count} consultas MPRO (esperadas: 6)",
            details={'actual': mpro_count, 'expected': 6}
        )
        
        # Todas SoloLectura
        solo_lectura = counts.get('consultas_solo_lectura', 0)
        report.add_check(
            name="Todas SoloLectura = 1",
            passed=solo_lectura == total_consultas,
            message=f"{solo_lectura}/{total_consultas} consultas son SoloLectura",
            details={'solo_lectura': solo_lectura, 'total': total_consultas}
        )
        
    except Exception as e:
        report.add_error(f"Error obteniendo conteos: {e}", "Conteos")
    
    # ========================================================================
    # 3. LISTAR CONSULTAS
    # ========================================================================
    try:
        consultas = repo.list_consultas(ConsultaSQLFilter(limit=100))
        report.add_check(
            name="Listar consultas",
            passed=len(consultas) > 0,
            message=f"Listadas {len(consultas)} consultas del catálogo"
        )
        
        # Verificar no duplicados
        codigos = [c.codigo_consulta for c in consultas]
        codigos_unicos = set(codigos)
        report.add_check(
            name="Sin duplicados",
            passed=len(codigos) == len(codigos_unicos),
            message=f"{len(codigos_unicos)} códigos únicos de {len(codigos)} totales"
        )
        
        # Verificar ninguno con SQL NULL
        sql_vacios = [c for c in consultas if not c.consulta_sql or not c.consulta_sql.strip()]
        report.add_check(
            name="Sin SQL NULL/vacío",
            passed=len(sql_vacios) == 0,
            message=f"{len(sql_vacios)} consultas con SQL vacío",
            details=[c.codigo_consulta for c in sql_vacios] if sql_vacios else None
        )
        
    except Exception as e:
        report.add_error(f"Error listando consultas: {e}", "Listado")
        consultas = []
    
    # ========================================================================
    # 4. VALIDAR CADA CONSULTA
    # ========================================================================
    consultas_validas = 0
    consultas_con_warnings = 0
    consultas_invalidas = []
    
    validator = SQLValidator()
    
    for consulta in consultas:
        try:
            validation = repo.validate_catalog_query(consulta.consulta_id)
            
            if validation.is_valid:
                consultas_validas += 1
                if validation.warnings:
                    consultas_con_warnings += 1
            else:
                consultas_invalidas.append({
                    'codigo': consulta.codigo_consulta,
                    'nombre': consulta.nombre_consulta,
                    'errors': validation.errors,
                })
        except Exception as e:
            consultas_invalidas.append({
                'codigo': consulta.codigo_consulta,
                'error': str(e),
            })
    
    report.add_check(
        name="Validación de seguridad SQL",
        passed=len(consultas_invalidas) == 0,
        message=f"{consultas_validas}/{len(consultas)} consultas pasan validación de seguridad",
        details={
            'validas': consultas_validas,
            'con_warnings': consultas_con_warnings,
            'invalidas': consultas_invalidas if consultas_invalidas else None
        }
    )
    
    if consultas_invalidas:
        for inv in consultas_invalidas:
            report.add_warning(
                name=f"Consulta inválida: {inv['codigo']}",
                message=str(inv.get('errors', inv.get('error', 'Error desconocido'))),
                details=inv
            )
    
    # ========================================================================
    # 5. VERIFICAR MÓDULOS
    # ========================================================================
    try:
        modulos = repo.get_modulos()
        report.add_check(
            name="Módulos obtenidos",
            passed=len(modulos) > 0,
            message=f"Encontrados {len(modulos)} módulos: {', '.join(modulos)}",
            details=modulos
        )
    except Exception as e:
        report.add_error(f"Error obteniendo módulos: {e}", "Módulos")
    
    # ========================================================================
    # 6. VERIFICAR SERVICE
    # ========================================================================
    try:
        service = ConsultasSQLService()
        stats = service.obtener_estadisticas()
        report.add_check(
            name="Service instanciado",
            passed='conteos' in stats,
            message="ConsultasSQLService operativo",
            details=stats
        )
        
        # Integridad
        integridad = service.verificar_integridad()
        report.add_check(
            name="Integridad del catálogo",
            passed=not integridad.get('has_critical', False),
            message=f"{integridad.get('total_issues', 0)} issues encontrados",
            details=integridad.get('issues') if integridad.get('issues') else None
        )
        
    except Exception as e:
        report.add_error(f"Error con service: {e}", "Service")
    
    # ========================================================================
    # 7. VERIFICAR PARÁMETROS POR CONSULTA
    # ========================================================================
    try:
        consultas_con_params = 0
        for consulta in consultas[:5]:  # Solo primeras 5 para no sobrecargar
            params = repo.get_parametros(consulta.consulta_id)
            if params:
                consultas_con_params += 1
        
        report.add_check(
            name="Parámetros por consulta",
            passed=consultas_con_params > 0,
            message=f"{consultas_con_params}/5 consultas verificadas tienen parámetros"
        )
    except Exception as e:
        report.add_warning(
            name="Verificación de parámetros",
            message=f"Error parcial: {e}"
        )
    
    # ========================================================================
    # 8. VERIFICAR VALIDADOR DIRECTO
    # ========================================================================
    try:
        # Test SQL válido
        valid_result = validator.validate_sql_text("SELECT * FROM tabla WHERE id = 1")
        report.add_check(
            name="Validador: SELECT simple",
            passed=valid_result.is_valid,
            message="SELECT simple pasa validación"
        )
        
        # Test SQL inválido (DELETE)
        invalid_result = validator.validate_sql_text("DELETE FROM tabla WHERE id = 1")
        report.add_check(
            name="Validador: DELETE bloqueado",
            passed=not invalid_result.is_valid,
            message="DELETE correctamente bloqueado"
        )
        
        # Test SQL con xp_
        xp_result = validator.validate_sql_text("SELECT xp_cmdshell('dir')")
        report.add_check(
            name="Validador: xp_ bloqueado",
            passed=not xp_result.is_valid,
            message="xp_ correctamente bloqueado"
        )
        
    except Exception as e:
        report.add_error(f"Error en validador: {e}", "Validador")
    
    return report


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Valida el módulo consultas_sql contra EDARSAHUB'
    )
    parser.add_argument('--json', action='store_true', help='Salida en formato JSON')
    parser.add_argument('-v', '--verbose', action='store_true', help='Modo verbose')
    args = parser.parse_args()
    
    try:
        report = run_validation(verbose=args.verbose)
        
        if args.json:
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            report.print_report(verbose=args.verbose)
        
        # Exit code
        sys.exit(0 if report.failed == 0 and len(report.errors) == 0 else 1)
        
    except Exception as e:
        if args.json:
            print(json.dumps({'error': str(e), 'success': False}, indent=2))
        else:
            print(f"\n❌ ERROR FATAL: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
