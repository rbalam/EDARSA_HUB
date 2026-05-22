/**
 * unidadesNegocioService.js
 * 
 * Servicio centralizado para obtener unidades de negocio según RBAC.
 * FASE 3.2: Reemplaza el uso de servidores como filtro visible en módulos de negocio.
 * 
 * FASE AUTH-SECURITY-01:
 * - Usa api.js centralizado que maneja cookies httpOnly + token en memoria
 * 
 * PROPÓSITO:
 * - El usuario ve "Unidad de Negocio" en lugar de "Servidor"
 * - El server_id se mantiene como dato interno para llamadas al backend
 * - EDARSA HUB es el cerebro: la lógica de permisos está en el backend
 * 
 * MÓDULOS QUE USAN ESTE SERVICIO:
 * - Compras (implementado)
 * - Comercial (pendiente)
 * - Operaciones (pendiente)
 * - Finanzas (pendiente)
 */

import api from '../lib/api';
import logger from './logger';

/**
 * Obtiene las unidades de negocio disponibles para el usuario actual.
 * El backend filtra según RBAC/empresas_permitidas.
 * FASE AUTH-SECURITY-01: Auth viaja en cookie httpOnly
 * 
 * @returns {Promise<Array>} Array de unidades de negocio:
 *   - id: ID de la empresa (para identificación)
 *   - codigo: Código corto
 *   - nombre: Nombre visible ("ORIGEN", "130 QRO", etc.)
 *   - server_id: ID técnico del servidor (para llamadas internas)
 *   - system_type: Tipo de sistema origen (MPRO, SoftRestaurant)
 *   - sucursal_origen_id: ID de sucursal en sistema externo (para MPRO)
 *   - sucursales: Lista de sucursales asociadas
 */
export const fetchUnidadesNegocio = async () => {
  try {
    // FASE AUTH-SECURITY-01: Usa api.js centralizado (cookie httpOnly + token en memoria)
    logger.log('[Unidades] Iniciando fetch de unidades de negocio...');
    const response = await api.get('/unidades-negocio');
    
    logger.log(`[Unidades] Cargadas ${response.data?.length || 0} unidades de negocio`);
    return response.data || [];
  } catch (error) {
    logger.error('[Unidades] Error cargando unidades de negocio:', error);
    return [];
  }
};

/**
 * Obtiene el server_id correspondiente a una unidad de negocio.
 * Útil cuando se necesita hacer llamadas a endpoints que requieren server_id.
 * 
 * @param {Array} unidades - Array de unidades de negocio
 * @param {string} unidadId - ID de la unidad seleccionada
 * @returns {string|null} server_id o null si no se encuentra
 */
export const getServerIdFromUnidad = (unidades, unidadId) => {
  const unidad = unidades.find(u => u.id === unidadId);
  return unidad ? unidad.server_id : null;
};

/**
 * Obtiene la sucursal_origen_id correspondiente a una unidad de negocio.
 * Para sistemas MPRO que tienen múltiples sucursales en el mismo servidor.
 * 
 * @param {Array} unidades - Array de unidades de negocio
 * @param {string} unidadId - ID de la unidad seleccionada
 * @returns {string|null} sucursal_origen_id o null
 */
export const getSucursalOrigenIdFromUnidad = (unidades, unidadId) => {
  const unidad = unidades.find(u => u.id === unidadId);
  return unidad ? unidad.sucursal_origen_id : null;
};

/**
 * Obtiene el nombre de la unidad para mostrar en UI.
 * 
 * @param {Array} unidades - Array de unidades de negocio
 * @param {string} unidadId - ID de la unidad seleccionada
 * @returns {string} Nombre de la unidad o string vacío
 */
export const getUnidadNombre = (unidades, unidadId) => {
  const unidad = unidades.find(u => u.id === unidadId);
  return unidad ? unidad.nombre : '';
};

export default {
  fetchUnidadesNegocio,
  getServerIdFromUnidad,
  getSucursalOrigenIdFromUnidad,
  getUnidadNombre
};
