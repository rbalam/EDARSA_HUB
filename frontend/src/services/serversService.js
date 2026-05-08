/**
 * serversService.js
 * 
 * Servicio centralizado para el consumo de /api/servers
 * PROPÓSITO: Eliminar duplicación de código sin modificar endpoints existentes
 * 
 * CORRECCIÓN P0 - 2026-05-08:
 * Migrado de axios directo a cliente API centralizado para garantizar
 * envío de Authorization header cuando cookie httpOnly falla por CORS/proxy.
 * 
 * IMPORTANTE:
 * - NO modifica el endpoint /api/servers
 * - NO modifica la estructura de respuesta
 * - Solo encapsula la lógica repetida de fetch + filtro
 * 
 * MÓDULOS QUE PUEDEN USAR ESTE SERVICIO:
 * - Comercial (implementado)
 * - Compras (pendiente)
 * - Reportes (pendiente)
 * - Dashboard (pendiente)
 * - ExploradorBD (pendiente)
 * - CatalogoConsultas (pendiente)
 * - AutorizacionCompras (pendiente)
 */

// CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
import api from '../lib/api';
import logger from './logger';

/**
 * Filtra servidores que son visibles en operaciones
 * Lógica: visible_en_operaciones !== false (incluye true y undefined)
 * 
 * @param {Array} servers - Array de servidores del endpoint /api/servers
 * @returns {Array} - Servidores filtrados (solo operativos)
 */
export const filterServersOperativos = (servers) => {
  if (!Array.isArray(servers)) return [];
  return servers.filter(s => s.visible_en_operaciones !== false);
};

/**
 * Obtiene servidores operativos desde /api/servers
 * Aplica automáticamente el filtro visible_en_operaciones
 * CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
 * 
 * @returns {Promise<Array>} - Array de servidores operativos
 * @throws {Error} - Si falla la petición
 */
export const fetchServersOperativos = async () => {
  // CORRECCIÓN P0: Migrado de axios directo a api centralizado
  const response = await api.get('/servers');
  
  return filterServersOperativos(response.data);
};

/**
 * Obtiene TODOS los servidores sin filtrar (para módulo Servidores/Admin)
 * CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
 * 
 * @returns {Promise<Array>} - Array de todos los servidores
 */
export const fetchAllServers = async () => {
  // CORRECCIÓN P0: Migrado de axios directo a api centralizado
  const response = await api.get('/servers');
  
  return response.data || [];
};
