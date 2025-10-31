# 💼 Modelo de Negócio

## Visão Geral

O Crypto Dashboard é uma plataforma de gestão para **fundos comunitários de criptoativos**, onde múltiplos participantes contribuem capital para um pool comum gerido centralmente, com total transparência e ownership justo baseado em shares.

### Proposta de Valor

**Para Participantes (Investidores)**:
- 💎 Diversificação profissional sem gestão ativa individual
- 📊 Transparência total: vê exatamente quanto possui do fundo em tempo real
- 🎯 Entrada/saída justa pelo NAV (sem beneficiar late-comers ou penalizar early-birds)
- 📈 Acompanhamento visual de performance e composição
- 🔒 Auditabilidade completa de todos os movimentos

**Para Gestores (Administradores)**:
- 🎛️ Ferramenta profissional para gestão centralizada
- 👥 Onboarding e offboarding automatizado via shares
- 📋 Reporting automático e sempre atualizado
- ⚖️ Sistema justo que elimina disputas sobre ownership
- 🔐 Base de dados auditável para compliance

## Estrutura do Fundo

### Participantes

#### 1. **Administradores**
- Gerem o portfólio (compras/vendas)
- Adicionam e removem participantes
- Processam depósitos e levantamentos
- Acesso a todas as funcionalidades e dados agregados

**Permissões**:
- ✅ Gestão de utilizadores
- ✅ Registo de transações de cripto
- ✅ Processamento de movimentos de capital
- ✅ Vista de fundo completo (todos os participantes)
- ✅ Configurações de sistema

#### 2. **Utilizadores/Participantes**
- Contribuem capital para o fundo
- Recebem shares proporcionais
- Acompanham seu ownership e performance
- Podem solicitar levantamentos

**Permissões**:
- ✅ Vista do próprio portfólio
- ✅ Histórico de depósitos/levantamentos
- ✅ Composição e performance pessoal
- ❌ Não gerem transações de cripto
- ❌ Não veem dados de outros participantes

### Modelo de Propriedade

```
┌──────────────────────────────────────────────────┐
│              FUNDO COMUNITÁRIO                    │
│                                                   │
│  Caixa: €5,000                                    │
│  Holdings: 1000 ADA, 2 ETH, 0.5 BTC               │
│  NAV Total: €150,000                              │
│  Total Shares: 100,000                            │
│  NAV/Share: €1.50                                 │
└──────────────────────────────────────────────────┘
                       ↓
        ┌──────────────┼──────────────┐
        │              │               │
   ┌────────┐    ┌────────┐     ┌────────┐
   │ João   │    │ Maria  │     │ Pedro  │
   │ 40,000 │    │ 35,000 │     │ 25,000 │
   │ shares │    │ shares │     │ shares │
   │  40%   │    │  35%   │     │  25%   │
   │€60,000 │    │€52,500 │     │€37,500 │
   └────────┘    └────────┘     └────────┘
```

**Características**:
- Ownership dinâmico baseado em shares
- NAV/share reflete performance do fundo
- Depósitos novos diluem % mas mantêm valor proporcional
- Levantamentos reduzem % mas não afetam outros participantes

## Casos de Uso

### 1. Fundo Familiar

**Contexto**: Família com múltiplos membros querendo investir em conjunto

**Setup**:
- 1 membro como administrador (pai/mãe)
- 3-8 participantes (filhos, cônjuges, etc)
- Depósitos mensais ou únicos
- Estratégia conservadora (BTC, ETH, stablecoins)

**Benefícios**:
- Gestão centralizada reduz overhead
- Transparência evita conflitos familiares
- Ensino financeiro para membros mais novos
- Economias de escala (fees menores em transações grandes)

**Exemplo Real**:
```
Família Silva - 5 membros
Depósito inicial total: €10,000
Após 1 ano: €15,000 (+50%)

Pai (admin): €3,000 → €4,500 (30%)
Mãe: €3,000 → €4,500 (30%)
Filho 1: €2,000 → €3,000 (20%)
Filho 2: €1,000 → €1,500 (10%)
Filha: €1,000 → €1,500 (10%)

Todos viram crescimento proporcional. ✅
```

