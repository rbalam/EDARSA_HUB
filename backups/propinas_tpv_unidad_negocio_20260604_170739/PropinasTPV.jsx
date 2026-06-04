/**
 * EDARSA HUB - Módulo de Control de Propinas TPV
 * ===============================================
 * Refactorizado: Subcomponentes en /components/finanzas/propinas/
 * 
 * SUBFASE 3.5: Migrado a endpoints EDARSAHUB v2
 * Fuente de datos: EDARSAHUB.propinas_tpv_control
 * 
 * Tabs:
 * - Cuadre: Listado y cuadre de propinas por corte
 * - Configuración: Gestión del % de descuento
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import { getSessionUser } from '../services/authStorage';
import logger from '../services/logger';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Settings, Calculator, RefreshCw, Plus, AlertCircle, Building2, Database } from 'lucide-react';

// Corporate Filters - SQL-FIRST
import { CorporateFiltersProvider, CorporateFilterBar, useCorporateFilters } from '../filters';

// Subcomponentes refactorizados
import {
  getDefaultConfig,
  PropinasKPICards,
  PropinasTable,
  PropinasConfigForm,
  PropinasConfigList
} from './finanzas/propinas';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Componente interno que usa Corporate Filters
function PropinasTPVContent() {
  // Corporate Filters - SQL-FIRST
  const { filters: corporateFilters, status: corporateStatus } = useCorporateFilters();
  
  const [activeTab, setActiveTab] = useState('cuadre');
  
  // Estado de configuración
  const [configs, setConfigs] = useState([]);
  const [loadingConfigs, setLoadingConfigs] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [showNewConfig, setShowNewConfig] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [newConfig, setNewConfig] = useState(getDefaultConfig());
  
  // Estado de cuadre - SUBFASE 3.5: Migrado a EDARSAHUB
  const [propinas, setPropinas] = useState([]);
  const [loadingPropinas, setLoadingPropinas] = useState(false);
  const [totalesServer, setTotalesServer] = useState(null); // Totales del servidor
  const [fuenteDatos, setFuenteDatos] = useState(null); // Indicador de fuente
  const [filtros, setFiltros] = useState({
    fecha_inicio: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    fecha_fin: new Date().toISOString().split('T')[0],
    estado: '',
    unidad_negocio_id: '' // SUBFASE 3.5: Cambiado de server_id a unidad_negocio_id
  });
  
  // Datos auxiliares - Corporate Filters (SQL-FIRST)
  const sucursales = corporateFilters?.sucursales || [];
  const empresas = corporateFilters?.empresas || [];
  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
  const [loadingUnidades, setLoadingUnidades] = useState(false);
  const [userRole, setUserRole] = useState('');
  
  useEffect(() => {
    const user = getSessionUser() || {};
    setUserRole(user.role || '');
    // cargarDatosAuxiliares eliminado - ahora usa Corporate Filters
    cargarUnidadesNegocio();
  }, []);
  
  useEffect(() => {
    if (activeTab === 'configuracion') cargarConfigs();
    else if (activeTab === 'cuadre') cargarPropinas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);
  
  // SUBFASE 3.5: Cargar unidades desde endpoint EDARSAHUB v2
  const cargarUnidadesNegocio = async () => {
    setLoadingUnidades(true);
    try {
      // Endpoint v2 EDARSAHUB - único origen
      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
        credentials: 'include'
      });
      
      if (resV2.ok) {
        const dataV2 = await resV2.json();
        // Formatear unidades desde EDARSAHUB
        const unidades = (dataV2.unidades || []).map(u => ({
          id: u.unidad_negocio_id,
          nombre: u.unidad_negocio_nombre,
          sistema: u.sistema_origen,
          registros: u.total_registros,
          propinas: u.total_propinas
        }));
        setUnidadesNegocio(unidades);
        
        // Si solo hay 1 unidad, seleccionarla automáticamente
        if (unidades.length === 1) {
          setFiltros(prev => ({ ...prev, unidad_negocio_id: unidades[0].id }));
        }
        return;
      }
      
      // Fallback: usar unidades de Corporate Filters
      const unidadesCF = corporateFilters?.unidades_negocio || [];
      if (unidadesCF.length > 0) {
        const unidades = unidadesCF.map(u => ({
          id: u.id,
          nombre: u.nombre,
          sistema: 'EDARSAHUB',
          registros: 0,
          propinas: 0
        }));
        setUnidadesNegocio(unidades);
        if (unidades.length === 1) {
          setFiltros(prev => ({ ...prev, unidad_negocio_id: unidades[0].id }));
        }
      }
    } catch (error) {
      logger.error('Error cargando unidades:', error);
    } finally {
      setLoadingUnidades(false);
    }
  };
  
  const cargarConfigs = useCallback(async () => {
    setLoadingConfigs(true);
    try {
      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setConfigs(data.configs || []);
      }
    } catch (error) {
      // Error silenciado
    } finally {
      setLoadingConfigs(false);
    }
  }, []);
  
  // SUBFASE 3.5: Cargar propinas desde EDARSAHUB v2
  const cargarPropinas = useCallback(async () => {
    setLoadingPropinas(true);
    setFuenteDatos(null);
    
    try {
      const params = new URLSearchParams();
      params.append('fecha_inicio', filtros.fecha_inicio);
      params.append('fecha_fin', filtros.fecha_fin);
      
      // Usar unidad_negocio_id para filtro (o TODAS si vacío)
      if (filtros.unidad_negocio_id) {
        params.append('unidad_negocio_id', filtros.unidad_negocio_id);
      } else {
        params.append('unidad_negocio_id', 'TODAS');
      }
      
      // Llamar endpoint v2 EDARSAHUB
      const res = await fetch(`${API_URL}/api/finanzas/propinas/v2/detalle?${params.toString()}`, {
        credentials: 'include'
      });
      
      if (res.ok) {
        const data = await res.json();
        
        // Transformar datos de EDARSAHUB al formato esperado por los componentes
        const propinasTransformadas = (data.detalle || []).map(p => ({
          id: p.id,
          server_name: p.unidad_negocio_nombre,
          sucursal_nombre: p.sucursal_nombre || p.unidad_negocio_nombre,
          folio_corte: p.folio_corte || p.folio_origen,
          fecha_corte: p.fecha_operacion,
          origen: {
            propinas_tpv: p.importe_propina_tpv,
            propinas_totales_corte: p.importe_propina_tpv,
            ventas_tarjeta: 0
          },
          calculo: {
            porcentaje_comision: p.porcentaje_comision || 0.02,
            comision_calculada: p.importe_comision,
            monto_a_pagar_meseros: p.importe_neto_a_entregar
          },
          cuadre: {
            estado: 'PENDIENTE' // Estado por defecto
          },
          pago: {
            monto_pagado: 0
          },
          // Metadata EDARSAHUB
          sistema_origen: p.sistema_origen,
          unidad_negocio_id: p.unidad_negocio_id,
          forma_pago: p.forma_pago_nombre
        }));
        
        setPropinas(propinasTransformadas);
        setTotalesServer(data.totales);
        setFuenteDatos(data.fuente || 'EDARSAHUB_REAL');
        
        return;
      }
      
      // Si falla v2, no usar fallback MongoDB (según máximas)
      logger.warn('Endpoint v2 no disponible, verificar autenticación');
      setPropinas([]);
      setTotalesServer(null);
      setFuenteDatos('ERROR');
      
    } catch (error) {
      logger.error('Error cargando propinas:', error);
      setPropinas([]);
      setTotalesServer(null);
      setFuenteDatos('ERROR');
    } finally {
      setLoadingPropinas(false);
    }
  }, [filtros]);
  
  const guardarConfig = async () => {
    const configData = editingConfig || newConfig;
    const isNew = !editingConfig;
    setSavingConfig(true);
    
    try {
      const url = isNew 
        ? `${API_URL}/api/finanzas/propinas/config`
        : `${API_URL}/api/finanzas/propinas/config/${configData.id}`;
      
      const res = await fetch(url, {
        method: isNew ? 'POST' : 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
      });
      
      if (res.ok) {
        await cargarConfigs();
        setShowNewConfig(false);
        setEditingConfig(null);
        setNewConfig(getDefaultConfig());
      } else {
        const error = await res.json();
        alert(error.detail || 'Error guardando configuración');
      }
    } catch (error) {
      logger.error('Error:', error);
      alert('Error de conexión');
    } finally {
      setSavingConfig(false);
    }
  };
  
  const handleCancelarConfig = () => {
    setShowNewConfig(false);
    setEditingConfig(null);
  };
  
  const isAdmin = useMemo(() => {
    return ['admin', 'superadmin', 'Admin', 'Administrador'].includes(userRole);
  }, [userRole]);
  
  // SUBFASE 3.5: Usar totales del servidor si están disponibles
  const totalesPropinas = useMemo(() => {
    // Si tenemos totales del servidor EDARSAHUB, usarlos
    if (totalesServer) {
      return {
        propinas_tpv: totalesServer.total_propinas_tpv || 0,
        comision: totalesServer.total_comision || 0,
        a_pagar: totalesServer.total_neto_a_entregar || 0,
        pagado: 0 // Estado de pago no está en EDARSAHUB aún
      };
    }
    
    // Fallback: calcular desde propinas locales
    return propinas.reduce((acc, p) => {
      acc.propinas_tpv += p.origen?.propinas_tpv || 0;
      acc.comision += p.calculo?.comision_calculada || 0;
      acc.a_pagar += p.calculo?.monto_a_pagar_meseros || 0;
      acc.pagado += p.pago?.monto_pagado || 0;
      return acc;
    }, { propinas_tpv: 0, comision: 0, a_pagar: 0, pagado: 0 });
  }, [propinas, totalesServer]);
  
  return (
    <div className="space-y-4" data-testid="propinas-tpv-module">
      {/* Header con tabs */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Control de Propinas TPV</h1>
          <p className="text-sm text-zinc-500">
            Cuadre y configuración del porcentaje de descuento
            {fuenteDatos && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                <Database className="h-3 w-3 mr-1" />
                {fuenteDatos}
              </span>
            )}
          </p>
        </div>
        
        <div className="flex bg-zinc-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('cuadre')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition ${
              activeTab === 'cuadre' ? 'bg-white text-zinc-900 shadow' : 'text-zinc-600 hover:text-zinc-900'
            }`}
            data-testid="tab-cuadre"
          >
            <Calculator className="h-4 w-4 inline mr-2" />
            Cuadre
          </button>
          <button
            onClick={() => setActiveTab('configuracion')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition ${
              activeTab === 'configuracion' ? 'bg-white text-zinc-900 shadow' : 'text-zinc-600 hover:text-zinc-900'
            }`}
            data-testid="tab-configuracion"
          >
            <Settings className="h-4 w-4 inline mr-2" />
            Configuración
          </button>
        </div>
      </div>
      
      {/* TAB: CUADRE */}
      {activeTab === 'cuadre' && (
        <div className="space-y-4">
          {/* Filtros */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex flex-wrap gap-4 items-end">
                {/* Selector de Unidad de Negocio - SUBFASE 3.5: Usa unidad_negocio_id */}
                <div>
                  <Label className="text-xs text-zinc-500">Unidad de Negocio</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Building2 className="h-4 w-4 text-zinc-400" />
                    {unidadesNegocio.length === 1 ? (
                      <div className="px-3 py-2 border rounded-lg text-sm bg-zinc-50 w-48">
                        {unidadesNegocio[0].nombre}
                      </div>
                    ) : (
                      <select
                        value={filtros.unidad_negocio_id}
                        onChange={(e) => setFiltros({...filtros, unidad_negocio_id: e.target.value})}
                        className="w-48 h-10 px-3 border rounded-md text-sm"
                        disabled={loadingUnidades}
                        data-testid="filtro-unidad"
                      >
                        <option value="">{loadingUnidades ? "Cargando..." : "Todas las unidades"}</option>
                        {unidadesNegocio.map(u => (
                          <option key={u.id} value={u.id}>
                            {u.nombre} {u.sistema ? `(${u.sistema})` : ''}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Fecha Inicio</Label>
                  <Input
                    type="date"
                    value={filtros.fecha_inicio}
                    onChange={(e) => setFiltros({...filtros, fecha_inicio: e.target.value})}
                    className="w-40"
                    data-testid="filtro-fecha-inicio"
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Fecha Fin</Label>
                  <Input
                    type="date"
                    value={filtros.fecha_fin}
                    onChange={(e) => setFiltros({...filtros, fecha_fin: e.target.value})}
                    className="w-40"
                    data-testid="filtro-fecha-fin"
                  />
                </div>
                <div>
                  <Label className="text-xs text-zinc-500">Estado</Label>
                  <select
                    value={filtros.estado}
                    onChange={(e) => setFiltros({...filtros, estado: e.target.value})}
                    className="w-40 h-10 px-3 border rounded-md text-sm opacity-50"
                    data-testid="filtro-estado"
                    disabled
                    title="Filtro de estado pendiente de implementar"
                  >
                    <option value="">Todos</option>
                    <option value="PENDIENTE">Pendiente</option>
                    <option value="PAGADO">Pagado</option>
                    <option value="CUADRADO">Cuadrado</option>
                    <option value="DESCUADRE">Descuadre</option>
                  </select>
                </div>
                <Button onClick={cargarPropinas} variant="outline" data-testid="btn-buscar-propinas">
                  <RefreshCw className={`h-4 w-4 mr-2 ${loadingPropinas ? 'animate-spin' : ''}`} />
                  Buscar
                </Button>
              </div>
            </CardContent>
          </Card>
          
          <PropinasKPICards totales={totalesPropinas} />
          <PropinasTable propinas={propinas} loading={loadingPropinas} fuenteDatos={fuenteDatos} />
        </div>
      )}
      
      {/* TAB: CONFIGURACIÓN */}
      {activeTab === 'configuracion' && (
        <div className="space-y-4">
          {isAdmin && !showNewConfig && !editingConfig && (
            <div className="flex justify-end">
              <Button onClick={() => setShowNewConfig(true)} data-testid="btn-nueva-config">
                <Plus className="h-4 w-4 mr-2" />
                Nueva Configuración
              </Button>
            </div>
          )}
          
          {(showNewConfig || editingConfig) && isAdmin && (
            <PropinasConfigForm
              config={editingConfig || newConfig}
              setConfig={editingConfig ? setEditingConfig : setNewConfig}
              empresas={empresas}
              sucursales={sucursales}
              onGuardar={guardarConfig}
              onCancelar={handleCancelarConfig}
              saving={savingConfig}
              isEditing={!!editingConfig}
            />
          )}
          
          <PropinasConfigList
            configs={configs}
            loading={loadingConfigs}
            onRefresh={cargarConfigs}
            onEdit={setEditingConfig}
            isAdmin={isAdmin}
          />
          
          {/* Info de jerarquía */}
          <Card className="bg-zinc-50">
            <CardContent className="pt-4">
              <h3 className="font-medium text-zinc-700 mb-2 flex items-center">
                <AlertCircle className="h-4 w-4 mr-2 text-blue-500" />
                Jerarquía de Aplicación
              </h3>
              <p className="text-sm text-zinc-600">
                El sistema aplica la configuración más específica disponible:
              </p>
              <ol className="text-sm text-zinc-600 mt-2 space-y-1 ml-6 list-decimal">
                <li><strong>Sucursal</strong>: Si existe config para la sucursal específica, se usa.</li>
                <li><strong>Empresa</strong>: Si no hay config de sucursal, se busca por empresa.</li>
                <li><strong>Global</strong>: Si no hay ninguna específica, se usa la global (default 2%).</li>
              </ol>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// Wrapper con Corporate Filters Provider
export default function PropinasTPV() {
  return (
    <CorporateFiltersProvider scope="finanzas.propinas_tpv">
      <CorporateFilterBar
        title="Filtros Corporativos"
        filters={[
          { key: "empresas", label: "Empresa" },
          { key: "unidades_negocio", label: "Unidad de Negocio" },
          { key: "sucursales", label: "Sucursal" }
        ]}
      />
      <PropinasTPVContent />
    </CorporateFiltersProvider>
  );
}
