# Script para configurar App Settings do Azure Web App
# Preenche os valores abaixo e executa

$dbHost = "PREENCHER"  # ex: myserver.postgres.database.azure.com
$dbPort = "5432"
$dbName = "crypto_dashboard"
$dbUser = "PREENCHER"  # ex: app_user
$dbPassword = "PREENCHER"

az webapp config appsettings set `
  --name arkilian-webapp `
  --resource-group arkilian-group `
  --settings `
    "DB_HOST=$dbHost" `
    "DB_PORT=$dbPort" `
    "DB_NAME=$dbName" `
    "DB_USER=$dbUser" `
    "DB_PASSWORD=$dbPassword" `
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true"

Write-Host "App Settings configurados com sucesso!"
