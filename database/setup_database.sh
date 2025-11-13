#!/bin/bash
# ========================================
# CRYPTO DASHBOARD - SETUP BASE DE DADOS
# ========================================
# Script para criar uma base de dados PostgreSQL nova
# com estrutura e dados do Crypto Dashboard
# ========================================

echo ""
echo "========================================"
echo "CRYPTO DASHBOARD - SETUP BASE DE DADOS"
echo "========================================"
echo ""

# Configurações (editar conforme necessário)
PGUSER=${PGUSER:-postgres}
PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5432}
NEW_DB_NAME=${NEW_DB_NAME:-crypto_dashboard_novo}

echo "Configurações:"
echo "- Utilizador PostgreSQL: $PGUSER"
echo "- Host: $PGHOST"
echo "- Porta: $PGPORT"
echo "- Nova base de dados: $NEW_DB_NAME"
echo ""

# Verificar se psql está disponível
if ! command -v psql &> /dev/null; then
    echo "[ERRO] psql não encontrado!"
    echo "Por favor, instale o PostgreSQL ou adicione ao PATH."
    exit 1
fi

# Verificar se os ficheiros existem
if [ ! -f "schema.sql" ]; then
    echo "[ERRO] Ficheiro schema.sql não encontrado!"
    exit 1
fi

if [ ! -f "data_export.sql" ]; then
    echo "[ERRO] Ficheiro data_export.sql não encontrado!"
    exit 1
fi

echo "[1/4] A criar base de dados '$NEW_DB_NAME'..."
psql -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" -c "CREATE DATABASE $NEW_DB_NAME;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] Base de dados criada!"
else
    echo "[INFO] Base de dados pode já existir. A continuar..."
fi
echo ""

echo "[2/4] A aplicar schema (estrutura das tabelas)..."
psql -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" -d "$NEW_DB_NAME" -f schema.sql
if [ $? -ne 0 ]; then
    echo "[ERRO] Falha ao aplicar schema!"
    exit 1
fi
echo "[OK] Schema aplicado com sucesso!"
echo ""

echo "[3/4] A importar dados (isto pode demorar alguns minutos)..."
psql -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" -d "$NEW_DB_NAME" -f data_export.sql
if [ $? -ne 0 ]; then
    echo "[ERRO] Falha ao importar dados!"
    exit 1
fi
echo "[OK] Dados importados com sucesso!"
echo ""

echo "[4/4] A verificar instalação..."
psql -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" -d "$NEW_DB_NAME" -c "SELECT 'Tabelas criadas: ' || COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
psql -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" -d "$NEW_DB_NAME" -c "SELECT 'Utilizadores: ' || COUNT(*) FROM t_users;"
psql -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" -d "$NEW_DB_NAME" -c "SELECT 'Transações: ' || COUNT(*) FROM t_transactions;"
psql -U "$PGUSER" -h "$PGHOST" -p "$PGPORT" -d "$NEW_DB_NAME" -c "SELECT 'Preços: ' || COUNT(*) FROM t_price_snapshots;"
echo ""

echo "========================================"
echo "INSTALAÇÃO CONCLUÍDA!"
echo "========================================"
echo ""
echo "Próximos passos:"
echo "1. Atualizar o ficheiro .env com:"
echo "   DB_NAME=$NEW_DB_NAME"
echo ""
echo "2. Testar a conexão:"
echo "   python database/test_connection.py"
echo ""
echo "3. Iniciar a aplicação:"
echo "   streamlit run app.py"
echo ""
