/**
 * Proveedores.js - Administración del Portal de Proveedores
 * Permite a los administradores de EDARSA HUB gestionar los proveedores del portal
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { 
  Users, Search, Check, X, Clock, Eye, Edit, Trash2, 
  Building2, Mail, Phone, CreditCard, RefreshCw, Filter,
  ChevronDown, ExternalLink, UserPlus, AlertCircle, KeyRound
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getToken } from '@/lib/auth';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function Proveedores() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [servers, setServers] = useState([]);
  const [selectedSucursales, setSelectedSucursales] = useState([]);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [resetResult, setResetResult] = useState(null);

  useEffect(() => {
    loadSuppliers();
    loadServers();
  }, []);

  const loadSuppliers = async () => {
    try {
      const res = await fetch(`${API_URL}/api/portal/admin/all-suppliers`, {
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const data = await res.json();
        setSuppliers(data);
      } else {
        toast.error('Error al cargar proveedores');
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  const loadServers = async () => {
    try {
      const res = await fetch(`${API_URL}/api/servers`, {
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        }
      });
      if (res.ok) {
        const data = await res.json();
        setServers(data.filter(s => s.active));
      }
    } catch (error) {
      console.error('Error cargando servidores:', error);
    }
  };

  const handleApprove = async (supplier) => {
    try {
      const res = await fetch(`${API_URL}/api/portal/admin/approve-supplier`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          supplier_id: supplier.id,
          action: 'approve',
          sucursales: selectedSucursales,
          approved_by: 'admin'
        })
      });
      
      if (res.ok) {
        toast.success(`Proveedor ${supplier.rfc} aprobado`);
        loadSuppliers();
        setShowModal(false);
        setSelectedSupplier(null);
        setSelectedSucursales([]);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Error al aprobar');
      }
    } catch (error) {
      toast.error('Error de conexión');
    }
  };

  const handleReject = async (supplier) => {
    if (!confirm(`¿Rechazar proveedor ${supplier.rfc}?`)) return;
    
    try {
      const res = await fetch(`${API_URL}/api/portal/admin/approve-supplier`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          supplier_id: supplier.id,
          action: 'reject',
          notes: 'Rechazado por administrador',
          approved_by: 'admin'
        })
      });
      
      if (res.ok) {
        toast.success(`Proveedor ${supplier.rfc} rechazado`);
        loadSuppliers();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Error al rechazar');
      }
    } catch (error) {
      toast.error('Error de conexión');
    }
  };

  const openApprovalModal = (supplier) => {
    setSelectedSupplier(supplier);
    setSelectedSucursales(supplier.sucursales_asignadas || []);
    setShowModal(true);
  };

  const openPasswordModal = (supplier) => {
    setSelectedSupplier(supplier);
    setNewPassword('');
    setResetResult(null);
    setShowPasswordModal(true);
  };

  const handleResetPassword = async () => {
    if (!selectedSupplier || !newPassword || newPassword.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/portal/admin/reset-password`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          supplier_id: selectedSupplier.id,
          rfc: selectedSupplier.rfc,
          new_password: newPassword,
          reset_by: 'admin'
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setResetResult(data);
        toast.success(`Contraseña actualizada para ${selectedSupplier.rfc}`);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Error al resetear contraseña');
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error de conexión');
    }
  };

  const generateRandomPassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
    let password = '';
    for (let i = 0; i < 8; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setNewPassword(password);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Pendiente' },
      approved: { bg: 'bg-green-100', text: 'text-green-700', label: 'Aprobado' },
      rejected: { bg: 'bg-red-100', text: 'text-red-700', label: 'Rechazado' },
      suspended: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Suspendido' }
    };
    const s = styles[status] || styles.pending;
    return <span className={`px-2 py-1 rounded text-xs font-medium ${s.bg} ${s.text}`}>{s.label}</span>;
  };

  const filteredSuppliers = suppliers
    .filter(s => filter === 'all' || s.status === filter)
    .filter(s => 
      s.rfc?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.razon_social?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email?.toLowerCase().includes(searchTerm.toLowerCase())
    );

  const pendingCount = suppliers.filter(s => s.status === 'pending').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-zinc-800"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="proveedores-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Portal Proveedores</h1>
          <p className="text-zinc-500">Administración de accesos al portal de proveedores</p>
        </div>
        <div className="flex items-center gap-3">
          {pendingCount > 0 && (
            <span className="flex items-center gap-2 px-3 py-1.5 bg-yellow-100 text-yellow-700 rounded-lg text-sm">
              <Clock className="h-4 w-4" />
              {pendingCount} pendiente{pendingCount > 1 ? 's' : ''}
            </span>
          )}
          <Button
            onClick={loadSuppliers}
            variant="outline"
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </Button>
          <a 
            href="/portal-proveedores" 
            target="_blank"
            className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 text-sm"
          >
            <ExternalLink className="h-4 w-4" />
            Ir al Portal
          </a>
        </div>
      </div>

      {/* Filtros y búsqueda */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex gap-2">
          {['all', 'pending', 'approved', 'rejected'].map(f => (
            <Button
              key={f}
              onClick={() => setFilter(f)}
              variant={filter === f ? 'default' : 'outline'}
              size="sm"
            >
              {f === 'all' ? 'Todos' : f === 'pending' ? 'Pendientes' : f === 'approved' ? 'Aprobados' : 'Rechazados'}
              {f === 'pending' && pendingCount > 0 && (
                <span className="ml-2 px-1.5 py-0.5 bg-yellow-500 text-white rounded-full text-xs">
                  {pendingCount}
                </span>
              )}
            </Button>
          ))}
        </div>
        <div className="relative w-80">
          <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-400" />
          <Input
            type="text"
            placeholder="Buscar por RFC, razón social, email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Tabla de proveedores */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">RFC</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Razón Social</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Contacto</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Estado</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Sucursales</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Registro</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-zinc-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredSuppliers.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-zinc-500">
                  <Users className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>No se encontraron proveedores</p>
                </td>
              </tr>
            ) : (
              filteredSuppliers.map(supplier => (
                <tr key={supplier.id} className="hover:bg-zinc-50">
                  <td className="px-4 py-3">
                    <span className="font-mono font-medium text-zinc-900">{supplier.rfc}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-zinc-900">{supplier.razon_social || '-'}</p>
                      <p className="text-sm text-zinc-500">{supplier.nombre_contacto}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      <p className="flex items-center gap-1 text-zinc-600">
                        <Mail className="h-3 w-3" /> {supplier.email || '-'}
                      </p>
                      <p className="flex items-center gap-1 text-zinc-500">
                        <Phone className="h-3 w-3" /> {supplier.telefono || '-'}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(supplier.status)}
                  </td>
                  <td className="px-4 py-3">
                    {supplier.sucursales_asignadas?.length > 0 ? (
                      <span className="text-sm text-zinc-600">
                        {supplier.sucursales_asignadas.length} asignada{supplier.sucursales_asignadas.length > 1 ? 's' : ''}
                      </span>
                    ) : (
                      <span className="text-sm text-zinc-400">Sin asignar</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-zinc-500">
                    {formatDate(supplier.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      {supplier.status === 'pending' && (
                        <>
                          <Button
                            onClick={() => openApprovalModal(supplier)}
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                          <Button
                            onClick={() => handleReject(supplier)}
                            size="sm"
                            variant="destructive"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      {supplier.status === 'approved' && (
                        <>
                          <Button
                            onClick={() => openApprovalModal(supplier)}
                            size="sm"
                            variant="outline"
                            title="Editar"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            onClick={() => openPasswordModal(supplier)}
                            size="sm"
                            variant="outline"
                            className="text-amber-600 border-amber-200 hover:bg-amber-50"
                            title="Resetear Contraseña"
                          >
                            <KeyRound className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        onClick={() => {
                          setSelectedSupplier(supplier);
                          setShowModal(true);
                        }}
                        size="sm"
                        variant="ghost"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de detalle/aprobación */}
      {showModal && selectedSupplier && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                {selectedSupplier.status === 'pending' ? 'Aprobar Proveedor' : 'Detalle del Proveedor'}
              </h2>
              <Button
                onClick={() => { setShowModal(false); setSelectedSupplier(null); setSelectedSucursales([]); }}
                variant="ghost"
                size="sm"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Datos del proveedor */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-zinc-500 uppercase">RFC</label>
                  <p className="font-mono font-semibold text-lg">{selectedSupplier.rfc}</p>
                </div>
                <div>
                  <label className="text-xs text-zinc-500 uppercase">Estado</label>
                  <p>{getStatusBadge(selectedSupplier.status)}</p>
                </div>
                <div className="col-span-2">
                  <label className="text-xs text-zinc-500 uppercase">Razón Social</label>
                  <p className="font-medium">{selectedSupplier.razon_social || '-'}</p>
                </div>
                <div>
                  <label className="text-xs text-zinc-500 uppercase">Contacto</label>
                  <p>{selectedSupplier.nombre_contacto || '-'}</p>
                </div>
                <div>
                  <label className="text-xs text-zinc-500 uppercase">Teléfono</label>
                  <p>{selectedSupplier.telefono || '-'}</p>
                </div>
                <div className="col-span-2">
                  <label className="text-xs text-zinc-500 uppercase">Email</label>
                  <p>{selectedSupplier.email || '-'}</p>
                </div>
                {selectedSupplier.banco && (
                  <>
                    <div>
                      <label className="text-xs text-zinc-500 uppercase">Banco</label>
                      <p>{selectedSupplier.banco}</p>
                    </div>
                    <div>
                      <label className="text-xs text-zinc-500 uppercase">CLABE</label>
                      <p className="font-mono">{selectedSupplier.clabe || '-'}</p>
                    </div>
                  </>
                )}
              </div>

              {/* Asignación de sucursales */}
              {(selectedSupplier.status === 'pending' || selectedSupplier.status === 'approved') && (
                <div className="border-t pt-4">
                  <label className="text-xs text-zinc-500 uppercase block mb-3">
                    Sucursales Asignadas (opcionales)
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {servers.map(server => (
                      <label
                        key={server.id}
                        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-zinc-50 ${
                          selectedSucursales.includes(server.id) ? 'border-green-500 bg-green-50' : ''
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedSucursales.includes(server.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedSucursales([...selectedSucursales, server.id]);
                            } else {
                              setSelectedSucursales(selectedSucursales.filter(id => id !== server.id));
                            }
                          }}
                          className="rounded"
                        />
                        <div>
                          <p className="font-medium text-sm">{server.name}</p>
                          <p className="text-xs text-zinc-500">{server.system_type}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                  {servers.length === 0 && (
                    <p className="text-sm text-zinc-500 text-center py-4">
                      No hay servidores configurados
                    </p>
                  )}
                </div>
              )}

              {/* Información de aprobación */}
              {selectedSupplier.approved_at && (
                <div className="border-t pt-4 text-sm text-zinc-500">
                  <p>Aprobado el {formatDate(selectedSupplier.approved_at)} por {selectedSupplier.approved_by}</p>
                  {selectedSupplier.approval_notes && (
                    <p className="mt-1">Notas: {selectedSupplier.approval_notes}</p>
                  )}
                </div>
              )}
            </div>

            {/* Acciones del modal */}
            {selectedSupplier.status === 'pending' && (
              <div className="sticky bottom-0 bg-zinc-50 border-t px-6 py-4 flex justify-end gap-3">
                <Button
                  onClick={() => handleReject(selectedSupplier)}
                  variant="outline"
                  className="text-red-600 border-red-200 hover:bg-red-50"
                >
                  <X className="h-4 w-4 mr-2" />
                  Rechazar
                </Button>
                <Button
                  onClick={() => handleApprove(selectedSupplier)}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Aprobar Proveedor
                </Button>
              </div>
            )}
            
            {selectedSupplier.status === 'approved' && (
              <div className="sticky bottom-0 bg-zinc-50 border-t px-6 py-4 flex justify-end gap-3">
                <Button
                  onClick={() => openPasswordModal(selectedSupplier)}
                  variant="outline"
                  className="text-amber-600 border-amber-200 hover:bg-amber-50"
                >
                  <KeyRound className="h-4 w-4 mr-2" />
                  Resetear Contraseña
                </Button>
                <Button
                  onClick={() => handleApprove(selectedSupplier)}
                  variant="outline"
                >
                  Guardar Cambios
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal de Resetear Contraseña */}
      {showPasswordModal && selectedSupplier && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="border-b px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <KeyRound className="h-5 w-5 text-amber-600" />
                Resetear Contraseña
              </h2>
              <Button
                onClick={() => { setShowPasswordModal(false); setResetResult(null); setNewPassword(''); }}
                variant="ghost"
                size="sm"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Datos del proveedor */}
              <div className="bg-zinc-50 rounded-lg p-4">
                <p className="text-sm text-zinc-500">Proveedor</p>
                <p className="font-mono font-bold text-lg">{selectedSupplier.rfc}</p>
                <p className="text-sm text-zinc-600">{selectedSupplier.razon_social}</p>
                <p className="text-sm text-zinc-500">{selectedSupplier.email}</p>
              </div>

              {!resetResult ? (
                <>
                  {/* Input de nueva contraseña */}
                  <div>
                    <label className="text-sm font-medium text-zinc-700 block mb-2">
                      Nueva Contraseña
                    </label>
                    <div className="flex gap-2">
                      <Input
                        type="text"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="Mínimo 6 caracteres"
                        className="font-mono text-lg"
                      />
                      <Button
                        onClick={generateRandomPassword}
                        variant="outline"
                        title="Generar contraseña aleatoria"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Botones */}
                  <div className="flex justify-end gap-3 pt-4">
                    <Button
                      onClick={() => { setShowPasswordModal(false); setNewPassword(''); }}
                      variant="outline"
                    >
                      Cancelar
                    </Button>
                    <Button
                      onClick={handleResetPassword}
                      className="bg-amber-600 hover:bg-amber-700"
                      disabled={!newPassword || newPassword.length < 6}
                    >
                      <KeyRound className="h-4 w-4 mr-2" />
                      Establecer Contraseña
                    </Button>
                  </div>
                </>
              ) : (
                /* Resultado del reset */
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <Check className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="font-medium text-green-800">Contraseña Actualizada</p>
                  </div>

                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <p className="text-xs text-amber-600 uppercase font-medium mb-1">Nueva Contraseña</p>
                    <p className="font-mono text-2xl font-bold text-zinc-800 select-all">
                      {resetResult.new_password}
                    </p>
                    <p className="text-xs text-amber-600 mt-2">
                      ⚠️ Guarda esta contraseña, no podrás verla de nuevo
                    </p>
                  </div>

                  <div className="text-sm text-zinc-500">
                    <p>Reseteo realizado: {new Date(resetResult.reset_at).toLocaleString('es-MX')}</p>
                    <p>Por: {resetResult.reset_by}</p>
                  </div>

                  <Button
                    onClick={() => { setShowPasswordModal(false); setResetResult(null); setNewPassword(''); }}
                    className="w-full"
                  >
                    Cerrar
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
