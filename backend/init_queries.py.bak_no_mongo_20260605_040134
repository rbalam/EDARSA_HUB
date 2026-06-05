"""
Script para inicializar consultas SQL predeterminadas en la base de datos
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from datetime import datetime, timezone
import uuid

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'test_database')

# Consultas MPRO
MPRO_QUERIES = {
    "ventas": """declare @sucursal nvarchar(50)
declare @fecha_ini nvarchar(12)
declare @fecha_fin nvarchar(12)
declare @codigo_venta nvarchar(10)
declare @dias INTEGER
set @sucursal = '@sucursal'
set @fecha_ini = '@fecha_ini'
set @fecha_fin = '@fecha_fin'
set @codigo_venta = '0913'
set @dias = 7
select
venta.Al_Cve_Almacen,
Producto_Kit.Pk_Producto,
categoria.Ct_Descripcion [Categoria],
familia.Fm_Descripcion [Familia],
producto.Pr_Descripcion,
Producto_Kit.Un_Cve_Unidad,
sum(venta.Vn_Cantidad_1*Producto_Kit.Pk_Cantidad) cantidad
from venta
LEFT join producto_kit on Producto_Kit.Pr_Cve_Producto = venta.Pr_Cve_Producto
LEFT join producto on producto.Pr_Cve_Producto = Producto_kit.Pk_Producto
LEFT JOIN PRODUCTO P2 ON P2.Pr_Cve_Producto = VENTA.Pr_Cve_Producto
INNER join Categoria on categoria.Ct_Cve_Categoria = producto.Ct_Cve_Categoria
INNER join Familia on familia.Fm_Cve_Familia = Producto.Fm_Cve_Familia
inner join sucursal on sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
where
sucursal.Sc_Descripcion like '%' + @sucursal + '%'
and venta.Es_Cve_Estado <>'CA' and
venta.Vn_Fecha between @fecha_ini and @fecha_fin
AND producto_kit.Pk_Producto like '%'
and venta.Es_Cve_Estado <> 'CA'
and producto.Ct_Cve_Categoria in ('0001','0002','0004')
and producto.Dp_Cve_Departamento in ('0003','0004','0007','0002')
group by
Producto_Kit.Pk_Producto,
producto.Pr_Descripcion,
Producto_Kit.Un_Cve_Unidad,
categoria.Ct_Descripcion,
familia.Fm_Descripcion,
FAMILIA.Fm_Cve_Familia,
venta.Al_Cve_Almacen
union all(
select
venta.Al_Cve_Almacen,
VENTA.Pr_Cve_Producto [Pk_Producto],
categoria.Ct_Descripcion [Categoria],
familia.Fm_Descripcion [Familia],
producto.Pr_Descripcion,
VENTA.Vn_Unidad_Control_1 [UN_Cve_Unidad],
sum(venta.Vn_Cantidad_Control_1) cantidad
from venta
INNER join producto on producto.Pr_Cve_Producto = VENTA.Pr_Cve_Producto
INNER join Categoria on categoria.Ct_Cve_Categoria = producto.Ct_Cve_Categoria
INNER join Familia on familia.Fm_Cve_Familia = Producto.Fm_Cve_Familia
inner join sucursal on sucursal.Sc_Cve_Sucursal = venta.Sc_Cve_Sucursal
where
sucursal.Sc_Descripcion like '%' + @sucursal + '%'
and venta.Es_Cve_Estado <>'CA' and
venta.Vn_Fecha between @fecha_ini and @fecha_fin
and venta.Es_Cve_Estado <> 'CA'
and producto.Ct_Cve_Categoria in ('0001','0002','0004')
and producto.Dp_Cve_Departamento in ('0003','0004','0007','0002')
group by
venta.Pr_Cve_Producto,
VENTA.Vn_Unidad_Control_1,
producto.Pr_Descripcion,
categoria.Ct_Descripcion,
familia.Fm_Descripcion,
FAMILIA.Fm_Cve_Familia,
venta.Al_Cve_Almacen
)""",
    
    "movimientos": """DECLARE @SUCURSAL VARCHAR(50)
DECLARE @ALMACEN VARCHAR(20)
DECLARE @FECHA_INICIAL VARCHAR(20)
DECLARE @FECHA_FINAL VARCHAR(20)
DECLARE @FAMILIA VARCHAR(50)
DECLARE @SUBFAMILIA VARCHAR(50)
SET @SUCURSAL = '@sucursal'
SET @ALMACEN = '@almacen'
SET @FECHA_INICIAL = '@fecha_ini'
SET @FECHA_FINAL = '@fecha_fin'
SET @FAMILIA = ''
SET @SUBFAMILIA = ''
SELECT
E.Mv_Folio,
E.Fecha_Alta,
CASE
    WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
        THEN 
            CASE WHEN E.Mv_Tabla = 'CONVERSION_PRODUCTO' THEN E.Mv_Fecha ELSE
            (
                SELECT C.Co_Fecha FROM Conversion_Producto CN
                INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
                WHERE CN.Cp_Folio = E.Mv_Documento
                GROUP BY Co_Fecha
            )
            END
        ELSE E.Mv_Fecha
        END Mv_Fecha,
