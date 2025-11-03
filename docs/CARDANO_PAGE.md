# 🔷 Página Cardano - Documentação

## Visão Geral

A página **Cardano** foi criada para fornecer uma interface completa de consulta à blockchain Cardano usando a API CardanoScan. Permite aos utilizadores visualizar saldos, tokens nativos e histórico de transações de qualquer endereço Cardano.

## Estrutura de Arquivos

### 1. `services/cardano_api.py`
**Serviço de integração com a API CardanoScan**

**Classe:** `CardanoScanAPI`

**Métodos principais:**
- `get_balance(address)` - Obtém saldo em ADA e tokens nativos
- `get_transactions(address, max_pages)` - Busca histórico de transações
- `format_timestamp(timestamp_str)` - Formata datas para formato legível
- `format_ada_amount(lovelace)` - Converte lovelace para ADA
- `get_token_name(token)` - Extrai nome amigável de tokens

**Características:**
- Tratamento robusto de erros
- Conversão automática de endereços bech32 para hexadecimal
- Suporte a paginação para transações
- Formatação de dados para leitura humana

### 2. `pages/cardano.py`
**Interface visual da página Cardano**

**Função principal:** `show()`

**Abas da interface:**

#### Tab 1: 💰 Saldo e Tokens
- Exibição do saldo em ADA, Lovelace e valor aproximado em EUR
- Listagem de todos os tokens nativos
- Tabela formatada com Policy ID e Fingerprint
- Botão de exportação para CSV

#### Tab 2: 📜 Transações
- Histórico completo de transações
- Estatísticas (total, taxas, confirmadas, última transação)
- Visualização detalhada de cada transação:
  - Hash, data, taxa, bloco, status
  - Inputs e outputs
  - Metadata (quando disponível)
- Link direto para CardanoScan Explorer
- Exportação para CSV

#### Tab 3: ℹ️ Informações
- Informações sobre o endereço consultado
- Documentação da API
- Links úteis
- Informações técnicas

## Funcionalidades

### ✅ Implementadas
1. **Consulta de Saldo**
   - Saldo em ADA e Lovelace
   - Conversão para moeda FIAT (exemplo)
   - Validação de endereço

2. **Tokens Nativos**
   - Listagem completa
   - Decodificação de nomes hexadecimais
   - Exibição de Policy ID e Fingerprint
   - Exportação CSV

3. **Transações**
   - Histórico paginado (configurável)
   - Detalhes completos de cada transação
   - Visualização de inputs/outputs
   - Metadata quando disponível
   - Links para explorador externo
   - Exportação CSV

4. **Interface**
   - Design responsivo com tabs
   - Métricas visuais (st.metric)
   - Expandables para transações
   - Botões de atualização
   - Sistema de cache de endereço

## Configuração

### Variáveis de Configuração
```python
# Em pages/cardano.py
API_KEY = "771d0a8a-9978-40b4-b60b-3fa873e5209d"
DEFAULT_ADDRESS = "addr1q86l9qs02uhmh95yj8vgmecky4yfkxlctaae8axx0xut63p42ytjhzpls30rpmffa6y335yrxcuzh0q55d30ramjyefqvyf4rw"
```

**⚠️ Recomendação:** Em produção, mover API_KEY para variáveis de ambiente (.env)

### Dependências
```
pycardano==0.17.0
requests==2.32.5
streamlit==1.39.0
pandas==2.2.3
```

## Uso

### Acesso
1. Fazer login no dashboard
2. Selecionar "🔷 Cardano" no menu lateral
3. Inserir endereço Cardano (formato addr1...)
4. Clicar em "🔄 Atualizar"

### Consultar Saldo
1. Aba "💰 Saldo e Tokens"
2. Visualizar métricas de saldo
3. Verificar tokens nativos na tabela
4. Exportar dados (opcional)

### Ver Transações
1. Aba "📜 Transações"
2. Ajustar número de páginas (1-20)
3. Clicar em "📥 Carregar Transações"
4. Expandir transações para ver detalhes
5. Exportar histórico (opcional)

