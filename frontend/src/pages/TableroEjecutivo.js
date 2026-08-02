import logger from '../services/logger';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import { clearSession } from '../services/authStorage';
import React, { useState, useEffect, useCallback, useRef } from 'react';
// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
import api from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import {
  Loader2, TrendingUp, TrendingDown, RefreshCw, Building2, Users, Receipt,
  DollarSign, ArrowLeft, ChevronRight, Target, Clock, Utensils, X,
  BarChart3, Wallet, UserCircle, Award, ChevronDown, AlertTriangle
} from 'lucide-react';
import { formatNombreSucursal } from '../lib/formatSucursal';
import CanonicalPeriodSelector, {
  TEMPORAL_MODES,
} from '../components/filters/CanonicalPeriodSelector';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// SUBFASE 5: Feature flag para Comercial V2 (default OFF)
const USE_COMERCIAL_V2 = process.env.REACT_APP_COMERCIAL_V2_ENABLED === 'true';

// ============================================================================
// NOTA (2026-06-09): Se ELIMINÓ el fallback estático con cifras de ventas
// hardcodeadas (FALLBACK_TABLERO_EJECUTIVO / transformFallbackToTableroFormat).
// Era código muerto (nunca se invocaba) y violaba la Regla de Oro (datos de
// negocio inventados). Ante error de API se preservan los datos previos y se
// muestra un toast — V2 es la fuente única, NO-LIVE.
// ============================================================================

// SUBFASE 5: Transformador de respuesta v2 al formato esperado por v1
const transformV2ToV1Format = (v2Response, selectedMeses, selectedAnios, logger) => {
  try {
    const data = v2Response.data || v2Response;
    const totales = data.totales || {};
    const unidades = data.unidades || [];
    const periodo = data.periodo || {};

    // =========================================================================
    // PROYECCIÓN MENSUAL V2 — REGLA DE NEGOCIO
    // =========================================================================
    // Fórmula: proyeccion = (venta_acumulada / dias_transcurridos) * dias_proyectables
    // - dias_transcurridos: días calendario ya transcurridos del mes
    // - dias_proyectables: días totales del mes (excepción enero = 30)
    // - Futuro: Se reemplazará por calendario operativo EDARSAHUB
    // =========================================================================

    const hoy = new Date();
    const mesSeleccionado = parseInt(selectedMeses[0]) || (hoy.getMonth() + 1);
    const anioSeleccionado = parseInt(selectedAnios[0]) || hoy.getFullYear();

    // Días totales del mes seleccionado
    const diasTotalesMes = new Date(anioSeleccionado, mesSeleccionado, 0).getDate();

    // Días proyectables: enero = 30 (1 de enero no laborable), otros meses = días naturales
    // TODO: Reemplazar por calendario operativo EDARSAHUB cuando exista
    const diasProyectables = (mesSeleccionado === 1) ? 30 : diasTotalesMes;

    // Determinar si es el mes actual
    const esElMesActual = (mesSeleccionado === (hoy.getMonth() + 1)) && (anioSeleccionado === hoy.getFullYear());

    // Días transcurridos válidos: si es mes actual, usar día calendario; si es mes pasado, usar días completos
    const diasTranscurridos = esElMesActual ? hoy.getDate() : diasTotalesMes;

    // Función para calcular proyección mensual
    const calcularProyeccion = (ventas) => {
      if (diasTranscurridos <= 0 || ventas <= 0) return 0;
      return Math.round((ventas / diasTranscurridos) * diasProyectables);
    };

    logger.log(`[COMERCIAL_V2] Proyección: mes=${mesSeleccionado}, diasTranscurridos=${diasTranscurridos}, diasProyectables=${diasProyectables}`);

    // Calcular promedios
    // CORRECCIÓN GLOBAL: Nomenclatura correcta
    // ticket_promedio / cheque_promedio = ventas / tickets
    // pax_promedio = ventas / pax
    const chequePromedio = Number(
      totales.cheque_promedio ?? totales.ticket_promedio ?? 0
    );
    const paxPromedio = Number(totales.pax_promedio || 0);

    // Transformar unidades al formato v1
    // =========================================================================
    // FASE 3 (Junio 2026): V2 es la fuente ÚNICA para Tablero Ejecutivo Comercial
    // - V2 ya devuelve unidad_negocio_codigo oficial desde EDARSAHUB
    // - V2 ya calcula variaciones (var_vs_mes_ant, var_vs_año_ant, etc.)
    // - NO se requiere llamar a V1 para enriquecer
    // - Si variación es null: mostrar "-"
    // - Si variación es 0.0: mostrar "0.0%" (valor real)
    // =========================================================================

    // =========================================================================
    // REGLA CANÓNICA: Proyección usa DiasTranscurridosOperativos GLOBAL
    // ACTUALIZACIÓN 16-May-2026: Usar FechaOperacionActual.day para TODAS las unidades
    // =========================================================================
    // El divisor es el mismo para todas las unidades: diasTranscurridos
    // diasTranscurridos = FechaOperacionActual.day (calculado en backend con corte 06:00 AM)
    //
    // Queda PROHIBIDO usar u.dias (último día con datos de cada unidad)
    // =========================================================================
    // NOTA: calcularProyeccion ya está definida arriba (línea 62-65)

    const unidadesTransformadas = unidades.map(u => ({
      id: u.unidad_negocio_id,
      unidad: u.unidad_negocio_nombre,
      server_id: u.unidad_negocio_id,
      sucursal: null,
      ventas: u.ventas_total || 0,
      propinas: u.propinas_total || 0,
      propinas_total: u.propinas_total || 0,
      pax: u.pax_total || 0,
      cheques: u.tickets_total || 0,
      // CORRECCIÓN GLOBAL: Nomenclatura correcta de KPIs
      // cheque_promedio es alias compatible de ticket_promedio
      cheque_promedio: u.cheque_promedio ?? u.ticket_promedio ?? 0,
      ticket_promedio: u.ticket_promedio ?? 0,
      pax_promedio: u.pax_promedio ?? null,
      // ACTUALIZADO: Usar días GLOBALES (FechaOperacionActual.day), NO u.dias
      proyeccion: u.proyeccion ?? calcularProyeccion(u.ventas_total || 0),
      // FASE 3: Variaciones vienen directamente de V2 (EDARSAHUB)
      // null = sin base comparativa (mostrar "-")
      // 0.0 = variación real cero (mostrar "0.0%")
      var_vs_mes_ant: u.var_vs_mes_ant !== undefined ? u.var_vs_mes_ant : null,
      var_vs_año_ant: u.var_vs_año_ant !== undefined ? u.var_vs_año_ant : null,
      ventas_ant: u.ventas_ant !== undefined ? u.ventas_ant : null,
      ventas_año: u.ventas_año !== undefined ? u.ventas_año : null,
      pax_ant: u.pax_ant !== undefined ? u.pax_ant : null,
      pax_año: u.pax_año !== undefined ? u.pax_año : null,
      cheques_ant: u.cheques_ant !== undefined ? u.cheques_ant : null,
      cheques_año: u.cheques_año !== undefined ? u.cheques_año : null,
      var_pax_mes: u.var_pax_mes !== undefined ? u.var_pax_mes : null,
      var_pax_año: u.var_pax_año !== undefined ? u.var_pax_año : null,
      var_cheques_mes: u.var_cheques_mes !== undefined ? u.var_cheques_mes : null,
      var_cheques_año: u.var_cheques_año !== undefined ? u.var_cheques_año : null,
      // FASE 3: Código canónico viene directamente de V2 (Unidades_Negocio.codigo)
      unidad_negocio_codigo: u.unidad_negocio_codigo || u.unidad_negocio_id,
      unidad_negocio_nombre: u.unidad_negocio_nombre,
      status: 'online',
      data_status: 'DATA_OK',
      live_status: 'LIVE_UNKNOWN',
      source_used: 'EDARSAHUB_V2',
      cache_warning: null,
      error_message: null,
      _v2_fuente: u._v2_fuente || 'EDARSAHUB',
      _v2_tabla: u._v2_tabla || 'Comercial_KPIs_Diarios_v2',
      _variaciones_source: 'V2_EDARSAHUB'  // FASE 3: Marcador de origen
    }));

    // Construir respuesta en formato v1
    // CORRECCIÓN MAYO 2026: Preservar variaciones si V2 las devuelve, si no usar null
    const resultado = {
      periodo: {
        mes: mesSeleccionado,
        anio: anioSeleccionado,
        dias_transcurridos: diasTranscurridos,
        dias_mes: diasProyectables,
        modo_ventas_dia: false
      },
      totales: {
        ventas: totales.ventas_total || 0,
        propinas: totales.propinas_total || 0,
        propinas_total: totales.propinas_total || 0,
        pax: totales.pax_total || 0,
        cheques: totales.tickets_total || 0,
        // CORRECCIÓN GLOBAL: Nomenclatura correcta de promedios
        cheque_promedio: chequePromedio,
        ticket_promedio: chequePromedio,
        pax_promedio: paxPromedio,
        proyeccion: totales.proyeccion ?? calcularProyeccion(totales.ventas_total || 0),
        // CORRECCIÓN: Usar valores de backend si existen, si no null (no 0 falso)
        var_vs_mes_ant: totales.var_vs_mes_ant !== undefined ? totales.var_vs_mes_ant : null,
        var_vs_año_ant: totales.var_vs_año_ant !== undefined ? totales.var_vs_año_ant : null,
        var_pax_mes: totales.var_pax_mes !== undefined ? totales.var_pax_mes : null,
        var_pax_año: totales.var_pax_año !== undefined ? totales.var_pax_año : null,
        var_cheques_mes: totales.var_cheques_mes !== undefined ? totales.var_cheques_mes : null,
        var_cheques_año: totales.var_cheques_año !== undefined ? totales.var_cheques_año : null,
        var_proy_vs_año: totales.var_proy_vs_año !== undefined ? totales.var_proy_vs_año : null,
        ventas_ant: totales.ventas_ant !== undefined ? totales.ventas_ant : null,
        ventas_año: totales.ventas_año !== undefined ? totales.ventas_año : null,
        unidades_año_ant: totales.total_unidades || 0
      },
      unidades: unidadesTransformadas,
      status_summary: {
        unidades_data_ok: unidadesTransformadas.length,
        unidades_live_connected: 0, // v2 no consulta en vivo
        unidades_source_cache: 0,
        unidades_data_error: 0
      },
      _v2_source: true,
      ventas_dia_actual: data.ventas_dia_actual || null,
      _v2_metadata: data.metadata || { source: 'EDARSAHUB_V2' }
    };

    logger.log('[COMERCIAL_V2] Datos transformados correctamente desde EDARSAHUB v2');
    return resultado;

  } catch (error) {
    logger.error('[COMERCIAL_V2] Error transformando respuesta v2:', error);
    throw error;
  }
};

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

