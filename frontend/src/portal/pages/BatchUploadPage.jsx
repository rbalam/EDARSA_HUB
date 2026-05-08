/**
 * BatchUploadPage - Carga Masiva de Facturas
 * FASE AUTH-SECURITY-01: Ya no recibe token, usa cookie httpOnly
 */
import React from 'react';
import { FolderUp, Upload, FileText, AlertCircle } from 'lucide-react';

export default function BatchUploadPage({ supplier, onNavigate }) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Carga Masiva de Facturas</h1>
        <p className="text-zinc-500">Sube múltiples facturas XML en un solo proceso</p>
      </div>

      {/* Zona de carga */}
      <div className="bg-white rounded-xl border p-8">
        <div className="border-2 border-dashed border-zinc-300 rounded-lg p-12 text-center hover:border-zinc-400 transition-colors">
          <FolderUp className="h-16 w-16 mx-auto text-zinc-300 mb-4" />
          <h3 className="text-lg font-medium text-zinc-700 mb-2">
            Arrastra archivos XML aquí
          </h3>
          <p className="text-zinc-500 mb-4">
            o haz clic para seleccionar archivos
          </p>
          <input
            type="file"
            multiple
            accept=".xml"
            className="hidden"
            id="batch-upload"
          />
          <label
            htmlFor="batch-upload"
            className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 text-white rounded-lg cursor-pointer hover:bg-zinc-800"
          >
            <Upload className="h-5 w-5" />
            Seleccionar archivos XML
          </label>
        </div>
      </div>

      {/* Instrucciones */}
      <div className="bg-white rounded-xl border p-6">
        <h2 className="font-semibold text-zinc-900 mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-zinc-400" />
          Instrucciones
        </h2>
        <ul className="space-y-2 text-sm text-zinc-600">
          <li className="flex items-start gap-2">
            <span className="text-zinc-400">•</span>
            Selecciona múltiples archivos XML de tus facturas CFDI
          </li>
          <li className="flex items-start gap-2">
            <span className="text-zinc-400">•</span>
            Todos los archivos deben tener el RFC de emisor correcto ({supplier?.rfc})
          </li>
          <li className="flex items-start gap-2">
            <span className="text-zinc-400">•</span>
            Se validará que las facturas no estén duplicadas
          </li>
          <li className="flex items-start gap-2">
            <span className="text-zinc-400">•</span>
            El proceso puede tomar varios minutos dependiendo de la cantidad de archivos
          </li>
        </ul>
      </div>

      {/* Nota */}
      <div className="bg-yellow-50 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
        <div>
          <p className="font-medium text-yellow-800">Módulo en desarrollo</p>
          <p className="text-sm text-yellow-700 mt-1">
            La carga masiva estará disponible próximamente. Por ahora, puedes subir facturas 
            una por una desde la sección "Subir Factura".
          </p>
        </div>
      </div>
    </div>
  );
}
