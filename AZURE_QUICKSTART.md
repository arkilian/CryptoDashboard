# 🚀 Quick Start - Deploy para Azure

## ✅ Validação Pré-Deployment

```powershell
.\scripts\validate-deployment.ps1
```

## 🔑 Autenticação

```powershell
az login
azd auth login
```

## 📦 Deployment Completo

```powershell
# Preview (recomendado)
azd provision --preview

# Deploy completo (infraestrutura + código)
azd up
```

**Tempo estimado:** 10-15 minutos

## 🗄️ Inicializar Base de Dados

Após o deployment:

```powershell
# Obter informações
$dbServer = azd env get-value POSTGRESQL_SERVER_FQDN
$dbPassword = "<password-do-deployment>"

# Aplicar schema
.\scripts\init-azure-db.ps1 `
    -ServerName $dbServer `
    -AdminUser dbadmin `
    -AdminPassword $dbPassword
```

## 🌐 Aceder à Aplicação

```powershell
# Ver URL
azd env get-value WEB_APP_URL

# Abrir no browser
Start-Process (azd env get-value WEB_APP_URL)
```

## 📚 Documentação Completa

- **[DEPLOYMENT_AZURE.md](DEPLOYMENT_AZURE.md)** - Guia completo de deployment
- **[.azure/plan.copilotmd](.azure/plan.copilotmd)** - Plano de deployment detalhado
- **[.azure/summary.copilotmd](.azure/summary.copilotmd)** - Resumo da infraestrutura

## 💰 Custos Estimados

- **Desenvolvimento/Teste:** ~€26-30/mês
- **SKUs:** B1 (App Service) + B1ms (PostgreSQL)

## 🔧 Comandos Úteis

```powershell
# Ver logs em tempo real
az webapp log tail --resource-group rg-<env-name> --name <webapp-name>

# Atualizar código (sem reprovisionar infraestrutura)
azd deploy

# Ver todas as variáveis de ambiente
azd env get-values

# Remover tudo
azd down
```

## 🆘 Ajuda

Ver documentação completa em [DEPLOYMENT_AZURE.md](DEPLOYMENT_AZURE.md)
