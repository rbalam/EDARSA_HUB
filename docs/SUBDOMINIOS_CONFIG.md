# 🌐 Guía de Configuración de Subdominios - EDARSAHUB

## Arquitectura Implementada: Host-based Routing

Se ha implementado **enrutamiento basado en hostname** que permite servir múltiples portales desde una única aplicación React.

### Mapeo de Subdominios

| Subdominio | Portal |
|------------|--------|
| `inteligencia.edarsa.com.mx` | Portal Inteligencia Comercial IA |
| `proveedores.edarsa.com.mx` | Portal de Proveedores (SupplierHub) |
| `erp.edarsa.com.mx` | CRM Principal EDARSAHUB |
| `*.edarsa.com.mx` (otros) | CRM Principal (default) |

---

## 📋 Paso 1: Configuración DNS

### Opción A: Usando Cloudflare (Recomendado)

1. Accede al dashboard de Cloudflare
2. Ve a **DNS** → **Records**
3. Agrega los siguientes registros CNAME:

```
Tipo: CNAME
Nombre: inteligencia
Contenido: stock-tracker-990.preview.emergentagent.com
Proxy: ✅ Proxied (naranja)
TTL: Auto

Tipo: CNAME
Nombre: proveedores
Contenido: stock-tracker-990.preview.emergentagent.com
Proxy: ✅ Proxied (naranja)
TTL: Auto
```

### Opción B: Usando GoDaddy/Otros Registradores

1. Accede al panel de administración de DNS
2. Agrega registros CNAME:

```
Host: inteligencia
Apunta a: stock-tracker-990.preview.emergentagent.com
TTL: 3600

Host: proveedores
Apunta a: stock-tracker-990.preview.emergentagent.com
TTL: 3600
```

---

## 📋 Paso 2: Configuración SSL (Si usas Cloudflare)

En Cloudflare → SSL/TLS:
- Modo: **Full (strict)** o **Flexible**
- Edge Certificates: Asegurar que estén activos

---

## 📋 Paso 3: Verificación

Una vez propagado el DNS (5-30 minutos), verifica:

```bash
# Verificar resolución DNS
nslookup inteligencia.edarsa.com.mx
nslookup proveedores.edarsa.com.mx

# Probar acceso
curl -I https://inteligencia.edarsa.com.mx
curl -I https://proveedores.edarsa.com.mx
```

---

## 🔧 Cómo Funciona Internamente

El archivo `/app/frontend/src/HostRouter.jsx` detecta el hostname y renderiza el portal correspondiente:

```javascript
// Configuración de subdominios
const SUBDOMAIN_CONFIG = {
  'inteligencia.edarsa.com.mx': 'inteligencia',
  'proveedores.edarsa.com.mx': 'proveedores',
  'ia.edarsa.com.mx': 'inteligencia',        // Alias
  'suppliers.edarsa.com.mx': 'proveedores',  // Alias
};
```

### Flujo de Detección:

1. Usuario accede a `inteligencia.edarsa.com.mx`
2. DNS resuelve a la IP del servidor Emergent
3. React carga y `HostRouter` detecta el hostname
4. `HostRouter` renderiza `PortalInteligenciaApp` directamente
5. El usuario ve el Portal de Inteligencia sin necesidad de navegar a `/inteligencia-comercial`

---

## 🔄 Agregar Nuevos Subdominios

Para agregar más subdominios en el futuro:

1. Editar `/app/frontend/src/HostRouter.jsx`
2. Agregar entrada en `SUBDOMAIN_CONFIG`
3. Agregar case en el switch de renderizado
4. Configurar DNS correspondiente

---

## ⚠️ Notas Importantes

- **Propagación DNS**: Puede tomar de 5 minutos a 48 horas
- **CORS**: El backend ya está configurado para aceptar requests de cualquier origen
- **Cookies**: Las cookies de sesión funcionarán correctamente si se configura el dominio base `.edarsa.com.mx`
- **SSL**: Cloudflare provee certificado SSL automático para los subdominios

---

## URLs Actuales de Prueba (Preview Emergent)

Mientras configuras los subdominios, puedes acceder directamente:

- **Portal Inteligencia**: `https://erp-crm-enterprise-1.preview.emergentagent.com/inteligencia-comercial`
- **Portal Proveedores**: `https://erp-crm-enterprise-1.preview.emergentagent.com/portal-proveedores`
- **CRM Principal**: `https://erp-crm-enterprise-1.preview.emergentagent.com/login`

---

*Documentación generada para EDARSAHUB - CRM COMERCIAL ENTERPRISE*
*Última actualización: Diciembre 2025*
