// /app/frontend/src/components/BarraLateral.jsx
// Componente de navegación lateral con lógica de Acordeón Exclusivo

import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronDown, ChevronRight } from 'lucide-react';
import api from '@/lib/api';
import { menuFallback, subMenusFallback } from '@/config/menuFallback';

const BarraLateral = ({ onClose }) => {
  const location = useLocation();
  
  // 1. ESTADO ÚNICO CENTRALIZADO: Solo un menú puede estar abierto a la vez
  const [activeMenuId, setActiveMenuId] = useState(null);
  
  // Estados de carga y datos
  const [menus, setMenus] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [useFallback, setUseFallback] = useState(false);

  // 2. CARGA DE MENÚS CON FALLBACK AUTOMÁTICO Y TIMEOUT
  useEffect(() => {
    const cargarMenus = async () => {
      setIsLoading(true);
      
      // Definimos un timeout de seguridad para forzar el fallback si la API se cuelga
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout de API')), 5000)
      );

      try {
        // Intentamos la petición con race para asegurar que no se quede pensando
        const response = await Promise.race([
          api.get('/sistema/menus/usuario'),
          timeoutPromise
        ]);
        
        setMenus(response.data);
        setUseFallback(false);
      } catch (error) {
        console.error("Fallo en API (502/Timeout). Ejecutando fallback de emergencia:", error);
        
        // FORZADO: Aplicamos el menuFallback inmediatamente
        setMenus(menuFallback);
        setUseFallback(true);
      } finally {
        // Garantizamos que el loader se desactive SIEMPRE
        setIsLoading(false);
      }
    };

    cargarMenus();
  }, []);

  // 3. LÓGICA DE ACORDEÓN EXCLUSIVO
  const toggleSubMenu = (e, menuId) => {
    // Evitar propagación absoluta para no activar elementos padres
    e.stopPropagation();
    e.preventDefault();

    // Si el menú clicado es el mismo que está abierto, lo cierra
    // Si es diferente, abre el nuevo y cierra el anterior automáticamente
    setActiveMenuId((prevId) => {
      const newId = prevId === menuId ? null : menuId;
      console.log(`[Acordeón] ${menuId}: ${prevId === menuId ? 'CERRADO' : 'ABIERTO'}`);
      return newId;
    });
  };

  // 4. OBTENER SUBMENÚS (desde API o fallback)
  const getSubMenus = (menuId) => {
    if (useFallback) {
      return subMenusFallback[menuId] || [];
    }
    // Si viene de la API, los submenús están en el objeto del menú
    const menu = menus.find(m => m.id === menuId || m.codigo === menuId);
    return menu?.menus || menu?.submenus || [];
  };

  // 5. RENDERIZADO
  if (isLoading) {
    return (
      <nav className="barra-lateral p-4">
        <div className="animate-pulse space-y-3">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-10 bg-zinc-700 rounded" />
          ))}
        </div>
      </nav>
    );
  }

  return (
    <nav className="barra-lateral">
      {/* Indicador de modo fallback (solo desarrollo) */}
      {process.env.NODE_ENV === 'development' && useFallback && (
        <div className="px-4 py-1 text-[9px] text-amber-500 bg-amber-500/10">
          Modo Fallback Activo
        </div>
      )}

      {menus.map((menu) => {
        const menuId = menu.id || menu.codigo;
        const isExpanded = activeMenuId === menuId;
        const subMenus = getSubMenus(menuId);
        const hasSubMenus = subMenus.length > 0;
        const isActive = location.pathname.startsWith(menu.path);

        return (
          <div key={menuId} className="menu-item-container">
            {/* Header del menú */}
            <div 
              className={`menu-header flex items-center justify-between px-4 py-3 cursor-pointer transition-colors ${
                isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
              }`}
              role="button"
              aria-expanded={isExpanded}
              aria-label={`Alternar ${menu.label}`}
              onClick={(e) => hasSubMenus ? toggleSubMenu(e, menuId) : null}
            >
              <Link 
                to={menu.path}
                onClick={(e) => {
                  if (hasSubMenus) {
                    e.preventDefault();
                    toggleSubMenu(e, menuId);
                  } else if (onClose) {
                    onClose();
                  }
                }}
                className="flex items-center gap-3 flex-1"
              >
                <span className="font-medium">{menu.label}</span>
                {menu.isSatelite && (
                  <span className="text-[9px] px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded">
                    SAT
                  </span>
                )}
              </Link>
              
              {/* Flecha de expansión */}
              {hasSubMenus && (
                <button
                  onClick={(e) => toggleSubMenu(e, menuId)}
                  className="p-1 hover:bg-zinc-700 rounded"
                  aria-label={isExpanded ? 'Cerrar submenú' : 'Abrir submenú'}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </button>
              )}
            </div>

            {/* Submenús con renderizado condicional */}
            {hasSubMenus && isExpanded && (
              <div className="submenu ml-4 border-l border-zinc-700 pl-3 space-y-1">
                {subMenus.map((item) => {
                  const isSubActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.id}
                      to={item.path}
                      onClick={onClose}
                      className={`block px-3 py-2 text-sm rounded transition-colors ${
                        isSubActive 
                          ? 'bg-zinc-800 text-white' 
                          : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                      }`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
};

export default BarraLateral;
