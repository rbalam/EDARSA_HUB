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


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    original = source

    helper_anchor = """const transformV2ToV1Format = (v2Response, selectedMeses, selectedAnios, logger) => {"""
    if helper_anchor not in source:
        raise RuntimeError("No se encontro transformV2ToV1Format")

    helper_end = """};\n\n// Constantes para meses y años (homologado con Dashboard Comercial)"""
    helper_code = """};

// Contrato dinamico compartido por Ejecutivo, Comercial e Inteligencia.
// El frontend solo presenta; comparativos y proyeccion vienen del backend.
const aplicarContratoPeriodo = (responseData, contratoGeneral, contratosUnidad = {}) => {
  const contrato = contratoGeneral?.data || contratoGeneral || null;
  if (!contrato || !responseData) return responseData;

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
    proyeccion: proyeccion.proyeccion_total ?? responseData.totales?.proyeccion ?? null,
    var_vs_mes_ant: inmediato.var_ventas ?? responseData.totales?.var_vs_mes_ant ?? null,
    var_vs_año_ant: anual.var_ventas ?? responseData.totales?.var_vs_año_ant ?? null,
    var_pax_mes: inmediato.var_pax ?? responseData.totales?.var_pax_mes ?? null,
    var_pax_año: anual.var_pax ?? responseData.totales?.var_pax_año ?? null,
    var_cheques_mes: inmediato.var_cheques ?? responseData.totales?.var_cheques_mes ?? null,
    var_cheques_año: anual.var_cheques ?? responseData.totales?.var_cheques_año ?? null,
    var_proy_vs_año: anual.var_proyeccion ?? responseData.totales?.var_proy_vs_año ?? null,
    ventas_ant: inmediato.ventas ?? responseData.totales?.ventas_ant ?? null,
    ventas_año: anual.ventas ?? responseData.totales?.ventas_año ?? null,
    pax_ant: inmediato.pax ?? responseData.totales?.pax_ant ?? null,
    pax_año: anual.pax ?? responseData.totales?.pax_año ?? null,
    cheques_ant: inmediato.cheques ?? responseData.totales?.cheques_ant ?? null,
    cheques_año: anual.cheques ?? responseData.totales?.cheques_año ?? null,
    unidades_año_ant: unidadesConDatos.anio_anterior ?? responseData.totales?.unidades_año_ant ?? null,
    proyeccion_detalle: proyeccion.detalle || [],
    proyeccion_metodo: proyeccion.metodo || null,
    proyeccion_confianza: proyeccion.nivel_confianza || null
  };

  responseData.unidades = (responseData.unidades || []).map((unidad) => {
    const key = unidad.unidad_negocio_codigo || unidad.unidad_negocio_id || unidad.id || unidad.server_id;
    const contratoUnidad = contratosUnidad[key]?.data || contratosUnidad[key] || null;
    if (!contratoUnidad) return unidad;

    const compInmediato = contratoUnidad.comparativos?.inmediato || {};
    const compAnual = contratoUnidad.comparativos?.anual || {};
    const proyUnidad = contratoUnidad.proyeccion || {};

    return {
      ...unidad,
      proyeccion: proyUnidad.proyeccion_total ?? unidad.proyeccion ?? null,
      var_vs_mes_ant: compInmediato.var_ventas ?? unidad.var_vs_mes_ant ?? null,
      var_vs_año_ant: compAnual.var_ventas ?? unidad.var_vs_año_ant ?? null,
      var_pax_mes: compInmediato.var_pax ?? unidad.var_pax_mes ?? null,
      var_pax_año: compAnual.var_pax ?? unidad.var_pax_año ?? null,
      var_cheques_mes: compInmediato.var_cheques ?? unidad.var_cheques_mes ?? null,
      var_cheques_año: compAnual.var_cheques ?? unidad.var_cheques_año ?? null,
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
                const fechaOperacion = ventasDiaResponse.data?.fecha || new Date().toISOString().slice(0, 10);
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
        "(esMultiMes ? 'vs Periodo Ant.' : 'vs Año Ant.')": "(esMultiMes ? 'vs Periodo Ant.' : 'vs Mes Año Ant.')",
        "<span className=\"text-xs\">Mes: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anterior}: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>",
        "<span className=\"text-xs\">Año: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>": "<span className=\"text-xs\">{leyendasComparativo.anioAnt}: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>",
    }
    for old, new in replacements.items():
        if old not in source:
            raise RuntimeError(f"No se encontro ancla de etiqueta: {old}")
        source = source.replace(old, new)

    if source == original:
        raise RuntimeError("El parche no produjo cambios")

    TARGET.write_text(source, encoding="utf-8")
    print("TABLERO_PERIODOS_CONNECTION=PASS")
    print(f"TARGET={TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