// Constantes para meses y años (homologado con Dashboard Comercial)
const MESES = [
  { value: '01', label: 'Enero' },
  { value: '02', label: 'Febrero' },
  { value: '03', label: 'Marzo' },
  { value: '04', label: 'Abril' },
  { value: '05', label: 'Mayo' },
  { value: '06', label: 'Junio' },
  { value: '07', label: 'Julio' },
  { value: '08', label: 'Agosto' },
  { value: '09', label: 'Septiembre' },
  { value: '10', label: 'Octubre' },
  { value: '11', label: 'Noviembre' },
  { value: '12', label: 'Diciembre' }
];


const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  if (num >= 1000000) return `$${(num/1000000).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}M`;
  if (num >= 1000) return `$${(num/1000).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}K`;
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(num);
};

const resolveProjectionPresentation = (data, esMultiMes) => {
  const projection = data?.projection_semantics
    || data?.proyeccion_semantica
    || null;

  if (projection) {
    return {
      enabled: Boolean(projection.enabled),
      status: projection.status || 'NOT_APPLICABLE',
      title: projection.title || 'No aplica',
      subtitle: projection.subtitle || null,
      value: projection.value ?? null,
      comparisonValue: projection.comparison_value ?? null,
      comparisonLabel: projection.comparison_label || null,
    };
  }

  const isCurrentOperation = Boolean(
    data?.periodo?.modo_ventas_dia
  );

  const isHistorical = Boolean(
    data?.periodo?.modo_historico_explicito
  );

  const isDateRange = Boolean(
    data?.periodo?.modo_rango_fechas
  );

  if (isCurrentOperation) {
    return {
      enabled: false,
      status: 'IN_PROGRESS_NO_PROJECTION',
      title: 'Operación en curso',
      subtitle: 'Venta acumulada vigente',
      value: data?.totales?.ventas ?? 0,
      comparisonValue: null,
      comparisonLabel: null,
    };
  }

  if (isHistorical || isDateRange || esMultiMes) {
    return {
      enabled: false,
      status: 'NOT_APPLICABLE',
      title: 'Venta del periodo',
      subtitle: 'Resultado real',
      value: data?.totales?.ventas ?? 0,
      comparisonValue: null,
      comparisonLabel: null,
    };
  }

  const backendProjection = data?.totales?.proyeccion;

  if (
    backendProjection !== null
    && backendProjection !== undefined
  ) {
    return {
      enabled: true,
      status: 'IN_PROGRESS',
      title: 'Proyección del periodo',
      subtitle: 'Calculada por el backend',
      value: backendProjection,
      comparisonValue:
        data?.totales?.var_proy_vs_año ?? null,
      comparisonLabel: 'vs periodo comparable',
    };
  }

  return {
    enabled: false,
    status: 'FINAL',
    title: 'Venta final',
    subtitle: 'Periodo cerrado',
    value: data?.totales?.ventas ?? 0,
    comparisonValue: null,
    comparisonLabel: null,
  };
};


const formatPercent = (num) => {
  // FASE 3 FIX: Distinguir correctamente 0.0 real de null/undefined
  // - null/undefined = sin base comparativa = mostrar "-"
  // - 0 o 0.0 = variación real cero = mostrar "0%" o "0.0%"
  if (num === null || num === undefined) return '-';
  if (num === 0) return '0%';
  const prefix = num > 0 ? '+' : '';
  return `${prefix}${num.toFixed(1)}%`;
};

