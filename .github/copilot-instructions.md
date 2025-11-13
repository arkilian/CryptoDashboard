# Crypto Dashboard - AI Coding Assistant Guide

## Project Overview

Portuguese-language cryptocurrency fund management platform built with **Streamlit + PostgreSQL**. Implements a NAV/shares-based ownership system for community crypto funds with blockchain integration (Cardano), transaction tracking, and historical price snapshots.

**Core Tech Stack:** Python 3.10+, Streamlit, PostgreSQL, psycopg2, SQLAlchemy, Plotly, CoinGecko API

## Architecture & Data Flow

### Three-Layer Architecture
```
Streamlit UI (app.py, pages/*) 
  ↓
Business Logic (services/*) 
  ↓
Database Layer (database/*) 
  ↓
PostgreSQL + External APIs (CoinGecko, CardanoScan)
```

- **Entry Point:** `app.py` handles routing, session state, and page navigation
- **Pages:** Each page in `pages/` is a complete Streamlit module with `show()` or `show_<name>_page()` function
- **Services:** Business logic layer - NAV calculations (`shares.py`), price caching (`snapshots.py`), API clients (`coingecko.py`, `cardano_api.py`)
- **Database:** Connection pooling via `database/connection.py` with context managers

### Database Schema (V2)
Schema defined in `database/tablesv2.sql` (apply externally - no runtime migrations).

**Key Tables:**
- `t_users`, `t_user_profile` - Authentication (bcrypt) and user profiles
- `t_transactions` - **Transaction Model V2** (multi-asset, multi-account) with both new fields (`from_asset_id`, `to_asset_id`, etc.) and legacy fields (`asset_id`, `quantity`) for backwards compatibility
- `t_user_capital_movements` - Deposits/withdrawals that allocate/burn shares
- `t_price_snapshots` - Historical price cache (DB-first approach to avoid API rate limits)
- `t_cardano_transactions`, `t_cardano_tx_io` - Cardano blockchain data
- `t_exchanges`, `t_exchange_accounts`, `t_assets` - Multi-exchange, multi-account support
- `t_wallet`, `t_banco` - Wallet and bank account management

### NAV/Shares System (Critical)
The **ownership model** is NAV-based (like traditional mutual funds):

1. **NAV Calculation:** `services/shares.py::calculate_fund_nav()`
   - NAV = Cash (EUR) + Crypto Holdings (at current prices)
   - Cash = Deposits - Withdrawals - Buys + Sells
   
2. **NAV per Share:** Total NAV ÷ Total Shares Outstanding

3. **Share Allocation/Burning:**
   - Deposit: User receives `deposit_amount ÷ NAV_per_share` shares
   - Withdrawal: Burns `withdrawal_amount ÷ NAV_per_share` shares
   - Ensures proportional ownership regardless of entry/exit timing

4. **Querying Functions:**
   - `get_all_users_shares()` - Get shares for all users
   - `get_user_ownership_percentage()` - User's % of fund
   - `get_user_nav_value()` - User's portfolio value

## Critical Developer Workflows

### Running the Application
```bash
# Start Streamlit app (default port 8501)
streamlit run app.py

# Set custom port
streamlit run app.py --server.port 8502
```

### Database Setup
```bash
# 1. Create PostgreSQL database
# 2. Apply schema: psql -U <user> -d <dbname> -f database/tablesv2.sql
# 3. Configure .env file (see Environment Variables below)
```

### Environment Variables (Required)
Create `.env` in project root:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crypto_dashboard
DB_USER=your_user
DB_PASSWORD=your_password
```

### Price Data Import (CoinGecko)
**Manual CSV import is the ONLY reliable method** (web scraping fails due to anti-bot):

```bash
# Import historical prices from CSV
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all

# Verify import
python debug_scripts/check_csv_import.py
```

See `docs/COINGECKO_CSV_IMPORT.md` for detailed workflow.

### Cardano Sync
```bash
# Sync Cardano wallet transactions (used by Portfolio v3)
python scripts/sync_wallet2_now.py
```

### Testing
```bash
# Run test suites (when available)
python tests/test_services.py
python tests/test_performance_optimizations.py
```

## Project-Specific Conventions

### Connection Pooling Pattern
Always use context managers from `database/connection.py`:

```python
from database.connection import get_db_cursor, get_connection, return_connection

