/**
 * EDARSA HUB - RH Colaboradores
 * =============================
 * Tabla de colaboradores con filtros, búsqueda y acciones.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Search,
  RefreshCw,
  UserPlus,
  Eye,
  Edit,
  AlertTriangle,
  Trash2,
} from 'lucide-react';
import { EstatusLaboralBadge } from './shared/RhSharedComponents';

/**
 * Tabla de colaboradores con filtros
 */
export default function RhColaboradores({
  // Data
  colaboradores = [],
  sucursales = [],
  // Filtros
  filtroBuscar,
  setFiltroBuscar,
  filtroSucursal,
  setFiltroSucursal,
  // Paginación
  page,
  setPage,
  totalPages,
  // Loading
  loading,
  // Handlers
  onRefresh,
  onNuevoColaborador,
  onVerDetalle,
  onEditarColaborador,
  onNuevaIncidencia,
  onDarBaja,
}) {
  return (
    <div className="space-y-4" data-testid="rh-colaboradores">
      {/* Filtros */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input
            placeholder="Buscar por nombre, RFC o CURP..."
            value={filtroBuscar}
            onChange={(e) => setFiltroBuscar(e.target.value)}
            className="pl-10"
            data-testid="colaboradores-search"
          />
        </div>
        <select
          value={filtroSucursal}
          onChange={(e) => setFiltroSucursal(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm"
          data-testid="colaboradores-filter-sucursal"
        >
          <option value="">Todas las sucursales</option>
          {sucursales.map(s => (
            <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
          ))}
        </select>
        <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
        <Button size="sm" className="bg-zinc-900 text-white" onClick={onNuevoColaborador}>
          <UserPlus className="h-4 w-4 mr-1" />
          Nuevo Colaborador
        </Button>
      </div>

      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Nombre</th>
                  <th className="text-left p-3 font-medium">RFC</th>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Puesto</th>
                  <th className="text-left p-3 font-medium">Estatus</th>
                  <th className="text-center p-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {colaboradores.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-zinc-400">
                      No hay colaboradores registrados
                    </td>
                  </tr>
                ) : (
                  colaboradores.map((col) => (
                    <tr key={col.ColaboradorID} className="border-b hover:bg-zinc-50">
                      <td className="p-3 font-medium">{col.Nombre_Completo}</td>
                      <td className="p-3 text-zinc-600 font-mono text-xs">{col.RFC || '-'}</td>
                      <td className="p-3">{col.Nombre_Sucursal || '-'}</td>
                      <td className="p-3">{col.Puesto || '-'}</td>
                      <td className="p-3">
                        <EstatusLaboralBadge estatus={col.Estatus_Laboral} />
                      </td>
                      <td className="p-3">
                        <div className="flex items-center justify-center gap-1">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => onVerDetalle(col)} 
                            title="Ver detalle"
                            data-testid={`btn-ver-${col.ColaboradorID}`}
                          >
                            <Eye className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => onEditarColaborador(col)} 
                            title="Editar"
                            data-testid={`btn-edit-${col.ColaboradorID}`}
                          >
                            <Edit className="h-4 w-4 text-amber-600" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => onNuevaIncidencia(col.ColaboradorID)} 
                            title="Nueva incidencia"
                            data-testid={`btn-incidencia-${col.ColaboradorID}`}
                          >
                            <AlertTriangle className="h-4 w-4 text-purple-600" />
                          </Button>
                          {col.Estatus_Laboral === 'Activo' && (
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => onDarBaja(col)} 
                              title="Dar de baja"
                              data-testid={`btn-baja-${col.ColaboradorID}`}
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
          >
            Anterior
          </Button>
          <span className="px-3 py-2 text-sm">
            Página {page} de {totalPages}
          </span>
          <Button 
            variant="outline" 
            size="sm" 
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  );
}
