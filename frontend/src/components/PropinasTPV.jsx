/**
 * EDARSA HUB - Módulo de Control de Propinas TPV
 * ===============================================
 * Fecha: 15 de Abril de 2026
 * 
 * Tabs:
 * - Cuadre: Listado y cuadre de propinas por corte
 * - Configuración: Gestión del % de descuento
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Settings,
  Calculator,
  RefreshCw,
  Save,
  Plus,
  Edit2,
  Check,
  X,
  AlertCircle,
  Building,
  Store,
  Percent,
  Calendar,
  History,
  ChevronRight,
  DollarSign
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Utilidades de formato
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2
  }).format(value);
};

const formatPercent = (value) => {
  if (value === null || value === undefined) return '-';
  return `${(value * 100).toFixed(2)}%`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('es-MX', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

export default function PropinasTPV() {
  // Estado de tabs
  const [activeTab, setActiveTab] = useState('cuadre');
  
  // Estado de configuración
  const [configs, setConfigs] = useState([]);
  const [loadingConfigs, setLoadingConfigs] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [showNewConfig, setShowNewConfig] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  
  // Estado para nueva config
  const [newConfig, setNewConfig] = useState({
    alcance: { tipo: 'GLOBAL', server_id: null, empresa_id: null, sucursal_id: null },
    vigencia: { fecha_inicio: new Date().toISOString().split('T')[0], fecha_fin: null, activa: true },
    parametros: { porcentaje_comision: 0.02, tolerancia_descuadre: 5.0, dias_para_cuadrar: 1 },
    motivo_cambio: ''
  });
  
  // Estado de cuadre (listado de propinas)
  const [propinas, setPropinas] = useState([]);
  const [loadingPropinas, setLoadingPropinas] = useState(false);
  const [filtros, setFiltros] = useState({
    fecha_inicio: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    fecha_fin: new Date().toISOString().split('T')[0],
    estado: ''
  });
  
  // Datos auxiliares
  const [sucursales, setSucursales] = useState([]);
  const [empresas, setEmpresas] = useState([]);
  const [userRole, setUserRole] = useState('');
  
  // Cargar datos iniciales
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setUserRole(user.role || '');
    
    // Cargar empresas y sucursales para los selectores
    cargarDatosAuxiliares();
  }, []);
  
  // Cargar configs cuando se activa el tab
  useEffect(() => {
    if (activeTab === 'configuracion') {
      cargarConfigs();
    } else if (activeTab === 'cuadre') {
      cargarPropinas();
    }
  }, [activeTab]);
  
  const cargarDatosAuxiliares = async () => {
    const token = localStorage.getItem('token');
    try {
      // Cargar sucursales
      const resSuc = await fetch(`${API_URL}/api/sucursales`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resSuc.ok) {
        const data = await resSuc.json();
        setSucursales(data.sucursales || data || []);
      }
      
      // Cargar empresas (pueden venir de servers o config)
      const resServers = await fetch(`${API_URL}/api/servers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resServers.ok) {
        const data = await resServers.json();
        const empresasSet = new Set();
        (data || []).forEach(s => {
          if (s.empresa) empresasSet.add(s.empresa);
        });
        setEmpresas(Array.from(empresasSet));
      }
    } catch (error) {
      console.error('Error cargando datos auxiliares:', error);
    }
  };
  
  const cargarConfigs = async () => {
    setLoadingConfigs(true);
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConfigs(data.configs || []);
      } else {
        console.error('Error cargando configs');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoadingConfigs(false);
    }
  };
  
  const cargarPropinas = async () => {
    setLoadingPropinas(true);
    const token = localStorage.getItem('token');
    try {
      const params = new URLSearchParams();
      if (filtros.fecha_inicio) params.append('fecha_inicio', filtros.fecha_inicio);
      if (filtros.fecha_fin) params.append('fecha_fin', filtros.fecha_fin);
      if (filtros.estado) params.append('estado', filtros.estado);
      
      const res = await fetch(`${API_URL}/api/finanzas/propinas?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPropinas(data.propinas || []);
      }
    } catch (error) {
      console.error('Error cargando propinas:', error);
    } finally {
      setLoadingPropinas(false);
    }
  };
  
  const guardarConfig = async (configData, isNew = true) => {
    setSavingConfig(true);
    const token = localStorage.getItem('token');
    
    try {
      const url = isNew 
        ? `${API_URL}/api/finanzas/propinas/config`
        : `${API_URL}/api/finanzas/propinas/config/${configData.id}`;
      
      const method = isNew ? 'POST' : 'PUT';
      
      const res = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
      });
      
      if (res.ok) {
        await cargarConfigs();
        setShowNewConfig(false);
        setEditingConfig(null);
        setNewConfig({
          alcance: { tipo: 'GLOBAL', server_id: null, empresa_id: null, sucursal_id: null },
          vigencia: { fecha_inicio: new Date().toISOString().split('T')[0], fecha_fin: null, activa: true },
          parametros: { porcentaje_comision: 0.02, tolerancia_descuadre: 5.0, dias_para_cuadrar: 1 },
          motivo_cambio: ''
        });
      } else {
        const error = await res.json();
        alert(error.detail || 'Error guardando configuración');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error de conexión');
    } finally {
      setSavingConfig(false);
    }
  };
  
  const isAdmin = useMemo(() => {
    return ['admin', 'superadmin', 'Admin', 'Administrador'].includes(userRole);
  }, [userRole]);
  
  // Calcular totales de propinas
  const totalesPropinas = useMemo(() => {
    return propinas.reduce((acc, p) => {
      acc.propinas_tpv += p.origen?.propinas_tpv || 0;
      acc.comision += p.calculo?.comision_calculada || 0;
      acc.a_pagar += p.calculo?.monto_a_pagar_meseros || 0;
      acc.pagado += p.pago?.monto_pagado || 0;
      return acc;
    }, { propinas_tpv: 0, comision: 0, a_pagar: 0, pagado: 0 });
  }, [propinas]);
  
  return (
    <div className="space-y-4" data-testid="propinas-tpv-module">
      {/* Header con tabs */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Control de Propinas TPV</h1>
          <p className="text-sm text-zinc-500">Cuadre y configuración del porcentaje de descuento</p>
        </div>
        
        {/* Tabs */}
        <div className="flex bg-zinc-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('cuadre')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition ${
              activeTab === 'cuadre'
                ? 'bg-white text-zinc-900 shadow'
                : 'text-zinc-600 hover:text-zinc-900'
            }`}
            data-testid="tab-cuadre"
          >
            <Calculator className="h-4 w-4 inline mr-2" />
            Cuadre
          </button>
          <button
            onClick={() => setActiveTab('configuracion')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition ${
              activeTab === 'configuracion'
                ? 'bg-white text-zinc-900 shadow'
                : 'text-zinc-600 hover:text-zinc-900'
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
                    className="w-40 h-10 px-3 border rounded-md text-sm"
                    data-testid="filtro-estado"
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
          
          {/* Resumen */}
          <div className="grid grid-cols-4 gap-4">
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-4">
                <p className="text-xs text-blue-600 font-medium">Propinas TPV</p>
                <p className="text-2xl font-bold text-blue-700">{formatCurrency(totalesPropinas.propinas_tpv)}</p>
              </CardContent>
            </Card>
            <Card className="bg-amber-50 border-amber-200">
              <CardContent className="pt-4">
                <p className="text-xs text-amber-600 font-medium">Comisión (2%)</p>
                <p className="text-2xl font-bold text-amber-700">{formatCurrency(totalesPropinas.comision)}</p>
              </CardContent>
            </Card>
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-4">
                <p className="text-xs text-green-600 font-medium">A Pagar Meseros</p>
                <p className="text-2xl font-bold text-green-700">{formatCurrency(totalesPropinas.a_pagar)}</p>
              </CardContent>
            </Card>
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="pt-4">
                <p className="text-xs text-purple-600 font-medium">Pagado</p>
                <p className="text-2xl font-bold text-purple-700">{formatCurrency(totalesPropinas.pagado)}</p>
              </CardContent>
            </Card>
          </div>
          
          {/* Listado de propinas */}
          <Card>
            <CardHeader className="bg-zinc-800 text-white py-3">
              <CardTitle className="text-base flex items-center">
                <DollarSign className="h-5 w-5 mr-2" />
                Propinas por Corte ({propinas.length} registros)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loadingPropinas ? (
                <div className="p-8 text-center text-zinc-500">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
                  Cargando...
                </div>
              ) : propinas.length === 0 ? (
                <div className="p-8 text-center text-zinc-500">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  No hay propinas en el período seleccionado
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-100">
                      <tr>
                        <th className="text-left p-3 font-medium">Sucursal</th>
                        <th className="text-center p-3 font-medium">Folio</th>
                        <th className="text-center p-3 font-medium">Fecha</th>
                        <th className="text-right p-3 font-medium">Propinas TPV</th>
                        <th className="text-right p-3 font-medium">Comisión</th>
                        <th className="text-right p-3 font-medium">A Pagar</th>
                        <th className="text-center p-3 font-medium">Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {propinas.map((propina, idx) => (
                        <tr key={propina.id || idx} className="border-b hover:bg-zinc-50">
                          <td className="p-3">{propina.sucursal_nombre || propina.server_name}</td>
                          <td className="p-3 text-center font-mono">{propina.folio_corte}</td>
                          <td className="p-3 text-center">{formatDate(propina.fecha_corte)}</td>
                          <td className="p-3 text-right font-mono">{formatCurrency(propina.origen?.propinas_tpv)}</td>
                          <td className="p-3 text-right font-mono text-amber-600">
                            {formatCurrency(propina.calculo?.comision_calculada)}
                          </td>
                          <td className="p-3 text-right font-mono font-bold text-green-600">
                            {formatCurrency(propina.calculo?.monto_a_pagar_meseros)}
                          </td>
                          <td className="p-3 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              propina.cuadre?.estado === 'CUADRADO' ? 'bg-green-100 text-green-700' :
                              propina.cuadre?.estado === 'PAGADO' ? 'bg-blue-100 text-blue-700' :
                              propina.cuadre?.estado === 'DESCUADRE' ? 'bg-red-100 text-red-700' :
                              'bg-zinc-100 text-zinc-700'
                            }`}>
                              {propina.cuadre?.estado || 'PENDIENTE'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* TAB: CONFIGURACIÓN */}
      {activeTab === 'configuracion' && (
        <div className="space-y-4">
          {/* Botón nueva config (solo admins) */}
          {isAdmin && !showNewConfig && (
            <div className="flex justify-end">
              <Button onClick={() => setShowNewConfig(true)} data-testid="btn-nueva-config">
                <Plus className="h-4 w-4 mr-2" />
                Nueva Configuración
              </Button>
            </div>
          )}
          
          {/* Formulario nueva/editar config */}
          {(showNewConfig || editingConfig) && isAdmin && (
            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardHeader className="bg-blue-600 text-white py-3">
                <CardTitle className="text-base">
                  {editingConfig ? 'Editar Configuración' : 'Nueva Configuración de % Descuento'}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  {/* Alcance */}
                  <div>
                    <Label className="text-xs text-zinc-500">Tipo de Alcance</Label>
                    <select
                      value={(editingConfig || newConfig).alcance.tipo}
                      onChange={(e) => {
                        const tipo = e.target.value;
                        const updater = editingConfig ? setEditingConfig : setNewConfig;
                        updater(prev => ({
                          ...prev,
                          alcance: {
                            ...prev.alcance,
                            tipo,
                            empresa_id: tipo === 'GLOBAL' ? null : prev.alcance.empresa_id,
                            sucursal_id: tipo !== 'SUCURSAL' ? null : prev.alcance.sucursal_id
                          }
                        }));
                      }}
                      className="w-full h-10 px-3 border rounded-md text-sm"
                      data-testid="config-alcance-tipo"
                    >
                      <option value="GLOBAL">GLOBAL (Toda la empresa)</option>
                      <option value="EMPRESA">Por Empresa</option>
                      <option value="SUCURSAL">Por Sucursal</option>
                    </select>
                  </div>
                  
                  {/* Empresa (si aplica) */}
                  {(editingConfig || newConfig).alcance.tipo !== 'GLOBAL' && (
                    <div>
                      <Label className="text-xs text-zinc-500">Empresa</Label>
                      <select
                        value={(editingConfig || newConfig).alcance.empresa_id || ''}
                        onChange={(e) => {
                          const updater = editingConfig ? setEditingConfig : setNewConfig;
                          updater(prev => ({
                            ...prev,
                            alcance: { ...prev.alcance, empresa_id: e.target.value || null }
                          }));
                        }}
                        className="w-full h-10 px-3 border rounded-md text-sm"
                        data-testid="config-empresa"
                      >
                        <option value="">Seleccionar...</option>
                        {empresas.map(emp => (
                          <option key={emp} value={emp}>{emp}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  
                  {/* Sucursal (si aplica) */}
                  {(editingConfig || newConfig).alcance.tipo === 'SUCURSAL' && (
                    <div>
                      <Label className="text-xs text-zinc-500">Sucursal</Label>
                      <select
                        value={(editingConfig || newConfig).alcance.sucursal_id || ''}
                        onChange={(e) => {
                          const updater = editingConfig ? setEditingConfig : setNewConfig;
                          updater(prev => ({
                            ...prev,
                            alcance: { ...prev.alcance, sucursal_id: e.target.value || null }
                          }));
                        }}
                        className="w-full h-10 px-3 border rounded-md text-sm"
                        data-testid="config-sucursal"
                      >
                        <option value="">Seleccionar...</option>
                        {sucursales.map(suc => (
                          <option key={suc.id || suc.name} value={suc.id || suc.name}>
                            {suc.name || suc.nombre}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
                
                <div className="grid grid-cols-4 gap-4">
                  {/* Porcentaje */}
                  <div>
                    <Label className="text-xs text-zinc-500">% Descuento</Label>
                    <div className="relative">
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        max="100"
                        value={((editingConfig || newConfig).parametros.porcentaje_comision * 100).toFixed(2)}
                        onChange={(e) => {
                          const pct = parseFloat(e.target.value) / 100;
                          const updater = editingConfig ? setEditingConfig : setNewConfig;
                          updater(prev => ({
                            ...prev,
                            parametros: { ...prev.parametros, porcentaje_comision: pct }
                          }));
                        }}
                        className="pr-8"
                        data-testid="config-porcentaje"
                      />
                      <span className="absolute right-3 top-2.5 text-zinc-400">%</span>
                    </div>
                  </div>
                  
                  {/* Tolerancia */}
                  <div>
                    <Label className="text-xs text-zinc-500">Tolerancia Descuadre ($)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={(editingConfig || newConfig).parametros.tolerancia_descuadre}
                      onChange={(e) => {
                        const updater = editingConfig ? setEditingConfig : setNewConfig;
                        updater(prev => ({
                          ...prev,
                          parametros: { ...prev.parametros, tolerancia_descuadre: parseFloat(e.target.value) }
                        }));
                      }}
                      data-testid="config-tolerancia"
                    />
                  </div>
                  
                  {/* Vigencia inicio */}
                  <div>
                    <Label className="text-xs text-zinc-500">Vigencia Desde</Label>
                    <Input
                      type="date"
                      value={(editingConfig || newConfig).vigencia.fecha_inicio?.split('T')[0] || ''}
                      onChange={(e) => {
                        const updater = editingConfig ? setEditingConfig : setNewConfig;
                        updater(prev => ({
                          ...prev,
                          vigencia: { ...prev.vigencia, fecha_inicio: e.target.value }
                        }));
                      }}
                      data-testid="config-vigencia-inicio"
                    />
                  </div>
                  
                  {/* Vigencia fin (opcional) */}
                  <div>
                    <Label className="text-xs text-zinc-500">Vigencia Hasta (opcional)</Label>
                    <Input
                      type="date"
                      value={(editingConfig || newConfig).vigencia.fecha_fin?.split('T')[0] || ''}
                      onChange={(e) => {
                        const updater = editingConfig ? setEditingConfig : setNewConfig;
                        updater(prev => ({
                          ...prev,
                          vigencia: { ...prev.vigencia, fecha_fin: e.target.value || null }
                        }));
                      }}
                      data-testid="config-vigencia-fin"
                    />
                  </div>
                </div>
                
                {/* Motivo del cambio */}
                <div>
                  <Label className="text-xs text-zinc-500">Motivo del Cambio</Label>
                  <Input
                    type="text"
                    placeholder="Ej: Ajuste por devaluación, nuevo acuerdo con personal..."
                    value={(editingConfig || newConfig).motivo_cambio || ''}
                    onChange={(e) => {
                      const updater = editingConfig ? setEditingConfig : setNewConfig;
                      updater(prev => ({ ...prev, motivo_cambio: e.target.value }));
                    }}
                    data-testid="config-motivo"
                  />
                </div>
                
                {/* Activo */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="config-activa"
                    checked={(editingConfig || newConfig).vigencia.activa}
                    onChange={(e) => {
                      const updater = editingConfig ? setEditingConfig : setNewConfig;
                      updater(prev => ({
                        ...prev,
                        vigencia: { ...prev.vigencia, activa: e.target.checked }
                      }));
                    }}
                    className="w-4 h-4"
                    data-testid="config-activa"
                  />
                  <Label htmlFor="config-activa" className="text-sm">Configuración Activa</Label>
                </div>
                
                {/* Botones */}
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowNewConfig(false);
                      setEditingConfig(null);
                    }}
                    data-testid="btn-cancelar-config"
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancelar
                  </Button>
                  <Button
                    onClick={() => guardarConfig(editingConfig || newConfig, !editingConfig)}
                    disabled={savingConfig}
                    data-testid="btn-guardar-config"
                  >
                    {savingConfig ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Guardar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Listado de configuraciones */}
          <Card>
            <CardHeader className="bg-zinc-800 text-white py-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  Configuraciones de % Descuento
                </CardTitle>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={cargarConfigs}
                  className="text-white hover:bg-zinc-700"
                  data-testid="btn-refrescar-configs"
                >
                  <RefreshCw className={`h-4 w-4 ${loadingConfigs ? 'animate-spin' : ''}`} />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {loadingConfigs ? (
                <div className="p-8 text-center text-zinc-500">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
                  Cargando...
                </div>
              ) : configs.length === 0 ? (
                <div className="p-8 text-center text-zinc-500">
                  <Settings className="h-8 w-8 mx-auto mb-2" />
                  No hay configuraciones. Se usará el 2% por defecto.
                </div>
              ) : (
                <div className="divide-y">
                  {configs.map((config, idx) => (
                    <div 
                      key={config.id || idx} 
                      className={`p-4 ${config.vigencia?.activa ? 'bg-white' : 'bg-zinc-50'}`}
                      data-testid={`config-item-${config.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          {/* Icono según alcance */}
                          <div className={`p-2 rounded-full ${
                            config.alcance?.tipo === 'SUCURSAL' ? 'bg-blue-100 text-blue-600' :
                            config.alcance?.tipo === 'EMPRESA' ? 'bg-amber-100 text-amber-600' :
                            'bg-zinc-100 text-zinc-600'
                          }`}>
                            {config.alcance?.tipo === 'SUCURSAL' ? <Store className="h-5 w-5" /> :
                             config.alcance?.tipo === 'EMPRESA' ? <Building className="h-5 w-5" /> :
                             <Percent className="h-5 w-5" />}
                          </div>
                          
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                {config.alcance?.tipo === 'SUCURSAL' 
                                  ? config.alcance.sucursal_id || 'Sucursal'
                                  : config.alcance?.tipo === 'EMPRESA'
                                  ? config.alcance.empresa_id || 'Empresa'
                                  : 'GLOBAL'}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-xs ${
                                config.vigencia?.activa 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-zinc-200 text-zinc-600'
                              }`}>
                                {config.vigencia?.activa ? 'Activa' : 'Inactiva'}
                              </span>
                            </div>
                            <p className="text-sm text-zinc-500">
                              Desde: {formatDate(config.vigencia?.fecha_inicio)}
                              {config.vigencia?.fecha_fin && ` hasta ${formatDate(config.vigencia.fecha_fin)}`}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-6">
                          {/* Porcentaje destacado */}
                          <div className="text-right">
                            <p className="text-2xl font-bold text-blue-600">
                              {formatPercent(config.parametros?.porcentaje_comision)}
                            </p>
                            <p className="text-xs text-zinc-500">Descuento</p>
                          </div>
                          
                          {/* Tolerancia */}
                          <div className="text-right">
                            <p className="text-lg font-medium text-zinc-700">
                              {formatCurrency(config.parametros?.tolerancia_descuadre)}
                            </p>
                            <p className="text-xs text-zinc-500">Tolerancia</p>
                          </div>
                          
                          {/* Botón editar (solo admin) */}
                          {isAdmin && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingConfig(config)}
                              data-testid={`btn-editar-config-${config.id}`}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                      
                      {/* Motivo del cambio si existe */}
                      {config.motivo_cambio && (
                        <p className="mt-2 text-xs text-zinc-500 italic">
                          {config.motivo_cambio}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
          
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
