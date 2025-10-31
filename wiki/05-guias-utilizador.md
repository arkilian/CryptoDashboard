# 👤 Guias de Utilizador

## Visão Geral

Este guia apresenta workflows práticos passo-a-passo para utilizadores e administradores do Crypto Dashboard.

---

## 🔐 Para Todos os Utilizadores

### Primeiro Acesso

**1. Receber Credenciais**

O administrador criará sua conta e fornecerá:
- Username
- Password inicial
- Link da aplicação

**2. Login Inicial**

1. Aceder ao URL da aplicação
2. Inserir username e password
3. Clicar em "Login"
4. Será redirecionado para o dashboard

**3. Alterar Password (Recomendado)**

1. No menu lateral → "⚙️ Configurações"
2. Secção "Alterar Password"
3. Inserir password atual
4. Inserir nova password (mínimo 6 caracteres)
5. Confirmar nova password
6. Clicar "Atualizar Password"

### Dashboard Principal

**Visão Geral do que vê**:

```
┌─────────────────────────────────────────┐
│  🏠 Crypto Dashboard                     │
├─────────────────────────────────────────┤
│  👤 Bem-vindo, [Seu Username]!          │
│                                          │
│  Menu Lateral:                           │
│  📊 Análise de Portfólio                │
│  ⚙️ Configurações                        │
│  🚪 Logout                               │
└─────────────────────────────────────────┘
```

### Ver Seu Portfólio

**Passo-a-passo**:

1. Menu lateral → "📊 Análise de Portfólio"
2. Verá automaticamente **seu** portfólio (não dos outros)

**Informação Mostrada**:

#### Métricas de Topo
```
💰 Saldo Atual (Fundo): €5,234.50
   └─> Seu valor total no fundo HOJE

📈 Total Depositado: €4,000.00
   └─> Soma de todos os seus depósitos

📉 Total Levantado: €0.00
   └─> Soma de todos os seus levantamentos
```

#### Gráfico de Evolução
- **Linha Azul**: Seus depósitos acumulados ao longo do tempo
- **Linha Vermelha**: Seus levantamentos acumulados
- **Linha Verde**: Valor real do seu portfólio (com ganhos/perdas do mercado)

**Interpretar o Gráfico**:
```
Se linha verde > linha azul → Está a ganhar 📈
Se linha verde < linha azul → Está a perder 📉
Se linha verde = linha azul → Break-even ➡️
```

#### Composição do Portfólio

**Exemplo**:
```
💼 Composição do Portfólio

💶 Caixa (EUR)         🪙 Valor em Cripto
   €500.00                €4,734.50

Ativos em Carteira:
┌──────┬────────────┬──────────────┬────────────┬──────────────┐
│Ativo │ Quantidade │ Preço Atual  │ Valor (€)  │ % Portfólio  │
├──────┼────────────┼──────────────┼────────────┼──────────────┤
│ ADA  │ 5000.0000  │ €0.524000    │ €2,620.00  │ 50.11%       │
│ BTC  │ 0.0500     │ €42,290.00   │ €2,114.50  │ 40.43%       │
└──────┴────────────┴──────────────┴────────────┴──────────────┘
```

**O que significa**:
- **Caixa**: Parte do fundo que está em EUR (pode ser usada para compras)
- **Valor em Cripto**: Soma de todos os ativos em criptomoedas
- **% do Portfólio**: Quanto cada ativo representa do total

### Solicitar Depósito

**Atenção**: Você não faz o depósito diretamente no sistema. O fluxo é:

1. **Contacta o administrador**:
   - Email, telefone ou presencialmente
   - Diz quanto quer depositar (ex: €1,000)

2. **Transfere o dinheiro**:
   - Transferência bancária para conta do fundo
   - OU entrega em dinheiro ao admin
   - OU transferência cripto (se fundo aceitar)

