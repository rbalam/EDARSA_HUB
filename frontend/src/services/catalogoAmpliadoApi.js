import api from '@/lib/api';

const ROOT = '/catalogo-ampliado';
const data = response => response?.data?.data ?? response?.data;

export const catalogoAmpliadoApi = {
  getConfiguracion: async empresaId => data(await api.get(`${ROOT}/empresas/${empresaId}/configuracion`)),
  updateConfiguracion: async (empresaId, payload) => data(await api.put(`${ROOT}/empresas/${empresaId}/configuracion`, payload)),
  listPersonas: async empresaId => data(await api.get(`${ROOT}/personas`, { params: empresaId ? { empresa_id: empresaId } : {} })),
  createPersona: async payload => data(await api.post(`${ROOT}/personas`, payload)),
  createVinculo: async (personaId, payload) => data(await api.post(`${ROOT}/personas/${personaId}/vinculos`, payload)),
  listRoles: async () => data(await api.get(`${ROOT}/roles-corporativos`)),
  assignRole: async (empresaId, payload) => data(await api.post(`${ROOT}/empresas/${empresaId}/roles`, payload)),
  listTiposDocumento: async () => data(await api.get(`${ROOT}/tipos-documento`)),
  listDocumentos: async empresaId => data(await api.get(`${ROOT}/empresas/${empresaId}/documentos`)),
  createDocumento: async (empresaId, payload) => data(await api.post(`${ROOT}/empresas/${empresaId}/documentos`, payload)),
  createVersion: async (documentoId, payload) => data(await api.post(`${ROOT}/documentos/${documentoId}/versiones`, payload)),
  getKardex: async documentoId => data(await api.get(`${ROOT}/documentos/${documentoId}/kardex`)),
  listVencimientos: async (empresaId, dias) => data(await api.get(`${ROOT}/empresas/${empresaId}/vencimientos`, { params: { dias } })),
  listAlertas: async empresaId => data(await api.get(`${ROOT}/empresas/${empresaId}/alertas/reglas`)),
  createAlerta: async (empresaId, payload) => data(await api.post(`${ROOT}/empresas/${empresaId}/alertas/reglas`, payload)),
};

export default catalogoAmpliadoApi;
