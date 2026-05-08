"""
EDARSA HUB - Catálogos Repository
=================================
Acceso a datos para el módulo de catálogos.
Ejecuta queries dinámicos contra SQL Server (EDARSA HUB).
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.db import execute_sql_query
from modules.catalogos.schemas import ESTRUCTURA_TABLAS

logger = logging.getLogger(__name__)


# ID del servidor EDARSA HUB
EDARSA_HUB_SERVER_ID = "bea40259-35f1-4693-bda2-d2d10e13e56a"


def escape_sql_string(value: str) -> str:
    """Escapa caracteres peligrosos para SQL."""
    if value is None:
        return "NULL"
    return str(value).replace("'", "''")


async def get_edarsa_hub_connection(db) -> Dict:
    """Obtiene las credenciales del servidor EDARSA HUB desde MongoDB."""
    server = await db.servers.find_one({"id": EDARSA_HUB_SERVER_ID, "active": True})
    if not server:
        raise Exception("Servidor EDARSA HUB no configurado")
    return server


def execute_edarsa_query(server: Dict, query: str) -> List[Dict]:
    """Ejecuta una query en EDARSA HUB."""
    return execute_sql_query(
        server['host'],
        server['port'],
        server['database'],
        server['username'],
        server['password'],
        query
    )


# ============================================================================
# DDL - SCRIPTS PARA CREAR TABLAS NUEVAS
# ============================================================================

DDL_TABLAS_NUEVAS = """
-- ============================================================================
-- CATÁLOGOS GLOBALES - EDARSA HUB
-- Creados por Módulo Maestro de Catálogos - Diciembre 2025
-- ============================================================================

-- 1. EMPRESAS
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_Empresas')
BEGIN
    CREATE TABLE Global_Cat_Empresas (
        EmpresaID INT IDENTITY(1,1) PRIMARY KEY,
        CodigoEmpresa VARCHAR(20) NOT NULL UNIQUE,
        RazonSocial VARCHAR(200) NOT NULL,
        NombreComercial VARCHAR(150) NULL,
        RFC VARCHAR(13) NULL,
        RegimenFiscalID INT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaAlta DATETIME2 NOT NULL DEFAULT GETDATE(),
        FechaModificacion DATETIME2 NULL
    );
    PRINT 'Tabla Global_Cat_Empresas creada';
END;

-- 2. BANCOS
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_Bancos')
BEGIN
    CREATE TABLE Global_Cat_Bancos (
        BancoID INT IDENTITY(1,1) PRIMARY KEY,
        CodigoBanco VARCHAR(10) NOT NULL UNIQUE,
        NombreBanco VARCHAR(100) NOT NULL,
        NombreCorto VARCHAR(50) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaAlta DATETIME2 NOT NULL DEFAULT GETDATE()
    );
    PRINT 'Tabla Global_Cat_Bancos creada';
    
    -- Datos iniciales de bancos mexicanos
    INSERT INTO Global_Cat_Bancos (CodigoBanco, NombreBanco, NombreCorto) VALUES
    ('002', 'BANAMEX', 'BANAMEX'),
    ('012', 'BBVA BANCOMER', 'BBVA'),
    ('014', 'SANTANDER', 'SANTANDER'),
    ('021', 'HSBC', 'HSBC'),
    ('030', 'BAJIO', 'BAJIO'),
    ('036', 'INBURSA', 'INBURSA'),
    ('044', 'SCOTIABANK', 'SCOTIABANK'),
    ('058', 'BANREGIO', 'BANREGIO'),
    ('072', 'BANORTE', 'BANORTE'),
    ('127', 'AZTECA', 'AZTECA'),
    ('137', 'BANCOPPEL', 'BANCOPPEL');
END;

-- 3. UNIDADES DE MEDIDA
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_UnidadesMedida')
BEGIN
    CREATE TABLE Global_Cat_UnidadesMedida (
        UnidadMedidaID INT IDENTITY(1,1) PRIMARY KEY,
        ClaveSAT VARCHAR(10) NOT NULL UNIQUE,
        Nombre VARCHAR(50) NOT NULL,
        Descripcion VARCHAR(150) NULL,
        Activo BIT NOT NULL DEFAULT 1
    );
    PRINT 'Tabla Global_Cat_UnidadesMedida creada';
    
    -- Datos iniciales
    INSERT INTO Global_Cat_UnidadesMedida (ClaveSAT, Nombre, Descripcion) VALUES
    ('H87', 'Pieza', 'Unidad'),
    ('KGM', 'Kilogramo', 'Kilogramo'),
    ('LTR', 'Litro', 'Litro'),
    ('MTR', 'Metro', 'Metro'),
    ('E48', 'Servicio', 'Unidad de servicio'),
    ('ACT', 'Actividad', 'Unidad de actividad'),
    ('XBX', 'Caja', 'Caja'),
    ('XPK', 'Paquete', 'Paquete');
