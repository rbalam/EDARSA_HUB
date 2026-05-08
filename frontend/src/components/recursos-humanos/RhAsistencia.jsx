/**
 * EDARSA HUB - RH Asistencia (Placeholder)
 * ========================================
 * Control de asistencia - Módulo de reloj checador.
 * Placeholder hasta conectar con RH_Reloj_Checador.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Clock } from 'lucide-react';

/**
 * Componente placeholder de Asistencia
 * Conectará con RH_Reloj_Checador de EDARSA HUB
 */
export default function RhAsistencia() {
  return (
    <Card className="border-2 border-dashed border-zinc-300" data-testid="rh-asistencia">
      <CardContent className="py-12 text-center">
        <Clock className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-zinc-600 mb-2">Control de Asistencia</h3>
        <p className="text-zinc-400 text-sm">
          Módulo de reloj checador en desarrollo.<br />
          Conectará con RH_Reloj_Checador de EDARSA HUB.
        </p>
        
        {/* Próximas funcionalidades */}
        <div className="mt-6 pt-6 border-t border-dashed border-zinc-200">
          <p className="text-xs text-zinc-400 mb-3">Funcionalidades planeadas:</p>
          <div className="flex flex-wrap justify-center gap-2">
            <span className="px-2 py-1 bg-zinc-100 text-zinc-500 rounded text-xs">Registro de entrada/salida</span>
            <span className="px-2 py-1 bg-zinc-100 text-zinc-500 rounded text-xs">Reportes de asistencia</span>
            <span className="px-2 py-1 bg-zinc-100 text-zinc-500 rounded text-xs">Gestión de turnos</span>
            <span className="px-2 py-1 bg-zinc-100 text-zinc-500 rounded text-xs">Horas extras</span>
            <span className="px-2 py-1 bg-zinc-100 text-zinc-500 rounded text-xs">Sincronización biométrica</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