E.Mv_Tabla,
E.Mv_Documento,
E.Sc_Cve_Sucursal,
S.Sc_Descripcion [Sucursal],
e.Al_Cve_Almacen,
a.Al_Descripcion,
e.Tm_Cve_Tipo_Movimiento [Codigo],
tm.Tm_Descripcion [Movimiento],
tm.Tm_Tipo,
FM.Fm_Descripcion [Familia],
SB.Sf_Descripcion [SubFamilia],
p.pr_cve_producto [Cod_prod],
p.Pr_Descripcion [Productos],
E.Mv_Cantidad_Control_1,
E.Mv_Unidad_Control_1,
E.Mv_Costo,
E.Mv_Costo_Importe,
E.ES_CVE_ESTADO
FROM
Movimiento E
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = E.Sc_Cve_Sucursal
INNER JOIN Almacen A ON A.Al_Cve_Almacen = E.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = S.Sc_Cve_Sucursal
inner join Tipo_Movimiento tm on tm.Tm_Cve_Tipo_Movimiento = e.Tm_Cve_Tipo_Movimiento
inner join Producto p on p.Pr_Cve_Producto = e.Pr_Cve_Producto
INNER JOIN FAMILIA FM ON FM.Fm_Cve_Familia = P.Fm_Cve_Familia
INNER JOIN SubFamilia SB ON SB.Sf_Cve_SubFamilia = P.Sf_Cve_SubFamilia
WHERE
s.Sc_Descripcion like '%'+ @SUCURSAL +'%'
AND a.Al_Descripcion like '%' + @ALMACEN + '%'
AND FM.Fm_Descripcion LIKE '%' + @FAMILIA + '%'
AND SB.Sf_Descripcion LIKE '%' + @SUBFAMILIA + '%'
AND
(CASE   
    WHEN TM.Tm_Cve_Tipo_Movimiento IN('508','108') 
        THEN 
        CASE WHEN E.Mv_Tabla = 'CONVERSION_PRODUCTO' THEN E.Mv_Fecha ELSE
            (
                SELECT C.Co_Fecha FROM Conversion_Producto CN
                INNER JOIN COMPRA C ON C.Co_Folio = CN.Cp_Documento AND C.Pr_Cve_Producto = CN.Pr_Cve_Producto
                WHERE CN.Cp_Folio = E.Mv_Documento
                GROUP BY Co_Fecha
            )
        END
        ELSE E.Mv_Fecha
        END)
between @FECHA_INICIAL and @FECHA_FINAL
AND E.Tm_Cve_Tipo_Movimiento IN ('050','100', '106', '108','112','202','400','500','506','508','510','512')
AND E.Es_Cve_Estado <> 'CA'""",
    
    "productos": """SELECT
DEPARTAMENTO.Dp_Cve_Departamento,
DEPARTAMENTO.Dp_Descripcion [Departamento],
Categoria.Ct_Cve_Categoria,
Categoria.Ct_Descripcion [Categoria],
Familia.Fm_Cve_Familia,
familia.Fm_Descripcion [Familia],
PRODUCTO.PR_CVE_PRODUCTO,
PRODUCTO.Dp_Cve_Departamento,
PRODUCTO.Pr_Descripcion,
PRODUCTO.Pr_Unidad_Control_1,
PRODUCTO.Pr_ultimo_costo,
case
    when 
        isnull
        (
            (
            SELECT Conversion_Unidad.Cu_Cantidad FROM Conversion_Unidad 
            WHERE Conversion_Unidad.Pr_Cve_Producto = producto.Pr_Cve_Producto
            AND Conversion_Unidad.Cu_Unidad_Origen = producto.Pr_Unidad_Compra AND Conversion_Unidad.Cu_Unidad_Destino = producto.Pr_Unidad_Control_1
            ) 
        ,-1) = -1 
    then 
        (
            CASE 
                WHEN 
                    ISNULL
                    (
                        (
                            SELECT TOP(1) Producto_Presentacion.Pp_Cantidad FROM Producto_Presentacion 
                            WHERE Producto_Presentacion.Pp_Producto = PRODUCTO.Pr_Cve_Producto ORDER BY Producto_Presentacion.Pp_Cantidad
                    ),-1
                ) = -1 
                THEN 
                    (
                        0                    )
                 ELSE 
                    (
                        SELECT TOP(1) Producto_Presentacion.Pp_Cantidad FROM Producto_Presentacion 
                        WHERE Producto_Presentacion.Pp_Producto = PRODUCTO.Pr_Cve_Producto ORDER BY Producto_Presentacion.Pp_Cantidad
                    ) 
            END 
        ) 
    else 
        (
            (
                SELECT Conversion_Unidad.Cu_Cantidad FROM Conversion_Unidad 
                WHERE Conversion_Unidad.Pr_Cve_Producto = producto.Pr_Cve_Producto
                AND Conversion_Unidad.Cu_Unidad_Origen = producto.Pr_Unidad_Compra AND Conversion_Unidad.Cu_Unidad_Destino = producto.Pr_Unidad_Control_1
            )  
        ) 
