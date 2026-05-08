/**
 * Componentes UI para Catálogo de Consultas
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Database, Play, Code, Eye, EyeOff, TestTube, 
  Edit, Trash2, BarChart3, ShoppingCart, CreditCard, Package
} from 'lucide-react';

// Iconos por categoría
export const iconosPorCategoria = {
  'Ventas': BarChart3,
  'Compras': ShoppingCart,
  'Pagos': CreditCard,
  'Inventarios': Package,
};

// Lista de consultas
export const ConsultasList = ({ consultas, onSelect, selectedId }) => (
  <div className="space-y-2">
    {consultas.map(consulta => {
      const Icon = iconosPorCategoria[consulta.categoria] || Database;
      const isSelected = selectedId === consulta.id;
      
      return (
        <Card 
          key={consulta.id}
          className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-zinc-50'}`}
          onClick={() => onSelect(consulta)}
        >
          <CardContent className="p-3">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${isSelected ? 'bg-blue-100' : 'bg-zinc-100'}`}>
                <Icon className={`h-4 w-4 ${isSelected ? 'text-blue-600' : 'text-zinc-500'}`} />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">{consulta.nombre}</h4>
                <p className="text-xs text-zinc-500 truncate">{consulta.descripcion}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-xs">{consulta.categoria}</Badge>
                  <Badge variant="outline" className="text-xs">{consulta.sistema}</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    })}
  </div>
);

// Tabla de resultados
export const ResultadosTable = ({ resultados, maxRows = 100 }) => {
  if (!resultados || !resultados.columnas || !resultados.datos) {
    return null;
  }

  const datos = resultados.datos.slice(0, maxRows);
  
  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-100">
            <tr>
              {resultados.columnas.map((col) => (
                <th key={`col-${col}`} className="px-3 py-2 text-left font-medium text-zinc-700">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {datos.map((row, rowIdx) => (
              <tr key={`row-${rowIdx}`} className="border-t hover:bg-zinc-50">
                {resultados.columnas.map((col) => (
                  <td key={`cell-${rowIdx}-${col}`} className="px-3 py-2 text-zinc-600">
                    {formatCellValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {resultados.datos.length > maxRows && (
        <div className="px-3 py-2 bg-zinc-50 text-xs text-zinc-500 text-center">
          Mostrando {maxRows} de {resultados.datos.length} filas
        </div>
      )}
    </div>
  );
};

// Helper para formatear valores de celda
const formatCellValue = (value) => {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? 'Sí' : 'No';
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return value.toLocaleString('es-MX');
    return value.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
    return new Date(value).toLocaleDateString('es-MX');
  }
  return String(value);
};

// Visor de SQL
export const SQLViewer = ({ sql, editable = false, onChange, onSave, saving }) => (
  <Card className="bg-zinc-900">
    <CardHeader className="py-2 px-3 border-b border-zinc-700">
      <div className="flex items-center justify-between">
        <CardTitle className="text-sm text-zinc-300 flex items-center gap-2">
          <Code className="h-4 w-4" />
          SQL Query
        </CardTitle>
        {editable && onSave && (
          <Button size="sm" variant="outline" onClick={onSave} disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar Cambios'}
          </Button>
        )}
      </div>
    </CardHeader>
    <CardContent className="p-0">
      {editable ? (
        <textarea
          className="w-full h-48 p-3 bg-zinc-900 text-green-400 font-mono text-xs resize-none focus:outline-none"
          value={sql}
          onChange={(e) => onChange?.(e.target.value)}
          spellCheck={false}
        />
      ) : (
        <pre className="p-3 text-green-400 font-mono text-xs overflow-x-auto whitespace-pre-wrap">
          {sql}
        </pre>
      )}
    </CardContent>
  </Card>
);

// Panel de parámetros
export const ParametrosPanel = ({ parametros, valores, onChange }) => {
  if (!parametros || parametros.length === 0) return null;
  
  return (
    <div className="grid grid-cols-2 gap-3">
      {parametros.map(param => (
        <div key={param.nombre}>
          <label className="text-xs text-zinc-500 mb-1 block">
            {param.label || param.nombre}
            {param.requerido && <span className="text-red-500">*</span>}
          </label>
          <input
            type={param.tipo === 'fecha' ? 'date' : param.tipo === 'numero' ? 'number' : 'text'}
            className="w-full px-3 py-1.5 border rounded text-sm"
            value={valores[param.nombre] || ''}
            onChange={(e) => onChange(param.nombre, e.target.value)}
            placeholder={param.placeholder}
          />
        </div>
      ))}
    </div>
  );
};

// Estado vacío
export const EmptyState = ({ message = 'Selecciona una consulta para ver los resultados' }) => (
  <div className="py-12 text-center text-zinc-400">
    <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
    <p>{message}</p>
  </div>
);
