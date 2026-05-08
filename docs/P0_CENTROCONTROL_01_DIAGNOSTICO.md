# P0-CENTROCONTROL-01 - DIAGNÓSTICO
## Corrección de Funciones/Variables No Definidas en CentroControl.jsx

**Fecha:** 2025-12-27  
**Estado:** EN PROGRESO  
**Archivo principal:** `/app/frontend/src/pages/CentroControl.jsx`

---

## 1. ERRORES IDENTIFICADOS

| # | Error | Archivo | Línea | Momento | Impacto | Causa Probable | Reparación Mínima |
|---|-------|---------|------:|---------|---------|----------------|-------------------|
| 1 | `enviarPruebaEmail is not defined` | CentroControl.jsx | 981 | Al hacer clic en "Enviar Email de Prueba" | Rompe botón | Función no declarada | Crear función que llame a `POST /api/centro-control/notificaciones/email/test` |
| 2 | `enviarPruebaWhatsApp is not defined` | CentroControl.jsx | 1011 | Al hacer clic en "Enviar WhatsApp de Prueba" | Rompe botón | Función no declarada | Crear función que llame a `POST /api/centro-control/notificaciones/whatsapp/test` |
| 3 | `nuevoDestinatario is not defined` | CentroControl.jsx | 1065-1086 | Al cargar tab Notificaciones | Rompe pantalla | Estado no declarado | Declarar `useState` con valor inicial `{ tipo: 'email', destinatario: '', nombre: '' }` |
| 4 | `setNuevoDestinatario is not defined` | CentroControl.jsx | 1066, 1076, 1083 | Al escribir en inputs de agregar | Rompe pantalla | Setter de estado no declarado | Incluido en declaración de `nuevoDestinatario` |
| 5 | `agregarDestinatario is not defined` | CentroControl.jsx | 1086 | Al hacer clic en "Agregar" | Rompe botón | Función no declarada | Crear función que llame a `POST /api/centro-control/destinatarios` |
| 6 | `loadingDestinatarios is not defined` | CentroControl.jsx | 1113 | Al cargar lista de destinatarios | Rompe render condicional | Estado no declarado | Declarar `useState(false)` |
| 7 | `toggleDestinatarioActivo is not defined` | CentroControl.jsx | 1152, 1198 | Al hacer clic en "Activar/Desactivar" | Rompe botón | Función no declarada | Crear función que llame a `PUT /api/centro-control/destinatarios/{id}` |
| 8 | `eliminarDestinatario is not defined` | CentroControl.jsx | 1160, 1206 | Al hacer clic en "Eliminar" | Rompe botón | Función no declarada | Crear función que llame a `DELETE /api/centro-control/destinatarios/{id}` |
| 9 | `Lock is not defined` | CentroControl.jsx | 1261 | Al cargar tab Blindaje | Rompe pantalla | Icon no importado | Agregar `Lock` a imports de lucide-react |

---

## 2. ENDPOINTS BACKEND EXISTENTES

| Endpoint | Método | Propósito | Estado |
|----------|--------|-----------|--------|
| `/api/centro-control/destinatarios` | GET | Listar destinatarios | ✅ Existe |
| `/api/centro-control/destinatarios` | POST | Crear destinatario | ✅ Existe |
| `/api/centro-control/destinatarios/{id}` | PUT | Actualizar destinatario | ✅ Existe |
| `/api/centro-control/destinatarios/{id}` | DELETE | Eliminar destinatario | ✅ Existe |
| `/api/centro-control/notificaciones/email/test` | POST | Enviar email prueba | ✅ Existe |
| `/api/centro-control/notificaciones/whatsapp/test` | POST | Enviar whatsapp prueba | ✅ Existe |
| `/api/notificaciones/config` | GET | Config de notificaciones | ✅ Usado |
| `/api/notificaciones/destinatarios` | GET | Lista de destinatarios | ⚠️ Diferente ruta |

---

## 3. PLAN DE REPARACIÓN

### 3.1 Agregar Import Faltante

```diff
import {
  Activity, AlertTriangle, CheckCircle, XCircle, RefreshCw, 
  Server, Database, Zap, Clock, Shield, Eye, Bell, 
  ChevronRight, Info, Settings, Wifi, WifiOff,
  Play, Pause, FileText, GitBranch, TrendingUp, Calendar,
  AlertCircle, CheckCircle2, Circle, ExternalLink,
- Timer, Cpu, Radio
+ Timer, Cpu, Radio, Lock
} from 'lucide-react';
```

### 3.2 Declarar Estados Faltantes

```javascript
// Estado para formulario de nuevo destinatario
const [nuevoDestinatario, setNuevoDestinatario] = useState({
  tipo: 'email',
  destinatario: '',
  nombre: ''
});

// Estado de loading para lista de destinatarios
const [loadingDestinatarios, setLoadingDestinatarios] = useState(false);
```

