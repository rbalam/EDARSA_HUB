/**
 * FASE 3A.4 - Utilidades Frontend para Respuestas Estructuradas Comercial
 * ========================================================================
 * 
 * Helper centralizado para normalizar respuestas del backend y mostrar
 * mensajes amigables al usuario. Mantiene compatibilidad con respuestas legacy.
 * 
 * Estados soportados:
 * - SUCCESS: Datos cargados correctamente
 * - NO_DATA: Sin datos para los filtros seleccionados
 * - NOT_AVAILABLE_FOR_SYSTEM: Consulta no aplica para el sistema origen
 * - UNSUPPORTED_SYSTEM_TYPE: Tipo de sistema no soportado
 * - QUERY_ERROR: Error en la consulta SQL o incompatibilidad
 * - FIELD_MAPPING_ERROR: Mapeo de campos no coincide
 * - SOURCE_UNREACHABLE: Servidor origen inalcanzable
 * - CONFIGURATION_MISSING: Configuración incompleta
 * - PERMISSION_DENIED: Sin permisos
 * - INACTIVE_SOURCE: Fuente de datos inactiva
 * - PARTIAL: Datos parciales disponibles
 * - DEGRADED_CACHE: Datos de caché (fuente no disponible)
 * - ERROR: Error genérico
 * 
 * Fecha: 2025-12
 * Fase: 3A.4
 */

/**
 * Normaliza la respuesta del backend a un formato consistente.
 * Mantiene compatibilidad con respuestas legacy (array directo, objeto con data, etc.)
 * 
 * @param {any} response - Respuesta del backend (axios response.data)
 * @returns {Object} Respuesta normalizada con status, data, meta, warnings, error
 */
export const normalizeComercialResponse = (response) => {
  // Si es null o undefined
  if (response === null || response === undefined) {
    return {
      status: 'NO_DATA',
      data: null,
      meta: {},
      warnings: [],
      error: null,
      isStructured: false
    };
  }

  // Si es un array directo (respuesta legacy)
  if (Array.isArray(response)) {
    return {
      status: response.length > 0 ? 'SUCCESS' : 'NO_DATA',
      data: response,
      meta: {},
      warnings: [],
      error: null,
      isStructured: false
    };
  }

  // Si tiene source_status (formato estructurado FASE 3A)
  if (response.source_status) {
    return {
      status: response.source_status,
      data: response.data || response.kpis || response.items || response,
      meta: {
        cache_used: response.cache_used || false,
        last_successful_sync: response.last_successful_sync || null,
        server_name: response.server_name || null,
        system_type: response.system_type || response.meta?.system_type || null,
        system_type_normalized: response.system_type_normalized || response.meta?.system_type_normalized || null
      },
      warnings: response.warnings || [],
      error: response.error || null,
      message: response.source_message || response.message || null,
      isStructured: true
    };
  }

  // Si tiene status (formato estructurado alternativo)
  if (response.status && typeof response.status === 'string') {
    return {
      status: response.status,
      data: response.data || response,
      meta: response.meta || {},
      warnings: response.warnings || [],
      error: response.error || null,
      message: response.message || null,
      isStructured: true
    };
  }

  // Si tiene data directamente (respuesta legacy con wrapper)
  if (response.data !== undefined) {
    const hasData = Array.isArray(response.data) ? response.data.length > 0 : !!response.data;
    return {
      status: hasData ? 'SUCCESS' : 'NO_DATA',
      data: response.data,
      meta: response.meta || {},
      warnings: [],
      error: null,
      isStructured: false
    };
  }

  // Caso por defecto: asumir que el objeto completo son los datos
  return {
    status: 'SUCCESS',
    data: response,
    meta: {},
    warnings: [],
    error: null,
    isStructured: false
  };
};

/**
 * Obtiene un mensaje amigable para el usuario basado en el estado de la respuesta.
 * 
 * @param {string} status - Estado de la respuesta
 * @param {string} errorMessage - Mensaje de error del backend (opcional)
 * @param {Object} meta - Metadatos de la respuesta (opcional)
 * @returns {Object} Objeto con título, mensaje, tipo de alerta y si debe mostrar
 */
