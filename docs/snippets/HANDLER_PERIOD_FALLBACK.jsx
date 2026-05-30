// =============================================================================
// SNIPPET: MANEJADOR DE PERIODOS CON FALLBACK A ULTIMO PERIODO VÁLIDO
// OBJETIVO: Evitar pantallas vacías redirigiendo a datos disponibles
// =============================================================================

// Parche de seguridad para el manejador de periodos
const handlePeriodChange = async (periodo) => {
  try {
    const data = await api.get(`/api/comercial/ventas/${periodo}`);
    
    // Si no hay datos, en lugar de dar error, buscamos el periodo más reciente
    if (!data.data || data.data.length === 0) {
      console.warn("Periodo vacío, redirigiendo a fecha con datos...");
      const latestData = await api.get('/api/comercial/ventas/ultimo_periodo_valido');
      setVentas(latestData.data);
      // Notificar al usuario sin expulsarlo
      alert("No hay datos en esta fecha, mostrando el periodo más reciente con información.");
    } else {
      setVentas(data.data);
    }
  } catch (error) {
    console.error("Error al cargar periodo:", error);
  }
};

// NOTAS DE IMPLEMENTACIÓN:
// 1. El endpoint /api/comercial/ventas/ultimo_periodo_valido debe existir en el backend
// 2. Este endpoint debe retornar el periodo más reciente que tenga datos
// 3. El alert puede ser reemplazado por un toast más elegante
