/**
 * EDARSA HUB - Utilidades de Caché para Modo Preview
 * ===================================================
 * P0-CACHE-PREVIEW: Limpieza automática de caché en modo preview
 * 
 * En modo preview, cada ingreso al sistema debe arrancar con caché limpia
 * para evitar estados corruptos de filtros, unidades, servidores, etc.
 * 
 * NO AFECTA PRODUCCIÓN - Solo actúa en ambientes preview/staging
 */

// =============================================================================
// DETECCIÓN DE MODO PREVIEW
// =============================================================================

/**
 * Detecta si la aplicación está corriendo en modo preview/staging/desarrollo
 * 
 * Criterios:
 * 1. URL contiene 'preview.emergentagent.com'
 * 2. URL contiene 'staging'
 * 3. Variable REACT_APP_PREVIEW_MODE='true'
 * 4. hostname es localhost (desarrollo local)
 * 
 * @returns {boolean} true si está en modo preview
 */
export function isPreviewMode() {
  // Verificar variable de entorno explícita
  if (process.env.REACT_APP_PREVIEW_MODE === 'true') {
    return true;
  }
  
  // Verificar URL de preview de Emergent
  const hostname = window.location.hostname;
  if (hostname.includes('preview.emergentagent.com')) {
    return true;
  }
  
  // Verificar staging
  if (hostname.includes('staging')) {
    return true;
  }
  
  // Desarrollo local
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return true;
  }
  
  return false;
}

/**
 * Obtiene información del ambiente actual
 * @returns {Object} Información del ambiente
 */
export function getEnvironmentInfo() {
  const hostname = window.location.hostname;
  const isPreview = isPreviewMode();
  
  let environment = 'production';
  if (hostname.includes('preview.emergentagent.com')) {
    environment = 'preview';
  } else if (hostname.includes('staging')) {
    environment = 'staging';
  } else if (hostname === 'localhost' || hostname === '127.0.0.1') {
    environment = 'development';
  }
  
  return {
    environment,
    isPreview,
    hostname,
    timestamp: new Date().toISOString()
  };
}


// =============================================================================
// LLAVES DE CACHÉ A LIMPIAR
// =============================================================================

const EDARSA_CACHE_KEYS = [
  // Auth y Token - EXCLUIDOS del cache reset para mantener sesión
  // 'edarsa_memory_token', // EXCLUIDO: Necesario para API calls
  // 'auth_token', // EXCLUIDO: Necesario para API calls
  // 'token', // EXCLUIDO: Necesario para API calls
  // 'user', // EXCLUIDO: Estado de sesión
  // 'currentUser', // EXCLUIDO: Estado de sesión
  
  // Selecciones
  'selectedServer',
  'selectedUnidadNegocio',
  'selectedEmpresa',
  'unidad_negocio_id',
  'empresa_id',
  
  // Catálogos
  'servers',
  'servidores',
  'unidades',
  'unidades_negocio',
  'empresas',
  
  // Dashboard y Módulos
  'dashboard',
  'dashboard_cache',
  'comercial',
  'comercial_cache',
  'finanzas',
  'finanzas_cache',
  'operaciones',
  'operaciones_cache',
  'catalogo',
  'catalogo_cache',
  'compras',
  'compras_cache',
  
  // RBAC y Permisos
  'rbac',
  'permisos',
  'permissions',
  'allowed_servers',
  'allowed_empresas',
  
  // Filtros
  'filtros',
  'filters',
  'dateRange',
  'fechaInicio',
  'fechaFin',
  
  // KPIs
  'kpis_cache',
  'ventas_cache',
  'resumen_cache',
  
  // Otros
  'edarsa_',
  'edarsahub_',
];

// Marcador de sesión para evitar limpieza repetida
const CACHE_RESET_MARKER = 'edarsa_preview_cache_reset_done';
const BUILD_VERSION = process.env.REACT_APP_VERSION || Date.now().toString();


// =============================================================================
// FUNCIONES DE LIMPIEZA
// =============================================================================

/**
 * Limpia localStorage de llaves relacionadas con EDARSAHUB
 * @returns {number} Número de llaves limpiadas
 */