### 3.3 Crear Funciones Faltantes

```javascript
// Agregar destinatario
const agregarDestinatario = async () => {
  if (!nuevoDestinatario.destinatario) {
    toast.error('Ingrese un destinatario');
    return;
  }
  try {
    const res = await fetch(`${API_URL}/api/centro-control/destinatarios`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(nuevoDestinatario)
    });
    if (res.ok) {
      toast.success('Destinatario agregado');
      setNuevoDestinatario({ tipo: 'email', destinatario: '', nombre: '' });
      fetchDestinatarios();
    } else {
      const err = await res.json();
      toast.error(err.detail || 'Error al agregar');
    }
  } catch (err) {
    toast.error('Error de conexión');
  }
};

// Toggle activo/inactivo
const toggleDestinatarioActivo = async (id, activo) => {
  try {
    const res = await fetch(`${API_URL}/api/centro-control/destinatarios/${id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ activo: !activo })
    });
    if (res.ok) {
      toast.success(activo ? 'Desactivado' : 'Activado');
      fetchDestinatarios();
    }
  } catch (err) {
    toast.error('Error al actualizar');
  }
};

// Eliminar destinatario
const eliminarDestinatario = async (id) => {
  if (!window.confirm('¿Eliminar destinatario?')) return;
  try {
    const res = await fetch(`${API_URL}/api/centro-control/destinatarios/${id}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    if (res.ok) {
      toast.success('Eliminado');
      fetchDestinatarios();
    }
  } catch (err) {
    toast.error('Error al eliminar');
  }
};

// Enviar email de prueba
const enviarPruebaEmail = async () => {
  const emailActivo = destinatarios.find(d => d.tipo === 'email' && d.activo);
  if (!emailActivo) {
    toast.error('No hay destinatarios de email activos');
    return;
  }
  try {
    toast.loading('Enviando email de prueba...');
    const res = await fetch(`${API_URL}/api/centro-control/notificaciones/email/test`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient: emailActivo.destinatario })
    });
    toast.dismiss();
    if (res.ok) {
      toast.success('Email de prueba enviado');
    } else {
      const err = await res.json();
      toast.error(err.detail || 'Error al enviar');
    }
  } catch (err) {
    toast.dismiss();
    toast.error('Error de conexión');
  }
};

// Enviar whatsapp de prueba
const enviarPruebaWhatsApp = async () => {
  const waActivo = destinatarios.find(d => d.tipo === 'whatsapp' && d.activo);
  if (!waActivo) {
    toast.error('No hay destinatarios de WhatsApp activos');
    return;
  }
  try {
    toast.loading('Enviando WhatsApp de prueba...');
    const res = await fetch(`${API_URL}/api/centro-control/notificaciones/whatsapp/test`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient: waActivo.destinatario })
    });
    toast.dismiss();
    if (res.ok) {
      toast.success('WhatsApp de prueba enviado');
    } else {
      const err = await res.json();
      toast.error(err.detail || 'Error al enviar');
    }
  } catch (err) {
    toast.dismiss();
    toast.error('Error de conexión');
  }
};
```

### 3.4 Actualizar fetchDestinatarios para usar loading

```javascript
const fetchDestinatarios = useCallback(async () => {
  setLoadingDestinatarios(true);
  try {
    const res = await fetch(`${API_URL}/api/centro-control/destinatarios`, {
      credentials: 'include'
    });
    if (res.ok) {
      const data = await res.json();
      setDestinatarios(data.destinatarios || []);
    }
  } catch (err) {
    logger.error('Error cargando destinatarios:', err);
  } finally {
    setLoadingDestinatarios(false);
  }
}, []);
```

---

## 4. ARCHIVOS A MODIFICAR

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/pages/CentroControl.jsx` | Agregar import Lock, estados faltantes, funciones faltantes |

---

## 5. VALIDACIONES POST-FIX

- [ ] npm run build exitoso
- [ ] CentroControl carga sin error fatal
- [ ] Tab Notificaciones carga sin errores
- [ ] Tab Blindaje carga sin errores (Lock icon)
- [ ] Botón "Enviar Email de Prueba" no rompe pantalla
- [ ] Botón "Enviar WhatsApp de Prueba" no rompe pantalla
- [ ] Botón "Agregar" destinatario no rompe pantalla
- [ ] Botones "Activar/Desactivar" no rompen pantalla
- [ ] Botones "Eliminar" no rompen pantalla
- [ ] Login sigue funcionando
- [ ] Comercial sigue cargando
- [ ] Finanzas sigue cargando
- [ ] No regresión en AUTH-SECURITY-01

---

**Documento creado:** 2025-12-27  
**Estado:** DIAGNÓSTICO COMPLETADO - LISTO PARA REPARACIÓN