3. **Aguarda confirmação**:
   - Admin confirma recebimento
   - Admin regista no sistema
   - **Sistema calcula automaticamente suas shares**

4. **Verifica no dashboard**:
   - Refresca página
   - Vê novo saldo e ownership %
   - Recebe confirmação do admin

**Nota**: O preço que pagará (NAV/share) é o do momento em que admin registar, não quando você transferiu. Idealmente, admin regista logo após confirmação.

### Solicitar Levantamento

**Fluxo similar ao depósito**:

1. **Verifica quanto pode levantar**:
   - Vai a "Análise de Portfólio"
   - Vê "Saldo Atual" (ex: €5,234.50)
   - Esse é o máximo que pode levantar

2. **Contacta administrador**:
   - Informa valor desejado (ex: €2,000)
   - Fornece dados para transferência (IBAN, wallet, etc)

3. **Admin processa**:
   - Valida que você tem saldo suficiente
   - Transfere o dinheiro para você
   - Regista levantamento no sistema
   - **Sistema queima shares automaticamente**

4. **Verifica no dashboard**:
   - Saldo atualizado
   - Ownership % reduzido (se não levantou 100%)

### Interpretar Ownership e Shares

**O que são Shares?**
- São como "ações" do fundo
- Representam sua parte do bolo 🍰
- Não são um número que você escolhe - são calculadas automaticamente

**Exemplo Prático**:
```
Você tem: 1,000 shares
Fundo tem: 10,000 shares no total
→ Você possui: 1,000 ÷ 10,000 = 10% do fundo

Se fundo vale €50,000:
→ Seu valor: 10% × €50,000 = €5,000

Se mercado sobe e fundo vale €60,000:
→ Seu valor: 10% × €60,000 = €6,000
→ Suas shares continuam 1,000 (não mudam)
→ Seu % continua 10% (não muda)
→ Apenas o valor em EUR aumentou!
```

**Quando Shares Mudam**:
- ✅ Você deposita → ganha shares
- ✅ Você levanta → perde shares
- ❌ Mercado sobe/desce → shares NÃO mudam
- ❌ Outras pessoas depositam → suas shares NÃO mudam (mas % sim)

---

## 👥 Para Administradores

### Gestão de Utilizadores

#### Criar Novo Utilizador

1. Menu → "👥 Utilizadores"
2. Secção "➕ Adicionar Novo Utilizador"
3. Preencher formulário:
   ```
   Username: joao_silva
   Email: joao@email.com
   Password: [gerar forte]
   Confirmar Password: [repetir]
   É Admin?: [ ] (deixar desmarcado para utilizador normal)
   ```
4. Clicar "Criar Utilizador"
5. **Anotar credenciais para enviar ao utilizador**

**Boas Práticas**:
- ✅ Username sem espaços (usar _ ou -)
- ✅ Email válido (para recuperação futura)
- ✅ Password forte: mínimo 8 caracteres, maiúsculas, números
- ✅ Não tornar todos admin (princípio do menor privilégio)

#### Editar Utilizador Existente

1. Menu → "👥 Utilizadores"
2. Na lista, clicar no utilizador desejado
3. Secção "✏️ Editar Utilizador"
4. Modificar campos desejados
5. Para alterar password:
   - Inserir nova password
   - Confirmar nova password
6. Clicar "Atualizar Utilizador"

#### Perfil Detalhado (Opcional)

Para compliance ou organização:

1. Após criar/editar utilizador
2. Secção "Perfil Detalhado"
3. Preencher:
   ```
   Nome Completo: João Pedro Silva
   Data de Nascimento: 01/01/1990
   Género: Masculino
   Morada: Rua Example, 123, Lisboa
   ```
4. Salvar

**Utilidade**:
- Documentação KYC/AML
- Contactos de emergência
- Organização interna

### Processar Depósitos

**Workflow Completo**:

#### 1. Receber Fundos (Fora do Sistema)

