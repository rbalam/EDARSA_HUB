#!/usr/bin/env python3
import argparse, json, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PREFIX = "EDARSAHUB_HEADER_RESULT="

def emit(data):
    print(PREFIX + json.dumps(data, ensure_ascii=False, default=str), flush=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--unidad", required=True)
    p.add_argument("--fecha-inicio", required=True)
    p.add_argument("--fecha-fin", required=True)
    p.add_argument("--run-id", required=True)
    a = p.parse_args()
    code = a.unidad.strip().upper()
    try:
        from core.unidades_service import UnidadesService
        from modules.comercial_v2.schemas import UnidadNegocioConfig, SistemaOrigen
        from modules.comercial_v2.sync_comercial_edarsahub import (
            sync_softrestaurant_ventas_cerradas, sync_mpro_ventas_cerradas,
        )
        u = next((x for x in UnidadesService.get_all()
                  if str(x.get("codigo") or "").strip().upper() == code), None)
        if not u:
            emit({"success": False, "error_message": "UNIT_NOT_FOUND"})
            return 4
        system = str(u.get("system_type") or "").upper()
        origin = (SistemaOrigen.SOFTRESTAURANT if "SOFTRESTAURANT" in system
                  else SistemaOrigen.MPRO if "MPRO" in system else None)
        if origin is None:
            emit({"success": False, "error_message": "SYSTEM_NOT_SUPPORTED"})
            return 4
        sucursal = u.get("sucursal_origen_id") or "DEFAULT"
        cfg = UnidadNegocioConfig(
            unidad_negocio_pk=u.get("unidad_negocio_pk"),
            unidad_negocio_nombre=u.get("nombre"),
            server_id=u.get("server_id"),
            sucursal_id=sucursal,
            sucursal_nombre=u.get("nombre"),
            sistema_origen=origin,
            activo=True,
        )
        fi, ff = date.fromisoformat(a.fecha_inicio), date.fromisoformat(a.fecha_fin)
        if origin == SistemaOrigen.SOFTRESTAURANT:
            r = sync_softrestaurant_ventas_cerradas(
                config=cfg, fecha_inicio=fi, fecha_fin=ff, run_id=a.run_id
            )
        else:
            r = sync_mpro_ventas_cerradas(
                config=cfg, sucursal_id=sucursal,
                fecha_inicio=fi, fecha_fin=ff, run_id=a.run_id
            )
        emit({
            "success": bool(r.success),
            "records_processed": int(r.records_processed or 0),
            "records_inserted": int(r.records_inserted or 0),
            "records_updated": int(r.records_updated or 0),
            "records_skipped": int(r.records_skipped or 0),
            "records_errored": int(r.records_errored or 0),
            "duration_seconds": float(r.duration_seconds or 0),
            "error_message": r.error_message,
        })
        return 0 if r.success else 5
    except Exception as exc:
        emit({"success": False, "records_errored": 1,
              "error_message": f"{type(exc).__name__}: {exc}"})
        return 10

if __name__ == "__main__":
    raise SystemExit(main())