### 2. Clube de Investimento

**Contexto**: Grupo de amigos/colegas com interesse em cripto

**Setup**:
- 1-2 administradores (mais experientes)
- 10-30 participantes
- Depósitos variáveis (€100-€10,000 cada)
- Estratégia mais agressiva (altcoins, DeFi)
- Reuniões mensais para decisões de investimento

**Benefícios**:
- Partilha de conhecimento e due diligence
- Poder de compra agregado
- Diversificação que indivíduos não conseguiriam
- Social + financeiro

**Regras Típicas**:
- Depósito mínimo: €100
- Taxa de entrada: 0% (mas pode haver)
- Taxa de gestão: 1-2% anual
- Lock-up: 3-6 meses (opcional)

### 3. Gestão Profissional (Small Fund)

**Contexto**: Gestor profissional com clientes pequenos

**Setup**:
- 1 gestor (admin)
- 20-100 clientes (utilizadores)
- Depósitos via transferência bancária
- Estratégia definida (whitepaper/prospecto)
- Reporting mensal automatizado

**Modelo de Receita**:
- Taxa de gestão: 2% anual sobre NAV
- Taxa de performance: 20% acima de 8% anual (High-Water Mark)

**Exemplo**:
```
Fundo início do ano: €100,000
Fim do ano: €120,000 (+20%)

Taxa de gestão: 2% × €100,000 = €2,000
Performance: 20% × (€20,000 - €8,000) = €2,400
Total fees: €4,400

NAV líquido: €115,600
Return líquido para investidores: +15.6% 🎯
```

### 4. DAO Treasury Management

**Contexto**: Organização descentralizada (DAO) gerindo tesouraria

**Setup**:
- Multisig wallet como "admin"
- Membros da DAO como participantes
- Contribuições via governance tokens
- Votações on-chain para transações grandes

**Características Únicas**:
- Integração com smart contracts (futuro)
- Votação para estratégia de investimento
- Transparência on-chain + off-chain
- Múltiplas carteiras (hot/cold)

## Fluxos Operacionais

### Onboarding de Novo Participante

```
1. Admin cria conta de utilizador
   └─> Username, email, password

2. Admin regista perfil completo (opcional)
   └─> Nome, data nascimento, morada, etc

3. Participante transfere capital (off-platform)
   └─> Transferência bancária, Crypto, etc

4. Admin confirma recebimento
   └─> Regista depósito no sistema
   └─> Sistema calcula NAV/share atual
   └─> Aloca shares automaticamente

5. Participante vê ownership imediatamente
   └─> Dashboard mostra shares, %, valor EUR
```

**Timeline**: ~5-10 minutos

### Processamento de Depósito

```
Participante: "Quero depositar €1,000"

1. Transfere fundos (externo)
2. Admin recebe confirmação
3. Admin acede a "Utilizadores" → Movimentos
4. Seleciona utilizador
5. Insere depósito: €1,000, data, notas
6. Sistema:
   a. NAV antes = €50,000, Shares = 25,000 → NAV/share = €2.00
   b. Novo depósito já está no NAV → NAV atual = €51,000
   c. NAV/share do momento = (€51,000 - €1,000) / 25,000 = €2.00
   d. Shares alocadas = €1,000 / €2.00 = 500 shares
   e. Insere registo em t_user_shares
7. Participante vê atualização: +500 shares, novo ownership %
```

**Fairness**: Participante paga preço real do momento (NAV/share).

### Processamento de Levantamento