## Limitações Conhecidas

1. **API Rate Limits**: CardanoScan pode ter limites de taxa
2. **Paginação**: Transações limitadas a 20 por página
3. **Formato de Endereço**: Apenas bech32 (addr1...) suportado
4. **Cotações**: Valor em EUR é exemplo fixo (implementar integração real)
5. **Histórico**: Máximo de 50 transações exibidas na interface (todas disponíveis no CSV)

## Melhorias Futuras

### Prioritárias
- [ ] Integração com API de cotações para valor real em FIAT
- [ ] Geração de QR Code do endereço
- [ ] Suporte a múltiplos endereços (watchlist)
- [ ] Gráficos de evolução de saldo
- [ ] Filtros avançados de transações

### Adicionais
- [ ] Suporte a stake addresses (stake1...)
- [ ] Visualização de NFTs com imagens
- [ ] Análise de pools de staking
- [ ] Alertas de transações
- [ ] Comparação entre endereços
- [ ] Exportação em JSON e Excel

## Tratamento de Erros

### Erros Comuns
1. **Endereço inválido**: Validação na interface
2. **404 Not Found**: Endereço sem transações ou não indexado
3. **Timeout**: Retry automático não implementado
4. **Rate Limit**: Mensagem de erro exibida ao utilizador

### Logs
Erros são exibidos na interface usando:
- `st.error()` para erros críticos
- `st.warning()` para avisos
- `st.info()` para informações

## Integração com Dashboard

### Menu Principal
Adicionado em `app.py`:
```python
from pages.cardano import show as show_cardano_page

menu_options = [
    "📊 Análise de Portfólio",
    "💰 Cotações",
    "🔷 Cardano",  # <-- Nova opção
    "📄 Documentos",
]

elif menu == "🔷 Cardano":
    show_cardano_page()
```

### Session State
- `cardano_address`: Endereço consultado (persistente)
- `cardano_transactions`: Cache de transações
- `cardano_transactions_error`: Cache de erro (se houver)

## API CardanoScan

### Endpoints Utilizados

1. **Balance**
   - URL: `GET /api/v1/address/balance`
   - Params: `address` (bech32)
   - Retorna: saldo e tokens

2. **Transactions**
   - URL: `GET /api/v1/transaction/list`
   - Params: `address` (hex), `pageNo`
   - Retorna: lista de transações e total de páginas

### Autenticação
Header: `apiKey: <API_KEY>`

### Documentação Oficial
https://docs.cardanoscan.io

## Exemplos de Uso

### Código - Consultar Saldo
```python
from services.cardano_api import CardanoScanAPI

api = CardanoScanAPI("YOUR_API_KEY")
balance_data, error = api.get_balance("addr1q86l9qs...")

if error:
    print(f"Erro: {error}")
else:
    print(f"Saldo: {balance_data['ada']} ADA")
    print(f"Tokens: {len(balance_data['tokens'])}")
```

### Código - Consultar Transações
```python
transactions, error = api.get_transactions("addr1q86l9qs...", max_pages=5)

if not error:
    print(f"Total de transações: {len(transactions)}")
    for tx in transactions[:5]:
        print(f"{tx['hash'][:16]}... | {tx['timestamp']} | {tx['fees']} ADA")
```

## Manutenção

### Atualização de API Key
Editar `pages/cardano.py`:
```python
API_KEY = "nova_chave_aqui"
```

### Adicionar Novos Endpoints
1. Implementar método em `services/cardano_api.py`
2. Adicionar visualização em `pages/cardano.py`
3. Criar nova aba se necessário

### Debug
Ativar logs detalhados:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Suporte

Para problemas ou sugestões:
1. Verificar logs no terminal
2. Consultar documentação da API CardanoScan
3. Verificar conectividade e rate limits
4. Reportar issues no repositório

---

**Última Atualização:** Novembro 2025
**Versão:** 1.0.0
**Status:** ✅ Produção
