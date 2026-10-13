#!/usr/bin/env python3
import json
from modules.comercial.service import _query_edarsahub_tablero
from modules.comercial.ticket_service import load_open_snapshot_lines

DATE="2026-10-12"

def safe(rows):
    out=[]
    for r in rows or []:
        out.append({k:(v.isoformat() if hasattr(v,"isoformat") else v) for k,v in r.items()})
    return out

for unit in ("130QRO","CIENFUEGOS"):
    closed=_query_edarsahub_tablero(f"""
        SELECT
            numero_ticket,
            MAX(ISNULL(pax,0)) AS pax,
            SUM(ISNULL(importe_neto,0)) AS ventas_sin_propina,
            MAX(ISNULL(propina,0)) AS propina
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto WITH (NOLOCK)
        WHERE unidad_negocio_id = '{unit}'
          AND fecha_operacion = '{DATE}'
          AND ISNULL(activo,1)=1
          AND ISNULL(es_kpi_valido,1)=1
          AND ISNULL(cancelado_origen,0)=0
        GROUP BY numero_ticket
        ORDER BY numero_ticket
    """) or []
    snap=load_open_snapshot_lines(unit,"",DATE)
    snap_tickets={}
    for row in snap:
        key=str(row.get("folio") or row.get("folio_origen") or "")
        cur=snap_tickets.setdefault(key,{
            "folio":row.get("folio"),
            "folio_origen":row.get("folio_origen"),
            "estado_ticket":row.get("estado_ticket"),
            "sistema_origen":row.get("sistema_origen"),
            "pax":row.get("pax"),
            "total_ticket":row.get("total_ticket"),
            "propina":row.get("propina"),
        })
    print(unit+"_CLOSED="+json.dumps(safe(closed),ensure_ascii=False,default=str))
    print(unit+"_SNAPSHOT="+json.dumps(list(snap_tickets.values()),ensure_ascii=False,default=str))
