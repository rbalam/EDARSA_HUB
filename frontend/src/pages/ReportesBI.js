import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { BarChart3, TrendingUp, FileBarChart, Brain, Target, Construction } from 'lucide-react';

export default function ReportesBI() {
  const modulos = [
    { nombre: 'Informes Automáticos', descripcion: 'Generación programada de reportes', icon: FileBarChart },
    { nombre: 'Análisis Predictivo', descripcion: 'Proyecciones basadas en datos históricos', icon: Brain },
    { nombre: 'KPIs en Tiempo Real', descripcion: 'Indicadores clave actualizados', icon: Target },
    { nombre: 'Dashboards Personalizados', descripcion: 'Tableros configurables por usuario', icon: BarChart3 },
  ];

  return (
    <div className="p-6" data-testid="reportes-bi-page">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Reportes e Inteligencia de Negocios</h1>
        <p className="text-zinc-500">Análisis avanzado y toma de decisiones basada en datos</p>
      </div>

      {/* Banner de próximamente */}
      <Card className="mb-6 border-2 border-dashed border-purple-300 bg-purple-50">
        <CardContent className="py-8 text-center">
          <Construction className="h-16 w-16 text-purple-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-purple-700 mb-2">Módulo en Desarrollo</h2>
          <p className="text-purple-600">
            Este módulo estará disponible próximamente. Ofrecerá análisis avanzado,
            proyecciones y reportes automatizados.
          </p>
        </CardContent>
      </Card>

      {/* Preview de funcionalidades */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {modulos.map((modulo) => {
          const Icon = modulo.icon;
          return (
            <Card key={modulo.nombre} className="border opacity-60 hover:opacity-80 transition-opacity">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-zinc-100">
                    <Icon className="h-5 w-5 text-zinc-500" />
                  </div>
                  <CardTitle className="text-sm font-medium">{modulo.nombre}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-zinc-400">{modulo.descripcion}</p>
                <span className="inline-block mt-2 text-xs px-2 py-1 bg-zinc-100 text-zinc-500 rounded">
                  Próximamente
                </span>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
