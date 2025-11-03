# 📚 Wiki do Crypto Dashboard

Documentação completa do sistema de gestão de fundos comunitários de criptomoedas.

---

## 📖 Índice Geral

### 🏗️ Documentação Técnica

1. **[Arquitetura Técnica](01-arquitetura.md)**
   - Visão geral do sistema
   - Stack tecnológico
   - Estrutura de diretórios
   - Base de dados (schema, relacionamentos)
   - Componentes principais
   - Fluxos de dados
   - Performance e otimizações
   - Segurança

2. **[Sistema de Shares/NAV](02-shares-nav.md)**
   - Por que shares?
   - Conceitos fundamentais (NAV, NAV/share, Total Shares)
   - Operações (depósito, levantamento, transações)
   - Ownership e propriedade
   - Histórico de shares
   - Casos especiais
   - Verificação de integridade

3. **[Snapshots e Preços](03-snapshots-precos.md)**
   - Por que snapshots?
   - Arquitetura (camadas de cache)
   - Tabela t_price_snapshots
   - Integração CoinGecko
   - Serviço de snapshots
   - Uso em páginas (prefetch pattern)
   - Performance e gestão de cache

4. **[Modelo de Transações V2](07-transaction-model-v2.md)**
   - Visão geral multi-asset/multi-conta
   - 13 tipos de transação suportados (buy, sell, deposit, withdrawal, swap, transfer, stake, unstake, reward, lend, borrow, repay, liquidate)
   - Estrutura e campos (from/to, fees em qualquer asset)
   - Cálculo de holdings por conta
   - Workflows típicos e cenários reais
   - Migração automática e compatibilidade legado
   - Boas práticas e notas importantes

5. **[Integração Blockchain Cardano](08-cardano-integration.md)** 🆕
   - Explorador completo da blockchain Cardano
   - Consulta de saldo, tokens nativos e metadados
   - Informações de staking (delegação, rewards, pool)
   - Histórico de transações com análise automática
   - Gestão de wallets multi-blockchain
   - Gestão de contas bancárias (IBAN/SWIFT)
   - Configuração de APIs via base de dados
   - Performance e otimizações (cache, batch, paginação reversa)

### 💼 Negócio

6. **[Modelo de Negócio](04-modelo-negocio.md)**
   - Visão geral e proposta de valor
   - Estrutura do fundo (participantes, modelo de propriedade)
   - Casos de uso (família, clubes, gestão profissional, DAOs)
   - Fluxos operacionais
   - Modelo de taxas (gestão, performance, entrada/saída)
   - Vantagens competitivas
   - Riscos e mitigações
   - Conformidade e legal
   - Monetização

### 👤 Utilizadores

7. **[Guias de Utilizador](05-guias-utilizador.md)**
   - Para todos: primeiro acesso, dashboard, ver portfólio
   - Para utilizadores: solicitar depósitos/levantamentos, interpretar shares
   - Para admins: gestão de utilizadores, processar movimentos, transações cripto
   - FAQ prático
   - Melhores práticas

### 🚀 Deployment

8. **[Setup e Deployment](06-setup-deployment.md)**
   - Requisitos do sistema
   - Instalação local (desenvolvimento)
   - Deployment em produção (Streamlit Cloud, Heroku, VPS)
   - Backup e recuperação
   - Monitorização e logs
   - Segurança
   - Troubleshooting
   - Performance tuning
   - Atualizações

---

## 🎯 Quick Start

