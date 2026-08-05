// Contrato canónico puro para periodos comerciales.
// Sin dependencias externas ni efectos secundarios.

export const normalizarModoContratoPeriodo = (modo) => {
  if (modo === 'historico') {
    return 'mensual';
  }

  if (modo === 'ventas_dia' || modo === 'mensual') {
    return modo;
  }

  throw new Error(
    `Modo de contrato comercial no soportado: ${String(modo)}`
  );
};

export const aplicarContratoPeriodo = (responseData, contratoGeneral, contratosUnidad = {}) => {
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
