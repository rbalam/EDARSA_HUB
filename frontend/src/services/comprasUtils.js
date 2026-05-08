/**
 * comprasUtils.js
 * 
 * Utilidades para el módulo de Compras - ESTABILIZACIÓN MULTI-UNIDAD MULTI-TAB
 * 
 * ARQUITECTURA:
 * - unidad_key: Identificador canónico único para aislamiento de estado
 * - Formato: {system_type}:{server_id}:{sucursal_origen_id}:{unidad_id}
 * - Control de race conditions: requestId por unidad_key y tab
 * 
 * PRINCIPIOS:
 * - EDARSAHUB SQL es fuente primaria de configuración
 * - MongoDB solo para cache/logs
 * - Aislamiento entre unidades
 * - Aislamiento entre tabs
 */

import logger from './logger';

// ============================================================================
// GENERACIÓN DE UNIDAD_KEY CANÓNICA
// ============================================================================

/**
 * Genera una unidad_key canónica para identificar unívocamente una unidad de negocio.
 * Esta key se usa para:
 * - Aislar estado entre unidades
 * - Aislar cache entre unidades
 * - Controlar race conditions
 * - Logs de diagnóstico
 * 
 * @param {Object} unidad - Objeto de unidad de negocio
 * @returns {string} unidad_key en formato: {system_type}:{server_id}:{sucursal_origen_id}:{unidad_id}
 */
export const generateUnidadKey = (unidad) => {
  if (!unidad) return 'NO_UNIDAD';
  
  const systemType = unidad.system_type || 'UNKNOWN';
  const serverId = unidad.server_id || 'NO_SERVER';
  const sucursalOrigenId = unidad.sucursal_origen_id || 'NO_SUCURSAL';
  const unidadId = unidad.id || 'NO_ID';
  
  return `${systemType}:${serverId}:${sucursalOrigenId}:${unidadId}`;
};

/**
 * Genera una cache_key completa para Compras incluyendo filtros.
 * 
 * @param {string} tab - Tab actual (dashboard, autorizacion, etc.)
 * @param {string} unidadKey - unidad_key canónica
 * @param {Object} filters - Filtros activos
 * @returns {string} cache_key única
 */
export const generateCacheKey = (tab, unidadKey, filters = {}) => {
  const filterHash = JSON.stringify({
    mes: filters.mes,
    anio: filters.anio,
    fecha_inicio: filters.fecha_inicio,
    fecha_fin: filters.fecha_fin,
    sucursal: filters.sucursal
  });
  
  return `compras:${tab}:${unidadKey}:${btoa(filterHash).slice(0, 20)}`;
};

// ============================================================================
// NORMALIZACIÓN DE FILTROS
// ============================================================================

/**
 * Normaliza los filtros de Compras a un formato canónico.
 * Convierte meses a numéricos, fechas a ISO, etc.
 * 
 * @param {Object} unidad - Unidad de negocio seleccionada
 * @param {Object} globalFilters - Filtros globales (mes, año, sucursal)
 * @param {Object} tabFilters - Filtros específicos del tab
 * @param {string} tab - Tab actual
 * @returns {Object} Filtros normalizados
 */
