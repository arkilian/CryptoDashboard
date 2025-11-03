# 📊 Crypto Dashboard

Uma plataforma completa para gestão de um fundo comunitário de criptomoedas, com sistema de ownership baseado em shares/NAV, tracking histórico de preços, e análise de performance em tempo real.

## 🎯 Visão Geral

O Crypto Dashboard é uma solução profissional para gestão transparente de fundos comunitários de criptoativos. Combina:
- **Sistema de Ownership Justo**: Baseado em NAV/share (Net Asset Value), garantindo que cada participante tem uma fatia proporcional do fundo
- **Histórico Completo**: Todos os movimentos, transações e variações de preço são rastreados e auditáveis
- **Análise Avançada**: Gráficos de evolução, composição de portfólio, e métricas de performance
- **Integração de Mercado**: Preços em tempo real e históricos via CoinGecko API
- **Transparência Total**: Cada utilizador vê sua propriedade exata do fundo e evolução patrimonial

## 🚀 Funcionalidades Principais

### 🔐 Autenticação e Perfis
- Registo seguro com username, email e password (hash bcrypt)
- Perfis completos com dados pessoais (nome, data de nascimento, género, morada)
- Dois níveis de acesso: **Administrador** e **Utilizador**
- Sessão persistente e gerida via Streamlit

### 👥 Gestão de Utilizadores (Admin)
- Dashboard completo de utilizadores com filtros e pesquisa
- Adicionar/editar utilizadores e definir passwords
- **Movimentos de Capital por Utilizador**:
  - Depósitos: registam crédito e **alocam shares automaticamente** com base no NAV/share do momento
  - Levantamentos: registam débito e **queimam shares proporcionalmente**
  - Histórico completo auditável com datas e valores

### 💎 Sistema de Shares & NAV (Ownership)
**O coração do sistema** - garante propriedade justa e proporcional:

- **NAV (Net Asset Value)**: Valor total do fundo = Caixa + Holdings em Cripto a preços atuais
- **NAV por Share**: Preço de cada share = NAV Total ÷ Total de Shares em circulação
- **Alocação em Depósitos**: Shares atribuídas = Valor depositado ÷ NAV/share no momento
- **Queima em Levantamentos**: Shares removidas = Valor levantado ÷ NAV/share no momento
- **Ownership %**: Percentagem do utilizador = (Suas shares ÷ Total shares) × 100

**Exemplo prático:**
```
Fundo tem NAV de €1000 e 1000 shares → NAV/share = €1.00
Utilizador A deposita €500 → recebe 500 shares (50% do fundo)
Mercado sobe 20% → NAV = €1200, NAV/share = €1.20
Utilizador B deposita €600 → recebe 500 shares (€600 ÷ €1.20)
Agora: Total 1500 shares, A tem 33.3%, B tem 33.3%, resto do fundo 33.3%
```

### 💰 Transações de Cripto
- **Compra e Venda** de criptoativos com tracking completo:
  - Quantidade, preço unitário, total em EUR, fees
  - Botão "Usar preço de mercado" para preencher automaticamente preço atual
  - **Preços históricos**: Para transações antigas, o sistema busca e armazena o preço da data selecionada
  - Validação de saldo de caixa disponível antes de compras
  - Atualização automática de holdings do fundo

### 🧩 Modelo de Transações V2 (multi-asset/multi-conta)
- Suporte a todos os tipos de operações: `buy`, `sell`, `deposit`, `withdrawal`, `swap`, `transfer`, `stake`, `unstake`, `reward`, `lend`, `borrow`, `repay`, `liquidate`.
- Campos estruturados para origem/destino: `from_asset_id`, `to_asset_id`, `from_quantity`, `to_quantity`, `from_account_id`, `to_account_id`, `fee_asset_id`, `fee_quantity`.
- Compatível com o legado: colunas antigas (`asset_id`, `quantity`, `price_eur`, `total_eur`, `fee_eur`) continuam válidas (tornadas NULLABLE), e são automaticamente mapeadas.
- EUR é tratado como um asset na tabela `t_assets` e existe a exchange especial "Banco" para movimentos FIAT.
- Migração automática e idempotente no arranque: a aplicação cria colunas/índices necessários, adiciona EUR, cria a exchange "Banco" e migra `buy/sell` antigas.

Guia completo com exemplos e impactos de holdings: **[Modelo de Transações V2 →](wiki/07-transaction-model-v2.md)**

### 📊 Análise de Portfólio
Dashboard completo com três componentes principais:

#### 1️⃣ **Métricas de Topo**
- 💰 Saldo Atual (Fundo): NAV total calculado em tempo real
- 📈 Total Depositado: Soma de todos os depósitos
- 📉 Total Levantado: Soma de todos os levantamentos

