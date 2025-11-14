"""Pequeno teste de conectividade à base de dados PostgreSQL.

Usa variáveis de ambiente (para correr em GitHub Actions ou local):
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Saída:
  - Código de saída 0 em sucesso
  - Código de saída != 0 em falha
"""

from __future__ import annotations
import os
import sys
import psycopg2


def main() -> int:
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    missing = [k for k, v in {"DB_HOST":host, "DB_NAME":name, "DB_USER":user, "DB_PASSWORD":password}.items() if not v]
    if missing:
        print(f"⚠️ Variáveis ausentes: {', '.join(missing)}", file=sys.stderr)
        return 2

    dsn = f"host={host} port={port} dbname={name} user={user} password={password} sslmode=require"
    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        print("✅ Conexão PostgreSQL OK")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"❌ Erro na conexão: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
