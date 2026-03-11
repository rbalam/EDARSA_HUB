import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Loader2, 
  Play, 
  Save,
  ChevronRight,
  ChevronLeft,
  Database,
  ShoppingCart,
  ArrowLeftRight,
  Info
} from 'lucide-react';
import { toast } from 'sonner';

const QUERY_TYPES = [
  {
    key: 'inventario',
    title: 'Inventarios',
    icon: Database,
    description: 'Consulta para obtener el inventario inicial y final del período',
    placeholder: `-- Ejemplo para SoftRestaurant:
SELECT 
    idinsumo as codigo,
    descripcion,
    existencia as cantidad
FROM insumos
WHERE idalmacen = @almacen

-- Ejemplo para MPRO:
SELECT 
    Pr_Cve_Producto as codigo,
    Pr_Descripcion as descripcion,
    Fd_Cantidad as cantidad
FROM FisicoDetalle
WHERE Fi_Folio = @folio`
  },
  {
    key: 'ventas',
    title: 'Ventas',
    icon: ShoppingCart,
    description: 'Consulta para obtener las ventas del período de análisis',
    placeholder: `-- Ejemplo para SoftRestaurant:
SELECT 
    idproducto as codigo,
    SUM(cantidad) as cantidad
FROM ventasdetalle v
WHERE fecha BETWEEN @fecha_ini AND @fecha_fin
GROUP BY idproducto

-- Ejemplo para MPRO:
SELECT 
    Pr_Cve_Producto as codigo,
    SUM(Vd_Cantidad) as cantidad
FROM VentaDetalle
WHERE Vd_Fecha BETWEEN @fecha_ini AND @fecha_fin
GROUP BY Pr_Cve_Producto`
  },
  {
    key: 'movimientos',
    title: 'Movimientos / Entradas',
    icon: ArrowLeftRight,
    description: 'Consulta para obtener entradas, traspasos y ajustes del período',
    placeholder: `-- Ejemplo para SoftRestaurant:
SELECT 
    idinsumo as codigo,
    SUM(cantidad) as cantidad,
    idconcepto as tipo_movimiento
FROM movimientos
WHERE fecha BETWEEN @fecha_ini AND @fecha_fin
GROUP BY idinsumo, idconcepto

-- Ejemplo para MPRO:
SELECT 
    Pr_Cve_Producto as codigo,
    SUM(Md_Cantidad) as cantidad,
    Tm_Cve_TipoMov as tipo_movimiento
FROM MovDetalle
WHERE Md_Fecha BETWEEN @fecha_ini AND @fecha_fin
GROUP BY Pr_Cve_Producto, Tm_Cve_TipoMov`
  }
];