#### 2️⃣ **Gráfico de Evolução do Portfólio**
- **Linha Azul**: Total depositado acumulado
- **Linha Vermelha**: Total levantado acumulado  
- **Linha Verde**: Saldo Atual evolutivo
  - Cada ponto usa **preços históricos da data** (via snapshots)
  - Marcadores em todas as datas de eventos (depósitos, levantamentos, transações)
  - Marcadores no **dia 1 de cada mês** para referência temporal
  - Prefetch inteligente de preços com cache para evitar rate limits

#### 3️⃣ **Composição do Portfólio**
- 💶 Caixa (EUR): Saldo disponível para compras
- 🪙 Valor em Cripto: Total em holdings a preços atuais
- **Tabela de Holdings**: Ativo, quantidade, preço atual, valor total, % do portfólio
- Todos os valores calculados com preços de **hoje** (métricas) vs **históricos** (gráfico)

#### 4️⃣ **Top Holders da Comunidade** (Admin)
- 📊 NAV por Share: Preço atual de cada share
- 🔢 Total Shares: Shares totais em circulação
- 💰 NAV Total Fundo: Valor total do fundo
- **Tabela de Propriedade**:
  - 🥇🥈🥉 Medalhas para top 3
  - Username, Shares, Propriedade (%), Valor (€)
  - Ordenação por % de propriedade
- **Gráfico Pizza**: Distribuição visual de ownership

### 📸 Sistema de Snapshots de Preços
**Cache inteligente** para otimizar performance e reduzir chamadas à API:

- **Tabela `t_price_snapshots`**: Armazena preços históricos (asset, data, preço, moeda)
- **Lógica DB-First**: 
  1. Tenta buscar preço na base de dados local
  2. Se não existir, consulta CoinGecko API
  3. Armazena resultado para uso futuro
  4. Delay de 2 segundos entre chamadas API para respeitar rate limits
- **Session Cache**: Evita buscas duplicadas na mesma sessão
- **Bulk Fetching**: Busca preços de múltiplos ativos de uma vez
- **Endpoints CoinGecko**:
  - Preços atuais: `/simple/price` (EUR)
  - Preços históricos: `/coins/{id}/history?date=DD-MM-YYYY` (EUR)

### 📈 Cotações em Tempo Real
- Consulta de preços via CoinGecko API
- Lista completa de ativos disponíveis para trading
- Integração com sistema de transações

### 🔷 Blockchain Cardano Explorer
**Nova funcionalidade**: Explorador completo da blockchain Cardano integrado ao dashboard.

- **💰 Saldo e Tokens**:
  - Consulta de saldo ADA em qualquer endereço Cardano
  - Lista completa de tokens nativos com metadados automáticos
  - Nomes e decimais resolvidos automaticamente via CardanoScan API
  - Cache inteligente de metadados para performance
  
- **🎯 Staking**:
  - Status de delegação (pool delegado ou não)
  - Informações completas do pool (nome, ticker, fees)
  - Recompensas totais, disponíveis e já levantadas
  - Stake controlado pela conta
  
- **📜 Transações**:
  - Histórico completo de transações (paginação inteligente)
  - Análise automática: enviado, recebido ou contrato
  - Detalhes de tokens movimentados em cada transação
  - Ordenação cronológica (mais recentes primeiro)
  - Links para CardanoScan explorer
  - Carregamento por páginas (últimas páginas = mais recentes)
  
- **Configuração via Base de Dados**:
  - APIs configuradas em `t_api_cardano` (sem hardcode)
  - Múltiplas wallets geridas em `t_wallet`
  - Suporte a stake addresses
  - Filtro por utilizador (admin vê todas)

### 🏦 Gestão de Bancos e Wallets
**Nova funcionalidade**: Gestão centralizada de contas bancárias e wallets de criptomoedas.

- **🏦 Contas Bancárias** (`t_banco`):
  - Cadastro completo: banco, titular, IBAN, SWIFT/BIC
  - Validação de IBAN
  - Tipos de conta: corrente, poupança, empresarial, investimento
  - Definir conta principal por utilizador
  - Filtro por moeda e país
  
- **👛 Wallets** (`t_wallet`):
  - Suporte multi-blockchain: Cardano, Ethereum, Bitcoin, Solana
  - Tipos: hot, cold, hardware, exchange, DeFi
  - Endereço principal + stake address (para Cardano)
  - Definir wallet principal por utilizador
  - Sincronização de saldo (preparado para automação)
  
