/**
 * Componente Tesorería - Cuadre de Cortes Z
 * 
 * Funcionalidades:
 * 1. Dashboard de Cortes Z pendientes de cuadrar
 * 2. Conteo de efectivo (billetes y monedas)
 * 3. Carga y validación de fichas de depósito
 * 4. Validación de fechas (día hábil siguiente)
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { 
  Building2, Calendar, DollarSign, CheckCircle2, AlertCircle, 
  Clock, Upload, RefreshCw, ChevronRight, ChevronDown, FileText,
  Banknote, Coins, Search, Filter, Eye, Edit2, X, Check
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Componente para el conteo de efectivo
const ConteoEfectivo = ({ conteo, onChange, readOnly = false }) => {
  const billetes = conteo?.billetes || {};
  const monedas = conteo?.monedas || {};
  
  const calcularTotal = () => {
    return (
      (billetes.b1000 || 0) * 1000 +
      (billetes.b500 || 0) * 500 +
      (billetes.b200 || 0) * 200 +
      (billetes.b100 || 0) * 100 +
      (billetes.b50 || 0) * 50 +
      (billetes.b20 || 0) * 20 +
      (monedas.m20 || 0) * 20 +
      (monedas.m10 || 0) * 10 +
      (monedas.m5 || 0) * 5 +
      (monedas.m2 || 0) * 2 +
      (monedas.m1 || 0) * 1 +
      (monedas.m050 || 0) * 0.50
    );
  };
  
  const handleBilleteChange = (key, value) => {
    const newBilletes = { ...billetes, [key]: parseInt(value) || 0 };
    onChange({ billetes: newBilletes, monedas });
  };
  
  const handleMonedaChange = (key, value) => {
    const newMonedas = { ...monedas, [key]: parseInt(value) || 0 };
    onChange({ billetes, monedas: newMonedas });
  };
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount);
  };
  
  return (
    <div className="space-y-4">
      {/* Billetes */}
      <div>
        <h4 className="text-sm font-medium text-zinc-700 mb-2 flex items-center gap-2">
          <Banknote className="h-4 w-4" />
          Billetes
        </h4>
        <div className="grid grid-cols-3 gap-2">
          {[
            { key: 'b1000', label: '$1,000', value: 1000, color: 'bg-purple-100 border-purple-300' },
            { key: 'b500', label: '$500', value: 500, color: 'bg-blue-100 border-blue-300' },
            { key: 'b200', label: '$200', value: 200, color: 'bg-green-100 border-green-300' },
            { key: 'b100', label: '$100', value: 100, color: 'bg-red-100 border-red-300' },
            { key: 'b50', label: '$50', value: 50, color: 'bg-pink-100 border-pink-300' },
            { key: 'b20', label: '$20', value: 20, color: 'bg-cyan-100 border-cyan-300' }
          ].map(b => (
            <div key={b.key} className={`p-2 rounded border ${b.color}`}>
              <label className="text-xs font-medium text-zinc-600">{b.label}</label>
              <div className="flex items-center gap-1 mt-1">
                <Input
                  type="number"
                  min="0"
                  value={billetes[b.key] || ''}
                  onChange={(e) => handleBilleteChange(b.key, e.target.value)}
                  disabled={readOnly}
                  className="h-8 text-sm"
                  placeholder="0"
                />
                <span className="text-xs text-zinc-500 whitespace-nowrap">
                  = {formatCurrency((billetes[b.key] || 0) * b.value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Monedas */}
      <div>
        <h4 className="text-sm font-medium text-zinc-700 mb-2 flex items-center gap-2">
          <Coins className="h-4 w-4" />
          Monedas
        </h4>
        <div className="grid grid-cols-3 gap-2">
          {[
            { key: 'm20', label: '$20', value: 20 },
            { key: 'm10', label: '$10', value: 10 },
            { key: 'm5', label: '$5', value: 5 },
            { key: 'm2', label: '$2', value: 2 },
            { key: 'm1', label: '$1', value: 1 },
            { key: 'm050', label: '$0.50', value: 0.50 }
          ].map(m => (
            <div key={m.key} className="p-2 rounded border bg-amber-50 border-amber-200">
              <label className="text-xs font-medium text-zinc-600">{m.label}</label>
              <div className="flex items-center gap-1 mt-1">
                <Input
                  type="number"
                  min="0"
                  value={monedas[m.key] || ''}
                  onChange={(e) => handleMonedaChange(m.key, e.target.value)}
                  disabled={readOnly}
                  className="h-8 text-sm"
                  placeholder="0"
                />
                <span className="text-xs text-zinc-500 whitespace-nowrap">
                  = {formatCurrency((monedas[m.key] || 0) * m.value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Total */}
      <div className="bg-zinc-800 text-white rounded-lg p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm">TOTAL CONTADO:</span>
          <span className="text-2xl font-bold">{formatCurrency(calcularTotal())}</span>
        </div>
      </div>
    </div>
  );
};

// Componente principal de Tesorería
const TesoreriaCorteZ = () => {
  const [loading, setLoading] = useState(false);
  const [cortesZ, setCortesZ] = useState([]);
  const [cuadres, setCuadres] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [selectedCorte, setSelectedCorte] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [conteoEfectivo, setConteoEfectivo] = useState({ billetes: {}, monedas: {} });
  const [fichaDeposito, setFichaDeposito] = useState({});
  const [filtros, setFiltros] = useState({
    fechaInicio: '',
    fechaFin: '',
    sucursal: '',
    estado: ''
  });
  const [vistaActiva, setVistaActiva] = useState('pendientes'); // 'pendientes', 'cuadrados', 'todos'
  
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount || 0);
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('es-MX', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };
  
  const getToken = () => localStorage.getItem('token');
  
  // Cargar Cortes Z disponibles
  const loadCortesZ = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filtros.fechaInicio) params.append('fecha_inicio', filtros.fechaInicio);
      if (filtros.fechaFin) params.append('fecha_fin', filtros.fechaFin);
      if (filtros.sucursal) params.append('sucursal', filtros.sucursal);
      
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cortes-z?${params}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCortesZ(data.cortes || []);
      }
    } catch (error) {
      console.error('Error cargando cortes Z:', error);
    } finally {
      setLoading(false);
    }
  }, [filtros]);
  
  // Cargar cuadres registrados
  const loadCuadres = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filtros.estado) params.append('estado', filtros.estado);
      if (filtros.fechaInicio) params.append('fecha_inicio', filtros.fechaInicio);
      if (filtros.fechaFin) params.append('fecha_fin', filtros.fechaFin);
      
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cuadres?${params}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCuadres(data.cuadres || []);
      }
    } catch (error) {
      console.error('Error cargando cuadres:', error);
    }
  }, [filtros]);
  
  // Cargar resumen
  const loadResumen = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cuadres/resumen`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setResumen(data.resumen);
      }
    } catch (error) {
      console.error('Error cargando resumen:', error);
    }
  }, []);
  
  useEffect(() => {
    loadCortesZ();
    loadCuadres();
    loadResumen();
  }, [loadCortesZ, loadCuadres, loadResumen]);
  
  // Abrir modal de cuadre
  const handleIniciarCuadre = (corte) => {
    setSelectedCorte(corte);
    setConteoEfectivo({ billetes: {}, monedas: {} });
    setFichaDeposito({});
    setModalOpen(true);
  };
  
  // Guardar cuadre
  const handleGuardarCuadre = async () => {
    if (!selectedCorte) return;
    
    setLoading(true);
    try {
      const cuadreData = {
        corte_z: selectedCorte,
        conteo_efectivo: conteoEfectivo,
        ficha_deposito: fichaDeposito,
        observaciones: ''
      };
      
      const response = await fetch(`${API_URL}/api/finanzas/tesoreria/cuadres`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cuadreData)
      });
      
      if (response.ok) {
        setModalOpen(false);
        loadCortesZ();
        loadCuadres();
        loadResumen();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error al guardar cuadre');
      }
    } catch (error) {
      console.error('Error guardando cuadre:', error);
      alert('Error al guardar cuadre');
    } finally {
      setLoading(false);
    }
  };
  
  // Renderizar tarjetas de resumen
  const renderResumen = () => (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <Card className="border-l-4 border-l-yellow-500">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-zinc-500">Pendientes</p>
              <p className="text-2xl font-bold text-yellow-600">{resumen?.PENDIENTE?.count || 0}</p>
              <p className="text-xs text-zinc-400">{formatCurrency(resumen?.PENDIENTE?.total_esperado)}</p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </CardContent>
      </Card>
      
      <Card className="border-l-4 border-l-blue-500">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-zinc-500">En Proceso</p>
              <p className="text-2xl font-bold text-blue-600">{resumen?.EN_PROCESO?.count || 0}</p>
              <p className="text-xs text-zinc-400">{formatCurrency(resumen?.EN_PROCESO?.total_esperado)}</p>
            </div>
            <RefreshCw className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>
      
      <Card className="border-l-4 border-l-green-500">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-zinc-500">Cuadrados</p>
              <p className="text-2xl font-bold text-green-600">{resumen?.CUADRADO?.count || 0}</p>
              <p className="text-xs text-zinc-400">{formatCurrency(resumen?.CUADRADO?.total_depositado)}</p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>
      
      <Card className="border-l-4 border-l-red-500">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-zinc-500">Descuadre</p>
              <p className="text-2xl font-bold text-red-600">{resumen?.DESCUADRE?.count || 0}</p>
              <p className="text-xs text-zinc-400">{formatCurrency(resumen?.DESCUADRE?.total_diferencia)}</p>
            </div>
            <AlertCircle className="h-8 w-8 text-red-500" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
  
  // Renderizar lista de cortes pendientes
  const renderCortesPendientes = () => (
    <div className="space-y-2">
      {cortesZ.filter(c => !c.tiene_cuadre).length === 0 ? (
        <Card className="border-2 border-dashed">
          <CardContent className="py-8 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-300 mx-auto mb-3" />
            <p className="text-zinc-500">No hay cortes pendientes de cuadrar</p>
          </CardContent>
        </Card>
      ) : (
        cortesZ.filter(c => !c.tiene_cuadre).map(corte => (
          <Card key={`${corte.sucursal_id}_${corte.folio_corte}`} className="hover:shadow-md transition">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg ${
                    corte.fuente === 'SOFTRESTAURANT' ? 'bg-emerald-100' : 'bg-indigo-100'
                  }`}>
                    <Building2 className={`h-5 w-5 ${
                      corte.fuente === 'SOFTRESTAURANT' ? 'text-emerald-600' : 'text-indigo-600'
                    }`} />
                  </div>
                  <div>
                    <p className="font-medium">{corte.sucursal_nombre}</p>
                    <p className="text-xs text-zinc-500">Folio: {corte.folio_corte}</p>
                  </div>
                  <div className="text-center px-4 border-l">
                    <p className="text-xs text-zinc-500">Fecha Corte</p>
                    <p className="font-medium">{formatDate(corte.fecha_corte)}</p>
                  </div>
                  <div className="text-center px-4 border-l">
                    <p className="text-xs text-zinc-500">Efectivo Ventas</p>
                    <p className="font-medium text-green-600">{formatCurrency(corte.efectivo_ventas)}</p>
                  </div>
                  <div className="text-center px-4 border-l">
                    <p className="text-xs text-zinc-500">Propinas Pagadas</p>
                    <p className="font-medium text-orange-600">{formatCurrency(corte.propinas_pagadas)}</p>
                  </div>
                  <div className="text-center px-4 border-l bg-zinc-100 rounded p-2">
                    <p className="text-xs text-zinc-500">A Depositar</p>
                    <p className="font-bold text-lg">{formatCurrency(corte.monto_a_depositar)}</p>
                  </div>
                  <div className="text-center px-4 border-l">
                    <p className="text-xs text-zinc-500">Depósito Esperado</p>
                    <p className="font-medium text-blue-600">{formatDate(corte.fecha_deposito_esperada)}</p>
                  </div>
                </div>
                <Button 
                  onClick={() => handleIniciarCuadre(corte)}
                  className="bg-amber-500 hover:bg-amber-600"
                >
                  Cuadrar
                </Button>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
  
  // Renderizar lista de cuadres
  const renderCuadresRegistrados = () => (
    <div className="space-y-2">
      {cuadres.length === 0 ? (
        <Card className="border-2 border-dashed">
          <CardContent className="py-8 text-center">
            <FileText className="h-12 w-12 text-zinc-300 mx-auto mb-3" />
            <p className="text-zinc-500">No hay cuadres registrados</p>
          </CardContent>
        </Card>
      ) : (
        cuadres.map(cuadre => (
          <Card key={cuadre.id} className={`border-l-4 ${
            cuadre.estado === 'CUADRADO' ? 'border-l-green-500' :
            cuadre.estado === 'DESCUADRE' ? 'border-l-red-500' :
            cuadre.estado === 'EN_PROCESO' ? 'border-l-blue-500' :
            'border-l-yellow-500'
          }`}>
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
        ))
      )}
    </div>
  );
  
  // Modal de cuadre
  const renderModal = () => {
    if (!modalOpen || !selectedCorte) return null;
    
    const calcularTotalContado = () => {
      const b = conteoEfectivo.billetes || {};
      const m = conteoEfectivo.monedas || {};
      return (
        (b.b1000 || 0) * 1000 + (b.b500 || 0) * 500 + (b.b200 || 0) * 200 +
        (b.b100 || 0) * 100 + (b.b50 || 0) * 50 + (b.b20 || 0) * 20 +
        (m.m20 || 0) * 20 + (m.m10 || 0) * 10 + (m.m5 || 0) * 5 +
        (m.m2 || 0) * 2 + (m.m1 || 0) * 1 + (m.m050 || 0) * 0.50
      );
    };
    
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
              <div>
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  Ficha de Depósito Bancario
                </h3>
                <div className="space-y-3">
                  <div className="border-2 border-dashed rounded-lg p-6 text-center">
                    <Upload className="h-8 w-8 text-zinc-400 mx-auto mb-2" />
                    <p className="text-sm text-zinc-500">Arrastra o haz clic para subir la ficha</p>
                    <input type="file" className="hidden" accept="image/*,.pdf" />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-zinc-500">Fecha Depósito</label>
                      <Input
                        type="date"
                        value={fichaDeposito.fecha_deposito || ''}
                        onChange={(e) => setFichaDeposito({...fichaDeposito, fecha_deposito: e.target.value})}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-zinc-500">Banco</label>
                      <Input
                        value={fichaDeposito.banco || ''}
                        onChange={(e) => setFichaDeposito({...fichaDeposito, banco: e.target.value})}
                        placeholder="BBVA, Santander..."
                      />
                    </div>
                    <div>
                      <label className="text-xs text-zinc-500">Referencia</label>
                      <Input
                        value={fichaDeposito.referencia || ''}
                        onChange={(e) => setFichaDeposito({...fichaDeposito, referencia: e.target.value})}
                        placeholder="Número de referencia"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-zinc-500">Cuenta</label>
                      <Input
                        value={fichaDeposito.cuenta || ''}
                        onChange={(e) => setFichaDeposito({...fichaDeposito, cuenta: e.target.value})}
                        placeholder="Número de cuenta"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="text-xs text-zinc-500">Importe Depositado</label>
                      <Input
                        type="number"
                        step="0.01"
                        value={fichaDeposito.importe || ''}
                        onChange={(e) => setFichaDeposito({...fichaDeposito, importe: parseFloat(e.target.value) || 0})}
                        placeholder="0.00"
                        className="text-lg font-bold"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Comparativa */}
            <Card className="bg-zinc-800 text-white">
              <CardContent className="p-4">
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div>
                    <p className="text-xs text-zinc-400">Esperado (Corte Z)</p>
                    <p className="text-xl font-bold">{formatCurrency(selectedCorte.monto_a_depositar)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-400">Contado</p>
                    <p className="text-xl font-bold text-cyan-400">{formatCurrency(calcularTotalContado())}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-400">Depositado</p>
                    <p className="text-xl font-bold text-green-400">{formatCurrency(fichaDeposito.importe || 0)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-zinc-400">Diferencia</p>
                    <p className={`text-xl font-bold ${
                      Math.abs((fichaDeposito.importe || 0) - selectedCorte.monto_a_depositar) <= 1 
                        ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {formatCurrency((fichaDeposito.importe || 0) - selectedCorte.monto_a_depositar)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
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
        <Button onClick={() => { loadCortesZ(); loadCuadres(); loadResumen(); }} variant="outline">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>
      
      {/* Resumen */}
      {resumen && renderResumen()}
      
      {/* Filtros */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-zinc-400" />
              <span className="text-sm font-medium">Filtros:</span>
            </div>
            <Input
              type="date"
              value={filtros.fechaInicio}
              onChange={(e) => setFiltros({...filtros, fechaInicio: e.target.value})}
              className="w-40"
              placeholder="Desde"
            />
            <Input
              type="date"
              value={filtros.fechaFin}
              onChange={(e) => setFiltros({...filtros, fechaFin: e.target.value})}
              className="w-40"
              placeholder="Hasta"
            />
            <select
              value={filtros.sucursal}
              onChange={(e) => setFiltros({...filtros, sucursal: e.target.value})}
              className="border rounded px-3 py-2 text-sm"
            >
              <option value="">Todas las sucursales</option>
              <option value="CIENFUEGOS">Cienfuegos</option>
              <option value="LA_ESTELAR">La Estelar</option>
              <option value="130_MERIDA">130° Mérida</option>
              <option value="MPRO_ORIGEN">MPRO Origen</option>
              <option value="MPRO_QUERETARO">MPRO Querétaro</option>
            </select>
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
