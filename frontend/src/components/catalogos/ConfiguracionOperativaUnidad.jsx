/**
 * Configuración Operativa de Unidad de Negocio
 * =============================================
 * 
 * Componente para configurar turnos operativos y reglas de Ventas del Día
 * por unidad de negocio.
 * 
 * UBICACIÓN: Catálogos → Unidades de Negocio → Configuración Operativa
 * 
 * FUNCIONALIDADES:
 * - Configurar turnos (DESAYUNO, COMIDA_CENA)
 * - Activar/desactivar turnos por unidad
 * - Configurar horarios por turno
 * - Probar cálculo de FechaOperacion
 * - Zona horaria: America/Mexico_City
 */

import React, { useState, useEffect } from 'react';
import {
  Clock,
  Sun,
  Moon,
  Save,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Play,
  Calendar,
  Settings,
  Loader2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const ConfiguracionOperativaUnidad = ({ unidadId, onClose, onSave }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState(null);
  const [config, setConfig] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [testDateTime, setTestDateTime] = useState('');

  // Cargar configuración
  useEffect(() => {
    if (unidadId) {
      loadConfig();
    }
  }, [unidadId]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/admin/unidades-negocio/${unidadId}/configuracion-operativa`
      );
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        setMessage({ type: 'error', text: 'Error cargando configuración' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    setLoading(false);
  };

  const handleTurnoChange = (turnoCodigo, field, value) => {
    setConfig(prev => ({
      ...prev,
      turnos: prev.turnos.map(t =>
        t.turno_codigo === turnoCodigo ? { ...t, [field]: value } : t
      )
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const response = await fetch(
        `${API_URL}/api/admin/unidades-negocio/${unidadId}/configuracion-operativa`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            unidad_negocio_id: unidadId,
            turnos: config.turnos,
            usa_configuracion_operativa: true
          })
        }
      );

      if (response.ok) {
        setMessage({ type: 'success', text: 'Configuración guardada correctamente' });
        if (onSave) onSave();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Error guardando' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const body = testDateTime
        ? { fecha_hora_mexico: testDateTime }
        : {};

      const response = await fetch(
        `${API_URL}/api/admin/unidades-negocio/${unidadId}/probar-fecha-operacion`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTestResult(data);
      } else {
        setMessage({ type: 'error', text: 'Error probando FechaOperacion' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error de conexión' });
    }
    setTesting(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2">Cargando configuración...</span>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="p-8 text-center text-red-600">
        No se pudo cargar la configuración
      </div>
    );
  }

  const desayuno = config.turnos?.find(t => t.turno_codigo === 'DESAYUNO');
  const comidaCena = config.turnos?.find(t => t.turno_codigo === 'COMIDA_CENA');

  return (
    <div className="bg-white rounded-lg shadow-lg max-w-2xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-t-lg p-4 text-white">
        <div className="flex items-center gap-2">
          <Settings className="w-6 h-6" />
          <div>
            <h2 className="text-lg font-semibold">Configuración Operativa</h2>
            <p className="text-blue-100 text-sm">{unidadId} - Turnos y Ventas del Día</p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Mensaje */}
        {message && (
          <div className={`p-3 rounded-lg flex items-center gap-2 ${
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

        {/* Info de Zona Horaria */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center gap-2 text-blue-700">
            <Clock className="w-4 h-4" />
            <span className="text-sm font-medium">
              Zona horaria oficial: <strong>America/Mexico_City</strong>
            </span>
          </div>
        </div>

        {/* Turno DESAYUNO */}
        {desayuno && (
          <div className={`border rounded-lg p-4 ${desayuno.activo ? 'border-amber-300 bg-amber-50' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sun className="w-5 h-5 text-amber-500" />
                <span className="font-semibold">Desayuno</span>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={desayuno.activo}
                  onChange={(e) => handleTurnoChange('DESAYUNO', 'activo', e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                />
                <span className="text-sm">{desayuno.activo ? 'Activo' : 'Inactivo'}</span>
              </label>
            </div>

            {desayuno.activo && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hora Inicio
                  </label>
                  <input
                    type="time"
                    value={desayuno.hora_inicio?.substring(0, 5) || '07:00'}
                    onChange={(e) => handleTurnoChange('DESAYUNO', 'hora_inicio', e.target.value + ':00')}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hora Fin
                  </label>
                  <input
                    type="time"
                    value={desayuno.hora_fin?.substring(0, 5) || '13:00'}
                    onChange={(e) => handleTurnoChange('DESAYUNO', 'hora_fin', e.target.value + ':00')}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Turno COMIDA/CENA */}
        {comidaCena && (
          <div className={`border rounded-lg p-4 ${comidaCena.activo ? 'border-indigo-300 bg-indigo-50' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Moon className="w-5 h-5 text-indigo-500" />
                <span className="font-semibold">Comida / Cena</span>
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={comidaCena.activo}
                  onChange={(e) => handleTurnoChange('COMIDA_CENA', 'activo', e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm">{comidaCena.activo ? 'Activo' : 'Inactivo'}</span>
              </label>
            </div>

            {comidaCena.activo && (
              <>
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Hora Inicio
                    </label>
                    <input
                      type="time"
                      value={comidaCena.hora_inicio?.substring(0, 5) || '13:00'}
                      onChange={(e) => handleTurnoChange('COMIDA_CENA', 'hora_inicio', e.target.value + ':00')}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Hora Fin
                    </label>
                    <input
                      type="time"
                      value={comidaCena.hora_fin?.substring(0, 5) || '06:00'}
                      onChange={(e) => handleTurnoChange('COMIDA_CENA', 'hora_fin', e.target.value + ':00')}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={comidaCena.cruza_medianoche}
                    onChange={(e) => handleTurnoChange('COMIDA_CENA', 'cruza_medianoche', e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-indigo-600"
                  />
                  <span className="text-sm text-gray-600">Cruza medianoche</span>
                </label>
              </>
            )}
          </div>
        )}

        {/* Probar FechaOperacion */}
        <div className="border rounded-lg p-4 bg-gray-50">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Play className="w-5 h-5 text-green-600" />
            Probar Cálculo de FechaOperacion
          </h3>
          
          <div className="flex gap-2 mb-3">
            <input
              type="datetime-local"
              value={testDateTime}
              onChange={(e) => setTestDateTime(e.target.value.replace('T', ' ') + ':00')}
              className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
              placeholder="Dejar vacío para hora actual"
            />
            <button
              onClick={handleTest}
              disabled={testing}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              {testing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Probar
            </button>
          </div>

          {testResult && (
            <div className="bg-white rounded-lg border p-3 space-y-2 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-gray-500">Fecha/Hora Input:</span>
                  <p className="font-mono">{testResult.fecha_hora_input_mexico}</p>
                </div>
                <div>
                  <span className="text-gray-500">FechaOperacion:</span>
                  <p className="font-mono font-bold text-lg text-green-700">
                    {testResult.fecha_operacion_calculada}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Turno Detectado:</span>
                  <p className={`font-semibold ${
                    testResult.turno_detectado === 'DESAYUNO' ? 'text-amber-600' :
                    testResult.turno_detectado === 'COMIDA_CENA' ? 'text-indigo-600' :
                    'text-gray-400'
                  }`}>
                    {testResult.turno_detectado || 'Ninguno'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Estado:</span>
                  <p className={`font-semibold ${
                    testResult.estado_operativo === 'CERRADO' ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {testResult.estado_operativo}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Ventana:</span>
                  <p className="font-mono">
                    {testResult.window_start} - {testResult.window_end}
                    {testResult.cruza_medianoche && ' (cruza)'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Timezone:</span>
                  <p className="font-mono text-blue-600">{testResult.timezone_usada}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Botones */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <button
            onClick={loadConfig}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Recargar
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Guardar Configuración
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfiguracionOperativaUnidad;
