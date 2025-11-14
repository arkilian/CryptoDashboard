# Deployment Guide - Azure Web App com PostgreSQL

Este guia explica como fazer o deployment da aplicação CryptoDashboard para o Azure usando Azure Developer CLI (azd).

## 📋 Pré-requisitos

### Ferramentas Necessárias

1. **Azure CLI** (az)
   ```powershell
   winget install Microsoft.AzureCLI
   # Ou
   # https://learn.microsoft.com/cli/azure/install-azure-cli
   ```

2. **Azure Developer CLI** (azd)
   ```powershell
   winget install Microsoft.Azd
   # Ou
   # https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd
   ```

3. **PostgreSQL Client Tools** (psql)
   ```powershell
   winget install PostgreSQL.PostgreSQL
   # Ou
   # https://www.postgresql.org/download/windows/
   ```

### Verificar Instalação

```powershell
az --version
azd version
psql --version
```

## 🚀 Deployment Passo-a-Passo

### 1. Autenticar no Azure

```powershell
# Login com Azure CLI
az login

# Login com Azure Developer CLI
azd auth login
```

### 2. Inicializar Ambiente azd

```powershell
# No diretório do projeto
cd C:\CryptoDashboard

# Inicializar ambiente (primeira vez)
azd init
```

Quando solicitado:
- **Environment name**: Escolha um nome único (ex: `cryptodash-prod`)
- **Subscription**: Selecione a sua subscrição Azure
- **Location**: Escolha a região (recomendado: `westeurope` ou `northeurope`)

### 3. Preview do Deployment (Recomendado)

```powershell
# Ver o que será criado SEM fazer o deployment
azd provision --preview
```

Isto mostra:
- Recursos que serão criados
- Custos estimados
- Configurações

### 4. Deployment Completo

```powershell
# Provisionar infraestrutura + deploy da aplicação
azd up
```

Este comando irá:
1. ✅ Criar Resource Group
2. ✅ Criar Managed Identity
3. ✅ Criar Log Analytics Workspace
4. ✅ Criar Application Insights
5. ✅ Criar Key Vault
6. ✅ Criar Azure PostgreSQL Flexible Server
7. ✅ Criar App Service Plan + Web App
8. ✅ Configurar variáveis de ambiente
9. ✅ Fazer deploy do código da aplicação

⏱️ **Tempo estimado**: 10-15 minutos

### 5. Obter Informações do Deployment

```powershell
# Ver outputs do deployment
azd env get-values

# URL da aplicação
azd env get-value WEB_APP_URL

# Nome do servidor PostgreSQL
azd env get-value POSTGRESQL_SERVER_FQDN
```

### 6. Inicializar Base de Dados

Após o deployment, é necessário aplicar o schema da base de dados:

```powershell
# Obter informações da base de dados
$dbServer = azd env get-value POSTGRESQL_SERVER_FQDN
$dbUser = "dbadmin"
$dbPassword = "<password-gerada-no-deployment>"

# Executar script de inicialização
.\scripts\init-azure-db.ps1 `
    -ServerName $dbServer `
    -AdminUser $dbUser `
    -AdminPassword $dbPassword
```

**Nota**: A password foi gerada automaticamente durante o deployment e está armazenada no Key Vault.

### 7. Aceder à Aplicação

```powershell
# Obter URL e abrir no browser
$url = azd env get-value WEB_APP_URL
Start-Process $url
```

## 🔧 Configuração Pós-Deployment

### 1. Configurar Chaves de API

Ligar à base de dados e configurar as chaves de API:

```sql
-- CoinGecko API
UPDATE t_api_coingecko 
SET api_key = 'sua-chave-coingecko'
WHERE api_id = 1;

-- CardanoScan API
UPDATE t_api_cardano 
SET api_key = 'sua-chave-cardanoscan'
WHERE api_id = 1;
```

### 2. Criar Utilizador Administrador

1. Aceder à aplicação
2. Clicar em "Criar Conta"
3. Registar primeiro utilizador
4. Atualizar na base de dados para admin:

```sql
UPDATE t_users 
SET is_admin = true 
WHERE username = 'seu-username';
```

### 3. Adicionar Firewall Rules (Opcional)

Para aceder à base de dados do seu IP local:

```powershell
# Adicionar regra de firewall para o seu IP
az postgres flexible-server firewall-rule create `
    --resource-group rg-<environment-name> `
    --name <postgresql-server-name> `
    --rule-name AllowMyIP `
    --start-ip-address <seu-ip> `
    --end-ip-address <seu-ip>
```