```
Utilizador transfere €1,000 via:
- Transferência bancária
- Dinheiro físico
- Transferência cripto para wallet do fundo
```

**Confirmar Recebimento**:
- Verificar extrato bancário ✅
- OU confirmar transação blockchain ✅
- OU contar dinheiro físico ✅

#### 2. Registar no Sistema

1. Menu → "👥 Utilizadores"
2. Selecionar utilizador que depositou
3. Secção "💰 Movimentos de Capital"
4. Tab "Depósito"
5. Preencher:
   ```
   💶 Valor (EUR): 1000
   📅 Data: 2025-10-31  [data do recebimento]
   📝 Notas: Transferência bancária ref. 12345
   ```
6. Clicar "Registar Depósito"

#### 3. Sistema Aloca Shares Automaticamente

**O que acontece nos bastidores**:
```
1. Sistema calcula NAV total do fundo
2. Sistema calcula NAV por share
3. Shares alocadas = €1,000 ÷ NAV/share
4. Registo guardado em histórico (imutável)
```

**Exemplo**:
```
Antes do depósito:
- Fundo NAV: €10,000
- Total Shares: 5,000
- NAV/share: €2.00

João deposita €1,000:
- Shares para João: €1,000 ÷ €2.00 = 500 shares
- Novo total shares: 5,500
- Novo NAV fundo: €11,000
- NAV/share mantém: €11,000 ÷ 5,500 = €2.00 ✅
```

#### 4. Confirmar com Utilizador

Mensagem sugerida:
```
Olá João,

Confirmamos o recebimento do seu depósito de €1,000.00.

Detalhes:
- Data: 31/10/2025
- Shares alocadas: 500.000000
- NAV/share no momento: €2.00
- Seu novo total de shares: 500.000000
- Ownership: 9.09% do fundo

Pode verificar no dashboard.

Obrigado!
```

### Processar Levantamentos

**Workflow Completo**:

#### 1. Receber Pedido

```
Utilizador contacta:
"Quero levantar €2,000"
```

#### 2. Validar Saldo

1. Menu → "👥 Utilizadores"
2. Selecionar utilizador
3. Ver métricas de topo ou ir a "Análise de Portfólio"
4. Verificar "Saldo Atual"

**Exemplo**:
```
Maria tem:
- Shares: 1,200
- NAV/share atual: €2.50
- Valor: 1,200 × €2.50 = €3,000

Pediu: €2,000
→ Pode levantar? SIM ✅ (€2,000 < €3,000)
```

#### 3. Transferir Fundos (Fora do Sistema)

```
Transferir €2,000 para:
- IBAN do utilizador
- Wallet de cripto do utilizador
- Entregar dinheiro físico
```

**Confirmar Transferência**:
- Guardar comprovativo bancário
- OU guardar TX hash (cripto)
- OU recibo assinado (cash)

#### 4. Registar no Sistema

1. Menu → "👥 Utilizadores"
2. Selecionar utilizador
3. Secção "💰 Movimentos de Capital"
4. Tab "Levantamento"
5. Preencher:
   ```
   💶 Valor (EUR): 2000
   📅 Data: 2025-10-31
   📝 Notas: Transferência bancária para IBAN PT50...
   ```
6. Clicar "Registar Levantamento"

#### 5. Sistema Queima Shares Automaticamente

**O que acontece**:
```
1. Sistema calcula NAV/share atual
2. Shares a queimar = €2,000 ÷ NAV/share
3. Valida: utilizador tem shares suficientes?
4. Se sim: insere registo negativo
5. Se não: mostra erro (não pode prosseguir)
```

**Exemplo**:
```
Maria tinha:
- Shares: 1,200
- NAV/share: €2.50

Levantamento de €2,000:
- Shares queimadas: €2,000 ÷ €2.50 = 800 shares
- Shares restantes: 1,200 - 800 = 400 shares
- Maria continua no fundo com 400 shares
```

