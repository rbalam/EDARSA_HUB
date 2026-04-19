/**
 * Servicio API para el Módulo Operativo Fase 2A
 * CAB-003 | EDARSA HUB
 * 
 * Centraliza las llamadas a los endpoints /api/v2/*
 */

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';
const API_V2 = `${API_BASE}/api/v2`;

/**
 * Helper para hacer requests con manejo de errores y autenticación
 */
async function apiRequest(url, options = {}) {
  try {
    // Obtener token de autenticación
    const token = localStorage.getItem('token');
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${url}]:`, error);
    throw error;
  }
}

// ============================================
// HEALTH CHECK
// ============================================

export async function checkHealth() {
  return apiRequest(`${API_V2}/health`);
}

// ============================================
// DASHBOARD
// ============================================

export async function getDashboardResumen() {
  return apiRequest(`${API_V2}/dashboard/resumen`);
}

export async function getDashboardAlertas() {
  return apiRequest(`${API_V2}/dashboard/alertas`);
}

export async function getDashboardKPIs() {
  return apiRequest(`${API_V2}/dashboard/kpis`);
}

export async function getWorkflowsPorEstado() {
  return apiRequest(`${API_V2}/dashboard/workflows/por-estado`);
}

export async function getTareasPorEstado() {
  return apiRequest(`${API_V2}/dashboard/tareas/por-estado`);
}

// ============================================
// WORKFLOWS
// ============================================

export async function getWorkflows(params = {}) {
  const queryParams = new URLSearchParams();
  if (params.estado) queryParams.append('estado', params.estado);
  if (params.procesado_id) queryParams.append('procesado_id', params.procesado_id);
  if (params.skip) queryParams.append('skip', params.skip);
  if (params.limit) queryParams.append('limit', params.limit);
  
  const query = queryParams.toString();
  return apiRequest(`${API_V2}/workflows${query ? `?${query}` : ''}`);
}

export async function getWorkflow(workflowId) {
  return apiRequest(`${API_V2}/workflows/${workflowId}`);
}

export async function getWorkflowResumen(workflowId) {
  return apiRequest(`${API_V2}/workflows/${workflowId}/resumen`);
}

export async function createWorkflow(data) {
  return apiRequest(`${API_V2}/workflows`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function cambiarEstadoWorkflow(workflowId, nuevoEstado) {
  return apiRequest(`${API_V2}/workflows/${workflowId}/estado`, {
    method: 'PATCH',
    body: JSON.stringify({ nuevo_estado: nuevoEstado }),
  });
}

export async function escalarWorkflow(workflowId, motivo, usuarioId) {
  return apiRequest(`${API_V2}/workflows/${workflowId}/escalar`, {
    method: 'POST',
    body: JSON.stringify({ motivo, usuario_id: usuarioId }),
  });
}

// ============================================
// TAREAS
// ============================================

export async function getTareas(params = {}) {
  const queryParams = new URLSearchParams();
  if (params.usuario_id) queryParams.append('usuario_id', params.usuario_id);
  if (params.workflow_id) queryParams.append('workflow_id', params.workflow_id);
  if (params.estado) queryParams.append('estado', params.estado);
  if (params.vencidas) queryParams.append('vencidas', 'true');
  if (params.pendientes) queryParams.append('pendientes', 'true');
  if (params.limit) queryParams.append('limit', params.limit);
  
  const query = queryParams.toString();
  return apiRequest(`${API_V2}/tareas${query ? `?${query}` : ''}`);
}

export async function getTarea(tareaId) {
  return apiRequest(`${API_V2}/tareas/${tareaId}`);
}

export async function asignarTarea(tareaId, usuarioAsignadoId, asignadoPorId) {
  return apiRequest(`${API_V2}/tareas/${tareaId}/asignar`, {
    method: 'PATCH',
    body: JSON.stringify({
      usuario_asignado_id: usuarioAsignadoId,
      asignado_por_id: asignadoPorId,
    }),
  });
}

export async function completarTarea(tareaId) {
  return apiRequest(`${API_V2}/tareas/${tareaId}/completar`, {
    method: 'PATCH',
  });
}

export async function getHistorialTarea(tareaId) {
  return apiRequest(`${API_V2}/tareas/${tareaId}/historial`);
}

// ============================================
// JUSTIFICACIONES
// ============================================

export async function getJustificaciones(params = {}) {
  const queryParams = new URLSearchParams();
  if (params.workflow_id) queryParams.append('workflow_id', params.workflow_id);
  if (params.diferencia_id) queryParams.append('diferencia_id', params.diferencia_id);
  if (params.tipo) queryParams.append('tipo', params.tipo);
  
  const query = queryParams.toString();
  return apiRequest(`${API_V2}/justificaciones${query ? `?${query}` : ''}`);
}

export async function getJustificacionesWorkflow(workflowId) {
  return apiRequest(`${API_V2}/justificaciones/workflow/${workflowId}`);
}

export async function verificarJustificacionesWorkflow(workflowId) {
  return apiRequest(`${API_V2}/justificaciones/workflow/${workflowId}/verificar`, {
    method: 'POST',
  });
}

export async function getUmbralJustificacion() {
  return apiRequest(`${API_V2}/justificaciones/umbral`);
}

// ============================================
// AUDITORÍA
// ============================================

export async function getAuditoriaPendientes() {
  return apiRequest(`${API_V2}/auditoria/pendientes`);
}

export async function getUltimaDecision(workflowId) {
  return apiRequest(`${API_V2}/auditoria/workflow/${workflowId}/ultima-decision`);
}

export async function getResumenAuditoria() {
  return apiRequest(`${API_V2}/auditoria/resumen`);
}

// ============================================
// CONFIGURACIÓN
// ============================================

export async function getConfiguracion() {
  return apiRequest(`${API_V2}/configuracion`);
}

export async function getTodasConfiguraciones() {
  return apiRequest(`${API_V2}/configuracion/todas`);
}

export async function actualizarConfiguracion(clave, valor, descripcion = null) {
  return apiRequest(`${API_V2}/configuracion/${clave}`, {
    method: 'PATCH',
    body: JSON.stringify({ valor, descripcion }),
  });
}

// ============================================
// RESPONSABILIDAD ECONÓMICA (Fase 2C.1)
// ============================================

export async function getResponsabilidadMetricas() {
  return apiRequest(`${API_V2}/responsabilidad/metricas`);
}

export async function getResponsabilidadLista(params = {}) {
  const queryParams = new URLSearchParams();
  if (params.sucursal_id) queryParams.append('sucursal_id', params.sucursal_id);
  if (params.estado) queryParams.append('estado', params.estado);
  if (params.excede_minimo !== undefined) queryParams.append('excede_minimo', params.excede_minimo);
  if (params.skip) queryParams.append('skip', params.skip);
  if (params.limit) queryParams.append('limit', params.limit);
  
  const query = queryParams.toString();
  return apiRequest(`${API_V2}/responsabilidad${query ? `?${query}` : ''}`);
}

export async function getResponsabilidadWorkflow(workflowId) {
  return apiRequest(`${API_V2}/responsabilidad/workflow/${workflowId}`);
}

export async function getResponsabilidadConfiguracion() {
  return apiRequest(`${API_V2}/responsabilidad/configuracion`);
}

export async function actualizarResponsabilidadConfiguracion(config) {
  return apiRequest(`${API_V2}/responsabilidad/configuracion`, {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

export async function calcularResponsabilidad(workflowId, usuarioId, forzar = false) {
  const params = new URLSearchParams({ usuario_id: usuarioId });
  if (forzar) params.append('forzar_recalculo', 'true');
  return apiRequest(`${API_V2}/responsabilidad/calcular/${workflowId}?${params.toString()}`, {
    method: 'POST',
  });
}

// Fase 2C.2 - Acciones de aprobación
export async function proponerResponsabilidad(responsabilidadId, usuarioId, usuarioRol, comentario) {
  return apiRequest(`${API_V2}/responsabilidad/${responsabilidadId}/proponer`, {
    method: 'POST',
    body: JSON.stringify({ usuario_id: usuarioId, usuario_rol: usuarioRol, comentario }),
  });
}

export async function aprobarResponsabilidad(responsabilidadId, usuarioId, usuarioRol, comentario) {
  return apiRequest(`${API_V2}/responsabilidad/${responsabilidadId}/aprobar`, {
    method: 'POST',
    body: JSON.stringify({ usuario_id: usuarioId, usuario_rol: usuarioRol, comentario }),
  });
}

export async function rechazarResponsabilidad(responsabilidadId, usuarioId, usuarioRol, comentario) {
  return apiRequest(`${API_V2}/responsabilidad/${responsabilidadId}/rechazar`, {
    method: 'POST',
    body: JSON.stringify({ usuario_id: usuarioId, usuario_rol: usuarioRol, comentario }),
  });
}

export async function exonerarResponsabilidad(responsabilidadId, usuarioId, usuarioRol, comentario) {
  return apiRequest(`${API_V2}/responsabilidad/${responsabilidadId}/exonerar`, {
    method: 'POST',
    body: JSON.stringify({ usuario_id: usuarioId, usuario_rol: usuarioRol, comentario }),
  });
}

export async function disputarResponsabilidad(responsabilidadId, usuarioId, usuarioRol, comentario) {
  return apiRequest(`${API_V2}/responsabilidad/${responsabilidadId}/disputar`, {
    method: 'POST',
    body: JSON.stringify({ usuario_id: usuarioId, usuario_rol: usuarioRol, comentario }),
  });
}

export async function resolverDisputaResponsabilidad(responsabilidadId, usuarioId, usuarioRol, comentario) {
  return apiRequest(`${API_V2}/responsabilidad/${responsabilidadId}/resolver-disputa`, {
    method: 'POST',
    body: JSON.stringify({ usuario_id: usuarioId, usuario_rol: usuarioRol, comentario }),
  });
}

export async function getPendientesAprobacion() {
  return apiRequest(`${API_V2}/responsabilidad/pendientes-aprobacion`);
}

export async function getEnDisputa() {
  return apiRequest(`${API_V2}/responsabilidad/en-disputa`);
}

export async function getResponsabilidadHistorial(responsabilidadId) {
  return apiRequest(`${API_V2}/responsabilidad/${responsabilidadId}/historial`);
}

// Export default para conveniencia
export default {
  checkHealth,
  getDashboardResumen,
  getDashboardAlertas,
  getDashboardKPIs,
  getWorkflows,
  getWorkflow,
  getTareas,
  getTarea,
  getConfiguracion,
  // Responsabilidad Económica
  getResponsabilidadMetricas,
  getResponsabilidadLista,
  getResponsabilidadWorkflow,
  getResponsabilidadConfiguracion,
  actualizarResponsabilidadConfiguracion,
  calcularResponsabilidad,
};
