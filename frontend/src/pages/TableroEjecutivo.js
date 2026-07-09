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
    // cheque_promedio = ventas / cheques (tickets_total)
    // pax_promedio = ventas / pax (pax_total)
    const chequePromedio = Number(totales.cheque_promedio || 0);
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
      pax: u.pax_total || 0,
      cheques: u.tickets_total || 0,
      // CORRECCIÓN GLOBAL: Nomenclatura correcta de KPIs
      // cheque_promedio = ventas / cheques
      // pax_promedio = ventas / pax
      cheque_promedio: u.cheque_promedio ?? 0,
      pax_promedio: u.pax_promedio ?? 0,
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
        pax: totales.pax_total || 0,
        cheques: totales.tickets_total || 0,
        // CORRECCIÓN GLOBAL: Nomenclatura correcta de promedios
        cheque_promedio: chequePromedio,
        pax_prom: paxPromedio,
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
      _v2_metadata: data.metadata || { source: 'EDARSAHUB_V2' }
    };

    logger.log('[COMERCIAL_V2] Datos transformados correctamente desde EDARSAHUB v2');
    return resultado;

  } catch (error) {
    logger.error('[COMERCIAL_V2] Error transformando respuesta v2:', error);
    throw error;
  }
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

const getAniosDisponibles = () => {
  const currentYear = new Date().getFullYear();
  const years = [
    { value: '-1', label: '📊 Ventas del Día' }
  ];
  for (let y = currentYear; y >= currentYear - 3; y--) {
    years.push({ value: y.toString(), label: y.toString() });
  }
  return years;
};