#### 6. Confirmar com Utilizador

```
Olá Maria,

Processámos o seu levantamento de €2,000.00.

Detalhes:
- Data: 31/10/2025
- Shares queimadas: 800.000000
- NAV/share no momento: €2.50
- Seu novo total de shares: 400.000000
- Ownership: 6.67% do fundo

Fundos transferidos para IBAN PT50****1234.

Obrigado!
```

### Executar Transações de Cripto

#### Comprar Criptomoeda

**Cenário**: Fundo tem €5,000 em caixa, quer comprar ADA

**Passo-a-passo**:

1. Menu → "💼 Portfólio"
2. Tab "Comprar"
3. Selecionar ativo:
   ```
   🪙 Ativo: ADA (Cardano)
   ```

4. Inserir quantidade:
   ```
   📊 Quantidade: 1000
   ```

5. **Opção A - Usar Preço de Mercado**:
   - Clicar botão "💹 Usar preço de mercado"
   - Sistema busca preço atual automaticamente
   - Campo "Preço Unitário" preenche sozinho (ex: €0.52)

6. **Opção B - Inserir Preço Manual**:
   - Preço Unitário (EUR): 0.52
   - Útil se comprou OTC ou noutra exchange

7. Data da transação:
   ```
   📅 Data: 2025-10-31  [hoje ou passado]
   ```

8. Fee (opcional):
   ```
   💸 Fee (EUR): 0.50  [taxa da exchange]
   ```

9. Notas (opcional):
   ```
   📝 Notas: Compra na Binance, ordem #123456
   ```

10. **Antes de confirmar, verificar**:
    ```
    Total: €520.50  [(1000 × €0.52) + €0.50 fee]
    Caixa disponível: €5,000 ✅
    ```

11. Clicar "Confirmar Compra"

**Sistema Atualiza**:
- ✅ Caixa: €5,000 → €4,479.50
- ✅ Holdings ADA: 0 → 1,000
- ✅ NAV mantém-se (trocou caixa por cripto)
- ✅ Shares de todos: NÃO mudam
- ✅ NAV/share: NÃO muda

#### Vender Criptomoeda

**Similar à compra, mas inverso**:

1. Menu → "💼 Portfólio"
2. Tab "Vender"
3. Selecionar ativo: ADA
4. Quantidade: 500 (vender metade)
5. Preço: usar botão "preço de mercado" ou manual
6. Fee: taxa da exchange
7. Confirmar

**Sistema Atualiza**:
- ✅ Holdings ADA: 1,000 → 500
- ✅ Caixa: aumenta (recebe EUR)
- ✅ NAV: pode subir/descer dependendo se vendeu com lucro/prejuízo
- ✅ Shares: NÃO mudam

#### Preços Históricos (Transação Antiga)

**Cenário**: Esqueceu-se de registar compra de ontem

1. Selecionar data no passado: 2025-10-30
2. Clicar "Usar preço de mercado"
3. **Sistema busca preço daquela data** (não de hoje!)
4. Confirma transação

**Importante**: 
- Sistema guarda o preço histórico para sempre
- Análises futuras usarão esse preço correto
- Não afeta cálculos de outras transações

### Analisar Performance do Fundo

#### Vista Agregada (Todos os Utilizadores)

1. Menu → "📊 Análise de Portfólio"
2. No topo, ver selector:
   ```
   🔍 Escolhe uma vista: 💰 Todos (Fundo Comunitário)
   ```
3. Deixar selecionado "Todos"

**Métricas Mostradas**:
```
💰 Saldo Atual (Fundo): €50,234.50
   └─> NAV total do fundo

📈 Total Depositado: €45,000.00
   └─> Soma de depósitos de TODOS

📉 Total Levantado: €3,000.00
   └─> Soma de levantamentos de TODOS

🎯 Performance implícita:
   €50,234.50 - €45,000 + €3,000 = €8,234.50 lucro (+18.3%)
```

