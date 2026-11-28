import React, { useEffect, useState } from 'react';
import api from '@/lib/api';
import IncidenciaCajaForm from '@/components/finanzas/IncidenciaCajaForm';

// Gate12C: solo lectura. No permitir altas hasta certificar SQL y resolutores.
export default function IncidenciasCaja() {
  const [state, setState] = useState({ loading: true, error: '', data: null });
  useEffect(() => {
    let active = true;
    api.get('/comercial/cajas/bootstrap')
      .then(({ data }) => {
        if (active) setState({ loading: false, error: '', data });
      })
      .catch((error) => {
        if (!active) return;
        setState({
          loading: false,
          data: null,
          error: error?.response?.status === 403
            ? 'No tienes permiso para consultar incidencias de caja.'
            : 'No se pudo verificar el acceso a Cajas.',
        });
      });
    return () => { active = false; };
  }, []);

  if (state.loading) return <main><p role="status">Verificando permisos de Cajas...</p></main>;
  if (state.error) return <main><h1>Incidencias de caja</h1><p role="alert">{state.error}</p></main>;

  return <main>
    <h1>Incidencias de caja</h1>
    <p role="status">Registro no disponible hasta certificar el alcance, catalogos y persistencia SQL.</p>
    <IncidenciaCajaForm tipos={[]} motivos={[]} contexto={null} />
  </main>;
}
