# EDARSA HUB - Checklist de Deployment a Producción

## 📋 PASO A PASO COMPLETO

---

## FASE 1: PREPARACIÓN (Antes del Deploy)

### ✅ 1.1 Verificar Estado de la Aplicación
- [ ] Login funciona correctamente
- [ ] Dashboard comercial carga (aunque muestre offline por VPN)
- [ ] Gestión de usuarios funciona
- [ ] RBAC funciona correctamente
- [ ] No hay errores críticos en consola

### ✅ 1.2 Guardar Código en GitHub
- [ ] Hacer clic en **"Save to GitHub"** en el chat de Emergent
- [ ] Verificar que el repositorio esté actualizado
- [ ] Anotar el último commit por si necesitas rollback

### ✅ 1.3 Preparar Variables de Entorno
- [ ] Generar nuevo `JWT_SECRET` seguro para producción
  ```
  # Ejemplo de generación (usa un generador de passwords)
  JWT_SECRET=EDARSA_PROD_2026_xK9mN2pL5qR8vT3wY6zA
  ```
- [ ] Tener a mano contraseña real de `EMAIL_PASSWORD`
- [ ] Definir `CORS_ORIGINS` (tu dominio de producción)
- [ ] Verificar credenciales de Twilio (si usas WhatsApp)

### ✅ 1.4 Verificar Conectividad de Servidores SQL
- [ ] Confirmar que los hosts DDNS están activos:
  - `servercien...` (CIENFUEGOS)
  - `serverestelar.ddns.net` (LA ESTELAR)
  - `130mid.ddns.net` (130° MERIDA)
  - `54.39.104.176` (ManagementPro)
- [ ] Verificar puertos abiertos (1433, 6969)
- [ ] Si usas VPN, tener configuración lista

---

## FASE 2: DEPLOYMENT EN EMERGENT

### ✅ 2.1 Iniciar Deployment
- [ ] Ir a la interfaz de Emergent
- [ ] Hacer clic en el botón **"Deploy"**
- [ ] Hacer clic en **"Deploy Now"**

### ✅ 2.2 Configurar Variables de Entorno
Durante o después del deploy, configurar:

```env
# Base de Datos
MONGO_URL=mongodb://localhost:27017
DB_NAME=edarsa_hub

# Seguridad
JWT_SECRET=[TU_CLAVE_SEGURA_PRODUCCION]
JWT_EXPIRATION_HOURS=72
CORS_ORIGINS=https://tu-dominio.com

# Email
EMAIL_HOST=mail.edarsa.com.mx
EMAIL_PORT=587
EMAIL_USER=notificaciones@edarsa.com.mx
EMAIL_PASSWORD=[TU_PASSWORD_REAL]
EMAIL_USE_TLS=true
EMAIL_FROM=notificaciones@edarsa.com.mx
EMAIL_FROM_NAME=EDARSA HUB
EMAIL_ENABLED=true
ALERT_EMAIL_TO=admin@edarsa.com.mx

# APIs MPRO
API_MPRO_QRO_URL=http://54.39.104.176:8001/query
API_MPRO_ORIGEN_URL=http://54.39.104.176:8000/query
API_MPRO_KEY=EDARSA_2026_SECURE_KEY

# WhatsApp (opcional)
TWILIO_ACCOUNT_SID=[TU_SID]
TWILIO_AUTH_TOKEN=[TU_TOKEN]
TWILIO_WHATSAPP_FROM=+14155238886
WHATSAPP_ENABLED=true
```

### ✅ 2.3 Esperar Deployment
- [ ] Esperar 10-15 minutos mientras se crea el entorno
- [ ] Observar el progreso en la interfaz de Emergent
- [ ] NO cerrar la ventana durante el proceso

### ✅ 2.4 Obtener URL de Producción
- [ ] Anotar la URL de producción proporcionada
- [ ] Ejemplo: `https://edarsa-hub-xxx.emergent.app`

---

## FASE 3: CONFIGURACIÓN POST-DEPLOYMENT

