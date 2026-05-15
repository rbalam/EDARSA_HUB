/**
 * UniversalQueryTester - Componente Frontend
 * ==========================================
 * Herramienta agnóstica para probar consultas SQL o endpoints API
 * contra cualquier origen de datos registrado.
 * 
 * AGNÓSTICO:
 * - NO asume dominio (no productos, no ventas, no inventarios)
 * - NO valida estructura de columnas específica
 * - Preview dinámico de cualquier resultado
 * - Compatible con cualquier sistema: SQL Server, Nóminas, RH, etc.
 * 
 * FASE API-UQT1:
 * - Soporta connectionType = 'sql' (default) para servidores SQL
 * - Soporta connectionType = 'api' para conexiones API (EDARSAHUB)
 * - Endpoints separados según tipo de conexión
 */

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Loader2, Play, CheckCircle2, XCircle, Plus, Trash2, 
  Database, Globe, Wifi, Wrench, AlertTriangle, Info,
  Clock, Rows3, Columns3
} from 'lucide-react';
import { toast } from 'sonner';

// Tipos de test para SQL Servers
const SQL_TEST_TYPES = [
  { key: 'sql_libre', label: 'SQL libre', icon: Database, description: 'Ejecutar consulta SELECT' },
  { key: 'api_rest', label: 'API REST', icon: Globe, description: 'Probar endpoint HTTP' },
  { key: 'conexion', label: 'Validar conexión', icon: Wifi, description: 'Verificar conectividad' },
  { key: 'diagnostico', label: 'Diagnóstico', icon: Wrench, description: 'Info técnica del servidor' }
];

// Tipos de test para Conexiones API (solo api_rest por ahora)
const API_TEST_TYPES = [
  { key: 'api_rest', label: 'API REST (GET)', icon: Globe, description: 'Probar endpoint HTTP GET' }
];

// ============================================================================
// API-SEC1: CONSTANTES DE SEGURIDAD PARA CONEXIONES API
// ============================================================================

// Nombres de parámetros BLOQUEADOS para conexiones API
const BLOCKED_API_PARAM_NAMES = [
  'sql', 'query', 'consulta', 'statement', 'command', 
  'script', 'exec', 'execute'
];

// Patrones SQL BLOQUEADOS en valores de parámetros API
const SQL_PATTERN_KEYWORDS = [
  'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER',
  'TRUNCATE', 'EXEC', 'MERGE', 'CREATE', 'UNION', 'FROM',
  'WHERE', 'INFORMATION_SCHEMA', 'sys.tables'
];

// Mensaje de bloqueo para UI
const SQL_BLOCK_MESSAGE = 
  'No se permite enviar SQL o comandos dinámicos mediante parámetros API en esta fase. ' +
  'Use el botón "Probar conexión" para validación técnica controlada.';

/**
 * API-SEC1: Valida que un nombre de parámetro no esté bloqueado
 * @param {string} paramName - Nombre del parámetro
 * @returns {{valid: boolean, message: string|null}}
 */
const validateApiParamName = (paramName) => {
  if (!paramName) return { valid: true, message: null };
  const nameLower = paramName.toLowerCase().trim();
  if (BLOCKED_API_PARAM_NAMES.includes(nameLower)) {
    return { 
      valid: false, 
      message: `El parámetro "${paramName}" no está permitido. ${SQL_BLOCK_MESSAGE}`
    };
  }
  return { valid: true, message: null };
};

/**
 * API-SEC1: Valida que un valor no contenga patrones SQL
 * @param {string} value - Valor del parámetro
 * @returns {{valid: boolean, message: string|null}}
 */
const validateApiParamValue = (value) => {
  if (!value) return { valid: true, message: null };
  const valueUpper = value.toUpperCase();
  for (const keyword of SQL_PATTERN_KEYWORDS) {
    // Usar regex para detectar palabras completas
    const regex = new RegExp(`\\b${keyword}\\b`, 'i');
    if (regex.test(valueUpper)) {
      return { 
        valid: false, 
        message: `El valor contiene el patrón SQL "${keyword}". ${SQL_BLOCK_MESSAGE}`
      };
    }
  }
  return { valid: true, message: null };
};

// ============================================================================
// FIN API-SEC1
// ============================================================================

const DEFAULT_SQL = 'SELECT TOP 10 * FROM INFORMATION_SCHEMA.TABLES';