export const getComercialStatusMessage = (status, errorMessage = '', meta = {}) => {
  const messages = {
    SUCCESS: {
      title: null,
      message: null,
      type: 'success',
      show: false
    },
    NO_DATA: {
      title: 'Sin Datos',
      message: 'No hay datos para los filtros seleccionados.',
      type: 'info',
      show: true
    },
    NOT_AVAILABLE_FOR_SYSTEM: {
      title: 'No Disponible',
      message: 'Esta consulta no aplica para el sistema origen seleccionado.',
      type: 'warning',
      show: true
    },
    UNSUPPORTED_SYSTEM_TYPE: {
      title: 'Sistema No Soportado',
      message: 'El tipo de sistema origen no está soportado para este tablero.',
      type: 'warning',
      show: true
    },
    QUERY_ERROR: {
      title: 'Error de Consulta',
      message: 'La consulta comercial falló por incompatibilidad de estructura o error interno.',
      type: 'error',
      show: true
    },
    FIELD_MAPPING_ERROR: {
      title: 'Error de Mapeo',
      message: 'El mapeo de campos del sistema origen no coincide con lo esperado.',
      type: 'error',
      show: true
    },
    SOURCE_UNREACHABLE: {
      title: 'Servidor Inalcanzable',
      message: 'No fue posible conectar con el servidor origen. Verifica la conexión VPN o túnel.',
      type: 'error',
      show: true
    },
    CONFIGURATION_MISSING: {
      title: 'Configuración Incompleta',
      message: 'La configuración de esta unidad no está completa. Contacta a soporte.',
      type: 'error',
      show: true
    },
    PERMISSION_DENIED: {
      title: 'Acceso Denegado',
      message: 'No tienes permisos para consultar esta unidad o tablero.',
      type: 'error',
      show: true
    },
    INACTIVE_SOURCE: {
      title: 'Fuente Inactiva',
      message: 'La fuente de datos seleccionada está inactiva.',
      type: 'warning',
      show: true
    },
    PARTIAL: {
      title: 'Datos Parciales',
      message: 'Se cargó información parcial. Algunas fuentes no respondieron correctamente.',
      type: 'warning',
      show: true
    },
    DEGRADED_CACHE: {
      title: 'Datos de Cache',
      message: 'La fuente de datos no está disponible. Mostrando datos guardados previamente.',
      type: 'warning',
      show: true
    },
    ERROR: {
      title: 'Error del Sistema',
      message: errorMessage || 'Ocurrió un error inesperado.',
      type: 'error',
      show: true
    }
  };

  const baseMessage = messages[status] || messages.ERROR;
  
  // Si hay mensaje personalizado del backend, usarlo (pero no technical_detail)
  if (errorMessage && !errorMessage.includes('password') && !errorMessage.includes('api_key') && !errorMessage.includes('connection string')) {
    return {
      ...baseMessage,
      message: errorMessage
    };
  }

  return baseMessage;
};

/**
 * Obtiene las clases CSS para el indicador de estado.
 * 
 * @param {string} status - Estado de la respuesta
 * @returns {Object} Objeto con clases para container, icon y text
 */
