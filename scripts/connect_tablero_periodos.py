#!/usr/bin/env python3
"""Conecta TableroEjecutivo con el contrato canonico de periodos.

Parche determinista y de una sola ejecucion. Falla cerrado si las anclas
verificadas cambiaron. No toca produccion, SQL ni archivos de entorno.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "src" / "pages" / "TableroEjecutivo.js"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: se esperaba 1 ancla y se encontraron {count}")
    return text.replace(old, new, 1)


def replace_all_required(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count < 1:
        raise RuntimeError(f"{label}: no se encontro el ancla")
    return text.replace(old, new)


def replace_optional(text: str, old: str, new: str) -> str:
    return text.replace(old, new) if old in text else text


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    original = source

    helper_anchor = "const transformV2ToV1Format = (v2Response, selectedMeses, selectedAnios, logger) => {"
    if helper_anchor not in source:
        raise RuntimeError("No se encontro transformV2ToV1Format")

    helper_end = "};\n\n// Constantes para meses y años (homologado con Dashboard Comercial)"
    helper_code = """};

// Contrato dinamico compartido por Ejecutivo, Comercial e Inteligencia.
// El frontend solo presenta; comparativos y proyeccion vienen del backend.
const aplicarContratoPeriodo = (responseData, contratoGeneral, contratosUnidad = {}) => {
  const contrato = contratoGeneral?.data || contratoGeneral || null;
  if (!contrato || !responseData) return responseData;

  const actual = contrato.actual || {};
  const inmediato = contrato.comparativos?.inmediato || {};
  const anual = contrato.comparativos?.anual || {};
  const proyeccion = contrato.proyeccion || {};
  const unidadesConDatos = contrato.unidades_con_datos || {};

  responseData.periodo = {
    ...(responseData.periodo || {}),
    modo_periodo: contrato.modo_periodo,
    fecha_corte_datos: contrato.periodos?.fecha_corte_datos,
    periodo_cerrado: contrato.periodos?.periodo_cerrado,
    etiquetas: contrato.etiquetas || {}
  };

  responseData.totales = {
    ...(responseData.totales || {}),
    pax_promedio: actual.pax_promedio ?? responseData.totales?.pax_promedio ?? null,
    cheque_promedio: actual.cheque_promedio ?? responseData.totales?.cheque_promedio ?? null,
    ticket_promedio: actual.cheque_promedio ?? responseData.totales?.ticket_promedio ?? null,
    proyeccion: proyeccion.proyeccion_total ?? responseData.totales?.proyeccion ?? null,
    var_vs_mes_ant: inmediato.var_ventas ?? responseData.totales?.var_vs_mes_ant ?? null,
    var_vs_año_ant: anual.var_ventas ?? responseData.totales?.var_vs_año_ant ?? null,
    var_pax_mes: inmediato.var_pax ?? responseData.totales?.var_pax_mes ?? null,
    var_pax_año: anual.var_pax ?? responseData.totales?.var_pax_año ?? null,
    var_cheques_mes: inmediato.var_cheques ?? responseData.totales?.var_cheques_mes ?? null,
    var_cheques_año: anual.var_cheques ?? responseData.totales?.var_cheques_año ?? null,
    var_proy_vs_mes: inmediato.var_proyeccion ?? responseData.totales?.var_proy_vs_mes ?? null,
    var_proy_vs_año: anual.var_proyeccion ?? responseData.totales?.var_proy_vs_año ?? null,
    ventas_ant: inmediato.ventas ?? responseData.totales?.ventas_ant ?? null,
    ventas_año: anual.ventas ?? responseData.totales?.ventas_año ?? null,
    pax_ant: inmediato.pax ?? responseData.totales?.pax_ant ?? null,
    pax_año: anual.pax ?? responseData.totales?.pax_año ?? null,
    cheques_ant: inmediato.cheques ?? responseData.totales?.cheques_ant ?? null,
    cheques_año: anual.cheques ?? responseData.totales?.cheques_año ?? null,
    unidades_periodo_ant: unidadesConDatos.periodo_anterior ?? null,
    unidades_año_ant: unidadesConDatos.anio_anterior ?? null,
    proyeccion_detalle: proyeccion.detalle || [],
    proyeccion_metodo: proyeccion.metodo || null,
    proyeccion_confianza: proyeccion.nivel_confianza || null
  };

  responseData.status_summary = {
    ...(responseData.status_summary || {}),
    unidades_data_ok: unidadesConDatos.actual ?? responseData.status_summary?.unidades_data_ok ?? responseData.unidades?.length ?? 0
  };

  responseData.unidades = (responseData.unidades || []).map((unidad) => {
    const key = unidad.unidad_negocio_codigo || unidad.unidad_negocio_id || unidad.id || unidad.server_id;
    const contratoUnidad = contratosUnidad[key]?.data || contratosUnidad[key] || null;
    if (!contratoUnidad) return unidad;

    const actualUnidad = contratoUnidad.actual || {};
    const compInmediato = contratoUnidad.comparativos?.inmediato || {};
    const compAnual = contratoUnidad.comparativos?.anual || {};
    const proyUnidad = contratoUnidad.proyeccion || {};

    return {
      ...unidad,
      pax_promedio: actualUnidad.pax_promedio ?? unidad.pax_promedio ?? null,
      cheque_promedio: actualUnidad.cheque_promedio ?? unidad.cheque_promedio ?? null,
      ticket_promedio: actualUnidad.cheque_promedio ?? unidad.ticket_promedio ?? null,
      proyeccion: proyUnidad.proyeccion_total ?? unidad.proyeccion ?? null,
      var_vs_mes_ant: compInmediato.var_ventas ?? unidad.var_vs_mes_ant ?? null,
      var_vs_año_ant: compAnual.var_ventas ?? unidad.var_vs_año_ant ?? null,
      var_pax_mes: compInmediato.var_pax ?? unidad.var_pax_mes ?? null,
      var_pax_año: compAnual.var_pax ?? unidad.var_pax_año ?? null,
      var_cheques_mes: compInmediato.var_cheques ?? unidad.var_cheques_mes ?? null,
      var_cheques_año: compAnual.var_cheques ?? unidad.var_cheques_año ?? null,
      var_proy_vs_mes: compInmediato.var_proyeccion ?? unidad.var_proy_vs_mes ?? null,
      var_proy_vs_año: compAnual.var_proyeccion ?? unidad.var_proy_vs_año ?? null,
      ventas_ant: compInmediato.ventas ?? unidad.ventas_ant ?? null,
      ventas_año: compAnual.ventas ?? unidad.ventas_año ?? null,
      pax_ant: compInmediato.pax ?? unidad.pax_ant ?? null,
      pax_año: compAnual.pax ?? unidad.pax_año ?? null,
      cheques_ant: compInmediato.cheques ?? unidad.cheques_ant ?? null,
      cheques_año: compAnual.cheques ?? unidad.cheques_año ?? null,
      proyeccion_detalle: proyUnidad.detalle || [],
      proyeccion_metodo: proyUnidad.metodo || null,
      proyeccion_confianza: proyUnidad.nivel_confianza || null
    };
  });

  responseData._contrato_periodo = contrato;
  return responseData;
};

