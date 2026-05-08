import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Building2, RefreshCw, DollarSign, CreditCard, Clock,
  CheckCircle2, FileSpreadsheet, Upload
} from 'lucide-react';

/**
 * FinanzasControlIngresos
 * 
 * Componente presentacional para el control de ingresos: cortes de caja,
 * saldos pendientes, comisiones y conciliación bancaria.
 * 
 * ACTUALIZADO: Filtro de sucursal reemplazado por Unidad de Negocio.
 * 
 * @param {Object} props
 * @param {Object} props.cortesData - Datos de cortes de caja
 * @param {Object} props.saldosPendientes - Saldos por depositar
 * @param {Object} props.resumenComisiones - Resumen de comisiones
 * @param {Object} props.configComisiones - Configuración de comisiones
 * @param {Array} props.unidadesNegocio - Unidades de negocio disponibles (filtradas por permisos)
 * @param {string} props.selectedUnidad - Unidad de negocio seleccionada
 * @param {boolean} props.loadingUnidades - Estado de carga de unidades
 * @param {string} props.ingresosSubTab - Tab activo dentro de control de ingresos
 * @param {string} props.ingresosFechaInicio - Fecha inicio filtro
 * @param {string} props.ingresosFechaFin - Fecha fin filtro
 * @param {boolean} props.ingresosSoloPendientes - Filtro solo pendientes
 * @param {boolean} props.loading - Estado de carga
 * @param {Function} props.onSubTabChange - Callback cambio de sub-tab
 * @param {Function} props.onFechaInicioChange - Callback cambio fecha inicio
 * @param {Function} props.onFechaFinChange - Callback cambio fecha fin
 * @param {Function} props.onUnidadChange - Callback cambio unidad
 * @param {Function} props.onSoloPendientesChange - Callback cambio checkbox pendientes
 * @param {Function} props.onFiltrar - Callback botón filtrar
 * @param {Function} props.onDepositoEfectivo - Callback marcar depósito efectivo
 * @param {Function} props.onDepositoTarjetas - Callback marcar depósito tarjetas
 * @param {Function} props.formatCurrency - Función para formatear moneda
 */
