"""
Script para atualizar a API key do CoinGecko na base de dados.
"""
from database.connection import get_connection, return_connection

def update_coingecko_api_key():
    """Atualiza a API key do CoinGecko na tabela t_api_coingecko."""
    api_key = "CG-W8ULqPLWzt88XAYVrd81ra4J"
    rate_limit = 30  # Demo API: 30 chamadas por minuto
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Atualizar configuração existente
        cur.execute("""
            UPDATE t_api_coingecko 
            SET api_key = %s, 
                rate_limit = %s,
                notes = 'CoinGecko Demo API (30 chamadas/minuto)'
            WHERE api_name = 'CoinGecko Free'
            RETURNING api_id, api_name, rate_limit;
        """, (api_key, rate_limit))
        
        result = cur.fetchone()
        if result:
            conn.commit()
            print(f"✅ API key atualizada com sucesso!")
            print(f"   - ID: {result[0]}")
            print(f"   - Nome: {result[1]}")
            print(f"   - Rate Limit: {result[2]}/min")
            print(f"   - API Key: {api_key[:8]}...{api_key[-4:]}")
            print(f"\n📊 Delay calculado: {60.0 / result[2] * 1.2:.2f}s entre chamadas (com 20% buffer)")
        else:
            print("❌ Nenhuma configuração encontrada com nome 'CoinGecko Free'")
            conn.rollback()
            
    except Exception as e:
        print(f"❌ Erro ao atualizar: {e}")
        conn.rollback()
    finally:
        return_connection(conn)

if __name__ == "__main__":
    update_coingecko_api_key()
