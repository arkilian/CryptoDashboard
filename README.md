# 📊 Crypto Dashboard

Uma plataforma para gestão de um fundo comunitário de criptomoedas, com foco em transparência, controlo e simplicidade para administradores e investidores.

## 🚀 Funcionalidades (o que a plataforma faz)

- 🔐 Autenticação e perfis
   - Registo com username, email e password
   - Perfis de utilizador com dados pessoais (nome, data de nascimento, género, morada)
   - Perfis de acesso: Administrador e Utilizador

- 👥 Gestão de Utilizadores (Admin)
   - Ver lista de utilizadores e respetivos contactos
   - Adicionar/editar utilizadores (inclui definição/alteração de password)
   - Secção de dados financeiros por utilizador (depósitos e levantamentos)

- 💰 Movimentos de Capital
   - Registo de depósitos e levantamentos por utilizador
   - Histórico completo e filtros por data

- 📸 Snapshots de Portfólio
   - Registo manual de valores por carteira (Binance, Ledger, DeFi, Outros)
   - Consulta de snapshots por intervalo de datas

- 📈 Análise de Portfólio
   - Evolução do saldo (gráfico e métricas)
   - Ranking de Top Holders da comunidade
   - Distribuição de capital por utilizador

- 📊 Cotações
   - Integração com CoinGecko para consulta de preços e lista de ativos

- 📄 Documentos
   - Visualização de PDFs (ex.: regulamento, estratégia, roadmap)

## 💼 Modelo de Negócio (como funciona)

O Crypto Dashboard foi desenhado para gerir um fundo comunitário de criptoativos, onde os participantes aportam capital e acompanham, em tempo real, a valorização e as operações do fundo.

- Entradas e saídas de capital
   - Os utilizadores podem aportar (depósitos) e resgatar (levantamentos) capital, com histórico totalmente auditável.

- Estrutura de taxas (configurável pelo Admin)
   - Taxa de manutenção: aplicada periodicamente com taxa percentual e mínimo por utilizador.
   - Taxa de performance: cobrada sobre lucros acima do High-Water Mark (HWM), garantindo que só há cobrança quando o valor líquido do utilizador supera o máximo histórico.

- Transparência e reporting
   - Evolução de saldo por utilizador e no agregado (Fundo Comunitário)
   - Ranking de Top Holders e distribuição do capital
   - Snapshots de portfólio por carteiras e histórico de movimentos

- Governança e perfis
   - Administradores gerem utilizadores, taxas, documentos e análises globais
   - Utilizadores acompanham o próprio saldo, movimentos e documentos do fundo

> Nota: Esta plataforma é uma ferramenta de gestão e transparência. Não constitui aconselhamento financeiro. A utilização e parametrização das taxas é da responsabilidade dos administradores do fundo.

## 📚 Documentação técnica

A documentação técnica (setup, dependências, arquitetura, migrações, etc.) está disponível na Wiki do projeto.

