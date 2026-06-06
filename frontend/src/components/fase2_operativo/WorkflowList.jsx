/**
 * WorkflowList.jsx - Lista de Workflows para Dashboard Operativo
 * CAB-003 | Fase 2A - Subfase 2A.8
 * EDARSA HUB
 */

import { useState } from 'react';
// FASE AUTH-V2-ALIGN: auth canónica vía Bearer (authedFetch) + cookie httpOnly
import { authedFetch } from '../../services/operativoApi';
import { 
  Activity, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  FileSearch,
  ChevronRight,
  RefreshCw,
  FileSpreadsheet,
  FileText,
  Loader2
} from 'lucide-react';
import logger from '../../services/logger';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

const estadoConfig = {
  pendiente: {
    label: 'Pendiente',
    icon: Clock,
    bgColor: 'bg-amber-100',
    textColor: 'text-amber-800',
  },
  en_proceso: {
    label: 'En Proceso',
    icon: Activity,
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-800',
  },
  en_revision: {
    label: 'En Revisión',
    icon: FileSearch,
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-800',
  },
  completado: {
    label: 'Completado',
    icon: CheckCircle2,
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
  },
  cancelado: {
    label: 'Cancelado',
    icon: XCircle,
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
  },
  escalado: {
    label: 'Escalado',
    icon: Activity,
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-800',
  },
};

const EstadoBadge = ({ estado }) => {
  const config = estadoConfig[estado] || {
    label: estado,
    icon: Activity,
    bgColor: 'bg-zinc-100',
    textColor: 'text-zinc-800',
  };
  const Icon = config.icon;

  return (
    <span 
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}
      data-testid={`workflow-estado-${estado}`}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
};

const WorkflowRow = ({ workflow, onClick, onDownloadExcel, onDownloadPdf, downloadingId }) => {
  const fechaFormateada = workflow.fecha_creacion 
    ? new Date(workflow.fecha_creacion).toLocaleDateString('es-MX', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : '-';

  const workflowId = workflow.id || workflow._id;

  const handleDownloadExcel = (e) => {
    e.stopPropagation();
    onDownloadExcel?.(workflowId);
  };

  const handleDownloadPdf = (e) => {
    e.stopPropagation();
    onDownloadPdf?.(workflowId);
  };

  const isDownloadingExcel = downloadingId === `excel-${workflowId}`;
  const isDownloadingPdf = downloadingId === `pdf-${workflowId}`;

  return (
    <tr 
      className="hover:bg-zinc-50 cursor-pointer transition-colors"
      onClick={() => onClick?.(workflow)}
      data-testid={`workflow-row-${workflowId}`}
    >
      <td className="px-4 py-3 text-sm font-mono text-zinc-600">
        {(workflowId || '').substring(0, 8)}...
      </td>
      <td className="px-4 py-3 text-sm">
        {workflow.procesado_id ? (
          <span className="font-mono text-zinc-700">
            {workflow.procesado_id.substring(0, 8)}...
          </span>
        ) : (
          <span className="text-zinc-400">-</span>
        )}
      </td>
      <td className="px-4 py-3">
        <EstadoBadge estado={workflow.estado} />
      </td>
      <td className="px-4 py-3 text-sm text-zinc-600">
        Ciclo {workflow.ciclo_actual || 1}
      </td>
      <td className="px-4 py-3 text-sm text-zinc-500">
        {fechaFormateada}
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-1">
          {/* Botón Excel */}
          <button
            onClick={handleDownloadExcel}
            disabled={isDownloadingExcel}
            className="p-1.5 text-zinc-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors disabled:opacity-50"
            title="Descargar Excel (detalle completo)"
            data-testid={`download-excel-${workflowId}`}
          >
            {isDownloadingExcel ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileSpreadsheet className="h-4 w-4" />
            )}
          </button>
          {/* Botón PDF */}
          <button
            onClick={handleDownloadPdf}
            disabled={isDownloadingPdf}
            className="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
            title="Descargar PDF (resumen ejecutivo)"
            data-testid={`download-pdf-${workflowId}`}
          >
            {isDownloadingPdf ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
          </button>
          <ChevronRight className="h-4 w-4 text-zinc-400 ml-1" />
        </div>
      </td>
    </tr>
  );
};

const WorkflowList = ({ 
  workflows, 
  loading, 
  error, 
  onRefresh, 
  onWorkflowClick,
  emptyMessage = 'No hay workflows disponibles'
}) => {
  const [downloadingId, setDownloadingId] = useState(null);

  // Helper para descargar archivos
  const downloadFile = async (workflowId, tipo, extension) => {
    try {
      setDownloadingId(`${tipo}-${workflowId}`);
      
      const response = await authedFetch(
        `${API_BASE}/api/v2/documentos/workflow/${workflowId}/${tipo}`
      );
      
      if (!response.ok) {
        throw new Error(`Error al descargar el archivo ${tipo.toUpperCase()}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `workflow_${workflowId}.${extension}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) filename = match[1];
      }
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      if (a && a.parentNode) { a.parentNode.removeChild(a); }
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      logger.error(`Error descargando ${tipo}:`, err);
      alert(`Error al descargar el archivo ${tipo.toUpperCase()}`);
    } finally {
      setDownloadingId(null);
    }
  };

  // Handlers específicos
  const handleDownloadExcel = (workflowId) => downloadFile(workflowId, 'excel', 'xlsx');
  const handleDownloadPdf = (workflowId) => downloadFile(workflowId, 'pdf', 'pdf');

  // Estado de carga
  if (loading) {
    return (
      <div 
        className="rounded-lg border border-zinc-200 bg-white overflow-hidden"
        data-testid="workflow-list-loading"
      >
        <div className="p-4 border-b border-zinc-200 bg-zinc-50">
          <div className="h-5 bg-zinc-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="p-4 space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={`skeleton-workflow-${i}`} className="h-12 bg-zinc-100 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  // Estado de error
  if (error) {
    return (
      <div 
        className="rounded-lg border border-red-200 bg-red-50 p-6 text-center"
        data-testid="workflow-list-error"
      >
        <XCircle className="h-8 w-8 text-red-400 mx-auto mb-2" />
        <p className="font-medium text-red-800">Error cargando workflows</p>
        <p className="text-sm text-red-600 mt-1">{error}</p>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
            data-testid="workflow-list-retry"
          >
            <RefreshCw className="h-4 w-4" />
            Reintentar
          </button>
        )}
      </div>
    );
  }

  // Estado vacío
  if (!workflows || workflows.length === 0) {
    return (
      <div 
        className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 text-center"
        data-testid="workflow-list-empty"
      >
        <Activity className="h-8 w-8 text-zinc-300 mx-auto mb-2" />
        <p className="text-zinc-500">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div 
      className="rounded-lg border border-zinc-200 bg-white overflow-hidden"
      data-testid="workflow-list"
    >
      <div className="flex items-center justify-between p-4 border-b border-zinc-200 bg-zinc-50">
        <h3 className="font-semibold text-zinc-900 flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-500" />
          Workflows ({workflows.length})
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 text-zinc-500 hover:text-zinc-700 hover:bg-zinc-100 rounded-md transition-colors"
            data-testid="workflow-list-refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-zinc-50 border-b border-zinc-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Procesado
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Ciclo
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Fecha
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-zinc-600 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {workflows.map((workflow, idx) => (
              <WorkflowRow 
                key={workflow.id || workflow._id || idx} 
                workflow={workflow}
                onClick={onWorkflowClick}
                onDownloadExcel={handleDownloadExcel}
                onDownloadPdf={handleDownloadPdf}
                downloadingId={downloadingId}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default WorkflowList;
