/**
 * DBA Credential Manager - FASE P0D
 * ==================================
 * 
 * Formulario seguro para registrar credencial DBA/SA
 * Solo accesible por SuperAdministrador
 * 
 * SEGURIDAD:
 * - Campo tipo password (nunca muestra valor)
 * - Envío por HTTPS únicamente
 * - No se loguea la contraseña
 * - No se almacena en localStorage
 * - Se cifra inmediatamente en backend
 * 
 * CREADO: FASE P0D - Diagnóstico Ejecutor B
 */

import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Key, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Loader2,
  Database,
  Search,
  Trash2,
  Eye,
  EyeOff,
  Server,
  Clock,
  FileText,
  AlertCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DBACredentialManager = () => {
  // Estados
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [testing, setTesting] = useState(false);
  const [diagnosing, setDiagnosing] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [message, setMessage] = useState(null);
  const [connectionTest, setConnectionTest] = useState(null);
  const [diagnosticResults, setDiagnosticResults] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [userEmail, setUserEmail] = useState(null);

  // Obtener token
  const getToken = () => localStorage.getItem('token');

  // Verificar rol del usuario
  useEffect(() => {
    const token = getToken();
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUserRole(payload.role);
        setUserEmail(payload.email);
      } catch (e) {
        console.error('Error decodificando token');
      }
    }
  }, []);

  // Cargar estado inicial
  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/dba-credential/status`, {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      
      if (response.status === 403) {
        setMessage({ type: 'error', text: 'Acceso denegado. Solo SuperAdministrador.' });
        setLoading(false);
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Error obteniendo estado' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    setLoading(false);
  };

  // Registrar credencial
  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (!password || password.length < 1) {
      setMessage({ type: 'error', text: 'Ingrese la contraseña SA' });
      return;
    }
    
    setRegistering(true);
    setMessage(null);
    
    try {
      const response = await fetch(`${API_URL}/api/admin/dba-credential/register`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password })
      });
      
      // Limpiar password del estado inmediatamente
      setPassword('');
      
      if (response.ok) {
        const data = await response.json();
        setMessage({ 
          type: 'success', 
          text: 'Credencial registrada de forma segura (cifrada)' 
        });
        fetchStatus();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Error registrando credencial' });
      }
    } catch (error) {
      setPassword('');
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    
    setRegistering(false);
  };

  // Probar conexión
  const handleTestConnection = async () => {
    setTesting(true);
    setConnectionTest(null);
    setMessage(null);
    
    try {
      const response = await fetch(`${API_URL}/api/admin/dba-credential/test-connection`, {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      
      const data = await response.json();
      setConnectionTest(data);
      
      if (data.success) {
        setMessage({ type: 'success', text: 'Conexión DBA exitosa' });
      } else {
        setMessage({ type: 'error', text: data.error || 'Error de conexión' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    
    setTesting(false);
  };

  // Ejecutar diagnóstico
  const handleDiagnostic = async () => {
    setDiagnosing(true);
    setDiagnosticResults(null);
    setMessage(null);
    
    try {
      const response = await fetch(`${API_URL}/api/admin/dba-credential/execute-diagnostic`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        setDiagnosticResults(data);
        setMessage({ 
          type: 'success', 
          text: `Diagnóstico completado. ${data.suspects?.length || 0} sospechosos identificados.` 
        });
      } else {
        setMessage({ type: 'error', text: 'Error ejecutando diagnóstico' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    
    setDiagnosing(false);
  };

  // Limpiar credencial
  const handleClear = async () => {
    if (!window.confirm('¿Eliminar la credencial DBA de memoria?')) return;
    
    setClearing(true);
    setMessage(null);
    
    try {
      const response = await fetch(`${API_URL}/api/admin/dba-credential/clear`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Credencial eliminada de memoria' });
        setConnectionTest(null);
        setDiagnosticResults(null);
        fetchStatus();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Error eliminando credencial' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    
    setClearing(false);
  };

  // Verificar acceso
  const isSuperAdmin = userRole?.toLowerCase().replace(/[_ ]/g, '') === 'superadministrador' ||
                       userRole?.toLowerCase().replace(/[_ ]/g, '') === 'superadmin';

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Cargando...</span>
      </div>
    );
  }

  if (!isSuperAdmin) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-700 mb-2">Acceso Denegado</h2>
          <p className="text-red-600">
            Solo SuperAdministrador puede acceder a esta funcionalidad.
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Usuario actual: {userEmail} ({userRole})
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-600 rounded-lg p-6 text-white">
        <div className="flex items-center gap-3">
          <Shield className="w-10 h-10" />
          <div>
            <h1 className="text-2xl font-bold">Diagnóstico DBA - Ejecutor B</h1>
            <p className="text-amber-100">
              Fase P0D: Identificación de SQL Server Agent Jobs externos
            </p>
          </div>
        </div>
      </div>

      {/* Mensaje */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' 
            ? 'bg-green-50 border border-green-200 text-green-700'
            : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertTriangle className="w-5 h-5" />
          )}
          {message.text}
        </div>
      )}

      {/* Estado del Sistema */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-gray-500" />
          Estado del Sistema
        </h2>
        
        {status && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase">Cifrado</p>
              <p className={`font-semibold ${status.encryption_available ? 'text-green-600' : 'text-red-600'}`}>
                {status.encryption_available ? '✓ Disponible' : '✗ No disponible'}
              </p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase">Credencial DBA</p>
              <p className={`font-semibold ${status.dba_credential_registered ? 'text-green-600' : 'text-gray-400'}`}>
                {status.dba_credential_registered ? '✓ Registrada' : '○ No registrada'}
              </p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase">Servidor</p>
              <p className="font-mono text-sm">{status.dba_server}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase">Usuario DBA</p>
              <p className="font-mono text-sm">{status.dba_username}</p>
            </div>
          </div>
        )}
      </div>

      {/* Formulario de Registro */}
      {!status?.dba_credential_registered && (
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5 text-amber-500" />
            Registrar Credencial SA
          </h2>
          
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div className="text-sm text-amber-700">
                <p className="font-semibold">Información de Seguridad</p>
                <ul className="mt-1 space-y-1 list-disc list-inside">
                  <li>La contraseña se cifra inmediatamente con Fernet</li>
                  <li>Nunca se almacena en texto plano</li>
                  <li>No se envía a logs ni se muestra en pantalla</li>
                  <li>Se almacena temporalmente en memoria (se pierde al reiniciar)</li>
                </ul>
              </div>
            </div>
          </div>

          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contraseña SA
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Ingrese la contraseña del usuario SA"
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 pr-10"
                  autoComplete="new-password"
                  data-testid="dba-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Servidor: {status?.dba_server} | Base de datos: {status?.dba_database}
              </p>
            </div>

            <button
              type="submit"
              disabled={registering || !password}
              className="w-full py-2 px-4 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              data-testid="dba-register-btn"
            >
              {registering ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Registrando...
                </>
              ) : (
                <>
                  <Key className="w-4 h-4" />
                  Registrar Credencial (Cifrada)
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* Acciones con credencial registrada */}
      {status?.dba_credential_registered && (
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-green-500" />
            Acciones de Diagnóstico
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Probar Conexión */}
            <button
              onClick={handleTestConnection}
              disabled={testing}
              className="p-4 border rounded-lg hover:bg-gray-50 transition-colors flex flex-col items-center gap-2 disabled:opacity-50"
              data-testid="dba-test-btn"
            >
              {testing ? (
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              ) : (
                <Server className="w-8 h-8 text-blue-600" />
              )}
              <span className="font-medium">Probar Conexión</span>
              <span className="text-xs text-gray-500">Verificar acceso a msdb</span>
            </button>

            {/* Ejecutar Diagnóstico */}
            <button
              onClick={handleDiagnostic}
              disabled={diagnosing}
              className="p-4 border rounded-lg hover:bg-gray-50 transition-colors flex flex-col items-center gap-2 disabled:opacity-50"
              data-testid="dba-diagnostic-btn"
            >
              {diagnosing ? (
                <Loader2 className="w-8 h-8 animate-spin text-amber-600" />
              ) : (
                <Search className="w-8 h-8 text-amber-600" />
              )}
              <span className="font-medium">Ejecutar Diagnóstico</span>
              <span className="text-xs text-gray-500">Buscar Ejecutor B</span>
            </button>

            {/* Limpiar Credencial */}
            <button
              onClick={handleClear}
              disabled={clearing}
              className="p-4 border border-red-200 rounded-lg hover:bg-red-50 transition-colors flex flex-col items-center gap-2 disabled:opacity-50"
              data-testid="dba-clear-btn"
            >
              {clearing ? (
                <Loader2 className="w-8 h-8 animate-spin text-red-600" />
              ) : (
                <Trash2 className="w-8 h-8 text-red-600" />
              )}
              <span className="font-medium text-red-600">Eliminar Credencial</span>
              <span className="text-xs text-gray-500">Limpiar de memoria</span>
            </button>
          </div>
        </div>
      )}

      {/* Resultado de Test de Conexión */}
      {connectionTest && (
        <div className={`rounded-lg border p-6 ${
          connectionTest.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
        }`}>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            {connectionTest.success ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            Resultado de Conexión
          </h3>
          
          {connectionTest.success && connectionTest.identity && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <p className="text-gray-500">Usuario Sistema</p>
                <p className="font-mono">{connectionTest.identity.system_user}</p>
              </div>
              <div>
                <p className="text-gray-500">Base de Datos</p>
                <p className="font-mono">{connectionTest.identity.database}</p>
              </div>
              <div>
                <p className="text-gray-500">Es SysAdmin</p>
                <p className={connectionTest.identity.is_sysadmin ? 'text-green-600' : 'text-gray-400'}>
                  {connectionTest.identity.is_sysadmin ? '✓ Sí' : '○ No'}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Jobs Encontrados</p>
                <p className="font-semibold">{connectionTest.msdb_access?.job_count || 0}</p>
              </div>
            </div>
          )}
          
          {!connectionTest.success && (
            <p className="text-red-600">{connectionTest.error}</p>
          )}
        </div>
      )}

      {/* Resultados del Diagnóstico */}
      {diagnosticResults && (
        <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
          <div className="bg-amber-50 border-b border-amber-200 p-4">
            <h3 className="font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-amber-600" />
              Resultados del Diagnóstico
              <span className="text-sm font-normal text-gray-500">
                ({diagnosticResults.timestamp})
              </span>
            </h3>
          </div>

          {/* Sospechosos */}
          {diagnosticResults.suspects?.length > 0 && (
            <div className="p-4 bg-red-50 border-b">
              <h4 className="font-semibold text-red-700 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                ⚠️ SOSPECHOSOS IDENTIFICADOS ({diagnosticResults.suspects.length})
              </h4>
              <div className="space-y-3">
                {diagnosticResults.suspects.map((suspect, idx) => (
                  <div key={idx} className="bg-white rounded-lg p-3 border border-red-200">
                    <p className="font-mono font-semibold text-red-700">{suspect.job_name}</p>
                    {suspect.step_name && (
                      <p className="text-sm"><strong>Step:</strong> {suspect.step_name}</p>
                    )}
                    {suspect.schedule_name && (
                      <p className="text-sm"><strong>Schedule:</strong> {suspect.schedule_name}</p>
                    )}
                    {suspect.frequency && (
                      <p className="text-sm text-red-600"><strong>Frecuencia:</strong> {suspect.frequency}</p>
                    )}
                    {suspect.owner && (
                      <p className="text-sm"><strong>Owner:</strong> {suspect.owner}</p>
                    )}
                    {suspect.reason && (
                      <p className="text-sm text-red-700 font-semibold">{suspect.reason}</p>
                    )}
                    {suspect.command_preview && (
                      <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                        {suspect.command_preview}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Jobs con schedules frecuentes */}
          {diagnosticResults.diagnostic_results?.frequent_schedules_5_10_min?.length > 0 && (
            <div className="p-4 border-b">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Clock className="w-5 h-5 text-amber-600" />
                Jobs con Schedule cada 5-10 minutos
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-2">Job</th>
                      <th className="text-left p-2">Schedule</th>
                      <th className="text-left p-2">Intervalo</th>
                      <th className="text-left p-2">Owner</th>
                    </tr>
                  </thead>
                  <tbody>
                    {diagnosticResults.diagnostic_results.frequent_schedules_5_10_min.map((sched, idx) => (
                      <tr key={idx} className={`border-t ${sched.freq_subday_interval === 5 ? 'bg-red-50' : ''}`}>
                        <td className="p-2 font-mono">{sched.job_name}</td>
                        <td className="p-2">{sched.schedule_name}</td>
                        <td className="p-2">
                          <span className={sched.freq_subday_interval === 5 ? 'text-red-600 font-bold' : ''}>
                            Cada {sched.freq_subday_interval} min
                          </span>
                        </td>
                        <td className="p-2">{sched.owner_name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Steps sospechosos */}
          {diagnosticResults.diagnostic_results?.suspicious_job_steps?.length > 0 && (
            <div className="p-4 border-b">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Database className="w-5 h-5 text-red-600" />
                Steps que mencionan tablas afectadas
              </h4>
              <div className="space-y-2">
                {diagnosticResults.diagnostic_results.suspicious_job_steps.map((step, idx) => (
                  <div key={idx} className="bg-red-50 rounded-lg p-3 border border-red-200">
                    <p className="font-mono font-semibold">{step.job_name} → {step.step_name}</p>
                    <p className="text-sm text-gray-600">Owner: {step.owner_name} | DB: {step.database_name}</p>
                    <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-32">
                      {step.command}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Resumen */}
          <div className="p-4 bg-gray-50">
            <h4 className="font-semibold mb-2">Resumen</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Jobs Activos</p>
                <p className="text-2xl font-bold">{diagnosticResults.diagnostic_results?.active_jobs_count || 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Steps Sospechosos</p>
                <p className="text-2xl font-bold text-red-600">
                  {diagnosticResults.diagnostic_results?.suspicious_job_steps?.length || 0}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Schedules 5-10min</p>
                <p className="text-2xl font-bold text-amber-600">
                  {diagnosticResults.diagnostic_results?.frequent_schedules_5_10_min?.length || 0}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Ejecutado por</p>
                <p className="font-mono text-sm">{diagnosticResults.executed_by}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instrucciones */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-800 mb-2">Instrucciones de Uso</h4>
        <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
          <li>Registre la contraseña SA en el formulario seguro</li>
          <li>Pruebe la conexión para verificar acceso a msdb</li>
          <li>Ejecute el diagnóstico para identificar el Ejecutor B</li>
          <li>Revise los sospechosos identificados (Jobs cada 5 minutos)</li>
          <li>NO modifique los jobs sin autorización previa</li>
          <li>Elimine la credencial después de completar el diagnóstico</li>
        </ol>
      </div>
    </div>
  );
};

export default DBACredentialManager;