export const normalizeComprasFilters = (unidad, globalFilters, tabFilters, tab) => {
  if (!unidad) {
    return { valid: false, error: 'UNIDAD_REQUIRED' };
  }
  
  const mes = parseInt(globalFilters.mes || new Date().getMonth() + 1, 10);
  const anio = parseInt(globalFilters.anio || new Date().getFullYear(), 10);
  
  // Calcular fechas del período
  const lastDay = new Date(anio, mes, 0).getDate();
  const fechaInicio = `${anio}-${String(mes).padStart(2, '0')}-01`;
  const fechaFin = `${anio}-${String(mes).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
  
  return {
    valid: true,
    unidad_key: generateUnidadKey(unidad),
    tab,
    unidad_negocio_id: unidad.id,
    empresa_id: unidad.empresa_id || null,
    server_id: unidad.server_id,
    sucursal_id: globalFilters.sucursal || unidad.sucursales?.[0]?.id || null,
    sucursal_origen_id: unidad.sucursal_origen_id || null,
    database_name: unidad.database_name || null,
    system_type: unidad.system_type,
    connection_type: unidad.connection_type || 'SQL_SERVER',
    mes,
    anio,
    fecha_inicio: fechaInicio,
    fecha_fin: fechaFin,
    // Filtros específicos del tab
    ...tabFilters
  };
};

// ============================================================================
// CONTROL DE RACE CONDITIONS
// ============================================================================

// Mapa global de requestIds por unidad_key y tab
const requestIdMap = new Map();

/**
 * Genera un nuevo requestId para una combinación de unidad_key y tab.
 * 
 * @param {string} unidadKey - unidad_key canónica
 * @param {string} tab - Tab actual
 * @returns {number} requestId único
 */
export const generateRequestId = (unidadKey, tab) => {
  const key = `${unidadKey}:${tab}`;
  const current = requestIdMap.get(key) || 0;
  const newId = current + 1;
  requestIdMap.set(key, newId);
  return newId;
};

/**
 * Verifica si un requestId es el más reciente para una combinación de unidad_key y tab.
 * 
 * @param {string} unidadKey - unidad_key canónica
 * @param {string} tab - Tab actual
 * @param {number} requestId - requestId a verificar
 * @returns {boolean} true si es el más reciente
 */
export const isLatestRequest = (unidadKey, tab, requestId) => {
  const key = `${unidadKey}:${tab}`;
  const current = requestIdMap.get(key) || 0;
  return requestId === current;
};

/**
 * Resetea el requestId para una combinación de unidad_key y tab.
 * Útil cuando se cambia de unidad o se limpia el estado.
 * 
 * @param {string} unidadKey - unidad_key canónica
 * @param {string} tab - Tab actual (opcional, si no se proporciona resetea todos los tabs)
 */
export const resetRequestId = (unidadKey, tab = null) => {
  if (tab) {
    requestIdMap.delete(`${unidadKey}:${tab}`);
  } else {
    // Resetear todos los tabs para esta unidad
    const tabs = ['dashboard', 'autorizacion', 'analisis', 'auditoria', 'proveedores'];
    tabs.forEach(t => requestIdMap.delete(`${unidadKey}:${t}`));
  }
};

// ============================================================================
// VALIDACIÓN DE RESPUESTAS
// ============================================================================

/**
 * Valida si una respuesta del backend corresponde a la solicitud actual.
 * Evita que respuestas tardías sobrescriban datos actuales.
 * 
 * @param {Object} response - Respuesta del backend
 * @param {string} expectedUnidadKey - unidad_key esperada
 * @param {string} expectedTab - Tab esperado
 * @param {number} expectedRequestId - requestId esperado
 * @returns {Object} { valid: boolean, reason?: string }
 */
export const validateResponse = (response, expectedUnidadKey, expectedTab, expectedRequestId) => {
  // Verificar que el requestId sea el más reciente
  if (!isLatestRequest(expectedUnidadKey, expectedTab, expectedRequestId)) {
    logger.debug(`[compras_fetch_ignored_stale] Request ${expectedRequestId} ignorado - hay uno más reciente`);
    return { valid: false, reason: 'STALE_REQUEST' };
  }
  
  // Si la respuesta tiene meta, verificar que coincida
  if (response?.meta) {
    if (response.meta.unidad_key && response.meta.unidad_key !== expectedUnidadKey) {
      logger.debug(`[compras_fetch_ignored_stale] unidad_key no coincide: ${response.meta.unidad_key} vs ${expectedUnidadKey}`);
      return { valid: false, reason: 'UNIDAD_MISMATCH' };
    }
    if (response.meta.tab && response.meta.tab !== expectedTab) {
      logger.debug(`[compras_fetch_ignored_stale] tab no coincide: ${response.meta.tab} vs ${expectedTab}`);
      return { valid: false, reason: 'TAB_MISMATCH' };
    }
  }
  
  return { valid: true };
};

// ============================================================================
// MANEJO DE ESTADOS (LOADING, ERROR, NO_DATA)
// ============================================================================

/**
 * Códigos de estado para respuestas de Compras.
 */
export const COMPRAS_STATUS = {
  SUCCESS: 'SUCCESS',
  NO_DATA: 'NO_DATA',
  LOADING: 'LOADING',
  ERROR_CONNECTION: 'ERROR_CONNECTION',
  ERROR_FILTERS: 'ERROR_FILTERS',
  ERROR_PERMISSION: 'ERROR_PERMISSION',
  ERROR_UNIT_INCOMPLETE: 'ERROR_UNIT_INCOMPLETE',
  ERROR_TAB_NOT_IMPLEMENTED: 'ERROR_TAB_NOT_IMPLEMENTED',
  ERROR_SERVER_UNREACHABLE: 'ERROR_SERVER_UNREACHABLE',
  ERROR_UNKNOWN: 'ERROR_UNKNOWN',
  ERROR: 'ERROR'  // Estado genérico de error
};

/**
 * Mensajes de usuario para cada código de estado.
 */
export const COMPRAS_STATUS_MESSAGES = {
  [COMPRAS_STATUS.SUCCESS]: null, // No mostrar mensaje en éxito
  [COMPRAS_STATUS.NO_DATA]: 'Sin datos para el período seleccionado',
  [COMPRAS_STATUS.LOADING]: 'Cargando...',
  [COMPRAS_STATUS.ERROR_CONNECTION]: 'No fue posible conectar con la fuente de datos de esta unidad',
  [COMPRAS_STATUS.ERROR_FILTERS]: 'Seleccione los filtros requeridos para continuar',
  [COMPRAS_STATUS.ERROR_PERMISSION]: 'No tiene permisos para consultar esta unidad',
  [COMPRAS_STATUS.ERROR_UNIT_INCOMPLETE]: 'Configuración incompleta para esta unidad de negocio',
  [COMPRAS_STATUS.ERROR_TAB_NOT_IMPLEMENTED]: 'Esta funcionalidad aún no está disponible para esta unidad',
  [COMPRAS_STATUS.ERROR_SERVER_UNREACHABLE]: 'Servidor no accesible. Requiere conexión VPN o entorno local.',
  [COMPRAS_STATUS.ERROR_UNKNOWN]: 'Error inesperado. Intente nuevamente.',
  [COMPRAS_STATUS.ERROR]: 'Error al consultar datos'
};

/**
 * Determina el código de estado basado en la respuesta del backend.
 * 
 * @param {Object} response - Respuesta del backend
 * @param {Object} error - Error si lo hubo
 * @returns {string} Código de estado de COMPRAS_STATUS
 */
export const getStatusFromResponse = (response, error = null) => {
  if (error) {
    if (error.response?.status === 403) return COMPRAS_STATUS.ERROR_PERMISSION;
    if (error.response?.status === 400) return COMPRAS_STATUS.ERROR_FILTERS;
    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') return COMPRAS_STATUS.ERROR_CONNECTION;
    if (error.response?.data?.code === 'COMPRAS_UNIT_INVALID') return COMPRAS_STATUS.ERROR_UNIT_INCOMPLETE;
    if (error.response?.data?.code === 'COMPRAS_TAB_NOT_IMPLEMENTED') return COMPRAS_STATUS.ERROR_TAB_NOT_IMPLEMENTED;
    return COMPRAS_STATUS.ERROR_UNKNOWN;
  }
  
  if (!response) return COMPRAS_STATUS.NO_DATA;
  
  if (response.code === 'COMPRAS_NO_DATA' || 
      (Array.isArray(response.data) && response.data.length === 0) ||
      (response.data && Object.keys(response.data).length === 0)) {
    return COMPRAS_STATUS.NO_DATA;
  }
  
  return COMPRAS_STATUS.SUCCESS;
};

// ============================================================================
// LOGGING DE DIAGNÓSTICO
// ============================================================================

/**
 * Log estructurado para eventos del módulo Compras.
 * 
 * @param {string} event - Nombre del evento
 * @param {Object} data - Datos del evento
 */
export const logComprasEvent = (event, data = {}) => {
  const logData = {
    timestamp: new Date().toISOString(),
    event,
    unidad_key: data.unidad_key || null,
    unidad_negocio_id: data.unidad_negocio_id || null,
    server_id: data.server_id || null,
    sucursal_id: data.sucursal_id || null,
    system_type: data.system_type || null,
    tab: data.tab || null,
    mes: data.mes || null,
    anio: data.anio || null,
    request_id: data.request_id || null,
    duration_ms: data.duration_ms || null,
    result: data.result || null,
    error_code: data.error_code || null,
    ...data.extra
  };
  
  // Filtrar campos null para logs más limpios
  const cleanData = Object.fromEntries(
    Object.entries(logData).filter(([_, v]) => v !== null && v !== undefined)
  );
  
  logger.debug(`[${event}]`, cleanData);
};

export default {
  generateUnidadKey,
  generateCacheKey,
  normalizeComprasFilters,
  generateRequestId,
  isLatestRequest,
  resetRequestId,
  validateResponse,
  COMPRAS_STATUS,
  COMPRAS_STATUS_MESSAGES,
  getStatusFromResponse,
  logComprasEvent
};
