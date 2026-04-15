param(
    [switch]$SkipInstall,
    [switch]$SkipIngest,
    [switch]$SkipTests,
    [switch]$NoStart,
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Title,
        [scriptblock]$Action
    )

    Write-Host "`n==> $Title" -ForegroundColor Cyan
    & $Action
}

function Invoke-Checked {
    param(
        [string]$Executable,
        [string[]]$Arguments
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        $argText = ($Arguments -join " ")
        throw "Command failed: $Executable $argText"
    }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Invoke-Step "Creating virtual environment" {
        python -m venv .venv
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python not found at $venvPython"
}

if (-not $SkipInstall) {
    Invoke-Step "Installing dependencies" {
        Invoke-Checked $venvPython @("-m", "pip", "install", "--upgrade", "pip")
        Invoke-Checked $venvPython @("-m", "pip", "install", "-r", "requirements.txt")
    }
}

$env:PYTHONPATH = "src"

if (-not $SkipIngest) {
    Invoke-Step "Ingesting sample documents" {
        Invoke-Checked $venvPython @("-m", "traceable_ai_compliance_agent.ingest_cli")
    }
}

if (-not $SkipTests) {
    Invoke-Step "Ensuring pytest is available" {
        Invoke-Checked $venvPython @("-m", "pip", "install", "pytest")
    }

    Invoke-Step "Running pytest smoke/API tests" {
        Invoke-Checked $venvPython @("-m", "pytest", "tests/test_api.py", "tests/test_smoke.py")
    }

    Invoke-Step "Running end-to-end smoke script" {
        Invoke-Checked $venvPython @("tools/run_e2e_smoke.py")
    }
}

if ($NoStart) {
    Write-Host "`nAll setup/test steps completed. Server start skipped (-NoStart)." -ForegroundColor Green
    exit 0
}

Invoke-Step "Starting API server (frontend served at /)" {
    Write-Host "Backend: http://$BindHost`:$Port" -ForegroundColor Green
    Write-Host "Frontend: http://$BindHost`:$Port/" -ForegroundColor Green
    & $venvPython -m uvicorn traceable_ai_compliance_agent.api:app --host $BindHost --port $Port
}