export default function FinanzasControlIngresos({
  cortesData,
  saldosPendientes,
  resumenComisiones,
  configComisiones,
  unidadesNegocio,
  selectedUnidad,
  loadingUnidades,
  ingresosSubTab,
  ingresosFechaInicio,
  ingresosFechaFin,
  ingresosSoloPendientes,
  loading,
  onSubTabChange,
  onFechaInicioChange,
  onFechaFinChange,
  onUnidadChange,
  onSoloPendientesChange,
  onFiltrar,
  onDepositoEfectivo,
  onDepositoTarjetas,
  formatCurrency
}) {
  const resumen = cortesData?.resumen || {};
  const saldos = saldosPendientes || {};
  const comisiones = configComisiones?.comisiones || {};

  return (
    <div className="space-y-4" data-testid="control-ingresos-container">
      {/* Sub-tabs */}
      <div className="flex gap-2 border-b pb-2" data-testid="ingresos-subtabs">
        {['cortes', 'pendientes', 'comisiones', 'conciliacion'].map(tab => (
          <button
            key={tab}
            onClick={() => onSubTabChange(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              ingresosSubTab === tab ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
            }`}
            data-testid={`ingresos-tab-${tab}`}
          >
            {tab === 'cortes' ? 'Cortes de Caja' :
             tab === 'pendientes' ? 'Por Depositar' :
             tab === 'comisiones' ? 'Comisiones' : 'Conciliación'}
          </button>
        ))}
      </div>
      
      {/* Filtros generales */}
      <Card>
        <CardContent className="p-3">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
            {/* Selector de Unidad de Negocio */}
            <div>
              <Label className="text-xs text-zinc-500">Unidad de Negocio</Label>
              <div className="flex items-center gap-2 mt-1">
                <Building2 className="h-4 w-4 text-zinc-400" />
                {unidadesNegocio.length === 1 ? (
                  <div className="px-3 py-2 border rounded-lg text-sm bg-zinc-50 flex-1">
                    {unidadesNegocio[0].nombre}
                  </div>
                ) : (
                  <select
                    value={selectedUnidad}
                    onChange={(e) => onUnidadChange(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                    disabled={loadingUnidades}
                    data-testid="ingresos-unidad-select"
                  >
                    <option value="">{loadingUnidades ? "Cargando..." : "Todas"}</option>
                    {unidadesNegocio.map(u => (
                      <option key={u.id} value={u.id}>{u.nombre}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Fecha Inicio</Label>
              <Input 
                type="date" 
                value={ingresosFechaInicio} 
                onChange={(e) => onFechaInicioChange(e.target.value)} 
                className="mt-1"
                data-testid="ingresos-fecha-inicio"
              />
            </div>
            <div>
              <Label className="text-xs text-zinc-500">Fecha Fin</Label>
              <Input 
                type="date" 
                value={ingresosFechaFin} 
                onChange={(e) => onFechaFinChange(e.target.value)} 
                className="mt-1"
                data-testid="ingresos-fecha-fin"
              />
            </div>
            <div className="flex items-center">
              <label className="flex items-center gap-2 text-sm">
                <input 
                  type="checkbox" 
                  checked={ingresosSoloPendientes} 
                  onChange={(e) => onSoloPendientesChange(e.target.checked)} 
                  className="rounded"
                  data-testid="ingresos-solo-pendientes"
                />
                Solo pendientes
              </label>
            </div>
            <div>
              <Button onClick={onFiltrar} disabled={loading} className="w-full" data-testid="ingresos-filtrar-btn">
                <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} /> Filtrar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* === TAB: CORTES DE CAJA === */}
      {ingresosSubTab === 'cortes' && (
        <div className="space-y-4" data-testid="tab-cortes">
          {/* Resumen */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Card className="border-l-4 border-l-green-500">
              <CardContent className="p-3">
                <p className="text-xs text-zinc-500">Total Efectivo</p>
                <p className="text-xl font-bold text-green-600">{formatCurrency(resumen.total_efectivo || 0)}</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="p-3">
                <p className="text-xs text-zinc-500">Tarjetas (Bruto)</p>
                <p className="text-xl font-bold text-blue-600">{formatCurrency(resumen.total_tarjetas_bruto || 0)}</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-red-500">
              <CardContent className="p-3">
                <p className="text-xs text-zinc-500">Comisiones</p>
                <p className="text-xl font-bold text-red-600">-{formatCurrency(resumen.total_comisiones || 0)}</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-purple-500">
              <CardContent className="p-3">
                <p className="text-xs text-zinc-500">Neto Tarjetas</p>
                <p className="text-xl font-bold text-purple-600">{formatCurrency(resumen.total_neto_tarjetas || 0)}</p>
              </CardContent>
            </Card>
            <Card className="border-l-4 border-l-zinc-800 bg-zinc-800 text-white">
              <CardContent className="p-3">
                <p className="text-xs text-zinc-300">TOTAL VENTAS</p>
                <p className="text-xl font-bold">{formatCurrency(resumen.total_ventas || 0)}</p>
              </CardContent>
            </Card>
          </div>
          
          {/* Tabla de cortes */}
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto max-h-[500px]">
                <table className="w-full text-xs">
                  <thead className="bg-zinc-800 text-white sticky top-0">
                    <tr>
                      <th className="p-2 text-left">Fecha</th>
                      <th className="p-2 text-left">Sucursal</th>
                      <th className="p-2 text-right">Efectivo</th>
                      <th className="p-2 text-right">Debito</th>
                      <th className="p-2 text-right">Credito</th>
                      <th className="p-2 text-right">AMEX</th>
                      <th className="p-2 text-right">Int'l</th>
                      <th className="p-2 text-right">Comisiones</th>
                      <th className="p-2 text-right">Total</th>
                      <th className="p-2 text-center">Efectivo</th>
                      <th className="p-2 text-center">Tarjetas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(cortesData?.cortes || []).map(corte => (
                      <tr key={corte.corte_id} className={`border-b hover:bg-zinc-50 ${corte.conciliado ? 'bg-green-50' : ''}`}>
                        <td className="p-2">
                          <div>
                            <p className="font-medium">{corte.fecha_corte}</p>
                            <p className="text-zinc-400">{corte.dia_semana}</p>
                          </div>
                        </td>
                        <td className="p-2 font-medium">{corte.sucursal_nombre}</td>
                        <td className="p-2 text-right font-mono text-green-600">{formatCurrency(corte.efectivo)}</td>
                        <td className="p-2 text-right font-mono">{formatCurrency(corte.debito)}</td>
                        <td className="p-2 text-right font-mono">{formatCurrency(corte.credito)}</td>
                        <td className="p-2 text-right font-mono">{corte.amex > 0 ? formatCurrency(corte.amex) : '-'}</td>
                        <td className="p-2 text-right font-mono">{corte.internacional > 0 ? formatCurrency(corte.internacional) : '-'}</td>
                        <td className="p-2 text-right font-mono text-red-500">-{formatCurrency(corte.total_comisiones)}</td>
                        <td className="p-2 text-right font-mono font-bold">{formatCurrency(corte.total_venta)}</td>
                        <td className="p-2 text-center">
                          {corte.efectivo_depositado ? (
                            <span className="text-green-600 flex items-center justify-center gap-1">
                              <CheckCircle2 className="h-4 w-4" />
                              <span className="text-[10px]">{corte.efectivo_referencia_deposito}</span>
                            </span>
                          ) : (
                            <button
                              onClick={() => {
                                const ref = prompt('Referencia del deposito:');
                                if (ref) onDepositoEfectivo(corte.corte_id, ref);
                              }}
                              className="text-yellow-600 hover:text-yellow-800"
                              title={`Depositar ${corte.fecha_deposito_efectivo}`}
                            >
                              <Clock className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                        <td className="p-2 text-center">
                          {corte.tarjetas_depositadas ? (
                            <span className="text-green-600 flex items-center justify-center gap-1">
                              <CheckCircle2 className="h-4 w-4" />
                              <span className="text-[10px]">{corte.tarjetas_referencia_netpay}</span>
                            </span>
                          ) : (
                            <button
                              onClick={() => {
                                const ref = prompt('Referencia NetPay:');
                                if (ref) onDepositoTarjetas(corte.corte_id, ref);
                              }}
                              className="text-yellow-600 hover:text-yellow-800"
                              title={`Depositar ${corte.fecha_deposito_debito}`}
                            >
                              <Clock className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* === TAB: SALDOS PENDIENTES === */}
      {ingresosSubTab === 'pendientes' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="tab-pendientes">
          {/* Efectivo Pendiente */}
          <Card>
            <CardHeader className="py-3 bg-green-50 border-b">
              <CardTitle className="text-base flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-green-600" />
                  Efectivo por Depositar
                </span>
                <span className="text-xl font-bold text-green-600">{formatCurrency(saldos.efectivo?.total_pendiente || 0)}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 max-h-[400px] overflow-y-auto">
              {(saldos.efectivo?.por_fecha || []).map(grupo => (
                <div key={grupo.fecha} className="border-b p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-sm">{grupo.fecha}</span>
                    <span className="font-bold text-green-600">{formatCurrency(grupo.monto)}</span>
                  </div>
                  <div className="space-y-1">
                    {grupo.cortes.map(c => (
                      <div key={c.corte_id} className="flex justify-between text-xs text-zinc-500">
                        <span>{c.sucursal} ({c.fecha_corte})</span>
                        <span>{formatCurrency(c.monto)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {(saldos.efectivo?.por_fecha || []).length === 0 && (
                <div className="p-8 text-center text-zinc-400">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-green-300" />
                  <p>Todo el efectivo esta depositado</p>
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Tarjetas Pendiente */}
          <Card>
            <CardHeader className="py-3 bg-blue-50 border-b">
              <CardTitle className="text-base flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5 text-blue-600" />
                  Tarjetas por Depositar (NetPay)
                </span>
                <span className="text-xl font-bold text-blue-600">{formatCurrency(saldos.tarjetas?.total_pendiente_neto || 0)}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 max-h-[400px] overflow-y-auto">
              {(saldos.tarjetas?.por_fecha || []).map(grupo => (
                <div key={grupo.fecha} className="border-b p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-sm">{grupo.fecha}</span>
                    <div className="text-right">
                      <p className="font-bold text-blue-600">{formatCurrency(grupo.monto_neto)}</p>
                      <p className="text-xs text-zinc-400">Bruto: {formatCurrency(grupo.monto_bruto)} | Com: -{formatCurrency(grupo.comisiones)}</p>
                    </div>
                  </div>
                  <div className="space-y-1">
                    {grupo.cortes.map(c => (
                      <div key={c.corte_id} className="flex justify-between text-xs text-zinc-500">
                        <span>{c.sucursal}</span>
                        <span>D:{formatCurrency(c.debito)} C:{formatCurrency(c.credito)} {c.amex > 0 && `A:${formatCurrency(c.amex)}`}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {(saldos.tarjetas?.por_fecha || []).length === 0 && (
                <div className="p-8 text-center text-zinc-400">
                  <CheckCircle2 className="h-12 w-12 mx-auto mb-2 text-blue-300" />
                  <p>Todas las tarjetas estan depositadas</p>
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Total */}
          <Card className="md:col-span-2 bg-zinc-800 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-lg">TOTAL POR DEPOSITAR</span>
                <span className="text-3xl font-bold">{formatCurrency(saldos.total_por_depositar || 0)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* === TAB: COMISIONES === */}
      {ingresosSubTab === 'comisiones' && (
        <div className="space-y-4" data-testid="tab-comisiones">
          {/* Configuracion de comisiones */}
          <Card>
            <CardHeader className="py-3 border-b">
              <CardTitle className="text-base">Configuracion de Comisiones (NetPay)</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(comisiones).map(([tipo, config]) => (
                  <div key={tipo} className="p-4 border rounded-lg">
                    <h4 className="font-medium mb-2">{config.nombre}</h4>
                    <div className="space-y-1 text-sm">
                      <p>Comision: <span className="font-bold">{config.comision_porcentaje}%</span></p>
                      <p>IVA: <span className="font-bold">{config.iva}%</span></p>
                      <p>Total: <span className="font-bold text-red-600">{config.comision_total_porcentaje}%</span></p>
                      <p>Deposito: <span className="font-bold">{config.dias_deposito} dia(s) habil(es)</span></p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg text-sm">
                <p className="font-medium text-yellow-800 mb-1">Reglas de Deposito:</p>
                <ul className="list-disc list-inside text-yellow-700 space-y-1">
                  <li>Efectivo: dia siguiente (Vie/Sab/Dom - Lunes)</li>
                  <li>Debito/Credito: 24 hrs habiles</li>
                  <li>AMEX/Internacional: 48 hrs habiles</li>
                </ul>
              </div>
            </CardContent>
          </Card>
          
          {/* Resumen de comisiones del periodo */}
          {resumenComisiones && (
            <Card>
              <CardHeader className="py-3 border-b">
                <CardTitle className="text-base">Resumen de Comisiones del Periodo</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead className="bg-zinc-100">
                    <tr>
                      <th className="p-3 text-left">Tipo</th>
                      <th className="p-3 text-right">Ventas</th>
                      <th className="p-3 text-right">Tasa</th>
                      <th className="p-3 text-right">Comisiones</th>
                      <th className="p-3 text-right">Neto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(resumenComisiones.por_tipo || {}).map(([tipo, data]) => (
                      <tr key={tipo} className="border-b">
                        <td className="p-3 font-medium capitalize">{tipo}</td>
                        <td className="p-3 text-right font-mono">{formatCurrency(data.ventas)}</td>
                        <td className="p-3 text-right">{data.tasa}</td>
                        <td className="p-3 text-right font-mono text-red-600">-{formatCurrency(data.comisiones)}</td>
                        <td className="p-3 text-right font-mono font-bold">{formatCurrency(data.neto)}</td>
                      </tr>
                    ))}
                    <tr className="bg-zinc-800 text-white font-bold">
                      <td className="p-3">TOTAL</td>
                      <td className="p-3 text-right font-mono">{formatCurrency(resumenComisiones.totales?.ventas || 0)}</td>
                      <td className="p-3"></td>
                      <td className="p-3 text-right font-mono text-red-300">-{formatCurrency(resumenComisiones.totales?.comisiones || 0)}</td>
                      <td className="p-3 text-right font-mono">{formatCurrency(resumenComisiones.totales?.neto || 0)}</td>
                    </tr>
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}
        </div>
      )}
      
      {/* === TAB: CONCILIACION === */}
      {ingresosSubTab === 'conciliacion' && (
        <Card className="border-2 border-dashed" data-testid="tab-conciliacion">
          <CardContent className="py-12 text-center">
            <FileSpreadsheet className="h-16 w-16 text-zinc-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-zinc-600 mb-2">Conciliacion Bancaria</h3>
            <p className="text-zinc-400 text-sm max-w-md mx-auto mb-4">
              Cargue el estado de cuenta de BBVA u otro banco para conciliar automaticamente los depositos de efectivo y tarjetas.
            </p>
            <Button variant="outline" className="mt-2">
              <Upload className="h-4 w-4 mr-2" />
              Cargar Estado de Cuenta
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