const cargarContratosPeriodo = async ({ modo, fechaInicio, fechaFin, unidades = [] }) => {
  const paramsBase = {
    modo,
    fecha_inicio: fechaInicio,
    fecha_fin: fechaFin,
    fecha_corte_datos: modo === 'ventas_dia' ? fechaFin : undefined
  };

  const generalPromise = api.get('/v2/comercial/periodos/contrato', {
    params: paramsBase,
    timeout: 30000
  });

  const unidadesUnicas = [...new Set(unidades.filter(Boolean))];
  const unidadesPromise = Promise.allSettled(
    unidadesUnicas.map(async (unidad) => {
      const result = await api.get('/v2/comercial/periodos/contrato', {
        params: { ...paramsBase, unidad_negocio_pk: unidad },
        timeout: 30000
      });
      return [unidad, result.data];
    })
  );

  const [generalResult, resultadosUnidad] = await Promise.all([
    generalPromise,
    unidadesPromise
  ]);

  const contratosUnidad = {};
  resultadosUnidad.forEach((result) => {
    if (result.status === 'fulfilled') {
      const [unidad, payload] = result.value;
      contratosUnidad[unidad] = payload;
    }
  });

  return {
    general: generalResult.data,
    unidades: contratosUnidad
  };
};

// Constantes para meses y años (homologado con Dashboard Comercial)"""
    source = replace_once(source, helper_end, helper_code, "insertar helpers de contrato")

    daily_anchor = """              usedV2 = true;
              logger.log(`[VENTAS_DIA_V2] Cargadas ${responseData.unidades.length} unidades desde EDARSAHUB SQL`);"""
    daily_new = """              try {
                const fechaOperacion = ventasDiaData.fecha_operacion || resumen.fecha;
                if (!fechaOperacion) {
                  throw new Error('fecha_operacion ausente en respuesta ventas-dia');
                }
                const contratos = await cargarContratosPeriodo({
                  modo: 'ventas_dia',
                  fechaInicio: fechaOperacion,
                  fechaFin: fechaOperacion,
                  unidades: responseData.unidades.map(u => u.unidad_negocio_codigo || u.id)
                });
                responseData = aplicarContratoPeriodo(responseData, contratos.general, contratos.unidades);
              } catch (contratoError) {
                logger.warn(`[PERIODOS] Contrato diario no disponible; se conservan datos base: ${contratoError.message}`);
              }

              usedV2 = true;
              logger.log(`[VENTAS_DIA_V2] Cargadas ${responseData.unidades.length} unidades desde EDARSAHUB SQL`);"""
    source = replace_once(source, daily_anchor, daily_new, "conectar contrato diario")

    monthly_anchor = """              responseData = transformV2ToV1Format(v2Response.data, selectedMeses, selectedAnios, logger);

              if (responseData.unidades && responseData.unidades.length > 0) {"""
    monthly_new = """              responseData = transformV2ToV1Format(v2Response.data, selectedMeses, selectedAnios, logger);

              try {
                const contratos = await cargarContratosPeriodo({
                  modo: 'mensual',
                  fechaInicio,
                  fechaFin,
                  unidades: responseData.unidades.map(u => u.unidad_negocio_codigo || u.id)
                });
                responseData = aplicarContratoPeriodo(responseData, contratos.general, contratos.unidades);
              } catch (contratoError) {
                logger.warn(`[PERIODOS] Contrato mensual no disponible; se conservan datos base: ${contratoError.message}`);
              }

              if (responseData.unidades && responseData.unidades.length > 0) {"""
    source = replace_once(source, monthly_anchor, monthly_new, "conectar contrato mensual")

    replacements = {
        "vs Mismo Día Año Ant.": "vs Día Año Ant.",
        "'vs Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Año')": "'vs Día Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Mes Año Ant.')",
        "(esMultiMes ? 'vs Periodo Ant.' : 'vs Año Ant.')": "(esMultiMes ? 'vs Periodo Ant.' : 'vs Mes Año Ant.')",
        "<span className=\"text-xs\">Mes: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anterior}: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>",
        "<span className=\"text-xs\">Año: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anioAnt}: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>",
        "? data.totales.ventas  // En Ventas del Día, la proyección ES la venta actual (al cierre será = venta real)": "? data.totales.proyeccion",
        "return data.totales.var_proy_vs_año || 0;": "return data.totales.var_proy_vs_año ?? null;",
        "{formatPercent(data.totales.var_pax_mes || 0)}": "{formatPercent(data.totales.var_pax_mes)}",
        "{formatPercent(data.totales.var_pax_año || 0)}": "{formatPercent(data.totales.var_pax_año)}",
        "{formatPercent(data.totales.var_cheques_mes || 0)}": "{formatPercent(data.totales.var_cheques_mes)}",
        "{formatPercent(data.totales.var_cheques_año || 0)}": "{formatPercent(data.totales.var_cheques_año)}",
    }
    for old, new in replacements.items():
        source = replace_all_required(source, old, new, f"reemplazo {old[:45]}")

    source = replace_optional(
        source,
        "pax_promedio: u.pax_promedio ?? 0,",
        "pax_promedio: u.pax_promedio ?? null,",
    )
    source = replace_all_required(
        source,
        "proyeccion: 0,",
        "proyeccion: null,",
        "proyeccion diaria inicial",
    )

    modal_replacements = {
        "<span className=\"text-xs\">{modoVentasDia ? 'Día Ant:' : 'Mes:'} <VariacionBadge valor={unidad.pax_ant > 0 ? ((unidad.pax - unidad.pax_ant) / unidad.pax_ant * 100) : 0} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anterior}: <VariacionBadge valor={unidad.var_pax_mes} /></span>",
        "<span className=\"text-xs\">{modoVentasDia ? 'Año Ant:' : 'Año:'} <VariacionBadge valor={unidad.pax_año > 0 ? ((unidad.pax - unidad.pax_año) / unidad.pax_año * 100) : 0} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anioAnt}: <VariacionBadge valor={unidad.var_pax_año} /></span>",
        "<span className=\"text-xs\">{modoVentasDia ? 'Día Ant:' : 'Mes:'} <VariacionBadge valor={unidad.cheques_ant > 0 ? ((unidad.cheques - unidad.cheques_ant) / unidad.cheques_ant * 100) : 0} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anterior}: <VariacionBadge valor={unidad.var_cheques_mes} /></span>",
        "<span className=\"text-xs\">{modoVentasDia ? 'Año Ant:' : 'Año:'} <VariacionBadge valor={unidad.cheques_año > 0 ? ((unidad.cheques - unidad.cheques_año) / unidad.cheques_año * 100) : 0} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anioAnt}: <VariacionBadge valor={unidad.var_cheques_año} /></span>",
    }
    for old, new in modal_replacements.items():
        source = replace_all_required(source, old, new, f"modal {old[:45]}")

    units_anchor = """                  {!data.status_summary && (
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 block">Año Ant.</span>
                      <p className="text-sm font-bold text-zinc-300">
                        {data.totales?.unidades_año_ant || 0}
                      </p>
                    </div>
                  )}"""
    units_new = """                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">
                      {data?.periodo?.modo_ventas_dia ? 'Día Ant.' : 'Mes Ant.'}
                    </span>
                    <p className="text-sm font-bold text-zinc-300">
                      {data.totales?.unidades_periodo_ant ?? '-'}
                    </p>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">
                      {data?.periodo?.modo_ventas_dia ? 'Día Año Ant.' : 'Mes Año Ant.'}
                    </span>
                    <p className="text-sm font-bold text-zinc-300">
                      {data.totales?.unidades_año_ant ?? '-'}
                    </p>
                  </div>"""
    source = replace_once(source, units_anchor, units_new, "mostrar comparativos de unidades")

    if source == original:
        raise RuntimeError("El parche no produjo cambios")

    TARGET.write_text(source, encoding="utf-8")
    print("TABLERO_PERIODOS_CONNECTION=PASS")
    print(f"TARGET={TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
