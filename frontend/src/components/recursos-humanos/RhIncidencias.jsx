/**
 * EDARSA HUB - RH Incidencias
 * ===========================
 * Tabla de incidencias con filtros y acciones.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileSpreadsheet, Plus } from 'lucide-react';

/**
 * Tabla de incidencias
 */
export default function RhIncidencias({
  // Data
  incidencias = [],
  sucursales = [],
  // Filtros
  filtroSucursal,
  setFiltroSucursal,
  // Helpers
  esIncidenciaIngreso,
  // Handlers
  onAbrirImportExcel,
  onNuevaIncidencia,
}) {
  return (
    <div className="space-y-4" data-testid="rh-incidencias">
      <div className="flex flex-wrap gap-3 justify-between">
        <select
          value={filtroSucursal}
          onChange={(e) => setFiltroSucursal(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm"
          data-testid="incidencias-filter-sucursal"
        >
          <option value="">Todas las sucursales</option>
          {sucursales.map(s => (
            <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
          ))}
        </select>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onAbrirImportExcel}>
            <FileSpreadsheet className="h-4 w-4 mr-1" />
            Importar Excel
          </Button>
          <Button size="sm" className="bg-zinc-900 text-white" onClick={() => onNuevaIncidencia()}>
            <Plus className="h-4 w-4 mr-1" />
            Nueva Incidencia
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Colaborador</th>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Tipo</th>
                  <th className="text-left p-3 font-medium">Fecha</th>
                  <th className="text-right p-3 font-medium">Monto</th>
                  <th className="text-right p-3 font-medium">Unidades</th>
                </tr>
              </thead>
              <tbody>
                {incidencias.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-zinc-400">
                      No hay incidencias registradas
                    </td>
                  </tr>
                ) : (
                  incidencias.map((inc) => {
                    const esIngreso = esIncidenciaIngreso(inc.Tipo_Incidencia);
                    return (
                      <tr key={inc.IncidenciaID} className="border-b hover:bg-zinc-50">
                        <td className="p-3 font-medium">{inc.Nombre_Completo}</td>
                        <td className="p-3">{inc.Nombre_Sucursal || '-'}</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 w-fit ${
                            esIngreso ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            <span className="font-bold">{esIngreso ? '+' : '-'}</span>
                            {inc.Tipo_Incidencia}
                          </span>
                        </td>
                        <td className="p-3 text-zinc-600">
                          {inc.Fecha_Incidencia ? new Date(inc.Fecha_Incidencia).toLocaleDateString('es-MX') : '-'}
                        </td>
                        <td className={`p-3 text-right font-medium ${esIngreso ? 'text-green-600' : 'text-red-600'}`}>
                          {esIngreso ? '+' : '-'}${(inc.Monto || 0).toLocaleString()}
                        </td>
                        <td className="p-3 text-right">{inc.Unidades || 0}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
