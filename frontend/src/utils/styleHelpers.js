/**
 * Utilidades de estilos condicionales para evitar ternarios anidados
 * ===================================================================
 * Reemplaza patrones como:
 *   valor > 0 ? 'text-green-600' : valor < 0 ? 'text-red-600' : ''
 * Por:
 *   getValueColorClass(valor)
 */

/**
 * Obtiene clase de color basada en valor numérico (positivo/negativo/neutro)
 */
export const getValueColorClass = (value, options = {}) => {
  const {
    positive = 'text-green-600',
    negative = 'text-red-600',
    neutral = '',
    zero = ''
  } = options;
  
  if (value > 0) return positive;
  if (value < 0) return negative;
  return zero || neutral;
};

/**
 * Obtiene clase de color basada en porcentaje de cumplimiento
 */
export const getCumplimientoColorClass = (porcentaje, options = {}) => {
  const {
    excellent = 'text-green-600',  // >= 100%
    good = 'text-yellow-600',      // >= 80%
    poor = 'text-red-600'          // < 80%
  } = options;
  
  if (porcentaje >= 100) return excellent;
  if (porcentaje >= 80) return good;
  return poor;
};

/**
 * Obtiene clase de color basada en porcentaje de ocupación
 */
export const getOcupacionColorClass = (porcentaje, options = {}) => {
  const {
    high = 'text-green-600',    // >= 80%
    medium = 'text-yellow-600', // >= 60%
    low = 'text-red-600'        // < 60%
  } = options;
  
  if (porcentaje >= 80) return high;
  if (porcentaje >= 60) return medium;
  return low;
};

/**
 * Obtiene clase de background basada en rol
 */
export const getRoleBgClass = (roleName) => {
  const roleStyles = {
    'Administrador': 'bg-red-100',
    'SuperAdministrador': 'bg-purple-100',
    'Supervisor': 'bg-blue-100',
    'Gerente': 'bg-amber-100',
    'Director': 'bg-indigo-100',
    'Tesoreria': 'bg-cyan-100'
  };
  return roleStyles[roleName] || 'bg-green-100';
};

/**
 * Obtiene clase de background basada en tipo de evento
 */
export const getEventoBgClass = (tipo) => {
  const eventoStyles = {
    'creacion': 'bg-blue-500',
    'avance': 'bg-green-500',
    'rechazo': 'bg-red-500',
    'aprobacion': 'bg-green-500',
    'modificacion': 'bg-amber-500'
  };
  return eventoStyles[tipo] || 'bg-zinc-400';
};

/**
 * Obtiene clase de badge basada en estado de filtro
 */
export const getFilterBadgeClass = (filter) => {
  const filterStyles = {
    'pending': 'bg-amber-100 text-amber-700',
    'approved': 'bg-green-100 text-green-700',
    'rejected': 'bg-red-100 text-red-700',
    'all': 'bg-zinc-100 text-zinc-700'
  };
  return filterStyles[filter] || 'bg-zinc-100 text-zinc-700';
};

/**
 * Obtiene etiqueta de filtro
 */
export const getFilterLabel = (filter) => {
  const labels = {
    'all': 'Todos',
    'pending': 'Pendientes',
    'approved': 'Aprobados',
    'rejected': 'Rechazados'
  };
  return labels[filter] || filter;
};

/**
 * Obtiene clase de color basada en tipo de alerta
 */
export const getAlertaClass = (tipo) => {
  const alertStyles = {
    'sobrestock': { bg: 'bg-orange-100', text: 'text-orange-700', label: 'SOBRESTOCK' },
    'error': { bg: 'bg-red-100', text: 'text-red-700', label: 'ERROR' },
    'baja_venta': { bg: 'bg-red-100', text: 'text-red-700', label: 'BAJA VENTA' }
  };
  return alertStyles[tipo] || { bg: 'bg-zinc-100', text: 'text-zinc-700', label: tipo?.toUpperCase() || 'ALERTA' };
};

/**
 * Obtiene clase de color basada en tipo de almacén
 */
export const getAlmacenTipoLabel = (tipo) => {
  const tipos = {
    1: '(Consumo)',
    2: '(Presentaciones)'
  };
  return tipos[tipo] || '';
};

/**
 * Obtiene clase basada en granularidad de reporte
 */
export const getGranularidadLabel = (granularidad) => {
  const labels = {
    'categoria': 'Categoría',
    'familia': 'Familia',
    'producto': 'Producto'
  };
  return labels[granularidad] || granularidad;
};

/**
 * Obtiene etiqueta de fuente de datos
 */
export const getFuenteLabel = (fuente) => {
  const labels = {
    'tempcheques': 'Ventas sin corte (tempcheques)',
    'api_local': 'API Local MPRO'
  };
  return labels[fuente] || fuente;
};

/**
 * Obtiene clase de color para nivel de aprobación
 */
export const getNivelAprobacionClass = (index) => {
  const colors = ['bg-green-400', 'bg-blue-400', 'bg-purple-400'];
  return colors[index] || 'bg-zinc-400';
};

/**
 * Obtiene descripción de niveles de aprobación
 */
export const getNivelAprobacionDesc = (niveles) => {
  const descripciones = {
    1: 'Supervisor o Admin aprueba',
    2: 'Supervisor → Admin',
    3: 'Supervisor → Admin → Admin final'
  };
  return descripciones[niveles] || `${niveles} niveles`;
};

/**
 * Combina clases CSS condicionalmente
 */
export const cn = (...classes) => {
  return classes.filter(Boolean).join(' ');
};

/**
 * Clase de resultado de acción
 */
export const getAccionResultLabel = (accion) => {
  const labels = {
    'aprobar': 'Enviado a Tesorería',
    'rechazar': 'Rechazado',
    'ajuste': 'Ajustado',
    'autorizar': 'autorizada',
    'pendiente': 'procesada'
  };
  return labels[accion] || 'procesada';
};

/**
 * Obtiene clase de color basada en diferencia numérica (para tablas)
 */
export const getDiferenciaClass = (value) => {
  if (value < 0) return 'text-red-600';
  if (value > 0) return 'text-green-600';
  return 'text-zinc-600';
};

/**
 * Obtiene clase de color para costo con diferencia
 */
export const getCostoDiferenciaClass = (value) => {
  if (value < 0) return 'text-red-600 font-semibold';
  if (value > 0) return 'text-green-600';
  return 'text-zinc-600';
};

/**
 * Obtiene badge de estado de almacén
 */
export const getAlmacenStatusBadge = (costoDiferencia) => {
  if (costoDiferencia < -10000) return { className: 'bg-red-100 text-red-700', label: 'Critico' };
  if (costoDiferencia < 0) return { className: 'bg-yellow-100 text-yellow-700', label: 'Atencion' };
  return { className: 'bg-green-100 text-green-700', label: 'OK' };
};

/**
 * Obtiene tipo de almacén legible
 */
export const getAlmacenTipoText = (tipo) => {
  if (tipo === 1) return '(Consumo)';
  if (tipo === 2) return '(Presentaciones)';
  return '';
};

/**
 * Obtiene placeholder dinámico para selector de almacén
 */
export const getAlmacenPlaceholder = (selectedUnidad, almacenes, todosAlmacenes) => {
  if (todosAlmacenes) return "Todos los folios";
  if (!selectedUnidad) return "Selecciona unidad primero";
  if (almacenes.length === 0) return "Cargando...";
  return "Selecciona almacén(es)";
};
