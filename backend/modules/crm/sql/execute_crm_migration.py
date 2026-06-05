#!/usr/bin/env python3
"""
EDARSA HUB - CRM Enterprise Migration Executor
Ejecuta los scripts SQL de creación de tablas CRM en EDARSAHUB
"""
import os
import sys
import pymssql
from datetime import datetime
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}

def execute_sql_script(script_path: str, description: str) -> dict:
    """Ejecuta un script SQL y retorna el resultado"""
    print(f"\n{'='*60}")
    print(f"EJECUTANDO: {description}")
    print(f"Archivo: {script_path}")
    print(f"Fecha: {datetime.now().isoformat()}")
    print('='*60)
    
    # Leer el script
    with open(script_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Separar por GO (SQL Server batch separator)
    # Nota: pymssql no soporta GO, hay que ejecutar cada batch por separado
    batches = []
    current_batch = []
    
    for line in sql_content.split('\n'):
        stripped = line.strip().upper()
        if stripped == 'GO':
            if current_batch:
                batches.append('\n'.join(current_batch))
                current_batch = []
        else:
            current_batch.append(line)
    
    # Agregar último batch si no termina en GO
    if current_batch:
        full_batch = '\n'.join(current_batch).strip()
        if full_batch:
            batches.append(full_batch)
    
    # Si no hay GOs, ejecutar todo como un solo batch
    if not batches:
        batches = [sql_content]
    
    results = {
        'script': script_path,
        'description': description,
        'batches_total': len(batches),
        'batches_success': 0,
        'batches_failed': 0,
        'messages': [],
        'errors': [],
        'success': False
    }
    
    try:
        conn = pymssql.connect(
            server=EDARSAHUB_CONFIG['host'],
            port=EDARSAHUB_CONFIG['port'],
            database=EDARSAHUB_CONFIG['database'],
            user=EDARSAHUB_CONFIG['username'],
            password=EDARSAHUB_CONFIG['password'],
            login_timeout=30,
            timeout=120,
            autocommit=True  # Importante para DDL
        )
        cursor = conn.cursor()
        
        print(f"\n✅ Conectado a EDARSAHUB ({EDARSAHUB_CONFIG['host']})")
        print(f"📦 Ejecutando {len(batches)} batches...\n")
        
        for i, batch in enumerate(batches, 1):
            batch_clean = batch.strip()
            if not batch_clean or batch_clean.startswith('--'):
                continue
                
            try:
                cursor.execute(batch_clean)
                results['batches_success'] += 1
                
                # Capturar PRINTs si los hay
                # Nota: pymssql no captura PRINT directamente, pero podemos inferir éxito
                if 'CREATE TABLE' in batch_clean.upper():
                    table_match = batch_clean.upper().find('CREATE TABLE')
                    results['messages'].append(f"Batch {i}: CREATE TABLE ejecutado")
                elif 'ALTER TABLE' in batch_clean.upper():
                    results['messages'].append(f"Batch {i}: ALTER TABLE ejecutado")
                elif 'INSERT INTO' in batch_clean.upper():
                    results['messages'].append(f"Batch {i}: INSERT ejecutado")
                elif 'CREATE INDEX' in batch_clean.upper():
                    results['messages'].append(f"Batch {i}: CREATE INDEX ejecutado")
                    
            except Exception as batch_error:
                error_str = str(batch_error)
                # Ignorar errores de "ya existe" (idempotencia)
                if 'already exists' in error_str.lower() or 'there is already' in error_str.lower():
                    results['messages'].append(f"Batch {i}: Objeto ya existe (OK - idempotente)")
                    results['batches_success'] += 1
                else:
                    results['batches_failed'] += 1
                    results['errors'].append(f"Batch {i}: {error_str[:200]}")
                    print(f"❌ Error en batch {i}: {error_str[:100]}")
        
        cursor.close()
        conn.close()
        
        results['success'] = results['batches_failed'] == 0
        
    except Exception as conn_error:
        results['errors'].append(f"Error de conexión: {str(conn_error)}")
        print(f"❌ Error de conexión: {conn_error}")
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"RESUMEN: {description}")
    print(f"  - Batches totales: {results['batches_total']}")
    print(f"  - Exitosos: {results['batches_success']}")
    print(f"  - Fallidos: {results['batches_failed']}")
    print(f"  - Estado: {'✅ ÉXITO' if results['success'] else '❌ CON ERRORES'}")
    print('='*60)
    
    return results


