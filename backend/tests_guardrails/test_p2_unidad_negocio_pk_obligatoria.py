"""
P2-25 Guardrail: unidad_negocio_pk obligatoria en KPIs Comercial
"""
import sys
from core.sql_first.db import get_sql_connection

def test_no_null_pk():
    conn = get_sql_connection()
    cur = conn.cursor()
    
    errors = []
    
    # Verificar Diarios
    cur.execute("SELECT COUNT(*) FROM dbo.Comercial_KPIs_Diarios_v2 WHERE unidad_negocio_pk IS NULL")
    n = cur.fetchone()[0]
    if n > 0:
        errors.append(f"Comercial_KPIs_Diarios_v2: {n} registros con unidad_negocio_pk NULL")
    
    # Verificar Mensuales
    cur.execute("SELECT COUNT(*) FROM dbo.Comercial_KPIs_Mensuales_v2 WHERE unidad_negocio_pk IS NULL")
    n = cur.fetchone()[0]
    if n > 0:
        errors.append(f"Comercial_KPIs_Mensuales_v2: {n} registros con unidad_negocio_pk NULL")
    
    conn.close()
    
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  {e}")
        return False
    
    print("PASS: unidad_negocio_pk obligatoria - 0 registros NULL")
    return True

if __name__ == "__main__":
    success = test_no_null_pk()
    sys.exit(0 if success else 1)
