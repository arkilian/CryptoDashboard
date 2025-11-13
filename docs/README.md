# 📚 Documentação Técnica - Índice

## 🎯 Guias Principais

### Para Utilizadores

- **[CoinGecko CSV Import](COINGECKO_CSV_IMPORT.md)** ⭐ **ESSENCIAL**
  - Como importar dados históricos de preços
  - Workflow manual (recomendado)
  - Troubleshooting e FAQ
  - **Status:** ✅ Workflow funcional, 2941 registos testados

- **[Guia Rápido de Análise](GUIA_RAPIDO_ANALISE.md)**
  - Quick start para análise do projeto
  - Estrutura e componentes principais

### Para Developers

- **[Web Scraping Anti-Bot](WEB_SCRAPING_ANTIBOT.md)** ⚠️ **IMPORTANTE**
  - Por que scraping automático NÃO funciona
  - Estratégias testadas e resultados
  - Alternativas e recomendações
  - **Conclusão:** Download manual é a única solução viável

- **[Performance Optimizations](PERFORMANCE_OPTIMIZATIONS.md)**
  - Otimizações implementadas no sistema
  - Rate limiting e caching
  - Métricas de performance

- **[Optimization Summary](OPTIMIZATION_SUMMARY.md)**
  - Resumo das otimizações gerais
  - Impacto e resultados

---

## 🔷 Cardano Integration

### Documentação Específica

- **[Cardano Page](CARDANO_PAGE.md)**
  - Página Portfolio v3 com integração Cardano
  - Funcionalidades e UI

- **[Cardano Performance](CARDANO_PERFORMANCE.md)**
  - Otimizações específicas para Cardano
  - Performance de queries e API calls

- **[Cardano Staking](CARDANO_STAKING.md)**
  - Sistema de staking
  - Rewards e delegação

- **[Cardano Transactions Summary](CARDANO_TRANSACTIONS_SUMMARY.md)**
  - Sumário de transações Cardano
  - Estrutura e dados

### Status Atual

- ✅ Integração completa com CardanoScan API
- ✅ Sync de transações e balance
- ✅ Portfolio v3 funcional
- ✅ Baseline reconciliation (fix valores negativos)
- ✅ Filtro de tokens efêmeros (fix picos 43k)

---

## 📊 Análise e Performance

### Documentação de Análise

- **[Análise Completa do Projeto](ANALISE_COMPLETA_PROJETO.md)**
  - Análise técnica detalhada
  - Arquitetura e componentes
  - Recomendações de melhoria

- **[Análise Visual](ANALISE_VISUAL.md)**
  - Análise da interface e UX
  - Screenshots e feedback

- **[README Análise](README_ANALISE.md)**
  - Overview da análise realizada
  - Sumário de descobertas

### Melhorias Implementadas

- **[Performance Improvements](PERFORMANCE_IMPROVEMENTS.md)**
  - Lista detalhada de melhorias
  - Before/After comparisons
  - Impact assessment

---

## 🚀 Portfolio v3

- **[Portfolio V3](PORTFOLIO_V3.md)**
  - Nova versão do portfolio
  - Integração DB-first
  - Cardano wallet transactions

### Features Principais

- ✅ DB-first approach (sem API calls desnecessárias)
- ✅ Cardano wallet integration
- ✅ CoinGecko price snapshots
- ✅ Baseline reconciliation
- ✅ Ephemeral token filtering
- ✅ Historical chart com preços reais

---

## 🔧 Manutenção e Updates

### Scripts de Debug

Localização: `debug_scripts/`

- `check_csv_import.py` - Verificar dados importados
- `inspect_coingecko_html.py` - Analisar HTML do CoinGecko
- Outros 12 scripts de debug e manutenção

Ver: `debug_scripts/README.md`

### Frequência de Atualização

| Documento | Frequência | Última Atualização |
|-----------|------------|-------------------|
| COINGECKO_CSV_IMPORT.md | Mensal | 2025-11-05 |
| WEB_SCRAPING_ANTIBOT.md | Trimestral | 2025-11-05 |
| Portfolio v3 docs | Contínua | 2025-11-05 |
| Cardano docs | Contínua | 2025-11-03 |
| Análise docs | Estático | 2025-11-02 |

---

## 📋 Quick Reference

### Comandos Essenciais

```bash
# 1. Importar preços históricos (recomendado)
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all

# 2. Verificar import
python debug_scripts/check_csv_import.py

# 3. Executar app
streamlit run app.py
```

### Links Úteis

- **CoinGecko:** https://www.coingecko.com/en/coins/cardano/historical_data
- **CardanoScan:** https://cardanoscan.io
- **Wiki Principal:** `../wiki/README.md`
- **README Root:** `../README.md`

---

## 🎯 Roadmap de Documentação

- [x] Guia de import de CSV do CoinGecko
- [x] Documentação de web scraping e limitações
- [x] Análise de performance Cardano
- [x] Índice de documentação
- [ ] Tutorial em vídeo de setup inicial
- [ ] API reference completa
- [ ] Guia de contribuição (CONTRIBUTING.md)
- [ ] Changelog automático

---

## 📝 Como Contribuir com Documentação

1. **Novos documentos:** Criar em `docs/` com naming claro
2. **Updates:** Manter data de última modificação
3. **Índice:** Atualizar este README.md quando adicionar docs
4. **Formato:** Markdown com emojis para navegação visual
5. **Links:** Sempre usar caminhos relativos

---

**Última atualização:** 2025-11-05  
**Maintainer:** @arkilian  
**Status:** ✅ Documentação ativa e mantida
