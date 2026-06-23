import { Card, CardContent } from '@/components/ui/card';
import { Clock } from 'lucide-react';

const ComingSoonPage = ({ title = 'Módulo en preparación', description }) => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">{title}</h1>
        <p className="text-zinc-500">
          {description || 'Esta funcionalidad ya está registrada en el sistema y se encuentra en preparación operativa.'}
        </p>
      </div>

      <Card>
        <CardContent className="py-16 text-center">
          <Clock className="h-14 w-14 mx-auto text-zinc-300 mb-4" />
          <h3 className="text-xl font-semibold text-zinc-700 mb-2">Próximamente</h3>
          <p className="text-zinc-500 max-w-lg mx-auto">
            El acceso permanecerá visible para control de permisos, menú y planeación, pero la operación todavía no está habilitada.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ComingSoonPage;