#### Vista Individual

1. No selector, escolher utilizador específico
2. Ver métricas e gráficos apenas daquele utilizador
3. Útil para:
   - Responder dúvidas de utilizador
   - Preparar relatórios individuais
   - Validar cálculos

#### Top Holders (Ranking)

Na mesma página "Análise de Portfólio", rolar para baixo:

```
🏆 Top Holders da Comunidade

📊 NAV por Share          🔢 Total Shares       💰 NAV Total Fundo
   €2.50                     20,000                €50,000

┌────┬───────────┬───────────┬─────────────┬──────────────┐
│ 🏅 │ Utilizador│  Shares   │  Ownership  │   Valor (€)  │
├────┼───────────┼───────────┼─────────────┼──────────────┤
│ 🥇 │ João      │ 8,000.00  │    40.00%   │  €20,000.00  │
│ 🥈 │ Maria     │ 6,000.00  │    30.00%   │  €15,000.00  │
│ 🥉 │ Pedro     │ 4,000.00  │    20.00%   │  €10,000.00  │
│    │ Ana       │ 2,000.00  │    10.00%   │   €5,000.00  │
└────┴───────────┴───────────┴─────────────┴──────────────┘
```

**Gráfico Pizza**: Mostra distribuição visual

**Utilidade**:
- Transparência total para todos
- Reuniões: mostrar quem tem quanto
- Decisões: votos proporcionais a ownership

### Gestão de Snapshots de Preços

#### Ver Estatísticas de Cache

1. Menu → "⚙️ Configurações"
2. Secção "📸 Gestão de Snapshots"
3. Ver métricas:
   ```
   Total Snapshots: 1,547
   Ativos Cacheados: 12
   Tamanho: 256 kB
   ```

**O que são Snapshots**:
- Preços históricos guardados na base de dados
- Reduzem chamadas à API (mais rápido, sem rate limits)
- Acumulam ao longo do tempo

#### Limpar Cache Antigo

Se tabela ficar muito grande (>10,000 registos):

1. Na mesma secção
2. Clicar "🗑️ Limpar Cache Antigo (>2 anos)"
3. Confirmar
4. Sistema apaga apenas registos muito antigos (que não são mais usados)

#### Rebuild Completo (Raramente Necessário)

Se suspeitar de preços incorretos:

1. Clicar "🔄 Rebuild Cache Completo"
2. ⚠️ **ATENÇÃO**: Apaga TODOS os snapshots
3. Marcar checkbox "Confirmar (vai apagar tudo)"
4. Clicar novamente
5. Na próxima análise de portfólio, sistema recarrega automaticamente

**Quando usar**:
- CoinGecko mudou API e preços ficaram errados
- Migrou para outro provider de preços
- Debugging (última opção)

### Relatórios e Documentos

#### Upload de Documentos (Futuro)

Funcionalidade para partilhar:
- Regulamento do fundo (PDF)
- Estratégia de investimento
- Atas de reuniões
- Relatórios mensais

**Como usar** (quando implementado):
1. Menu → "📄 Documentos"
2. Upload de PDF
3. Todos os utilizadores podem visualizar

#### Exportar Dados

**Manualmente via Base de Dados**:
```sql
-- Exportar histórico de movimentos
COPY (
    SELECT u.username, cm.movement_date, cm.credit, cm.debit, cm.notes
    FROM t_user_capital_movements cm
    JOIN t_users u ON u.user_id = cm.user_id
    ORDER BY cm.movement_date DESC
) TO '/tmp/movimentos.csv' CSV HEADER;

-- Exportar shares atuais
COPY (
    SELECT u.username, 
           SUM(s.shares_amount) as total_shares,
           SUM(s.shares_amount) / (SELECT SUM(shares_amount) FROM t_user_shares) * 100 as ownership_pct
    FROM t_users u
    JOIN t_user_shares s ON u.user_id = s.user_id
    GROUP BY u.user_id, u.username
    ORDER BY total_shares DESC
) TO '/tmp/ownership.csv' CSV HEADER;
```

