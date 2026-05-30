// =============================================================================
// SNIPPET: DASHBOARD CON DEBOUNCING Y CONTROL DE ERRORES 401/500
// OBJETIVO: Evitar re-renderizados excesivos y manejar errores sin cerrar sesión
// =============================================================================

import React, { useState, useCallback, useRef } from 'react';
import debounce from 'lodash/debounce'; // Asegúrate de tener lodash instalado

const Dashboard = () => {
  const [filter, setFilter] = useState({ month: 'Mayo', year: '2026' });
  const [statusMessage, setStatusMessage] = useState('');
  
  // 1. Implementación de 'debouncing' (500ms de espera antes de disparar la petición)
  const fetchDashboardData = useCallback(
    debounce(async (newFilter) => {
      setStatusMessage('Cargando datos...');
      try {
        const response = await api.get('/api/dashboard/data', { params: newFilter });
        // Procesar datos exitosos...
        setStatusMessage('');
      } catch (error) {
        // 3. Control de estado ante 401/500 (No cierra sesión)
        if (error.response?.status === 401 || error.response?.status === 500) {
          setStatusMessage('Error de red, reintentando carga...');
          // Implementar lógica de reintento automático aquí si es necesario
        } else {
          setStatusMessage('Error al cargar datos');
        }
      }
    }, 500),
    []
  );

  // 2. Manejador de cambios sin re-renderizar AuthContext
  const handleFilterChange = (newParams) => {
    const updatedFilter = { ...filter, ...newParams };
    setFilter(updatedFilter);
    fetchDashboardData(updatedFilter);
  };

  return (
    <div>
      {/* Indicador de estado para no perder contexto */}
      {statusMessage && <div className="status-banner">{statusMessage}</div>}
      
      {/* Controles de filtro */}
      <select onChange={(e) => handleFilterChange({ month: e.target.value })}>
        <option value="Mayo">Mayo</option>
        {/* ... */}
      </select>
    </div>
  );
};

export default Dashboard;
