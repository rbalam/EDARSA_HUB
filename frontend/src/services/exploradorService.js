/**
 * exploradorService.js
 * 
 * Servicio para el Explorador de Base de Datos.
 * 
 * CORRECCIÓN P1 (2026-05-15):
 * - Usa endpoint dedicado /api/explorador/conexiones-explorables
 * - Lista TODAS las conexiones explorables activas desde EDARSAHUB
 * - No está limitado a unidades operativas
 * - Incluye nuevos servidores y sistemas del catálogo
 */

import api from '../lib/api';
import logger from './logger';

/**
 * Obtiene todas las conexiones explorables activas.
 * 
 * Diferencia con unidades de negocio:
 * - Unidades de negocio: empresas operativas con permisos RBAC
 * - Conexiones explorables: servidores técnicamente accesibles para administración
 * 
 * @returns {Promise<Array>} Array de conexiones explorables:
 *   - id: ID de la conexión/servidor
 *   - nombre: Nombre visible
 *   - sistema_codigo: MPRO, SOFTRESTAURANT, SAP_BUSINESS_ONE, etc.
 *   - sistema_descripcion: Descripción legible
 *   - tipo_conexion: SQL_SERVER, API_LOCAL, DATA_SOURCE
 *   - host: Host (sin credenciales)
 *   - database: Nombre de la base de datos
 *   - activo: Boolean
 *   - explorable: Boolean derivado
 */
export const fetchConexionesExplorables = async () => {
  try {
    const response = await api.get('/explorador/conexiones-explorables');
    
    if (response.data?.success && response.data?.data) {
      logger.debug(`[Explorador] Cargadas ${response.data.data.length} conexiones explorables`);
      return response.data.data;
    }
    
    return response.data || [];
  } catch (error) {
    logger.error('Error cargando conexiones explorables:', error);
    return [];
  }
};

/**
 * Obtiene sistemas activos desde el catálogo.
 * Reutiliza endpoint existente de catalogos.
 * 
 * @returns {Promise<Array>} Array de sistemas:
 *   - Codigo: Código del sistema
 *   - Descripcion: Descripción legible
 */
export const fetchSistemasDisponibles = async () => {
  try {
    const response = await api.get('/catalogos/sistemas/activos');
    
    if (response.data?.success && response.data?.data) {
      return response.data.data;
    }
    
    return [];
  } catch (error) {
    logger.error('Error cargando sistemas:', error);
    return [];
  }
};

export default {
  fetchConexionesExplorables,
  fetchSistemasDisponibles
};
