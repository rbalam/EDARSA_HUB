param(
    [string]$TunnelId,
    [string]$ProfileName = "edarsa-sql-auditor",
    [string]$RequesterEmail = "carlosruz@edarsa.com.mx",
    [string]$EdarsaHubHost = "54.39.104.176",
    [int]$EdarsaHubPort = 1433,
    [string]$EdarsaHubDatabase = "EDARSAHUB",
    [string]$EdarsaHubUser = "HRLectura",
    [string]$CienfuegosUser = "CF_Auditor_SQL",
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Save-CredentialSecret {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$UserName,
        [Parameter(Mandatory = $true)][Security.SecureString]$Secret
    )

    $credential = [PSCredential]::new($UserName, $Secret)
    $credential | Export-Clixml -Path $Path -Force
}

function Get-PlainSecret {
    param([Parameter(Mandatory = $true)][string]$Path)
    $credential = Import-Clixml -Path $Path
    return $credential.GetNetworkCredential().Password
}

function Remove-AuditorEnvironment {
    @(
        "EDARSA_SQL_AUDITOR_REQUESTER_EMAIL",
        "EDARSAHUB_SQL_HOST",
        "EDARSAHUB_SQL_PORT",
        "EDARSAHUB_SQL_DATABASE",
        "EDARSAHUB_SQL_USER",
        "EDARSAHUB_SQL_PASSWORD",
        "EDARSA_SQL_AUDITOR_CF_USER",
        "EDARSA_SQL_AUDITOR_CF_PASSWORD",
        "EDARSA_SQL_AUDITOR_TRANSPORT",
        "CONTROL_PLANE_API_KEY"
    ) | ForEach-Object {
        Remove-Item "Env:$_" -ErrorAction SilentlyContinue
    }
}

$mcpDir = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $mcpDir ".venv\Scripts\python.exe"
$serverPath = Join-Path $mcpDir "server.py"
$testPath = Join-Path $mcpDir "test_readonly_policy.py"

if (-not (Test-Path $pythonPath)) {
    throw "No existe el entorno virtual esperado: $pythonPath"
}
if (-not (Test-Path $serverPath)) {
    throw "No existe server.py: $serverPath"
}

$stateDir = Join-Path $env:LOCALAPPDATA "EDARSA\SQLAuditor"
$secretDir = Join-Path $stateDir "secrets"
$downloadDir = Join-Path $stateDir "downloads"
$binRoot = Join-Path $stateDir "bin"
New-Item -ItemType Directory -Force -Path $stateDir, $secretDir, $downloadDir, $binRoot | Out-Null

if ([string]::IsNullOrWhiteSpace($TunnelId)) {
    $TunnelId = Read-Host "Tunnel ID de OpenAI (tunnel_...)"
}
if ([string]::IsNullOrWhiteSpace($TunnelId) -or -not $TunnelId.StartsWith("tunnel_")) {
    throw "TunnelId invalido. Debe comenzar con tunnel_."
}

Write-Host "Configuracion segura de EDARSA SQL Auditor"
Write-Host "Las contrasenas se guardaran cifradas con Windows DPAPI para el usuario actual."

$hrSecret = Read-Host "Contrasena SQL de $EdarsaHubUser en EDARSAHUB" -AsSecureString
$cfSecret = Read-Host "Contrasena SQL de $CienfuegosUser en CIENFUEGOS" -AsSecureString
$tunnelSecret = Read-Host "OpenAI Tunnel Runtime API Key" -AsSecureString

$hrSecretPath = Join-Path $secretDir "edarsahub_hrlectura.credential.xml"
$cfSecretPath = Join-Path $secretDir "cienfuegos_auditor.credential.xml"
$tunnelSecretPath = Join-Path $secretDir "openai_tunnel_runtime.credential.xml"

Save-CredentialSecret -Path $hrSecretPath -UserName $EdarsaHubUser -Secret $hrSecret
Save-CredentialSecret -Path $cfSecretPath -UserName $CienfuegosUser -Secret $cfSecret
Save-CredentialSecret -Path $tunnelSecretPath -UserName "openai-tunnel-runtime" -Secret $tunnelSecret

$hrSecret = $null
$cfSecret = $null
$tunnelSecret = $null

$architecture = switch ($env:PROCESSOR_ARCHITECTURE.ToUpperInvariant()) {
    "AMD64" { "amd64" }
    "ARM64" { "arm64" }
    default { throw "Arquitectura Windows no soportada automaticamente: $env:PROCESSOR_ARCHITECTURE" }
}

Write-Host "Descargando la version oficial mas reciente de OpenAI tunnel-client..."
$release = Invoke-RestMethod `
    -Uri "https://api.github.com/repos/openai/tunnel-client/releases/latest" `
    -Headers @{ "User-Agent" = "EDARSA-SQL-Auditor" }

$expectedName = "tunnel-client-$($release.tag_name)-windows-$architecture.zip"
$asset = $release.assets | Where-Object { $_.name -eq $expectedName } | Select-Object -First 1
if (-not $asset) {
    throw "No se encontro el asset oficial esperado: $expectedName"
}