END;

-- 4. CENTROS DE COSTO
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_CentrosCosto')
BEGIN
    CREATE TABLE Global_Cat_CentrosCosto (
        CentroCostoID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo VARCHAR(20) NOT NULL,
        Nombre VARCHAR(100) NOT NULL,
        Descripcion VARCHAR(250) NULL,
        EmpresaID INT NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaAlta DATETIME2 NOT NULL DEFAULT GETDATE(),
        CONSTRAINT UQ_CentroCosto_Codigo_Empresa UNIQUE (Codigo, EmpresaID)
    );
    PRINT 'Tabla Global_Cat_CentrosCosto creada';
END;

-- 5. FORMAS DE PAGO SAT
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_FormaPagoSAT')
BEGIN
    CREATE TABLE Global_Cat_FormaPagoSAT (
        FormaPagoID INT IDENTITY(1,1) PRIMARY KEY,
        Clave VARCHAR(5) NOT NULL UNIQUE,
        Descripcion VARCHAR(150) NOT NULL,
        Activo BIT NOT NULL DEFAULT 1
    );
    PRINT 'Tabla Global_Cat_FormaPagoSAT creada';
    
    -- Datos del catálogo SAT
    INSERT INTO Global_Cat_FormaPagoSAT (Clave, Descripcion) VALUES
    ('01', 'Efectivo'),
    ('02', 'Cheque nominativo'),
    ('03', 'Transferencia electrónica de fondos'),
    ('04', 'Tarjeta de crédito'),
    ('05', 'Monedero electrónico'),
    ('06', 'Dinero electrónico'),
    ('08', 'Vales de despensa'),
    ('12', 'Dación en pago'),
    ('13', 'Pago por subrogación'),
    ('14', 'Pago por consignación'),
    ('15', 'Condonación'),
    ('17', 'Compensación'),
    ('23', 'Novación'),
    ('24', 'Confusión'),
    ('25', 'Remisión de deuda'),
    ('26', 'Prescripción o caducidad'),
    ('27', 'A satisfacción del acreedor'),
    ('28', 'Tarjeta de débito'),
    ('29', 'Tarjeta de servicios'),
    ('30', 'Aplicación de anticipos'),
    ('31', 'Intermediario pagos'),
    ('99', 'Por definir');
END;

-- 6. MÉTODOS DE PAGO SAT
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_MetodoPagoSAT')
BEGIN
    CREATE TABLE Global_Cat_MetodoPagoSAT (
        MetodoPagoID INT IDENTITY(1,1) PRIMARY KEY,
        Clave VARCHAR(5) NOT NULL UNIQUE,
        Descripcion VARCHAR(100) NOT NULL,
        Activo BIT NOT NULL DEFAULT 1
    );
    PRINT 'Tabla Global_Cat_MetodoPagoSAT creada';
    
    INSERT INTO Global_Cat_MetodoPagoSAT (Clave, Descripcion) VALUES
    ('PUE', 'Pago en una sola exhibición'),
    ('PPD', 'Pago en parcialidades o diferido');
END;

