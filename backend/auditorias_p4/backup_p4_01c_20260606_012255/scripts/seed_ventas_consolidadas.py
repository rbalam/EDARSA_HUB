"""
Seed Script para Fact_Ventas_Consolidadas
=========================================
EDARSA HUB - Portal Inteligencia Comercial IA

Genera datos sintéticos de ventas para poblar la tabla Fact_Ventas_Consolidadas
y habilitar el dashboard de Inteligencia Comercial con datos de prueba.

Uso:
    EDARSAHUB_PASSWORD=<password> python3 seed_ventas_consolidadas.py

Estructura de tabla esperada:
    - Id (int, identity)
    - TenantID (int)
    - Fecha (date)
    - Periodo (nvarchar)
    - IdProducto (int)
    - Cantidad (decimal)
    - ImporteNeto (decimal)
    - Propina (decimal)
    - Pax (int)
    - IdAreaVenta (int, nullable)
    - IdFormaCobro (int, nullable)
"""

import pymssql
import os
from datetime import datetime, timedelta
import random


def seed_ventas_consolidadas():
    conn = pymssql.connect(
        server='<REDACTED_EDARSAHUB_SQL_HOST>',
        port=1433,
        user='<REDACTED_EDARSAHUB_SQL_USER>',
        password=os.environ.get('EDARSAHUB_PASSWORD', ''),
        database='EDARSAHUB',
        timeout=60
    )
    cursor = conn.cursor(as_dict=True)

    # 1. Limpiar datos previos si es necesario (Descomentar para reinicio limpio)
    # cursor.execute("TRUNCATE TABLE Fact_Ventas_Consolidadas")
    
    # 2. Obtener IDs de productos existentes
    cursor.execute("SELECT Id FROM Products")
    productos = [row['Id'] for row in cursor.fetchall()]
    
    print(f"Productos disponibles en DB: {len(productos)}")
    if not productos:
        print("ERROR: No hay productos en la tabla Products. No se puede generar ventas.")
        return

    # 3. Insertar datos con la estructura correcta
    insert_count = 0
    fecha_base = datetime.now()

    print("Iniciando inserción de datos sintéticos...")
    for dias_atras in range(30):
        fecha = fecha_base - timedelta(days=dias_atras)
        periodo = fecha.strftime('%Y-%m')
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        for tenant_id in [1, 2, 3, 4, 5]:  # 5 Sucursales
            for _ in range(random.randint(15, 30)):  # 15 a 30 ventas por día
                producto_id = random.choice(productos)
                cantidad = random.randint(1, 5)
                importe = round(random.uniform(100, 800) * cantidad, 2)
                propina = round(importe * random.uniform(0.05, 0.15), 2) if random.random() > 0.4 else 0
                pax = random.randint(1, 6)
                
                try:
                    cursor.execute("""
                        INSERT INTO Fact_Ventas_Consolidadas 
                        (TenantID, Fecha, Periodo, IdProducto, Cantidad, ImporteNeto, Propina, Pax) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (tenant_id, fecha_str, periodo, producto_id, cantidad, importe, propina, pax))
                    insert_count += 1
                except Exception as e:
                    print(f"Error insertando fila: {e}")
                    break
    
    conn.commit()
    print(f"\n✅ Proceso completado. Insertados {insert_count} registros de ventas.")

    # 4. Verificar la inserción
    cursor.execute("SELECT COUNT(*) as total FROM Fact_Ventas_Consolidadas")
    print(f"✅ Total actual en la tabla: {cursor.fetchone()['total']}")

    # 5. Probar salida de la Vista de Inteligencia
    try:
        cursor.execute("SELECT TOP 5 * FROM View_Inteligencia_Comercial")
        rows = cursor.fetchall()
        print(f"\n=== View_Inteligencia_Comercial ({len(rows)} filas de muestra) ===")
        if rows:
            print("Columnas de la Vista:", list(rows[0].keys()))
    except Exception as e:
        print(f"Error al probar la vista: {e}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    seed_ventas_consolidadas()