## 🔄 Atualizações e Manutenção

### Fazer Deploy de Novas Alterações

```powershell
# Apenas deploy do código (sem reprovisionar infraestrutura)
azd deploy

# Deploy completo (infraestrutura + código)
azd up
```

### Ver Logs da Aplicação

```powershell
# Logs em tempo real
az webapp log tail `
    --resource-group rg-<environment-name> `
    --name <webapp-name>

# Download de logs
az webapp log download `
    --resource-group rg-<environment-name> `
    --name <webapp-name>
```

### Ligar ao PostgreSQL

```powershell
# Obter connection string do Key Vault
$connString = az keyvault secret show `
    --vault-name <keyvault-name> `
    --name postgresql-connection-string `
    --query value -o tsv

# Ou ligar diretamente
psql "host=<server-fqdn> port=5432 dbname=cryptodashboard user=dbadmin sslmode=require"
```

## 💰 Estimativa de Custos

Com a configuração padrão (SKUs básicos):

- **App Service Plan (B1)**: ~€12/mês
- **PostgreSQL Flexible Server (B1ms)**: ~€10/mês
- **Key Vault**: ~€0.50/mês
- **Application Insights**: ~€2/mês (primeiros 5GB grátis)
- **Log Analytics**: ~€2/mês (primeiros 5GB grátis)

**Total estimado**: ~€26-30/mês

### Otimização de Custos

Para desenvolvimento/teste:
```powershell
# Parar a aplicação quando não estiver em uso
az webapp stop --name <webapp-name> --resource-group rg-<environment-name>

# Parar o servidor PostgreSQL
az postgres flexible-server stop --name <server-name> --resource-group rg-<environment-name>
```

## 🛡️ Segurança

### Melhores Práticas Implementadas

✅ HTTPS obrigatório (TLS 1.2+)  
✅ Managed Identity para autenticação  
✅ Secrets no Key Vault (não em código)  
✅ SSL obrigatório para PostgreSQL  
✅ Firewall no PostgreSQL  
✅ Application Insights para monitoring  

### Melhorias Recomendadas para Produção

1. **Mudar Password da Base de Dados**
   ```powershell
   az postgres flexible-server update `
       --resource-group rg-<environment-name> `
       --name <server-name> `
       --admin-password '<nova-password-forte>'
   ```

2. **Configurar Domínio Customizado**
   ```powershell
   az webapp config hostname add `
       --webapp-name <webapp-name> `
       --resource-group rg-<environment-name> `
       --hostname www.seudominio.com
   ```

3. **Upgrade SKUs para Produção**
   - App Service: P1V2 ou superior
   - PostgreSQL: General Purpose (GP_Standard_D2s_v3)

4. **Configurar Backups Automáticos**
   ```powershell
   az postgres flexible-server backup create `
       --resource-group rg-<environment-name> `
       --name <server-name> `
       --backup-name manual-backup
   ```

## 🧹 Limpar Recursos

Para remover todos os recursos criados:

```powershell
# Remover ambiente completo
azd down

# Ou manualmente
az group delete --name rg-<environment-name> --yes
```

## 📚 Recursos Adicionais

- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Azure App Service Documentation](https://learn.microsoft.com/azure/app-service/)
- [Azure Database for PostgreSQL Documentation](https://learn.microsoft.com/azure/postgresql/)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)

## 🆘 Troubleshooting

### Aplicação não inicia

```powershell
# Verificar logs
az webapp log tail --resource-group rg-<env> --name <webapp-name>

# Verificar variáveis de ambiente
az webapp config appsettings list --resource-group rg-<env> --name <webapp-name>
```

### Erro de conexão à base de dados

```powershell
# Verificar se o servidor está a correr
az postgres flexible-server show --resource-group rg-<env> --name <server-name>

# Testar conexão
psql "host=<server-fqdn> port=5432 dbname=postgres user=dbadmin sslmode=require"
```

### Key Vault access denied

```powershell
# Verificar access policies
az keyvault show --name <keyvault-name> --resource-group rg-<env>

# Adicionar permissões manualmente se necessário
az keyvault set-policy `
    --name <keyvault-name> `
    --object-id <managed-identity-principal-id> `
    --secret-permissions get list
```

---

**Última atualização**: Novembro 2025  
**Versão**: 1.0
