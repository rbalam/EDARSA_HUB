import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Building2, FileText, Plus, Edit, Trash2 } from 'lucide-react';

/**
 * FinanzasPresupuestos
 * 
 * Componente presentacional para la gestion de presupuestos.
 * 
 * ACTUALIZADO: Filtro de sucursal reemplazado por Unidad de Negocio.
 * Solo se muestran las unidades a las que el usuario tiene acceso.
 * 
 * @param {Object} props
 * @param {Array} props.presupuestos - Lista de presupuestos
 * @param {Array} props.unidadesNegocio - Unidades de negocio disponibles (filtradas por permisos)
 * @param {string} props.selectedUnidad - Unidad de negocio seleccionada
 * @param {boolean} props.loadingUnidades - Estado de carga de unidades
 * @param {Array} props.meses - Array de nombres de meses
 * @param {number} props.filtroAnio - Ano seleccionado
 * @param {number} props.filtroMes - Mes seleccionado
 * @param {Function} props.onUnidadChange - Callback cambio unidad
 * @param {Function} props.onAnioChange - Callback cambio ano
 * @param {Function} props.onMesChange - Callback cambio mes
 * @param {Function} props.onVerScript - Callback ver script SQL
 * @param {Function} props.onNuevoPresupuesto - Callback nuevo presupuesto
 * @param {Function} props.onEditarPresupuesto - Callback editar presupuesto
 * @param {Function} props.onEliminarPresupuesto - Callback eliminar presupuesto
 * @param {Function} props.formatCurrency - Funcion para formatear moneda
 */
export default function FinanzasPresupuestos({
  presupuestos,
  unidadesNegocio,
  selectedUnidad,
  loadingUnidades,
  meses,
  filtroAnio,
  filtroMes,
  onUnidadChange,
  onAnioChange,
  onMesChange,
  onVerScript,
  onNuevoPresupuesto,
  onEditarPresupuesto,
  onEliminarPresupuesto,
  formatCurrency
}) {
  return (
    <div className="space-y-4" data-testid="presupuestos-container">
      {/* Filtros y acciones */}
      <div className="flex flex-wrap gap-3 justify-between" data-testid="presupuestos-filtros">
        <div className="flex flex-wrap gap-2 items-center">
          {/* Selector de Unidad de Negocio */}
          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-zinc-400" />
            {unidadesNegocio.length === 1 ? (
              <div className="px-3 py-2 border rounded-lg text-sm bg-zinc-50 flex items-center gap-2">
                <span>{unidadesNegocio[0].nombre}</span>
              </div>
            ) : (
              <select
                value={selectedUnidad}
                onChange={(e) => onUnidadChange(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm"
                disabled={loadingUnidades}
                data-testid="presupuestos-unidad-select"
              >
                <option value="">{loadingUnidades ? "Cargando..." : "Todas las unidades"}</option>
                {unidadesNegocio.map(u => (
                  <option key={u.id} value={u.id}>{u.nombre}</option>
                ))}
              </select>
            )}
          </div>
          <select
            value={filtroAnio}
            onChange={(e) => onAnioChange(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
            data-testid="presupuestos-anio-select"
          >
            {[2024, 2025, 2026, 2027].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <select
            value={filtroMes}
            onChange={(e) => onMesChange(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
            data-testid="presupuestos-mes-select"
          >
            <option value="">Todos los meses</option>
            {meses.map((m, i) => (
              <option key={`mes-select-${i + 1}`} value={i + 1}>{m}</option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onVerScript} data-testid="presupuestos-ver-script-btn">
            <FileText className="h-4 w-4 mr-1" />
            Ver Script SQL
          </Button>
          <Button size="sm" className="bg-zinc-900 text-white" onClick={onNuevoPresupuesto} data-testid="presupuestos-nuevo-btn">
            <Plus className="h-4 w-4 mr-1" />
            Nuevo Presupuesto
          </Button>
        </div>
      </div>
      
      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="presupuestos-tabla">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Unidad de Negocio</th>
                  <th className="text-left p-3 font-medium">Categoria</th>
                  <th className="text-center p-3 font-medium">Tipo</th>
                  <th className="text-center p-3 font-medium">Periodo</th>
                  <th className="text-right p-3 font-medium">Presupuestado</th>
                  <th className="text-right p-3 font-medium">Ejecutado</th>
                  <th className="text-center p-3 font-medium">%</th>
                  <th className="text-center p-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {presupuestos.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-zinc-400">
                      No hay presupuestos registrados para este periodo
                    </td>
                  </tr>
                ) : (
                  presupuestos.map((pres, i) => {
                    const porcentaje = pres.Monto_Presupuestado > 0 
                      ? Math.round((pres.Monto_Ejecutado / pres.Monto_Presupuestado) * 100) 
                      : 0;
                    
                    return (
                      <tr key={pres.PresupuestoID || i} className="border-b hover:bg-zinc-50">
                        <td className="p-3 font-medium">{pres.Nombre_Sucursal || pres.Nombre_Unidad || '-'}</td>
                        <td className="p-3">
                          <div>
                            <span>{pres.Categoria}</span>
                            {pres.SubCategoria && (
                              <span className="text-xs text-zinc-400 block">{pres.SubCategoria}</span>
                            )}
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            pres.Tipo === 'Ingreso' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {pres.Tipo}
                          </span>
                        </td>
                        <td className="p-3 text-center text-zinc-500">
                          {meses[pres.Mes - 1]?.substring(0, 3)} {pres.Anio}
                        </td>
                        <td className="p-3 text-right font-mono">{formatCurrency(pres.Monto_Presupuestado)}</td>
                        <td className="p-3 text-right font-mono font-medium">{formatCurrency(pres.Monto_Ejecutado)}</td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            porcentaje >= 100 ? 'bg-green-100 text-green-700' :
                            porcentaje >= 80 ? 'bg-amber-100 text-amber-700' :
                            'bg-zinc-100 text-zinc-600'
                          }`}>
                            {porcentaje}%
                          </span>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center justify-center gap-1">
                            <Button variant="ghost" size="sm" onClick={() => onEditarPresupuesto(pres)} title="Editar">
                              <Edit className="h-4 w-4 text-amber-600" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => onEliminarPresupuesto(pres)} title="Eliminar">
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          </div>
                        </td>
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