const MAX_ROWS_OPTIONS = [10, 25, 50, 100, 250, 500];
const TIMEOUT_OPTIONS = [10, 30, 60, 120];

/**
 * @param {Object} props
 * @param {boolean} props.open - Si el modal está abierto
 * @param {Function} props.onClose - Callback al cerrar
 * @param {Object} props.server - Servidor o conexión { id, name, system_type }
 * @param {string} props.connectionType - 'sql' (default) | 'api'
 */
const UniversalQueryTester = ({ open, onClose, server, connectionType = 'sql' }) => {
  // Determinar tipos de test según connectionType
  const TEST_TYPES = connectionType === 'api' ? API_TEST_TYPES : SQL_TEST_TYPES;
  const defaultTestType = connectionType === 'api' ? 'api_rest' : 'sql_libre';
  
  // Estado del formulario
  const [testName, setTestName] = useState('');
  const [testType, setTestType] = useState(defaultTestType);
  const [moduleRelated, setModuleRelated] = useState('');
  const [parameters, setParameters] = useState([]);
  
  // SQL Config (solo para connectionType = 'sql')
  const [sqlQuery, setSqlQuery] = useState(DEFAULT_SQL);
  const [maxRows, setMaxRows] = useState(100);
  const [sqlTimeout, setSqlTimeout] = useState(30);
  
  // API Config
  const [apiMethod, setApiMethod] = useState('GET');
  const [apiUrl, setApiUrl] = useState('');
  const [apiEndpointPath, setApiEndpointPath] = useState('');  // FASE API-UQT1
  const [apiHeaders, setApiHeaders] = useState([]);
  const [apiParams, setApiParams] = useState([]);
  const [apiTimeout, setApiTimeout] = useState(30);
  
  // Estado de ejecución
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);

  // Reset al abrir
  useEffect(() => {
    if (open) {
      setTestName('');
      setTestType(defaultTestType);
      setModuleRelated('');
      setParameters([]);
      setSqlQuery(DEFAULT_SQL);
      setMaxRows(100);
      setSqlTimeout(30);
      setApiUrl('');
      setApiEndpointPath('');
      setApiHeaders([]);
      setApiParams([]);
      setResult(null);
    }
  }, [open, defaultTestType]);

  // Agregar parámetro
  const addParameter = () => {
    setParameters([...parameters, { key: '', value: '' }]);
  };

  const removeParameter = (index) => {
    setParameters(parameters.filter((_, i) => i !== index));
  };

  const updateParameter = (index, field, value) => {
    const updated = [...parameters];
    updated[index][field] = value;
    setParameters(updated);
  };

  // Agregar header API
  const addApiHeader = () => {
    setApiHeaders([...apiHeaders, { key: '', value: '' }]);
  };

  const removeApiHeader = (index) => {
    setApiHeaders(apiHeaders.filter((_, i) => i !== index));
  };

  const updateApiHeader = (index, field, value) => {
    const updated = [...apiHeaders];
    updated[index][field] = value;
    setApiHeaders(updated);
  };

  // Agregar param API
  const addApiParam = () => {
    setApiParams([...apiParams, { key: '', value: '', error: null }]);
  };

  const removeApiParam = (index) => {
    setApiParams(apiParams.filter((_, i) => i !== index));
  };

  // API-SEC1: Actualizar param API con validación de seguridad
  const updateApiParam = (index, field, value) => {
    const updated = [...apiParams];
    updated[index][field] = value;
    
    // Solo validar si es conexión API
    if (connectionType === 'api') {
      let error = null;
      
      // Validar nombre de parámetro
      if (field === 'key') {
        const nameValidation = validateApiParamName(value);
        if (!nameValidation.valid) {
          error = nameValidation.message;
          toast.error(nameValidation.message, { duration: 5000 });
        }
      }
      
      // Validar valor del parámetro
      if (field === 'value') {
        const valueValidation = validateApiParamValue(value);
        if (!valueValidation.valid) {
          error = valueValidation.message;
          toast.error(valueValidation.message, { duration: 5000 });
        }
      }
      
      updated[index].error = error;
    }
    
    setApiParams(updated);
  };

  // API-SEC1: Verificar si hay errores de validación en parámetros API
  const hasApiParamErrors = () => {
    if (connectionType !== 'api') return false;
    return apiParams.some(p => p.error);
  };

  // Ejecutar prueba
  const executeTest = async () => {
    if (!server?.id) {
      toast.error('Servidor no seleccionado');
      return;
    }

    // API-SEC1: Validar que no hay errores de seguridad antes de ejecutar
    if (connectionType === 'api' && hasApiParamErrors()) {
      toast.error(SQL_BLOCK_MESSAGE, { duration: 5000 });
      return;
    }

    // API-SEC1: Validación final de parámetros para conexiones API
    if (connectionType === 'api') {
      for (const param of apiParams) {
        if (param.key) {
          const nameValidation = validateApiParamName(param.key);
          if (!nameValidation.valid) {
            toast.error(nameValidation.message, { duration: 5000 });
            return;
          }
        }
        if (param.value) {
          const valueValidation = validateApiParamValue(param.value);
          if (!valueValidation.valid) {
            toast.error(valueValidation.message, { duration: 5000 });
            return;
          }
        }
      }
    }

    setExecuting(true);
    setResult(null);

    try {
      // Determinar endpoint según connectionType
      const endpoint = connectionType === 'api'
        ? `/api-connections/${server.id}/universal-query-test`
        : `/servers/${server.id}/universal-query-test`;
      
      // Construir request según connectionType
      let requestBody;
      
      if (connectionType === 'api') {
        // Request para Conexiones API (FASE API-UQT1)
        // NO enviar sql_config, solo api_rest GET
        requestBody = {
          test_name: testName || 'Prueba API REST',
          test_type: 'api_rest',
          method: 'GET',  // Solo GET permitido en esta fase
          endpoint_path: apiEndpointPath || '',
          query_params: apiParams.reduce((acc, p) => {
            if (p.key) acc[p.key] = p.value;
            return acc;
          }, {}),
          headers: apiHeaders.reduce((acc, h) => {
            if (h.key) acc[h.key] = h.value;
            return acc;
          }, {}),
          timeout_seconds: apiTimeout,
          module: moduleRelated || null
        };
      } else {
        // Request para SQL Servers (endpoint original)
        requestBody = {
          test_name: testName || `Prueba ${testType}`,
          test_type: testType,
          module: moduleRelated || null,
          parameters: parameters.reduce((acc, p) => {
            if (p.key) acc[p.key] = p.value;
            return acc;
          }, {}),
          sql_config: testType === 'sql_libre' ? {
            query: sqlQuery,
            max_rows: maxRows,
            timeout_seconds: sqlTimeout
          } : null,
          api_config: testType === 'api_rest' ? {
            method: apiMethod,
            url: apiUrl,
            headers: apiHeaders.reduce((acc, h) => {
              if (h.key) acc[h.key] = h.value;
              return acc;
            }, {}),
            query_params: apiParams.reduce((acc, p) => {
              if (p.key) acc[p.key] = p.value;
              return acc;
            }, {}),
            timeout_seconds: apiTimeout
          } : null
        };
      }

      const response = await api.post(endpoint, requestBody);
      setResult(response.data);

      if (response.data.success) {
        toast.success('Prueba ejecutada correctamente');
      } else {
        toast.error(`Error: ${response.data.execution?.error_message || 'Error desconocido'}`);
      }
    } catch (error) {
      console.error('Error ejecutando prueba:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Error de conexión';
      toast.error(`Error: ${errorMsg}`);
      setResult({
        success: false,
        execution: {
          status: 'error',
          error_message: errorMsg
        }
      });
    } finally {
      setExecuting(false);
    }
  };

  // Render dinámico de tabla de resultados
  const renderDynamicTable = () => {
    if (!result?.preview || !Array.isArray(result.preview) || result.preview.length === 0) {
      return <p className="text-zinc-500 text-sm">Sin datos para mostrar</p>;
    }

    const columns = result.metadata?.columns || Object.keys(result.preview[0] || {});

    return (
      <div className="overflow-x-auto max-h-64 overflow-y-auto border rounded">
        <table className="w-full text-xs">
          <thead className="bg-zinc-100 sticky top-0">
            <tr>
              {columns.map((col, i) => (
                <th key={i} className="border-b p-2 text-left font-medium text-zinc-700 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.preview.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-zinc-50">
                {columns.map((col, colIndex) => (
                  <td key={colIndex} className="border-b p-2 text-zinc-600 whitespace-nowrap">
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Render JSON para API
  const renderJsonPreview = () => {
    if (!result?.preview) return null;

    const previewData = typeof result.preview === 'string' 
      ? result.preview.substring(0, 1000) 
      : JSON.stringify(result.preview, null, 2).substring(0, 2000);

    return (
      <pre className="bg-zinc-900 text-zinc-100 p-3 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto">
        {previewData}
      </pre>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" data-testid="universal-query-tester-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {connectionType === 'api' ? (
              <Globe className="h-5 w-5 text-purple-600" />
            ) : (
              <Database className="h-5 w-5" />
            )}
            Test Universal {connectionType === 'api' ? 'API' : 'SQL/API'} - {server?.name || 'Servidor'}
          </DialogTitle>
          <DialogDescription>
            {connectionType === 'api' 
              ? 'Prueba conexiones API REST (solo GET). La URL base se obtiene de la configuración.'
              : 'Herramienta agnóstica de diagnóstico técnico'
            }
          </DialogDescription>
        </DialogHeader>

        {/* Aviso de herramienta agnóstica */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800 flex items-start gap-2">
          <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>
            Esta prueba no está asociada a ningún catálogo ni módulo obligatorio. 
            Es una herramienta de diagnóstico técnico agnóstica.
          </span>
        </div>

        <div className="space-y-4">
          {/* PARA CONEXIONES API: Resumen simplificado de solo lectura */}
          {connectionType === 'api' ? (
            <>
              {/* Resumen de la conexión */}
              <Card className="bg-zinc-50 border-zinc-200">
                <CardHeader className="py-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    Resumen de prueba
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-zinc-500">Servidor:</span>
                    <p className="font-medium">{server?.name || 'Sin nombre'}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Sistema:</span>
                    <p className="font-medium">{server?.system_type || 'API REST'}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Tipo de prueba:</span>
                    <p className="font-medium">Conexión API REST (GET)</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Método:</span>
                    <Badge variant="outline" className="text-xs">GET</Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Configuración de la prueba API */}
              <Card>
                <CardHeader className="py-3">
                  <CardTitle className="text-sm font-medium">Configuración de prueba</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Path adicional */}
                  <div className="space-y-2">
                    <Label className="text-sm flex items-center gap-1">
                      Path adicional
                      <span className="text-xs text-zinc-500">(opcional)</span>
                    </Label>
                    <Input
                      placeholder="/ventas, /inventario?sucursal=0021"
                      value={apiEndpointPath}
                      onChange={(e) => setApiEndpointPath(e.target.value)}
                      className="font-mono text-sm"
                      data-testid="api-endpoint-path-input"
                    />
                    <p className="text-xs text-zinc-500">
                      Ruta que se agregará a la URL base de la conexión. Ejemplo: /ventas o /inventario?sucursal=0021
                    </p>
                  </div>

                  {/* Vista previa de URL */}
                  <div className="bg-zinc-100 rounded-lg p-3 space-y-1">
                    <Label className="text-xs text-zinc-600">Vista previa de URL final:</Label>
                    <div className="font-mono text-sm text-zinc-800 break-all">
                      <Badge variant="secondary" className="mr-2">GET</Badge>
                      <span className="text-zinc-500">[URL_BASE_CONEXIÓN]</span>
                      <span className="text-blue-600">{apiEndpointPath || ''}</span>
                      {apiParams.length > 0 && (
                        <span className="text-green-600">
                          ?{apiParams.filter(p => p.key).map(p => `${p.key}=${p.value || '...'}`).join('&')}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Headers opcionales */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm flex items-center gap-1">
                        Headers
                        <span className="text-xs text-zinc-500">(opcional)</span>
                      </Label>
                      <Button variant="ghost" size="sm" onClick={addApiHeader} className="h-7">
                        <Plus className="h-3 w-3 mr-1" /> Agregar
                      </Button>
                    </div>
                    {apiHeaders.length === 0 ? (
                      <p className="text-xs text-zinc-500 italic">
                        Usa headers cuando la API requiera autenticación o configuración adicional.
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {apiHeaders.map((header, index) => (
                          <div key={index} className="flex gap-2 items-center">
                            <Input
                              placeholder="Clave (ej: X-Custom-Header)"
                              value={header.key}
                              onChange={(e) => updateApiHeader(index, 'key', e.target.value)}
                              className="w-1/3 h-8 text-xs"
                            />
                            <Input
                              placeholder="Valor"
                              value={header.value}
                              onChange={(e) => updateApiHeader(index, 'value', e.target.value)}
                              className="flex-1 h-8 text-xs"
                              type={header.key.toLowerCase().includes('auth') || 
                                    header.key.toLowerCase().includes('token') || 
                                    header.key.toLowerCase().includes('key') ? 'password' : 'text'}
                            />
                            <Button variant="ghost" size="sm" onClick={() => removeApiHeader(index)} className="h-8 w-8 p-0">
                              <Trash2 className="h-3 w-3 text-red-500" />
                            </Button>
                          </div>
                        ))}
                        <p className="text-xs text-zinc-500">Los valores sensibles se enmascaran automáticamente.</p>
                      </div>
                    )}
                  </div>

                  {/* Query Params opcionales */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm flex items-center gap-1">
                        Query Params
                        <span className="text-xs text-zinc-500">(opcional)</span>
                      </Label>
                      <Button variant="ghost" size="sm" onClick={addApiParam} className="h-7">
                        <Plus className="h-3 w-3 mr-1" /> Agregar
                      </Button>
                    </div>
                    {apiParams.length === 0 ? (
                      <p className="text-xs text-zinc-500 italic">
                        Filtros enviados en la URL. Ejemplo: fecha=2026-05-15, sucursal=0021
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {apiParams.map((param, index) => (
                          <div key={index} className="flex gap-2 items-center">
                            <Input
                              placeholder="Clave"
                              value={param.key}
                              onChange={(e) => updateApiParam(index, 'key', e.target.value)}
                              className="w-1/3 h-8 text-xs"
                            />
                            <Input
                              placeholder="Valor"
                              value={param.value}
                              onChange={(e) => updateApiParam(index, 'value', e.target.value)}
                              className="flex-1 h-8 text-xs"
                            />
                            <Button variant="ghost" size="sm" onClick={() => removeApiParam(index)} className="h-8 w-8 p-0">
                              <Trash2 className="h-3 w-3 text-red-500" />
                            </Button>
                          </div>
                        ))}
                        <p className="text-xs text-zinc-500">No se permite SQL libre en los parámetros.</p>
                      </div>
                    )}
                  </div>

                  {/* Timeout */}
                  <div className="flex items-center gap-3">
                    <Label className="text-sm">Timeout:</Label>
                    <Select value={String(apiTimeout)} onValueChange={(v) => setApiTimeout(Number(v))}>
                      <SelectTrigger className="w-24 h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TIMEOUT_OPTIONS.map((n) => (
                          <SelectItem key={n} value={String(n)}>{n} segundos</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <span className="text-xs text-zinc-500">Tiempo máximo de espera para la respuesta.</span>
                  </div>

                  {/* Aviso de seguridad */}
                  <div className="flex items-center gap-2 text-amber-600 text-xs bg-amber-50 p-2 rounded">
                    <AlertTriangle className="h-3 w-3 flex-shrink-0" />
                    <span>Solo método GET permitido. Los headers sensibles se enmascararán. No se permite SQL libre.</span>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            /* FORMULARIO ORIGINAL PARA SQL */
            <>
              {/* Fila 1: Nombre y Tipo */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nombre de prueba</Label>
                  <Input
                    placeholder="Ej: Listar tablas, Validar conexión..."
                    value={testName}
                    onChange={(e) => setTestName(e.target.value)}
                    data-testid="test-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipo de prueba</Label>
                  <Select value={testType} onValueChange={setTestType}>
                    <SelectTrigger data-testid="test-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TEST_TYPES.map((type) => (
                        <SelectItem key={type.key} value={type.key}>
                          <div className="flex items-center gap-2">
                            <type.icon className="h-4 w-4" />
                            <span>{type.label}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Fila 2: Sistema y Módulo */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Sistema detectado</Label>
                  <Input
                    value={server?.system_type || 'Desconocido'}
                    disabled
                    className="bg-zinc-50"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Módulo relacionado (opcional)</Label>
                  <Input
                    placeholder="Ej: Nóminas, RH, Contabilidad, Ninguno..."
                    value={moduleRelated}
                    onChange={(e) => setModuleRelated(e.target.value)}
                    data-testid="module-input"
                  />
                  <p className="text-xs text-zinc-500">Campo libre. Escribe cualquier módulo o déjalo vacío.</p>
                </div>
              </div>

              {/* Parámetros dinámicos */}
              <Card>
                <CardHeader className="py-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">Parámetros dinámicos (opcional)</CardTitle>
                    <Button variant="outline" size="sm" onClick={addParameter}>
                      <Plus className="h-3 w-3 mr-1" /> Agregar
                    </Button>
                  </div>
                </CardHeader>
                {parameters.length > 0 && (
                  <CardContent className="pt-0">
                    <div className="space-y-2">
                      {parameters.map((param, index) => (
                        <div key={index} className="flex gap-2 items-center">
                          <Input
                            placeholder="Clave"
                            value={param.key}
                            onChange={(e) => updateParameter(index, 'key', e.target.value)}
                            className="w-1/3"
                          />
                          <Input
                            placeholder="Valor"
                            value={param.value}
                            onChange={(e) => updateParameter(index, 'value', e.target.value)}
                            className="flex-1"
                          />
                          <Button variant="ghost" size="sm" onClick={() => removeParameter(index)}>
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-zinc-500 mt-2">
                      Usa {'{clave}'} en tu query para sustituir el valor.
                    </p>
                  </CardContent>
                )}
              </Card>

              {/* Configuración según tipo */}
              {testType === 'sql_libre' && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm font-medium">Editor SQL</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Textarea
                  className="font-mono text-sm min-h-32"
                  value={sqlQuery}
                  onChange={(e) => setSqlQuery(e.target.value)}
                  placeholder="SELECT TOP 10 * FROM INFORMATION_SCHEMA.TABLES"
                  data-testid="sql-editor"
                />
                <div className="flex gap-4">
                  <div className="flex items-center gap-2">
                    <Label className="text-xs">Límite filas:</Label>
                    <Select value={String(maxRows)} onValueChange={(v) => setMaxRows(Number(v))}>
                      <SelectTrigger className="w-20 h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {MAX_ROWS_OPTIONS.map((n) => (
                          <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Label className="text-xs">Timeout:</Label>
                    <Select value={String(sqlTimeout)} onValueChange={(v) => setSqlTimeout(Number(v))}>
                      <SelectTrigger className="w-20 h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TIMEOUT_OPTIONS.map((n) => (
                          <SelectItem key={n} value={String(n)}>{n}s</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-amber-600 text-xs">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Solo se permiten consultas SELECT (lectura)</span>
                </div>
              </CardContent>
            </Card>
          )}

          {testType === 'api_rest' && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm font-medium">
                  {connectionType === 'api' ? 'Configuración API REST (Solo GET)' : 'Configuración API REST'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Para Conexiones API: solo endpoint_path (URL base viene de la conexión) */}
                {connectionType === 'api' ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs text-zinc-500 mb-2">
                      <Info className="h-3 w-3" />
                      <span>La URL base se obtiene automáticamente de la configuración de la conexión</span>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="outline" className="text-xs px-2 py-1">GET</Badge>
                      <Input
                        placeholder="Path adicional: /endpoint o /ventas?fecha=hoy"
                        value={apiEndpointPath}
                        onChange={(e) => setApiEndpointPath(e.target.value)}
                        className="flex-1"
                        data-testid="api-endpoint-path-input"
                      />
                    </div>
                    <p className="text-xs text-zinc-500">Ejemplo: /ventas, /inventario?sucursal=0021</p>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <Select value={apiMethod} onValueChange={setApiMethod}>
                      <SelectTrigger className="w-24">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="GET">GET</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder="https://api.ejemplo.com/endpoint"
                      value={apiUrl}
                      onChange={(e) => setApiUrl(e.target.value)}
                      className="flex-1"
                      data-testid="api-url-input"
                    />
                  </div>
                )}
                
                {/* Headers */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Headers</Label>
                    <Button variant="ghost" size="sm" onClick={addApiHeader}>
                      <Plus className="h-3 w-3" />
                    </Button>
                  </div>
                  {apiHeaders.map((header, index) => (
                    <div key={index} className="flex gap-2 items-center">
                      <Input
                        placeholder="Clave"
                        value={header.key}
                        onChange={(e) => updateApiHeader(index, 'key', e.target.value)}
                        className="w-1/3 h-8 text-xs"
                      />
                      <Input
                        placeholder="Valor"
                        value={header.value}
                        onChange={(e) => updateApiHeader(index, 'value', e.target.value)}
                        className="flex-1 h-8 text-xs"
                        type={header.key.toLowerCase().includes('auth') || header.key.toLowerCase().includes('token') ? 'password' : 'text'}
                      />
                      <Button variant="ghost" size="sm" onClick={() => removeApiHeader(index)}>
                        <Trash2 className="h-3 w-3 text-red-500" />
                      </Button>
                    </div>
                  ))}
                </div>

                {/* Query Params */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Query Params</Label>
                    <Button variant="ghost" size="sm" onClick={addApiParam}>
                      <Plus className="h-3 w-3" />
                    </Button>
                  </div>
                  {apiParams.map((param, index) => (
                    <div key={index} className="flex gap-2 items-center">
                      <Input
                        placeholder="Clave"
                        value={param.key}
                        onChange={(e) => updateApiParam(index, 'key', e.target.value)}
                        className="w-1/3 h-8 text-xs"
                      />
                      <Input
                        placeholder="Valor"
                        value={param.value}
                        onChange={(e) => updateApiParam(index, 'value', e.target.value)}
                        className="flex-1 h-8 text-xs"
                      />
                      <Button variant="ghost" size="sm" onClick={() => removeApiParam(index)}>
                        <Trash2 className="h-3 w-3 text-red-500" />
                      </Button>
                    </div>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <Label className="text-xs">Timeout:</Label>
                  <Select value={String(apiTimeout)} onValueChange={(v) => setApiTimeout(Number(v))}>
                    <SelectTrigger className="w-20 h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TIMEOUT_OPTIONS.map((n) => (
                        <SelectItem key={n} value={String(n)}>{n}s</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center gap-2 text-amber-600 text-xs">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Solo método GET permitido en esta fase. Los headers sensibles se enmascararán.</span>
                </div>
              </CardContent>
            </Card>
          )}

          {(testType === 'conexion' || testType === 'diagnostico') && (
            <Card>
              <CardContent className="py-4">
                <p className="text-sm text-zinc-600">
                  {testType === 'conexion' 
                    ? 'Se ejecutará una prueba de conexión básica (SELECT 1).'
                    : 'Se obtendrá información técnica del servidor (versión, nombre, conteo de tablas).'}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Botón ejecutar */}
          <Button 
            onClick={executeTest} 
            disabled={executing || (connectionType !== 'api' && testType === 'api_rest' && !apiUrl)}
            className="w-full"
            data-testid="execute-test-btn"
          >
            {executing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Ejecutando...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Ejecutar Prueba
              </>
            )}
          </Button>

          {/* Resultado */}
          {result && (
            <Card className={result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
              <CardHeader className="py-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  {result.success ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600" />
                  )}
                  Resultado: {result.success ? 'Éxito' : 'Error'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Métricas */}
                <div className="flex flex-wrap gap-3 text-xs">
                  {result.execution?.response_time_ms !== undefined && (
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {result.execution.response_time_ms}ms
                    </Badge>
                  )}
                  {result.execution?.rows_returned !== undefined && (
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Rows3 className="h-3 w-3" />
                      {result.execution.rows_returned} filas
                    </Badge>
                  )}
                  {result.metadata?.total_columns !== undefined && (
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Columns3 className="h-3 w-3" />
                      {result.metadata.total_columns} columnas
                    </Badge>
                  )}
                  {result.execution?.http_status !== undefined && (
                    <Badge variant="outline">
                      HTTP {result.execution.http_status}
                    </Badge>
                  )}
                </div>

                {/* Columnas detectadas */}
                {result.metadata?.columns && result.metadata.columns.length > 0 && (
                  <div className="text-xs">
                    <span className="font-medium">Columnas: </span>
                    <span className="text-zinc-600">{result.metadata.columns.join(', ')}</span>
                  </div>
                )}

                {/* Error message */}
                {result.execution?.error_message && (
                  <div className="text-sm text-red-700 bg-red-100 p-2 rounded">
                    {result.execution.error_message}
                  </div>
                )}

                {/* Preview de datos */}
                {result.success && result.preview && (
                  <div>
                    <Label className="text-xs mb-2 block">Preview:</Label>
                    {testType === 'api_rest' ? renderJsonPreview() : renderDynamicTable()}
                  </div>
                )}

                {/* Query ejecutada */}
                {result.execution?.query_executed && (
                  <div>
                    <Label className="text-xs mb-1 block">Query ejecutada:</Label>
                    <pre className="bg-zinc-800 text-zinc-100 p-2 rounded text-xs overflow-x-auto">
                      {result.execution.query_executed}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default UniversalQueryTester;