-- 7. USOS DE CFDI
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_UsoCFDI')
BEGIN
    CREATE TABLE Global_Cat_UsoCFDI (
        UsoCFDIID INT IDENTITY(1,1) PRIMARY KEY,
        Clave VARCHAR(5) NOT NULL UNIQUE,
        Descripcion VARCHAR(200) NOT NULL,
        AplicaFisica BIT NOT NULL DEFAULT 1,
        AplicaMoral BIT NOT NULL DEFAULT 1,
        Activo BIT NOT NULL DEFAULT 1
    );
    PRINT 'Tabla Global_Cat_UsoCFDI creada';
    
    INSERT INTO Global_Cat_UsoCFDI (Clave, Descripcion, AplicaFisica, AplicaMoral) VALUES
    ('G01', 'Adquisición de mercancías', 1, 1),
    ('G02', 'Devoluciones, descuentos o bonificaciones', 1, 1),
    ('G03', 'Gastos en general', 1, 1),
    ('I01', 'Construcciones', 1, 1),
    ('I02', 'Mobiliario y equipo de oficina', 1, 1),
    ('I03', 'Equipo de transporte', 1, 1),
    ('I04', 'Equipo de cómputo y accesorios', 1, 1),
    ('I05', 'Dados, troqueles, moldes, matrices', 1, 1),
    ('I06', 'Comunicaciones telefónicas', 1, 1),
    ('I07', 'Comunicaciones satelitales', 1, 1),
    ('I08', 'Otra maquinaria y equipo', 1, 1),
    ('D01', 'Honorarios médicos, dentales y gastos hospitalarios', 1, 0),
    ('D02', 'Gastos médicos por incapacidad o discapacidad', 1, 0),
    ('D03', 'Gastos funerales', 1, 0),
    ('D04', 'Donativos', 1, 0),
    ('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios', 1, 0),
    ('D06', 'Aportaciones voluntarias al SAR', 1, 0),
    ('D07', 'Primas por seguros de gastos médicos', 1, 0),
    ('D08', 'Gastos de transportación escolar obligatoria', 1, 0),
    ('D09', 'Depósitos en cuentas para el ahorro, primas de pensiones', 1, 0),
    ('D10', 'Pagos por servicios educativos (colegiaturas)', 1, 0),
    ('S01', 'Sin efectos fiscales', 1, 1),
    ('CP01', 'Pagos', 1, 1),
    ('CN01', 'Nómina', 0, 1);
END;

-- 8. REGÍMENES FISCALES
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Global_Cat_RegimenFiscal')
BEGIN
    CREATE TABLE Global_Cat_RegimenFiscal (
        RegimenFiscalID INT IDENTITY(1,1) PRIMARY KEY,
        Clave VARCHAR(5) NOT NULL UNIQUE,
        Descripcion VARCHAR(200) NOT NULL,
        AplicaFisica BIT NOT NULL DEFAULT 1,
        AplicaMoral BIT NOT NULL DEFAULT 1,
        Activo BIT NOT NULL DEFAULT 1
    );
    PRINT 'Tabla Global_Cat_RegimenFiscal creada';
    
    INSERT INTO Global_Cat_RegimenFiscal (Clave, Descripcion, AplicaFisica, AplicaMoral) VALUES
    ('601', 'General de Ley Personas Morales', 0, 1),
    ('603', 'Personas Morales con Fines no Lucrativos', 0, 1),
    ('605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios', 1, 0),
    ('606', 'Arrendamiento', 1, 0),
    ('607', 'Régimen de Enajenación o Adquisición de Bienes', 1, 0),
    ('608', 'Demás ingresos', 1, 0),
    ('610', 'Residentes en el Extranjero sin Establecimiento Permanente en México', 1, 1),
    ('611', 'Ingresos por Dividendos (socios y accionistas)', 1, 0),
    ('612', 'Personas Físicas con Actividades Empresariales y Profesionales', 1, 0),
    ('614', 'Ingresos por intereses', 1, 0),
    ('615', 'Régimen de los ingresos por obtención de premios', 1, 0),
    ('616', 'Sin obligaciones fiscales', 1, 0),
    ('620', 'Sociedades Cooperativas de Producción', 0, 1),
    ('621', 'Incorporación Fiscal', 1, 0),
    ('622', 'Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras', 1, 1),
    ('623', 'Opcional para Grupos de Sociedades', 0, 1),
    ('624', 'Coordinados', 0, 1),
    ('625', 'Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas', 1, 0),
    ('626', 'Régimen Simplificado de Confianza', 1, 1);
END;

-- 9. CUENTAS BANCARIAS (FINANZAS)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Finanzas_Cat_CuentasBancarias')
BEGIN
    CREATE TABLE Finanzas_Cat_CuentasBancarias (
        CuentaBancariaID INT IDENTITY(1,1) PRIMARY KEY,
        EmpresaID INT NULL,
        BancoID INT NULL,
        NumeroCuenta VARCHAR(20) NOT NULL,
        CLABE VARCHAR(18) NULL,
        Alias VARCHAR(50) NOT NULL,
        Moneda VARCHAR(3) NOT NULL DEFAULT 'MXN',
        EsCuentaPrincipal BIT NOT NULL DEFAULT 0,
        Activo BIT NOT NULL DEFAULT 1,
        FechaAlta DATETIME2 NOT NULL DEFAULT GETDATE()
    );
    PRINT 'Tabla Finanzas_Cat_CuentasBancarias creada';
