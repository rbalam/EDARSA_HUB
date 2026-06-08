/**
 * EDARSA HUB - AuthContext
 * ========================
 * Contexto centralizado para manejo de autenticación.
 * 
 * FASE AUTH-SECURITY-01:
 * - Intenta usar cookies httpOnly como método primario
 * - Fallback: token en memoria + header Authorization (para entornos donde CORS bloquea cookies)
 * - El token NUNCA se guarda en localStorage/sessionStorage (seguridad XSS)
 * - Solo se cachea 'user' para UI mientras se verifica con servidor
 * 
 * P0-CACHE-PREVIEW:
 * - En modo preview, limpia cachés automáticamente al iniciar
 * - Evita estados corruptos de filtros, unidades, servidores
 * 
 * Uso:
 *   import { useAuth } from '@/contexts/AuthContext';
 *   const { user, login, logout, isAuthenticated } = useAuth();
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { getSessionUser, setSessionUser, clearSession } from '../services/authStorage';
import api, { setMemoryToken, clearMemoryToken } from '../lib/api';
import { isPreviewMode, clearPreviewFrontendCache, clearCacheOnLogout, clearPreviewBackendCache } from '../lib/previewCacheUtils';

// Crear el contexto
const AuthContext = createContext(null);

/**
 * AuthProvider - Componente que envuelve la app y provee el contexto de auth
 */
