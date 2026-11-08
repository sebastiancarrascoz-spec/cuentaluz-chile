$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Falta el entorno .venv. Sigue la instalación del README.md.'
}
$taskUrl = 'http://127.0.0.1:8018'
$taskRunning = $false
try {
    $taskHealth = Invoke-RestMethod -Uri "$taskUrl/health/live" -TimeoutSec 2
    $taskRunning = $taskHealth.version -eq '2.0.0'
} catch { }
if (-not $taskRunning) {
    $taskArtifacts = Join-Path $PSScriptRoot 'artifacts'
    New-Item -ItemType Directory -Force -Path $taskArtifacts | Out-Null
    Start-Process -FilePath $taskPython -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8018', '--no-access-log') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskArtifacts 'servidor-salida.log') -RedirectStandardError (Join-Path $taskArtifacts 'servidor-error.log') | Out-Null
    for ($taskAttempt = 0; $taskAttempt -lt 20; $taskAttempt++) {
        try {
            $taskHealth = Invoke-RestMethod -Uri "$taskUrl/health/live" -TimeoutSec 1
            if ($taskHealth.version -eq '2.0.0') { $taskRunning = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
}
if (-not $taskRunning) { throw 'No se pudo iniciar CuentaLuz. Revisa artifacts/servidor-error.log.' }
Start-Process $taskUrl
