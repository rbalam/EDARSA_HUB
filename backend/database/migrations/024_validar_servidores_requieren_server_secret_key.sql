/* ============================================================
   EDARSAHUB - VALIDACIÓN SERVIDORES QUE REQUIEREN SERVER_SECRET_KEY
   No expone passwords ni api keys.
   No modifica datos.
   ============================================================ */

SET NOCOUNT ON;

SELECT
    nombre,
    system_type,
    tipo_conexion,
    host,
    port,
    database_name,
    CASE 
        WHEN username IS NULL OR LTRIM(RTRIM(username)) = '' THEN 'SIN_USUARIO'
        ELSE 'USUARIO_CONFIGURADO'
    END AS usuario_status,
    CASE 
        WHEN password_encrypted IS NULL OR LTRIM(RTRIM(password_encrypted)) = '' THEN 'SIN_PASSWORD'
        ELSE 'PASSWORD_ENCRYPTED_CONFIGURADO'
    END AS password_status,
    CASE 
        WHEN api_url IS NULL OR LTRIM(RTRIM(api_url)) = '' THEN 'SIN_API_URL'
        ELSE 'API_URL_CONFIGURADA'
    END AS api_url_status,
    CASE 
        WHEN api_key_encrypted IS NULL OR LTRIM(RTRIM(api_key_encrypted)) = '' THEN 'SIN_API_KEY'
        ELSE 'API_KEY_ENCRYPTED_CONFIGURADA'
    END AS api_key_status,
    activo,
    visible_en_operaciones,
    source_status,
    ultimo_error_sync
FROM dbo.Servidores_Conexiones
WHERE activo = 1
  AND (
        password_encrypted IS NOT NULL
        OR api_key_encrypted IS NOT NULL
      )
ORDER BY system_type, nombre;


/* ============================================================
   Validación específica de servidores comerciales críticos
   ============================================================ */

SELECT
    nombre,
    system_type,
    tipo_conexion,
    host,
    port,
    database_name,
    CASE 
        WHEN username IS NULL OR LTRIM(RTRIM(username)) = '' THEN 'SIN_USUARIO'
        ELSE 'USUARIO_CONFIGURADO'
    END AS usuario_status,
    CASE 
        WHEN password_encrypted IS NULL OR LTRIM(RTRIM(password_encrypted)) = '' THEN 'SIN_PASSWORD'
        ELSE 'PASSWORD_ENCRYPTED_CONFIGURADO'
    END AS password_status,
    CASE 
        WHEN api_key_encrypted IS NULL OR LTRIM(RTRIM(api_key_encrypted)) = '' THEN 'SIN_API_KEY'
        ELSE 'API_KEY_ENCRYPTED_CONFIGURADA'
    END AS api_key_status,
    activo,
    source_status,
    ultimo_error_sync
FROM dbo.Servidores_Conexiones
WHERE nombre LIKE '%CIENFUEGOS%'
   OR nombre LIKE '%130%'
   OR nombre LIKE '%ESTELAR%'
   OR nombre LIKE '%ManagmentPro%'
   OR nombre LIKE '%ManagementPro%'
   OR nombre LIKE '%MPRO%'
ORDER BY nombre;