```
Participante: "Quero levantar €2,000"

1. Participante solicita (email/verbal)
2. Admin valida ownership: 
   └─> User tem 1,000 shares, NAV/share = €2.50 → pode levantar até €2,500 ✅
3. Admin transfere fundos (externo)
4. Admin regista levantamento no sistema
5. Sistema:
   a. NAV/share no momento = €2.50
   b. Shares a queimar = €2,000 / €2.50 = 800 shares
   c. Valida: 1,000 - 800 = 200 shares restantes ✅
   d. Insere registo negativo em t_user_shares
6. Participante vê redução: -800 shares, novo ownership %
```

**Proteção**: Sistema nunca permite levantamento maior que ownership.

### Execução de Transação de Cripto

```
Admin decide: "Comprar 100 ADA"

1. Admin acede a "Portfólio" → "Comprar"
2. Seleciona ativo: ADA
3. Insere quantidade: 100
4. Clica "Usar preço de mercado" (ou insere manual)
   └─> Sistema busca preço atual: €0.52
5. Sistema valida caixa disponível:
   └─> Caixa = €5,000
   └─> Custo = 100 × €0.52 + fee €0.10 = €52.10 ✅
6. Confirma transação
7. Sistema:
   a. Insere em t_transactions (buy)
   b. Caixa reduz: €5,000 → €4,947.90
   c. Holdings aumentam: 0 ADA → 100 ADA
   d. NAV mantém-se (trocou caixa por cripto)
   e. Shares NÃO mudam
   f. NAV/share mantém-se
```

**Importante**: Transações são neutras para ownership.

### Análise de Performance

```
Participante acede a "Análise de Portfólio"

Sistema mostra:
1. Métricas principais:
   - 💰 Saldo Atual: €5,234.50
   - 📈 Total Depositado: €4,000
   - 📉 Total Levantado: €0
   - 🎯 Ganho/Perda: +€1,234.50 (+30.86%)

2. Gráfico de evolução:
   - Linha azul: Depósitos acumulados
   - Linha vermelha: Levantamentos acumulados
   - Linha verde: Valor atual evolutivo

3. Composição:
   - 💶 Caixa: €1,500 (28.7%)
   - 🪙 BTC: €2,500 (47.8%)
   - 🪙 ADA: €1,234.50 (23.6%)

4. Top Holders (se admin):
   - Ranking com medalhas 🥇🥈🥉
   - % de ownership de cada um
   - Gráfico pizza de distribuição
```

## Modelo de Taxas (Configurável)

### Taxa de Gestão (Management Fee)

**Definição**: Taxa periódica sobre o NAV

**Típico**: 1-2% anual

**Cobrança**:
```python
# Mensal: 2% anual = 0.1667% mensal
monthly_fee = NAV_total * 0.02 / 12

# Deduz do fundo (reduz caixa)
# → NAV diminui → NAV/share diminui → Todos pagam proporcionalmente
```

**Exemplo**:
```
Fundo NAV: €100,000
Taxa: 2% anual = €2,000/ano = €166.67/mês

Mês 1: Cobra €166.67
- Caixa reduz de €10,000 → €9,833.33
- NAV reduz de €100,000 → €99,833.33
- Shares mantêm-se (10,000)
- NAV/share: €10.00 → €9.98 (todos pagam -0.2%)
```

### Taxa de Performance (Performance Fee)

**Definição**: Percentagem sobre lucros acima de threshold

**Típico**: 20% sobre retorno acima de 8% anual (High-Water Mark)

**High-Water Mark (HWM)**:
- Máximo NAV/share histórico
- Só cobra se superar HWM anterior
- Protege investidores: sem taxa em "recovery"

**Exemplo**:
```
Ano 1:
- Início: NAV/share = €1.00 (HWM = €1.00)
- Fim: NAV/share = €1.20 (+20%)
- Threshold: €1.08 (8%)
- Lucro acima threshold: €1.20 - €1.08 = €0.12
- Fee: 20% × €0.12 = €0.024 por share
- NAV/share final: €1.176
- Novo HWM: €1.176

Ano 2 (mercado cai):
- Início: NAV/share = €1.176 (HWM = €1.176)
- Fim: NAV/share = €1.00 (-15%)
- Sem fee (abaixo HWM) ✅

Ano 3 (recuperação):
- Início: NAV/share = €1.00 (HWM = €1.176)
- Fim: NAV/share = €1.30 (+30%)
- Só cobra acima do HWM:
  └─> Fee sobre (€1.30 - €1.176) apenas
```

