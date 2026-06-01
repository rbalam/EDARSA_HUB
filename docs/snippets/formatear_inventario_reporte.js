/**
 * Formatea la etiqueta o columna del inventario para el reporte y vistas UI.
 * @param {Object} inventario - El objeto del inventario (ej. { folio: "SB-0001056", fecha: "...", almacen_nombre: "...", comentario: "..." })
 * @param {string} unidadNegocio - El nombre de la unidad (ej. "ORIGEN (MPRO)" o "LA ESTELAR")
 */
function formatearInventarioReporte(inventario, unidadNegocio) {
  // 1. Extraer los datos base garantizados
  const folio = inventario.folio || inventario.id; // Ajusta según tu base de datos
  const fecha = inventario.fecha ? inventario.fecha.split('T')[0] : ""; // Formato de fecha limpia (cortado en T)
  const almacen = inventario.almacen_nombre || inventario.nombre_almacen || "ALMACÉN DESCONOCIDO";

  // 2. Armado base (Folio - Fecha - Almacén)
  let etiquetaStr = `${folio} - ${fecha} - ${almacen}`;

  // 3. Normalizar el nombre de la unidad para identificar si es servidor MPRO
  const unidad = (unidadNegocio || "").toUpperCase();
  const esMpro = unidad.includes("ORIGEN") || 
                 unidad.includes("130° QUERETARO") || 
                 unidad.includes("QUERETARO") ||
                 unidad.includes("MPRO");

  // 4. Si es servidor MPRO y el campo comentario contiene información, se concatena
  if (esMpro && inventario.comentario && inventario.comentario.trim() !== "") {
    etiquetaStr += ` - [Comentario: ${inventario.comentario.trim()}]`;
  }

  return etiquetaStr;
}

// =======================================================
// Ejemplo de cómo aplicarlo al "Generar Reporte" o al JSON a enviar:
// =======================================================

const filtrosAEnviar = {
  unidadNegocio: unidadSeleccionada,
  // Al mapear tus inventarios iniciales y finales, usa la función
  inventariosIniciales: arrayInventariosIniciales.map(inv => ({
    ...inv,
    etiqueta_reporte: formatearInventarioReporte(inv, unidadSeleccionada)
  })),
  inventariosFinales: arrayInventariosFinales.map(inv => ({
    ...inv,
    etiqueta_reporte: formatearInventarioReporte(inv, unidadSeleccionada)
  }))
};
