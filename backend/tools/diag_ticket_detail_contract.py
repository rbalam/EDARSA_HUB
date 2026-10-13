#!/usr/bin/env python3
import json, os
from core.db import execute_sql_query

CFG={
 "host":os.getenv("EDARSAHUB_SQL_HOST"),
 "port":int(os.getenv("EDARSAHUB_SQL_PORT") or 1433),
 "database":os.getenv("EDARSAHUB_SQL_DATABASE") or "EDARSAHUB",
 "username":os.getenv("EDARSAHUB_SQL_USER"),
 "password":os.getenv("EDARSAHUB_SQL_PASSWORD"),
}

def q(sql):
    return execute_sql_query(CFG["host"],CFG["port"],CFG["database"],CFG["username"],CFG["password"],sql) or []

def emit(label,rows):
    print(label+"="+json.dumps(rows,default=str,ensure_ascii=False))

for unit in ("130QRO","CIENFUEGOS"):
    hist=q(f"""
    SELECT
      unidad_negocio_id,
      numero_ticket,
      MIN(CONVERT(varchar(19),fecha_hora,120)) AS fecha_hora,
      MAX(ISNULL(pax,0)) AS pax,
      SUM(ISNULL(importe_neto,0)) AS ventas_sin_propina,
      MAX(ISNULL(propina,0)) AS propina,
      COUNT(*) AS lineas
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto WITH (NOLOCK)
    WHERE unidad_negocio_id='{unit}'
      AND fecha_operacion='2026-10-12'
      AND ISNULL(activo,1)=1
      AND ISNULL(es_kpi_valido,1)=1
      AND ISNULL(cancelado_origen,0)=0
    GROUP BY unidad_negocio_id, numero_ticket
    ORDER BY numero_ticket
    """)
    emit(f"HIST_{unit}",hist)

    snap=q(f"""
    SELECT TOP 1 detalle_abiertas_json
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2 WITH (NOLOCK)
    WHERE unidad_negocio_id='{unit}'
      AND fecha_operacion='2026-10-12'
    ORDER BY snapshot_timestamp DESC, fecha_ultima_actualizacion DESC
    """)
    payload=[]
    if snap and snap[0].get("detalle_abiertas_json"):
        try:
            payload=json.loads(snap[0]["detalle_abiertas_json"])
        except Exception as exc:
            payload=[{"parse_error":str(exc)}]
    # ticket-level reduction
    tickets={}
    for row in payload if isinstance(payload,list) else []:
        folio=str(row.get("folio") or "").strip()
        origen=str(row.get("folio_origen") or "").strip()
        key=(str(row.get("sistema_origen") or ""), str(row.get("estado_ticket") or ""), folio, origen)
        t=tickets.setdefault(key,{
            "sistema_origen":row.get("sistema_origen"),
            "estado_ticket":row.get("estado_ticket"),
            "folio":folio,
            "folio_origen":origen,
            "total_ticket":0.0,
            "propina":0.0,
            "pax":0,
            "rows":0,
        })
        t["rows"]+=1
        try:t["total_ticket"]=max(t["total_ticket"],float(row.get("total_ticket") or 0))
        except:pass
        try:t["propina"]=max(t["propina"],float(row.get("propina") or 0))
        except:pass
        try:t["pax"]=max(t["pax"],int(float(row.get("pax") or 0)))
        except:pass
    emit(f"SNAP_{unit}",list(tickets.values()))
