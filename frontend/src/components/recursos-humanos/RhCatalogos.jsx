/**
 * EDARSA HUB - RH Catálogos
 * =========================
 * Gestión de catálogos de RRHH: Puestos, Tipos de Incidencias y Solicitudes.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  RefreshCw,
  Plus,
  Edit,
  Trash2,
  Lock,
  Database,
  Briefcase,
  Tag,
  Bell,
  FileText,
} from 'lucide-react';
import { GestionSolicitudesCatalogo } from '../GestionSolicitudesCatalogo';

/**
 * Componente de Gestión de Catálogos RRHH
 */
export default function RhCatalogos({
  // Loading
  loadingCatalogos,
  // Data
  catalogoPuestos = [],
  catalogoIncidencias = [],
  // Sub-tab
  catalogoSubTab,
  setCatalogoSubTab,
  // Permisos
  isAdmin,
  // Handlers
  loadCatalogosCompleto,
  loadScriptCatalogos,
  handleNuevoPuesto,
  handleEditarPuesto,
  handleEliminarPuesto,
  handleNuevoTipoIncidencia,
  handleEditarTipoIncidencia,
  handleEliminarTipoIncidencia,
}) {
  return (
    <div className="space-y-6" data-testid="rh-catalogos">
      {/* Header con aviso de permisos */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-800">Catálogos de RRHH</h2>
          <p className="text-sm text-zinc-500">Administración de Puestos y Tipos de Incidencias</p>
        </div>
        <div className="flex items-center gap-2">
          {!isAdmin && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
              <Lock className="h-4 w-4" />
              <span>Solo lectura (requiere rol Administrador para editar)</span>
            </div>
          )}
          <Button variant="outline" size="sm" onClick={loadCatalogosCompleto}>
            <RefreshCw className={`h-4 w-4 mr-1 ${loadingCatalogos ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Button variant="outline" size="sm" onClick={loadScriptCatalogos}>
            <Database className="h-4 w-4 mr-1" />
            Script SQL
          </Button>
        </div>
      </div>

      {/* Sub-pestañas */}
      <div className="flex gap-2 border-b border-zinc-200">
        <button
          onClick={() => setCatalogoSubTab('puestos')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-all ${
            catalogoSubTab === 'puestos'
              ? 'border-zinc-900 text-zinc-900'
              : 'border-transparent text-zinc-500 hover:text-zinc-700'
          }`}
          data-testid="tab-puestos"
        >
          <Briefcase className="h-4 w-4 inline mr-2" />
          Puestos
        </button>
        <button
          onClick={() => setCatalogoSubTab('incidencias')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-all ${
            catalogoSubTab === 'incidencias'
              ? 'border-zinc-900 text-zinc-900'
              : 'border-transparent text-zinc-500 hover:text-zinc-700'
          }`}
          data-testid="tab-incidencias"
        >
          <Tag className="h-4 w-4 inline mr-2" />
          Tipos de Incidencias
        </button>
        <button
          onClick={() => setCatalogoSubTab('solicitudes')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-all ${
            catalogoSubTab === 'solicitudes'
              ? 'border-zinc-900 text-zinc-900'
              : 'border-transparent text-zinc-500 hover:text-zinc-700'
          }`}
          data-testid="tab-solicitudes"
        >
          <Bell className="h-4 w-4 inline mr-2" />
          Solicitudes de Alta
        </button>
      </div>

      {/* Vista Puestos */}
      {catalogoSubTab === 'puestos' && (
        <PuestosTable
          catalogoPuestos={catalogoPuestos}
          loadingCatalogos={loadingCatalogos}
          isAdmin={isAdmin}
          handleNuevoPuesto={handleNuevoPuesto}
          handleEditarPuesto={handleEditarPuesto}
          handleEliminarPuesto={handleEliminarPuesto}
        />
      )}

      {/* Vista Incidencias */}
      {catalogoSubTab === 'incidencias' && (
        <IncidenciasTable
          catalogoIncidencias={catalogoIncidencias}
          loadingCatalogos={loadingCatalogos}
          isAdmin={isAdmin}
          handleNuevoTipoIncidencia={handleNuevoTipoIncidencia}
          handleEditarTipoIncidencia={handleEditarTipoIncidencia}
          handleEliminarTipoIncidencia={handleEliminarTipoIncidencia}
        />
      )}

      {/* Nota informativa */}
      {(catalogoSubTab === 'puestos' || catalogoSubTab === 'incidencias') && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Integración con Sistemas Externos
          </h4>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li><strong>NomiPAQ:</strong> Use el campo NomiPAQ_ID para mapear con conceptos de nómina.</li>
            <li><strong>MPRO:</strong> Use el campo MPRO_ID para sincronizar con el sistema MPRO.</li>
            <li><strong>Excel:</strong> Los códigos se usan como referencia en las importaciones de nómina.</li>
          </ul>
        </div>
      )}

      {/* Vista de Solicitudes de Alta */}
      {catalogoSubTab === 'solicitudes' && (
        <GestionSolicitudesCatalogo />
      )}
    </div>
  );
}

/**
 * Tabla de Puestos
 */