# Preferred: Auto-commit context manager
with get_db_cursor() as cur:
    cur.execute("SELECT * FROM t_users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    # Commits automatically on success, rollbacks on exception

# Alternative: Manual connection management
conn = get_connection()
try:
    cur = conn.cursor()
    cur.execute("...")
    conn.commit()
finally:
    cur.close()
    return_connection(conn)
```

### Session State Management
Streamlit session state keys (initialized in `app.py`):
- `page` - Current navigation page ('login', 'register', or menu selection)
- `user_id`, `username`, `is_admin` - Authentication state
- `menu_selection` - Current menu item (e.g., "📊 Análise de Portfólio")
- Component-specific keys use prefixes: `tx_v2_date`, `portfolio_data`

### Transaction Model V2 (Multi-Asset)
**Critical:** Understand the dual-mode system in `t_transactions`:

```python
# New V2 fields (preferred):
from_asset_id, from_quantity, from_account_id
to_asset_id, to_quantity, to_account_id
fee_asset_id, fee_quantity

# Legacy fields (still supported for backwards compatibility):
asset_id, quantity, price_eur, total_eur, fee_eur
```

**Transaction types** defined in `utils/transaction_types.py`:
- FIAT: `deposit`, `withdrawal`
- Trading: `buy`, `sell`, `swap`
- Transfer: `transfer`
- Staking: `stake`, `unstake`, `reward`
- DeFi: `lend`, `borrow`, `repay`, `liquidate`

See `wiki/07-transaction-model-v2.md` for detailed examples.

### Price Snapshot Strategy (Rate Limit Avoidance)
**DB-First approach** to minimize CoinGecko API calls:

```python
from services.snapshots import get_asset_price_on_date

# 1. Check t_price_snapshots table
# 2. If not found, call CoinGecko API
# 3. Store result in DB for future use
# 4. Respect 2-4 second delay between API calls
price = get_asset_price_on_date('cardano', '2024-01-15', 'eur')
```

Rate limiting config in `t_api_coingecko` table (dynamic, DB-driven).

### CSS Styling Pattern
Custom CSS injected via markdown in each page:

```python
from css.base import get_app_base_style
from css.sidebar import get_sidebar_style
from css.tables import get_tables_style

st.markdown(get_app_base_style(), unsafe_allow_html=True)
st.markdown(get_sidebar_style(), unsafe_allow_html=True)
```

Global gradient background: `linear-gradient(180deg, #0f172a 0%, #1e293b 100%)`

### Cardano Integration Pattern
Cardano data flows **DB-first** (not real-time API):

1. Sync via `services/cardano_sync.py` → populates `t_cardano_transactions`, `t_cardano_tx_io`
2. UI reads from local DB tables (Portfolio v3)
3. On-demand sync triggered by button in UI
4. Metadata (token names, decimals) cached in `t_cardano_assets`

API config in `t_api_cardano` (CardanoScan API key).

## Key Files Reference

### Core Application Files
- `app.py` - Main entry point, routing, session management
- `config.py` - Watched coins list, cache durations (30s users, 5min prices)
- `requirements.txt` - Pin dependencies (streamlit 1.39.0, pandas/numpy conditional on Python version)

### Critical Service Modules
- `services/shares.py` - NAV calculation, share allocation/burning (397 lines)
- `services/snapshots.py` - Price caching with DB-first strategy (408+ lines)
- `services/coingecko.py` - CoinGecko API client with rate limiting (667+ lines)
- `services/cardano_sync.py` - Cardano blockchain sync service (369+ lines)

### Database Modules
- `database/connection.py` - Connection pool, context managers, SQLAlchemy engine
- `database/users.py` - User CRUD, authentication with bcrypt
- `database/portfolio.py` - Portfolio snapshot operations
- `database/wallets.py` - Wallet management queries
- `database/api_config.py` - Dynamic API configuration from DB

### UI Components
- `components/transaction_form_v2.py` - Multi-asset transaction form (628 lines)
- `pages/portfolio_v3.py` - Main portfolio dashboard with Cardano integration
- `pages/portfolio_analysis.py` - Analytics dashboard with evolution charts
- `pages/users.py` - User management (admin only, 556+ lines)
- `pages/transactions.py` - Transaction management (admin only, 543+ lines)

### Utilities
- `utils/transaction_types.py` - Transaction type definitions and validation (316 lines)
- `utils/security.py` - bcrypt password hashing
- `utils/formatters.py` - Number/date formatting helpers

## Common Pitfalls & Solutions

### ❌ Don't: Create New Connection per Query
```python
# BAD - bypasses connection pool
import psycopg2
conn = psycopg2.connect(...)
```

### ✅ Do: Use Connection Pool
```python
# GOOD - reuses pooled connections
from database.connection import get_db_cursor
with get_db_cursor() as cur:
    cur.execute(...)
```

### ❌ Don't: Call CoinGecko API Directly in Loops
```python
# BAD - triggers rate limits
for date in dates:
    price = requests.get(f"https://api.coingecko.com/...{date}")
```

### ✅ Do: Use Snapshot Service with Bulk Fetch
```python
# GOOD - checks DB first, batches API calls with delays
from services.snapshots import ensure_assets_and_snapshots
ensure_assets_and_snapshots(assets, dates)
```

### ❌ Don't: Assume EUR is a Regular Asset
```python
# BAD - EUR might not be in t_assets
asset_id = get_asset_by_symbol('BTC')  # Works
eur_id = get_asset_by_symbol('EUR')    # May fail if not migrated
```

### ✅ Do: Query EUR Explicitly from t_assets
```python
# GOOD - EUR added by V2 migration to t_assets table
df = pd.read_sql("SELECT asset_id FROM t_assets WHERE symbol = 'EUR'", engine)
eur_asset_id = int(df.iloc[0]['asset_id']) if not df.empty else None
```

## Documentation

- **Wiki:** `wiki/` - Technical guides (architecture, NAV system, transaction model V2, Cardano integration)
- **Docs:** `docs/` - Operational guides (CSV import, performance optimizations, debugging)
- **Debug Scripts:** `debug_scripts/README.md` - Maintenance scripts (use with caution, may be outdated)

## Language & User-Facing Text

All UI text, comments, and messages are in **Portuguese (PT)**. Maintain this convention for consistency.

Example patterns:
- Error messages: `st.error("⚠️ Erro ao...")`
- Success messages: `st.success("✅ Sucesso!")`
- Menu items: `"📊 Análise de Portfólio"`, `"💰 Transações"`
- Button labels: `"🚪 Sair"`, `"🔄 Atualizar"`

## External Dependencies

- **CoinGecko API:** Free tier has strict rate limits (10-50 calls/min). Always use snapshot service, never direct calls.
- **CardanoScan API:** Configured per-wallet in `t_api_cardano`. Supports pagination for transaction history.
- **PostgreSQL 12+:** Required for JSON operations and modern SQL features.

---

**For detailed examples and workflows:** See `wiki/` directory, especially `wiki/01-arquitetura.md` and `wiki/07-transaction-model-v2.md`.
