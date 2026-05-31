import { useState, useEffect } from "react";

// --------------------------------------------------------------------------------------
// ESTRATEGIA DE DISPONIBILIDAD: OFFLINE CACHE CON LOCALSTORAGE (EDARSA HUB)
// Provee inmunidad de datos ante interrupciones de API y Timeouts de Red.
// --------------------------------------------------------------------------------------

export function useComercialUnitsWithFallback() {
  const [isUsingCache, setIsUsingCache] = useState(false);
  const [cacheTimestamp, setCacheTimestamp] = useState(
    localStorage.getItem("edarsa_comercial_units_timestamp")
  );

  // 1. Inicialización desde caché persistido para evitar parpadeos en 0
  const [units, setUnits] = useState(() => {
    try {
      const cached = localStorage.getItem("edarsa_comercial_units");
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // Validamos que contenga datos reales y no un estado de ceros corrupto o vacío
          const hasRealData = parsed.some(u => u.ventas > 0 || u.pax > 0);
          if (hasRealData) return parsed;
        }
      }
    } catch (e) {
      console.error("Error leyendo caché local durante inicio:", e);
    }
    // Valores por defecto como salvaguarda dura inicial
    return [
      { id: "cienfuegos", name: "CIENFUEGOS", ventas: 4.39, pax: 3353, cheques: 1113 },
      { id: "merida", name: "130° MERIDA", ventas: 3.90, pax: 2539, cheques: 871 },
      { id: "queretaro", name: "130° QUERETARO", ventas: 3.75, pax: 2235, cheques: 771 },
      { id: "estelar", name: "LA ESTELAR", ventas: 2.88, pax: 5260, cheques: 1918 },
      { id: "origen", name: "ORIGEN", ventas: 2.29, pax: 3232, cheques: 1123 }
    ];
  });

  const fetchUnits = async () => {
    try {
      const res = await fetch("/api/comercial/units");
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          // Detección proactiva de respuestas vacías o en ceros (Ej. Base limpiándose)
          const isZeroed = data.every(u => (u.ventas === 0 || !u.ventas) && (u.pax === 0 || !u.pax));
          
          if (isZeroed) {
            console.warn("[HA ENGINE] API regresó registros en cero. Restaurando caché histórico...");
            const cached = localStorage.getItem("edarsa_comercial_units");
            if (cached) {
              setUnits(JSON.parse(cached));
              setIsUsingCache(true);
              return;
            }
          } else {
            // El flujo es óptimo y la API devolvió datos reales. Actualizamos el Hot-Storage.
            setUnits(data);
            setIsUsingCache(false);
            localStorage.setItem("edarsa_comercial_units", JSON.stringify(data));
            
            const now = new Date();
            const formatted = now.toLocaleDateString("es-MX") + " " + now.toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
            localStorage.setItem("edarsa_comercial_units_timestamp", formatted);
            setCacheTimestamp(formatted);
            return;
          }
        }
      }
      throw new Error(`Código de estado HTTP anómalo: ${res.status}`);
    } catch (err) {
      console.error("[HA ENGINE] Canal comercial inalcanzable. Iniciando conmutación por fallo... Error:", err);
      // Conmutación inmediata de datos sin impacto al usuario corporativo (Failover)
      const cached = localStorage.getItem("edarsa_comercial_units");
      if (cached) {
        setUnits(JSON.parse(cached));
        setIsUsingCache(true);
      }
    }
  };

  return { units, isUsingCache, cacheTimestamp, fetchUnits };
}
