from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
P1-FASE5A.1 - Repository para Cuentas y Saldos Bancarios
=========================================================
Acceso a datos EDARSAHUB. NO usar MongoDB.

Tablas:
- Finanzas_Cat_CuentasBancarias
- Finanzas_SaldosBancarios
- Global_Cat_Bancos
- Usuario_Catalogo
"""

from typing import Optional, List, Tuple
from datetime import date, datetime
from decimal import Decimal
import logging

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

logger = logging.getLogger(__name__)


def _execute_edarsahub(query: str, params: dict = None) -> List[dict]:
    """
    Ejecuta query en EDARSAHUB.
    
    IMPORTANTE: Solo usar EDARSAHUB, NO MongoDB.
    """
    try:
        # Reemplazar parámetros en query si existen
        if params:
            for key, value in params.items():
                placeholder = f"@{key}"
                if isinstance(value, str):
                    # Escapar comillas simples
                    value = value.replace("'", "''")
                    query = query.replace(placeholder, f"'{value}'")
                elif value is None:
                    query = query.replace(placeholder, "NULL")
                elif isinstance(value, bool):
                    query = query.replace(placeholder, "1" if value else "0")
                elif isinstance(value, (int, float, Decimal)):
                    query = query.replace(placeholder, str(value))
                elif isinstance(value, date):
                    query = query.replace(placeholder, f"'{value.isoformat()}'")
                else:
                    query = query.replace(placeholder, f"'{str(value)}'")
        
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        return result if result else []
    except Exception as e:
        logger.error(f"Error ejecutando query EDARSAHUB: {str(e)}")
        raise


def _get_valid_usuario_id(usuario_id: int) -> str:
    """
    Verifica si el usuario existe en Usuario_Catalogo.
    Si no existe, retorna 'NULL' para evitar conflictos de FK.
    """
    if not usuario_id:
        return "NULL"
    try:
        query = f"SELECT COUNT(*) as total FROM Usuario_Catalogo WHERE UsuarioID = {usuario_id}"
        result = _execute_edarsahub(query)
        if result and result[0]['total'] > 0:
            return str(usuario_id)
    except Exception:
        pass
    return "NULL"


# =============================================================================
# CATÁLOGO DE BANCOS
# =============================================================================

def get_bancos_activos() -> List[dict]:
    """
    Obtiene catálogo de bancos activos.
    
    Tabla: Global_Cat_Bancos
    """
    query = """
    SELECT 
        BancoID,
        CodigoBanco,
        NombreBanco,
        NombreCorto
    FROM Global_Cat_Bancos
    WHERE Activo = 1
    ORDER BY NombreBanco
    """
    return _execute_edarsahub(query)


def get_banco_by_id(banco_id: int) -> Optional[dict]:
    """
    Obtiene banco por ID.
    """
    query = f"""
    SELECT 
        BancoID,
        CodigoBanco,
        NombreBanco,
        NombreCorto,
        Activo
    FROM Global_Cat_Bancos
    WHERE BancoID = {banco_id}
    """
    result = _execute_edarsahub(query)
    return result[0] if result else None


# =============================================================================
# CUENTAS BANCARIAS
# =============================================================================

def get_cuentas_bancarias(
    banco_id: Optional[int] = None,
    activo: bool = True,
    include_inactive: bool = False,
    empresa_codigo: Optional[str] = None
) -> List[dict]:
    """
    Lista cuentas bancarias con información de banco.
    
    Tabla: Finanzas_Cat_CuentasBancarias
    JOIN: Global_Cat_Bancos, Sistema_Empresas (identidad canónica)
    Filtro canónico opcional por unidad de negocio (empresa_codigo).
    """
    where_clauses = []
    params = {}
    
    if not include_inactive:
        where_clauses.append("cb.Activo = 1")
    elif activo is not None:
        where_clauses.append(f"cb.Activo = {1 if activo else 0}")
    
    if banco_id:
        where_clauses.append(f"cb.BancoID = {banco_id}")
    
    if empresa_codigo:
        where_clauses.append("se.CodigoEmpresa = @empresa_codigo")
        params['empresa_codigo'] = empresa_codigo
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"""
    SELECT 
        cb.CuentaBancariaID,
        cb.EmpresaID,
        se.NombreEmpresa AS empresa_nombre,
        se.CodigoEmpresa AS empresa_codigo,
        cb.BancoID,
        b.NombreBanco,
        b.CodigoBanco,
        b.NombreCorto,
        cb.NumeroCuenta,
        cb.CLABE,
        cb.Alias,
        cb.Moneda,
        cb.EsCuentaPrincipal,
        cb.Activo,
        cb.FechaAlta,
        cb.UsuarioCreacionID,
        cb.FechaModificacion,
        cb.UsuarioModificacionID
    FROM Finanzas_Cat_CuentasBancarias cb
    LEFT JOIN Global_Cat_Bancos b ON cb.BancoID = b.BancoID
    LEFT JOIN Sistema_Empresas se ON cb.EmpresaID = se.EmpresaID
    {where_sql}
    ORDER BY cb.Alias
    """
    return _execute_edarsahub(query, params if params else None)


def get_cuenta_by_id(cuenta_id: int) -> Optional[dict]:
    """
    Obtiene cuenta bancaria por ID.
    """
    query = f"""
    SELECT 
        cb.CuentaBancariaID,
        cb.EmpresaID,
        cb.BancoID,
        b.NombreBanco,
        b.CodigoBanco,
        b.NombreCorto,
        cb.NumeroCuenta,
        cb.CLABE,
        cb.Alias,
        cb.Moneda,
        cb.EsCuentaPrincipal,
        cb.Activo,
        cb.FechaAlta,
        cb.UsuarioCreacionID,
        cb.FechaModificacion,
        cb.UsuarioModificacionID
    FROM Finanzas_Cat_CuentasBancarias cb
    LEFT JOIN Global_Cat_Bancos b ON cb.BancoID = b.BancoID
    WHERE cb.CuentaBancariaID = {cuenta_id}
    """
    result = _execute_edarsahub(query)
    return result[0] if result else None


def existe_numero_cuenta(numero_cuenta: str, excluir_id: Optional[int] = None) -> bool:
    """
    Verifica si ya existe una cuenta con ese número.
    """
    excluir_sql = f"AND CuentaBancariaID != {excluir_id}" if excluir_id else ""
    query = f"""
    SELECT COUNT(*) as total 
    FROM Finanzas_Cat_CuentasBancarias 
    WHERE NumeroCuenta = '{numero_cuenta}' {excluir_sql}
    """
    result = _execute_edarsahub(query)
    return result[0]['total'] > 0 if result else False


def existe_alias(alias: str, excluir_id: Optional[int] = None) -> bool:
    """
    Verifica si ya existe una cuenta con ese alias.
    """
    alias_escaped = alias.replace("'", "''")
    excluir_sql = f"AND CuentaBancariaID != {excluir_id}" if excluir_id else ""
    query = f"""
    SELECT COUNT(*) as total 
    FROM Finanzas_Cat_CuentasBancarias 
    WHERE Alias = '{alias_escaped}' {excluir_sql}
    """
    result = _execute_edarsahub(query)
    return result[0]['total'] > 0 if result else False


def crear_cuenta_bancaria(
    banco_id: int,
    numero_cuenta: str,
    alias: str,
    moneda: str,
    usuario_creacion_id: int,
    clabe: Optional[str] = None,
    es_cuenta_principal: bool = False,
    empresa_id: Optional[int] = None
) -> int:
    """
    Crea cuenta bancaria y retorna el ID generado.
    
    NOTA: Si Usuario_Catalogo está vacío, UsuarioCreacionID se guarda como NULL
    para evitar conflictos de FK.
    """
    clabe_sql = f"'{clabe}'" if clabe else "NULL"
    empresa_sql = empresa_id if empresa_id else "NULL"
    usuario_sql = _get_valid_usuario_id(usuario_creacion_id)
    alias_escaped = alias.replace("'", "''")
    
    query = f"""
    INSERT INTO Finanzas_Cat_CuentasBancarias (
        EmpresaID, BancoID, NumeroCuenta, CLABE, Alias, 
        Moneda, EsCuentaPrincipal, Activo, FechaAlta, UsuarioCreacionID
    )
    OUTPUT INSERTED.CuentaBancariaID
    VALUES (
        {empresa_sql}, {banco_id}, '{numero_cuenta}', {clabe_sql}, '{alias_escaped}',
        '{Moneda}', {1 if es_cuenta_principal else 0}, 1, GETDATE(), {usuario_sql}
    )
    """
    result = _execute_edarsahub(query)
    if result and 'CuentaBancariaID' in result[0]:
        return result[0]['CuentaBancariaID']
    raise Exception("Error al crear cuenta bancaria")


def actualizar_cuenta_bancaria(
    cuenta_id: int,
    usuario_modificacion_id: int,
    alias: Optional[str] = None,
    es_cuenta_principal: Optional[bool] = None,
    empresa_id: Optional[int] = None
) -> bool:
    """
    Actualiza campos editables de cuenta bancaria.
    """
    set_clauses = []
    
    if alias is not None:
        alias_escaped = alias.replace("'", "''")
        set_clauses.append(f"Alias = '{alias_escaped}'")    
    if es_cuenta_principal is not None:
        set_clauses.append(f"EsCuentaPrincipal = {1 if es_cuenta_principal else 0}")
    
    if empresa_id is not None:
        set_clauses.append(f"EmpresaID = {empresa_id}")
    
    if not set_clauses:
        return False
    
    # Verificar si el usuario existe
    usuario_sql = _get_valid_usuario_id(usuario_modificacion_id)
    set_clauses.append(f"UsuarioModificacionID = {usuario_sql}")
    set_clauses.append("FechaModificacion = GETDATE()")
    
    query = f"""
    UPDATE Finanzas_Cat_CuentasBancarias
    SET {', '.join(set_clauses)}
    WHERE CuentaBancariaID = {cuenta_id}
    """
    _execute_edarsahub(query)
    return True


def desactivar_cuenta_bancaria(
    cuenta_id: int,
    usuario_modificacion_id: int
) -> bool:
    """
    Desactiva cuenta bancaria (baja lógica).
    """
    usuario_sql = _get_valid_usuario_id(usuario_modificacion_id)
    query = f"""
    UPDATE Finanzas_Cat_CuentasBancarias
    SET Activo = 0,
        UsuarioModificacionID = {usuario_sql},
        FechaModificacion = GETDATE()
    WHERE CuentaBancariaID = {cuenta_id}
    """
    _execute_edarsahub(query)
    return True


def cuenta_tiene_saldos_vigentes(cuenta_id: int) -> bool:
    """
    Verifica si la cuenta tiene saldos vigentes.
    """
    query = f"""
    SELECT COUNT(*) as total 
    FROM Finanzas_SaldosBancarios 
    WHERE CuentaBancariaID = {cuenta_id} 
    AND EsVigente = 1 
    AND Activo = 1 
    AND Estatus = 'VIGENTE'
    """
    result = _execute_edarsahub(query)
    return result[0]['total'] > 0 if result else False


# =============================================================================
# SALDOS BANCARIOS
# =============================================================================

def get_saldos_cuenta(
    cuenta_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    solo_vigentes: bool = False,
    limit: int = 100
) -> List[dict]:
    """
    Lista saldos de una cuenta bancaria.
    """
    where_clauses = [f"sb.CuentaBancariaID = {cuenta_id}"]
    
    if solo_vigentes:
        where_clauses.append("sb.EsVigente = 1 AND sb.Activo = 1 AND sb.Estatus = 'VIGENTE'")
    
    if fecha_inicio:
        where_clauses.append(f"sb.FechaSaldo >= '{fecha_inicio.isoformat()}'")
    
    if fecha_fin:
        where_clauses.append(f"sb.FechaSaldo <= '{fecha_fin.isoformat()}'")
    
    where_sql = "WHERE " + " AND ".join(where_clauses)
    
    query = f"""
    SELECT TOP {limit}
        sb.SaldoBancarioID,
        sb.CuentaBancariaID,
        sb.FechaSaldo,
        sb.SaldoFinal,
        sb.Moneda,
        sb.TipoCambio,
        sb.FuenteDatos,
        sb.Observaciones,
        sb.EsVigente,
        sb.Activo,
        sb.Estatus,
        sb.FechaCreacion,
        sb.UsuarioCreacionID,
        uc.NombreCompleto AS NombreUsuarioCreacion,
        sb.FechaCancelacion,
        sb.UsuarioCancelacionID,
        ucancel.NombreCompleto AS NombreUsuarioCancelacion,
        sb.MotivoCancelacion
    FROM Finanzas_SaldosBancarios sb
    LEFT JOIN Usuario_Catalogo uc ON sb.UsuarioCreacionID = uc.UsuarioID
    LEFT JOIN Usuario_Catalogo ucancel ON sb.UsuarioCancelacionID = ucancel.UsuarioID
    {where_sql}
    ORDER BY sb.FechaSaldo DESC, sb.FechaCreacion DESC
    """
    return _execute_edarsahub(query)


def get_ultimo_saldo_vigente(cuenta_id: int) -> Optional[dict]:
    """
    Obtiene el último saldo vigente de una cuenta.
    """
    query = f"""
    SELECT TOP 1
        sb.SaldoBancarioID,
        sb.CuentaBancariaID,
        sb.FechaSaldo,
        sb.SaldoFinal,
        sb.Moneda,
        sb.FuenteDatos,
        sb.FechaCreacion,
        uc.NombreCompleto AS NombreUsuarioCreacion,
        DATEDIFF(day, sb.FechaSaldo, GETDATE()) AS DiasDesdeActualizacion
    FROM Finanzas_SaldosBancarios sb
    LEFT JOIN Usuario_Catalogo uc ON sb.UsuarioCreacionID = uc.UsuarioID
    WHERE sb.CuentaBancariaID = {cuenta_id}
      AND sb.EsVigente = 1
      AND sb.Activo = 1
      AND sb.Estatus = 'VIGENTE'
    ORDER BY sb.FechaSaldo DESC
    """
    result = _execute_edarsahub(query)
    return result[0] if result else None


def existe_saldo_vigente(cuenta_id: int, fecha_saldo: date) -> bool:
    """
    Verifica si existe un saldo vigente para cuenta+fecha.
    """
    query = f"""
    SELECT COUNT(*) as total 
    FROM Finanzas_SaldosBancarios 
    WHERE CuentaBancariaID = {cuenta_id}
    AND FechaSaldo = '{fecha_saldo.isoformat()}'
    AND EsVigente = 1
    AND Activo = 1
    AND Estatus = 'VIGENTE'
    """
    result = _execute_edarsahub(query)
    return result[0]['total'] > 0 if result else False


def get_saldo_by_id(saldo_id: int) -> Optional[dict]:
    """
    Obtiene saldo por ID.
    """
    query = f"""
    SELECT 
        sb.SaldoBancarioID,
        sb.CuentaBancariaID,
        sb.FechaSaldo,
        sb.SaldoFinal,
        sb.Moneda,
        sb.TipoCambio,
        sb.FuenteDatos,
        sb.Observaciones,
        sb.EsVigente,
        sb.Activo,
        sb.Estatus,
        sb.FechaCreacion,
        sb.UsuarioCreacionID,
        sb.FechaCancelacion,
        sb.UsuarioCancelacionID,
        sb.MotivoCancelacion,
        cb.Alias
    FROM Finanzas_SaldosBancarios sb
    LEFT JOIN Finanzas_Cat_CuentasBancarias cb ON sb.CuentaBancariaID = cb.CuentaBancariaID
    WHERE sb.SaldoBancarioID = {saldo_id}
    """
    result = _execute_edarsahub(query)
    return result[0] if result else None


def crear_saldo_bancario(
    cuenta_id: int,
    fecha_saldo: date,
    saldo_final: Decimal,
    moneda: str,
    usuario_creacion_id: int,
    observaciones: Optional[str] = None,
    fuente_datos: str = "MANUAL"
) -> int:
    """
    Crea saldo bancario y retorna el ID generado.
    """
    if observaciones:
        obs_escaped = observaciones.replace("'", "''")
        obs_sql = f"'{obs_escaped}'"
    else:
        obs_sql = "NULL"
    
    usuario_sql = _get_valid_usuario_id(usuario_creacion_id)
    
    query = f"""
    INSERT INTO Finanzas_SaldosBancarios (
        CuentaBancariaID, FechaSaldo, SaldoFinal, Moneda,
        FuenteDatos, Observaciones, EsVigente, Activo, Estatus,
        UsuarioCreacionID, FechaCreacion
    )
    OUTPUT INSERTED.SaldoBancarioID
    VALUES (
        {cuenta_id}, '{fecha_saldo.isoformat()}', {saldo_final}, '{Moneda}',
        '{fuente_datos}', {obs_sql}, 1, 1, 'VIGENTE',
        {usuario_sql}, GETDATE()
    )
    """
    result = _execute_edarsahub(query)
    if result and 'SaldoBancarioID' in result[0]:
        return result[0]['SaldoBancarioID']
    raise Exception("Error al crear saldo bancario")


def marcar_saldo_corregido(
    saldo_id: int,
    usuario_cancelacion_id: int,
    motivo: str
) -> bool:
    """
    Marca un saldo como CORREGIDO.
    """
    motivo_escaped = motivo.replace("'", "''")
    usuario_sql = _get_valid_usuario_id(usuario_cancelacion_id)
    query = f"""
    UPDATE Finanzas_SaldosBancarios
    SET EsVigente = 0,
        Activo = 0,
        Estatus = 'CORREGIDO',
        UsuarioCancelacionID = {usuario_sql},
        FechaCancelacion = GETDATE(),
        MotivoCancelacion = '{motivo_escaped}'
    WHERE SaldoBancarioID = {saldo_id}
    """
    _execute_edarsahub(query)
    return True


def marcar_saldo_cancelado(
    saldo_id: int,
    usuario_cancelacion_id: int,
    motivo: str
) -> bool:
    """
    Marca un saldo como CANCELADO.
    """
    motivo_escaped = motivo.replace("'", "''")
    usuario_sql = _get_valid_usuario_id(usuario_cancelacion_id)
    query = f"""
    UPDATE Finanzas_SaldosBancarios
    SET EsVigente = 0,
        Activo = 0,
        Estatus = 'CANCELADO',
        UsuarioCancelacionID = {usuario_sql},
        FechaCancelacion = GETDATE(),
        MotivoCancelacion = '{motivo_escaped}'
    WHERE SaldoBancarioID = {saldo_id}
    """
    _execute_edarsahub(query)
    return True


def get_saldo_bancario_total(fecha_consulta: Optional[date] = None) -> dict:
    """
    Calcula el saldo bancario total de todas las cuentas activas.
    
    Usa el último saldo vigente de cada cuenta.
    """
    if fecha_consulta is None:
        fecha_consulta = date.today()
    
    # Query con CTE para obtener últimos saldos
    query = f"""
    WITH UltimosSaldos AS (
        SELECT 
            sb.CuentaBancariaID,
            sb.SaldoFinal,
            sb.FechaSaldo,
            sb.Moneda,
            cb.BancoID,
            b.NombreCorto AS BancoNombre,
            DATEDIFF(day, sb.FechaSaldo, GETDATE()) AS DiasDesdeActualizacion,
            ROW_NUMBER() OVER (
                PARTITION BY sb.CuentaBancariaID 
                ORDER BY sb.FechaSaldo DESC
            ) AS rn
        FROM Finanzas_SaldosBancarios sb
        INNER JOIN Finanzas_Cat_CuentasBancarias cb 
            ON sb.CuentaBancariaID = cb.CuentaBancariaID
        LEFT JOIN Global_Cat_Bancos b ON cb.BancoID = b.BancoID
        WHERE sb.EsVigente = 1
          AND sb.Activo = 1
          AND sb.Estatus = 'VIGENTE'
          AND cb.Activo = 1
          AND sb.FechaSaldo <= '{fecha_consulta.isoformat()}'
    )
    SELECT 
        COALESCE(SUM(CASE WHEN rn = 1 THEN SaldoFinal ELSE 0 END), 0) AS SaldoTotal,
        COUNT(DISTINCT CASE WHEN rn = 1 THEN CuentaBancariaID END) AS CuentasConSaldo,
        COUNT(DISTINCT CASE WHEN rn = 1 AND DiasDesdeActualizacion > 3 THEN CuentaBancariaID END) AS CuentasDesactualizadas
    FROM UltimosSaldos
    """
    result = _execute_edarsahub(query)
    
    # Contar cuentas activas sin saldo
    query_sin_saldo = """
    SELECT COUNT(*) AS total
    FROM Finanzas_Cat_CuentasBancarias cb
    WHERE cb.Activo = 1
    AND NOT EXISTS (
        SELECT 1 FROM Finanzas_SaldosBancarios sb
        WHERE sb.CuentaBancariaID = cb.CuentaBancariaID
        AND sb.EsVigente = 1 AND sb.Activo = 1
    )
    """
    result_sin_saldo = _execute_edarsahub(query_sin_saldo)
    
    # Detalle por banco
    query_por_banco = f"""
    WITH UltimosSaldos AS (
        SELECT 
            sb.CuentaBancariaID,
            sb.SaldoFinal,
            cb.BancoID,
            b.NombreCorto AS BancoNombre,
            ROW_NUMBER() OVER (
                PARTITION BY sb.CuentaBancariaID 
                ORDER BY sb.FechaSaldo DESC
            ) AS rn
        FROM Finanzas_SaldosBancarios sb
        INNER JOIN Finanzas_Cat_CuentasBancarias cb 
            ON sb.CuentaBancariaID = cb.CuentaBancariaID
        LEFT JOIN Global_Cat_Bancos b ON cb.BancoID = b.BancoID
        WHERE sb.EsVigente = 1
          AND sb.Activo = 1
          AND sb.Estatus = 'VIGENTE'
          AND cb.Activo = 1
          AND sb.FechaSaldo <= '{fecha_consulta.isoformat()}'
    )
    SELECT 
        BancoID,
        BancoNombre,
        SUM(SaldoFinal) AS SaldoTotal,
        COUNT(*) AS Cuentas
    FROM UltimosSaldos
    WHERE rn = 1
    GROUP BY BancoID, BancoNombre
    ORDER BY SaldoTotal DESC
    """
    detalle_banco = _execute_edarsahub(query_por_banco)
    
    return {
        "saldo_total": float(result[0]['SaldoTotal']) if result else 0.0,
        "cuentas_con_saldo": result[0]['CuentasConSaldo'] if result else 0,
        "cuentas_sin_saldo": result_sin_saldo[0]['total'] if result_sin_saldo else 0,
        "cuentas_desactualizadas": result[0]['CuentasDesactualizadas'] if result else 0,
        "detalle_por_banco": [
            {
                "banco_id": d['BancoID'],
                "banco_nombre": d['BancoNombre'],
                "saldo_total": float(d['SaldoTotal']),
                "cuentas": d['Cuentas']
            }
            for d in detalle_banco
        ] if detalle_banco else []
    }


def get_historial_saldo(saldo_id: int) -> List[dict]:
    """
    Obtiene historial de auditoría de un saldo y sus correcciones.
    """
    # Primero obtener el saldo y su cuenta/fecha
    saldo = get_saldo_by_id(saldo_id)
    if not saldo:
        return []
    
    # Buscar todos los saldos de esa cuenta+fecha (para ver correcciones)
    query = f"""
    SELECT 
        sb.SaldoBancarioID,
        sb.FechaSaldo,
        sb.SaldoFinal,
        sb.Estatus,
        sb.FechaCreacion,
        uc.NombreCompleto AS UsuarioCreacion,
        sb.FechaCancelacion,
        ucancel.NombreCompleto AS UsuarioCancelacion,
        sb.MotivoCancelacion
    FROM Finanzas_SaldosBancarios sb
    LEFT JOIN Usuario_Catalogo uc ON sb.UsuarioCreacionID = uc.UsuarioID
    LEFT JOIN Usuario_Catalogo ucancel ON sb.UsuarioCancelacionID = ucancel.UsuarioID
    WHERE sb.CuentaBancariaID = {saldo['CuentaBancariaID']}
    AND sb.FechaSaldo = '{saldo['FechaSaldo']}'
    ORDER BY sb.FechaCreacion ASC
    """
    return _execute_edarsahub(query)
