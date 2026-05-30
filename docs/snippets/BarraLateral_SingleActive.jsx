import React, { useState } from 'react';

// Este componente maneja la lógica de navegación de forma centralizada
const BarraLateral = ({ menus }) => {
  // 1. ESTADO ÚNICO: Reemplaza múltiples estados rígidos (isExpandedCRM, isExpandedComercial, etc.)
  // 'activeMenuId' mantiene el ID del único menú que debe estar abierto.
  const [activeMenuId, setActiveMenuId] = useState(null);

  // 2. LÓGICA DE ACORDEÓN EXCLUSIVO: 
  // Esta función maestra maneja la apertura y cierre automático de cualquier submenú.
  const toggleSubMenu = (e, menuId) => {
    // Evita propagación para que el clic no afecte a elementos padres
    e.stopPropagation();
    e.preventDefault();

    // Si el menú clicado es el mismo que está abierto, lo cierra (null). 
    // Si es diferente, abre el nuevo y cierra el anterior automáticamente.
    setActiveMenuId((prevId) => (prevId === menuId ? null : menuId));
    
    console.log(`Estado cambiado: ${menuId} es ahora ${activeMenuId === menuId ? 'cerrado' : 'abierto'}`);
  };

  return (
    <nav className="barra-lateral">
      {menus.map((menu) => (
        <div key={menu.id} className="menu-item-container">
          <div 
            className="menu-header"
            role="button"
            aria-expanded={activeMenuId === menu.id}
            aria-label={`Alternar ${menu.label}`}
            onClick={(e) => toggleSubMenu(e, menu.id)} // 3. INDEPENDENCIA: Cada flecha invoca esta función con su ID
          >
            <span>{menu.label}</span>
            <span className={`arrow ${activeMenuId === menu.id ? 'open' : ''}`}>
              ▼
            </span>
          </div>

          {/* Renderizado condicional basado en el ID centralizado */}
          {activeMenuId === menu.id && (
            <div className="submenu">
              {menu.items.map((item) => (
                <div key={item.id} className="submenu-item">
                  {item.label}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </nav>
  );
};

export default BarraLateral;
