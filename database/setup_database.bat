@echo off
REM ========================================
REM CRYPTO DASHBOARD - SETUP BASE DE DADOS
REM ========================================
REM Script para criar uma base de dados PostgreSQL nova
REM com estrutura e dados do Crypto Dashboard
REM ========================================

echo.
echo ========================================
echo CRYPTO DASHBOARD - SETUP BASE DE DADOS
echo ========================================
echo.

REM Configurações (editar conforme necessário)
set PGUSER=postgres
set PGHOST=localhost
set PGPORT=5432
set NEW_DB_NAME=crypto_dashboard_novo

echo Configuracoes:
echo - Usuario PostgreSQL: %PGUSER%
echo - Host: %PGHOST%
echo - Porta: %PGPORT%
echo - Nova base de dados: %NEW_DB_NAME%
echo.

REM Verificar se psql está disponível
where psql >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] psql nao encontrado!
    echo Por favor, adicione o PostgreSQL ao PATH ou execute manualmente.
    echo.
    pause
    exit /b 1
)

echo [1/4] A criar base de dados '%NEW_DB_NAME%'...
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -c "CREATE DATABASE %NEW_DB_NAME%;"
if %errorlevel% equ 0 (
    echo [OK] Base de dados criada!
) else (
    echo [INFO] Base de dados pode ja existir. A continuar...
)
echo.

echo [2/4] A aplicar schema (estrutura das tabelas)...
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -d %NEW_DB_NAME% -f schema.sql
if %errorlevel% equ 0 (
    echo [OK] Schema aplicado com sucesso!
) else (
    echo [ERRO] Falha ao aplicar schema!
    pause
    exit /b 1
)
echo.

echo [3/4] A importar dados (isto pode demorar alguns minutos)...
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -d %NEW_DB_NAME% -f data_export.sql
if %errorlevel% equ 0 (
    echo [OK] Dados importados com sucesso!
) else (
    echo [ERRO] Falha ao importar dados!
    pause
    exit /b 1
)
echo.

echo [4/4] A verificar instalacao...
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -d %NEW_DB_NAME% -c "SELECT 'Tabelas criadas: ' || COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -d %NEW_DB_NAME% -c "SELECT 'Utilizadores: ' || COUNT(*) FROM t_users;"
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -d %NEW_DB_NAME% -c "SELECT 'Transacoes: ' || COUNT(*) FROM t_transactions;"
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -d %NEW_DB_NAME% -c "SELECT 'Precos: ' || COUNT(*) FROM t_price_snapshots;"
echo.

echo ========================================
echo INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Proximos passos:
echo 1. Atualizar o ficheiro .env com:
echo    DB_NAME=%NEW_DB_NAME%
echo.
echo 2. Testar a conexao:
echo    python database/test_connection.py
echo.
echo 3. Iniciar a aplicacao:
echo    streamlit run app.py
echo.
pause
