# Script para inicializar a base de dados PostgreSQL no Azure
# Execute este script após o deployment com azd

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerName,
    
    [Parameter(Mandatory=$true)]
    [string]$AdminUser,
    
    [Parameter(Mandatory=$true)]
    [string]$AdminPassword,
    
    [Parameter(Mandatory=$false)]
    [string]$DatabaseName = "cryptodashboard",
    
    [Parameter(Mandatory=$false)]
    [string]$SchemaFile = "database/tablesv2.sql"
)

Write-Host "🔄 Inicializando base de dados PostgreSQL no Azure..." -ForegroundColor Cyan
Write-Host ""

# Verificar se o ficheiro de schema existe
if (-not (Test-Path $SchemaFile)) {
    Write-Host "❌ Erro: Ficheiro de schema não encontrado: $SchemaFile" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Configuração:" -ForegroundColor Yellow
Write-Host "  Servidor: $ServerName"
Write-Host "  Database: $DatabaseName"
Write-Host "  User: $AdminUser"
Write-Host "  Schema: $SchemaFile"
Write-Host ""

# Criar a string de conexão
$env:PGPASSWORD = $AdminPassword

Write-Host "🔌 A ligar ao servidor PostgreSQL..." -ForegroundColor Cyan

# Testar conexão
$testQuery = "SELECT version();"
$testResult = psql -h $ServerName -U $AdminUser -d postgres -c $testQuery 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao ligar ao servidor PostgreSQL" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}

Write-Host "✅ Conexão estabelecida com sucesso!" -ForegroundColor Green
Write-Host ""

# Aplicar o schema
Write-Host "📝 A aplicar schema da base de dados..." -ForegroundColor Cyan
$result = psql -h $ServerName -U $AdminUser -d $DatabaseName -f $SchemaFile 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao aplicar schema" -ForegroundColor Red
    Write-Host $result
    exit 1
}

Write-Host "✅ Schema aplicado com sucesso!" -ForegroundColor Green
Write-Host ""

# Verificar tabelas criadas
Write-Host "🔍 A verificar tabelas criadas..." -ForegroundColor Cyan
$tablesQuery = "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
$tables = psql -h $ServerName -U $AdminUser -d $DatabaseName -c $tablesQuery -t

Write-Host "📊 Tabelas criadas:" -ForegroundColor Green
Write-Host $tables
Write-Host ""

Write-Host "✅ Inicialização da base de dados concluída com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "ℹ️  Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. Aceder à aplicação web no URL fornecido pelo deployment"
Write-Host "  2. Criar conta de administrador"
Write-Host "  3. Configurar chaves de API (CoinGecko, CardanoScan) na tabela t_api_coingecko e t_api_cardano"
Write-Host ""

# Limpar password da memória
$env:PGPASSWORD = $null