function PuestosTable({
  catalogoPuestos,
  loadingCatalogos,
  isAdmin,
  handleNuevoPuesto,
  handleEditarPuesto,
  handleEliminarPuesto,
}) {
  return (
    <Card data-testid="puestos-table">
      <CardHeader className="flex flex-row items-center justify-between py-4">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Briefcase className="h-5 w-5 text-zinc-600" />
          Catálogo de Puestos ({catalogoPuestos.length})
        </CardTitle>
        {isAdmin && (
          <Button size="sm" onClick={handleNuevoPuesto} data-testid="btn-nuevo-puesto">
            <Plus className="h-4 w-4 mr-1" />
            Nuevo Puesto
          </Button>
        )}
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 border-y">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">ID</th>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">Descripción</th>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">Departamento</th>
                <th className="px-4 py-3 text-right font-medium text-zinc-600">Sueldo Base</th>
                <th className="px-4 py-3 text-center font-medium text-zinc-600">NomiPAQ</th>
                <th className="px-4 py-3 text-center font-medium text-zinc-600">MPRO</th>
                {isAdmin && <th className="px-4 py-3 text-center font-medium text-zinc-600">Acciones</th>}
              </tr>
            </thead>
            <tbody className="divide-y">
              {loadingCatalogos ? (
                <tr>
                  <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />
                    Cargando...
                  </td>
                </tr>
              ) : catalogoPuestos.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                    No hay puestos registrados. Ejecute el script SQL si la tabla no existe.
                  </td>
                </tr>
              ) : (
                catalogoPuestos.map((p) => (
                  <tr key={p.PuestoID} className="hover:bg-zinc-50">
                    <td className="px-4 py-3 text-zinc-600">{p.PuestoID}</td>
                    <td className="px-4 py-3 font-medium text-zinc-800">{p.Descripcion}</td>
                    <td className="px-4 py-3 text-zinc-600">{p.Departamento || '-'}</td>
                    <td className="px-4 py-3 text-right text-zinc-800">
                      ${(p.Sueldo_Base_Seman_SBC || 0).toLocaleString('es-MX', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {p.NomiPAQ_ID ? (
                        <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{p.NomiPAQ_ID}</span>
                      ) : (
                        <span className="text-zinc-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {p.MPRO_ID ? (
                        <span className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded">{p.MPRO_ID}</span>
                      ) : (
                        <span className="text-zinc-400">-</span>
                      )}
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-center">
                        <div className="flex justify-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEditarPuesto(p)} data-testid={`btn-edit-puesto-${p.PuestoID}`}>
                            <Edit className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleEliminarPuesto(p.PuestoID)} data-testid={`btn-delete-puesto-${p.PuestoID}`}>
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Tabla de Tipos de Incidencias
 */
function IncidenciasTable({
  catalogoIncidencias,
  loadingCatalogos,
  isAdmin,
  handleNuevoTipoIncidencia,
  handleEditarTipoIncidencia,
  handleEliminarTipoIncidencia,
}) {
  return (
    <Card data-testid="incidencias-table">
      <CardHeader className="flex flex-row items-center justify-between py-4">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Tag className="h-5 w-5 text-zinc-600" />
          Tipos de Incidencias ({catalogoIncidencias.length})
        </CardTitle>
        {isAdmin && (
          <Button size="sm" onClick={handleNuevoTipoIncidencia} data-testid="btn-nuevo-tipo-incidencia">
            <Plus className="h-4 w-4 mr-1" />
            Nuevo Tipo
          </Button>
        )}
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 border-y">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">Código</th>
                <th className="px-4 py-3 text-left font-medium text-zinc-600">Descripción</th>
                <th className="px-4 py-3 text-center font-medium text-zinc-600">Categoría</th>
                <th className="px-4 py-3 text-center font-medium text-zinc-600">Cálculo</th>
                <th className="px-4 py-3 text-center font-medium text-zinc-600">NomiPAQ</th>
                <th className="px-4 py-3 text-center font-medium text-zinc-600">MPRO</th>
                {isAdmin && <th className="px-4 py-3 text-center font-medium text-zinc-600">Acciones</th>}
              </tr>
            </thead>
            <tbody className="divide-y">
              {loadingCatalogos ? (
                <tr>
                  <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2" />
                    Cargando...
                  </td>
                </tr>
              ) : catalogoIncidencias.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 7 : 6} className="px-4 py-8 text-center text-zinc-500">
                    No hay tipos de incidencia registrados. Ejecute el script SQL para crear la tabla.
                  </td>
                </tr>
              ) : (
                catalogoIncidencias.map((t) => (
                  <tr key={t.TipoIncidenciaID} className="hover:bg-zinc-50">
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-zinc-100 text-zinc-700 font-mono text-xs rounded">{t.Codigo}</span>
                    </td>
                    <td className="px-4 py-3 font-medium text-zinc-800">{t.Descripcion}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        t.Categoria === 'Ingreso' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {t.Categoria === 'Ingreso' ? '+ Ingreso' : '- Descuento'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-zinc-600 text-xs">
                      {t.Calculo_Monto || 'Manual'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {t.NomiPAQ_ID ? (
                        <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{t.NomiPAQ_ID}</span>
                      ) : (
                        <span className="text-zinc-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {t.MPRO_ID ? (
                        <span className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded">{t.MPRO_ID}</span>
                      ) : (
                        <span className="text-zinc-400">-</span>
                      )}
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-center">
                        <div className="flex justify-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEditarTipoIncidencia(t)} data-testid={`btn-edit-tipo-${t.TipoIncidenciaID}`}>
                            <Edit className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleEliminarTipoIncidencia(t.TipoIncidenciaID)} data-testid={`btn-delete-tipo-${t.TipoIncidenciaID}`}>
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
