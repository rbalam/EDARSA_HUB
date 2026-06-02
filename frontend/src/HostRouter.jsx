/**
 * HostRouter - Enrutamiento basado en subdominio (Host-based routing)
 * 
 * Detecta el hostname y renderiza la aplicación correspondiente:
 * - inteligencia.edarsa.com.mx → Portal Inteligencia Comercial IA
 * - proveedores.edarsa.com.mx  → Portal de Proveedores (SupplierHub)
 * - Cualquier otro dominio     → CRM Principal (EDARSAHUB)
 * 
 * Esto permite mantener TODO el código en una sola aplicación React,
 * pero servir portales independientes según el subdominio de acceso.
 */
import React, { useMemo } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'sonner';

// Aplicaciones/Portales
import MainApp from './App';
import PortalInteligenciaApp from './portal-inteligencia/App';
import PortalProveedoresApp from './portal/App';

// Configuración de subdominios → Portal
const SUBDOMAIN_CONFIG = {
  // Producción
  'inteligencia.edarsa.com.mx': 'inteligencia',
  'proveedores.edarsa.com.mx': 'proveedores',
  
  // Aliases adicionales (si se requieren)
  'ia.edarsa.com.mx': 'inteligencia',
  'suppliers.edarsa.com.mx': 'proveedores',
  'portal.edarsa.com.mx': 'proveedores',
  
  // Desarrollo/Testing local
  'inteligencia.localhost': 'inteligencia',
  'proveedores.localhost': 'proveedores',
};

// Función para detectar qué portal renderizar
function detectPortal(hostname) {
  // Normalizar hostname (lowercase, sin puerto)
  const normalizedHost = hostname.toLowerCase().split(':')[0];
  
  // Buscar coincidencia exacta en config
  if (SUBDOMAIN_CONFIG[normalizedHost]) {
    return SUBDOMAIN_CONFIG[normalizedHost];
  }
  
  // Buscar por patrón de subdominio
  const parts = normalizedHost.split('.');
  if (parts.length >= 2) {
    const subdomain = parts[0];
    
    // Detectar por prefijo de subdominio
    if (subdomain === 'inteligencia' || subdomain === 'ia' || subdomain === 'intel') {
      return 'inteligencia';
    }
    if (subdomain === 'proveedores' || subdomain === 'suppliers' || subdomain === 'portal') {
      return 'proveedores';
    }
  }
  
  // Default: CRM Principal
  return 'main';
}

export default function HostRouter() {
  // Detectar portal basado en hostname actual
  const portal = useMemo(() => {
    const hostname = window.location.hostname;
    const detected = detectPortal(hostname);
    
    // Log para debugging (solo en desarrollo)
    if (process.env.NODE_ENV === 'development') {
      console.log(`[HostRouter] Hostname: ${hostname} → Portal: ${detected}`);
    }
    
    return detected;
  }, []);

  // Renderizar el portal correspondiente
  switch (portal) {
    case 'inteligencia':
      // Portal de Inteligencia Comercial IA - Standalone
      return (
        <BrowserRouter>
          <PortalInteligenciaApp />
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      );
      
    case 'proveedores':
      // Portal de Proveedores (SupplierHub) - Standalone
      return (
        <BrowserRouter>
          <PortalProveedoresApp />
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      );
      
    case 'main':
    default:
      // CRM Principal - Ya incluye BrowserRouter internamente
      return <MainApp />;
  }
}
