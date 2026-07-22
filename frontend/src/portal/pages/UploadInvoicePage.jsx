/**
 * Portal Proveedores - Subir Factura
 * FASE AUTH-SECURITY-01: Usa credentials: 'include' para cookie httpOnly
 */
import React, { useState, useRef } from 'react';
import { toast } from 'sonner';
import { Upload, FileText, File, X, CheckCircle, AlertCircle } from 'lucide-react';

const UPLOAD_DISABLED_MESSAGE = 'Carga CFDI pendiente de flujo SQL canónico autorizado.';

export default function UploadInvoicePage({ supplier, onNavigate }) {
  const [xmlFile, setXmlFile] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const xmlInputRef = useRef(null);
  const pdfInputRef = useRef(null);

  const handleXmlSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.xml')) {
        toast.error('Solo se permiten archivos XML');
        return;
      }
      setXmlFile(file);
      setUploadResult(null);
    }
  };

  const handlePdfSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        toast.error('Solo se permiten archivos PDF');
        return;
      }
      setPdfFile(file);
    }
  };

  const handleUpload = async () => {
    if (!xmlFile) {
      toast.error('Selecciona un archivo XML');
      return;
    }

    setUploading(false);
    setUploadResult({
      success: false,
      message: UPLOAD_DISABLED_MESSAGE
    });
    toast.error(UPLOAD_DISABLED_MESSAGE);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(value || 0);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-zinc-800">Subir Factura</h2>
        <p className="text-zinc-500 mt-1">Recepción CFDI pendiente de flujo SQL canónico</p>
      </div>

      {/* Área de carga */}
      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-6">
        {/* XML (Requerido) */}
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-2">
            Archivo XML (CFDI) <span className="text-red-500">*</span>
          </label>
          
          {!xmlFile ? (
            <div
              onClick={() => xmlInputRef.current?.click()}
              className="border-2 border-dashed border-zinc-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
            >
              <Upload className="h-10 w-10 mx-auto text-zinc-400 mb-3" />
              <p className="text-zinc-600">Haz clic para seleccionar tu XML</p>
              <p className="text-xs text-zinc-400 mt-1">o arrastra y suelta aquí</p>
            </div>
          ) : (
            <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl p-4">
              <FileText className="h-8 w-8 text-green-600" />
              <div className="flex-1">
                <p className="font-medium text-green-800">{xmlFile.name}</p>
                <p className="text-xs text-green-600">{(xmlFile.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                onClick={() => {
                  setXmlFile(null);
                  if (xmlInputRef.current) xmlInputRef.current.value = '';
                }}
                className="p-2 hover:bg-green-100 rounded-lg"
              >
                <X className="h-4 w-4 text-green-600" />
              </button>
            </div>
          )}
          
          <input
            ref={xmlInputRef}
            type="file"
            accept=".xml"
            onChange={handleXmlSelect}
            className="hidden"
          />
        </div>

        {/* PDF (Opcional) */}
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-2">
            Archivo PDF (Representación impresa) <span className="text-zinc-400">- Opcional</span>
          </label>
          
          {!pdfFile ? (
            <div
              onClick={() => pdfInputRef.current?.click()}
              className="border-2 border-dashed border-zinc-200 rounded-xl p-6 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
            >
              <File className="h-8 w-8 mx-auto text-zinc-300 mb-2" />
              <p className="text-zinc-500 text-sm">Agregar PDF (opcional)</p>
            </div>
          ) : (
            <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-xl p-4">
              <File className="h-8 w-8 text-blue-600" />
              <div className="flex-1">
                <p className="font-medium text-blue-800">{pdfFile.name}</p>
                <p className="text-xs text-blue-600">{(pdfFile.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                onClick={() => {
                  setPdfFile(null);
                  if (pdfInputRef.current) pdfInputRef.current.value = '';
                }}
                className="p-2 hover:bg-blue-100 rounded-lg"
              >
                <X className="h-4 w-4 text-blue-600" />
              </button>
            </div>
          )}
          
          <input
            ref={pdfInputRef}
            type="file"
            accept=".pdf"
            onChange={handlePdfSelect}
            className="hidden"
          />
        </div>

        {/* Botón de subir */}
        <button
          onClick={handleUpload}
          disabled={!xmlFile || uploading}
          className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Procesando...
            </>
          ) : (
            <>
              <Upload className="h-5 w-5" />
              Registrar en EDARSAHUB
            </>
          )}
        </button>
      </div>

      {/* Resultado de la carga */}
      {uploadResult && (
        <div className={`rounded-xl p-6 ${uploadResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-start gap-3">
            {uploadResult.success ? (
              <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-6 w-6 text-red-600 flex-shrink-0" />
            )}
            <div className="flex-1">
              <p className={`font-semibold ${uploadResult.success ? 'text-green-800' : 'text-red-800'}`}>
                {uploadResult.message}
              </p>
              
              {uploadResult.success && uploadResult.invoice && (
                <div className="mt-3 space-y-1 text-sm text-green-700">
                  <p><strong>UUID:</strong> {uploadResult.invoice.uuid}</p>
                  <p><strong>Folio:</strong> {uploadResult.invoice.serie}{uploadResult.invoice.folio}</p>
                  <p><strong>Total:</strong> {formatCurrency(uploadResult.invoice.total)}</p>
                  <p><strong>Receptor:</strong> {uploadResult.invoice.receptor_nombre}</p>
                </div>
              )}
            </div>
          </div>
          
          {uploadResult.success && (
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => setUploadResult(null)}
                className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
              >
                Subir otra factura
              </button>
              <button
                onClick={() => onNavigate('invoices')}
                className="flex-1 bg-white text-green-700 py-2 rounded-lg border border-green-300 hover:bg-green-50"
              >
                Ver mis facturas
              </button>
            </div>
          )}
        </div>
      )}

      {/* Información */}
      <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
        <h4 className="font-semibold text-blue-800 mb-2">Información importante</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Solo se aceptan facturas CFDI 3.3 y 4.0</li>
          <li>• El RFC del emisor debe coincidir con tu RFC registrado</li>
          <li>• La recepción directa requiere storage canónico y validación SQL</li>
          <li>• No se envían archivos a endpoints deshabilitados</li>
        </ul>
      </div>
    </div>
  );
}
