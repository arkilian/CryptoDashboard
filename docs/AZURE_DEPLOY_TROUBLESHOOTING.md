# Azure App Service Deploy - Troubleshooting

## Problema: Ficheiros não aparecem em /home/site/wwwroot após deploy

### Sintomas
- GitHub Actions mostra "Success"
- Portal Azure > Files mostra apenas ficheiros básicos (hostingstart.html, oryx-manifest.toml)
- Aplicação retorna 503 Service Unavailable
- Gunicorn tenta arrancar mas falha com "Failed to find attribute 'app' in 'app'"

### Causas Identificadas
1. **GitHub Actions deploy não copia ficheiros** - artifact upload/download pode estar incompleto
2. **Oryx build falha** silenciosamente
3. **Startup command ignorado** - Azure usa Gunicorn padrão em vez de `startup.sh`
4. **Python 3.13** ainda não tem suporte completo

---

## Soluções Tentadas

### ✅ 1. Configurações Aplicadas
- [x] Startup Command: `sh startup.sh` (via CLI)
- [x] `startup.sh` marcado como executável (git mode 755)
- [x] `.deployment` criado para forçar comando
- [x] App Settings DB_* configurados
- [x] SCM_DO_BUILD_DURING_DEPLOYMENT = true

### ❌ 2. Deploys que Falharam
- ZIP deploy via `az webapp deployment source config-zip` → Build failed
- Deploy manual via `az webapp deploy` (não testado completamente)

---

## Solução Recomendada: Deploy Manual via Kudu

### Opção A: Deploy via FTP (mais simples)

1. **Obter credenciais FTP:**
```powershell
az webapp deployment list-publishing-profiles --name arkilian-webapp --resource-group arkilian-group --xml
```

2. **Extrair:**
   - FTP Host: `ftps://waws-prod-xxxxx.ftp.azurewebsites.windows.net`
   - Username: `arkilian-webapp\$arkilian-webapp`
   - Password: (do XML)

3. **Cliente FTP (FileZilla/WinSCP):**
   - Conectar via FTPS (porta 990)
   - Navegar para `/site/wwwroot/`
   - Upload de **todos** os ficheiros do projeto (exceto `.git`, `.venv`, `__pycache__`)

### Opção B: Deploy via Azure CLI com --local-git

1. **Configurar local git:**
```powershell
az webapp deployment source config-local-git --name arkilian-webapp --resource-group arkilian-group
```

2. **Adicionar remote:**
```powershell
$url = az webapp deployment list-publishing-credentials --name arkilian-webapp --resource-group arkilian-group --query scmUri -o tsv
git remote add azure $url
git push azure main
```

### Opção C: Kudu Deploy Engine (API)

1. **Obter token:**
```powershell
$token = az account get-access-token --resource https://management.azure.com/ --query accessToken -o tsv
```

2. **POST ZIP:**
```powershell
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "https://arkilian-webapp-def7evcab7gghrfn.scm.francecentral-01.azurewebsites.net/api/zipdeploy" `
  -Method POST `
  -Headers $headers `
  -InFile deploy.zip
```

---

## Verificação Pós-Deploy

### 1. Listar ficheiros via Kudu Console
Abrir no browser:
```
https://arkilian-webapp-def7evcab7gghrfn.scm.francecentral-01.azurewebsites.net/DebugConsole
```

Ou via CLI:
```powershell
# Não funciona diretamente, usar browser
```

### 2. Verificar logs
```powershell
az webapp log tail --name arkilian-webapp --resource-group arkilian-group
```

Procurar por:
- `==== Startup ... ====` (confirma que startup.sh executou)
- `Python version:` (deve ser 3.12)
- `Starting Streamlit on port ...`

### 3. Testar endpoint
```powershell
curl -v https://arkilian-webapp-def7evcab7gghrfn.francecentral-01.azurewebsites.net/
```

Deve retornar HTML do Streamlit (não 503).

---

## Configuração Crítica no Portal

### Configuration > General Settings
- **Stack:** Python
- **Major version:** 3.12 (não 3.13)
- **Startup Command:** `sh startup.sh`

### Configuration > Application settings
```
DB_HOST=<servidor>.postgres.database.azure.com
DB_PORT=5432
DB_NAME=crypto_dashboard
DB_USER=<user>
DB_PASSWORD=<password>
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

---

## Rollback para Deploy Funcional

Se nada funcionar, considerar:

### Container App (alternativa)
- Usar Azure Container Apps em vez de App Service
- Build de imagem Docker localmente
- Push para Azure Container Registry
- Deploy controlado

### VM com Systemd
- Controlo total do ambiente
- Custo potencialmente menor (B1s)
- Configuração manual mas previsível

---

## Comandos Úteis de Debug

```powershell
# Ver runtime
az webapp config show -n arkilian-webapp -g arkilian-group --query linuxFxVersion

# Ver startup command
az webapp config show -n arkilian-webapp -g arkilian-group --query appCommandLine

# Ver último deployment
az webapp deployment list -n arkilian-webapp -g arkilian-group --query "[0]"

# Restart forçado
az webapp restart -n arkilian-webapp -g arkilian-group

# Stop/Start (mais agressivo que restart)
az webapp stop -n arkilian-webapp -g arkilian-group
az webapp start -n arkilian-webapp -g arkilian-group
```

---

## Próximos Passos (Prioridade)

1. ✅ **Configurar DB settings** (já feito)
2. 🔄 **Tentar FTP deploy manual** para confirmar que ficheiros chegam ao servidor
3. ⏳ **Verificar se Python 3.12** está configurado (não 3.13)
4. ⏳ **Confirmar startup.sh executa** via logs

Se FTP funcionar, problema é no GitHub Actions workflow ou Oryx build process.
