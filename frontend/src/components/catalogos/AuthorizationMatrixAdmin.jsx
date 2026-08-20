import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  CheckCircle,
  Edit2,
  Loader2,
  Plus,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';


const EMPTY_FORM = {
  NivelAutorizacion: 1,
  RolID: '',
  UsuarioID: '',
  MontoMinimo: '',
  MontoMaximo: '',
  Prioridad: 1,
  RequiereTodosLosNiveles: false,
  Activo: true,
};


function money(value) {
  if (value === null || value === undefined || value === '') {
    return 'Sin límite';
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return String(value);
  }

  return number.toLocaleString('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
  });
}


function normalizeApiError(error) {
  if (error?.response?.status === 403) {
    return {
      forbidden: true,
      message:
        'No cuenta con el permiso SEGURIDAD_CONFIGURAR para administrar matrices de autorización.',
    };
  }

  return {
    forbidden: false,
    message:
      error?.response?.data?.detail ||
      error?.message ||
      'Error al consultar la matriz de autorización.',
  };
}


export default function AuthorizationMatrixAdmin({
  apiClient,
  tipoAutorizacion,
}) {
  const tipoId = tipoAutorizacion?.TipoAutorizacionID;

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [matrixData, setMatrixData] = useState(null);
  const [selectors, setSelectors] = useState({
    roles: [],
    modulos: [],
    acciones: [],
    usuarios: [],
  });

  const [error, setError] = useState('');
  const [forbidden, setForbidden] = useState(false);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRow, setEditingRow] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const roles = selectors.roles || [];
  const usuarios = selectors.usuarios || [];

  const selectedRole = useMemo(
    () =>
      roles.find(
        (role) => String(role.RolID) === String(form.RolID)
      ) || null,
    [roles, form.RolID]
  );

  const loadData = useCallback(async () => {
    if (!tipoId || !apiClient) {
      return;
    }

    setLoading(true);
    setError('');
    setForbidden(false);

    try {
      const [matrixResponse, selectorsResponse] = await Promise.all([
        apiClient.get(
          `/catalogos/autorizaciones/tipos/${tipoId}/matriz`
        ),
        apiClient.get('/catalogos/autorizaciones/catalogos'),
      ]);

      setMatrixData(matrixResponse?.data || null);
      setSelectors(
        selectorsResponse?.data || {
          roles: [],
          modulos: [],
          acciones: [],
          usuarios: [],
        }
      );
    } catch (err) {
      const parsed = normalizeApiError(err);
      setForbidden(parsed.forbidden);
      setError(parsed.message);
      setMatrixData(null);
    } finally {
      setLoading(false);
    }
  }, [apiClient, tipoId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openCreate = () => {
    const rows = matrixData?.matriz || [];

    const nextLevel =
      rows.length > 0
        ? Math.max(
            ...rows.map((row) =>
              Number(row.NivelAutorizacion || 0)
            )
          ) + 1
        : 1;

    setEditingRow(null);
    setForm({
      ...EMPTY_FORM,
      NivelAutorizacion: nextLevel,
    });
    setDialogOpen(true);
  };

  const openEdit = (row) => {
    setEditingRow(row);

    setForm({
      NivelAutorizacion: Number(row.NivelAutorizacion),
      RolID: String(row.RolID),
      UsuarioID:
        row.UsuarioID === null || row.UsuarioID === undefined
          ? ''
          : String(row.UsuarioID),
      MontoMinimo:
        row.MontoMinimo === null ||
        row.MontoMinimo === undefined
          ? ''
          : String(row.MontoMinimo),
      MontoMaximo:
        row.MontoMaximo === null ||
        row.MontoMaximo === undefined
          ? ''
          : String(row.MontoMaximo),
      Prioridad: Number(row.Prioridad || 1),
      RequiereTodosLosNiveles: Boolean(
        row.RequiereTodosLosNiveles
      ),
      Activo: Boolean(row.Activo),
    });

    setDialogOpen(true);
  };

  const buildPayload = () => ({
    NivelAutorizacion: Number(form.NivelAutorizacion),
    RolID: Number(form.RolID),
    UsuarioID: form.UsuarioID
      ? Number(form.UsuarioID)
      : null,
    MontoMinimo:
      form.MontoMinimo === ''
        ? null
        : Number(form.MontoMinimo),
    MontoMaximo:
      form.MontoMaximo === ''
        ? null
        : Number(form.MontoMaximo),
    Prioridad: Number(form.Prioridad),
    RequiereTodosLosNiveles: Boolean(
      form.RequiereTodosLosNiveles
    ),
    Activo: Boolean(form.Activo),
  });

  const save = async () => {
    if (!form.RolID) {
      setError('Debe seleccionar un rol autorizador.');
      return;
    }

    if (
      Number(form.NivelAutorizacion) <= 0 ||
      !Number.isInteger(Number(form.NivelAutorizacion))
    ) {
      setError('El nivel debe ser un entero positivo.');
      return;
    }

    if (
      Number(form.Prioridad) <= 0 ||
      !Number.isInteger(Number(form.Prioridad))
    ) {
      setError('La prioridad debe ser un entero positivo.');
      return;
    }

    const min =
      form.MontoMinimo === ''
        ? null
        : Number(form.MontoMinimo);

    const max =
      form.MontoMaximo === ''
        ? null
        : Number(form.MontoMaximo);

    if (
      min !== null &&
      max !== null &&
      min > max
    ) {
      setError(
        'El monto mínimo no puede ser mayor al monto máximo.'
      );
      return;
    }

    setSaving(true);
    setError('');

    try {
      const payload = buildPayload();

      if (editingRow) {
        await apiClient.put(
          `/catalogos/autorizaciones/matriz/${editingRow.MatrizAutorizacionID}`,
          payload
        );
      } else {
        await apiClient.post(
          `/catalogos/autorizaciones/tipos/${tipoId}/matriz`,
          payload
        );
      }

      setDialogOpen(false);
      await loadData();
    } catch (err) {
      const parsed = normalizeApiError(err);
      setForbidden(parsed.forbidden);
      setError(parsed.message);
    } finally {
      setSaving(false);
    }
  };

  if (!tipoId) {
    return null;
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-10">
          <Loader2 className="h-5 w-5 animate-spin mr-2" />
          Cargando matriz de autorización...
        </CardContent>
      </Card>
    );
  }

  if (forbidden) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="h-5 w-5" />
            Matriz de autorización
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  const tipo = matrixData?.tipo || tipoAutorizacion;
  const rows = matrixData?.matriz || [];

  return (
    <>
      <Card data-testid="authorization-matrix-admin">
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldCheck className="h-5 w-5" />
                Matriz de autorización
              </CardTitle>

              <p className="text-sm text-zinc-500 mt-1">
                Define qué rol o usuario puede resolver esta
                autorización y bajo qué rango.
              </p>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadData}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Actualizar
              </Button>

              <Button
                size="sm"
                onClick={openCreate}
                data-testid="btn-nueva-matriz"
              >
                <Plus className="h-4 w-4 mr-1" />
                Nuevo nivel
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-md border p-3">
              <div className="text-xs text-zinc-500">
                Tipo
              </div>
              <div className="font-medium">
                {tipo?.NombreTipoAutorizacion ||
                  tipo?.CodigoTipoAutorizacion ||
                  '-'}
              </div>
              <div className="text-xs text-zinc-500 mt-1">
                {tipo?.CodigoTipoAutorizacion || ''}
              </div>
            </div>

            <div className="rounded-md border p-3">
              <div className="text-xs text-zinc-500">
                Contexto de unidad
              </div>
              <div className="mt-1">
                {tipo?.RequiereUnidadNegocio ? (
                  <Badge>Requerido</Badge>
                ) : (
                  <Badge variant="outline">No requerido</Badge>
                )}
              </div>
            </div>

            <div className="rounded-md border p-3">
              <div className="text-xs text-zinc-500">
                Niveles configurados
              </div>
              <div className="font-semibold text-lg">
                {rows.length}
              </div>
            </div>
          </div>

          {rows.length === 0 ? (
            <div className="border rounded-md py-8 text-center text-zinc-500">
              No existen niveles configurados.
            </div>
          ) : (
            <div className="overflow-x-auto border rounded-md">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nivel</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Usuario específico</TableHead>
                    <TableHead>Desde</TableHead>
                    <TableHead>Hasta</TableHead>
                    <TableHead>Prioridad</TableHead>
                    <TableHead>Todos niveles</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {rows.map((row) => (
                    <TableRow
                      key={row.MatrizAutorizacionID}
                    >
                      <TableCell className="font-medium">
                        {row.NivelAutorizacion}
                      </TableCell>

                      <TableCell>
                        <div>{row.NombreRol}</div>
                        <div className="text-xs text-zinc-400">
                          {row.CodigoRol}
                        </div>
                      </TableCell>

                      <TableCell>
                        {row.UsuarioID ? (
                          <>
                            <div>{row.NombreUsuario || '-'}</div>
                            <div className="text-xs text-zinc-400">
                              {row.EmailUsuario || ''}
                            </div>
                          </>
                        ) : (
                          <Badge variant="outline">
                            Dinámico por rol/contexto
                          </Badge>
                        )}
                      </TableCell>

                      <TableCell>
                        {money(row.MontoMinimo)}
                      </TableCell>

                      <TableCell>
                        {money(row.MontoMaximo)}
                      </TableCell>

                      <TableCell>
                        {row.Prioridad}
                      </TableCell>

                      <TableCell>
                        {row.RequiereTodosLosNiveles ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <XCircle className="h-4 w-4 text-zinc-300" />
                        )}
                      </TableCell>

                      <TableCell>
                        {row.Activo ? (
                          <Badge>Activo</Badge>
                        ) : (
                          <Badge variant="outline">
                            Inactivo
                          </Badge>
                        )}
                      </TableCell>

                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEdit(row)}
                          title="Editar nivel"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingRow
                ? 'Editar nivel de autorización'
                : 'Nuevo nivel de autorización'}
            </DialogTitle>
          </DialogHeader>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Nivel</Label>
              <Input
                type="number"
                min="1"
                step="1"
                value={form.NivelAutorizacion}
                onChange={(e) =>
                  setForm({
                    ...form,
                    NivelAutorizacion: Number(e.target.value),
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>Prioridad</Label>
              <Input
                type="number"
                min="1"
                step="1"
                value={form.Prioridad}
                onChange={(e) =>
                  setForm({
                    ...form,
                    Prioridad: Number(e.target.value),
                  })
                }
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label>Rol autorizador</Label>

              <Select
                value={String(form.RolID || '')}
                onValueChange={(value) =>
                  setForm({
                    ...form,
                    RolID: value,
                    UsuarioID: '',
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar rol" />
                </SelectTrigger>

                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem
                      key={role.RolID}
                      value={String(role.RolID)}
                    >
                      {role.NombreRol} ({role.CodigoRol})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label>
                Usuario específico
              </Label>

              <Select
                value={
                  form.UsuarioID
                    ? String(form.UsuarioID)
                    : '__dynamic__'
                }
                onValueChange={(value) =>
                  setForm({
                    ...form,
                    UsuarioID:
                      value === '__dynamic__'
                        ? ''
                        : value,
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Dinámico por rol/contexto" />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="__dynamic__">
                    Dinámico por rol/contexto
                  </SelectItem>

                  {usuarios.map((user) => (
                    <SelectItem
                      key={user.UsuarioID}
                      value={String(user.UsuarioID)}
                    >
                      {user.NombreCompleto} — {user.Email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedRole && (
                <p className="text-xs text-zinc-500">
                  Si no selecciona usuario, EDARSAHUB resolverá
                  dinámicamente al usuario activo del rol{' '}
                  <strong>{selectedRole.NombreRol}</strong> según
                  el contexto de Unidad de Negocio.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Monto mínimo</Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder="Sin mínimo"
                value={form.MontoMinimo}
                onChange={(e) =>
                  setForm({
                    ...form,
                    MontoMinimo: e.target.value,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>Monto máximo</Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder="Sin límite"
                value={form.MontoMaximo}
                onChange={(e) =>
                  setForm({
                    ...form,
                    MontoMaximo: e.target.value,
                  })
                }
              />
            </div>

            <div className="flex items-center justify-between rounded-md border p-3">
              <div>
                <Label>Requiere todos los niveles</Label>
                <p className="text-xs text-zinc-500 mt-1">
                  Actívelo únicamente cuando el workflow deba
                  completar todos los niveles aplicables.
                </p>
              </div>

              <Switch
                checked={form.RequiereTodosLosNiveles}
                onCheckedChange={(checked) =>
                  setForm({
                    ...form,
                    RequiereTodosLosNiveles: checked,
                  })
                }
              />
            </div>

            <div className="flex items-center justify-between rounded-md border p-3">
              <div>
                <Label>Activo</Label>
                <p className="text-xs text-zinc-500 mt-1">
                  Las filas inactivas no participan en el motor.
                </p>
              </div>

              <Switch
                checked={form.Activo}
                onCheckedChange={(checked) =>
                  setForm({
                    ...form,
                    Activo: checked,
                  })
                }
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={saving}
            >
              Cancelar
            </Button>

            <Button
              onClick={save}
              disabled={saving}
              data-testid="btn-guardar-matriz"
            >
              {saving && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}

              {editingRow
                ? 'Guardar cambios'
                : 'Crear nivel'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
