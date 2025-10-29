# 📊 Crypto Dashboard

Um dashboard em Streamlit para gerir portfólio de criptomoedas como um fundo comunitário.
Suporta multi-utilizador, com taxas configuráveis, snapshots de portfólio e histórico completo.

## 🚀 Funcionalidades

### 🔐 Autenticação e Gestão de Utilizadores
- Login/registro seguro com hash + salt
- Diferenciação Admin / User
- Gestão de perfis e dados pessoais

### 💰 Portfolio e Investimentos
- Visualização de saldo e movimentos
- Gráficos de evolução do portfólio
- Top holders e distribuição de ativos
- Snapshots manuais de diferentes carteiras

### 💹 Cotações e Mercado
- Integração com CoinGecko API
- Preços em tempo real
- Gráficos históricos
- Widget de cotações ao vivo

### ⚙️ Administração
- Configuração de taxas (manutenção e performance)
- Histórico detalhado de taxas
- Gestão de documentos e PDFs
- Controle de acesso baseado em roles

### 📜 Análise e Relatórios
- Snapshots automáticos do portfólio
- Histórico de movimentações
- Gráficos de desempenho
- Exportação de dados

## 🛠️ Tecnologias

### Frontend
- **Streamlit**: Interface principal
- **Plotly**: Gráficos interativos
- **Streamlit-AgGrid**: Tabelas avançadas

### Backend
- **PostgreSQL**: Base de dados
- **Python 3.10+**: Linguagem principal
- **psycopg2**: Conexão PostgreSQL
- **python-dotenv**: Gestão de configuração

### APIs e Integrações
- **CoinGecko API**: Dados de mercado
- **Python-Jose**: Tokens JWT
- **Requests**: Chamadas HTTP

## ⚙️ Setup

1. Clone o repositório
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente:
   - Windows: `.\.venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instale as dependências: `pip install -r requirements.txt`
5. Configure o `.env` baseado no `.env.example`
6. Execute as migrações: `python database/run_migrations.py`
7. Inicie o app: `streamlit run app.py`

## 📁 Estrutura do Projeto

```
CryptoDashboard/
├── app.py              # Ponto de entrada
├── config.py           # Configurações
├── requirements.txt    # Dependências
├── auth/              # Autenticação
├── database/          # Banco de dados
│   └── migrations/    # Scripts SQL
├── pages/             # Páginas Streamlit
├── services/          # Lógica de negócio
├── utils/             # Utilitários
└── docs/              # Documentação
```

## 🧪 Testes

Execute os testes com:
```bash
python -m unittest discover tests
```

## 📄 Licença

MIT License - veja LICENSE para mais detalhes.