export const getStatusStyles = (status) => {
  const styles = {
    SUCCESS: {
      container: '',
      icon: '',
      text: ''
    },
    NO_DATA: {
      container: 'border-blue-200 bg-blue-50',
      icon: 'text-blue-500',
      text: 'text-blue-700'
    },
    NOT_AVAILABLE_FOR_SYSTEM: {
      container: 'border-yellow-200 bg-yellow-50',
      icon: 'text-yellow-500',
      text: 'text-yellow-700'
    },
    UNSUPPORTED_SYSTEM_TYPE: {
      container: 'border-yellow-200 bg-yellow-50',
      icon: 'text-yellow-500',
      text: 'text-yellow-700'
    },
    QUERY_ERROR: {
      container: 'border-red-200 bg-red-50',
      icon: 'text-red-500',
      text: 'text-red-700'
    },
    FIELD_MAPPING_ERROR: {
      container: 'border-red-200 bg-red-50',
      icon: 'text-red-500',
      text: 'text-red-700'
    },
    SOURCE_UNREACHABLE: {
      container: 'border-orange-200 bg-orange-50',
      icon: 'text-orange-500',
      text: 'text-orange-700'
    },
    CONFIGURATION_MISSING: {
      container: 'border-red-200 bg-red-50',
      icon: 'text-red-500',
      text: 'text-red-700'
    },
    PERMISSION_DENIED: {
      container: 'border-red-200 bg-red-50',
      icon: 'text-red-500',
      text: 'text-red-700'
    },
    INACTIVE_SOURCE: {
      container: 'border-gray-200 bg-gray-50',
      icon: 'text-gray-500',
      text: 'text-gray-700'
    },
    PARTIAL: {
      container: 'border-yellow-200 bg-yellow-50',
      icon: 'text-yellow-500',
      text: 'text-yellow-700'
    },
    DEGRADED_CACHE: {
      container: 'border-amber-200 bg-amber-50',
      icon: 'text-amber-500',
      text: 'text-amber-700'
    },
    ERROR: {
      container: 'border-red-200 bg-red-50',
      icon: 'text-red-500',
      text: 'text-red-700'
    }
  };

  return styles[status] || styles.ERROR;
};

/**
 * Mapea errores HTTP a estados estructurados.
 * 
 * @param {Error} error - Error de axios o fetch
 * @returns {string} Estado estructurado correspondiente
 */
export const mapHttpErrorToStatus = (error) => {
  if (!error.response) {
    // Error de red (sin respuesta del servidor)
    return 'SOURCE_UNREACHABLE';
  }

  const statusCode = error.response.status;

  switch (statusCode) {
    case 401:
    case 403:
      return 'PERMISSION_DENIED';
    case 404:
      return 'CONFIGURATION_MISSING';
    case 408:
    case 504:
      return 'SOURCE_UNREACHABLE';
    case 422:
      return 'FIELD_MAPPING_ERROR';
    case 500:
    case 502:
    case 503:
      return 'QUERY_ERROR';
    default:
      return 'ERROR';
  }
};

/**
 * Log de diagnóstico para desarrollo (no muestra datos sensibles).
 * Solo activo en modo desarrollo.
 * 
 * @param {string} tablero - Nombre del tablero
 * @param {string} status - Estado de la respuesta
 * @param {Object} meta - Metadatos (sin datos sensibles)
 */
export const logComercialStatus = (tablero, status, meta = {}) => {
  if (process.env.NODE_ENV !== 'production') {
    const safeLog = {
      tablero,
      status,
      system_type: meta.system_type || 'N/A',
      system_type_normalized: meta.system_type_normalized || 'N/A',
      server_id: meta.server_id || 'N/A',
      cache_used: meta.cache_used || false
    };
    console.debug('[COMERCIAL][STATUS]', safeLog);
  }
};

/**
 * Verifica si un estado es considerado "error" (requiere acción del usuario o soporte).
 * 
 * @param {string} status - Estado de la respuesta
 * @returns {boolean} True si es un estado de error
 */
export const isErrorStatus = (status) => {
  const errorStatuses = [
    'QUERY_ERROR',
    'FIELD_MAPPING_ERROR',
    'SOURCE_UNREACHABLE',
    'CONFIGURATION_MISSING',
    'PERMISSION_DENIED',
    'ERROR'
  ];
  return errorStatuses.includes(status);
};

/**
 * Verifica si un estado permite mostrar datos (aunque parciales o de cache).
 * 
 * @param {string} status - Estado de la respuesta
 * @returns {boolean} True si se pueden mostrar datos
 */
export const canShowData = (status) => {
  const showableStatuses = [
    'SUCCESS',
    'PARTIAL',
    'DEGRADED_CACHE'
  ];
  return showableStatuses.includes(status);
};

export default {
  normalizeComercialResponse,
  getComercialStatusMessage,
  getStatusStyles,
  mapHttpErrorToStatus,
  logComercialStatus,
  isErrorStatus,
  canShowData
};
