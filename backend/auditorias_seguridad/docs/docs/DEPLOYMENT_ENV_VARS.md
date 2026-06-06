# EDARSA HUB - Variables de Entorno para Deployment

## 📋 INSTRUCCIONES
1. Copia estas variables al panel de deployment de Emergent
2. Reemplaza los valores marcados con `[CAMBIAR]` por tus valores reales
3. Las variables marcadas con `[OPCIONAL]` pueden omitirse si no usas esa funcionalidad

---

## 🔐 VARIABLES OBLIGATORIAS

### Base de Datos MongoDB
```
MONGO_URL=<REDACTED_MONGO_URL>
DB_NAME=edarsa_hub
```
> ⚠️ Si usas MongoDB Atlas u otro servicio externo, cambia MONGO_URL

### Seguridad JWT
```
JWT_SECRET=[CAMBIAR] Tu clave secreta única y segura
JWT_EXPIRATION_HOURS=72
```
> ⚠️ IMPORTANTE: Genera una clave segura y única para producción

### CORS
```
CORS_ORIGINS=https://tu-dominio.com
```
> Cambia `*` por tu dominio de producción para mayor seguridad

---

## 📧 CONFIGURACIÓN DE EMAIL

```
EMAIL_HOST=mail.edarsa.com.mx
EMAIL_PORT=587
EMAIL_USER=notificaciones@edarsa.com.mx
EMAIL_PASSWORD=[CAMBIAR] Tu contraseña real
EMAIL_USE_TLS=true
EMAIL_FROM=notificaciones@edarsa.com.mx
EMAIL_FROM_NAME=EDARSA HUB
EMAIL_ENABLED=true
ALERT_EMAIL_TO=admin@edarsa.com.mx
```

---

## 📱 WHATSAPP/TWILIO [OPCIONAL]

```
TWILIO_ACCOUNT_SID=[CAMBIAR] Tu Account SID de Twilio
TWILIO_AUTH_TOKEN=[CAMBIAR] Tu Auth Token de Twilio
TWILIO_WHATSAPP_FROM=+14155238886
WHATSAPP_ENABLED=true
ALERT_WHATSAPP_TO=[CAMBIAR] Número destino (+521234567890)
```

---

## 🖥️ API MPRO (ManagementPro)

```
API_MPRO_QRO_URL=http://<REDACTED_EDARSAHUB_SQL_HOST>:8001/query
API_MPRO_ORIGEN_URL=http://<REDACTED_EDARSAHUB_SQL_HOST>:8000/query
API_MPRO_KEY=EDARSA_2026_SECURE_KEY
```
> Estas APIs deben ser accesibles desde el servidor de producción

---

## 🌐 FRONTEND

```
REACT_APP_BACKEND_URL=https://tu-dominio-produccion.com
```
> ⚠️ IMPORTANTE: Cambiar al dominio de producción después del deployment

---

## 🗄️ SERVIDORES SQL (SoftRestaurant, MPRO)

Los servidores SQL están configurados en MongoDB (colección `servers`).
No son variables de entorno, sino registros en la base de datos.

### Servidores Actuales Configurados:

| Servidor | Host | Puerto | Base de Datos | Tipo |
|----------|------|--------|---------------|------|
| ManagmentPro | <REDACTED_EDARSAHUB_SQL_HOST> | 1433 | CENTRAL2020 | MPRO |
| CIENFUEGOS | servercien....n... | 1433 | softrestaurant95pro | SoftRestaurant |
| LA ESTELAR | serverestelar.ddns.net | 6969 | softrestaurant12 | SoftRestaurant |
| 130° MERIDA | 130mid.ddns.net | 1433 | softrestaurant10 | SoftRestaurant |

### Requisitos de Conectividad:
- Los servidores SoftRestaurant usan DNS dinámico (DDNS)
- Requieren conectividad de red desde el servidor de producción
- Si están detrás de VPN, necesitarás configurar VPN en el servidor de producción

---

## 📝 NOTAS IMPORTANTES

1. **MongoDB**: El deployment de Emergent incluye MongoDB local. Si prefieres usar MongoDB Atlas, actualiza MONGO_URL.

2. **Conexiones SQL**: Los servidores SoftRestaurant/MPRO requieren:
   - Acceso de red a los hosts (VPN si es necesario)
   - Puertos abiertos (1433, 6969, etc.)
   - Credenciales SQL correctas (ya almacenadas en MongoDB)

3. **Dominio personalizado**: Después del deployment, puedes configurar un dominio personalizado en Emergent.

4. **SSL/HTTPS**: El deployment de Emergent incluye SSL automático.

---

## ✅ CHECKLIST PRE-DEPLOYMENT

- [ ] JWT_SECRET cambiado a valor único y seguro
- [ ] EMAIL_PASSWORD configurado correctamente
- [ ] CORS_ORIGINS actualizado (no usar `*` en producción)
- [ ] Verificar conectividad a servidores SQL externos
- [ ] Backup de MongoDB realizado
- [ ] Credenciales de Twilio actualizadas (si se usa WhatsApp)

---

## 🚀 DESPUÉS DEL DEPLOYMENT

1. Actualiza `REACT_APP_BACKEND_URL` con la URL de producción
2. Verifica que los servidores SQL aparezcan "Online"
3. Prueba login con SuperAdministrador
4. Verifica dashboards con datos reales