- **🔌 APIs Cardano** (`t_api_cardano`):
  - Gestão centralizada de chaves de API
  - Múltiplas APIs configuráveis
  - Rate limit e timeout por API
  - Endereço padrão por API
  - Ativar/desativar APIs sem remover

**Página de Configurações**: Interface completa para admins gerirem bancos, wallets e APIs sem editar código.

### 📄 Gestão de Documentos (Admin)
- Upload e visualização de PDFs
- Documentos típicos: regulamento, estratégia de investimento, roadmap
- Acesso para todos os utilizadores

### ⚙️ Configurações
- **Gestão de Snapshots** (Admin):
  - Ver total de snapshots armazenados
  - Limpar cache se necessário
  - Estatísticas de uso
- Configurações de perfil de utilizador

## 💼 Modelo de Negócio

### Como Funciona o Fundo

O Crypto Dashboard implementa um modelo de **fundo comunitário** onde:

1. **Participantes depositam capital** que entra para um pool comum
2. **Administradores gerem investimentos** em criptoativos
3. **Sistema de shares garante propriedade justa**:
   - Quem entra quando NAV está baixo recebe mais shares
   - Quem entra quando NAV está alto recebe menos shares
   - Todos beneficiam proporcionalmente dos ganhos (ou perdas)
4. **Transparência total**: Cada participante vê exatamente quanto possui do fundo

### Vantagens do Sistema de Shares/NAV

✅ **Justo**: Entrada e saída sempre pelo valor real do fundo  
✅ **Transparente**: Ownership calculado matematicamente  
✅ **Flexível**: Depósitos e levantamentos a qualquer momento  
✅ **Profissional**: Mesmo modelo usado por fundos de investimento tradicionais  
✅ **Auditável**: Todo o histórico de shares preservado

### Casos de Uso

- **Fundos Comunitários**: Grupo de amigos ou família investindo juntos
- **Clubes de Investimento**: Comunidades com interesse em cripto
- **Family Offices**: Gestão patrimonial familiar em cripto
- **Gestão de Tesouraria**: Organizações/DAOs gerindo ativos digitais

### Estrutura de Taxas (Configurável)

O sistema suporta implementação de:
- Taxa de manutenção periódica
- Taxa de performance sobre lucros (High-Water Mark)
- Configuração por administradores

> **Nota Legal**: Esta plataforma é uma ferramenta de gestão e transparência. Não constitui aconselhamento financeiro ou de investimento. A utilização, parametrização e legalidade da operação são responsabilidade dos administradores e participantes do fundo.

## 🏗️ Stack Tecnológico

- **Frontend**: Streamlit (Python)
- **Backend**: Python 3.10+
- **Base de Dados**: PostgreSQL
- **APIs Externas**: 
  - CoinGecko (preços de criptomoedas)
  - CardanoScan API v1 (blockchain Cardano)
- **Autenticação**: bcrypt para hash de passwords
- **Gráficos**: Plotly
- **Cache**: Sistema próprio de snapshots em PostgreSQL
- **Blockchain**: Integração nativa com Cardano (balance, staking, transactions)

## 📚 Documentação Completa

Para documentação técnica detalhada, arquitetura, guias de setup e modelo de negócio, consulte a **[Wiki do Projeto](wiki/)**:

- [🏗️ Arquitetura Técnica](wiki/01-arquitetura.md)
- [💎 Sistema de Shares/NAV](wiki/02-shares-nav.md)
- [📸 Snapshots e Preços](wiki/03-snapshots-precos.md)
- [💼 Modelo de Negócio](wiki/04-modelo-negocio.md)
- [👤 Guias de Utilizador](wiki/05-guias-utilizador.md)
- [🚀 Setup e Deployment](wiki/06-setup-deployment.md)
- [🧩 Modelo de Transações V2](wiki/07-transaction-model-v2.md)
- [🔷 Integração Blockchain Cardano](wiki/08-cardano-integration.md)

## 🎯 Roadmap

- [x] Sistema de Shares/NAV
- [x] Cache de preços históricos (snapshots)
- [x] Modelo de transações V2 (multi-asset/multi-conta)
- [x] Explorador Cardano (balance, staking, transactions)
- [x] Gestão de wallets e contas bancárias
- [x] Configuração de APIs via base de dados
- [ ] Sistema de notificações (email/push)
- [ ] Relatórios mensais automatizados
- [ ] Implementação completa de taxas de gestão
- [ ] API REST para integrações externas
- [ ] Mobile app (React Native)
- [ ] Suporte multi-moeda (USD, GBP, etc)
- [ ] Integração com mais exchanges (Binance, Coinbase)
- [ ] Sistema de proposta e votação (governança)

