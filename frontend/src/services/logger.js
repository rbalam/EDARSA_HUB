/**
 * EDARSA HUB - Logger Service
 * ===========================
 * Wrapper para logging que permite control centralizado.
 * En producción, los logs se desactivan automáticamente.
 */

const isDevelopment = process.env.NODE_ENV === 'development';
const isDebugEnabled = process.env.REACT_APP_DEBUG === 'true';

const logger = {
  /**
   * Log informativo - solo en desarrollo
   */
  log: (...args) => {
    if (isDevelopment || isDebugEnabled) {
      console.log('[EDARSA]', ...args);
    }
  },

  /**
   * Log de información importante - siempre visible
   */
  info: (...args) => {
    if (isDevelopment || isDebugEnabled) {
      console.info('[EDARSA INFO]', ...args);
    }
  },

  /**
   * Log de warning - siempre visible
   */
  warn: (...args) => {
    console.warn('[EDARSA WARN]', ...args);
  },

  /**
   * Log de error - siempre visible
   */
  error: (...args) => {
    console.error('[EDARSA ERROR]', ...args);
  },

  /**
   * Log de debug - solo con flag explícito
   */
  debug: (...args) => {
    if (isDebugEnabled) {
      console.debug('[EDARSA DEBUG]', ...args);
    }
  },

  /**
   * Log para API calls - solo en desarrollo
   */
  api: (method, url, data = null) => {
    if (isDevelopment || isDebugEnabled) {
      console.log(`[API ${method}]`, url, data ? JSON.stringify(data).substring(0, 100) : '');
    }
  },

  /**
   * Log para errores de API
   */
  apiError: (method, url, error) => {
    console.error(`[API ERROR ${method}]`, url, error?.message || error);
  },

  /**
   * Desactivar todos los logs (útil para tests)
   */
  disable: () => {
    logger._disabled = true;
  },

  /**
   * Reactivar logs
   */
  enable: () => {
    logger._disabled = false;
  },

  _disabled: false,
};

export default logger;
