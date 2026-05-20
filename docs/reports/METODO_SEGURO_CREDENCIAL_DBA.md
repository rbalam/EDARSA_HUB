# MÉTODO SEGURO PARA REGISTRAR CREDENCIAL DBA

**Fecha**: 2025-12-19  
**Fase**: P0D - Diagnóstico Ejecutor B  
**Usuario Autorizado**: ricardo@edarsa.com.mx (SuperAdministrador)

---

## RESUMEN

Se ha implementado un endpoint seguro para registrar la credencial DBA/SA sin exponerla en chat, logs o frontend.

## VALIDACIONES COMPLETADAS

| Verificación | Estado |
|--------------|--------|
| SERVER_SECRET_KEY configurada | ✅ |
| Secret Manager funcional | ✅ |
| Cifrado Fernet disponible | ✅ |
| Key fingerprint | d60eba8b |
| Endpoint /api/admin/dba-credential | ✅ Registrado |

---

## CÓMO USAR (OPCIÓN A - Frontend)

### Paso 1: Iniciar sesión como SuperAdministrador
```
Email: ricardo@edarsa.com.mx
Password: [tu contraseña actual]
```

### Paso 2: Verificar estado del sistema
```bash
# En el navegador o con curl autenticado:
GET /api/admin/dba-credential/status
```

### Paso 3: Registrar credencial DBA
**Opción Frontend**: En el módulo de Servidores/Administración, buscar la opción para registrar credencial DBA.

**Opción API directa** (con token válido):
```bash
curl -X POST "https://[tu-dominio]/api/admin/dba-credential/register" \
  -H "Authorization: Bearer [TU_TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{"password":"[CONTRASEÑA_SA_AQUÍ]"}'
```

La contraseña:
- Se cifra inmediatamente con Fernet
- NUNCA se loguea
- NUNCA se devuelve al frontend
- Se almacena temporalmente en memoria (se pierde al reiniciar)

### Paso 4: Probar conexión DBA
```bash
GET /api/admin/dba-credential/test-connection
```

### Paso 5: Ejecutar diagnóstico
```bash
POST /api/admin/dba-credential/execute-diagnostic
```

Esto ejecutará las consultas de `/app/docs/reports/CONSULTAS_DBA_EJECUTAR_CON_SA.sql` y retornará:
- Jobs activos
- Steps sospechosos (que mencionan las tablas afectadas)
- Schedules cada 5-10 minutos
- Historial reciente
- Lista de sospechosos

### Paso 6: Limpiar credencial (después del diagnóstico)
```bash
DELETE /api/admin/dba-credential/clear
```

---

## OPCIÓN B - Variable de Entorno Temporal

Si prefieres no usar el endpoint, puedes:

1. Conectarte por SSH al servidor
2. Exportar temporalmente:
   ```bash
   export DBA_SA_PASSWORD="[contraseña]"
   ```
3. Ejecutar el script de diagnóstico
4. Eliminar la variable:
   ```bash
   unset DBA_SA_PASSWORD
   ```

---

## SEGURIDAD IMPLEMENTADA

| Control | Implementación |
|---------|---------------|
| Cifrado | Fernet (AES-128-CBC) |
| Almacenamiento | Memoria temporal (no persistido) |
| Acceso | Solo SuperAdministrador |
| Logs | Sin exposición de secretos |
| Auditoría | Registro de acciones (sin contraseña) |
| Frontend | Nunca recibe la contraseña |

---

## PRÓXIMOS PASOS

1. **Registrar la credencial SA** usando el método preferido
2. **Ejecutar diagnóstico** para identificar el Ejecutor B
3. **Documentar hallazgos** sin modificar jobs
4. **Solicitar autorización** para acciones correctivas
5. **Limpiar credencial** después del diagnóstico

---

## ENDPOINTS DISPONIBLES

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/admin/dba-credential/status | Estado del sistema |
| POST | /api/admin/dba-credential/register | Registrar credencial (cifrada) |
| GET | /api/admin/dba-credential/test-connection | Probar conexión |
| POST | /api/admin/dba-credential/execute-diagnostic | Ejecutar diagnóstico |
| DELETE | /api/admin/dba-credential/clear | Eliminar credencial de memoria |
