/**
 * Tabla de listado de propinas por corte
 * SUBFASE 3.5: Actualizado para EDARSAHUB
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DollarSign, RefreshCw, AlertCircle, Database } from 'lucide-react';
import { formatCurrency, formatDate } from './utils';

export default function PropinasTable({ propinas, loading, fuenteDatos }) {
  return (
    <Card>
      <CardHeader className="bg-zinc-800 text-white py-3">
        <CardTitle className="text-base flex items-center justify-between">
          <span className="flex items-center">
            <DollarSign className="h-5 w-5 mr-2" />
            Propinas por Corte ({propinas.length} registros)
          </span>
          {fuenteDatos && fuenteDatos !== 'ERROR' && (
            <span className="text-xs font-normal bg-green-600 px-2 py-1 rounded flex items-center">
              <Database className="h-3 w-3 mr-1" />
              {fuenteDatos}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {loading ? (
          <div className="p-8 text-center text-zinc-500">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
            Cargando...
          </div>
        ) : propinas.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            {fuenteDatos === 'ERROR' 
              ? 'Error al cargar datos. Verifique su sesión.'
              : 'Sin propinas TPV sincronizadas para el rango seleccionado'
            }
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-100">
                <tr>
                  <th className="text-left p-3 font-medium">Unidad</th>
                  <th className="text-center p-3 font-medium">Folio</th>
                  <th className="text-center p-3 font-medium">Fecha</th>
                  <th className="text-right p-3 font-medium">Propinas TPV</th>
                  <th className="text-right p-3 font-medium">Comisión</th>
                  <th className="text-right p-3 font-medium">A Pagar</th>
                  <th className="text-center p-3 font-medium">Sistema</th>
                </tr>
              </thead>
              <tbody>
                {propinas.map((propina, idx) => (
                  <tr key={propina.id || idx} className="border-b hover:bg-zinc-50">
                    <td className="p-3">{propina.sucursal_nombre || propina.server_name}</td>
                    <td className="p-3 text-center font-mono text-xs">{propina.folio_corte}</td>
                    <td className="p-3 text-center">{formatDate(propina.fecha_corte)}</td>
                    <td className="p-3 text-right font-mono">{formatCurrency(propina.origen?.propinas_tpv)}</td>
                    <td className="p-3 text-right font-mono text-amber-600">
                      {formatCurrency(propina.calculo?.comision_calculada)}
                    </td>
                    <td className="p-3 text-right font-mono font-bold text-green-600">
                      {formatCurrency(propina.calculo?.monto_a_pagar_meseros)}
                    </td>
                    <td className="p-3 text-center">
                      <SistemaOrigenBadge sistema={propina.sistema_origen} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SistemaOrigenBadge({ sistema }) {
  const styles = {
    'SoftRestaurant': 'bg-blue-100 text-blue-700',
    'MPRO': 'bg-purple-100 text-purple-700'
  };
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${styles[sistema] || 'bg-zinc-100 text-zinc-700'}`}>
      {sistema || 'N/A'}
    </span>
  );
}
