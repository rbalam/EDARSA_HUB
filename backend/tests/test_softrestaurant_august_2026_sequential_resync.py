import asyncio
import json
import time
from datetime import date, timedelta

from api.admin_scheduler_resync import (
    _get_unidad_config,
    _ejecutar_dry_run,
    _ejecutar_sync_real,
    _execute_edarsahub_query,
)

UNIDADES = ("ESTELAR", "CIENFUEGOS", "130MID")
SERVERS = {
    "ESTELAR": "a5ff0e25-f029-43db-b634-d4ac814c904f",
    "CIENFUEGOS": "6d053c22-523e-48c0-b72b-96081e2d781b",
    "130MID": "a5547321-1139-4d2b-9d53-182ca737b6b6",
}

def _metricas(row):
    return {
        "ventas_total": round(float(row.get("ventas_total") or 0), 2),
        "propinas_total": round(float(row.get("propinas_total") or 0), 2),
        "tickets_total": int(row.get("tickets_total") or 0),
        "pax_total": int(row.get("pax_total") or 0),
    }

def _leer_final(codigo, fecha):
    rows = _execute_edarsahub_query(f"""
        SELECT
            COUNT(*) AS registros_activos,
            SUM(ISNULL(ventas_total, 0)) AS ventas_total,
            SUM(ISNULL(propinas_total, 0)) AS propinas_total,
            SUM(ISNULL(tickets_total, 0)) AS tickets_total,
            SUM(ISNULL(pax_total, 0)) AS pax_total
        FROM dbo.Comercial_KPIs_Diarios_v2
        WHERE unidad_negocio_id = '{codigo}'
          AND fecha_operacion = '{fecha.isoformat()}'
          AND ISNULL(activo, 1) = 1
    """)
    assert rows, (codigo, fecha, "Sin lectura final EDARSAHUB")
    row = rows[0]
    return {
        "registros_activos": int(row.get("registros_activos") or 0),
        "ventas_total": round(float(row.get("ventas_total") or 0), 2),
        "propinas_total": round(float(row.get("propinas_total") or 0), 2),
        "tickets_total": int(row.get("tickets_total") or 0),
        "pax_total": int(row.get("pax_total") or 0),
    }

def test_softrestaurant_agosto_2026_secuencial_dia_por_dia():
    fecha = date(2026, 8, 1)
    fin = date(2026, 8, 30)
    evidencia = []

    while fecha <= fin:
        dia = []
        for codigo in UNIDADES:
            unidad = _get_unidad_config(codigo)
            assert unidad, (codigo, fecha, "Unidad no encontrada")
            assert unidad.get("server_id") == SERVERS[codigo], (codigo, unidad)
            assert unidad.get("sistema") == "SOFTRESTAURANT", (codigo, unidad)

            dry = asyncio.run(_ejecutar_dry_run(codigo, unidad, fecha, fecha))
            assert dry.get("success") is True, (codigo, fecha, dry)
            detalle = dry.get("detalle") or []
            assert len(detalle) == 1, (codigo, fecha, dry)
            origen = _metricas(detalle[0])

            run_id = f"CHATGPT-SOFT-AUG2026-{fecha.strftime('%Y%m%d')}-{codigo}"
            real = asyncio.run(_ejecutar_sync_real(codigo, unidad, fecha, fecha, run_id))
            assert real.get("success") is True, (codigo, fecha, real)

            final = _leer_final(codigo, fecha)
            assert final["registros_activos"] == 1, (codigo, fecha, final)
            for campo in ("ventas_total", "propinas_total", "tickets_total", "pax_total"):
                assert final[campo] == origen[campo], (codigo, fecha, campo, origen, final)

            dia.append({
                "unidad": codigo,
                "fecha": fecha.isoformat(),
                "origen": origen,
                "destino": final,
                "real": {
                    "processed": real.get("records_processed"),
                    "inserted": real.get("records_inserted"),
                    "updated": real.get("records_updated"),
                    "errored": real.get("records_errored"),
                },
            })
            time.sleep(0.5)

        evidencia.extend(dia)
        print("SOFTRESTAURANT_DAY_OK=" + json.dumps({"fecha": fecha.isoformat(), "unidades": dia}, ensure_ascii=False, default=str))
        fecha += timedelta(days=1)
        time.sleep(0.5)

    assert len(evidencia) == 90
    assert evidencia[-1]["fecha"] == "2026-08-30"
    print("SOFTRESTAURANT_AUGUST_SEQUENTIAL_COMPLETE=90")