---

## ❓ FAQ Prático

### Para Utilizadores

**Q: Posso ver quanto os outros têm?**  
A: Não, apenas admins veem todos. Você só vê seu próprio portfólio.

**Q: Posso comprar/vender cripto diretamente?**  
A: Não, apenas admins fazem transações. Você participa do fundo, admin gere.

**Q: Quando posso levantar?**  
A: Depende das regras do seu fundo. Alguns permitem sempre, outros têm lock-up period (3-6 meses). Pergunte ao admin.

**Q: O preço que vejo está atualizado?**  
A: Sim! Preços são de hoje (CoinGecko API). Gráfico histórico usa preços de cada data.

**Q: Posso depositar em cripto?**  
A: Depende do fundo. Alguns aceitam, mas admin precisa converter para EUR equivalente.

### Para Administradores

**Q: E se errar um depósito/levantamento?**  
A: ⚠️ Sistema não tem "delete". Pode fazer movimento inverso (levantamento para corrigir depósito). Melhor validar sempre antes.

**Q: Posso editar o preço de uma transação antiga?**  
A: Não diretamente. Teria que ajustar manualmente na BD (não recomendado). Melhor registar corretamente desde o início.

**Q: Sistema cobra taxas automaticamente?**  
A: Não. Taxas de gestão/performance precisam ser implementadas manualmente (deduzir do caixa como "despesa").

**Q: Como fazer backup?**  
A: Ver próximo documento: [Setup e Deployment →](06-setup-deployment.md)

**Q: Posso ter múltiplos admins?**  
A: Sim! Ao criar/editar utilizador, marcar "É Admin?". Múltiplos admins veem e fazem tudo.

**Q: E se um utilizador quiser levantamento parcial?**  
A: Sem problema. Sistema queima apenas as shares equivalentes ao valor levantado. Utilizador continua com shares restantes.

---

## 🎓 Melhores Práticas

### Para Administradores

**Registro de Movimentos**:
- ✅ Sempre preencher campo "Notas" (rastreabilidade)
- ✅ Registar no mesmo dia do recebimento/envio
- ✅ Guardar comprovativos bancários separadamente
- ✅ Validar valores antes de confirmar

**Comunicação**:
- ✅ Confirmar com utilizador após processar depósito/levantamento
- ✅ Enviar relatório mensal (NAV, performance, holdings)
- ✅ Avisar antes de transações grandes (>20% do fundo)
- ✅ Manter canal aberto para dúvidas

**Segurança**:
- ✅ Não partilhar credenciais de admin
- ✅ Usar passwords fortes e únicas
- ✅ Fazer backup semanal da base de dados
- ✅ Validar endereços de wallet antes de transferir cripto

**Transparência**:
- ✅ Reuniões regulares (mensais ou trimestrais)
- ✅ Mostrar Top Holders (todos sabem ownership de todos)
- ✅ Explicar estratégia e raciocínio de trades
- ✅ Admitir erros e aprender com eles

### Para Utilizadores

**Monitorização**:
- ✅ Verificar dashboard semanalmente
- ✅ Validar depósitos/levantamentos após processamento
- ✅ Acompanhar performance vs. mercado (BTC/ETH baseline)
- ✅ Questionar se algo não fizer sentido

**Expectativas**:
- ✅ Entender que cripto é volátil
- ✅ Não esperar liquidez instantânea (admin precisa processar)
- ✅ Respeitar decisões de investimento (ou sair do fundo)
- ✅ Contribuir com ideias, mas não exigir trades específicos

---

**Anterior**: [← Modelo de Negócio](04-modelo-negocio.md)  
**Próximo**: [Setup e Deployment →](06-setup-deployment.md)
