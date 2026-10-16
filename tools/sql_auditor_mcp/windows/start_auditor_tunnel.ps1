param(
    [string]$ProfileName = "edarsa-sql-auditor"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

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

$stateDir = Join-Path $env:LOCALAPPDATA "EDARSA\SQLAuditor"
$configPath = Join-Path $stateDir "settings.json"
$secretDir = Join-Path $stateDir "secrets"

if (-not (Test-Path $configPath)) {
    throw "SQL Auditor no esta configurado. Ejecuta primero windows\setup_auditor_tunnel.ps1"
}

$config = Get-Content -Raw -Path $configPath | ConvertFrom-Json
if ($ProfileName -eq "edarsa-sql-auditor" -and $config.profile_name) {
    $ProfileName = [string]$config.profile_name
}

$hrSecretPath = Join-Path $secretDir "edarsahub_hrlectura.credential.xml"
$cfSecretPath = Join-Path $secretDir "cienfuegos_auditor.credential.xml"
$tunnelSecretPath = Join-Path $secretDir "openai_tunnel_runtime.credential.xml"

foreach ($requiredPath in @($hrSecretPath, $cfSecretPath, $tunnelSecretPath)) {
    if (-not (Test-Path $requiredPath)) {
        throw "Falta secreto local protegido: $requiredPath. Ejecuta setup nuevamente."
    }
}

$hrPassword = $null
$cfPassword = $null
$tunnelApiKey = $null

try {
    $hrPassword = Get-PlainSecret -Path $hrSecretPath
    $cfPassword = Get-PlainSecret -Path $cfSecretPath
    $tunnelApiKey = Get-PlainSecret -Path $tunnelSecretPath

    $env:EDARSA_SQL_AUDITOR_REQUESTER_EMAIL = [string]$config.requester_email
    $env:EDARSAHUB_SQL_HOST = [string]$config.edarsahub_host
    $env:EDARSAHUB_SQL_PORT = [string]$config.edarsahub_port
    $env:EDARSAHUB_SQL_DATABASE = [string]$config.edarsahub_database
    $env:EDARSAHUB_SQL_USER = [string]$config.edarsahub_user
    $env:EDARSAHUB_SQL_PASSWORD = $hrPassword
    $env:EDARSA_SQL_AUDITOR_CF_USER = [string]$config.cienfuegos_user
    $env:EDARSA_SQL_AUDITOR_CF_PASSWORD = $cfPassword
    $env:EDARSA_SQL_AUDITOR_TRANSPORT = "stdio"
    $env:CONTROL_PLANE_API_KEY = $tunnelApiKey

    if (-not (Test-Path ([string]$config.tunnel_exe))) {
        throw "No existe tunnel-client.exe en la ruta registrada. Ejecuta setup nuevamente."
    }

    Write-Host "Iniciando EDARSA SQL Auditor por Secure MCP Tunnel..."
    Write-Host "Perfil: $ProfileName"
    Write-Host "Presiona Ctrl+C para detenerlo."

    & ([string]$config.tunnel_exe) run --profile $ProfileName
    if ($LASTEXITCODE -ne 0) {
        throw "tunnel-client termino con codigo $LASTEXITCODE"
    }
}
finally {
    $hrPassword = $null
    $cfPassword = $null
    $tunnelApiKey = $null
    Remove-AuditorEnvironment
}