const formatCurrency = (num) => {
  if (num === null || num === undefined) return '-';
  if (num >= 1000000) return `$${(num/1000000).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}M`;
  if (num >= 1000) return `$${(num/1000).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}K`;
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 }).format(num);
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
                <span className="text-xs text-zinc-500">{modoVentasDia ? 'vs Mismo Día Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Año Ant.')}</span>
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
                    <span className="text-xs">Mes: <VariacionBadge valor={unidad.var_vs_mes_ant} /></span>
                    <span className="text-xs">Año: <VariacionBadge valor={unidad.var_vs_año_ant} /></span>
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
                    <span className="text-xs">{modoVentasDia ? 'Día Ant:' : 'Mes:'} <VariacionBadge valor={unidad.pax_ant > 0 ? ((unidad.pax - unidad.pax_ant) / unidad.pax_ant * 100) : 0} /></span>
                    <span className="text-xs">{modoVentasDia ? 'Año Ant:' : 'Año:'} <VariacionBadge valor={unidad.pax_año > 0 ? ((unidad.pax - unidad.pax_año) / unidad.pax_año * 100) : 0} /></span>
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
                    <span className="text-xs">{modoVentasDia ? 'Día Ant:' : 'Mes:'} <VariacionBadge valor={unidad.cheques_ant > 0 ? ((unidad.cheques - unidad.cheques_ant) / unidad.cheques_ant * 100) : 0} /></span>
                    <span className="text-xs">{modoVentasDia ? 'Año Ant:' : 'Año:'} <VariacionBadge valor={unidad.cheques_año > 0 ? ((unidad.cheques - unidad.cheques_año) / unidad.cheques_año * 100) : 0} /></span>
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

  // Estados para filtros multiselección (homologado con Dashboard Comercial)
  const [selectedMeses, setSelectedMeses] = useState(() => {
    const saved = localStorage.getItem('tablero_filtros_v2');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.selectedMeses || [String(new Date().getMonth() + 1).padStart(2, '0')];
      } catch (e) { return [String(new Date().getMonth() + 1).padStart(2, '0')]; }
    }
    return [String(new Date().getMonth() + 1).padStart(2, '0')];
  });

  const [selectedAnios, setSelectedAnios] = useState(() => {
    const saved = localStorage.getItem('tablero_filtros_v2');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.selectedAnios || [new Date().getFullYear().toString()];
      } catch (e) { return [new Date().getFullYear().toString()]; }
    }
    return [new Date().getFullYear().toString()];
  });

  const [tipoComparacion, setTipoComparacion] = useState('dias_equiv');
  const [showMesesDropdown, setShowMesesDropdown] = useState(false);
  const [showAniosDropdown, setShowAniosDropdown] = useState(false);

  const ANIOS = getAniosDisponibles();

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

  // Guardar filtros cuando cambien
  useEffect(() => {
    localStorage.setItem('tablero_filtros_v2', JSON.stringify({ selectedMeses, selectedAnios, tipoComparacion }));
  }, [selectedMeses, selectedAnios, tipoComparacion]);

  // Funciones para toggle de selección
  const toggleMes = (mesValue) => {
    if (selectedMeses.includes(mesValue)) {
      if (selectedMeses.length > 1) {
        setSelectedMeses(selectedMeses.filter(m => m !== mesValue));
      }
    } else {
      setSelectedMeses([...selectedMeses, mesValue].sort());
    }
  };

  const toggleAnio = (anioValue) => {
    // Si es "Ventas del Día", selección exclusiva
    if (anioValue === '-1') {
      setSelectedAnios(['-1']);
      return;
    }
    // Si ya está en "Ventas del Día" y selecciona otro año, quitar -1
    if (selectedAnios.includes('-1')) {
      setSelectedAnios([anioValue]);
      return;
    }
    if (selectedAnios.includes(anioValue)) {
      if (selectedAnios.length > 1) {
        setSelectedAnios(selectedAnios.filter(a => a !== anioValue));
      }
    } else {
      setSelectedAnios([...selectedAnios, anioValue].sort().reverse());
    }
  };

  // Labels para los dropdowns
  const getMesesLabel = () => {
    if (selectedMeses.length === 0) return 'Seleccionar';
    if (selectedMeses.length === 1) {
      return MESES.find(m => m.value === selectedMeses[0])?.label || 'Mes';
    }
    if (selectedMeses.length === 12) return 'Todo el año';
    return `${selectedMeses.length} meses`;
  };

  const getAniosLabel = () => {
    if (selectedAnios.includes('-1')) return '📊 Ventas del Día';
    if (selectedAnios.length === 0) return 'Seleccionar';
    if (selectedAnios.length === 1) {
      return selectedAnios[0];
    }
    return `${selectedAnios.length} años`;
  };

  // Detectar si es modo "Ventas del Día"
  const esVentasDelDia = selectedAnios.includes('-1');

  // Detectar si hay multiselección de meses (para deshabilitar "vs mes")
  const esMultiMes = selectedMeses.length > 1;

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
            logger.log('[COMERCIAL_V2] Consultando ventas-dia desde EDARSAHUB SQL...');

            const v2VentasDia = await api.get(`/v2/comercial/ventas-dia`, { timeout: 30000 });

            if (v2VentasDia.data?.success) {
              const ventasDiaData = v2VentasDia.data.data;
              const resumen = ventasDiaData.resumen || {};
              const porUnidad = ventasDiaData.por_unidad || [];

              responseData = {
                totales: {
                  ventas: resumen.total_estimado_dia || 0,
                  pax: resumen.total_pax || 0,
                  cheques: resumen.total_tickets || 0,
                    cheque_promedio: resumen.cheque_promedio ?? 0,
                    pax_prom: resumen.pax_promedio ?? 0,
                  var_vs_mes_ant: null,
                  var_vs_año_ant: null,
                  proyeccion: null
                },
                periodo: {
                  mes: new Date().getMonth() + 1,
                  anio: new Date().getFullYear(),
                  dias_transcurridos: new Date().getDate(),
                  dias_mes: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate(),
                  modo_ventas_dia: true
                },
                unidades: porUnidad
                  .sort((a, b) => (b.total_estimado_dia || 0) - (a.total_estimado_dia || 0))
                  .map(u => ({
                    unidad_negocio_id: u.unidad_negocio_id,
                    id: u.unidad_negocio_id,
                    sucursal_id: u.unidad_negocio_id,
                    sucursal_nombre: u.unidad_negocio_nombre,
                    unidad_negocio_codigo: u.unidad_negocio_id,
                    unidad: u.unidad_negocio_nombre,
                    server_id: u.server_id,
                    sistema_tipo: u.sistema_origen,
                    ventas: u.total_estimado_dia || 0,
                    pax: (u.pax_abiertos || 0) + (u.pax_cerrados_dia || 0),
                    cheques: (u.tickets_abiertos || 0) + (u.tickets_cerrados_dia || 0),
                    cheque_promedio: u.cheque_promedio ?? 0,
                    pax_promedio: u.pax_promedio ?? 0,
                    proyeccion: 0,
                    ventas_ant: u.dia_anterior_ventas || 0,
                    pax_ant: u.dia_anterior_pax || 0,
                    cheques_ant: u.dia_anterior_cheques || 0,
                    ventas_año: u.dia_anio_ant_ventas || 0,
                    pax_año: u.dia_anio_ant_pax || 0,
                    cheques_año: u.dia_anio_ant_cheques || 0,
                    var_vs_mes_ant: null,
                    var_vs_año_ant: null,
                    data_status: u.dato_vencido ? 'DATA_FROM_CACHE' : 'DATA_OK',
                    live_status: 'NOT_APPLICABLE',
                    source_used: 'EDARSAHUB_SQL_V2',
                    snapshot_timestamp: u.snapshot_timestamp,
                    minutos_desde_ultima_actualizacion: u.minutos_desde_ultima_actualizacion,
                    dato_vencido: u.dato_vencido,
                    fuente_original: u.fuente_original,
                    _fuente: 'EDARSAHUB_SQL_V2'
                  })),
                _v2_source: true
              };
              usedV2 = true;
              logger.log(`[VENTAS_DIA_V2] Cargadas ${responseData.unidades.length} unidades desde EDARSAHUB SQL`);
            } else {
              throw new Error('Respuesta ventas-dia v2 no exitosa');
            }

          } else {
            logger.log('[COMERCIAL_V2] Consultando dashboard V2...');

            const anioActual = parseInt(selectedAnios[0]) || new Date().getFullYear();
            const mesInicio = Math.min(...selectedMeses.map(m => parseInt(m)));
            const mesFin = Math.max(...selectedMeses.map(m => parseInt(m)));
            const fechaInicio = `${anioActual}-${String(mesInicio).padStart(2, '0')}-01`;
            const ultimoDia = new Date(anioActual, mesFin, 0).getDate();
            const fechaFin = `${anioActual}-${String(mesFin).padStart(2, '0')}-${ultimoDia}`;

            const v2Response = await api.get(`/v2/comercial/dashboard`, {
              params: {
                fecha_inicio: fechaInicio,
                fecha_fin: fechaFin,
                meses: selectedMeses.map(m => parseInt(m)).join(',')
              },
              timeout: 30000
            });

            if (v2Response.data?.success) {
              responseData = transformV2ToV1Format(v2Response.data, selectedMeses, selectedAnios, logger);

              if (responseData.unidades && responseData.unidades.length > 0) {
                responseData.unidades.sort((a, b) => (b.ventas || 0) - (a.ventas || 0));
              }

              usedV2 = true;
              responseData._v2_source = true;
              logger.log(`[FASE3] V2 fuente ÚNICA: ${responseData.unidades?.length} unidades desde EDARSAHUB`);
            } else {
              throw new Error('Respuesta v2 no exitosa');
            }
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
  }, [selectedMeses, selectedAnios, tipoComparacion, requestId, latestRequestId, esVentasDelDia, data]);

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
  }, [selectedMeses, selectedAnios, tipoComparacion]);

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

  // Cerrar dropdowns cuando se hace click fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('[data-dropdown="meses"]') && !event.target.closest('[data-dropdown="anios"]')) {
        setShowMesesDropdown(false);
        setShowAniosDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
                {/* Selector de Meses (multiselección) */}
                <div className="flex-1 min-w-[140px] max-w-[180px] relative" data-dropdown="meses">
                  <Label className="text-xs mb-1 block">Mes(es)</Label>
                  <button
                    type="button"
                    onClick={() => { setShowMesesDropdown(!showMesesDropdown); setShowAniosDropdown(false); }}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    disabled={esVentasDelDia}
                  >
                    <span>{esVentasDelDia ? 'N/A' : getMesesLabel()}</span>
                    <ChevronDown className="h-4 w-4 opacity-50" />
                  </button>
                  {showMesesDropdown && !esVentasDelDia && (
                    <div className="absolute z-50 mt-1 w-full rounded-md border bg-white shadow-lg max-h-60 overflow-auto">
                      <div className="p-2 border-b">
                        <button
                          type="button"
                          onClick={() => setSelectedMeses(MESES.map(m => m.value))}
                          className="text-xs text-blue-600 hover:underline mr-3"
                        >
                          Todos
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedMeses([String(new Date().getMonth() + 1).padStart(2, '0')])}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Solo actual
                        </button>
                      </div>
                      {MESES.map(mes => (
                        <label
                          key={mes.value}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-zinc-100 cursor-pointer"
                        >
                          <Checkbox
                            checked={selectedMeses.includes(mes.value)}
                            onCheckedChange={() => toggleMes(mes.value)}
                          />
                          <span className="text-sm">{mes.label}</span>
                        </label>
                      ))}
                      <div className="p-2 border-t">
                        <Button size="sm" onClick={() => setShowMesesDropdown(false)} className="w-full">
                          Aplicar
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Selector de Año (multiselección + Ventas del Día) */}
                <div className="flex-1 min-w-[140px] max-w-[180px] relative" data-dropdown="anios">
                  <Label className="text-xs mb-1 block">Año(s)</Label>
                  <button
                    type="button"
                    onClick={() => { setShowAniosDropdown(!showAniosDropdown); setShowMesesDropdown(false); }}
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  >
                    <span>{getAniosLabel()}</span>
                    <ChevronDown className="h-4 w-4 opacity-50" />
                  </button>
                  {showAniosDropdown && (
                    <div className="absolute z-50 mt-1 w-full rounded-md border bg-white shadow-lg max-h-60 overflow-auto">
                      <div className="p-2 border-b">
                        <button
                          type="button"
                          onClick={() => setSelectedAnios([new Date().getFullYear().toString(), (new Date().getFullYear() - 1).toString()])}
                          className="text-xs text-blue-600 hover:underline mr-3"
                        >
                          Actual + Anterior
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedAnios([new Date().getFullYear().toString()])}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Solo actual
                        </button>
                      </div>
                      {ANIOS.map(anio => (
                        <label
                          key={anio.value}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-zinc-100 cursor-pointer"
                        >
                          <Checkbox
                            checked={selectedAnios.includes(anio.value)}
                            onCheckedChange={() => toggleAnio(anio.value)}
                          />
                          <span className="text-sm">{anio.label}</span>
                        </label>
                      ))}
                      <div className="p-2 border-t">
                        <Button size="sm" onClick={() => setShowAniosDropdown(false)} className="w-full">
                          Aplicar
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                <Button
                  onClick={() => {
                    setShowMesesDropdown(false);
                    setShowAniosDropdown(false);
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
                    {data.periodo.modo_ventas_dia
                      ? <span className="text-amber-600 font-medium">🔴 Ventas del Día (sin corte)</span>
                      : `${data.periodo.mes ? MESES.find(m => m.value === String(data.periodo.mes).padStart(2, '0'))?.label : ''} ${data.periodo.anio} • Día ${data.periodo.dias_transcurridos} de ${data.periodo.dias_mes}`
                    }
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
                <p className="text-xs text-zinc-400 uppercase tracking-wide">Ventas Consolidadas</p>
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
                    <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Año')}</span>
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
                <p className="text-xs text-zinc-400 mt-1">Pax Prom: {formatCurrency(data.totales.pax_prom ?? 0)}</p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  {!esMultiMes && (
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Día Ant.' : 'vs Mes'}</span>
                      <p className={`text-sm font-bold ${(data.totales.var_pax_mes || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPercent(data.totales.var_pax_mes || 0)}
                      </p>
                    </div>
                  )}
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Año')}</span>
                    <p className={`text-sm font-bold ${(data.totales.var_pax_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_pax_año || 0)}
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
                        {formatPercent(data.totales.var_cheques_mes || 0)}
                      </p>
                    </div>
                  )}
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">{data?.periodo?.modo_ventas_dia ? 'vs Año Ant.' : (esMultiMes ? 'vs Periodo Ant.' : 'vs Año')}</span>
                    <p className={`text-sm font-bold ${(data.totales.var_cheques_año || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(data.totales.var_cheques_año || 0)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Proyección Mes/Anual/Día - Dinámico según selector */}
              <div className="flex flex-col text-center">
                <p className="text-xs text-zinc-400 uppercase tracking-wide">
                  {data?.periodo?.modo_ventas_dia
                    ? 'Proyección del Día'
                    : (esMultiMes ? 'Proyección Anual' : 'Proyección Mes')
                  }
                </p>
                <p className="text-2xl font-bold text-orange-400">
                  {formatCurrency(
                    data?.periodo?.modo_ventas_dia
                      ? data.totales.ventas  // En Ventas del Día, la proyección ES la venta actual (al cierre será = venta real)
                      : (esMultiMes
                          ? (data.totales.ventas / (data.periodo?.dias_transcurridos || 1)) * 365
                          : data.totales.proyeccion
                        )
                  )}
                </p>
                <p className="text-xs text-zinc-400 mt-1">
                  {data?.periodo?.modo_ventas_dia
                    ? 'Al cierre del día'
                    : (esMultiMes
                        ? `${data.periodo?.dias_transcurridos || 0} días → 365 días`
                        : 'Si mantiene ritmo'
                      )
                  }
                </p>
                <div className="flex gap-4 mt-auto pt-2 justify-center">
                  <div className="text-center">
                    <span className="text-xs text-zinc-400 block">
                      {data?.periodo?.modo_ventas_dia ? 'vs Mismo Día Año Ant.' : (esMultiMes ? 'vs Ventas Año Ant.' : 'vs Año Ant.')}
                    </span>
                    <p className={`text-sm font-bold ${(() => {
                      if (esMultiMes) {
                        // Proyección 2026 vs Proyección 2025 (ambas anualizadas)
                        const proy2026 = (data.totales.ventas / (data.periodo?.dias_transcurridos || 1)) * 365;
                        const proy2025 = (data.totales.ventas_año / (data.periodo?.dias_transcurridos || 1)) * 365;
                        return proy2025 > 0 ? ((proy2026 - proy2025) / proy2025 * 100) : 0;
                      }
                      return data.totales.var_proy_vs_año || 0;
                    })() >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent((() => {
                        if (esMultiMes) {
                          // Proyección 2026 vs Proyección 2025 (ambas anualizadas)
                          const proy2026 = (data.totales.ventas / (data.periodo?.dias_transcurridos || 1)) * 365;
                          const proy2025 = (data.totales.ventas_año / (data.periodo?.dias_transcurridos || 1)) * 365;
                          return proy2025 > 0 ? ((proy2026 - proy2025) / proy2025 * 100) : 0;
                        }
                        return data.totales.var_proy_vs_año || 0;
                      })())}
                    </p>
                  </div>
                </div>
              </div>

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
                  {!data.status_summary && (
                    <div className="text-center">
                      <span className="text-xs text-zinc-400 block">Año Ant.</span>
                      <p className="text-sm font-bold text-zinc-300">
                        {data.totales?.unidades_año_ant || 0}
                      </p>
                    </div>
                  )}
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