$zipPath = Join-Path $downloadDir $asset.name
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath

if ($asset.digest -and $asset.digest.StartsWith("sha256:")) {
    $expectedHash = $asset.digest.Substring(7).ToLowerInvariant()
    $actualHash = (Get-FileHash -Algorithm SHA256 -Path $zipPath).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        throw "SHA256 de tunnel-client no coincide con el publicado por OpenAI."
    }
}

$installDir = Join-Path $binRoot "$($release.tag_name)-windows-$architecture"
if (Test-Path $installDir) {
    Remove-Item $installDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $installDir -Force
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

$tunnelExe = Get-ChildItem -Path $installDir -Recurse -Filter "tunnel-client.exe" | Select-Object -First 1
if (-not $tunnelExe) {
    throw "No se encontro tunnel-client.exe despues de extraer el paquete oficial."
}
$tunnelExePath = $tunnelExe.FullName

$config = [ordered]@{
    version = 1
    profile_name = $ProfileName
    tunnel_id = $TunnelId
    requester_email = $RequesterEmail
    edarsahub_host = $EdarsaHubHost
    edarsahub_port = $EdarsaHubPort
    edarsahub_database = $EdarsaHubDatabase
    edarsahub_user = $EdarsaHubUser
    cienfuegos_user = $CienfuegosUser
    mcp_dir = $mcpDir
    python_path = $pythonPath
    server_path = $serverPath
    tunnel_exe = $tunnelExePath
    tunnel_client_release = $release.tag_name
}
$configPath = Join-Path $stateDir "settings.json"
$config | ConvertTo-Json -Depth 5 | Set-Content -Path $configPath -Encoding UTF8

$hrPassword = $null
$cfPassword = $null
$tunnelApiKey = $null

try {
    $hrPassword = Get-PlainSecret -Path $hrSecretPath
    $cfPassword = Get-PlainSecret -Path $cfSecretPath
    $tunnelApiKey = Get-PlainSecret -Path $tunnelSecretPath

    $env:EDARSA_SQL_AUDITOR_REQUESTER_EMAIL = $RequesterEmail
    $env:EDARSAHUB_SQL_HOST = $EdarsaHubHost
    $env:EDARSAHUB_SQL_PORT = [string]$EdarsaHubPort
    $env:EDARSAHUB_SQL_DATABASE = $EdarsaHubDatabase
    $env:EDARSAHUB_SQL_USER = $EdarsaHubUser
    $env:EDARSAHUB_SQL_PASSWORD = $hrPassword
    $env:EDARSA_SQL_AUDITOR_CF_USER = $CienfuegosUser
    $env:EDARSA_SQL_AUDITOR_CF_PASSWORD = $cfPassword
    $env:EDARSA_SQL_AUDITOR_TRANSPORT = "stdio"
    $env:CONTROL_PLANE_API_KEY = $tunnelApiKey

    Push-Location $mcpDir
    try {
        Write-Host "Ejecutando pruebas de politica readonly..."
        & $pythonPath -m pytest -q $testPath
        if ($LASTEXITCODE -ne 0) {
            throw "Las pruebas readonly fallaron. No se configurara el tunel."
        }

        Write-Host "Ejecutando canario RBAC..."
        & $pythonPath -c "from server import _authorize; print(_authorize())"
        if ($LASTEXITCODE -ne 0) {
            throw "El canario RBAC fallo. No se configurara el tunel."
        }
    }
    finally {
        Pop-Location
    }

    $mcpCommand = '"' + $pythonPath + '" "' + $serverPath + '"'

    Write-Host "Inicializando perfil Secure MCP Tunnel: $ProfileName"
    & $tunnelExePath init `
        --sample sample_mcp_stdio_local `
        --profile $ProfileName `
        --tunnel-id $TunnelId `
        --mcp-command $mcpCommand
    if ($LASTEXITCODE -ne 0) {
        throw "tunnel-client init fallo."
    }

    Write-Host "Ejecutando diagnostico del tunel..."
    & $tunnelExePath doctor --profile $ProfileName --explain
    if ($LASTEXITCODE -ne 0) {
        throw "tunnel-client doctor reporto un error."
    }

    Write-Host ""
    Write-Host "CONFIGURACION COMPLETADA"
    Write-Host "Perfil: $ProfileName"
    Write-Host "Tunnel ID: $TunnelId"
    Write-Host "Estado local: $stateDir"
    Write-Host "Las contrasenas NO fueron guardadas en el repositorio."

    if ($StartNow) {
        Write-Host "Iniciando el tunel. Deja esta ventana abierta durante la prueba de ChatGPT."
        & $tunnelExePath run --profile $ProfileName
        if ($LASTEXITCODE -ne 0) {
            throw "tunnel-client run termino con error."
        }
    }
}
finally {
    $hrPassword = $null
    $cfPassword = $null
    $tunnelApiKey = $null
    Remove-AuditorEnvironment
}