**Implementação** (futuro):
```python
def calculate_performance_fee(user_id: int) -> float:
    # Obter HWM do utilizador
    hwm = get_user_hwm(user_id)
    current_nav_per_share = calculate_nav_per_share()
    
    if current_nav_per_share <= hwm:
        return 0.0  # Sem fee se não superou HWM
    
    # Fee sobre a parte acima do HWM
    user_shares = get_user_total_shares(user_id)
    excess = current_nav_per_share - hwm
    fee_rate = 0.20  # 20%
    fee_amount = user_shares * excess * fee_rate
    
    # Atualizar HWM
    update_user_hwm(user_id, current_nav_per_share)
    
    return fee_amount
```

### Taxa de Entrada/Saída (Entry/Exit Fee)

**Opcional**: Cobrado em depósitos ou levantamentos

**Típico**: 0-2%

**Propósito**:
- Desincentivar trading frequente
- Cobrir custos administrativos
- Proteger investidores de longo prazo

**Exemplo**:
```
Pedro deposita €10,000, taxa entrada 1%

Opção A (taxa antes):
- Valor efetivo: €10,000 × 99% = €9,900
- Shares baseadas em €9,900

Opção B (taxa para fundo):
- €100 fica no fundo (beneficia todos)
- Shares baseadas em €10,000
- Pedro paga "entrada" que aumenta NAV de todos
```

## Vantagens Competitivas

### vs. Investimento Individual

| Aspecto | Individual | Fundo Comunitário |
|---------|-----------|-------------------|
| Diversificação | Limitada (capital pequeno) | Ampla (pool grande) |
| Fees de Exchange | Altas (% sobre pequenos valores) | Baixas (economia de escala) |
| Gestão | Tempo próprio necessário | Delegada |
| Conhecimento | Curva aprendizagem íngreme | Partilhado |
| Emocional | Decisões sozinho | Discussão em grupo |
| Custódia | Risco individual | Pode usar cold storage profissional |

### vs. Fundos Tradicionais de Cripto

| Aspecto | Fundo Tradicional | Crypto Dashboard |
|---------|-------------------|------------------|
| Mínimo | €10,000-€100,000 | €100-€1,000 |
| Fees | 2-3% gestão + 20% performance | Configurável (ou zero) |
| Transparência | Relatórios trimestrais | Real-time 24/7 |
| Liquidez | Lock-ups 6-12 meses | Flexível (config) |
| Setup | Lawyers, compliance (€€€) | Self-service (grátis) |
| Regulamentação | Pesada (MiFID, UCITS) | Peer-to-peer (cuidado legal) |

### vs. Exchange Staking/Earn

| Aspecto | Exchange Earn | Fundo Comunitário |
|---------|---------------|-------------------|
| Controlo | Na exchange (custódia deles) | Próprio (self-custody possível) |
| Estratégia | Fixa (staking APY) | Flexível (trading ativo) |
| Retorno | 3-8% APY | Potencial maior (ou menor) |
| Risco | Risco de exchange | Risco de mercado + gestão |
| Taxas | Taxas implícitas | Transparentes |

## Riscos e Mitigações

### Risco 1: Má Gestão

**Descrição**: Admin faz trades ruins, fundo perde valor

**Mitigação**:
- ✅ Transparência total: todos veem transações
- ✅ Definir estratégia clara antecipadamente
- ✅ Stop-loss automático (futuro)
- ✅ Votação para trades grandes (governança)

### Risco 2: Fraude/Theft

**Descrição**: Admin desvia fundos

