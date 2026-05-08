/**
 * Componente Tesorería - Cuadre de Cortes Z
 * 
 * Funcionalidades:
 * 1. Dashboard de Cortes Z pendientes de cuadrar
 * 2. Conteo de efectivo (billetes y monedas)
 * 3. Carga y validación de fichas de depósito
 * 4. Validación de fechas (día hábil siguiente)
 * 
 * REFACTORIZADO: Lógica extraída a useTesoreriaCorteZData hook
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { 
  Building2, Calendar, DollarSign, CheckCircle2, AlertCircle, 
  Clock, RefreshCw, X, Search, Filter, Eye, Check,
  Banknote
} from 'lucide-react';
import {
  useTesoreriaCorteZData,
  ConteoEfectivo,
  ResumenCards,
  CorteCard,
  FichaDepositoForm,
  ComparativaCard,
  EmptyState,
  formatCurrency,
  formatDate
} from './tesoreria';

// ============================================================================
// Componente Principal
// ============================================================================

const TesoreriaCorteZ = () => {
  const {
    loading,
    cortesZ,
    cuadres,
    resumen,
    selectedCorte,
    modalOpen,
    conteoEfectivo,
    fichaDeposito,
    filtros,
    vistaActiva,
    unidadesNegocio,
    loadingUnidades,
    setModalOpen,
    setConteoEfectivo,
    setVistaActiva,
    loadCortesZ,
    refetchAll,
    handleIniciarCuadre,
    handleGuardarCuadre,
    calcularTotalContado,
    updateFiltros,
    updateFichaDeposito
  } = useTesoreriaCorteZData();

  // Renderizar lista de cortes pendientes
  const renderCortesPendientes = () => {
    const pendientes = cortesZ.filter(c => !c.tiene_cuadre);
    
    if (pendientes.length === 0) {
      return <EmptyState message="No hay cortes pendientes de cuadrar" iconColor="text-green-300" />;
    }
    
    return (
      <div className="space-y-2">
        {pendientes.map(corte => (
          <CorteCard
            key={`${corte.sucursal_id}_${corte.folio_corte}`}
            corte={corte}
            onIniciarCuadre={handleIniciarCuadre}
          />
        ))}
      </div>
    );
  };

  // Renderizar lista de cuadres
  const renderCuadresRegistrados = () => {
    if (cuadres.length === 0) {
      return <EmptyState icon={AlertCircle} message="No hay cuadres registrados" iconColor="text-zinc-300" />;
    }
    
    return (
      <div className="space-y-2">
        {cuadres.map(cuadre => (
          <Card 
            key={cuadre.id} 
            className={`border-l-4 ${
              cuadre.estado === 'CUADRADO' ? 'border-l-green-500' :
              cuadre.estado === 'DESCUADRE' ? 'border-l-red-500' :
              cuadre.estado === 'EN_PROCESO' ? 'border-l-blue-500' :
              'border-l-yellow-500'
            }`}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-medium">{cuadre.corte_z?.sucursal_nombre}</p>
                    <p className="text-xs text-zinc-500">
                      Folio: {cuadre.corte_z?.folio_corte} | {formatDate(cuadre.corte_z?.fecha_corte)}
                    </p>
                  </div>
                  <div className="text-center px-4 border-l">
                    <p className="text-xs text-zinc-500">Esperado</p>
                    <p className="font-medium">{formatCurrency(cuadre.monto_esperado)}</p>
                  </div>
                  <div className="text-center px-4 border-l">
                    <p className="text-xs text-zinc-500">Depositado</p>
                    <p className="font-medium">{formatCurrency(cuadre.monto_depositado)}</p>
                  </div>
                  <div className="text-center px-4 border-l">
                    <p className="text-xs text-zinc-500">Diferencia</p>
                    <p className={`font-bold ${cuadre.diferencia === 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(cuadre.diferencia)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    cuadre.estado === 'CUADRADO' ? 'bg-green-100 text-green-700' :
                    cuadre.estado === 'DESCUADRE' ? 'bg-red-100 text-red-700' :
                    cuadre.estado === 'EN_PROCESO' ? 'bg-blue-100 text-blue-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {cuadre.estado}
                  </span>
                  {cuadre.validacion_fecha ? (
                    <Check className="h-5 w-5 text-green-500" title="Fecha válida" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-orange-500" title="Revisar fecha" />
                  )}
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  // Modal de cuadre
  const renderModal = () => {
    if (!modalOpen || !selectedCorte) return null;
    
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="bg-zinc-800 text-white p-4 rounded-t-xl flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold">Cuadre de Corte Z</h2>
              <p className="text-sm text-zinc-300">
                {selectedCorte.sucursal_nombre} - Folio {selectedCorte.folio_corte}
              </p>
            </div>
            <button onClick={() => setModalOpen(false)} className="p-2 hover:bg-zinc-700 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Datos del Corte Z */}
            <Card className="bg-zinc-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Datos del Corte Z</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-zinc-500">Fecha Corte</p>
                    <p className="font-medium">{formatDate(selectedCorte.fecha_corte)}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Efectivo Ventas</p>
                    <p className="font-medium text-green-600">{formatCurrency(selectedCorte.efectivo_ventas)}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Propinas Pagadas</p>
                    <p className="font-medium text-orange-600">{formatCurrency(selectedCorte.propinas_pagadas)}</p>
                  </div>
                  <div className="bg-amber-100 rounded p-2 -m-2">
                    <p className="text-zinc-500">Monto a Depositar</p>
                    <p className="font-bold text-xl">{formatCurrency(selectedCorte.monto_a_depositar)}</p>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-blue-500" />
                  <span>Fecha esperada de depósito: </span>
                  <span className="font-medium text-blue-600">{formatDate(selectedCorte.fecha_deposito_esperada)}</span>
                </div>
              </CardContent>
            </Card>
            
            <div className="grid grid-cols-2 gap-6">
              {/* Conteo de Efectivo */}
              <div>
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <Banknote className="h-5 w-5 text-green-600" />
                  Conteo de Efectivo Entregado
                </h3>
                <ConteoEfectivo 
                  conteo={conteoEfectivo} 
                  onChange={setConteoEfectivo} 
                />
              </div>
              
              {/* Ficha de Depósito */}
              <FichaDepositoForm 
                fichaDeposito={fichaDeposito}
                onUpdate={updateFichaDeposito}
              />
            </div>
            
            {/* Comparativa */}
            <ComparativaCard
              esperado={selectedCorte.monto_a_depositar}
              contado={calcularTotalContado()}
              depositado={fichaDeposito.importe}
            />
            
            {/* Acciones */}
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setModalOpen(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={handleGuardarCuadre}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700"
              >
                {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : null}
                Guardar Cuadre
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6" data-testid="tesoreria-corte-z">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Cuadre de Cortes Z</h2>
          <p className="text-sm text-zinc-500">Conciliación de efectivo y depósitos bancarios</p>
        </div>
        <Button onClick={refetchAll} variant="outline">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>
      
      {/* Resumen */}
      <ResumenCards resumen={resumen} />
      
      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-zinc-400" />
              <span className="text-sm font-medium">Filtros:</span>
            </div>
            {/* Selector de Unidad de Negocio */}
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-zinc-400" />
              {unidadesNegocio.length === 1 ? (
                <div className="px-3 py-2 border rounded text-sm bg-zinc-50">
                  {unidadesNegocio[0].nombre}
                </div>
              ) : (
                <select
                  value={filtros.server_id}
                  onChange={(e) => updateFiltros('server_id', e.target.value)}
                  className="border rounded px-3 py-2 text-sm"
                  disabled={loadingUnidades}
                  data-testid="filtro-unidad-tesoreria"
                >
                  <option value="">{loadingUnidades ? "Cargando..." : "Todas las unidades"}</option>
                  {unidadesNegocio.map(u => (
                    <option key={u.id} value={u.id}>{u.nombre}</option>
                  ))}
                </select>
              )}
            </div>
            <Input
              type="date"
              value={filtros.fechaInicio}
              onChange={(e) => updateFiltros('fechaInicio', e.target.value)}
              className="w-40"
              placeholder="Desde"
            />
            <Input
              type="date"
              value={filtros.fechaFin}
              onChange={(e) => updateFiltros('fechaFin', e.target.value)}
              className="w-40"
              placeholder="Hasta"
            />
            <Button onClick={loadCortesZ} size="sm">
              <Search className="h-4 w-4 mr-1" />
              Buscar
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Tabs de vista */}
      <div className="flex gap-2 border-b">
        {[
          { id: 'pendientes', label: 'Pendientes de Cuadrar', icon: Clock },
          { id: 'cuadrados', label: 'Cuadres Registrados', icon: CheckCircle2 }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setVistaActiva(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
              vistaActiva === tab.id 
                ? 'border-amber-500 text-amber-600' 
                : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Contenido según vista */}
      {loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <RefreshCw className="h-8 w-8 text-zinc-400 mx-auto mb-3 animate-spin" />
            <p className="text-zinc-500">Cargando datos...</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {vistaActiva === 'pendientes' && renderCortesPendientes()}
          {vistaActiva === 'cuadrados' && renderCuadresRegistrados()}
        </>
      )}
      
      {/* Modal */}
      {renderModal()}
    </div>
  );
};

export default TesoreriaCorteZ;