END;

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================
SELECT 
    t.name AS Tabla,
    CASE WHEN t.name IS NOT NULL THEN 'EXISTE' ELSE 'NO EXISTE' END AS Estado
FROM (VALUES 
    ('Global_Cat_Empresas'),
    ('Global_Cat_Bancos'),
    ('Global_Cat_UnidadesMedida'),
    ('Global_Cat_CentrosCosto'),
    ('Global_Cat_FormaPagoSAT'),
    ('Global_Cat_MetodoPagoSAT'),
    ('Global_Cat_UsoCFDI'),
    ('Global_Cat_RegimenFiscal'),
    ('Finanzas_Cat_CuentasBancarias')
) AS Requeridas(name)
LEFT JOIN sys.tables t ON t.name = Requeridas.name;
"""


# ============================================================================
# FUNCIONES DE REPOSITORIO
# ============================================================================

async def listar_registros_catalogo(
    db,
    tabla: str,
    solo_activos: bool = False,
    buscar: Optional[str] = None,
    limit: int = 500
) -> List[Dict]:
    """
    Lista registros de un catálogo.
    
    Args:
        db: Conexión a MongoDB (para obtener credenciales SQL)
        tabla: Nombre de la tabla
        solo_activos: Si True, filtra solo registros activos
        buscar: Texto para búsqueda
        limit: Máximo de registros a retornar
    """
    server = await get_edarsa_hub_connection(db)
    
    estructura = ESTRUCTURA_TABLAS.get(tabla)
    if not estructura:
        raise ValueError(f"Tabla '{tabla}' no está configurada en el módulo de catálogos")
    
    campos = ", ".join(estructura["campos"])
    campo_activo = estructura.get("campo_activo")
    campo_nombre = estructura.get("campo_nombre", "Descripcion")
    
    where_clauses = []
    
    if solo_activos and campo_activo:
        where_clauses.append(f"{campo_activo} = 1")
    
    if buscar:
        buscar_escaped = escape_sql_string(buscar)
        where_clauses.append(f"{campo_nombre} LIKE '%{buscar_escaped}%'")
    
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    query = f"""
        SELECT TOP {limit} {campos}
        FROM {tabla}
        {where_sql}
        ORDER BY {estructura['pk']}
    """
    
    try:
        result = execute_edarsa_query(server, query)
        return result
    except Exception as e:
        logger.error(f"Error listando catálogo {tabla}: {e}")
        raise


async def obtener_registro_catalogo(db, tabla: str, id_valor: int) -> Optional[Dict]:
    """Obtiene un registro específico de un catálogo."""
    server = await get_edarsa_hub_connection(db)
    
    estructura = ESTRUCTURA_TABLAS.get(tabla)
    if not estructura:
        raise ValueError(f"Tabla '{tabla}' no está configurada")
    
    campos = ", ".join(estructura["campos"])
    pk = estructura["pk"]
    
    query = f"SELECT {campos} FROM {tabla} WHERE {pk} = {int(id_valor)}"
    
    result = execute_edarsa_query(server, query)
    return result[0] if result else None


async def crear_registro_catalogo(db, tabla: str, datos: Dict[str, Any], usuario: str) -> int:
    """
    Crea un nuevo registro en un catálogo.
    
    Returns:
        ID del registro creado
    """
    server = await get_edarsa_hub_connection(db)
    
    estructura = ESTRUCTURA_TABLAS.get(tabla)
    if not estructura:
        raise ValueError(f"Tabla '{tabla}' no está configurada")
    
    campos_editables = estructura["campos_editables"]
    pk = estructura["pk"]
    
    # Filtrar solo campos permitidos
    campos_insert = []
    valores_insert = []
    
    for campo in campos_editables:
        if campo in datos:
            campos_insert.append(campo)
            valor = datos[campo]
            if valor is None:
                valores_insert.append("NULL")
            elif isinstance(valor, bool):
                valores_insert.append("1" if valor else "0")
            elif isinstance(valor, (int, float)):
                valores_insert.append(str(valor))
            else:
                valores_insert.append(f"'{escape_sql_string(str(valor))}'")
    
    # Agregar campos de auditoría si existen en la estructura
    if "FechaAlta" in estructura["campos"] and "FechaAlta" not in campos_insert:
        campos_insert.append("FechaAlta")
        valores_insert.append("GETDATE()")
    
    if not campos_insert:
        raise ValueError("No hay campos válidos para insertar")
    
    query = f"""
        INSERT INTO {tabla} ({', '.join(campos_insert)})
        OUTPUT INSERTED.{pk}
        VALUES ({', '.join(valores_insert)})
    """
    
    try:
        result = execute_edarsa_query(server, query)
        if result and len(result) > 0:
            return result[0].get(pk)
        return None
    except Exception as e:
        logger.error(f"Error creando registro en {tabla}: {e}")
        raise


async def actualizar_registro_catalogo(
    db, 
    tabla: str, 
    id_valor: int, 
    datos: Dict[str, Any],
    usuario: str
) -> bool:
    """Actualiza un registro existente en un catálogo."""
    server = await get_edarsa_hub_connection(db)
    
    estructura = ESTRUCTURA_TABLAS.get(tabla)
    if not estructura:
        raise ValueError(f"Tabla '{tabla}' no está configurada")
    
    campos_editables = estructura["campos_editables"]
    pk = estructura["pk"]
    
    # Construir SET clause
    set_parts = []
    
    for campo in campos_editables:
        if campo in datos:
            valor = datos[campo]
            if valor is None:
                set_parts.append(f"{campo} = NULL")
            elif isinstance(valor, bool):
                set_parts.append(f"{campo} = {'1' if valor else '0'}")
            elif isinstance(valor, (int, float)):
                set_parts.append(f"{campo} = {valor}")
            else:
                set_parts.append(f"{campo} = '{escape_sql_string(str(valor))}'")
    
    # Agregar fecha de modificación si existe
    if "FechaModificacion" in estructura["campos"]:
        set_parts.append("FechaModificacion = GETDATE()")
    
    if not set_parts:
        raise ValueError("No hay campos válidos para actualizar")
    
    query = f"""
        UPDATE {tabla}
        SET {', '.join(set_parts)}
        WHERE {pk} = {int(id_valor)}
    """
    
    try:
        execute_edarsa_query(server, query)
        return True
    except Exception as e:
        logger.error(f"Error actualizando registro en {tabla}: {e}")
        raise


async def desactivar_registro_catalogo(db, tabla: str, id_valor: int) -> bool:
    """Desactiva (soft delete) un registro de un catálogo."""
    server = await get_edarsa_hub_connection(db)
    
    estructura = ESTRUCTURA_TABLAS.get(tabla)
    if not estructura:
        raise ValueError(f"Tabla '{tabla}' no está configurada")
    
    campo_activo = estructura.get("campo_activo")
    if not campo_activo:
        raise ValueError(f"La tabla '{tabla}' no tiene campo de activo/inactivo")
    
    pk = estructura["pk"]
    
    set_clause = f"{campo_activo} = 0"
    if "FechaModificacion" in estructura["campos"]:
        set_clause += ", FechaModificacion = GETDATE()"
    
    query = f"""
        UPDATE {tabla}
        SET {set_clause}
        WHERE {pk} = {int(id_valor)}
    """
    
    try:
        execute_edarsa_query(server, query)
        return True
    except Exception as e:
        logger.error(f"Error desactivando registro en {tabla}: {e}")
        raise


async def activar_registro_catalogo(db, tabla: str, id_valor: int) -> bool:
    """Reactiva un registro de un catálogo."""
    server = await get_edarsa_hub_connection(db)
    
    estructura = ESTRUCTURA_TABLAS.get(tabla)
    if not estructura:
        raise ValueError(f"Tabla '{tabla}' no está configurada")
    
    campo_activo = estructura.get("campo_activo")
    if not campo_activo:
        raise ValueError(f"La tabla '{tabla}' no tiene campo de activo/inactivo")
    
    pk = estructura["pk"]
    
    set_clause = f"{campo_activo} = 1"
    if "FechaModificacion" in estructura["campos"]:
        set_clause += ", FechaModificacion = GETDATE()"
    
    query = f"""
        UPDATE {tabla}
        SET {set_clause}
        WHERE {pk} = {int(id_valor)}
    """
    
    try:
        execute_edarsa_query(server, query)
        return True
    except Exception as e:
        logger.error(f"Error activando registro en {tabla}: {e}")
        raise


async def obtener_estructura_tabla(db, tabla: str) -> Dict:
    """Obtiene la estructura de columnas de una tabla desde la BD."""
    server = await get_edarsa_hub_connection(db)
    
    query = f"""
        SELECT 
            COLUMN_NAME as columna,
            DATA_TYPE as tipo,
            CHARACTER_MAXIMUM_LENGTH as longitud,
            IS_NULLABLE as nullable,
            COLUMN_DEFAULT as default_value
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{escape_sql_string(tabla)}'
        ORDER BY ORDINAL_POSITION
    """
    
    result = execute_edarsa_query(server, query)
    return result


async def contar_registros_tabla(db, tabla: str) -> int:
    """Cuenta el total de registros en una tabla."""
    server = await get_edarsa_hub_connection(db)
    
    # Query optimizado que verifica existencia y cuenta en uno solo
    query = f"""
    IF EXISTS (SELECT 1 FROM sys.tables WHERE name = '{escape_sql_string(tabla)}')
        SELECT COUNT(*) as total FROM [{tabla}]
    ELSE
        SELECT -1 as total
    """
    
    try:
        result = execute_edarsa_query(server, query)
        return result[0].get("total", -1) if result else -1
    except Exception as e:
        logger.warning(f"Error contando registros en {tabla}: {e}")
        return -1


async def obtener_conteos_tablas(db, tablas: list) -> Dict[str, int]:
    """Obtiene conteos de múltiples tablas en una sola consulta."""
    server = await get_edarsa_hub_connection(db)
    
    if not tablas:
        return {}
    
    # Primero obtener qué tablas existen
    tablas_str = ",".join([f"'{escape_sql_string(t)}'" for t in tablas])
    check_query = f"SELECT name FROM sys.tables WHERE name IN ({tablas_str})"
    
    try:
        tablas_existentes = execute_edarsa_query(server, check_query)
        tablas_que_existen = {row['name'] for row in tablas_existentes}
    except Exception as e:
        logger.error(f"Error verificando tablas: {e}")
        tablas_que_existen = set()
    
    # Construir resultado
    resultado = {}
    for tabla in tablas:
        if tabla in tablas_que_existen:
            try:
                count_query = f"SELECT COUNT(*) as total FROM [{tabla}]"
                count_result = execute_edarsa_query(server, count_query)
                resultado[tabla] = count_result[0].get('total', 0) if count_result else 0
            except Exception:
                resultado[tabla] = 0
        else:
            resultado[tabla] = -1  # No existe
    
    return resultado


async def ejecutar_ddl_tablas_nuevas(db) -> Dict:
    """Ejecuta el DDL para crear las tablas nuevas de catálogos globales."""
    server = await get_edarsa_hub_connection(db)
    
    # Dividir el script en statements individuales
    statements = DDL_TABLAS_NUEVAS.split(";")
    
    resultados = {
        "exitosos": 0,
        "errores": 0,
        "detalles": []
    }
    
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt or stmt.startswith("--"):
            continue
        
        # Ejecutar cada statement
        try:
            execute_edarsa_query(server, stmt)
            resultados["exitosos"] += 1
        except Exception as e:
            error_msg = str(e)
            # Ignorar errores de "ya existe"
            if "already exists" in error_msg.lower() or "ya existe" in error_msg.lower():
                resultados["detalles"].append(f"OK (ya existía): {stmt[:50]}...")
            else:
                resultados["errores"] += 1
                resultados["detalles"].append(f"ERROR: {error_msg[:100]}")
    
    return resultados


async def verificar_tablas_nuevas(db) -> Dict[str, bool]:
    """Verifica qué tablas nuevas existen."""
    server = await get_edarsa_hub_connection(db)
    
    tablas_nuevas = [
        "Global_Cat_Empresas",
        "Global_Cat_Bancos",
        "Global_Cat_UnidadesMedida",
        "Global_Cat_CentrosCosto",
        "Global_Cat_FormaPagoSAT",
        "Global_Cat_MetodoPagoSAT",
        "Global_Cat_UsoCFDI",
        "Global_Cat_RegimenFiscal",
        "Finanzas_Cat_CuentasBancarias"
    ]
    
    resultado = {}
    
    for tabla in tablas_nuevas:
        query = f"SELECT 1 FROM sys.tables WHERE name = '{tabla}'"
        try:
            result = execute_edarsa_query(server, query)
            resultado[tabla] = len(result) > 0
        except Exception:
            resultado[tabla] = False
    
    return resultado
