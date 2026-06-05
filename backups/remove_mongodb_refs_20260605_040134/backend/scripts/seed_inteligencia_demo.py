"""
Script de Seed para Portal Inteligencia Comercial
Inserta datos de demostración en Fact_Ventas_Consolidadas

EDARSA HUB - Junio 2026
"""
import pymssql
import os
from datetime import datetime, timedelta
import random

# Configuración
EDARSAHUB_HOST = '54.39.104.176'
EDARSAHUB_PORT = 1433
EDARSAHUB_DB = 'EDARSAHUB'
EDARSAHUB_USER = 'HRLectura'
EDARSAHUB_PASS = os.environ.get('EDARSAHUB_PASSWORD', '')

def seed_ventas():
    """Inserta datos de demostración"""
    
    conn = pymssql.connect(
        server=EDARSAHUB_HOST,
        port=EDARSAHUB_PORT,
        user=EDARSAHUB_USER,
        password=EDARSAHUB_PASS,
        database=EDARSAHUB_DB,
        timeout=60
    )
    cursor = conn.cursor(as_dict=True)
    
    # Obtener productos existentes
    cursor.execute("SELECT Id, NombreProducto, Familia FROM Products")
    productos = cursor.fetchall()
    
    if not productos:
        print("ERROR: No hay productos en la tabla Products")
        return
    
    print(f"Encontrados {len(productos)} productos")
    
    # Unidades de negocio
    unidades = ['CIENFUEGOS', '130_MERIDA', '130_QUERETARO', 'LA_ESTELAR', 'ORIGEN']
    
    # Generar datos para los últimos 30 días
    fecha_base = datetime.now()
    
    insert_count = 0
    
    for dias_atras in range(30):
        fecha = fecha_base - timedelta(days=dias_atras)
        periodo = fecha.strftime('%Y-%m')
        
        for unidad in unidades:
            # Generar entre 20-50 transacciones por día por unidad
            num_transacciones = random.randint(20, 50)
            
            for _ in range(num_transacciones):
                producto = random.choice(productos)
                
                # Variar cantidad e importe según hora
                hora = random.randint(6, 23)
                fecha_hora = fecha.replace(hour=hora, minute=random.randint(0, 59))
                
                cantidad = random.randint(1, 5)
                precio_base = random.uniform(50, 500)
                importe = round(cantidad * precio_base, 2)
                pax = random.randint(1, 6)
                propina = round(importe * random.uniform(0.05, 0.20), 2) if random.random() > 0.3 else 0
                
                # Insert
                sql = """
                INSERT INTO Fact_Ventas_Consolidadas 
                (Fecha, TenantID, Periodo, IdProducto, Cantidad, ImporteNeto, Pax, Propina)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                try:
                    cursor.execute(sql, (
                        fecha_hora,
                        unidad,
                        periodo,
                        producto['Id'],
                        cantidad,
                        importe,
                        pax,
                        propina
                    ))
                    insert_count += 1
                except Exception as e:
                    print(f"Error insertando: {e}")
    
    conn.commit()
    print(f"\n✅ Insertados {insert_count} registros de ventas de demostración")
    
    # Verificar vista
    cursor.execute("SELECT COUNT(*) as total FROM View_Inteligencia_Comercial")
    total_vista = cursor.fetchone()['total']
    print(f"✅ View_Inteligencia_Comercial ahora tiene {total_vista} registros")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    seed_ventas()
