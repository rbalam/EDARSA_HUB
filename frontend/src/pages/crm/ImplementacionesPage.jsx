import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Settings, CheckCircle, Clock, AlertTriangle, RefreshCw } from 'lucide-react';
import api from '@/lib/api';

const ImplementacionesPage = () => {
  const [implementaciones, setImplementaciones] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchImplementaciones();
  }, []);

  const fetchImplementaciones = async () => {
    try {
      const response = await api.get('/crm/implementaciones');
      setImplementaciones(response.data?.implementaciones || []);
    } catch (error) {
      console.error('Error cargando implementaciones:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEstadoBadge = (estado) => {
    const estados = {
      'pendiente': { color: 'bg-yellow-500/20 text-yellow-400', icon: Clock },
      'en_progreso': { color: 'bg-blue-500/20 text-blue-400', icon: RefreshCw },
      'completada': { color: 'bg-green-500/20 text-green-400', icon: CheckCircle },
      'bloqueada': { color: 'bg-red-500/20 text-red-400', icon: AlertTriangle }
    };
    const config = estados[estado] || estados.pendiente;
    const Icon = config.icon;
    return (
      <Badge className={config.color}>
        <Icon className="h-3 w-3 mr-1" />
        {estado?.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Implementaciones</h1>
          <p className="text-zinc-500">Gestión de implementaciones de proyectos CRM</p>
        </div>
        <Button onClick={fetchImplementaciones}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      <div className="grid gap-4">
        {implementaciones.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Settings className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <p className="text-zinc-500">No hay implementaciones registradas</p>
            </CardContent>
          </Card>
        ) : (
          implementaciones.map((impl) => (
            <Card key={impl.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{impl.nombre_proyecto}</CardTitle>
                  {getEstadoBadge(impl.estado)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-zinc-500">Cliente:</span>
                    <p className="font-medium">{impl.cliente}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Responsable:</span>
                    <p className="font-medium">{impl.responsable}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Fecha Inicio:</span>
                    <p className="font-medium">{impl.fecha_inicio}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Avance:</span>
                    <p className="font-medium">{impl.porcentaje_avance}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default ImplementacionesPage;