def validate_tables_created() -> dict:
    """Valida que las tablas CRM se crearon correctamente"""
    print(f"\n{'='*60}")
    print("VALIDACIÓN: Verificando tablas CRM creadas")
    print('='*60)
    
    expected_tables = [
        'CRM_Leads',
        'CRM_Oportunidades',
        'CRM_Propuestas',
        'CRM_Contratos',
        'CRM_Config_Pipelines',
        'CRM_Config_PipelineEtapas',
        'CRM_Oportunidad_Contactos',
        'CRM_Oportunidad_Documentos',
        'CRM_Oportunidades_HistorialEtapas',
        'CRM_Cat_OrigenLead',
        'CRM_Cat_EstatusLead',
        'CRM_Cat_EstatusOportunidad',
        'CRM_Cat_MotivosPerdida',
        'CRM_Cat_MotivosGanada',
        'CRM_Cat_Prioridades',
        'CRM_Cat_Sectores',
        'CRM_Cat_TamanosCliente',
        'CRM_Cat_TiposPipeline',
        'CRM_Cat_EstatusPropuesta',
        'CRM_Cat_EstatusContrato'
    ]
    
    try:
        conn = pymssql.connect(
            server=EDARSAHUB_CONFIG['host'],
            port=EDARSAHUB_CONFIG['port'],
            database=EDARSAHUB_CONFIG['database'],
            user=EDARSAHUB_CONFIG['username'],
            password=EDARSAHUB_CONFIG['password'],
            login_timeout=30,
            timeout=60
        )
        cursor = conn.cursor(as_dict=True)
        
        # Verificar tablas
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_NAME LIKE 'CRM_%'
            ORDER BY TABLE_NAME
        """)
        existing_tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
        
        # Verificar columnas agregadas a Cliente_Catalogo
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Cliente_Catalogo'
            AND COLUMN_NAME IN (
                'EjecutivoPrincipalUserID', 'GerenteComercialUserID', 
                'CustomerSuccessUserID', 'SectorID', 'SubsectorID',
                'TamanoClienteID', 'RiesgoCuentaID', 'EsProspecto',
                'EsPartner', 'EsCuentaEstrategica', 'FechaUltimaInteraccion',
                'ScoreCuenta', 'OrigenCuentaID'
            )
        """)
        crm_columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        
        # Verificar datos seed en catálogos
        catalog_counts = {}
        for cat in ['CRM_Cat_OrigenLead', 'CRM_Cat_EstatusLead', 'CRM_Cat_Prioridades']:
            if cat in existing_tables:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {cat}")
                result = cursor.fetchone()
                catalog_counts[cat] = result['cnt'] if result else 0
        
        # Verificar Pipeline Default
        pipeline_info = None
        if 'CRM_Config_Pipelines' in existing_tables:
            cursor.execute("""
                SELECT p.Nombre as Pipeline, COUNT(e.EtapaID) as Etapas
                FROM CRM_Config_Pipelines p
                LEFT JOIN CRM_Config_PipelineEtapas e ON p.PipelineID = e.PipelineID
                WHERE p.Codigo = 'VENTAS_DEFAULT'
                GROUP BY p.Nombre
            """)
            result = cursor.fetchone()
            if result:
                pipeline_info = f"{result['Pipeline']} ({result['Etapas']} etapas)"
        
        cursor.close()
        conn.close()
        
        # Reporte
        print(f"\n📊 TABLAS CRM ENCONTRADAS ({len(existing_tables)}):")
        for t in existing_tables:
            status = "✅" if t in expected_tables else "🆕"
            print(f"   {status} {t}")
        
        missing = set(expected_tables) - set(existing_tables)
        if missing:
            print(f"\n⚠️ TABLAS FALTANTES ({len(missing)}):")
            for t in missing:
                print(f"   ❌ {t}")
        
        print(f"\n📊 COLUMNAS CRM EN Cliente_Catalogo ({len(crm_columns)}/13):")
        for c in crm_columns:
            print(f"   ✅ {c}")
        
        print(f"\n📊 DATOS SEED EN CATÁLOGOS:")
        for cat, count in catalog_counts.items():
            print(f"   {cat}: {count} registros")
        
        if pipeline_info:
            print(f"\n📊 PIPELINE DEFAULT: {pipeline_info}")
        
        return {
            'tables_found': len(existing_tables),
            'tables_expected': len(expected_tables),
            'tables_missing': list(missing),
            'crm_columns_added': len(crm_columns),
            'catalog_counts': catalog_counts,
            'pipeline_default': pipeline_info,
            'success': len(missing) == 0
        }
        
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    print("\n" + "="*70)
    print("  EDARSA HUB - CRM ENTERPRISE - MIGRACIÓN DE BASE DE DATOS")
    print("  Fecha: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)
    
    # Script 1: Tablas principales
    result1 = execute_sql_script(
        os.path.join(base_path, '01_create_crm_tables.sql'),
        "Script 01: Tablas Principales CRM"
    )
    
    # Script 2: Catálogos
    result2 = execute_sql_script(
        os.path.join(base_path, '02_seed_crm_catalogs.sql'),
        "Script 02: Catálogos CRM"
    )
    
    # Validación final
    validation = validate_tables_created()
    
    # Resumen final
    print("\n" + "="*70)
    print("  RESUMEN FINAL DE MIGRACIÓN CRM")
    print("="*70)
    print(f"  Script 01 (Tablas): {'✅ OK' if result1['success'] else '❌ ERRORES'}")
    print(f"  Script 02 (Catálogos): {'✅ OK' if result2['success'] else '❌ ERRORES'}")
    print(f"  Validación: {'✅ OK' if validation.get('success') else '⚠️ REVISAR'}")
    print("="*70)
    
    # Exit code
    sys.exit(0 if (result1['success'] and result2['success']) else 1)
