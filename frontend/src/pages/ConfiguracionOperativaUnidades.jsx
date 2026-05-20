/**
 * Página de Configuración Operativa de Unidades
 * ==============================================
 * 
 * Permite configurar turnos operativos y reglas de Ventas del Día
 * por unidad de negocio.
 * 
 * UBICACIÓN: Sistema → Configuración Operativa Unidades
 * ACCESO: SuperAdministrador, Administrador
 * 
 * FUNCIONALIDADES:
 * - Ver todas las unidades con su configuración
 * - Editar turnos (DESAYUNO, COMIDA_CENA)
 * - Probar cálculo de FechaOperacion
 */

import React, { useState, useEffect } from 'react';
import {
  Settings,
  Sun,
  Moon,
  Clock,
  CheckCircle,
  XCircle,
  Edit2,
  Play,
  Loader2,
  RefreshCw,
  Building2,
  Calendar,
  AlertCircle,
  Save
} from 'lucide-react';
import ConfiguracionOperativaUnidad from '../components/catalogos/ConfiguracionOperativaUnidad';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ConfiguracionOperativaUnidades = () => {
  const [loading, setLoading] = useState(true);
  const [unidades, setUnidades] = useState({});
  const [selectedUnidad, setSelectedUnidad] = useState(null);
  const [showEditor, setShowEditor] = useState(false);
  const [message, setMessage] = useState(null);
  const [testingUnidad, setTestingUnidad] = useState(null);
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    loadUnidades();
  }, []);

  const loadUnidades = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/admin/unidades-negocio/todas/configuracion-operativa`
      );
      if (response.ok) {
        const data = await response.json();
        setUnidades(data.unidades || {});
      } else {
        setMessage({ type: 'error', text: 'Error cargando configuraciones' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    setLoading(false);
  };

  const handleTestUnidad = async (unidadId) => {
    setTestingUnidad(unidadId);
    try {
      const response = await fetch(
        `${API_URL}/api/admin/unidades-negocio/${unidadId}/probar-fecha-operacion`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        }
      );
      if (response.ok) {
        const data = await response.json();
        setTestResults(prev => ({ ...prev, [unidadId]: data }));
      }
    } catch (error) {
      console.error('Error testing:', error);
    }
    setTestingUnidad(null);
  };

  const handleEdit = (unidadId) => {
    setSelectedUnidad(unidadId);
    setShowEditor(true);
  };

  const handleSave = () => {
    loadUnidades();
    setShowEditor(false);
    setMessage({ type: 'success', text: 'Configuración actualizada' });
    setTimeout(() => setMessage(null), 3000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Cargando configuraciones...</span>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Configuración Operativa de Unidades
              </h1>
              <p className="text-gray-500">
                Turnos y reglas de Ventas del Día por unidad de negocio
              </p>
            </div>
          </div>
          <button
            onClick={loadUnidades}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Recargar
          </button>
        </div>
      </div>

      {/* Mensaje */}
      {message && (
        <div className={`mb-4 p-3 rounded-lg flex items-center gap-2 ${
          message.type === 'success'
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          {message.text}
        </div>
      )}

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <Clock className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <p className="font-semibold text-blue-800">Zona Horaria Oficial: America/Mexico_City</p>
            <p className="text-sm text-blue-600 mt-1">
              Todas las FechaOperacion se calculan usando la hora de México, no la hora del servidor local.
            </p>
          </div>
        </div>
      </div>

      {/* Lista de Unidades */}
      <div className="grid gap-4">
        {Object.entries(unidades).map(([unidadId, config]) => {
          const testResult = testResults[unidadId];
          
          return (
            <div
              key={unidadId}
              className="bg-white rounded-lg border shadow-sm overflow-hidden"
            >
              <div className="p-4">
                <div className="flex items-center justify-between">
                  {/* Info de Unidad */}
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-gray-500" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{unidadId}</h3>
                      <div className="flex items-center gap-3 mt-1">
                        {/* Badge Desayuno */}
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                          config.tiene_desayuno_activo
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-gray-100 text-gray-400'
                        }`}>
                          <Sun className="w-3 h-3" />
                          Desayuno {config.tiene_desayuno_activo ? 'Activo' : 'Inactivo'}
                        </span>
                        
                        {/* Badge Comida/Cena */}
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                          config.tiene_comida_cena_activo
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-gray-100 text-gray-400'
                        }`}>
                          <Moon className="w-3 h-3" />
                          Comida/Cena {config.tiene_comida_cena_activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Acciones */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleTestUnidad(unidadId)}
                      disabled={testingUnidad === unidadId}
                      className="px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 flex items-center gap-1"
                    >
                      {testingUnidad === unidadId ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                      Probar
                    </button>
                    <button
                      onClick={() => handleEdit(unidadId)}
                      className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-1"
                    >
                      <Edit2 className="w-4 h-4" />
                      Configurar
                    </button>
                  </div>
                </div>

                {/* Resultado del Test */}
                {testResult && (
                  <div className="mt-4 pt-4 border-t bg-gray-50 -mx-4 -mb-4 px-4 pb-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Hora México (actual)</p>
                        <p className="font-mono">{testResult.fecha_hora_input_mexico}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">FechaOperacion</p>
                        <p className="font-mono font-bold text-lg text-green-700">
                          {testResult.fecha_operacion_calculada}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Turno</p>
                        <p className={`font-semibold ${
                          testResult.turno_detectado === 'DESAYUNO' ? 'text-amber-600' :
                          testResult.turno_detectado === 'COMIDA_CENA' ? 'text-indigo-600' :
                          'text-gray-400'
                        }`}>
                          {testResult.turno_detectado || 'Ninguno'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Estado</p>
                        <p className={`font-semibold ${
                          testResult.estado_operativo === 'CERRADO' ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {testResult.estado_operativo}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Turnos Configurados */}
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                  {config.turnos?.map(turno => (
                    <div
                      key={turno.turno_codigo}
                      className={`p-3 rounded-lg border ${
                        turno.activo
                          ? turno.turno_codigo === 'DESAYUNO'
                            ? 'bg-amber-50 border-amber-200'
                            : 'bg-indigo-50 border-indigo-200'
                          : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {turno.turno_codigo === 'DESAYUNO' ? (
                            <Sun className={`w-4 h-4 ${turno.activo ? 'text-amber-500' : 'text-gray-400'}`} />
                          ) : (
                            <Moon className={`w-4 h-4 ${turno.activo ? 'text-indigo-500' : 'text-gray-400'}`} />
                          )}
                          <span className={`font-medium ${turno.activo ? '' : 'text-gray-400'}`}>
                            {turno.turno_nombre}
                          </span>
                        </div>
                        {turno.activo ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-gray-300" />
                        )}
                      </div>
                      <p className="text-sm mt-1 font-mono">
                        {turno.hora_inicio} - {turno.hora_fin}
                        {turno.cruza_medianoche && (
                          <span className="ml-2 text-xs text-gray-500">(cruza medianoche)</span>
                        )}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal de Edición */}
      {showEditor && selectedUnidad && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="max-h-[90vh] overflow-y-auto">
            <ConfiguracionOperativaUnidad
              unidadId={selectedUnidad}
              onClose={() => setShowEditor(false)}
              onSave={handleSave}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfiguracionOperativaUnidades;
