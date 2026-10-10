import React, { useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, ClipboardCheck, Plus, RotateCcw, Search, Trash2 } from 'lucide-react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  CorporateFiltersProvider,
  useCorporateFilters,
} from '../../filters';
import { useAccessContext } from '../../hooks/useAccessContext';
import CavaNavHeader from './CavaNavHeader';

const newObservation = () => ({
  observation_id: `OBS-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
  observed_reference: '',
  observed_quantity: 1,
  observed_level_pct: 100,
  evidence_id: '',
});

function BlindAuditCavaContent() {
  const { selected, loading: filtersLoading } = useCorporateFilters();
  const { context, loading: contextLoading, error: contextError } = useAccessContext();
  const unidadNegocioPk = selected?.unidades_negocio || context?.unidad_activa || '';

  const [step, setStep] = useState('CAPTURE');
  const [observations, setObservations] = useState([newObservation()]);
  const [inventory, setInventory] = useState([]);
  const [mapping, setMapping] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const canLockCapture = useMemo(
    () => observations.length > 0 && observations.every((item) => item.observed_reference.trim()),
    [observations]
  );

  const updateObservation = (index, field, value) => {
    setObservations((current) => current.map((item, idx) => (
      idx === index ? { ...item, [field]: value } : item
    )));
  };

  const addObservation = () => {
    setObservations((current) => [...current, newObservation()]);
  };

  const removeObservation = (index) => {
    setObservations((current) => current.filter((_, idx) => idx !== index));
  };

  const lockCapture = async () => {
    if (!unidadNegocioPk || !canLockCapture) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        unidad_negocio_pk: unidadNegocioPk,
        estatus: 'EN_CAVA',
        skip: '0',
        limit: '1000',
      });
      const response = await api.get(`/cava-socios/inventario?${params}`);
      setInventory(response.data?.botellas || []);
      setStep('IDENTIFY');
    } catch (err) {
      setError(err?.response?.data?.detail || 'No se pudo cargar el inventario para la etapa de identificación.');
    } finally {
      setLoading(false);
    }
  };

  const reconcile = async () => {
    if (!unidadNegocioPk) return;
    const missingMappings = observations.some((item) => !mapping[item.observation_id]);
    if (missingMappings) {
      setError('Identifica cada observación antes de comparar.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.post(
        `/cava-socios/auditorias-ciegas/reconciliar?unidad_negocio_pk=${encodeURIComponent(unidadNegocioPk)}`,
        {
          idempotency_key: `blind-audit-${unidadNegocioPk}-${Date.now()}`,
          observations: observations.map((item) => ({
            ...item,
            observed_quantity: Number(item.observed_quantity || 0),
            observed_level_pct: item.observed_level_pct === '' ? null : Number(item.observed_level_pct),
            evidence_id: item.evidence_id?.trim() || null,
          })),
          observation_to_bottle: mapping,
          level_tolerance_pct: 5,
          min_recognition_confidence: 0.9,
        }
      );
      setResult(response.data);
      setStep('RESULT');
    } catch (err) {
      setError(err?.response?.data?.detail || 'No se pudo reconciliar la auditoría ciega.');
    } finally {
      setLoading(false);
    }
  };

  const resetAudit = () => {
    setStep('CAPTURE');
    setObservations([newObservation()]);
    setInventory([]);
    setMapping({});
    setResult(null);
    setError(null);
  };

  const outcomeLabel = {
    CONFIRMED: 'Coincidencia confirmada',
    DIFFERENCE: 'Se detectaron diferencias',
    REVIEW_REQUIRED: 'Requiere revisión humana',
  }[result?.outcome] || result?.outcome;

  return (
    <div className="p-6 space-y-6" data-testid="blind-audit-cava-page">
      <CavaNavHeader
        title="Auditoría Ciega de Cavas"
        subtitle="Captura primero lo observado; el inventario esperado se revela solo después de cerrar la captura."
      />

      {(error || contextError) && (
        <div className="p-4 rounded-xl bg-red-50 text-red-700 border border-red-200 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          <span>{error || contextError?.message}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {[
          ['CAPTURE', '1. Captura ciega'],
          ['IDENTIFY', '2. Identificar'],
          ['RESULT', '3. Resultado'],
        ].map(([key, label]) => (
          <Card key={key} className={step === key ? 'border-purple-600' : ''}>
            <CardContent className="p-4 text-sm font-medium">{label}</CardContent>
          </Card>
        ))}
      </div>

      {step === 'CAPTURE' && (
        <Card>
          <CardHeader>
            <CardTitle>Captura lo que ves físicamente</CardTitle>
            <CardDescription>
              En esta etapa no se muestra el inventario teórico. Registra cada botella observada y su nivel aproximado.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {observations.map((item, index) => (
              <div key={item.observation_id} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end border rounded-lg p-3">
                <div className="md:col-span-6">
                  <Label>Referencia observada</Label>
                  <Input
                    value={item.observed_reference}
                    onChange={(e) => updateObservation(index, 'observed_reference', e.target.value)}
                    placeholder="Etiqueta, marca, nombre o referencia visible"
                  />
                </div>
                <div className="md:col-span-2">
                  <Label>Cantidad</Label>
                  <Input
                    type="number"
                    min="0"
                    value={item.observed_quantity}
                    onChange={(e) => updateObservation(index, 'observed_quantity', e.target.value)}
                  />
                </div>
                <div className="md:col-span-3">
                  <Label>Nivel observado %</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={item.observed_level_pct}
                    onChange={(e) => updateObservation(index, 'observed_level_pct', e.target.value)}
                  />
                </div>
                <div className="md:col-span-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeObservation(index)}
                    disabled={observations.length === 1}
                    aria-label="Eliminar observación"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}

            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={addObservation}>
                <Plus className="h-4 w-4 mr-2" />
                Agregar observación
              </Button>
              <Button
                type="button"
                onClick={lockCapture}
                disabled={!canLockCapture || loading || filtersLoading || contextLoading || !unidadNegocioPk}
              >
                <ClipboardCheck className="h-4 w-4 mr-2" />
                Cerrar captura ciega
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 'IDENTIFY' && (
        <Card>
          <CardHeader>
            <CardTitle>Identifica cada observación</CardTitle>
            <CardDescription>
              La captura ya quedó cerrada. Ahora relaciona cada observación con una botella del inventario canónico.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {observations.map((item) => (
              <div key={item.observation_id} className="grid grid-cols-1 md:grid-cols-2 gap-3 border rounded-lg p-3">
                <div>
                  <p className="font-medium">{item.observed_reference}</p>
                  <p className="text-sm text-muted-foreground">
                    Cantidad {item.observed_quantity} · Nivel {item.observed_level_pct}%
                  </p>
                </div>
                <Select
                  value={mapping[item.observation_id] || ''}
                  onValueChange={(value) => setMapping((current) => ({ ...current, [item.observation_id]: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar botella canónica" />
                  </SelectTrigger>
                  <SelectContent>
                    {inventory.map((bottle) => (
                      <SelectItem key={bottle.botella_id} value={String(bottle.botella_id)}>
                        {bottle.producto_nombre || 'Botella'} · {bottle.numero_socio || 'Sin socio'} · {bottle.ubicacion || 'Sin ubicación'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ))}

            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={resetAudit}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Reiniciar
              </Button>
              <Button onClick={reconcile} disabled={loading || inventory.length === 0}>
                <Search className="h-4 w-4 mr-2" />
                Comparar contra inventario
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 'RESULT' && result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {result.outcome === 'CONFIRMED' ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <AlertCircle className="h-5 w-5 text-amber-600" />}
              {outcomeLabel}
            </CardTitle>
            <CardDescription>
              La auditoría no aplicó ajustes ni movimientos de inventario automáticamente.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(result.findings || []).map((finding, index) => (
              <div key={index} className="border rounded-lg p-3">
                <div className="font-medium">{finding.status}</div>
                <div className="text-sm text-muted-foreground">{finding.reason}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Esperado: {finding.expected_level_pct ?? '—'}% · Observado: {finding.observed_level_pct ?? '—'}%
                </div>
              </div>
            ))}

            <Button variant="outline" onClick={resetAudit}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Nueva auditoría
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function BlindAuditCava() {
  return (
    <CorporateFiltersProvider scope="cava_socios">
      <BlindAuditCavaContent />
    </CorporateFiltersProvider>
  );
}
