from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Service de Homologación de Catálogos
=================================================
Gestiona la homologación de Sucursales, Puestos y Departamentos
entre los valores del staging y los catálogos oficiales.

FLUJO:
1. Extraer valores únicos del staging
2. Poblar catálogos oficiales
3. Crear equivalencias (valor_origen → catálogo_id)
4. Actualizar staging con IDs
5. Validar homologación completa antes de aprobar
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pymssql
import unicodedata
import re

logger = logging.getLogger(__name__)

# ============================================================================
# CONEXIÓN
# ============================================================================

def get_hub_connection(server: Dict):
    """Obtiene conexión directa a EDARSA HUB."""
    return pymssql.connect(
        server=server['host'],
        port=server['port'],
        database=server['database'],
        user=server['username'],
        password=server['password'],
        login_timeout=30,
        autocommit=True
    )

def escape_sql(value) -> str:
    """Escapa una cadena para SQL Server."""
    if value is None:
        return ""
    return str(value).replace("'", "''").strip()[:200]

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparación."""
    if not texto:
        return ""
    # Remover acentos
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    # Mayúsculas y trim
    texto = texto.upper().strip()
    # Remover caracteres especiales excepto espacios
    texto = re.sub(r'[^A-Z0-9\s]', '', texto)
    # Normalizar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    return texto


# ============================================================================
# CREAR TABLA DE EQUIVALENCIAS
# ============================================================================

SCRIPT_CREAR_EQUIVALENCIAS = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'RH_Homologacion_Equivalencias')
BEGIN
    CREATE TABLE RH_Homologacion_Equivalencias (
        EquivalenciaID INT IDENTITY(1,1) PRIMARY KEY,
        Tipo VARCHAR(20) NOT NULL,
        Valor_Origen NVARCHAR(200) NOT NULL,
        Valor_Normalizado NVARCHAR(200),
        CatalogoID INT,
        Estado VARCHAR(20) DEFAULT 'Aprobado',
        Usuario_Aprobador VARCHAR(100),
        Fecha_Aprobacion DATETIME DEFAULT GETDATE(),
        Observaciones NVARCHAR(500),
        CONSTRAINT UQ_Tipo_ValorOrigen UNIQUE(Tipo, Valor_Origen)
    );
    PRINT 'Tabla RH_Homologacion_Equivalencias creada';
END
ELSE
BEGIN
    PRINT 'Tabla RH_Homologacion_Equivalencias ya existe';
END
"""

