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
 * 
 * FASE 7 (Dic-2025):
 * - Migración a Catálogo Maestro de Sistemas y Capacidades
 * - Usa /api/catalogos/sistemas-capacidades/explorables para filtro dinámico
 * - Elimina hardcoding de SOFTRESTAURANT/MPRO/API_LOCAL
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
 *   - sistema_codigo: MPRO, SOFTRESTAURANT, API_LOCAL, etc.
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
 * Obtiene sistemas con capacidad EXPLORADOR_BD desde el Catálogo Maestro.
 * 
 * Endpoint: /api/catalogos/sistemas-capacidades/explorables
 * 
 * Este endpoint retorna los sistemas que tienen capacidad EXPLORADOR_BD activa
 * en EDARSAHUB SQL.
 * 
 * @returns {Promise<Array>} Array de sistemas explorables:
 *   - Codigo: Código del sistema
 *   - Descripcion: Nombre legible
 */
export const fetchSistemasDisponibles = async () => {
  try {
    // RESTAURADO: Usar endpoint estable del Catálogo Maestro
    // El endpoint dinámico causaba regresiones en múltiples pantallas
    const response = await api.get('/catalogos/sistemas-capacidades/explorables');
    
    if (response.data?.success && response.data?.data) {
      const sistemas = response.data.data.map(s => ({
        Codigo: s.codigo_sistema,
        Descripcion: s.nombre_sistema
      }));
      
      logger.debug(`[Explorador] Sistemas explorables: ${sistemas.length}`);
      return sistemas;
    }
    
    return [];
  } catch (error) {
    logger.error('Error cargando sistemas desde Catálogo Maestro:', error);
    
    // Fallback: Usar endpoint legacy si el Catálogo Maestro falla
    try {
      logger.warn('[Explorador] Intentando fallback a /catalogos/sistemas/activos');
      const fallbackResponse = await api.get('/catalogos/sistemas/activos');
      
      if (fallbackResponse.data?.success && fallbackResponse.data?.data) {
        return fallbackResponse.data.data;
      }
    } catch (fallbackError) {
      logger.error('Error en fallback de sistemas:', fallbackError);
    }
    
    return [];
  }
};

/**
 * FASE 7: Obtiene sistemas con capacidad de Sync Ventas desde Catálogo Maestro.
 * 
 * Endpoint: /api/catalogos/sistemas-capacidades/sync-ventas
 * 
 * IMPORTANTE: API_LOCAL NO aparece aquí porque no tiene capacidades SYNC_VENTAS_* activas.
 * 
 * @returns {Promise<Array>} Array de sistemas con sync ventas:
 *   - Codigo: Código del sistema
 *   - Descripcion: Nombre legible
 *   - sync_capabilities: Array de capacidades activas
 */
export const fetchSistemasSyncVentas = async () => {
  try {
    const response = await api.get('/catalogos/sistemas-capacidades/sync-ventas');
    
    if (response.data?.success && response.data?.data) {
      const sistemas = response.data.data.map(s => ({
        Codigo: s.codigo_sistema,
        Descripcion: s.nombre_sistema,
        sync_capabilities: s.sync_capabilities || []
      }));
      
      logger.debug(`[Explorador] Sistemas sync ventas: ${sistemas.length}`);
      return sistemas;
    }
    
    return [];
  } catch (error) {
    logger.error('Error cargando sistemas sync ventas:', error);
    return [];
  }
};

/**
 * FASE 7: Normaliza un system_type a su código canónico.
 * 
 * Útil para validar variantes como "ManagmentPro" -> "MPRO"
 * 
 * @param {string} systemType - Variante de nombre de sistema
 * @returns {Promise<Object>} Resultado de normalización
 */
export const normalizarSystemType = async (systemType) => {
  if (!systemType) return null;
  
  try {
    const response = await api.get(`/catalogos/sistemas-capacidades/normalizar/${encodeURIComponent(systemType)}`);
    
    if (response.data?.success && response.data?.data) {
      return response.data.data;
    }
    
    return null;
  } catch (error) {
    logger.error(`Error normalizando system_type ${systemType}:`, error);
    return null;
  }
};

/**
 * FASE 7: Obtiene diagnóstico completo de un sistema.
 * 
 * @param {string} systemType - Código o variante del sistema
 * @returns {Promise<Object>} Diagnóstico con capacidades, visibilidad, etc.
 */
export const diagnosticarSistema = async (systemType) => {
  if (!systemType) return null;
  
  try {
    const response = await api.get(`/catalogos/sistemas-capacidades/diagnostico/${encodeURIComponent(systemType)}`);
    
    if (response.data?.success && response.data?.data) {
      return response.data.data;
    }
    
    return null;
  } catch (error) {
    logger.error(`Error en diagnóstico de sistema ${systemType}:`, error);
    return null;
  }
};

export default {
  fetchConexionesExplorables,
  fetchSistemasDisponibles,
  fetchSistemasSyncVentas,
  normalizarSystemType,
  diagnosticarSistema
};