### ✅ 3.1 Actualizar REACT_APP_BACKEND_URL
- [ ] Ir a configuración de variables de entorno
- [ ] Actualizar:
  ```
  REACT_APP_BACKEND_URL=https://tu-url-produccion.emergent.app
  ```
- [ ] Redesplegar si es necesario

### ✅ 3.2 Configurar Dominio Personalizado (Opcional)
- [ ] Si tienes dominio propio (ej: hub.edarsa.com.mx):
  - Ir a configuración de dominio en Emergent
  - Agregar tu dominio
  - Configurar DNS (CNAME o A record)
  - Esperar propagación DNS (hasta 24h)

---

## FASE 4: VERIFICACIÓN POST-DEPLOYMENT

### ✅ 4.1 Pruebas Básicas
- [ ] Abrir URL de producción en navegador
- [ ] Verificar que carga sin errores
- [ ] Verificar HTTPS (candado verde)

### ✅ 4.2 Prueba de Login
- [ ] Login con SuperAdministrador:
  ```
  Email: ricardo@edarsa.com.mx
  Password: Ricardo2024
  ```
- [ ] Verificar que el token se genera correctamente
- [ ] Verificar que el menú carga completo

### ✅ 4.3 Prueba de Conectividad SQL
- [ ] Ir a Dashboard Comercial
- [ ] Verificar que los servidores aparecen **Online** (no Offline)
- [ ] Si aparecen Offline:
  - Verificar conectividad de red a los hosts
  - Revisar logs del backend
  - Verificar configuración de VPN si aplica

### ✅ 4.4 Pruebas Funcionales
- [ ] Crear un usuario de prueba
- [ ] Editar un usuario existente
- [ ] Verificar Bitácora RBAC registra operaciones
- [ ] Probar tab de Estructura
- [ ] Verificar datos de ventas en Dashboard

### ✅ 4.5 Prueba de Email (Opcional)
- [ ] Triggear una notificación por email
- [ ] Verificar que llega correctamente

---

## FASE 5: MONITOREO INICIAL

### ✅ 5.1 Primeras 24 Horas
- [ ] Monitorear que la aplicación sigue activa
- [ ] Verificar que no hay errores 500 frecuentes
- [ ] Confirmar que los dashboards cargan datos frescos
- [ ] Verificar que los usuarios pueden hacer login

### ✅ 5.2 Backup
- [ ] Verificar que tienes acceso al código en GitHub
- [ ] Documentar la URL de producción
- [ ] Guardar configuración de variables de entorno

---

## 🚨 TROUBLESHOOTING

### Si el deployment falla:
1. Revisar logs de deployment en Emergent
2. Verificar que todas las dependencias están en requirements.txt y package.json
3. Contactar soporte de Emergent si persiste

### Si los servidores SQL aparecen Offline:
1. Verificar que el servidor de producción puede alcanzar los hosts
2. Probar ping a los hosts DDNS
3. Verificar puertos (1433, 6969)
4. Revisar credenciales SQL en MongoDB (colección `servers`)

### Si el login falla:
1. Verificar JWT_SECRET está configurado
2. Verificar CORS_ORIGINS incluye tu dominio
3. Revisar logs del backend

### Si necesitas rollback:
1. Ir a la sección de deployments en Emergent
2. Seleccionar versión anterior
3. Hacer rollback (sin costo adicional)

---

## 📞 INFORMACIÓN DE SOPORTE

- **Emergent Support**: Disponible en la plataforma
- **Documentación**: /app/docs/
- **Variables de Entorno**: /app/docs/DEPLOYMENT_ENV_VARS.md

---

## ✅ CHECKLIST RESUMEN RÁPIDO

```
ANTES:
[ ] Guardar en GitHub
[ ] Preparar JWT_SECRET nuevo
[ ] Tener EMAIL_PASSWORD

DURANTE:
[ ] Click en Deploy
[ ] Configurar variables de entorno
[ ] Esperar 10-15 min

DESPUÉS:
[ ] Actualizar REACT_APP_BACKEND_URL
[ ] Probar login
[ ] Verificar servidores Online
[ ] Probar funcionalidades principales
```

---

**Costo del Deployment: 50 créditos/mes**

¡Listo para producción! 🚀
