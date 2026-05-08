/**
 * EDARSA HUB - RH Nóminas (Módulo Kanban)
 * =======================================
 * Gestión de ciclos de nómina con tablero Kanban, captura masiva y configuración.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  RefreshCw,
  Plus,
  Eye,
  Clock,
  Calendar,
  Timer,
  ArrowRight,
  Search,
  Download,
  Save,
  Users,
  ClipboardList,
  History,
  Lock,
} from 'lucide-react';

/**
 * Componente de Gestión de Nóminas con Kanban
 */
export default function RhNominas({
  // Loading states
  loadingNominas,
  loadingCaptura,
  savingCaptura,
  savingForm,
  // Data
  ciclosNomina = [],
  sucursales = [],
  departamentos = [],
  colaboradoresCaptura = [],
  capturaData = {},
  // Sub-tabs
  nominaSubTab,
  setNominaSubTab,
  // Filtros captura
  capturaSemana,
  setCapturaSemana,
  capturaFiltroSucursal,
  setCapturaFiltroSucursal,
  capturaFiltroDepartamento,
  setCapturaFiltroDepartamento,
  // Config form
  formConfigNomina,
  setFormConfigNomina,
  diasSemana = [],
  // Constantes
  ETAPAS_NOMINA = [],
  SIMBOLOS_INCIDENCIA = [],
  DIAS_SEMANA_LABELS = [],
  DIAS_SEMANA_CAPTURA = [],
  // Permisos
  isAdmin,
  isSupervisor,
  // Helpers
  getCiclosPorEtapa,
  calcularTiempoRestante,
  calcularTotalesColaborador,
  getSimboloColor,
  // Handlers
  loadCiclosNomina,
  loadColaboradoresCaptura,
  handleCapturaDiaChange,
  handleGuardarCapturaMasiva,
  handleExportarCapturaExcel,
  handleGuardarConfigNomina,
  handleVerMovimientosCiclo,
  // Modal handlers
  setModalNuevoCiclo,
  setCicloSeleccionado,
  setPasswordAprobacion,
  setComentarioAprobacion,
  setModalAprobarCiclo,
  setModalHistorialCiclo,
}) {
  // Memoized: Colaboradores filtrados por departamento
  const colaboradoresFiltrados = useMemo(() => 
    colaboradoresCaptura.filter(c => !capturaFiltroDepartamento || c.Departamento === capturaFiltroDepartamento),
    [colaboradoresCaptura, capturaFiltroDepartamento]
  );

  // Memoized: Totales pre-calculados para cada colaborador (evita recálculos en JSX)
  const totalesPorColaborador = useMemo(() => {
    const map = {};
    colaboradoresFiltrados.forEach(col => {
      map[col.ColaboradorID] = calcularTotalesColaborador(col.ColaboradorID);
    });
    return map;
  }, [colaboradoresFiltrados, calcularTotalesColaborador]);

  // Memoized: Totales globales para footer (evita múltiples reduce en cada render)
  const totalesGlobales = useMemo(() => {
    let turnos = 0, retardos = 0, faltas = 0, faltasPorRetardos = 0;
    let proporcionalDescanso = 0, proporcionalAguinaldoSemanal = 0;
    
    Object.values(totalesPorColaborador).forEach(t => {
      turnos += parseFloat(t.turnos) || 0;
      retardos += t.retardos || 0;
      faltas += t.faltas || 0;
      faltasPorRetardos += t.faltasPorRetardos || 0;
      proporcionalDescanso += parseFloat(t.proporcionalDescanso) || 0;
      proporcionalAguinaldoSemanal += parseFloat(t.proporcionalAguinaldoSemanal) || 0;
    });
    
    return { turnos, retardos, faltas, faltasPorRetardos, proporcionalDescanso, proporcionalAguinaldoSemanal };
  }, [totalesPorColaborador]);

  // Loading state
  if (loadingNominas) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="rh-nominas-loading">
        <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="rh-nominas">
      {/* Sub-Tabs */}
      <div className="flex items-center justify-between border-b pb-2">
        <div className="flex gap-2 flex-wrap">
          {['kanban', 'captura', 'lista', 'config'].map(tab => (
            <button
              key={tab}
              onClick={() => setNominaSubTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                nominaSubTab === tab ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
              data-testid={`nomina-tab-${tab}`}
            >
              {tab === 'kanban' ? 'Tablero Kanban' : 
               tab === 'captura' ? 'Captura Incidencias' :
               tab === 'lista' ? 'Lista' : 'Configuración'}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadCiclosNomina}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          {(isAdmin || isSupervisor) && (
            <Button size="sm" className="bg-zinc-900 text-white" onClick={() => setModalNuevoCiclo(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Nuevo Ciclo
            </Button>
          )}
        </div>
      </div>
      
      {/* Vista Kanban */}
      {nominaSubTab === 'kanban' && (
        <KanbanView
          ETAPAS_NOMINA={ETAPAS_NOMINA}
          getCiclosPorEtapa={getCiclosPorEtapa}
          calcularTiempoRestante={calcularTiempoRestante}
          handleVerMovimientosCiclo={handleVerMovimientosCiclo}
          setCicloSeleccionado={setCicloSeleccionado}
          setPasswordAprobacion={setPasswordAprobacion}
          setComentarioAprobacion={setComentarioAprobacion}
          setModalAprobarCiclo={setModalAprobarCiclo}
        />
      )}
      
      {/* Vista Captura Masiva */}
      {nominaSubTab === 'captura' && (
        <CapturaView
          sucursales={sucursales}
          departamentos={departamentos}
          colaboradoresCaptura={colaboradoresCaptura}
          capturaData={capturaData}
          capturaSemana={capturaSemana}
          setCapturaSemana={setCapturaSemana}
          capturaFiltroSucursal={capturaFiltroSucursal}
          setCapturaFiltroSucursal={setCapturaFiltroSucursal}
          capturaFiltroDepartamento={capturaFiltroDepartamento}
          setCapturaFiltroDepartamento={setCapturaFiltroDepartamento}
          loadingCaptura={loadingCaptura}
          savingCaptura={savingCaptura}
          loadColaboradoresCaptura={loadColaboradoresCaptura}
          handleCapturaDiaChange={handleCapturaDiaChange}
          handleGuardarCapturaMasiva={handleGuardarCapturaMasiva}
          handleExportarCapturaExcel={handleExportarCapturaExcel}
          calcularTotalesColaborador={calcularTotalesColaborador}
          getSimboloColor={getSimboloColor}
          SIMBOLOS_INCIDENCIA={SIMBOLOS_INCIDENCIA}
          DIAS_SEMANA_LABELS={DIAS_SEMANA_LABELS}
          DIAS_SEMANA_CAPTURA={DIAS_SEMANA_CAPTURA}
        />
      )}
      
      {/* Vista Lista */}
      {nominaSubTab === 'lista' && (
        <ListaView
          ciclosNomina={ciclosNomina}
          ETAPAS_NOMINA={ETAPAS_NOMINA}
          calcularTiempoRestante={calcularTiempoRestante}
          handleVerMovimientosCiclo={handleVerMovimientosCiclo}
          setCicloSeleccionado={setCicloSeleccionado}
          setModalHistorialCiclo={setModalHistorialCiclo}
        />
      )}
      
      {/* Vista Configuración */}
      {nominaSubTab === 'config' && isAdmin && (
        <ConfigView
          formConfigNomina={formConfigNomina}
          setFormConfigNomina={setFormConfigNomina}
          diasSemana={diasSemana}
          handleGuardarConfigNomina={handleGuardarConfigNomina}
          savingForm={savingForm}
          ETAPAS_NOMINA={ETAPAS_NOMINA}
        />
      )}
      
      {nominaSubTab === 'config' && !isAdmin && (
        <Card className="border-2 border-dashed border-zinc-300">
          <CardContent className="py-12 text-center">
            <Lock className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-zinc-600 mb-2">Acceso Restringido</h3>
            <p className="text-zinc-400 text-sm">Solo Administradores pueden modificar la configuración.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/**
 * Kanban View - Tablero de etapas
 */
function KanbanView({
  ETAPAS_NOMINA,
  getCiclosPorEtapa,
  calcularTiempoRestante,
  handleVerMovimientosCiclo,
  setCicloSeleccionado,
  setPasswordAprobacion,
  setComentarioAprobacion,
  setModalAprobarCiclo,
}) {
  return (
    <div className="overflow-x-auto pb-4" data-testid="kanban-view">
      <div className="flex gap-4 min-w-max">
        {ETAPAS_NOMINA.map(etapa => {
          const ciclosEtapa = getCiclosPorEtapa(etapa.id);
          const IconoEtapa = etapa.icon;
          return (
            <div key={etapa.id} className="w-64 bg-zinc-50 rounded-xl p-3 flex-shrink-0">
              <div className="flex items-center gap-2 mb-3">
                <div className={`p-2 rounded-lg ${etapa.color}`}>
                  <IconoEtapa className="h-4 w-4 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-zinc-900 text-sm">{etapa.nombre}</h3>
                  <p className="text-xs text-zinc-500">{etapa.responsable}</p>
                </div>
                <span className="bg-zinc-200 text-zinc-700 text-xs font-medium px-2 py-1 rounded-full">
                  {ciclosEtapa.length}
                </span>
              </div>
              <div className="space-y-2">
                {ciclosEtapa.length === 0 ? (
                  <div className="text-center py-6 text-zinc-400 text-xs">Sin nóminas</div>
                ) : (
                  ciclosEtapa.map(ciclo => {
                    const tiempoRestante = calcularTiempoRestante(ciclo);
                    return (
                      <Card key={ciclo.id} className={`cursor-pointer hover:shadow-md transition-shadow ${
                        tiempoRestante?.vencido ? 'border-red-300 bg-red-50' : ''
                      }`}>
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <p className="font-medium text-sm text-zinc-900">{ciclo.sucursal_nombre || 'Sucursal'}</p>
                              <p className="text-xs text-zinc-500 capitalize">{ciclo.tipo_nomina}</p>
                            </div>
                            {tiempoRestante && (
                              <div className={`flex items-center gap-1 text-xs ${tiempoRestante.color}`}>
                                <Timer className="h-3 w-3" />{tiempoRestante.texto}
                              </div>
                            )}
                          </div>
                          <div className="text-xs text-zinc-500 mb-2">
                            <Calendar className="h-3 w-3 inline mr-1" />
                            Corte: {new Date(ciclo.fecha_corte).toLocaleDateString()}
                          </div>
                          <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
                            <span>{ciclo.total_colaboradores || 0} colab.</span>
                            <span>{ciclo.total_movimientos || 0} mov.</span>
                          </div>
                          {etapa.id !== 'pagada' && (
                            <div className="flex gap-1 pt-2 border-t">
                              <Button size="sm" variant="outline" className="flex-1 text-xs h-7"
                                onClick={() => handleVerMovimientosCiclo(ciclo)}>
                                <Eye className="h-3 w-3 mr-1" />Ver
                              </Button>
                              <Button size="sm" className="flex-1 text-xs h-7 bg-green-600 hover:bg-green-700"
                                onClick={() => { 
                                  setCicloSeleccionado(ciclo); 
                                  setPasswordAprobacion(''); 
                                  setComentarioAprobacion(''); 
                                  setModalAprobarCiclo(true); 
                                }}>
                                <ArrowRight className="h-3 w-3 mr-1" />Avanzar
                              </Button>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Captura View - Captura masiva de incidencias estilo Excel
 */
function CapturaView({
  sucursales,
  departamentos,
  colaboradoresCaptura,
  capturaData,
  capturaSemana,
  setCapturaSemana,
  capturaFiltroSucursal,
  setCapturaFiltroSucursal,
  capturaFiltroDepartamento,
  setCapturaFiltroDepartamento,
  loadingCaptura,
  savingCaptura,
  loadColaboradoresCaptura,
  handleCapturaDiaChange,
  handleGuardarCapturaMasiva,
  handleExportarCapturaExcel,
  calcularTotalesColaborador,
  getSimboloColor,
  SIMBOLOS_INCIDENCIA,
  DIAS_SEMANA_LABELS,
  DIAS_SEMANA_CAPTURA,
}) {
  return (
    <div className="space-y-4" data-testid="captura-view">
      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <Label className="text-xs text-zinc-500">Semana (Inicio Lunes)</Label>
              <Input
                type="date"
                value={capturaSemana}
                onChange={(e) => setCapturaSemana(e.target.value)}
                className="mt-1"
              />
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Sucursal *</Label>
              <select
                value={capturaFiltroSucursal}
                onChange={(e) => setCapturaFiltroSucursal(e.target.value)}
                className="w-full border border-zinc-300 rounded-lg px-3 py-2 mt-1 text-sm bg-white text-zinc-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Seleccionar sucursal...</option>
                {sucursales.map(s => (
                  <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Departamento</Label>
              <select
                value={capturaFiltroDepartamento}
                onChange={(e) => setCapturaFiltroDepartamento(e.target.value)}
                className="w-full border border-zinc-300 rounded-lg px-3 py-2 mt-1 text-sm bg-white text-zinc-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                {departamentos.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <Button 
                onClick={loadColaboradoresCaptura}
                disabled={!capturaFiltroSucursal || loadingCaptura}
                className="w-full"
              >
                {loadingCaptura ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
                Cargar
              </Button>
            </div>
            <div className="flex items-end">
              <Button 
                onClick={handleExportarCapturaExcel}
                disabled={colaboradoresCaptura.length === 0}
                variant="outline"
                className="w-full"
              >
                <Download className="h-4 w-4 mr-2" />
                Exportar Excel
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Leyenda de Símbolos */}
      {colaboradoresCaptura.length > 0 && (
        <Card>
          <CardContent className="p-3">
            <div className="flex flex-wrap gap-2 text-xs">
              {SIMBOLOS_INCIDENCIA.map(s => (
                <span key={s.codigo} className={`px-2 py-1 rounded ${s.color}`} title={s.nombre}>
                  <strong>{s.codigo}</strong> {s.nombre}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Tabla de Captura */}
      {colaboradoresCaptura.length > 0 && (
        <Card>
          <CardHeader className="py-3 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <ClipboardList className="h-5 w-5" />
                Captura Semanal - {colaboradoresCaptura.length} colaboradores
              </CardTitle>
              <div className="flex gap-2">
                <Button 
                  onClick={handleGuardarCapturaMasiva}
                  disabled={savingCaptura || !capturaSemana}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {savingCaptura ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                  Guardar Incidencias
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="bg-zinc-800 text-white sticky top-0 z-10">
                  <tr>
                    <th className="text-left p-2 font-medium w-8 sticky left-0 bg-zinc-800">#</th>
                    <th className="text-left p-2 font-medium min-w-[200px] sticky left-8 bg-zinc-800">Colaborador</th>
                    <th className="text-left p-2 font-medium min-w-[120px]">Puesto</th>
                    {DIAS_SEMANA_LABELS.map((dia, i) => (
                      <th key={`dia-${i}`} className="text-center p-2 font-medium w-14">{dia}</th>
                    ))}
                    <th className="text-center p-2 font-medium w-14 bg-green-700">Turnos</th>
                    <th className="text-center p-2 font-medium w-14 bg-yellow-600">Ret.</th>
                    <th className="text-center p-2 font-medium w-14 bg-red-700">Faltas</th>
                    <th className="text-center p-2 font-medium w-14 bg-red-600">F.xRet</th>
                    <th className="text-center p-2 font-medium w-16 bg-blue-700">Desc.</th>
                    <th className="text-center p-2 font-medium w-16 bg-purple-700">Agui.</th>
                  </tr>
                </thead>
                <tbody>
                  {colaboradoresFiltrados.map((col, idx) => {
                    const datos = capturaData[col.ColaboradorID] || {};
                    const totales = totalesPorColaborador[col.ColaboradorID] || {};
                    
                    return (
                      <tr key={col.ColaboradorID} className="border-b hover:bg-zinc-50">
                        <td className="p-2 text-zinc-400 sticky left-0 bg-white">{idx + 1}</td>
                        <td className="p-2 sticky left-8 bg-white">
                          <div>
                            <p className="font-medium text-xs truncate max-w-[180px]" title={col.Nombre_Completo}>
                              {col.Nombre_Completo}
                            </p>
                          </div>
                        </td>
                        <td className="p-2 text-zinc-600 truncate max-w-[100px]" title={col.Puesto}>
                          {col.Puesto || '-'}
                        </td>
                        {DIAS_SEMANA_CAPTURA.map((dia, i) => (
                          <td key={`${col.ColaboradorID}-${dia}`} className="p-1 text-center">
                            <select
                              value={datos[dia] || '1'}
                              onChange={(e) => handleCapturaDiaChange(col.ColaboradorID, dia, e.target.value)}
                              className={`w-12 text-center text-xs p-1 border rounded ${getSimboloColor(datos[dia] || '1')}`}
                            >
                              {SIMBOLOS_INCIDENCIA.map(s => (
                                <option key={s.codigo} value={s.codigo}>{s.codigo}</option>
                              ))}
                            </select>
                          </td>
                        ))}
                        <td className="p-2 text-center font-bold bg-green-50">{totales.turnos}</td>
                        <td className="p-2 text-center font-bold bg-yellow-50">{totales.retardos}</td>
                        <td className="p-2 text-center font-bold bg-red-50">{totales.faltas}</td>
                        <td className="p-2 text-center font-bold bg-red-100">{totales.faltasPorRetardos}</td>
                        <td className="p-2 text-center font-medium bg-blue-50">{totales.proporcionalDescanso}</td>
                        <td className="p-2 text-center font-medium bg-purple-50">{totales.proporcionalAguinaldoSemanal}</td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot className="bg-zinc-100 font-bold sticky bottom-0">
                  <tr>
                    <td colSpan={3} className="p-2 text-right">TOTALES:</td>
                    {DIAS_SEMANA_LABELS.map((_, i) => <td key={`footer-${i}`} className="p-2"></td>)}
                    <td className="p-2 text-center bg-green-100">{totalesGlobales.turnos.toFixed(1)}</td>
                    <td className="p-2 text-center bg-yellow-100">{totalesGlobales.retardos}</td>
                    <td className="p-2 text-center bg-red-100">{totalesGlobales.faltas}</td>
                    <td className="p-2 text-center bg-red-200">{totalesGlobales.faltasPorRetardos}</td>
                    <td className="p-2 text-center bg-blue-100">{totalesGlobales.proporcionalDescanso.toFixed(2)}</td>
                    <td className="p-2 text-center bg-purple-100">{totalesGlobales.proporcionalAguinaldoSemanal.toFixed(3)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Estado vacío */}
      {colaboradoresCaptura.length === 0 && (
        <Card className="border-2 border-dashed border-zinc-300">
          <CardContent className="py-12 text-center">
            <Users className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-zinc-600 mb-2">Captura Semanal de Incidencias</h3>
            <p className="text-zinc-400 text-sm max-w-md mx-auto mb-4">
              Capture día por día las incidencias de cada colaborador usando los símbolos del catálogo.
            </p>
            <div className="text-xs text-zinc-500 space-y-1">
              <p><strong>Reglas:</strong></p>
              <p>• 6 días laborados = 1 día descanso proporcional</p>
              <p>• 3 retardos = 1 falta</p>
              <p>• 365 días laborados = 15 días de aguinaldo</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/**
 * Lista View - Tabla de ciclos
 */
function ListaView({
  ciclosNomina,
  ETAPAS_NOMINA,
  calcularTiempoRestante,
  handleVerMovimientosCiclo,
  setCicloSeleccionado,
  setModalHistorialCiclo,
}) {
  return (
    <Card data-testid="lista-view">
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 border-b">
              <tr>
                <th className="text-left p-3 font-medium">Sucursal</th>
                <th className="text-left p-3 font-medium">Tipo</th>
                <th className="text-left p-3 font-medium">Fecha Corte</th>
                <th className="text-left p-3 font-medium">Etapa</th>
                <th className="text-left p-3 font-medium">Deadline</th>
                <th className="text-left p-3 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ciclosNomina.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-8 text-zinc-400">No hay ciclos de nómina</td></tr>
              ) : (
                ciclosNomina.map(ciclo => {
                  const etapa = ETAPAS_NOMINA.find(e => e.id === ciclo.etapa_actual);
                  const tiempoRestante = calcularTiempoRestante(ciclo);
                  return (
                    <tr key={ciclo.id} className="border-b hover:bg-zinc-50">
                      <td className="p-3 font-medium">{ciclo.sucursal_nombre}</td>
                      <td className="p-3 capitalize">{ciclo.tipo_nomina}</td>
                      <td className="p-3">{new Date(ciclo.fecha_corte).toLocaleDateString()}</td>
                      <td className="p-3">
                        {etapa && <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium text-white ${etapa.color}`}>
                          <etapa.icon className="h-3 w-3" />{etapa.nombre}
                        </span>}
                      </td>
                      <td className="p-3">{tiempoRestante && <span className={`${tiempoRestante.color} font-medium`}>{tiempoRestante.texto}</span>}</td>
                      <td className="p-3">
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm" onClick={() => { setCicloSeleccionado(ciclo); setModalHistorialCiclo(true); }}>
                            <History className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleVerMovimientosCiclo(ciclo)}>
                            <Eye className="h-4 w-4" />
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
  );
}

/**
 * Config View - Configuración de tiempos y flujo
 */
function ConfigView({
  formConfigNomina,
  setFormConfigNomina,
  diasSemana,
  handleGuardarConfigNomina,
  savingForm,
  ETAPAS_NOMINA,
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="config-view">
      <Card>
        <CardHeader className="py-4">
          <CardTitle className="text-base flex items-center gap-2"><Clock className="h-5 w-5" />Configuración de Tiempos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Día de Corte</Label>
              <select 
                value={formConfigNomina.dia_corte} 
                onChange={(e) => setFormConfigNomina({...formConfigNomina, dia_corte: parseInt(e.target.value)})} 
                className="w-full border border-zinc-300 rounded-lg px-3 py-2 mt-1 bg-white text-zinc-900"
              >
                {diasSemana.map((dia, idx) => <option key={`rh-corte-${dia}`} value={idx}>{dia}</option>)}
              </select>
            </div>
            <div>
              <Label>Día de Pago</Label>
              <select 
                value={formConfigNomina.dia_pago} 
                onChange={(e) => setFormConfigNomina({...formConfigNomina, dia_pago: parseInt(e.target.value)})} 
                className="w-full border border-zinc-300 rounded-lg px-3 py-2 mt-1 bg-white text-zinc-900"
              >
                {diasSemana.map((dia, idx) => <option key={`rh-pago-${dia}`} value={idx}>{dia}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <Label>Horario Headcount</Label>
              <Input type="time" value={formConfigNomina.horario_headcount} onChange={(e) => setFormConfigNomina({...formConfigNomina, horario_headcount: e.target.value})} className="mt-1" />
            </div>
            <div>
              <Label>Horario Autorización</Label>
              <Input type="time" value={formConfigNomina.horario_autorizacion} onChange={(e) => setFormConfigNomina({...formConfigNomina, horario_autorizacion: e.target.value})} className="mt-1" />
            </div>
            <div>
              <Label>Horario Maquilador</Label>
              <Input type="time" value={formConfigNomina.horario_maquilador} onChange={(e) => setFormConfigNomina({...formConfigNomina, horario_maquilador: e.target.value})} className="mt-1" />
            </div>
            <div>
              <Label>Horario Tesorería</Label>
              <Input type="time" value={formConfigNomina.horario_tesoreria} onChange={(e) => setFormConfigNomina({...formConfigNomina, horario_tesoreria: e.target.value})} className="mt-1" />
            </div>
          </div>
          <Button onClick={handleGuardarConfigNomina} disabled={savingForm} className="w-full">
            {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}Guardar Configuración
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="py-4">
          <CardTitle className="text-base flex items-center gap-2"><ArrowRight className="h-5 w-5" />Flujo de Nómina</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {ETAPAS_NOMINA.map((etapa, idx) => {
              const IconoEtapa = etapa.icon;
              return (
                <div key={etapa.id} className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${etapa.color}`}><IconoEtapa className="h-4 w-4 text-white" /></div>
                  <div className="flex-1">
                    <p className="font-medium text-sm">{idx + 1}. {etapa.nombre}</p>
                    <p className="text-xs text-zinc-500">Responsable: {etapa.responsable}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
