-- ========================================
-- Migration: API CoinGecko Configuration
-- Created: 2025-11-04
-- ========================================
-- Cria tabela para configurar chave API do CoinGecko
-- (análoga a t_api_cardano)

CREATE TABLE IF NOT EXISTS t_api_coingecko (
    api_id SERIAL PRIMARY KEY,
    api_name TEXT UNIQUE NOT NULL,      -- Ex: "CoinGecko Pro", "CoinGecko Free"
    api_key TEXT,                       -- API key (opcional para plano free)
    base_url TEXT NOT NULL DEFAULT 'https://api.coingecko.com/api/v3',
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER DEFAULT 50,      -- Chamadas por minuto (ajustar conforme plano)
    timeout INTEGER DEFAULT 15,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice para lookup de API ativa
CREATE INDEX IF NOT EXISTS idx_api_coingecko_active ON t_api_coingecko(is_active);

-- Inserir configuração padrão (plano free sem API key)
INSERT INTO t_api_coingecko (api_name, api_key, base_url, is_active, rate_limit, notes)
VALUES (
    'CoinGecko Free',
    NULL,
    'https://api.coingecko.com/api/v3',
    TRUE,
    10,
    'Plano gratuito do CoinGecko (10-50 chamadas/minuto). Para planos Pro/Enterprise, adicionar API key.'
)
ON CONFLICT (api_name) DO NOTHING;