def crear_tabla_equivalencias(server: Dict) -> Dict:
    """Crea la tabla de equivalencias si no existe."""
    conn = get_hub_connection(server)
    cursor = conn.cursor()
    
    try:
        cursor.execute(SCRIPT_CREAR_EQUIVALENCIAS)
        return {'success': True, 'mensaje': 'Tabla de equivalencias verificada/creada'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


# ============================================================================
# POBLAR CATÁLOGOS
# ============================================================================

def poblar_catalogo_sucursales(server: Dict, usuario: str = "Sistema") -> Dict:
    """Pobla RH_Cat_Sucursales con valores únicos del staging."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    resultado = {
        'tipo': 'SUCURSAL',
        'insertados': 0,
        'equivalencias_creadas': 0,
        'detalle': []
    }
    
    try:
        # Obtener valores únicos del staging
        cursor.execute("""
            SELECT DISTINCT Sucursal_Nombre as valor
            FROM RH_Importacion_Staging
            WHERE Fuente = 'MPro_CENTRAL2020' 
              AND Estado != 'Excluido'
              AND Sucursal_Nombre IS NOT NULL 
              AND Sucursal_Nombre != ''
            ORDER BY Sucursal_Nombre
        """)
        valores = cursor.fetchall()
        
        for v in valores:
            valor_origen = v['valor']
            valor_normalizado = normalizar_texto(valor_origen)
            
            # Verificar si ya existe en catálogo
            cursor.execute(f"""
                SELECT SucursalID FROM RH_Cat_Sucursales 
                WHERE UPPER(LTRIM(RTRIM(Nombre_Sucursal))) = '{escape_sql(valor_origen.upper())}'
            """)
            existente = cursor.fetchone()
            
            if existente:
                catalogo_id = existente['SucursalID']
            else:
                # Insertar en catálogo
                cursor.execute(f"""
                    INSERT INTO RH_Cat_Sucursales (Nombre_Sucursal, Ciudad, Activa)
                    OUTPUT INSERTED.SucursalID
                    VALUES (N'{escape_sql(valor_origen)}', 'México', 1)
                """)
                new_id = cursor.fetchone()
                catalogo_id = new_id['SucursalID'] if new_id else None
                resultado['insertados'] += 1
            
            # Crear equivalencia
            if catalogo_id:
                cursor.execute(f"""
                    IF NOT EXISTS (
                        SELECT 1 FROM RH_Homologacion_Equivalencias 
                        WHERE Tipo = 'SUCURSAL' AND Valor_Origen = N'{escape_sql(Valor_Origen)}'
                    )
                    INSERT INTO RH_Homologacion_Equivalencias 
                    (Tipo, Valor_Origen, Valor_Normalizado, CatalogoID, Estado, Usuario_Aprobador)
                    VALUES ('SUCURSAL', N'{escape_sql(Valor_Origen)}', '{Valor_Normalizado}', {catalogo_id}, 'Aprobado', '{escape_sql(usuario)}')
                """)
                resultado['equivalencias_creadas'] += 1
                
            resultado['detalle'].append({
                'valor': valor_origen,
                'catalogo_id': catalogo_id
            })
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error poblando sucursales: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def poblar_catalogo_departamentos(server: Dict, usuario: str = "Sistema") -> Dict:
    """Pobla RH_Cat_Departamentos con valores únicos del staging."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    resultado = {
        'tipo': 'DEPARTAMENTO',
        'insertados': 0,
        'equivalencias_creadas': 0,
        'detalle': []
    }
    
    try:
        cursor.execute("""
            SELECT DISTINCT Area_Departamento as valor
            FROM RH_Importacion_Staging
            WHERE Fuente = 'MPro_CENTRAL2020' 
              AND Estado != 'Excluido'
              AND Area_Departamento IS NOT NULL 
              AND Area_Departamento != ''
            ORDER BY Area_Departamento
        """)
        valores = cursor.fetchall()
        
        for v in valores:
            valor_origen = v['valor']
            valor_normalizado = normalizar_texto(valor_origen)
            
            cursor.execute(f"""
                SELECT DepartamentoID FROM RH_Cat_Departamentos 
                WHERE UPPER(LTRIM(RTRIM(NombreDepartamento))) = '{escape_sql(valor_origen.upper())}'
            """)
            existente = cursor.fetchone()
            
            if existente:
                catalogo_id = existente['DepartamentoID']
            else:
                cursor.execute(f"""
                    INSERT INTO RH_Cat_Departamentos (CodigoDepartamento, NombreDepartamento, Activo)
                    OUTPUT INSERTED.DepartamentoID
                    VALUES ('{valor_normalizado[:20]}', N'{escape_sql(valor_origen)}', 1)
                """)
                new_id = cursor.fetchone()
                catalogo_id = new_id['DepartamentoID'] if new_id else None
                resultado['insertados'] += 1
            
            if catalogo_id:
                cursor.execute(f"""
                    IF NOT EXISTS (
                        SELECT 1 FROM RH_Homologacion_Equivalencias 
                        WHERE Tipo = 'DEPARTAMENTO' AND Valor_Origen = N'{escape_sql(Valor_Origen)}'
                    )
                    INSERT INTO RH_Homologacion_Equivalencias 
                    (Tipo, Valor_Origen, Valor_Normalizado, CatalogoID, Estado, Usuario_Aprobador)
                    VALUES ('DEPARTAMENTO', N'{escape_sql(Valor_Origen)}', '{Valor_Normalizado}', {catalogo_id}, 'Aprobado', '{escape_sql(usuario)}')
                """)
                resultado['equivalencias_creadas'] += 1
                
            resultado['detalle'].append({
                'valor': valor_origen,
                'catalogo_id': catalogo_id
            })
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error poblando departamentos: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def poblar_catalogo_puestos(server: Dict, usuario: str = "Sistema") -> Dict:
    """Pobla RH_Cat_Puestos con valores únicos del staging."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    resultado = {
        'tipo': 'PUESTO',
        'insertados': 0,
        'equivalencias_creadas': 0,
        'detalle': []
    }
    
    try:
        cursor.execute("""
            SELECT DISTINCT Puesto_Nombre as valor
            FROM RH_Importacion_Staging
            WHERE Fuente = 'MPro_CENTRAL2020' 
              AND Estado != 'Excluido'
              AND Puesto_Nombre IS NOT NULL 
              AND Puesto_Nombre != ''
            ORDER BY Puesto_Nombre
        """)
        valores = cursor.fetchall()
        
        for v in valores:
            valor_origen = v['valor']
            valor_normalizado = normalizar_texto(valor_origen)
            
            cursor.execute(f"""
                SELECT PuestoID FROM RH_Cat_Puestos 
                WHERE UPPER(LTRIM(RTRIM(Descripcion))) = '{escape_sql(valor_origen.upper())}'
            """)
            existente = cursor.fetchone()
            
            if existente:
                catalogo_id = existente['PuestoID']
            else:
                cursor.execute(f"""
                    INSERT INTO RH_Cat_Puestos (CodigoPuesto, Descripcion, Activo)
                    OUTPUT INSERTED.PuestoID
                    VALUES ('{valor_normalizado[:20]}', N'{escape_sql(valor_origen)}', 1)
                """)
                new_id = cursor.fetchone()
                catalogo_id = new_id['PuestoID'] if new_id else None
                resultado['insertados'] += 1
            
            if catalogo_id:
                cursor.execute(f"""
                    IF NOT EXISTS (
                        SELECT 1 FROM RH_Homologacion_Equivalencias 
                        WHERE Tipo = 'PUESTO' AND Valor_Origen = N'{escape_sql(Valor_Origen)}'
                    )
                    INSERT INTO RH_Homologacion_Equivalencias 
                    (Tipo, Valor_Origen, Valor_Normalizado, CatalogoID, Estado, Usuario_Aprobador)
                    VALUES ('PUESTO', N'{escape_sql(Valor_Origen)}', '{Valor_Normalizado}', {catalogo_id}, 'Aprobado', '{escape_sql(usuario)}')
                """)
                resultado['equivalencias_creadas'] += 1
                
            resultado['detalle'].append({
                'valor': valor_origen,
                'catalogo_id': catalogo_id
            })
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error poblando puestos: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


# ============================================================================
# ACTUALIZAR STAGING CON IDs
# ============================================================================

def actualizar_staging_con_ids(server: Dict) -> Dict:
    """Actualiza los campos SucursalID y PuestoID en staging según equivalencias."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    resultado = {
        'sucursales_actualizadas': 0,
        'puestos_actualizados': 0,
        'sin_homologar': 0
    }
    
    try:
        # Actualizar SucursalID
        cursor.execute("""
            UPDATE s
            SET s.SucursalID = e.CatalogoID
            FROM RH_Importacion_Staging s
            INNER JOIN RH_Homologacion_Equivalencias e 
                ON e.Tipo = 'SUCURSAL' 
                AND e.Valor_Origen = s.Sucursal_Nombre
                AND e.Estado = 'Aprobado'
            WHERE s.Fuente = 'MPro_CENTRAL2020'
              AND s.Estado != 'Excluido'
              AND (s.SucursalID IS NULL OR s.SucursalID = 0)
        """)
        resultado['sucursales_actualizadas'] = cursor.rowcount
        
        # Actualizar PuestoID
        cursor.execute("""
            UPDATE s
            SET s.PuestoID = e.CatalogoID
            FROM RH_Importacion_Staging s
            INNER JOIN RH_Homologacion_Equivalencias e 
                ON e.Tipo = 'PUESTO' 
                AND e.Valor_Origen = s.Puesto_Nombre
                AND e.Estado = 'Aprobado'
            WHERE s.Fuente = 'MPro_CENTRAL2020'
              AND s.Estado != 'Excluido'
              AND (s.PuestoID IS NULL OR s.PuestoID = 0)
        """)
        resultado['puestos_actualizados'] = cursor.rowcount
        
        # Contar sin homologar
        cursor.execute("""
            SELECT COUNT(*) as cantidad
            FROM RH_Importacion_Staging
            WHERE Fuente = 'MPro_CENTRAL2020'
              AND Estado NOT IN ('Excluido', 'Procesado')
              AND (SucursalID IS NULL OR SucursalID = 0 OR PuestoID IS NULL OR PuestoID = 0)
        """)
        resultado['sin_homologar'] = cursor.fetchone()['cantidad']
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error actualizando staging: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