const QueryConfigWizard = ({ open, onClose, server, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [queries, setQueries] = useState({
    inventario: { sql: '', validated: false, validating: false, result: null },
    ventas: { sql: '', validated: false, validating: false, result: null },
    movimientos: { sql: '', validated: false, validating: false, result: null }
  });
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  // Cargar consultas existentes al abrir
  useEffect(() => {
    if (open && server?.id) {
      loadExistingQueries();
    }
  }, [open, server?.id]);

  const loadExistingQueries = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/servers/${server.id}/queries`);
      const serverQueries = response.data.queries;
      
      setQueries({
        inventario: {
          sql: serverQueries.inventario?.sql || '',
          validated: serverQueries.inventario?.validated || false,
          validating: false,
          result: serverQueries.inventario?.validated ? { valid: true, message: 'Consulta validada anteriormente' } : null
        },
        ventas: {
          sql: serverQueries.ventas?.sql || '',
          validated: serverQueries.ventas?.validated || false,
          validating: false,
          result: serverQueries.ventas?.validated ? { valid: true, message: 'Consulta validada anteriormente' } : null
        },
        movimientos: {
          sql: serverQueries.movimientos?.sql || '',
          validated: serverQueries.movimientos?.validated || false,
          validating: false,
          result: serverQueries.movimientos?.validated ? { valid: true, message: 'Consulta validada anteriormente' } : null
        }
      });
    } catch (error) {
      console.error('Error cargando consultas:', error);
    } finally {
      setLoading(false);
    }
  };

  const currentQuery = QUERY_TYPES[currentStep];
  const queryState = queries[currentQuery.key];

  const handleSqlChange = (sql) => {
    setQueries(prev => ({
      ...prev,
      [currentQuery.key]: {
        ...prev[currentQuery.key],
        sql,
        validated: false,
        result: null
      }
    }));
  };

  const validateQuery = async () => {
    if (!queryState.sql.trim()) {
      toast.error('Ingresa una consulta SQL');
      return;
    }

    setQueries(prev => ({
      ...prev,
      [currentQuery.key]: { ...prev[currentQuery.key], validating: true, result: null }
    }));

    try {
      const response = await api.post(`/servers/${server.id}/queries/validate`, {
        query_type: currentQuery.key,
        sql: queryState.sql
      });

      const result = response.data;
      
      setQueries(prev => ({
        ...prev,
        [currentQuery.key]: {
          ...prev[currentQuery.key],
          validating: false,
          validated: result.valid,
          result
        }
      }));

      if (result.valid) {
        toast.success('Consulta validada correctamente');
      } else {
        toast.error('La consulta no cumple con los requisitos');
      }
    } catch (error) {
      console.error('Error validando:', error);
      setQueries(prev => ({
        ...prev,
        [currentQuery.key]: {
          ...prev[currentQuery.key],
          validating: false,
          result: {
            valid: false,
            message: error.response?.data?.detail || 'Error al validar la consulta'
          }
        }
      }));
      toast.error('Error al validar la consulta');
    }
  };

  const saveCurrentQuery = async () => {
    if (!queryState.sql.trim()) {
      toast.error('Ingresa una consulta SQL');
      return;
    }

    setSaving(true);
    try {
      await api.put(`/servers/${server.id}/queries/${currentQuery.key}`, {
        sql: queryState.sql,
        validated: queryState.validated
      });
      
      toast.success(`Consulta de ${currentQuery.title} guardada`);
      
      // Avanzar al siguiente paso si hay más
      if (currentStep < QUERY_TYPES.length - 1) {
        setCurrentStep(currentStep + 1);
      }
    } catch (error) {
      console.error('Error guardando:', error);
      toast.error('Error al guardar la consulta');
    } finally {
      setSaving(false);
    }
  };

  const saveAllAndClose = async () => {
    setSaving(true);
    try {
      // Guardar todas las consultas que tienen contenido
      for (const queryType of QUERY_TYPES) {
        const q = queries[queryType.key];
        if (q.sql.trim()) {
          await api.put(`/servers/${server.id}/queries/${queryType.key}`, {
            sql: q.sql,
            validated: q.validated
          });
        }
      }
      
      toast.success('Configuración guardada correctamente');
      onComplete?.();
      onClose();
    } catch (error) {
      console.error('Error guardando:', error);
      toast.error('Error al guardar la configuración');
    } finally {
      setSaving(false);
    }
  };

  const getStepStatus = (index) => {
    const queryType = QUERY_TYPES[index];
    const q = queries[queryType.key];
    
    if (q.validated) return 'complete';
    if (q.sql.trim()) return 'partial';
    return 'pending';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'partial':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-zinc-300" />;
    }
  };

  const allConfigured = QUERY_TYPES.every(qt => queries[qt.key].validated);
  const hasAnyQuery = QUERY_TYPES.some(qt => queries[qt.key].sql.trim());

  if (loading) {
    return (
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            <span className="ml-3 text-zinc-600">Cargando configuración...</span>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Configurar Consultas SQL - {server?.name}
          </DialogTitle>
          <DialogDescription>
            Configura las consultas SQL necesarias para generar el análisis de inventario.
            Puedes guardar tu avance y continuar después.
          </DialogDescription>
        </DialogHeader>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-2 py-4 border-b">
          {QUERY_TYPES.map((qt, index) => {
            const Icon = qt.icon;
            const status = getStepStatus(index);
            const isActive = index === currentStep;
            
            return (
              <div key={qt.key} className="flex items-center">
                <button
                  onClick={() => setCurrentStep(index)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    isActive 
                      ? 'bg-zinc-900 text-white' 
                      : status === 'complete'
                        ? 'bg-green-50 text-green-700 hover:bg-green-100'
                        : status === 'partial'
                          ? 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100'
                          : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
                  }`}
                >
                  {status !== 'pending' ? getStatusIcon(status) : <Icon className="h-4 w-4" />}
                  <span className="font-medium text-sm">{qt.title}</span>
                </button>
                {index < QUERY_TYPES.length - 1 && (
                  <ChevronRight className="h-4 w-4 text-zinc-400 mx-1" />
                )}
              </div>
            );
          })}
        </div>

        {/* Current Step Content */}
        <div className="flex-1 overflow-y-auto py-4">
          <div className="space-y-4">
            {/* Query Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-900">{currentQuery.title}</h4>
                  <p className="text-sm text-blue-700 mt-1">{currentQuery.description}</p>
                  <div className="mt-2 text-xs text-blue-600">
                    <span className="font-medium">Columnas requeridas:</span>{' '}
                    <code className="bg-blue-100 px-1 rounded">codigo</code>,{' '}
                    <code className="bg-blue-100 px-1 rounded">cantidad</code>
                  </div>
                </div>
              </div>
            </div>

            {/* SQL Editor */}
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-2">
                Consulta SQL
              </label>
              <Textarea
                value={queryState.sql}
                onChange={(e) => handleSqlChange(e.target.value)}
                placeholder={currentQuery.placeholder}
                className="font-mono text-sm min-h-[200px] bg-zinc-950 text-zinc-100 border-zinc-700"
                data-testid={`query-${currentQuery.key}-input`}
              />
            </div>

            {/* Validation Actions */}
            <div className="flex items-center gap-3">
              <Button
                onClick={validateQuery}
                disabled={queryState.validating || !queryState.sql.trim()}
                variant="outline"
                data-testid={`validate-${currentQuery.key}-btn`}
              >
                {queryState.validating ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                Probar Consulta
              </Button>
              
              {queryState.validated && (
                <Badge variant="success" className="bg-green-100 text-green-800">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Validada
                </Badge>
              )}
            </div>

            {/* Validation Results */}
            {queryState.result && (
              <div className={`rounded-lg border p-4 ${
                queryState.result.valid 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-start gap-3">
                  {queryState.result.valid ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className={`font-medium ${queryState.result.valid ? 'text-green-800' : 'text-red-800'}`}>
                      {queryState.result.message}
                    </p>
                    
                    {/* Columns Found */}
                    {queryState.result.columns_found?.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-zinc-700 mb-1">Columnas encontradas:</p>
                        <div className="flex flex-wrap gap-1">
                          {queryState.result.columns_found.map((col, i) => (
                            <code key={i} className="text-xs bg-white px-2 py-0.5 rounded border">
                              {col}
                            </code>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Columns */}
                    {queryState.result.columns_missing?.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-red-700 mb-1">Columnas faltantes:</p>
                        <div className="flex flex-wrap gap-1">
                          {queryState.result.columns_missing.map((col, i) => (
                            <code key={i} className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded border border-red-200">
                              {col}
                            </code>
                          ))}
                        </div>
                        <p className="text-xs text-red-600 mt-2">
                          Tip: Usa alias como "as codigo" o "as cantidad" para renombrar las columnas.
                        </p>
                      </div>
                    )}
                    
                    {/* Sample Data */}
                    {queryState.result.sample_data?.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-zinc-700 mb-1">
                          Datos de ejemplo ({queryState.result.row_count} registros):
                        </p>
                        <div className="overflow-x-auto">
                          <table className="text-xs border-collapse w-full">
                            <thead>
                              <tr className="bg-zinc-100">
                                {Object.keys(queryState.result.sample_data[0]).map((key) => (
                                  <th key={key} className="border border-zinc-200 px-2 py-1 text-left font-medium">
                                    {key}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {queryState.result.sample_data.slice(0, 3).map((row, i) => (
                                <tr key={i} className="bg-white">
                                  {Object.values(row).map((val, j) => (
                                    <td key={j} className="border border-zinc-200 px-2 py-1 truncate max-w-[150px]">
                                      {val?.toString() || '-'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <DialogFooter className="border-t pt-4">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2 text-sm text-zinc-600">
              {allConfigured ? (
                <Badge className="bg-green-100 text-green-800">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Todas las consultas configuradas
                </Badge>
              ) : (
                <span>
                  {QUERY_TYPES.filter(qt => queries[qt.key].validated).length} de {QUERY_TYPES.length} consultas validadas
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {currentStep > 0 && (
                <Button variant="outline" onClick={() => setCurrentStep(currentStep - 1)}>
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Anterior
                </Button>
              )}
              
              <Button
                onClick={saveCurrentQuery}
                disabled={saving || !queryState.sql.trim()}
                variant="outline"
                data-testid="save-query-btn"
              >
                <Save className="h-4 w-4 mr-2" />
                {currentStep < QUERY_TYPES.length - 1 ? 'Guardar y Continuar' : 'Guardar'}
              </Button>
              
              <Button
                onClick={saveAllAndClose}
                disabled={saving || !hasAnyQuery}
                className="bg-zinc-900 text-white hover:bg-zinc-800"
                data-testid="save-all-queries-btn"
              >
                {saving ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                )}
                Guardar y Cerrar
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default QueryConfigWizard;