**Novo Desenvolvedor?** Comece aqui:
1. [Setup Local](06-setup-deployment.md#instalação-local-desenvolvimento)
2. [Arquitetura](01-arquitetura.md#visão-geral)
3. [Sistema de Shares](02-shares-nav.md#visão-geral)
4. [Integração Cardano](08-cardano-integration.md#visão-geral) 🆕

**Novo Administrador?** Comece aqui:
1. [Primeiro Acesso](05-guias-utilizador.md#primeiro-acesso)
2. [Gestão de Utilizadores](05-guias-utilizador.md#gestão-de-utilizadores)
3. [Processar Depósitos](05-guias-utilizador.md#processar-depósitos)

**Novo Utilizador?** Comece aqui:
1. [Login Inicial](05-guias-utilizador.md#primeiro-acesso)
2. [Ver Seu Portfólio](05-guias-utilizador.md#ver-seu-portfólio)
3. [Interpretar Shares](05-guias-utilizador.md#interpretar-ownership-e-shares)

**Quer Entender o Negócio?** Comece aqui:
1. [Visão Geral](04-modelo-negocio.md#visão-geral)
2. [Casos de Uso](04-modelo-negocio.md#casos-de-uso)
3. [Fluxos Operacionais](04-modelo-negocio.md#fluxos-operacionais)

---

## 🔍 Pesquisa Rápida

### Por Conceito

- **NAV (Net Asset Value)**: [Sistema de Shares → NAV](02-shares-nav.md#nav-net-asset-value)
- **Ownership**: [Sistema de Shares → Ownership](02-shares-nav.md#ownership-propriedade)
- **Cache de Preços**: [Snapshots → Arquitetura](03-snapshots-precos.md#arquitetura)
- **Cardano Explorer**: [Integração Cardano → Funcionalidades](08-cardano-integration.md#funcionalidades) 🆕
- **Wallets Multi-Blockchain**: [Integração Cardano → Gestão de Wallets](08-cardano-integration.md#gestão-de-wallets) 🆕
- **Segurança**: [Deployment → Segurança](06-setup-deployment.md#segurança)
- **Backup**: [Deployment → Backup](06-setup-deployment.md#backup-e-recuperação)

### Por Tarefa

- **Como criar utilizador**: [Guias → Gestão de Utilizadores](05-guias-utilizador.md#criar-novo-utilizador)
- **Como processar depósito**: [Guias → Processar Depósitos](05-guias-utilizador.md#processar-depósitos)
- **Como configurar API Cardano**: [Integração Cardano → Configuração](08-cardano-integration.md#configuração) 🆕
- **Como adicionar wallet**: [Integração Cardano → Gestão de Wallets](08-cardano-integration.md#crud-operations) 🆕
- **Como fazer backup**: [Deployment → Backup](06-setup-deployment.md#backup-automatizado)
- **Como otimizar performance**: [Deployment → Performance Tuning](06-setup-deployment.md#performance-tuning)
- **Como resolver erro 429**: [Troubleshooting](06-setup-deployment.md#problema-erro-429-too-many-requests)

### Por Tecnologia

- **PostgreSQL**: [Arquitetura → Base de Dados](01-arquitetura.md#base-de-dados)
- **Streamlit**: [Arquitetura → Interface](01-arquitetura.md#6-interface-streamlit)
- **CoinGecko API**: [Snapshots → Integração](03-snapshots-precos.md#integração-coingecko)
- **CardanoScan API**: [Integração Cardano → API CardanoScan](08-cardano-integration.md#api-cardanoscan) 🆕
- **Python Services**: [Arquitetura → Componentes](01-arquitetura.md#componentes-principais)

---

## 📊 Diagramas Principais

### Fluxo de Depósito
```
Utilizador → Transfere Fundos → Admin Confirma → Regista no Sistema
→ Sistema Calcula NAV/share → Aloca Shares → Utilizador Vê Ownership
```
[Detalhes](05-guias-utilizador.md#processar-depósitos)

### Arquitetura do Sistema
```
Frontend (Streamlit) → Services (Business Logic) → Database Layer → PostgreSQL
                    ↓
              External APIs (CoinGecko)
```
[Detalhes](01-arquitetura.md#visão-geral)

### Cache de Preços (3 Camadas)
```
Session Cache (Memória) → Database Cache (PostgreSQL) → CoinGecko API
```
[Detalhes](03-snapshots-precos.md#camadas-de-cache)

---

## 🛠️ Recursos Adicionais

### Ficheiros de Referência no Projeto

- `database/tablesv2.sql` - Schema completo da BD (V2)
- `services/shares.py` - Lógica core de shares/NAV
- `services/snapshots.py` - Sistema de cache de preços
- `services/coingecko.py` - Cliente API
- `services/cardano_api.py` - Cliente CardanoScan API 🆕
- `pages/portfolio_analysis.py` - Dashboard principal
- `pages/cardano.py` - Explorador Cardano 🆕
- `database/wallets.py` - CRUD wallets 🆕
- `database/banks.py` - CRUD bancos 🆕
- `database/api_config.py` - CRUD APIs Cardano 🆕

### Links Externos

- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
- [CardanoScan API Docs](https://docs.cardanoscan.io/) 🆕
- [Streamlit Documentation](https://docs.streamlit.io)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python bcrypt](https://github.com/pyca/bcrypt/)

---

## 🤝 Contribuir

Para melhorar esta documentação:

1. Identificar secção a melhorar
2. Editar ficheiro markdown relevante em `wiki/`
3. Seguir estrutura existente
4. Incluir exemplos práticos
5. Testar comandos/código antes de documentar

**Estilo**:
- ✅ Exemplos práticos e reais
- ✅ Comandos copyable (code blocks)
- ✅ Explicação do "porquê", não só "como"
- ✅ Screenshots/diagramas quando útil
- ❌ Evitar jargão sem explicação
- ❌ Não assumir conhecimento prévio

---

## 📝 Changelog da Wiki

**Versão 1.1 (Novembro 2025)**: 🆕
- ✅ Nova secção: Integração Blockchain Cardano (08)
- ✅ Documentação completa de explorador Cardano
- ✅ Gestão de wallets multi-blockchain
- ✅ Gestão de contas bancárias
- ✅ Configuração de APIs via base de dados
- ✅ 80+ páginas de conteúdo adicional
- ✅ Casos de uso práticos e troubleshooting

**Versão 1.0 (Outubro 2025)**:
- ✅ Documentação completa de 6 secções
- ✅ 200+ páginas de conteúdo
- ✅ Cobertura: técnico, negócio, utilizadores, deployment
- ✅ Exemplos práticos em todos os guias
- ✅ Troubleshooting e FAQ

**Próximas Adições Planeadas**:
- [ ] Vídeos tutoriais (screencast)
- [ ] Diagramas interativos
- [ ] API documentation (se implementar REST API)
- [ ] Guia de contribuição detalhado
- [ ] Glossário de termos

---

## ❓ Precisa de Ajuda?

**Não encontrou o que procurava?**

1. Use Ctrl+F para pesquisar nesta página
2. Verifique [Troubleshooting](06-setup-deployment.md#troubleshooting)
3. Consulte [FAQ em Guias](05-guias-utilizador.md#-faq-prático)
4. Abra issue no GitHub (se aplicável)

**Encontrou erro na documentação?**
- Abra issue ou PR com correção
- Inclua: página, secção, erro, correção sugerida

---

**[↑ Voltar ao README Principal](../README.md)**
