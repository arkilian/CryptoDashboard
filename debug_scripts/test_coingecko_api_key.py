"""
Script de teste para verificar se a API key do CoinGecko está sendo usada corretamente.
"""
import logging
from services.coingecko import _get_coingecko_config, _get_headers, _get_base_url, get_price_by_symbol

# Configurar logging para ver os detalhes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_config():
    """Testa se a configuração está sendo carregada da DB."""
    print("\n" + "="*60)
    print("🧪 TESTE: Configuração CoinGecko")
    print("="*60)
    
    config = _get_coingecko_config()
    
    if config:
        print("✅ Config encontrada na DB:")
        print(f"   - API Name: {config.get('api_name')}")
        print(f"   - Base URL: {config.get('base_url')}")
        print(f"   - Rate Limit: {config.get('rate_limit')}/min")
        print(f"   - Timeout: {config.get('timeout')}s")
        print(f"   - Is Active: {config.get('is_active')}")
        
        api_key = config.get('api_key')
        if api_key:
            # Mostrar apenas primeiros e últimos caracteres
            masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            print(f"   - API Key: {masked}")
        else:
            print("   - API Key: ❌ Não configurada (usando plano free)")
    else:
        print("❌ Nenhuma config encontrada na DB")
    
    return config


def test_headers():
    """Testa se os headers estão sendo construídos corretamente."""
    print("\n" + "="*60)
    print("🧪 TESTE: Headers HTTP e Query Parameters")
    print("="*60)
    
    from services.coingecko import _get_coingecko_config
    
    headers = _get_headers()
    config = _get_coingecko_config()
    
    print("Headers que serão enviados:")
    for key, value in headers.items():
        if 'key' in key.lower():
            # Mascarar API key nos logs
            masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"   - {key}: {masked}")
        else:
            print(f"   - {key}: {value}")
    
    # Verificar tipo de API key
    if config and config.get('api_key'):
        api_key = config['api_key']
        if api_key.startswith('CG-'):
            print("\n✅ Demo API Key detectada - será enviada como query parameter (correto!)")
            print("   Parâmetro: x_cg_demo_api_key")
        elif 'x-cg-pro-api-key' in headers:
            print("\n✅ Pro API Key - será enviada como header (correto!)")
            print("   Header: x-cg-pro-api-key")
    else:
        print("\n⚠️ Nenhuma API key configurada - usando API pública")
    
    return headers


def test_base_url():
    """Testa se a URL base está correta."""
    print("\n" + "="*60)
    print("🧪 TESTE: URL Base")
    print("="*60)
    
    url = _get_base_url()
    print(f"URL Base: {url}")
    
    if 'pro-api' in url:
        print("✅ Usando URL da API Pro")
    else:
        print("⚠️ Usando URL da API pública")
        config = _get_coingecko_config()
        if config and config.get('api_key'):
            print("   ⚠️ ATENÇÃO: API Key configurada mas URL é pública!")
            print("   💡 Altere base_url para: https://pro-api.coingecko.com/api/v3")
    
    return url


def test_api_call():
    """Testa uma chamada real à API."""
    print("\n" + "="*60)
    print("🧪 TESTE: Chamada Real à API")
    print("="*60)
    
    try:
        print("Buscando preço do BTC...")
        result = get_price_by_symbol(["BTC"], vs_currency="eur")
        
        if result and result.get("BTC"):
            print(f"✅ Preço obtido: €{result['BTC']:,.2f}")
            print("\n📊 Verifique os logs acima para confirmar:")
            print("   1. Se 'CoinGecko config' mostra API Key=✓")
            print("   2. Se '🔑 API Key configurada' aparece nos logs")
            return True
        else:
            print("❌ Não foi possível obter preço")
            return False
    except Exception as e:
        print(f"❌ Erro na chamada: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("🔍 VERIFICAÇÃO DA API KEY DO COINGECKO")
    print("="*60)
    
    config = test_config()
    headers = test_headers()
    url = test_base_url()
    success = test_api_call()
    
    print("\n" + "="*60)
    print("📋 RESUMO")
    print("="*60)
    
    if config and config.get('api_key'):
        api_key = config['api_key']
        print("✅ API Key configurada na DB")
        
        if api_key.startswith('CG-'):
            print("✅ Demo API Key - enviada como query parameter (correto!)")
        elif 'x-cg-pro-api-key' in headers:
            print("✅ Pro API Key - enviada como header (correto!)")
        else:
            print("❌ API Key configurada mas não está sendo enviada")
        
        if 'pro-api' in url and not api_key.startswith('CG-'):
            print("✅ URL correta para API Pro")
        elif not api_key.startswith('CG-'):
            print("⚠️ URL pública - deveria usar pro-api.coingecko.com para Pro API")
        else:
            print("✅ URL pública correta para Demo API")
    else:
        print("⚠️ API Key não configurada - usando plano free")
    
    if success:
        print("✅ Chamada à API bem-sucedida")
    else:
        print("❌ Falha na chamada à API")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Vá para Settings > APIs CoinGecko")
    print("   2. Edite a configuração existente")
    print("   3. Adicione sua API key")
    print("   4. Se tiver plano Pro, altere base_url para:")
    print("      https://pro-api.coingecko.com/api/v3")
    print("   5. Execute este script novamente para verificar")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
