/**
 * ProtectedRoute - Wrapper para rutas que requieren autenticación
 * Solo verifica auth para rutas del CRM principal, no para portales externos
 */
import { Navigate, useLocation } from 'react-router-dom';
import { isAuthenticated } from '@/lib/auth';

export function ProtectedRoute({ children }) {
  const location = useLocation();
  const path = location.pathname;
  
  // IMPORTANTE: No proteger portales externos
  const isExternalPortal = path.startsWith('/portal-proveedores') || 
                           path.startsWith('/inteligencia-comercial');
  
  if (isExternalPortal) {
    // No verificar auth para portales externos
    return children;
  }
  
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

export default ProtectedRoute;