end
PRESENTACION
FROM PRODUCTO
INNER JOIN FAMILIA ON FAMILIA.Fm_Cve_Familia = PRODUCTO.Fm_Cve_Familia
INNER JOIN DEPARTAMENTO ON Departamento.dp_cve_departamento = Producto.Dp_Cve_Departamento
INNER JOIN CATEGORIA ON CATEGORIA.Ct_Cve_Categoria = PRODUCTO.Ct_Cve_Categoria
WHERE PRODUCTO.Es_Cve_Estado <> 'BA'
and categoria.Ct_Cve_Categoria in ('0001','0002','0004')
AND Departamento.Dp_Cve_Departamento IN ('0003','0004','0007','0002')""",
    
    "inventarios": """DECLARE @SUCURSAL VARCHAR(20)
DECLARE @PRODUCTO VARCHAR(50)
DECLARE @FECHA_INICIAL VARCHAR(10)
DECLARE @FECHA_FIN VARCHAR(10)
SET @SUCURSAL = '@sucursal'
SET @FECHA_INICIAL = '@fecha_ini'
SET @FECHA_FIN = '@fecha_fin'
SELECT
f.Sc_Cve_Sucursal,
s.sc_descripcion,
F.Fi_Folio,
F.Fi_ID,
F.fi_fecha Fecha_Alta,
F.Fecha_Ult_Modif,
f.Al_Cve_Almacen,
a.Al_Descripcion [Almacen],
F.Pr_Cve_Producto,
P.Pr_Descripcion [Producto],
f.Fi_Producto_Kit,
pk.Pr_Descripcion [Kit],
f.Fi_Cantidad_Control_1,
F.Fi_Unidad_Control_1,
f.Fi_Cantidad_Control_2,
f.Fi_Unidad_Control_2,
F.Fi_Costo,
F.Fi_Unidad_Costo,
F.Fi_Costo_Importe,
F.Fi_Costo_Kit,
F.Fi_Unidad_Kit,
f.Oper_Ult_Modif
FROM Fisico F
inner join Almacen a on a.Al_Cve_Almacen = f.Al_Cve_Almacen AND F.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
inner join producto p on p.Pr_Cve_Producto = f.Pr_Cve_Producto
LEFT join producto pk on pk.Pr_Cve_Producto = f.Fi_Producto_Kit
INNER JOIN SUCURSAL S ON S.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
WHERE F.Es_Cve_Estado not in ('BA')
AND F.fi_fecha BETWEEN @FECHA_INICIAL AND @FECHA_FIN
AND S.Sc_Descripcion LIKE '%' + @SUCURSAL +'%'"""
}

async def init_queries():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Check if queries already exist
    existing = await db.queries.count_documents({})
    if existing > 0:
        print(f"Ya existen {existing} consultas en la base de datos")
        client.close()
        return
    
    # Insert MPRO queries
    for query_type, sql_query in MPRO_QUERIES.items():
        query_doc = {
            "id": str(uuid.uuid4()),
            "name": f"MPRO - {query_type.capitalize()}",
            "system_type": "MPRO",
            "query_type": query_type,
            "sql_query": sql_query,
            "description": f"Consulta predeterminada de {query_type} para ManagementPro",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.queries.insert_one(query_doc)
        print(f"Consulta creada: {query_doc['name']}")
    
    # Create admin user if doesn't exist
    admin_exists = await db.users.count_documents({"role": "Administrador"})
    if admin_exists == 0:
        import bcrypt
        hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": "admin@inventario.com",
            "name": "Administrador",
            "password": hashed_pw,
            "role": "Administrador",
            "sucursales": [],
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_user)
        print("Usuario administrador creado: admin@inventario.com / admin123")
    
    client.close()
    print("Inicialización completada")

if __name__ == "__main__":
    asyncio.run(init_queries())
