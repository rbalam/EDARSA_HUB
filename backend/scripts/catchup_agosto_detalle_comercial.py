#!/usr/bin/env python3
"""Catch-up controlado del detalle comercial de agosto 2026.

Se ejecuta DENTRO del runtime de EDARSAHUB Desarrollo para reutilizar:
- /app/backend/.env
- SERVER_SECRET_KEY
- conexión SQL EDARSAHUB
- acceso de red a los POS

Dry-run por defecto. Para escribir debe recibirse --commit explícitamente.
Solo escribe unidad+fecha cuando el extractor POS concilia contra Runtime V2.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path("/app/backend")))

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from scripts.backfill_detalle_producto_pendientes import ejecutar_backfill


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--fecha-inicio",
        default="2026-08-01",
        help="Inicio inclusivo YYYY-MM-DD",
    )
    ap.add_argument(
        "--fecha-fin",
        default="2026-08-22",
        help="Fin exclusivo YYYY-MM-DD",
    )
    ap.add_argument(
        "--unidad",
        action="append",
        default=None,
        help="Unidad a procesar; repetible. Si se omite, procesa todas.",
    )
    ap.add_argument(
        "--commit",
        action="store_true",
        default=False,
        help="Escribe solo días OK_HEADER_CANONICO. Sin esta bandera es dry-run.",
    )
    args = ap.parse_args()

    fecha_inicio = date.fromisoformat(args.fecha_inicio)
    fecha_fin = date.fromisoformat(args.fecha_fin)

    code, resumen = ejecutar_backfill(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        unidades=args.unidad,
        commit=args.commit,
    )

    print("[CATCHUP_AGOSTO_DETALLE] RESULTADO")
    print(json.dumps(resumen, indent=2, ensure_ascii=False, default=str))

    if not args.commit:
        print("[CATCHUP_AGOSTO_DETALLE] DRY_RUN: no se escribieron datos")
    else:
        print(
            "[CATCHUP_AGOSTO_DETALLE] COMMIT: "
            f"filas_insertadas={resumen.get('filas_insertadas', 0)}; "
            f"dias_reparables={resumen.get('dias_reparables', 0)}; "
            f"dias_bloqueados={resumen.get('dias_bloqueados', 0)}; "
            f"dias_sin_runtime={resumen.get('dias_sin_runtime', 0)}"
        )

    return code


if __name__ == "__main__":
    sys.exit(main())
