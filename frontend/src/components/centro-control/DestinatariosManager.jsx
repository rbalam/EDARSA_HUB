/**
 * DestinatariosManager - Gestión de destinatarios de alertas
 */
import React, { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import logger from '../../services/logger';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Mail, MessageSquare, Trash2, Plus, Phone, Bell, Send, Settings
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function DestinatariosManager({ headers }) {
  const [destinatarios, setDestinatarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nuevoDestinatario, setNuevoDestinatario] = useState({ 
    tipo: 'email', 
    destinatario: '', 
    nombre: '' 
  });
  const [notificacionesConfig, setNotificacionesConfig] = useState(null);

  const fetchDestinatarios = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/centro-control/destinatarios`, { headers });
      if (res.ok) {
        const data = await res.json();
        setDestinatarios(data.destinatarios || []);
      }
    } catch (err) {
      logger.error('Error fetching destinatarios:', err);
    }
    setLoading(false);
  }, [headers]);

  const fetchConfig = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/centro-control/notificaciones/config`, { headers });
      if (res.ok) {
        setNotificacionesConfig(await res.json());
      }
    } catch (err) {
      logger.error('Error fetching notificaciones config:', err);
    }
  }, [headers]);

  useEffect(() => {
    fetchDestinatarios();
    fetchConfig();
  }, [fetchDestinatarios, fetchConfig]);

  const agregarDestinatario = async () => {
    if (!nuevoDestinatario.destinatario.trim()) {
      toast.error('Ingrese un destinatario válido');
      return;
    }
    
    try {
      const res = await fetch(`${API_URL}/api/centro-control/destinatarios`, {
        method: 'POST',
        headers,
        body: JSON.stringify(nuevoDestinatario)
      });
      
      if (res.ok) {
        toast.success('Destinatario agregado correctamente');
        setNuevoDestinatario({ tipo: 'email', destinatario: '', nombre: '' });
        fetchDestinatarios();
        fetchConfig();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Error al agregar destinatario');
      }
    } catch (err) {
      toast.error('Error de conexión');
    }
  };

  const eliminarDestinatario = async (id) => {
    try {
      const res = await fetch(`${API_URL}/api/centro-control/destinatarios/${id}`, {
        method: 'DELETE',
        headers
      });
      
      if (res.ok) {
        toast.success('Destinatario eliminado');
        fetchDestinatarios();
        fetchConfig();
      }
    } catch (err) {
      toast.error('Error eliminando destinatario');
    }
  };

  const enviarPruebaWhatsApp = async (telefono) => {
    try {
      toast.loading('Enviando mensaje de prueba...');
      const res = await fetch(`${API_URL}/api/centro-control/test-whatsapp`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ telefono })
      });
      toast.dismiss();
      
      if (res.ok) {
        toast.success('Mensaje de prueba enviado');
      } else {
        toast.error('Error al enviar mensaje de prueba');
      }
    } catch (err) {
      toast.dismiss();
      toast.error('Error al enviar WhatsApp de prueba');
    }
  };

  const TipoIcon = ({ tipo }) => {
    switch (tipo) {
      case 'email': return <Mail className="w-4 h-4" />;
      case 'whatsapp': return <MessageSquare className="w-4 h-4 text-green-500" />;
      case 'sms': return <Phone className="w-4 h-4 text-blue-500" />;
      default: return <Bell className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Resumen de Configuración */}
      {notificacionesConfig && (
        <Card className="bg-zinc-800/50 border-zinc-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Settings className="w-4 h-4" /> Configuración Actual
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-zinc-500">Email</p>
                <p className="text-white">{notificacionesConfig.email_count || 0} destinos</p>
              </div>
              <div>
                <p className="text-zinc-500">WhatsApp</p>
                <p className="text-white">{notificacionesConfig.whatsapp_count || 0} destinos</p>
              </div>
              <div>
                <p className="text-zinc-500">SMS</p>
                <p className="text-white">{notificacionesConfig.sms_count || 0} destinos</p>
              </div>
              <div>
                <p className="text-zinc-500">Notificaciones</p>
                <Badge variant={notificacionesConfig.enabled ? 'default' : 'secondary'}>
                  {notificacionesConfig.enabled ? 'Activas' : 'Pausadas'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agregar Nuevo Destinatario */}
      <Card className="bg-zinc-800/50 border-zinc-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Plus className="w-4 h-4" /> Agregar Destinatario
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex flex-col md:flex-row gap-3">
            <select
              value={nuevoDestinatario.tipo}
              onChange={(e) => setNuevoDestinatario(prev => ({ ...prev, tipo: e.target.value }))}
              className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white"
            >
              <option value="email">Email</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="sms">SMS</option>
            </select>
            <input
              type="text"
              value={nuevoDestinatario.nombre}
              onChange={(e) => setNuevoDestinatario(prev => ({ ...prev, nombre: e.target.value }))}
              placeholder="Nombre (opcional)"
              className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white flex-1"
            />
            <input
              type="text"
              value={nuevoDestinatario.destinatario}
              onChange={(e) => setNuevoDestinatario(prev => ({ ...prev, destinatario: e.target.value }))}
              placeholder={nuevoDestinatario.tipo === 'email' ? 'correo@ejemplo.com' : '+52 xxx xxx xxxx'}
              className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white flex-1"
            />
            <Button onClick={agregarDestinatario} size="sm">
              <Plus className="w-4 h-4 mr-1" /> Agregar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Destinatarios */}
      <Card className="bg-zinc-800/50 border-zinc-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Destinatarios Configurados</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {loading ? (
            <p className="text-zinc-500 text-sm py-4 text-center">Cargando...</p>
          ) : destinatarios.length === 0 ? (
            <p className="text-zinc-500 text-sm py-4 text-center">
              No hay destinatarios configurados
            </p>
          ) : (
            <div className="space-y-2">
              {destinatarios.map((d) => (
                <div 
                  key={d.id} 
                  className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <TipoIcon tipo={d.tipo} />
                    <div>
                      <p className="text-white text-sm">{d.destinatario}</p>
                      {d.nombre && <p className="text-zinc-500 text-xs">{d.nombre}</p>}
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {d.tipo}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    {d.tipo === 'whatsapp' && (
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => enviarPruebaWhatsApp(d.destinatario)}
                      >
                        <Send className="w-4 h-4" />
                      </Button>
                    )}
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => eliminarDestinatario(d.id)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default DestinatariosManager;
