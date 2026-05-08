/**
 * serversService.js
 * 
 * Servicio centralizado para el consumo de /api/servers
 * PROPÓSITO: Eliminar duplicación de código sin modificar endpoints existentes
 * 
 * FASE AUTH-SECURITY-01 / FASE 4:
 * - Migrado a cookie httpOnly (withCredentials)
 * - getAccessToken ya no se usa
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

import axios from 'axios';
import logger from './logger';

const API_URL = process.env.REACT_APP_BACKEND_URL;

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
 * FASE AUTH-SECURITY-01: Auth viaja en cookie httpOnly
 * 
 * @returns {Promise<Array>} - Array de servidores operativos
 * @throws {Error} - Si falla la petición
 */
export const fetchServersOperativos = async () => {
  const response = await axios.get(`${API_URL}/api/servers`, {
    withCredentials: true
  });
  
  return filterServersOperativos(response.data);
};

/**
 * Obtiene TODOS los servidores sin filtrar (para módulo Servidores/Admin)
 * FASE AUTH-SECURITY-01: Auth viaja en cookie httpOnly
 * 
 * @returns {Promise<Array>} - Array de todos los servidores
 */
export const fetchAllServers = async () => {
  const response = await axios.get(`${API_URL}/api/servers`, {
    withCredentials: true
  });
  
  return response.data || [];
};
