import { useState } from 'react';

/**
 * Estado canónico del período del Portal Inteligencia.
 * Soporta atajos (dia/semana/mes/anio) y rango PERSONALIZADO (fecha_inicio/fecha_fin).
 *
 * `params` entrega ya los query-params correctos para apiGet:
 *   - atajos          -> { periodo }
 *   - personalizado   -> { fecha_inicio, fecha_fin }  (solo cuando ambas fechas existen)
 * `listo` indica si se puede consultar (evita pegarle al backend con rango incompleto).
 */
export function usePeriodo(inicial = 'mes') {
  const [periodo, setPeriodo] = useState(inicial);
  const [rangoInicio, setRangoInicio] = useState('');
  const [rangoFin, setRangoFin] = useState('');

  const onRango = (ini, fin) => {
    setRangoInicio(ini || '');
    setRangoFin(fin || '');
  };

  const esCustomCompleto = periodo === 'personalizado' && !!rangoInicio && !!rangoFin;
  const listo = periodo !== 'personalizado' || esCustomCompleto;
  const params = esCustomCompleto
    ? { fecha_inicio: rangoInicio, fecha_fin: rangoFin }
    : { periodo };

  return { periodo, setPeriodo, rangoInicio, rangoFin, onRango, listo, params };
}
