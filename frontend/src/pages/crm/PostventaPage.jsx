import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Shield, CheckCircle, Clock, AlertTriangle, RefreshCw, MessageSquare } from 'lucide-react';
import api from '@/lib/api';

const PostventaPage = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = async () => {
    try {
      const response = await api.get('/crm/postventa/tickets');
      setTickets(response.data?.tickets || []);
    } catch (error) {
      console.error('Error cargando tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPrioridadBadge = (prioridad) => {
    const prioridades = {
      'alta': 'bg-red-500/20 text-red-400',
      'media': 'bg-yellow-500/20 text-yellow-400',
      'baja': 'bg-green-500/20 text-green-400'
    };
    return <Badge className={prioridades[prioridad] || prioridades.media}>{prioridad?.toUpperCase()}</Badge>;
  };

  const getEstadoBadge = (estado) => {
    const estados = {
      'abierto': { color: 'bg-blue-500/20 text-blue-400', icon: Clock },
      'en_proceso': { color: 'bg-yellow-500/20 text-yellow-400', icon: RefreshCw },
      'resuelto': { color: 'bg-green-500/20 text-green-400', icon: CheckCircle },
      'escalado': { color: 'bg-red-500/20 text-red-400', icon: AlertTriangle }
    };
    const config = estados[estado] || estados.abierto;
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
          <h1 className="text-2xl font-bold text-zinc-900">Postventa</h1>
          <p className="text-zinc-500">Gestión de tickets y soporte al cliente</p>
        </div>
        <Button onClick={fetchTickets}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      <div className="grid gap-4">
        {tickets.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Shield className="h-12 w-12 mx-auto text-zinc-300 mb-4" />
              <p className="text-zinc-500">No hay tickets de soporte registrados</p>
            </CardContent>
          </Card>
        ) : (
          tickets.map((ticket) => (
            <Card key={ticket.id}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-zinc-400" />
                    <CardTitle className="text-lg">#{ticket.numero} - {ticket.asunto}</CardTitle>
                  </div>
                  <div className="flex gap-2">
                    {getPrioridadBadge(ticket.prioridad)}
                    {getEstadoBadge(ticket.estado)}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-zinc-500">Cliente:</span>
                    <p className="font-medium">{ticket.cliente}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Asignado:</span>
                    <p className="font-medium">{ticket.asignado_a || 'Sin asignar'}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Fecha Apertura:</span>
                    <p className="font-medium">{ticket.fecha_apertura}</p>
                  </div>
                  <div>
                    <span className="text-zinc-500">Tipo:</span>
                    <p className="font-medium">{ticket.tipo}</p>
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

export default PostventaPage;
