from pathlib import Path

TARGET = Path("backend/modules/comercial_v2/sync_comercial_edarsahub.py")
TEST = Path("backend/tests/test_estelar_softrestaurant_official_aggregate_bootstrap.py")

text = TARGET.read_text(encoding="utf-8")

old_query = '''QUERY_SOFTRESTAURANT_VENTAS_CERRADAS = """
SELECT
    t.apertura AS fecha_hora,
    ch.folio AS folio,
    1 AS num_cheques,
    ISNULL(ch.totalalimentossindescuentos, 0) AS alimentos,
    ISNULL(ch.totalbebidassindescuentos, 0) AS bebidas,
    ISNULL(ch.totalotrossindescuentos, 0) AS otros,
    ISNULL(ch.totalcortesias, 0) AS cortesias,
    ISNULL(ch.totaldescuentos, 0) AS descuentos,
    ISNULL(ch.subtotal, 0) AS subtotal,
    ISNULL(ch.totalimpuesto1, 0) AS iva,
    ISNULL(ch.total, 0) AS ventas_total,
    ISNULL(ch.propina, 0) AS propinas,
    ISNULL(ch.total, 0) + ISNULL(ch.propina, 0) AS total_con_propina,
    ISNULL(ch.nopersonas, 0) AS num_personas
FROM cheques AS ch
INNER JOIN turnos AS t
    ON t.idturno = ch.idturno
   AND t.idempresa = ch.idempresa
WHERE t.apertura >= DATEADD(DAY, -1, CONVERT(DATETIME, REPLACE('{fecha_inicio}', '-', ''), 112))
  AND t.apertura < DATEADD(DAY, 2, CONVERT(DATETIME, REPLACE('{fecha_fin}', '-', ''), 112))
  AND ch.idempresa = '{empresa_id}'
  AND t.idempresa = '{empresa_id}'
  AND t.cierre IS NOT NULL
  AND ch.cancelado = 0
ORDER BY t.apertura, ch.folio
"""'''
new_query = '''QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA = """
SELECT
    CONVERT(datetime, '{fecha_operacion} 12:00:00 AM') AS fecha_hora,
    CONVERT(date, '{fecha_operacion}') AS fecha_operacion,
    SUM(totalalimentossindescuentos) AS alimentos,
    SUM(totalbebidassindescuentos) AS bebidas,
    SUM(totalotrossindescuentos) AS otros,
    SUM(totalcortesias) AS cortesias,
    SUM(totaldescuentos) AS descuentos,
    SUM(subtotal) AS subtotal,
    SUM(totalimpuesto1) AS iva,
    SUM(total) AS ventas_total,
    SUM(propina) AS propinas,
    SUM(total + propina) AS total_con_propina,
    SUM(nopersonas) AS num_personas,
    COUNT(folio) AS num_cheques
FROM cheques
WHERE idempresa = '{empresa_id}'
  AND idturno IN (
      SELECT idturno FROM turnos
      WHERE idempresa = '{empresa_id}'
        AND apertura BETWEEN '{inicio_operativo}' AND '{fin_operativo}'
        AND cierre IS NOT NULL
  )
  AND cancelado = 0
"""'''

old_builder = '''    empresa_sql = empresa_id.replace("'", "''")
    return QUERY_SOFTRESTAURANT_VENTAS_CERRADAS.format(
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=empresa_sql,
    )'''
new_builder = '''    empresa_sql = empresa_id.replace("'", "''")
    bloques = []
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fecha_siguiente = fecha_actual + timedelta(days=1)
        bloques.append(QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA.format(
            fecha_operacion=fecha_actual.strftime('%Y-%m-%d'),
            empresa_id=empresa_sql,
            inicio_operativo=fecha_actual.strftime('%Y-%m-%d 09:00:00'),
            fin_operativo=fecha_siguiente.strftime('%Y-%m-%d 08:59:59'),
        ))
        fecha_actual = fecha_siguiente
    return "\\nUNION ALL\\n".join(bloques)'''

old_date_logic = '''        sistema_origen = getattr(config, "sistema_origen", None)

        if sistema_origen == SistemaOrigen.MPRO:
            # MPRO entrega Vn_Fecha como fecha comercial con hora 00:00:00.
            # Aplicar nuevamente la ventana operativa desplaza el registro
            # artificialmente al día anterior.
            fecha_operacion = _normalizar_fecha_operacion_value(
                fecha_hora
            )
        elif sistema_origen == SistemaOrigen.SOFTRESTAURANT:
            # SoftRestaurant sí entrega un timestamp real del cheque.
            fecha_operacion = _normalizar_fecha_operacion_value(
                get_fecha_operacion(unidad_negocio_pk, fecha_hora)
            )'''
new_date_logic = '''        sistema_origen = getattr(config, "sistema_origen", None)
        fecha_operacion_query = row_dict.get("fecha_operacion")

        if fecha_operacion_query is not None:
            fecha_operacion = _normalizar_fecha_operacion_value(fecha_operacion_query)
        elif sistema_origen == SistemaOrigen.MPRO:
            fecha_operacion = _normalizar_fecha_operacion_value(fecha_hora)
        elif sistema_origen == SistemaOrigen.SOFTRESTAURANT:
            fecha_operacion = _normalizar_fecha_operacion_value(
                get_fecha_operacion(unidad_negocio_pk, fecha_hora)
            )'''

for label, old, new in (
    ("query", old_query, new_query),
    ("builder", old_builder, new_builder),
    ("date_logic", old_date_logic, new_date_logic),
):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    text = text.replace(old, new, 1)

TARGET.write_text(text, encoding="utf-8")

TEST.write_text(
    '''from datetime import date\nfrom modules.comercial_v2 import sync_comercial_edarsahub as sync_module\n\ndef test_estelar_uses_official_aggregate_contract():\n    query = sync_module.build_softrestaurant_ventas_cerradas_query({"empresa_id": "EST"}, date(2026, 8, 31), date(2026, 8, 31))\n    for fragment in (\n        "SUM(total) AS ventas_total",\n        "SUM(propina) AS propinas",\n        "SUM(nopersonas) AS num_personas",\n        "COUNT(folio) AS num_cheques",\n        "WHERE idempresa = 'EST'",\n        "apertura BETWEEN '2026-08-31 09:00:00' AND '2026-09-01 08:59:59'",\n        "AND cierre IS NOT NULL",\n        "AND cancelado = 0",\n    ):\n        assert fragment in query\n    assert "JOIN turnos" not in query\n    assert "ch.folio AS folio" not in query\n''',
    encoding="utf-8",
)

print("ESTELAR_AGGREGATE_PATCH_APPLIED=1")