# ============================================================================
# CONSULTAS DE HOMOLOGACIÓN
# ============================================================================

def obtener_equivalencias(server: Dict, tipo: Optional[str] = None) -> List[Dict]:
    """Obtiene las equivalencias registradas."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    try:
        where_tipo = f"WHERE Tipo = '{tipo}'" if tipo else ""
        cursor.execute(f"""
            SELECT 
                EquivalenciaID,
                Tipo,
                Valor_Origen,
                Valor_Normalizado,
                CatalogoID,
                Estado,
                Usuario_Aprobador,
                Fecha_Aprobacion,
                Observaciones
            FROM RH_Homologacion_Equivalencias
            {where_tipo}
            ORDER BY Tipo, Valor_Origen
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error obteniendo equivalencias: {e}")
        return []
    finally:
        conn.close()


def obtener_estadisticas_homologacion(server: Dict) -> Dict:
    """Obtiene estadísticas del estado de homologación."""
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    stats = {
        'catalogos': {},
        'equivalencias': {},
        'staging': {}
    }
    
    try:
        # Catálogos poblados
        cursor.execute("SELECT COUNT(*) as total FROM RH_Cat_Sucursales")
        stats['catalogos']['sucursales'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM RH_Cat_Puestos")
        stats['catalogos']['puestos'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM RH_Cat_Departamentos")
        stats['catalogos']['departamentos'] = cursor.fetchone()['total']
        
        # Equivalencias por tipo
        cursor.execute("""
            SELECT Tipo, Estado, COUNT(*) as cantidad
            FROM RH_Homologacion_Equivalencias
            GROUP BY Tipo, Estado
        """)
        for r in cursor.fetchall():
            key = f"{r['Tipo']}_{r['Estado']}"
            stats['equivalencias'][key] = r['cantidad']
        
        # Staging homologado
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN SucursalID IS NOT NULL AND SucursalID > 0 THEN 1 ELSE 0 END) as con_sucursal,
                SUM(CASE WHEN PuestoID IS NOT NULL AND PuestoID > 0 THEN 1 ELSE 0 END) as con_puesto
            FROM RH_Importacion_Staging
            WHERE Fuente = 'MPro_CENTRAL2020'
              AND Estado NOT IN ('Excluido', 'Procesado')
              AND Clasificacion = 'nuevo'
        """)
        staging = cursor.fetchone()
        stats['staging'] = {
            'total_candidatos': staging['total'],
            'con_sucursal_id': staging['con_sucursal'],
            'con_puesto_id': staging['con_puesto'],
            'completamente_homologados': min(staging['con_sucursal'], staging['con_puesto']),
            'pendientes_homologacion': staging['total'] - min(staging['con_sucursal'], staging['con_puesto'])
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return stats
    finally:
        conn.close()


def verificar_homologacion_completa(server: Dict) -> Tuple[bool, str, int]:
    """
    Verifica si todos los candidatos están homologados.
    Retorna (esta_completa, mensaje, pendientes).
    """
    conn = get_hub_connection(server)
    cursor = conn.cursor(as_dict=True)
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as pendientes
            FROM RH_Importacion_Staging
            WHERE Fuente = 'MPro_CENTRAL2020'
              AND Estado = 'Pendiente'
              AND Clasificacion = 'nuevo'
              AND (SucursalID IS NULL OR SucursalID = 0 OR PuestoID IS NULL OR PuestoID = 0)
        """)
        pendientes = cursor.fetchone()['pendientes']
        
        if pendientes == 0:
            return True, "Todos los candidatos están homologados", 0
        else:
            return False, f"{pendientes} registros pendientes de homologación", pendientes
            
    except Exception as e:
        return False, f"Error verificando: {str(e)}", -1
    finally:
        conn.close()


