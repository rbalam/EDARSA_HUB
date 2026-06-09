/**
 * Utilidades CANÓNICAS para el selector de Inventario Inicial / Final.
 * ====================================================================
 * Regla de centralización: esta lógica se usa en Análisis (Reportes.js) y
 * Auditoría (Compras.js). Fuente única de verdad para:
 *   - obtener la fecha base de un inventario,
 *   - calcular la fecha mínima de los inventarios iniciales,
 *   - filtrar los inventarios finales (solo fecha >= fecha del inicial).
 *
 * Sin estado, sin side-effects: funciones puras reutilizables.
 */

/** Normaliza la fecha de un inventario a 'YYYY-MM-DD' (soporta ISO y con espacio). */
export function getFechaBase(inv) {
  if (!inv || !inv.fecha) return null;
  return inv.fecha.split('T')[0] || inv.fecha.split(' ')[0] || null;
}

/**
 * Fecha más antigua entre los inventarios iniciales seleccionados.
 * @returns {string|null} 'YYYY-MM-DD' o null si no hay fechas.
 */
export function fechaMinimaInventarios(inventariosIniciales) {
  if (!Array.isArray(inventariosIniciales) || inventariosIniciales.length === 0) {
    return null;
  }
  const fechas = inventariosIniciales
    .map((inv) => inv?.fecha?.split('T')[0])
    .filter((f) => f);
  if (fechas.length === 0) return null;
  return fechas.sort()[0];
}

/**
 * Filtra los inventarios finales: solo los que tienen fecha >= fechaMinima.
 * Si no hay fechaMinima, devuelve todos. Inventarios sin fecha se conservan.
 */
export function filtrarInventariosFinales(inventarios, fechaMinima) {
  if (!fechaMinima) return inventarios;
  return (inventarios || []).filter((inv) => {
    const fechaInv = inv?.fecha?.split('T')[0];
    if (!fechaInv) return true; // sin fecha -> mostrar
    return fechaInv >= fechaMinima;
  });
}
