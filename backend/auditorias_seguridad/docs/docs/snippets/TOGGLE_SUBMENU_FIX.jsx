// =============================================================================
// SNIPPET: CORRECCIÓN TOGGLE SUBMENÚ - CIERRE REACTIVO
// OBJETIVO: Evitar propagación y garantizar que el evento no se pierda
// =============================================================================

// Este bloque corrige la función de cierre y asegura que el evento no se pierda
const toggleSubMenu = (e) => {
  // 1. Evitar propagación para no activar elementos padres accidentalmente
  e.stopPropagation();
  e.preventDefault();

  // 2. Forzar actualización del estado de reactividad
  setIsExpanded((prev) => {
    const newState = !prev;
    console.log("Cambiando estado de CRM a:", newState);
    return newState;
  });
};

// Asegurar que el icono de la flecha tenga el evento vinculado
<div 
  className="menu-arrow" 
  onClick={(e) => toggleSubMenu(e)}
  role="button"
  aria-label="Cerrar submenú"
>
  {isExpanded ? <ChevronDown /> : <ChevronRight />}
</div>
