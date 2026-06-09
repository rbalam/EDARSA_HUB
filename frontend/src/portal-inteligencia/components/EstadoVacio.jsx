/**
 * Estado vacío / honesto para el Portal de Inteligencia.
 * Nunca muestra datos inventados: comunica SIN_DATOS_SYNC, sesión, permiso o error.
 */
import React from 'react';
import { Database, AlertTriangle, Loader2 } from 'lucide-react';
import { ESTADO } from '../api/client';

const TEXTOS = {
  [ESTADO.SIN_DATOS]: { t: 'Sin datos sincronizados', d: 'No hay información para el período o unidad seleccionados.' },
  [ESTADO.SESION_EXPIRADA]: { t: 'Sesión expirada', d: 'Vuelve a iniciar sesión para ver estos datos.' },
  [ESTADO.SIN_PERMISO]: { t: 'Sin permiso', d: 'Tu usuario no tiene permiso para consultar esta información.' },
  [ESTADO.SIN_SESION]: { t: 'Sin sesión', d: 'Inicia sesión para ver estos datos.' },
  [ESTADO.ERROR]: { t: 'No se pudo cargar', d: 'Ocurrió un problema al consultar los datos. Intenta de nuevo.' },
  PENDIENTE_SYNC_DETALLE: { t: 'Pendiente de sincronización', d: 'Este detalle aún no está disponible en EDARSAHUB.' },
};

export function EstadoVacio({ estado, testid, compacto }) {
  const pad = compacto ? 'py-10' : 'py-20';
  if (estado === ESTADO.CARGANDO) {
    return (
      <div className={`flex flex-col items-center justify-center ${pad} text-slate-400`} data-testid={testid || 'estado-cargando'}>
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        <p className="mt-3 text-sm">Cargando…</p>
      </div>
    );
  }
  const m = TEXTOS[estado] || TEXTOS[ESTADO.SIN_DATOS];
  const danger = estado === ESTADO.ERROR || estado === ESTADO.SIN_PERMISO;
  const Icon = danger ? AlertTriangle : Database;
  return (
    <div className={`flex flex-col items-center justify-center ${pad} text-center`} data-testid={testid || `estado-${String(estado || '').toLowerCase()}`}>
      <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 ${danger ? 'bg-rose-500/15' : 'bg-slate-700/50'}`}>
        <Icon className={`h-6 w-6 ${danger ? 'text-rose-400' : 'text-slate-400'}`} />
      </div>
      <p className="text-white font-medium">{m.t}</p>
      <p className="text-sm text-slate-500 mt-1 max-w-sm">{m.d}</p>
    </div>
  );
}