function clearLocalStorage() {
  let count = 0;
  const keysToRemove = [];
  
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && shouldClearKey(key)) {
      keysToRemove.push(key);
    }
  }
  
  keysToRemove.forEach(key => {
    localStorage.removeItem(key);
    count++;
  });
  
  return count;
}

/**
 * Limpia sessionStorage de llaves relacionadas con EDARSAHUB
 * @returns {number} Número de llaves limpiadas
 */
function clearSessionStorage() {
  let count = 0;
  const keysToRemove = [];
  
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    // No limpiar el marcador de reset ni el token activo
    if (key && shouldClearKey(key) && key !== CACHE_RESET_MARKER) {
      keysToRemove.push(key);
    }
  }
  
  keysToRemove.forEach(key => {
    sessionStorage.removeItem(key);
    count++;
  });
  
  return count;
}

/**
 * Determina si una llave debe ser limpiada
 * @param {string} key - Nombre de la llave
 * @returns {boolean}
 */
function shouldClearKey(key) {
  const lowerKey = key.toLowerCase();
  
  // NUNCA limpiar llaves de autenticación/sesión: borrarlas provoca logout y
  // carreras de 401/403 en recarga dura (el token se reconstruía tarde).
  const NEVER_CLEAR = [
    'edarsa_memory_token',
    'token',
    'access_token',
    'auth_token',
    'user',
    'edarsa_preview_cache_reset_done',

    // Preferencias visuales del usuario. No son sesión ni datos sensibles.
    'edarsahub_sql_enterprise_menu_cache_v1',
    'edarsahub_sidebar_collapsed',
    'edarsahub_menu_favorites',
  ];
  if (NEVER_CLEAR.includes(lowerKey)) return false;
  
  // Verificar prefijos conocidos
  if (lowerKey.startsWith('edarsa')) return true;
  if (lowerKey.startsWith('edarsahub')) return true;
  
  // Verificar llaves específicas
  for (const cacheKey of EDARSA_CACHE_KEYS) {
    if (lowerKey === cacheKey.toLowerCase()) return true;
    if (lowerKey.includes(cacheKey.toLowerCase())) return true;
  }
  
  return false;
}

/**
 * Limpia Cache API del navegador (si existe)
 * @returns {Promise<number>} Número de caches limpiados
 */
async function clearBrowserCaches() {
  if (!('caches' in window)) {
    return 0;
  }
  
  let count = 0;
  try {
    const cacheNames = await caches.keys();
    for (const name of cacheNames) {
      // Solo limpiar caches relacionados con EDARSAHUB
      if (name.includes('edarsa') || name.includes('edarsahub') || name.includes('workbox')) {
        await caches.delete(name);
        count++;
      }
    }
  } catch (e) {
    console.warn('[PREVIEW_CACHE_RESET] Error limpiando browser caches:', e);
  }
  
  return count;
}

/**
 * Limpia React Query cache (si está disponible globalmente)
 * @param {Object} queryClient - Instancia de QueryClient de React Query
 * @returns {boolean}
 */
export function clearReactQueryCache(queryClient) {
  if (!queryClient) return false;
  
  try {
    // Limpiar todas las queries
    queryClient.clear();
    
    // Invalidar queries específicas si están en caché
    const queryKeysToInvalidate = [
      ['servers'],
      ['servidores'],
      ['unidades'],
      ['unidades-negocio'],
      ['empresas'],
      ['comercial'],
      ['dashboard'],
      ['finanzas'],
      ['operaciones'],
      ['catalogo-sql'],
      ['auth', 'me'],
      ['rbac'],
    ];
    
    queryKeysToInvalidate.forEach(key => {
      try {
        queryClient.invalidateQueries({ queryKey: key });
      } catch (e) {
        // Ignorar si la query no existe
      }
    });
    
    console.log('[PREVIEW_CACHE_RESET] React Query cache cleared');
    return true;
  } catch (e) {
    console.warn('[PREVIEW_CACHE_RESET] Error clearing React Query cache:', e);
    return false;
  }
}


// =============================================================================
// FUNCIÓN PRINCIPAL DE LIMPIEZA
// =============================================================================

