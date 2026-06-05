# =============================================================================
# CAB-003 FASE 1B.1 - QUERIES MPRO (ManagementPro)
# =============================================================================
# Constantes SQL para detección de inventarios válidos en MPRO
# 
# REGLAS DE NEGOCIO MPRO:
# - Estados válidos para automatización: AC (Activo), AP (Aplicado)
# - Estados NO válidos: CON (Consolidado), BA (Baja)
# - Inventario inicial: Último inventario válido del MES ANTERIOR
# - Un mismo folio puede generar 2 análisis: uno en AC, otro en AP
# - Clave incluye: almacen + sucursal + comentario + folio + fecha + estado
# =============================================================================

# Estados válidos para automatización
ESTADOS_AUTOMATIZABLES = ('AC', 'AP')
ESTADOS_EXCLUIDOS = ('CON', 'BA')

# -----------------------------------------------------------------------------
# QUERY: Último inventario válido por almacén/sucursal/comentario
# -----------------------------------------------------------------------------
QUERY_ULTIMO_INVENTARIO_VALIDO = """
WITH inventarios_validos AS (
    SELECT
        F.Fi_Folio AS folio,
        F.Fi_Fecha AS fecha,
        F.Al_Cve_Almacen AS almacen_id,
        F.Sc_Cve_Sucursal AS sucursal_id,
        F.Fi_Comentario AS comentario,
        F.Es_Cve_Estado AS estado,
        ROW_NUMBER() OVER (
            PARTITION BY F.Al_Cve_Almacen, F.Sc_Cve_Sucursal, F.Fi_Comentario, CONVERT(date, F.Fi_Fecha), F.Es_Cve_Estado
            ORDER BY F.Fi_Folio DESC, F.Fi_Fecha DESC
        ) AS rn_dia
    FROM Fisico F
    WHERE F.Al_Cve_Almacen = :almacen_id
      AND F.Sc_Cve_Sucursal = :sucursal_id
      AND ISNULL(F.Fi_Comentario, '') = ISNULL(:comentario, '')
      AND F.Es_Cve_Estado IN ('AC', 'AP')
      AND F.Fecha_Baja IS NULL
)
SELECT TOP 1 folio, fecha, almacen_id, sucursal_id, comentario, estado
FROM inventarios_validos
WHERE rn_dia = 1
ORDER BY fecha DESC, folio DESC
"""

# -----------------------------------------------------------------------------
# QUERY: Último inventario válido del mes anterior (inventario inicial)
# -----------------------------------------------------------------------------
QUERY_ULTIMO_INVENTARIO_MES_ANTERIOR = """
WITH inventarios_validos AS (
    SELECT
        F.Fi_Folio AS folio,
        F.Fi_Fecha AS fecha,
        F.Al_Cve_Almacen AS almacen_id,
        F.Sc_Cve_Sucursal AS sucursal_id,
        F.Fi_Comentario AS comentario,
        F.Es_Cve_Estado AS estado,
        ROW_NUMBER() OVER (
            PARTITION BY F.Al_Cve_Almacen, F.Sc_Cve_Sucursal, F.Fi_Comentario, CONVERT(date, F.Fi_Fecha)
            ORDER BY 
                CASE F.Es_Cve_Estado WHEN 'AP' THEN 1 WHEN 'AC' THEN 2 ELSE 3 END,
                F.Fi_Folio DESC, 
                F.Fi_Fecha DESC
        ) AS rn_dia
    FROM Fisico F
    WHERE F.Al_Cve_Almacen = :almacen_id
      AND F.Sc_Cve_Sucursal = :sucursal_id
      AND ISNULL(F.Fi_Comentario, '') = ISNULL(:comentario, '')
      AND F.Es_Cve_Estado IN ('AC', 'AP')
      AND F.Fecha_Baja IS NULL
      AND F.Fi_Fecha >= :inicio_mes_anterior
      AND F.Fi_Fecha < :inicio_mes_actual
)
SELECT TOP 1 folio, fecha, almacen_id, sucursal_id, comentario, estado
FROM inventarios_validos
WHERE rn_dia = 1
ORDER BY fecha DESC, folio DESC
"""

# -----------------------------------------------------------------------------
# QUERY: Listar inventarios válidos recientes por sucursal (para detección)
# -----------------------------------------------------------------------------
QUERY_INVENTARIOS_VALIDOS_SUCURSAL = """
SELECT DISTINCT
    F.Fi_Folio AS folio,
    F.Fi_Fecha AS fecha,
    F.Al_Cve_Almacen AS almacen_id,
    A.Al_Descripcion AS almacen_nombre,
    F.Sc_Cve_Sucursal AS sucursal_id,
    S.Sc_Descripcion AS sucursal_nombre,
    F.Fi_Comentario AS comentario,
    F.Es_Cve_Estado AS estado
FROM Fisico F
INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
WHERE F.Es_Cve_Estado IN ('AC', 'AP')
  AND F.Fecha_Baja IS NULL
  AND F.Fi_Fecha >= DATEADD(MONTH, -2, GETDATE())
GROUP BY 
    F.Fi_Folio, F.Fi_Fecha, 
    F.Al_Cve_Almacen, A.Al_Descripcion,
    F.Sc_Cve_Sucursal, S.Sc_Descripcion,
    F.Fi_Comentario, F.Es_Cve_Estado
ORDER BY F.Fi_Fecha DESC
"""

# -----------------------------------------------------------------------------
# QUERY: Listar sucursales disponibles
# -----------------------------------------------------------------------------
QUERY_SUCURSALES = """
SELECT 
    Sc_Cve_Sucursal AS sucursal_id,
    Sc_Descripcion AS sucursal_nombre
FROM Sucursal
ORDER BY Sc_Descripcion
"""

# -----------------------------------------------------------------------------
# QUERY: Listar almacenes por sucursal
# -----------------------------------------------------------------------------
QUERY_ALMACENES_SUCURSAL = """
SELECT 
    Al_Cve_Almacen AS almacen_id,
    Al_Descripcion AS almacen_nombre,
    Sc_Cve_Sucursal AS sucursal_id
FROM Almacen
WHERE Sc_Cve_Sucursal = :sucursal_id
ORDER BY Al_Descripcion
"""