**Mitigação**:
- ✅ Multi-sig para carteiras (requere 2+ assinaturas)
- ✅ Audit trail completo (impossível apagar)
- ✅ Regular auditorias externas
- ✅ Segregação de fundos (cold + hot wallet)
- ❌ **Limitação**: Sistema não impede transferências externas

### Risco 3: Preço Incorreto

**Descrição**: Bug causa NAV/share errado → alocação injusta

**Mitigação**:
- ✅ Fonte externa confiável (CoinGecko)
- ✅ Múltiplos endpoints (fallback)
- ✅ Validação de consistência (NAV = caixa + holdings)
- ✅ Histórico imutável (pode reverter se detetado)

### Risco 4: Regulamentação

**Descrição**: Autoridades consideram operação ilegal

**Mitigação**:
- ⚠️ **DISCLAIMER**: Sistema é ferramenta, não serviço regulado
- ⚠️ Participantes devem verificar legalidade local
- ⚠️ Não é aconselhamento financeiro
- ✅ Pode ser usado para fundos regulados (compliance externo)
- ✅ Pode ser usado apenas para tracking (sem movimentação real)

### Risco 5: Disputas entre Participantes

**Descrição**: Desacordo sobre estratégia ou levantamentos

**Mitigação**:
- ✅ Ownership matematicamente justo (elimina "ele entrou tarde e tem mais")
- ✅ Histórico completo auditável (prova de tudo)
- ✅ Regras claras documentadas antecipadamente
- ✅ Lock-up periods configuráveis
- ✅ Exit always at fair NAV/share

## Conformidade e Legal

### Disclaimer Importante

**Este software é uma ferramenta de gestão e não constitui**:
- ❌ Aconselhamento financeiro ou de investimento
- ❌ Oferta de valores mobiliários
- ❌ Serviço regulado de gestão de ativos
- ❌ Exchange ou plataforma de trading

**Responsabilidades dos utilizadores**:
- ✅ Verificar legalidade da operação na jurisdição local
- ✅ Cumprir requisitos de KYC/AML se aplicável
- ✅ Reportar ganhos de capital para fins fiscais
- ✅ Estabelecer contratos entre participantes
- ✅ Obter aconselhamento legal se necessário

### Uso Apropriado

**✅ Permitido e Recomendado**:
- Fundo familiar informal (sem publicidade)
- Clube de investimento privado entre amigos
- Tracking de portfólio pessoal (single-user)
- Ferramenta de back-office para fundo regulado (com compliance externo)

**⚠️ Zona Cinzenta** (verificar com advogado):
- Fundo com >50 participantes
- Publicidade ou captação pública
- Cobrar taxas de gestão/performance
- Aceitar participantes desconhecidos

**❌ Proibido** (sem licença apropriada):
- Operação como fundo de investimento regulado
- Gestão de capital de terceiros como serviço comercial
- Emissão de securities ou tokens
- Operação sem cumprir AML/KYC em jurisdições que requerem

## Monetização (Para Desenvolvedores)

Se você forkar este projeto e quiser monetizar:

### Modelo SaaS

**Planos**:
- **Free**: Até 5 participantes, funcionalidades básicas
- **Pro** (€29/mês): Até 50 participantes, histórico ilimitado, support
- **Enterprise** (€299/mês): Participantes ilimitados, white-label, API, SLA

**Receita Estimada**:
```
100 clientes Pro + 10 Enterprise = €5,890/mês = €70,680/ano
```

### Modelo Marketplace

**Taxa de Plataforma**: 0.5% sobre AUM (Assets Under Management)

**Exemplo**:
```
10 fundos, €500,000 AUM médio cada = €5M total AUM
0.5% anual = €25,000/ano para plataforma
```

### Serviços Profissionais

- Setup e consultoria: €1,000-€5,000
- Custom features: €500-€2,000 each
- Integração com exchanges: €5,000-€10,000
- Auditoria e compliance: €2,000-€10,000

---

**Anterior**: [← Snapshots e Preços](03-snapshots-precos.md)  
**Próximo**: [Guias de Utilizador →](05-guias-utilizador.md)