/**
 * Ejecuta limpieza completa de caché frontend en modo preview.
 * Solo ejecuta una vez por sesión (a menos que cambie la versión).
 * 
 * @param {Object} options - Opciones de limpieza
 * @param {boolean} options.force - Forzar limpieza aunque ya se haya hecho
 * @param {Object} options.queryClient - QueryClient de React Query (opcional)
 * @returns {Object} Resultado de la limpieza
 */
export async function clearPreviewFrontendCache(options = {}) {
  const { force = false, queryClient = null } = options;
  
  // Solo ejecutar en modo preview
  if (!isPreviewMode()) {
    return {
      executed: false,
      reason: 'Not in preview mode',
      environment: getEnvironmentInfo()
    };
  }
  
  // Verificar si ya se hizo la limpieza en esta sesión
  const lastReset = sessionStorage.getItem(CACHE_RESET_MARKER);
  if (!force && lastReset === BUILD_VERSION) {
    return {
      executed: false,
      reason: 'Already reset this session',
      lastReset
    };
  }
  
  console.log('[PREVIEW_CACHE_RESET] Starting cache cleanup...');
  
  const result = {
    executed: true,
    timestamp: new Date().toISOString(),
    environment: getEnvironmentInfo(),
    cleared: {
      localStorage: 0,
      sessionStorage: 0,
      browserCaches: 0,
      reactQuery: false
    }
  };
  
  try {
    // 1. Limpiar localStorage
    result.cleared.localStorage = clearLocalStorage();
    console.log(`[PREVIEW_CACHE_RESET] localStorage cleared: ${result.cleared.localStorage} keys`);
    
    // 2. Limpiar sessionStorage (excepto marcador)
    result.cleared.sessionStorage = clearSessionStorage();
    console.log(`[PREVIEW_CACHE_RESET] sessionStorage cleared: ${result.cleared.sessionStorage} keys`);
    
    // 3. Limpiar Browser Caches
    result.cleared.browserCaches = await clearBrowserCaches();
    console.log(`[PREVIEW_CACHE_RESET] Browser caches cleared: ${result.cleared.browserCaches}`);
    
    // 4. Limpiar React Query (si se proporciona)
    if (queryClient) {
      result.cleared.reactQuery = clearReactQueryCache(queryClient);
    }
    
    // 5. Marcar que ya se hizo la limpieza
    sessionStorage.setItem(CACHE_RESET_MARKER, BUILD_VERSION);
    
    console.log('[PREVIEW_CACHE_RESET] Cache cleanup completed', result);
    
  } catch (e) {
    console.error('[PREVIEW_CACHE_RESET] Error during cleanup:', e);
    result.error = e.message;
  }
  
  return result;
}


/**
 * Limpieza de caché al hacer logout (siempre ejecuta en preview)
 */
export function clearCacheOnLogout() {
  if (!isPreviewMode()) return;
  
  console.log('[PREVIEW_CACHE_RESET] Clearing cache on logout...');
  
  // Limpiar todo excepto el marcador
  clearLocalStorage();
  clearSessionStorage();
  
  // Remover marcador para que se limpie de nuevo al próximo login
  sessionStorage.removeItem(CACHE_RESET_MARKER);
}


/**
 * Llamar al backend para limpiar cachés del servidor (solo admin)
 * 
 * @param {Object} api - Instancia de axios configurada
 * @returns {Promise<Object>} Resultado de la limpieza del backend
 */
export async function clearPreviewBackendCache(api) {
  if (!isPreviewMode()) {
    return { executed: false, reason: 'Not in preview mode' };
  }
  
  try {
    const response = await api.post('/admin/cache/clear-preview');
    console.log('[PREVIEW_CACHE_RESET] Backend cache cleared:', response.data);
    return response.data;
  } catch (e) {
    // Si falla (ej. no tiene permisos), no es crítico
    console.warn('[PREVIEW_CACHE_RESET] Could not clear backend cache:', e.message);
    return { executed: false, error: e.message };
  }
}


// =============================================================================
// EXPORTS
// =============================================================================

export default {
  isPreviewMode,
  getEnvironmentInfo,
  clearPreviewFrontendCache,
  clearReactQueryCache,
  clearCacheOnLogout,
  clearPreviewBackendCache,
};