const VariacionBadge = ({ valor, size = 'sm' }) => {
  // FASE 3 FIX: Distinguir correctamente 0.0 real de null/undefined
  // - null/undefined = sin base comparativa = mostrar "-"
  // - 0 o 0.0 = variación real cero = mostrar "0%" con estilo neutro
  if (valor === null || valor === undefined) {
    return <span className="text-zinc-400">-</span>;
  }

  // Valor 0 real: mostrar "0%" con estilo neutro (ni verde ni rojo)
  if (valor === 0) {
    const sizeClass = size === 'lg' ? 'text-lg font-bold' : 'text-sm font-semibold';
    return <span className={`${sizeClass} text-zinc-500`}>0%</span>;
  }

  const isPositive = valor > 0;
  const sizeClass = size === 'lg' ? 'text-lg font-bold' : 'text-sm font-semibold';
  return (
    <span className={`inline-flex items-center gap-1 ${sizeClass} ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
      {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {formatPercent(valor)}
    </span>
  );
};

// Función para formatear fecha de última actualización
const formatLastUpdate = (isoDate) => {
  if (!isoDate) return '';
  try {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'hace un momento';
    if (diffMins < 60) return `hace ${diffMins} min`;
    if (diffHours < 24) return `hace ${diffHours}h`;

    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return '';
  }
};

// Tarjeta de Unidad clickeable - P0: Usando data_status y live_status separados
const UnidadCard = ({ unidad, onClick, esMultiMes = false, modoVentasDia = false }) => {
  const isPositive = unidad.var_vs_mes_ant >= 0;

  // P0 TAREA 6: Determinar estado visual basado en data_status y live_status
  const dataStatus = unidad.data_status || (unidad.status === 'online' ? 'DATA_OK' : 'DATA_ERROR');
  const liveStatus = unidad.live_status || (unidad.status === 'online' ? 'LIVE_CONNECTED' : 'LIVE_UNKNOWN');
  const sourceUsed = unidad.source_used || (unidad.status === 'online' ? 'REAL_SOURCE' : 'NONE');
  const cacheWarning = unidad.cache_warning;

  // Determinar color del indicador
  const getStatusIndicator = () => {
    // Caso A: DATA_OK + REAL_SOURCE + LIVE_CONNECTED = Verde
    if (dataStatus === 'DATA_OK' && sourceUsed === 'REAL_SOURCE') {
      if (liveStatus === 'LIVE_CONNECTED') {
        return { color: 'bg-green-500', title: 'Datos actualizados desde fuente real' };
      }
      // Caso B/C: DATA_OK pero live no disponible = Verde/Gris
      if (liveStatus === 'LIVE_UNREACHABLE_PREVIEW_ENV') {
        return { color: 'bg-green-400', title: 'Datos del período cargados · Venta en vivo no disponible desde Preview' };
      }
      if (liveStatus === 'LIVE_UNREACHABLE_REAL' || liveStatus === 'LIVE_API_UNREACHABLE') {
        return { color: 'bg-amber-500', title: 'Datos del período cargados · Venta en vivo no disponible' };
      }
    }
    // Caso D: DATA_FROM_CACHE = Amarillo/Gris
    if (dataStatus === 'DATA_FROM_CACHE') {
      return { color: 'bg-amber-400', title: cacheWarning || 'Mostrando último dato disponible (caché)' };
    }
    // Caso E: DATA_ERROR = Rojo
    if (dataStatus === 'DATA_ERROR') {
      return { color: 'bg-red-500 animate-pulse', title: unidad.error_message || 'Error de conexión' };
    }
    // Caso G: NO_DATA_CONFIRMED = Gris
    if (dataStatus === 'NO_DATA_CONFIRMED') {
      return { color: 'bg-zinc-400', title: 'Sin datos confirmados para el período' };
    }
    // Defaul
    return { color: 'bg-zinc-300', title: 'Estado desconocido' };
  };

  const statusIndicator = getStatusIndicator();
  const hasValidData = dataStatus === 'DATA_OK' || dataStatus === 'DATA_FROM_CACHE';
  const isFromCache = dataStatus === 'DATA_FROM_CACHE' || sourceUsed === 'CACHE';
  const hasError = dataStatus === 'DATA_ERROR';

  return (
    <Card
      className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border-2 ${
        isPositive ? 'hover:border-green-400' : 'hover:border-red-400'
      } ${hasError ? 'bg-red-50' : isFromCache ? 'bg-amber-50' : ''}`}
      onClick={() => onClick(unidad)}
      data-testid={`unidad-card-${unidad.server_id}`}
    >
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            {/* P0 TAREA 6: Indicador de estado basado en data_status/live_status */}
            <span
              className={`h-2.5 w-2.5 rounded-full ${statusIndicator.color}`}
              title={statusIndicator.title}
            />
            <h3 className="font-bold text-zinc-800 text-sm truncate max-w-[160px]">{formatNombreSucursal(unidad.unidad)}</h3>
          </div>
          <ChevronRight className="h-4 w-4 text-zinc-400" />
        </div>

        {/* P0 TAREA 6 Caso D: Advertencia de caché visible */}
        {isFromCache && cacheWarning && (
          <div className="mb-2 px-2 py-1 bg-amber-100 rounded text-xs text-amber-700 flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>Datos en caché</span>
          </div>
        )}

        {/* P0 TAREA 6 Caso E: Error controlado */}
        {hasError && (
          <div className="mb-2 px-2 py-1 bg-red-100 rounded text-xs text-red-700 flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            <span className="truncate">{unidad.error_message || 'Error de conexión'}</span>
          </div>
        )}

        {/* P0: Live status secundario si aplica */}
        {hasValidData && liveStatus === 'LIVE_UNREACHABLE_PREVIEW_ENV' && (
          <div className="mb-2 px-2 py-1 bg-zinc-100 rounded text-xs text-zinc-600">
            Venta en vivo no disponible desde Preview
          </div>
        )}

        <div className="space-y-2">
          {/* ============================================================ */}
          {/* BLOQUE PRINCIPAL: Ventas + Proyección                        */}
          {/* FIX UI 15-May-2026: Proyección debajo de Ventas              */}
          {/* ============================================================ */}
          <div className="flex justify-between items-center">
            <span className="text-xs text-zinc-500">Ventas</span>
            <span className={`font-bold ${hasError ? 'text-zinc-400' : 'text-green-600'}`}>
              {hasError && !unidad.ventas ? '-' : formatCurrency(unidad.ventas)}
            </span>
          </div>

          {hasValidData && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-zinc-500">Proyección</span>
              <span className="font-semibold text-orange-600">{formatCurrency(unidad.proyeccion)}</span>
            </div>
          )}

          {/* ============================================================ */}
          {/* BLOQUE COMPARATIVOS: vs Día/Mes Ant. + vs Año Ant.           */}
          {/* ============================================================ */}
          {hasValidData && (
            <div className="border-t pt-2 mt-2 space-y-1">
              {/* Ocultar "vs Mes Ant" cuando hay multiselección de meses */}
              {!esMultiMes && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-zinc-500">{modoVentasDia ? 'vs Día Ant.' : 'vs Mes Ant.'}</span>
                  <VariacionBadge valor={unidad.var_vs_mes_ant} />
                </div>
              )}

              <div className="flex justify-between items-center">
                <span className="text-xs text-zinc-500">{modoVentasDia ? 'vs Día Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Mes Año Ant.')}</span>
                <VariacionBadge valor={unidad.var_vs_año_ant} />
              </div>
            </div>
          )}

          {/* ============================================================ */}
          {/* BLOQUE OPERATIVO: PAX + Cheques en 2 columnas                */}
          {/* FIX UI 15-May-2026: PAX Prom debajo de PAX, Cheque Prom debajo de Cheques */}
          {/* ============================================================ */}
          {hasValidData && (
            <div className="border-t pt-2 mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              {/* Columna izquierda: PAX */}
              <div>
                <span className="text-zinc-500">PAX</span>
                <p className="font-semibold">{unidad.pax?.toLocaleString() ?? '-'}</p>
              </div>
              {/* Columna derecha: Cheques */}
              <div>
                <span className="text-zinc-500">Cheques</span>
                <p className="font-semibold">{unidad.cheques?.toLocaleString() ?? '-'}</p>
              </div>
              {/* Columna izquierda: PAX Promedio */}
              <div>
                <span className="text-zinc-500">PAX Prom.</span>
                <p className="font-semibold">{unidad.pax_promedio ? formatCurrency(unidad.pax_promedio) : '-'}</p>
              </div>
              {/* Columna derecha: Cheque Promedio */}
              <div>
                <span className="text-zinc-500">Cheque Prom.</span>
                <p className="font-semibold">{formatCurrency(unidad.cheque_promedio)}</p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Detalle de Unidad (Drill-down)
const DetalleUnidad = ({ unidad, onClose, mes, anio, modoVentasDia = false }) => {
  const [detalleData, setDetalleData] = useState(null);
  const [loading, setLoading] = useState(true);

  // CORRECCIÓN GLOBAL: Leyendas dinámicas según selector de periodo
  const leyendasComparativo = modoVentasDia
    ? { actual: 'Día Actual', anterior: 'Día Anterior', anioAnt: 'Día Año Ant.' }
    : { actual: 'Mes Actual', anterior: 'Mes Anterior', anioAnt: 'Mes Año Ant.' };

  useEffect(() => {
    const cargarDetalle = async () => {
      setLoading(true);
      try {
        // En modo Ventas del Día, NO hacer llamadas a endpoints legacy (que consultan en vivo)
        // En su lugar, calcular datos desde EDARSAHUB SQL sincronizado
        if (modoVentasDia) {
          // Intentar obtener datos de ventas por día de semana desde el historial
          // Esto usa Comercial_KPIs_Diarios_v2 que ya está sincronizado
          let ventasPorDia = null;

          try {
            // Obtener últimos 7 días de la unidad para mostrar tendencia semanal
            const histResponse = await api.get(`/v2/comercial/kpis-diarios/${unidad.unidad_negocio_id || unidad.id}`, {
              params: { dias: 7 }
            });

            if (histResponse.data?.success && histResponse.data?.data?.length > 0) {
              // Agrupar por día de semana
              const diasSemana = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
              const ventasPorDiaSemana = {};

              histResponse.data.data.forEach(d => {
                const fecha = new Date(d.fecha_operacion);
                const diaNombre = diasSemana[fecha.getDay()];
                if (!ventasPorDiaSemana[diaNombre]) {
                  ventasPorDiaSemana[diaNombre] = { ventas: 0, pax: 0, count: 0 };
                }
                ventasPorDiaSemana[diaNombre].ventas += d.ventas_total || 0;
                ventasPorDiaSemana[diaNombre].pax += d.pax_total || 0;
                ventasPorDiaSemana[diaNombre].count++;
              });

              ventasPorDia = Object.entries(ventasPorDiaSemana).map(([dia, data]) => ({
                dia,
                ventas: data.ventas,
                pax: data.pax
              }));
            }
          } catch (e) {
            logger.warn('[DetalleUnidad] No se pudo obtener historial para día de semana:', e.message);
          }

          setDetalleData({
            dashboard: null,
            ventasTiempo: ventasPorDia ? {
              por_hora: null, // No hay datos de hora sincronizados en EDARSAHUB
              por_dia: ventasPorDia
            } : null,
            mesas: null,
            modoVentasDia: true,
            sinDatosHora: true // Flag para mostrar mensaje informativo
          });
          setLoading(false);
          return;
        }

        // V2 ES FUENTE ÚNICA:
        // No llamar endpoints legacy /comercial/dashboard, /comercial/ventas-tiempo ni /comercial/mesas.
        // El modal conserva KPIs desde la respuesta canónica V2 ya cargada.
        // Sin MongoDB, sin live, sin fuentes paralelas.
        setDetalleData({
          dashboard: null,
          ventasTiempo: null,
          mesas: null,
          modoVentasDia: false,
          fuente: 'EDARSAHUB_SQL_V2',
          sinLegacy: true
        });
      } catch (error) {
        logger.error('Error cargando detalle:', error);
        // Establecer datos vacíos para que el modal siga funcionando
        setDetalleData({
          dashboard: null,
          ventasTiempo: null,
          mesas: null
        });
      } finally {
        setLoading(false);
      }
    };

    // CORRECCIÓN: En modo Ventas del Día, cargar inmediatamente sin server_id
    if (modoVentasDia || unidad?.server_id) {
      cargarDetalle();
    } else {
      // Sin server_id y sin modo diario, mostrar datos básicos
      setDetalleData({
        dashboard: null,
        ventasTiempo: null,
        mesas: null
      });
      setLoading(false);
    }
  }, [unidad, modoVentasDia]);

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {formatNombreSucursal(unidad.unidad)}
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* KPIs principales */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Card className="bg-green-50 border-green-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="text-xs text-zinc-600">Ventas</span>
                  </div>
                  <p className="text-xl font-bold text-green-600">{formatCurrency(unidad.ventas)}</p>
                  <div className="flex justify-center gap-2 mt-1">
                    <span className="text-xs">{leyendasComparativo.anterior}: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>
                    <span className="text-xs">{leyendasComparativo.anioAnt}: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Users className="h-4 w-4 text-blue-600" />
                    <span className="text-xs text-zinc-600">PAX</span>
                  </div>
                  <p className="text-xl font-bold text-blue-600">{unidad.pax?.toLocaleString()}</p>
                  <p className="text-xs text-zinc-500">Pax Prom: {formatCurrency(unidad.pax_promedio)}</p>
                  <div className="flex justify-center gap-2 mt-1">
                    {/* CORRECCIÓN: Etiquetas dinámicas según selector */}
                    <span className="text-xs">{leyendasComparativo.anterior}: <VariacionBadge valor={unidad.var_pax_mes} /></span>
                    <span className="text-xs">{leyendasComparativo.anioAnt}: <VariacionBadge valor={unidad.var_pax_año} /></span>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-purple-50 border-purple-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Receipt className="h-4 w-4 text-purple-600" />
                    <span className="text-xs text-zinc-600">Cheques</span>
                  </div>
                  <p className="text-xl font-bold text-purple-600">{unidad.cheques?.toLocaleString()}</p>
                  <p className="text-xs text-zinc-500">Cheque Prom: {formatCurrency(unidad.cheque_promedio)}</p>
                  <div className="flex justify-center gap-2 mt-1">
                    {/* CORRECCIÓN: Etiquetas dinámicas según selector */}
                    <span className="text-xs">{leyendasComparativo.anterior}: <VariacionBadge valor={unidad.var_cheques_mes} /></span>
                    <span className="text-xs">{leyendasComparativo.anioAnt}: <VariacionBadge valor={unidad.var_cheques_año} /></span>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-orange-50 border-orange-200">
                <CardContent className="p-3 text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Target className="h-4 w-4 text-orange-600" />
                    <span className="text-xs text-zinc-600">{modoVentasDia ? 'Resumen' : 'Proyección'}</span>
                  </div>
                  <p className="text-xl font-bold text-orange-600">{formatCurrency(modoVentasDia ? unidad.ventas : unidad.proyeccion)}</p>
                  <p className="text-xs text-zinc-500">{modoVentasDia ? 'Día actual' : 'Mes completo'}</p>
                  <div className="flex justify-center gap-2 mt-1">
                    <span className="text-xs">{modoVentasDia ? 'vs Día Ant:' : 'vs Mes:'} <VariacionBadge valor={unidad.ventas_ant > 0 ? (((modoVentasDia ? unidad.ventas : unidad.proyeccion) - unidad.ventas_ant) / unidad.ventas_ant * 100) : 0} /></span>
                    <span className="text-xs">{modoVentasDia ? 'vs Año Ant:' : 'vs Año:'} <VariacionBadge valor={unidad.ventas_año > 0 ? (((modoVentasDia ? unidad.ventas : unidad.proyeccion) - unidad.ventas_año) / unidad.ventas_año * 100) : 0} /></span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Comparativo - CORRECCIÓN GLOBAL: Leyendas dinámicas según selector */}
            <Card>
              <CardHeader className="py-2 bg-zinc-100">
                <CardTitle className="text-sm">Comparativo</CardTitle>
              </CardHeader>
              <CardContent className="p-3">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-xs text-zinc-500">{leyendasComparativo.actual}</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas || 0)}</p>
                    <p className="text-xs text-purple-600">{unidad.pax || 0} pax</p>
                    <p className="text-xs">{unidad.cheques || 0} cheques</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">{leyendasComparativo.anterior}</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas_ant || 0)}</p>
                    <p className="text-xs text-purple-600">{unidad.pax_ant || 0} pax</p>
                    <p className="text-xs">{unidad.cheques_ant || 0} cheques</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500">{leyendasComparativo.anioAnt}</p>
                    <p className="font-bold text-lg">{formatCurrency(unidad.ventas_año || 0)}</p>
                    <p className="text-xs text-purple-600">{unidad.pax_año || 0} pax</p>
                    <p className="text-xs">{unidad.cheques_año || 0} cheques</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Ventas por Hora */}
            {detalleData?.ventasTiempo?.por_hora?.length > 0 ? (
              <Card>
                <CardHeader className="py-2 bg-zinc-100">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Ventas por Hora (Top 6)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                    {detalleData.ventasTiempo.por_hora.slice(0, 6).map((h) => (
                      <div key={`hora-${h.hora}`} className="text-center p-2 bg-zinc-50 rounded">
                        <p className="font-bold text-sm">{h.hora}</p>
                        <p className="text-xs text-green-600">{formatCurrency(h.ventas)}</p>
                        <p className="text-xs text-zinc-500">{h.pax} pax</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : detalleData?.sinDatosHora && (
              <Card>
                <CardHeader className="py-2 bg-zinc-100">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Ventas por Hora
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <p className="text-sm text-zinc-500 text-center py-4">
                    Sin datos de hora sincronizados para Ventas del Día
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Ventas por Día */}
            {detalleData?.ventasTiempo?.por_dia?.length > 0 && (
              <Card>
                <CardHeader className="py-2 bg-zinc-100">
                  <CardTitle className="text-sm">Ventas por Día de Semana</CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="grid grid-cols-7 gap-1">
                    {(() => {
                      // Asegurar que siempre tengamos los 7 días de la semana (Lunes a Domingo)
                      const diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
                      const diasMap = {};
                      detalleData.ventasTiempo.por_dia.forEach(d => {
                        const diaKey = d.dia.substring(0, 3);
                        diasMap[diaKey] = d;
                      });

                      const diasCompletos = diasSemana.map(dia => ({
                        dia: dia,
                        ventas: diasMap[dia]?.ventas || 0,
                        pax: diasMap[dia]?.pax || 0
                      }));

                      const maxVenta = Math.max(...diasCompletos.map(x => x.ventas), 1);

                      return diasCompletos.map((d) => {
                        const height = (d.ventas / maxVenta * 60) + 20;
                        return (
                          <div key={`dia-${d.dia}`} className="text-center">
                            <div
                              className={`rounded-t mx-auto w-8 transition-all ${d.ventas > 0 ? 'bg-blue-500' : 'bg-zinc-200'}`}
                              style={{ height: `${height}px` }}
                            />
                            <p className="text-xs font-medium mt-1">{d.dia}</p>
                            <p className="text-xs text-zinc-500">{formatCurrency(d.ventas)}</p>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default function TableroEjecutivo() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  // Selector temporal canónico.
  // Ventas del Día es un modo explícito, no un año ficticio.
  const [temporalSelection, setTemporalSelection] = useState(() => {
    const saved = localStorage.getItem('tablero_periodo_canonico_v1');

    if (saved) {
      try {
        const parsed = JSON.parse(saved);

        if (
          parsed
          && Object.values(TEMPORAL_MODES).includes(parsed.mode)
        ) {
          return parsed;
        }
      } catch (error) {
        logger.warn(
          '[PERIODOS] Selección temporal almacenada inválida',
          error
        );
      }
    }

    return {
      mode: TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY,
    };
  });

  const [periodAvailability, setPeriodAvailability] = useState(null);
  const [periodAvailabilityLoading, setPeriodAvailabilityLoading] = useState(true);
  const [periodAvailabilityError, setPeriodAvailabilityError] = useState(null);

  const [tipoComparacion, setTipoComparacion] = useState('dias_equiv');

  const [unidadSeleccionada, setUnidadSeleccionada] = useState(null);

  // P0 TAREA 1 & 4: Control de request_id y TTL para evitar race conditions
  const [lastRefreshTime, setLastRefreshTime] = useState(null);
  const [requestId, setRequestId] = useState(0);
  const [latestRequestId, setLatestRequestId] = useState(0); // Para validar respuestas
  // FIX race condition: useRef se actualiza de forma SÍNCRONA (el estado en el closure
  // quedaba obsoleto y descartaba respuestas válidas como 'stale_request').
  const latestRequestIdRef = useRef(0);
  const [refreshError, setRefreshError] = useState(null); // Error sin borrar datos
  const STATUS_TTL_SECONDS = 120; // TTL de 2 minutos para considerar datos stale

  useEffect(() => {
    localStorage.setItem(
      'tablero_periodo_canonico_v1',
      JSON.stringify(temporalSelection)
    );
  }, [temporalSelection]);

  useEffect(() => {
    let active = true;

    const cargarDisponibilidadTemporal = async () => {
      setPeriodAvailabilityLoading(true);
      setPeriodAvailabilityError(null);

      try {
        const response = await api.get(
          '/v2/comercial/periodos/disponibles',
          { timeout: 30000 }
        );

        if (!response.data?.success) {
          throw new Error(
            'Respuesta no exitosa de periodos disponibles'
          );
        }

        if (active) {
          setPeriodAvailability(response.data.data || null);
        }
      } catch (error) {
        logger.error(
          '[PERIODOS] Error cargando disponibilidad temporal',
          error
        );

        if (active) {
          setPeriodAvailabilityError(
            'No fue posible cargar los periodos disponibles'
          );
        }
      } finally {
        if (active) {
          setPeriodAvailabilityLoading(false);
        }
      }
    };

    cargarDisponibilidadTemporal();

    return () => {
      active = false;
    };
  }, []);

  const esVentasDelDia = (
    temporalSelection.mode
    === TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY
  );

  const esRangoFechas = (
    temporalSelection.mode
    === TEMPORAL_MODES.DATE_RANGE
  );

  const esHistoricoExplicito = (
    temporalSelection.mode
    === TEMPORAL_MODES.HISTORICAL_PERIODS
  );

  const periodosHistoricos = (
    Array.isArray(temporalSelection.periods)
      ? temporalSelection.periods
      : []
  );

  const selectedAnios = periodosHistoricos.map(
    periodo => String(periodo.year)
  );

  const selectedMeses = [
    ...new Set(
      periodosHistoricos.flatMap(
        periodo => periodo.months || []
      )
    ),
  ].map(
    mes => String(mes).padStart(2, '0')
  );

  const esMultiMes = (
    esHistoricoExplicito
    && periodosHistoricos.reduce(
      (total, periodo) => total + (periodo.months?.length || 0),
      0
    ) > 1
  );


  const cargarDatos = useCallback(async (retry = 0, forceRefresh = false) => {
    // =========================================================================
    // PROTECCIÓN RACE CONDITION: requestId incremental
    // Solo aplicar respuesta si requestId === latestRequestId
    // =========================================================================
    const currentRequestId = latestRequestIdRef.current + 1;
    latestRequestIdRef.current = currentRequestId; // síncrono: refleja el request más reciente
    setRequestId(currentRequestId);
    setLatestRequestId(currentRequestId);
    setRefreshError(null); // Limpiar error previo

    // REGLA: Loading NO limpia datos existentes
    if (retry === 0) {
      setLoading(true);
      logger.log(`[REFRESH_LOG] START: requestId=${currentRequestId}, forceRefresh=${forceRefresh}, dataExists=${!!data}, source=V2_ONLY`);
    }

    try {
      let responseData = null;
      let usedV2 = false;

      // =========================================================================
      // V2 ES FUENTE ÚNICA - NO HAY FALLBACK A V1 NI MONGO
      // =========================================================================
      if (USE_COMERCIAL_V2) {
        try {
          if (esVentasDelDia) {
            logger.log(
              '[COMERCIAL_ANALYTICS] Consultando operación en curso canónica...'
            );

            const operationResponse = await api.get(
              '/v2/comercial/analytics/operacion-en-curso',
              {
                timeout: 30000,
              }
            );

            if (!operationResponse.data?.success) {
              throw new Error(
                'Respuesta de operación en curso no exitosa'
              );
            }

            const operationData = operationResponse.data.data || {};
            const operationTotals = (
              operationData.totales?.operacion_estimada || {}
            );
            const closedTotals = (
              operationData.totales?.cerradas || {}
            );
            const openTotals = (
              operationData.totales?.abiertas || {}
            );
            const operationItems = Array.isArray(operationData.items)
              ? operationData.items
              : [];

            const totalSales = Number(operationTotals.ventas || 0);
            const totalChecks = Number(operationTotals.cheques || 0);
            const totalPax = Number(operationTotals.pax || 0);

            const checkAverage = (
              totalChecks > 0 ? totalSales / totalChecks : 0
            );
            const paxAverage = (
              totalPax > 0 ? totalSales / totalPax : 0
            );

            const effectiveDates = Array.isArray(
              operationData.fechas_operacion
            )
              ? operationData.fechas_operacion
              : [];

            const singleEffectiveDate = (
              !operationData.fecha_operacion_multiple
                ? (
                  operationData.fecha_operacion
                  || effectiveDates[0]
                  || null
                )
                : null
            );

            const effectiveDateParts = (
              singleEffectiveDate
                ? String(singleEffectiveDate)
                  .slice(0, 10)
                  .split('-')
                  .map(Number)
                : []
            );

            responseData = {
              totales: {
                ventas: totalSales,
                ventas_cerradas: Number(closedTotals.ventas || 0),
                ventas_abiertas: Number(openTotals.ventas || 0),
                propinas: Number(operationTotals.propinas || 0),
                pax: totalPax,
                cheques: totalChecks,
                cheque_promedio: checkAverage,
                ticket_promedio: checkAverage,
                pax_promedio: paxAverage,
                var_vs_mes_ant: null,
                var_vs_año_ant: null,
                proyeccion: null,
              },
              periodo: {
                mes: effectiveDateParts[1] || null,
                anio: effectiveDateParts[0] || null,
                dias_transcurridos: null,
                dias_mes: null,
                modo_ventas_dia: true,
                fecha_operacion: singleEffectiveDate,
                fechas_operacion: effectiveDates,
                fecha_operacion_multiple: Boolean(
                  operationData.fecha_operacion_multiple
                ),
              },
              unidades: operationItems
                .slice()
                .sort(
                  (a, b) => (
                    Number(b.operacion_estimada?.ventas || 0)
                    - Number(a.operacion_estimada?.ventas || 0)
                  )
                )
                .map((item) => {
                  const estimated = item.operacion_estimada || {};
                  const closed = item.cerradas || {};
                  const opened = item.abiertas || {};

                  const unitSales = Number(estimated.ventas || 0);
                  const unitChecks = Number(estimated.cheques || 0);
                  const unitPax = Number(estimated.pax || 0);

                  const unitCheckAverage = (
                    unitChecks > 0 ? unitSales / unitChecks : 0
                  );
                  const unitPaxAverage = (
                    unitPax > 0 ? unitSales / unitPax : 0
                  );

                  return {
                    unidad_negocio_id: item.unidad_negocio_id,
                    id: item.unidad_negocio_id,
                    sucursal_id: item.unidad_negocio_id,
                    sucursal_nombre: item.unidad_negocio_nombre,
                    unidad_negocio_codigo: item.unidad_negocio_id,
                    unidad: item.unidad_negocio_nombre,
                    fecha_operacion: item.fecha_operacion,

                    ventas: unitSales,
                    ventas_cerradas: Number(closed.ventas || 0),
                    ventas_abiertas: Number(opened.ventas || 0),

                    propinas: Number(estimated.propinas || 0),
                    propinas_cerradas: Number(closed.propinas || 0),
                    propinas_abiertas: Number(opened.propinas || 0),

                    pax: unitPax,
                    pax_cerrados: Number(closed.pax || 0),
                    pax_abiertos: Number(opened.pax || 0),

                    cheques: unitChecks,
                    cheques_cerrados: Number(closed.cheques || 0),
                    cheques_abiertos: Number(opened.cheques || 0),

                    cheque_promedio: unitCheckAverage,
                    ticket_promedio: unitCheckAverage,
                    pax_promedio: unitPaxAverage,

                    proyeccion: null,
                    ventas_ant: 0,
                    pax_ant: 0,
                    cheques_ant: 0,
                    ventas_año: 0,
                    pax_año: 0,
                    cheques_año: 0,
                    var_vs_mes_ant: null,
                    var_vs_año_ant: null,

                    data_status: 'DATA_OK',
                    live_status: 'OPERATIONAL',
                    source_used: 'COMERCIAL_ANALYTICS_OPERATION',
                    _fuente: 'COMERCIAL_ANALYTICS_OPERATION',
                  };
                }),
              operacion_en_curso: {
                fecha_operacion: singleEffectiveDate,
                fechas_operacion: effectiveDates,
                fecha_operacion_multiple: Boolean(
                  operationData.fecha_operacion_multiple
                ),
                cerradas: closedTotals,
                abiertas: openTotals,
                operacion_estimada: operationTotals,
                unidades_sin_fecha_operativa: (
                  operationData.unidades_sin_fecha_operativa || []
                ),
                trazabilidad: operationData.traceability || {},
              },
              _v2_source: true,
              _operacion_canonica: true,
            };

            usedV2 = true;

            logger.log(
              `[OPERACION_EN_CURSO] Cargadas ${
                responseData.unidades.length
              } unidades; fechas=${
                effectiveDates.join(',') || 'SIN_FECHA'
              }`
            );

          } else if (esRangoFechas) {
            const fechaInicio = temporalSelection.startDate;
            const fechaFin = temporalSelection.endDate;

            if (!fechaInicio || !fechaFin) {
              throw new Error(
                'El rango temporal no tiene fecha inicial y final'
              );
            }

            logger.log(
              `[COMERCIAL_V2] Consultando rango ${fechaInicio} a ${fechaFin}`
            );

            const v2Response = await api.get(
              '/v2/comercial/dashboard',
              {
                params: {
                  fecha_inicio: fechaInicio,
                  fecha_fin: fechaFin,
                },
                timeout: 30000,
              }
            );

            if (!v2Response.data?.success) {
              throw new Error('Respuesta de rango no exitosa');
            }

            const startDate = new Date(`${fechaInicio}T12:00:00`);

            responseData = transformV2ToV1Format(
              v2Response.data,
              [String(startDate.getMonth() + 1).padStart(2, '0')],
              [String(startDate.getFullYear())],
              logger
            );

            responseData.periodo = {
              ...(responseData.periodo || {}),
              fecha_inicio: fechaInicio,
              fecha_fin: fechaFin,
              modo_ventas_dia: false,
              modo_rango_fechas: true,
            };

            if (responseData.unidades?.length > 0) {
              responseData.unidades.sort(
                (a, b) => (b.ventas || 0) - (a.ventas || 0)
              );
            }

            usedV2 = true;
            responseData._v2_source = true;

          } else if (esHistoricoExplicito) {
            if (periodosHistoricos.length === 0) {
              throw new Error(
                'No existen periodos históricos seleccionados'
              );
            }

            logger.log(
              '[COMERCIAL_V2] Consultando periodos históricos explícitos'
            );

            const historicalResponse = await api.post(
              '/v2/comercial/periodos/agregado',
              {
                periodos: periodosHistoricos.map(periodo => ({
                  anio: periodo.year,
                  meses: periodo.months,
                })),
              },
              { timeout: 30000 }
            );

            if (!historicalResponse.data?.success) {
              throw new Error(
                'Respuesta histórica multianual no exitosa'
              );
            }

            const historicalData = historicalResponse.data.data || {};
            const totals = historicalData.totales || {};
            const units = historicalData.unidades || [];
            const firstPeriod = periodosHistoricos[0] || {};
            const firstMonth = firstPeriod.months?.[0] || 1;

            responseData = {
              totales: {
                ventas: totals.ventas_total || 0,
                propinas: totals.propinas_total || 0,
                propinas_total: totals.propinas_total || 0,
                pax: totals.pax_total || 0,
                cheques: totals.tickets_total || 0,
                cheque_promedio: totals.cheque_promedio || 0,
                ticket_promedio: totals.ticket_promedio || 0,
                pax_promedio: totals.pax_promedio || 0,
                proyeccion: null,
                var_vs_mes_ant: null,
                var_vs_año_ant: null,
              },
              periodo: {
                mes: firstMonth,
                anio: firstPeriod.year,
                fecha_inicio: totals.fecha_min || null,
                fecha_fin: totals.fecha_max || null,
                dias_transcurridos: totals.dias || 0,
                dias_mes: totals.dias || 0,
                modo_ventas_dia: false,
                modo_historico_explicito: true,
                periodos_seleccionados:
                  historicalData.periodos_seleccionados || [],
              },
              unidades: units.map(unidad => ({
                id:
                  unidad.unidad_negocio_pk
                  || unidad.unidad_negocio_codigo,
                unidad_negocio_id:
                  unidad.unidad_negocio_pk
                  || unidad.unidad_negocio_codigo,
                unidad_negocio_codigo:
                  unidad.unidad_negocio_codigo,
                unidad_negocio_nombre:
                  unidad.unidad_negocio_nombre,
                unidad:
                  unidad.unidad_negocio_nombre
                  || unidad.unidad_negocio_codigo,
                sucursal_nombre:
                  unidad.unidad_negocio_nombre,
                sistema_tipo: unidad.sistema_origen,
                ventas: unidad.ventas_total || 0,
                propinas: unidad.propinas_total || 0,
                propinas_total: unidad.propinas_total || 0,
                pax: unidad.pax_total || 0,
                cheques: unidad.tickets_total || 0,
                cheque_promedio:
                  unidad.cheque_promedio || 0,
                ticket_promedio:
                  unidad.ticket_promedio || 0,
                pax_promedio:
                  unidad.pax_promedio || 0,
                proyeccion: null,
                var_vs_mes_ant: null,
                var_vs_año_ant: null,
                data_status: 'DATA_OK',
                source_used: 'EDARSAHUB_SQL_V2',
                _fuente: 'EDARSAHUB_SQL_V2',
              })),
              _v2_source: true,
              _historical_periods: true,
            };

            responseData.unidades.sort(
              (a, b) => (b.ventas || 0) - (a.ventas || 0)
            );

            usedV2 = true;

          } else {
            throw new Error(
              `Modo temporal no soportado: ${temporalSelection.mode}`
            );
          }

        } catch (v2Error) {
          logger.error(`[COMERCIAL_V2] Error V2: ${v2Error.message}`);
          throw v2Error; // NO hay fallback, propagar error
        }
      } else {
        // V2 deshabilitado - error
        throw new Error('V2 deshabilitado. No hay fuente de datos alternativa.');
      }

      // =========================================================================
      // VALIDACIÓN RACE CONDITION: Solo aplicar si es el request más reciente
      // =========================================================================
      if (currentRequestId !== latestRequestIdRef.current) {
        logger.log(`[REFRESH_LOG] IGNORED_STALE: requestId=${currentRequestId}, latestRequestId=${latestRequestIdRef.current}, applied=false, reason=stale_request`);
        setLoading(false);
        return;
      }

      // =========================================================================
      // PROTECCIÓN CONTRA CEROS: No sobrescribir datos válidos con respuesta vacía
      // Si: source=V2, unidades.length > 0, pero totales=0 y ya hay datos > 0
      // =========================================================================
      const newVentasTotal = responseData?.totales?.ventas || 0;
      const newPaxTotal = responseData?.totales?.pax || 0;
      const newChequesTotal = responseData?.totales?.cheques || 0;
      const newUnidadesCount = responseData?.unidades?.length || 0;
      const existingVentasTotal = data?.totales?.ventas || 0;

      const isResponseEmpty = newVentasTotal === 0 && newPaxTotal === 0 && newChequesTotal === 0;
      const hasUnidadesButEmpty = newUnidadesCount > 0 && isResponseEmpty;
      const existingDataHasValue = existingVentasTotal > 0;

      if (hasUnidadesButEmpty && existingDataHasValue && responseData?._v2_source) {
        // BLOQUEAR: No sobrescribir datos válidos con ceros
        logger.warn(`[REFRESH_LOG] BLOCKED_ZERO_OVERWRITE: requestId=${currentRequestId}, newVentas=${newVentasTotal}, existingVentas=${existingVentasTotal}, unidades=${newUnidadesCount}, applied=false, reason=v2_returned_zeros_existing_data_valid`);
        setRefreshError('Respuesta V2 vacía detectada. Manteniendo datos anteriores.');
        toast.warning('La actualización devolvió datos vacíos. Se mantienen los datos anteriores.', { duration: 4000 });
        setLoading(false);
        return;
      }

      // =========================================================================
      // APLICAR DATOS: Respuesta válida
      // =========================================================================
      setData(responseData);
      setLastRefreshTime(new Date());
      setRefreshError(null);

      logger.log(`[REFRESH_LOG] APPLIED: requestId=${currentRequestId}, ventasTotal=${newVentasTotal}, unidades=${newUnidadesCount}, source=V2, applied=true, reason=valid_response`);
      setLoading(false);

    } catch (error) {
      logger.error('Error cargando tablero:', error);
      const statusCode = error.response?.status;

      // =========================================================================
      // VALIDACIÓN RACE CONDITION EN ERROR
      // =========================================================================
      if (currentRequestId !== latestRequestId) {
        logger.log(`[REFRESH_LOG] ERROR_IGNORED_STALE: requestId=${currentRequestId}, error=${error.message}, applied=false, reason=stale_request`);
        setLoading(false);
        return;
      }

      if (statusCode === 401) {
        clearSession();
        window.location.href = '/login';
        setLoading(false);
      } else if (retry < 2 && statusCode !== 404 && statusCode !== 502 && statusCode !== 503) {
        logger.log(`Reintentando (${retry + 1}/2)...`);
        setTimeout(() => cargarDatos(retry + 1, forceRefresh), 1000);
        // REGLA: No apagar loading durante reintentos, NO limpiar datos
      } else {
        // =========================================================================
        // ERROR FINAL: NO usar fallback, NO limpiar datos
        // V2 es fuente única - si falla, mantener datos anteriores
        // =========================================================================
        const errorMsg = `Error al actualizar: ${error.message || 'Conexión no disponible'}`;
        setRefreshError(errorMsg);

        // NO setData(null) - mantener datos anteriores
        // Sin fallback con cifras inventadas (eliminado 2026-06-09): V2 es fuente única.

        logger.warn(`[REFRESH_LOG] ERROR_PRESERVED_DATA: requestId=${currentRequestId}, statusCode=${statusCode}, error=${error.message}, existingDataPreserved=${!!data}, applied=false, reason=error_no_fallback`);

        if (data) {
          toast.error('Error al actualizar. Se mantienen los datos anteriores.', { duration: 5000 });
        } else {
          toast.error('No se pudieron cargar los datos. Intente nuevamente.', { duration: 5000 });
        }

        setLoading(false);
      }
    }
  }, [temporalSelection, tipoComparacion, requestId, latestRequestId, esVentasDelDia, esRangoFechas, esHistoricoExplicito, data]);

  // P0 TAREA 1: Carga inicial
  useEffect(() => {
    logger.log('[P0-LOG] tablero_init: Carga inicial del tablero');
    cargarDatos(0, true);
  }, []);  // Solo en montaje inicial

  // P0 TAREA 1: Recargar cuando cambien los filtros
  useEffect(() => {
    if (lastRefreshTime) {  // Solo si ya hubo una carga inicial
      logger.log('[P0-LOG] tablero_filters_changed: Recargando por cambio de filtros');
      cargarDatos(0, true);
    }
  }, [temporalSelection, tipoComparacion]);

  // P0 TAREA 1: Refresco automático cuando la página vuelve a ser visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Verificar si los datos están stale (más de TTL segundos)
        if (lastRefreshTime) {
          const secondsSinceRefresh = (new Date() - lastRefreshTime) / 1000;
          if (secondsSinceRefresh > STATUS_TTL_SECONDS) {
            logger.log(`[P0-LOG] tablero_visibilitychange_refresh: Datos stale (${Math.round(secondsSinceRefresh)}s), refrescando`);
            cargarDatos(0, true);
          } else {
            logger.log(`[P0-LOG] tablero_visible: Datos frescos (${Math.round(secondsSinceRefresh)}s < ${STATUS_TTL_SECONDS}s TTL)`);
          }
        } else {
          logger.log('[P0-LOG] tablero_visible: Sin datos previos, cargando');
          cargarDatos(0, true);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [lastRefreshTime, cargarDatos]);

  return (
    <div className="space-y-4" data-testid="tablero-ejecutivo">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-zinc-800">Tablero Ejecutivo</h1>
        <p className="text-sm text-zinc-500">Vista consolidada para directivos • Clic en unidad para detalle</p>
      </div>

      {/* Tabs de Sub-tableros */}
      <Tabs defaultValue="comercial" className="w-full">
        <TabsList className="grid w-full max-w-2xl mx-auto grid-cols-4 mb-4">
          <TabsTrigger value="comercial" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Comercial
          </TabsTrigger>
          <TabsTrigger value="finanzas" className="flex items-center gap-2" disabled>
            <Wallet className="h-4 w-4" />
            Finanzas
          </TabsTrigger>
          <TabsTrigger value="rh" className="flex items-center gap-2" disabled>
            <UserCircle className="h-4 w-4" />
            RH
          </TabsTrigger>
          <TabsTrigger value="bsc" className="flex items-center gap-2" disabled>
            <Award className="h-4 w-4" />
            BSC
          </TabsTrigger>
        </TabsList>

        {/* Tab Comercial (Actual) */}
        <TabsContent value="comercial">
          {/* Filtros - Homologados con Dashboard Comercial */}
          <Card className="border bg-white">
            <CardContent className="py-3">
              <div className="flex items-center gap-4 flex-wrap">
                <CanonicalPeriodSelector
                  value={temporalSelection}
                  availability={periodAvailability}
                  loading={periodAvailabilityLoading}
                  onChange={setTemporalSelection}
                  className="flex-1 min-w-[260px] max-w-[520px]"
                />

                {periodAvailabilityError && (
                  <span className="text-xs text-amber-600">
                    {periodAvailabilityError}
                  </span>
                )}

                <Button
                  onClick={() => {
                    // P0 TAREA 7: Forzar recarga contra fuente real
                    logger.log('[P0-LOG] tablero_manual_refresh: Botón Actualizar presionado');
                    cargarDatos(0, true);
                  }}
                  disabled={loading}
                  size="sm"
                  className="mt-5"
                  data-testid="tablero-btn-actualizar"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                  Actualizar
                </Button>
                {data?.periodo && (
                  <span className="text-xs text-zinc-500 ml-auto bg-zinc-100 px-2 py-1 rounded mt-5">
                    {data.periodo.modo_ventas_dia ? (
                      <span className="text-amber-600 font-medium">
                        🔴 Ventas del Día (sin corte)
                      </span>
                    ) : data.periodo.modo_rango_fechas ? (
                      <span>
                        {data.periodo.fecha_inicio}
                        {' – '}
                        {data.periodo.fecha_fin}
                      </span>
                    ) : data.periodo.modo_historico_explicito ? (
                      <span>
                        {data.periodo.periodos_seleccionados?.reduce(
                          (total, periodo) => (
                            total + (periodo.meses?.length || 0)
                          ),
                          0
                        ) || 0}
                        {' meses históricos'}
                      </span>
                    ) : (
                      `${data.periodo.mes
                        ? MESES.find(
                          m => m.value === String(
                            data.periodo.mes
                          ).padStart(2, '0')
                        )?.label
                        : ''
                      } ${data.periodo.anio}`
                    )}
                    {/* P0: Mostrar timestamp de última actualización */}
                    {lastRefreshTime && (
                      <span className="ml-2 text-zinc-400">
                        • {formatLastUpdate(lastRefreshTime.toISOString())}
                      </span>
                    )}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

      {/* Banner de Error de Refresh (sin borrar datos) */}
      {refreshError && data && (
        <Card className="border-2 border-amber-400 bg-amber-50">
          <CardContent className="py-3 px-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <div>
                <p className="text-sm font-medium text-amber-800">{refreshError}</p>
                <p className="text-xs text-amber-600">Los datos mostrados son de la última actualización exitosa.</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="border-amber-500 text-amber-700 hover:bg-amber-100"
              onClick={() => {
                setRefreshError(null);
                cargarDatos(0, true);
              }}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Reintentar
            </Button>
          </CardContent>
        </Card>
      )}

      {/* TOTALES - Vista Ejecutiva Grande */}
      {data?.totales && (
        <Card className="border-2 border-zinc-300 bg-gradient-to-br from-zinc-900 to-zinc-800 text-white">
          <CardContent className="py-6">
            {/* P0-AUTH-COOKIE-FRONTEND-01: Mostrar error si hay falla de API */}
            {data.error ? (
              <div className="text-center py-8">
                <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
                <p className="text-lg font-semibold text-amber-400">Error de Conexión</p>
                <p className="text-sm text-zinc-400 mt-2">{data.errorMessage || 'No se pudieron cargar los datos'}</p>
                <Button
                  variant="outline"
                  className="mt-4 border-amber-500 text-amber-400 hover:bg-amber-500/10"
                  onClick={() => cargarDatos()}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reintentar
                </Button>
              </div>
            ) : (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              {/* Ventas Consolidadas */}
              <div className="col-span-2 md:col-span-1 flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">{data?.periodo?.modo_ventas_dia ? 'Ventas del Día' : 'Acumulado Cerrado'}</p>
                <p className="text-3xl font-bold text-green-400">{data.totales.ventas != null ? formatCurrency(data.totales.ventas) : 'Sin datos'}</p>
                <p className="text-xs text-zinc-400 mt-1">&nbsp;</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  {!esMultiMes && (
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Día Ant.' : 'vs Mes'}</span>
                      <p className={`font-bold ${data.totales.var_vs_mes_ant >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPercent(data.totales.var_vs_mes_ant)}
                      </p>
                    </div>
                  )}
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Día Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Mes Año Ant.')}</span>
                    <p className={`font-bold ${data.totales.var_vs_año_ant >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_vs_año_ant)}
                    </p>
                  </div>
                </div>
              </div>

              {/* PAX Total */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">PAX Total</p>
                <p className="text-2xl font-bold">{data.totales.pax?.toLocaleString()}</p>
                <p className="text-xs text-zinc-400 mt-1">Pax Prom: {formatCurrency(data.totales.pax_promedio ?? 0)}</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  {!esMultiMes && (
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Día Ant.' : 'vs Mes'}</span>
                      <p className={`text-sm font-bold ${(data.totales.var_pax_mes || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPercent(data.totales.var_pax_mes)}
                      </p>
                    </div>
                  )}
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Día Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Mes Año Ant.')}</span>
                    <p className={`text-sm font-bold ${(data.totales.var_pax_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_pax_año)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Cheques */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Cheques</p>
                <p className="text-2xl font-bold">{data.totales.cheques?.toLocaleString()}</p>
                <p className="text-xs text-zinc-400 mt-1">Cheque Prom: {formatCurrency(data.totales.cheque_promedio ?? 0)}</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  {!esMultiMes && (
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Día Ant.' : 'vs Mes'}</span>
                      <p className={`text-sm font-bold ${(data.totales.var_cheques_mes || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPercent(data.totales.var_cheques_mes)}
                      </p>
                    </div>
                  )}
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Día Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Mes Año Ant.')}</span>
                    <p className={`text-sm font-bold ${(data.totales.var_cheques_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_cheques_año)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Proyección/resultado — semántica canónica, sin cálculos frontend */}
              {(() => {
                const projection = resolveProjectionPresentation(
                  data,
                  esMultiMes
                );

                return (
                  <div className="flex flex-col text-center">
                    <p className="text-xs text-zinc-400 uppercase tracking-wide">
                      {projection.title}
                    </p>

                    <p className="text-2xl font-bold text-orange-400">
                      {formatCurrency(projection.value)}
                    </p>

                    <p className="text-xs text-zinc-400 mt-1">
                      {projection.subtitle || '—'}
                    </p>

                    {projection.comparisonValue !== null
                      && projection.comparisonValue !== undefined
                      && (
                        <div className="flex gap-4 mt-auto pt-2 justify-center">
                          <div className="text-center">
                            <span className="text-xs text-zinc-400 block">
                              {projection.comparisonLabel
                                || 'vs periodo comparable'}
                            </span>
                            <p
                              className={`text-sm font-bold ${
                                projection.comparisonValue >= 0
                                  ? 'text-green-400'
                                  : 'text-red-400'
                              }`}
                            >
                              {formatPercent(
                                projection.comparisonValue
                              )}
                            </p>
                          </div>
                        </div>
                      )}
                  </div>
                );
              })()}

              {/* Unidades - P0 TAREA 9: Consolidado con estados separados */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Unidades</p>
                <p className="text-2xl font-bold">{data.status_summary?.unidades_data_ok || data.unidades?.length || 0}</p>
                <p className="text-xs text-zinc-400 mt-1">con datos</p>
                <div className="flex gap-2 mt-auto pt-2 justify-center flex-wrap">
                  {/* P0: Mostrar desglose de estados */}
                  {data.status_summary?.unidades_live_connected > 0 && (
                    <div className="text-center" title="Unidades con conexión en vivo">
                      <span className="text-xs text-zinc-400 block">🟢 En vivo</span>
                      <p className="text-sm font-bold text-green-400">
                        {data.status_summary.unidades_live_connected}
                      </p>
                    </div>
                  )}
                  {data.status_summary?.unidades_source_cache > 0 && (
                    <div className="text-center" title="Unidades mostrando datos de caché">
                      <span className="text-xs text-zinc-400 block">🟡 Cache</span>
                      <p className="text-sm font-bold text-amber-400">
                        {data.status_summary.unidades_source_cache}
                      </p>
                    </div>
                  )}
                  {data.status_summary?.unidades_data_error > 0 && (
                    <div className="text-center" title="Unidades con error">
                      <span className="text-xs text-zinc-400 block">🔴 Error</span>
                      <p className="text-sm font-bold text-red-400">
                        {data.status_summary.unidades_data_error}
                      </p>
                    </div>
                  )}
                  <div className="text-center">
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
                  </div>
                </div>
              </div>
            </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Grid de Unidades - Clickeables */}
      {data?.unidades && data.unidades.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Unidades ({data.unidades.length})
            <span className="text-xs font-normal text-zinc-500">• Clic para ver detalle</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.unidades.map((unidad, idx) => (
              <UnidadCard
                key={unidad.id || unidad.nombre || `unidad-${idx}`}
                unidad={unidad}
                onClick={setUnidadSeleccionada}
                esMultiMes={esMultiMes}
                modoVentasDia={data?.periodo?.modo_ventas_dia || false}
              />
            ))}
          </div>
        </div>
      )}

      {/* Loading State - Solo mostrar spinner si NO hay datos */}
      {loading && !data && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
          <span className="ml-2 text-zinc-500">Consultando todas las unidades...</span>
        </div>
      )}

      {/* Loading Overlay - Mostrar indicador sutil cuando hay datos y está recargando */}
      {loading && data && (
        <div className="fixed bottom-4 right-4 bg-white shadow-lg rounded-lg px-4 py-2 flex items-center gap-2 z-50 border">
          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          <span className="text-sm text-zinc-600">Actualizando...</span>
        </div>
      )}
        </TabsContent>

        {/* Tab Finanzas (Próximamente) */}
        <TabsContent value="finanzas">
          <Card className="border bg-zinc-50">
            <CardContent className="py-12 text-center">
              <Wallet className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <h3 className="text-lg font-semibold text-zinc-600">Tablero Financiero</h3>
              <p className="text-sm text-zinc-500 mt-2">Próximamente: Flujo de caja, cuentas por cobrar/pagar, indicadores financieros</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab RH (Próximamente) */}
        <TabsContent value="rh">
          <Card className="border bg-zinc-50">
            <CardContent className="py-12 text-center">
              <UserCircle className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <h3 className="text-lg font-semibold text-zinc-600">Tablero de Recursos Humanos</h3>
              <p className="text-sm text-zinc-500 mt-2">Próximamente: Plantilla, rotación, productividad, horas extra</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab BSC (Próximamente) */}
        <TabsContent value="bsc">
          <Card className="border bg-zinc-50">
            <CardContent className="py-12 text-center">
              <Award className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <h3 className="text-lg font-semibold text-zinc-600">Balance Scorecard</h3>
              <p className="text-sm text-zinc-500 mt-2">Próximamente: Perspectivas financiera, cliente, procesos, aprendizaje</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal de Detalle */}
      {unidadSeleccionada && (
        <DetalleUnidad
          unidad={unidadSeleccionada}
          onClose={() => setUnidadSeleccionada(null)}
          mes={selectedMeses.length > 0 ? selectedMeses[0] : null}
          anio={selectedAnios.length > 0 ? selectedAnios[0] : null}
          modoVentasDia={data?.periodo?.modo_ventas_dia || false}
        />
      )}
    </div>
  );
}
