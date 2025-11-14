# Script de validacao pre-deployment
# Verifica se todos os pre-requisitos estao cumpridos

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$hasErrors = $false

Write-Host "=== Validacao de Pre-requisitos para Deployment no Azure ===" -ForegroundColor Cyan
Write-Host ""

# ========================================
# 1. Verificar ferramentas instaladas
# ========================================
Write-Host "[1/7] Verificando ferramentas instaladas..." -ForegroundColor Yellow

# Azure CLI
try {
    $azVersion = az version --output json 2>$null | ConvertFrom-Json
    if ($azVersion) {
        Write-Host "  [OK] Azure CLI: $($azVersion.'azure-cli')" -ForegroundColor Green
    }
} catch {
    Write-Host "  [ERRO] Azure CLI nao encontrada. Instale: winget install Microsoft.AzureCLI" -ForegroundColor Red
    $hasErrors = $true
}

# Azure Developer CLI
try {
    $azdVersion = azd version 2>$null
    if ($azdVersion) {
        Write-Host "  [OK] Azure Developer CLI: $azdVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "  [ERRO] Azure Developer CLI nao encontrada. Instale: winget install Microsoft.Azd" -ForegroundColor Red
    $hasErrors = $true
}

# PostgreSQL Client
try {
    $psqlVersion = psql --version 2>$null
    if ($psqlVersion) {
        Write-Host "  [OK] PostgreSQL Client: $psqlVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "  [AVISO] PostgreSQL Client nao encontrado (opcional)" -ForegroundColor Yellow
}

Write-Host ""

# ========================================
# 2. Verificar autenticacao Azure
# ========================================
Write-Host "[2/7] Verificando autenticacao Azure..." -ForegroundColor Yellow

try {
    $azAccount = az account show 2>$null | ConvertFrom-Json
    if ($azAccount) {
        Write-Host "  [OK] Azure CLI autenticado: $($azAccount.user.name)" -ForegroundColor Green
        Write-Host "       Subscription: $($azAccount.name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  [ERRO] Azure CLI nao autenticado. Execute: az login" -ForegroundColor Red
    $hasErrors = $true
}

Write-Host ""

# ========================================
# 3. Verificar ficheiros necessarios
# ========================================
Write-Host "[3/7] Verificando ficheiros necessarios..." -ForegroundColor Yellow

$requiredFiles = @(
    "azure.yaml",
    "infra/main.bicep",
    "infra/main.parameters.json",
    "database/tablesv2.sql",
    "requirements.txt",
    "app.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [ERRO] $file nao encontrado" -ForegroundColor Red
        $hasErrors = $true
    }
}

Write-Host ""

# ========================================
# 4. Verificar modulos Bicep
# ========================================
Write-Host "[4/7] Verificando modulos Bicep..." -ForegroundColor Yellow

$bicepModules = @(
    "infra/resources/identity.bicep",
    "infra/resources/monitoring.bicep",
    "infra/resources/keyvault.bicep",
    "infra/resources/database.bicep",
    "infra/resources/web.bicep"
)

foreach ($module in $bicepModules) {
    if (Test-Path $module) {
        Write-Host "  [OK] $module" -ForegroundColor Green
    } else {
        Write-Host "  [ERRO] $module nao encontrado" -ForegroundColor Red
        $hasErrors = $true
    }
}

Write-Host ""

# ========================================
# 5. Validar sintaxe Bicep
# ========================================
Write-Host "[5/7] Validando sintaxe Bicep..." -ForegroundColor Yellow

try {
    $bicepBuild = az bicep build --file infra/main.bicep 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Sintaxe Bicep valida" -ForegroundColor Green
    } else {
        Write-Host "  [ERRO] Erros de sintaxe Bicep:" -ForegroundColor Red
        Write-Host $bicepBuild -ForegroundColor Red
        $hasErrors = $true
    }
} catch {
    Write-Host "  [AVISO] Nao foi possivel validar Bicep" -ForegroundColor Yellow
}

Write-Host ""

# ========================================
# 6. Verificar azure.yaml
# ========================================
Write-Host "[6/7] Verificando azure.yaml..." -ForegroundColor Yellow

if (Test-Path "azure.yaml") {
    $azureYaml = Get-Content "azure.yaml" -Raw
    
    if ($azureYaml -match "name:\s*\S+") {
        Write-Host "  [OK] Projeto configurado" -ForegroundColor Green
    } else {
        Write-Host "  [ERRO] Nome do projeto nao definido em azure.yaml" -ForegroundColor Red
        $hasErrors = $true
    }
    
    if ($azureYaml -match "host:\s*appservice") {
        Write-Host "  [OK] Host configurado para App Service" -ForegroundColor Green
    } else {
        Write-Host "  [AVISO] Host nao configurado para App Service" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [ERRO] azure.yaml nao encontrado" -ForegroundColor Red
    $hasErrors = $true
}

Write-Host ""

# ========================================
# 7. Verificar requirements.txt
# ========================================
Write-Host "[7/7] Verificando dependencias Python..." -ForegroundColor Yellow

if (Test-Path "requirements.txt") {
    $requirements = Get-Content "requirements.txt"
    
    $criticalPackages = @("streamlit", "psycopg2-binary", "python-dotenv")
    
    foreach ($package in $criticalPackages) {
        if ($requirements -match $package) {
            Write-Host "  [OK] $package encontrado" -ForegroundColor Green
        } else {
            Write-Host "  [ERRO] $package nao encontrado em requirements.txt" -ForegroundColor Red
            $hasErrors = $true
        }
    }
} else {
    Write-Host "  [ERRO] requirements.txt nao encontrado" -ForegroundColor Red
    $hasErrors = $true
}

Write-Host ""

# ========================================
# RESUMO
# ========================================
Write-Host "===============================================" -ForegroundColor Cyan
if ($hasErrors) {
    Write-Host "VALIDACAO FALHOU" -ForegroundColor Red
    Write-Host "Corrija os erros acima antes de fazer deployment" -ForegroundColor Red
    Write-Host "===============================================" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "VALIDACAO COMPLETA - PRONTO PARA DEPLOYMENT" -ForegroundColor Green
    Write-Host ""
    Write-Host "Proximos passos:" -ForegroundColor Yellow
    Write-Host "  1. azd up          # Deploy completo" -ForegroundColor White
    Write-Host "  2. Aguardar conclusao (~10-15 min)" -ForegroundColor White
    Write-Host "  3. Executar script de inicializacao da BD" -ForegroundColor White
    Write-Host "===============================================" -ForegroundColor Cyan
    exit 0
}