# ============================================================================
# EJECUTAR HOMOLOGACIÓN COMPLETA
# ============================================================================

def ejecutar_homologacion_completa(server: Dict, usuario: str = "Sistema") -> Dict:
    """
    Ejecuta el proceso completo de homologación:
    1. Crear tabla de equivalencias
    2. Poblar catálogos
    3. Actualizar staging con IDs
    """
    resultado = {
        'success': True,
        'pasos': [],
        'resumen': {}
    }
    
    try:
        # Paso 1: Crear tabla de equivalencias
        r1 = crear_tabla_equivalencias(server)
        resultado['pasos'].append({'paso': 'Crear tabla equivalencias', 'resultado': r1})
        
        # Paso 2: Poblar sucursales
        r2 = poblar_catalogo_sucursales(server, usuario)
        resultado['pasos'].append({'paso': 'Poblar sucursales', 'resultado': r2})
        
        # Paso 3: Poblar departamentos
        r3 = poblar_catalogo_departamentos(server, usuario)
        resultado['pasos'].append({'paso': 'Poblar departamentos', 'resultado': r3})
        
        # Paso 4: Poblar puestos
        r4 = poblar_catalogo_puestos(server, usuario)
        resultado['pasos'].append({'paso': 'Poblar puestos', 'resultado': r4})
        
        # Paso 5: Actualizar staging
        r5 = actualizar_staging_con_ids(server)
        resultado['pasos'].append({'paso': 'Actualizar staging', 'resultado': r5})
        
        # Paso 6: Verificar completitud
        completa, mensaje, pendientes = verificar_homologacion_completa(server)
        resultado['pasos'].append({'paso': 'Verificar homologación', 'resultado': {
            'completa': completa,
            'mensaje': mensaje,
            'pendientes': pendientes
        }})
        
        # Resumen
        resultado['resumen'] = {
            'sucursales_creadas': r2.get('insertados', 0),
            'departamentos_creados': r3.get('insertados', 0),
            'puestos_creados': r4.get('insertados', 0),
            'staging_actualizado': r5.get('sucursales_actualizadas', 0) + r5.get('puestos_actualizados', 0),
            'homologacion_completa': completa,
            'pendientes': pendientes
        }
        
        return resultado
        
    except Exception as e:
        resultado['success'] = False
        resultado['error'] = str(e)
        return resultado
