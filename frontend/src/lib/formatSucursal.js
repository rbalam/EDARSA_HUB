/**
 * Utilidades para formatear nombres de sucursales/unidades
 * Mapea nombres de la BD a nombres de visualización personalizados
 */

// Mapeo de nombres de sucursales (BD → Display)
const NOMBRE_SUCURSAL_MAP = {
  // 130 Merida variants
  '130 Merida': '130° MERIDA',
  '130 MERIDA': '130° MERIDA',
  '130Merida': '130° MERIDA',
  '130 merida': '130° MERIDA',
  // ERP variants - remover prefijo "ERP"
  'ERP EDARSA HUB': 'EDARSA HUB',
  'ERP Edarsa Hub': 'EDARSA HUB',
  'ERP EDARSA hub': 'EDARSA HUB',
  'Edarsa Hub': 'EDARSA HUB',
};

/**
 * Formatea el nombre de una sucursal/unidad para mostrar en dashboards
 * @param {string} nombre - Nombre original de la BD
 * @returns {string} - Nombre formateado para display
 */
export const formatNombreSucursal = (nombre) => {
  if (!nombre) return '';
  
  // Buscar en el mapeo exacto
  if (NOMBRE_SUCURSAL_MAP[nombre]) {
    return NOMBRE_SUCURSAL_MAP[nombre];
  }
  
  // Buscar coincidencia parcial (case insensitive)
  const nombreLower = nombre.toLowerCase();
  for (const [key, value] of Object.entries(NOMBRE_SUCURSAL_MAP)) {
    if (nombreLower.includes(key.toLowerCase())) {
      return nombre.replace(new RegExp(key, 'i'), value);
    }
  }
  
  return nombre;
};

/**
 * Formatea un array de datos reemplazando nombres de sucursales
 * @param {Array} data - Array de objetos con campo 'unidad' o 'sucursal'
 * @returns {Array} - Array con nombres formateados
 */
export const formatDataSucursales = (data) => {
  if (!Array.isArray(data)) return data;
  
  return data.map(item => ({
    ...item,
    unidad: item.unidad ? formatNombreSucursal(item.unidad) : item.unidad,
    sucursal: item.sucursal ? formatNombreSucursal(item.sucursal) : item.sucursal,
    nombre: item.nombre ? formatNombreSucursal(item.nombre) : item.nombre,
  }));
};

export default formatNombreSucursal;