export function AuthProvider({ children }) {
  // Estado del usuario (cache para UI)
  const [user, setUser] = useState(() => getSessionUser());
  const [loading, setLoading] = useState(true);
  const cacheResetDone = useRef(false);

  /**
   * P0-CACHE-PREVIEW: Limpiar cachés al montar en modo preview
   */
  useEffect(() => {
    const initPreviewCache = async () => {
      if (isPreviewMode() && !cacheResetDone.current) {
        console.log('[PREVIEW_CACHE_RESET] Initializing cache cleanup on app mount...');
        const result = await clearPreviewFrontendCache({ force: false });
        console.log('[PREVIEW_CACHE_RESET] Initial cleanup result:', result);
        cacheResetDone.current = true;
      }
    };
    
    initPreviewCache();
  }, []);

  /**
   * Verificar sesión al montar
   * FASE AUTH-SECURITY-01: Verificar con /api/auth/me (lee cookie httpOnly)
   * FASE FILTRO-FIX: También setea token en memoria para CORS fallback
   */
  useEffect(() => {
    const verifySession = async () => {
      try {
        // Intentar obtener usuario desde el servidor (usa cookie httpOnly)
        const response = await api.get('/auth/me');
        const serverUser = response.data;
        
        // Actualizar cache y estado
        setSessionUser(serverUser);
        setUser(serverUser);
        
        // FASE FILTRO-FIX: Si el servidor retorna un token, setearlo en memoria
        // Esto permite que las llamadas API funcionen sin cookies (CORS fallback)
        if (serverUser.token) {
          setMemoryToken(serverUser.token);
        }
        
        // P0-CACHE-PREVIEW: Limpiar caché del backend si es admin en preview
        if (isPreviewMode() && (serverUser.role === 'SuperAdministrador' || serverUser.role === 'Administrador')) {
          try {
            await clearPreviewBackendCache(api);
          } catch (e) {
            // No es crítico si falla
            console.debug('[PREVIEW_CACHE_RESET] Backend cache clear skipped:', e.message);
          }
        }
      } catch (error) {
        // Sin sesión válida o error de conexión
        // Limpiar cualquier cache local
        clearSession();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifySession();
  }, []);

  /**
   * Login - Envía credenciales y maneja tanto cookie como token en memoria
   * FASE AUTH-SECURITY-01: Cookie httpOnly como primario, memoria como fallback
   */
  const login = useCallback(async (email, password) => {
    try {
      // El servidor setea la cookie httpOnly en la respuesta
      // También retorna el token para fallback cuando CORS bloquea cookies
      const response = await api.post('/auth/login', { email, password });
      const userData = response.data.user;
      const token = response.data.token;
      
      // Guardar token en memoria (NO en storage) como fallback para CORS
      if (token) {
        setMemoryToken(token);
      }
      
      // Cachear user para UI (no el token)
      setSessionUser(userData);
      setUser(userData);
      
      return { success: true, user: userData };
    } catch (error) {
      throw error;
    }
  }, []);

  /**
   * Login legacy - Para compatibilidad con Login.js actual
   * Recibe token y user directamente
   * P0-CACHE-PREVIEW: Limpia cachés antes de cargar datos frescos
   */
  const loginWithData = useCallback(async (token, userData) => {
    // P0-CACHE-PREVIEW: Limpiar cachés antes de login para estado limpio
    if (isPreviewMode()) {
      await clearPreviewFrontendCache({ force: true });
    }
    
    // Guardar token en memoria como fallback para CORS
    if (token) {
      setMemoryToken(token);
    }
    // Cachear user para UI
    setSessionUser(userData);
    setUser(userData);
    
    // P0-CACHE-PREVIEW: Intentar limpiar caché del backend
    if (isPreviewMode() && (userData?.role === 'SuperAdministrador' || userData?.role === 'Administrador')) {
      try {
        await clearPreviewBackendCache(api);
      } catch (e) {
        console.debug('[PREVIEW_CACHE_RESET] Backend cache clear on login skipped:', e.message);
      }
    }
  }, []);

  /**
   * Logout - Limpia sesión llamando al backend
   * FASE AUTH-SECURITY-01: El backend elimina la cookie httpOnly
   * P0-CACHE-PREVIEW: Limpia cachés en modo preview
   */
  const logout = useCallback(async () => {
    try {
      // P0-CACHE-PREVIEW: Limpiar cachés antes de logout
      if (isPreviewMode()) {
        clearCacheOnLogout();
      }
      
      // Llamar al backend para eliminar la cookie httpOnly
      await api.post('/auth/logout');
    } catch (error) {
      // Ignorar errores de logout (ej: ya no hay sesión)
      console.debug('Logout request failed, clearing local state anyway');
    } finally {
      // Siempre limpiar estado local Y token en memoria
      clearMemoryToken();
      clearSession();
      setUser(null);
    }
  }, []);

  /**
   * Actualizar usuario (ej: después de editar perfil)
   */
  const updateUser = useCallback((updatedUser) => {
    setSessionUser(updatedUser);
    setUser(updatedUser);
  }, []);

  /**
   * Verificar si está autenticado
   * NOTA: Esto solo verifica si hay user cacheado
   * La autenticación real la verifica el servidor con la cookie
   */
  const isAuthenticated = useMemo(() => !!user, [user]);

  /**
   * Verificar roles
   */
  const hasRole = useCallback((requiredRole) => {
    if (!user) return false;
    
    const roles = ['Usuario', 'Supervisor', 'Administrador'];
    const userRoleIndex = roles.indexOf(user.role);
    const requiredRoleIndex = roles.indexOf(requiredRole);
    
    return userRoleIndex >= requiredRoleIndex;
  }, [user]);

  /**
   * Verificar si es admin
   */
  const isAdmin = useMemo(() => {
    return user?.role === 'Administrador' || user?.role === 'admin' || user?.role === 'SuperAdministrador';
  }, [user]);

  // Valor del contexto
  const value = useMemo(() => ({
    // Estado
    user,
    loading,
    isAuthenticated,
    isAdmin,
    
    // Acciones
    login: loginWithData,  // Para compatibilidad con Login.js actual
    loginAsync: login,     // Nuevo método async
    logout,
    updateUser,
    hasRole,
    // FASE AUTH-SECURITY-01 / FASE 4.2: Funciones deprecated eliminadas
    // token, getToken, authHeaders, getAuthHeaders ya no existen
  }), [user, loading, isAuthenticated, isAdmin, loginWithData, login, logout, updateUser, hasRole]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth - Hook para acceder al contexto de auth
 * 
 * Uso:
 *   const { user, login, logout } = useAuth();
 */
export function useAuth() {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  
  return context;
}

/**
 * withAuth - HOC para componentes de clase (legacy)
 */
export function withAuth(Component) {
  return function AuthenticatedComponent(props) {
    const auth = useAuth();
    return <Component {...props} auth={auth} />;
  };
}

// Export default para compatibilidad
export default AuthContext;
