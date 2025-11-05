# Estratégias Anti-Bloqueio para Web Scraping do CoinGecko

## Problema
O CoinGecko (e muitos sites modernos) bloqueia scraping simples com **403 Forbidden** devido a:
- Detecção de bot via User-Agent desatualizado
- Falta de headers sec-ch-ua (Chrome moderno)
- Ausência de Referer natural
- Padrões de acesso não-humanos
- Proteções Cloudflare/bot-detection JS

---

## ✅ Soluções Implementadas

### 1. **Headers Realistas (Chrome 131)**
```python
headers = {
    "User-Agent": "Mozilla/5.0 ... Chrome/131.0.0.0 ...",  # Versão atual
    "sec-ch-ua": '"Google Chrome";v="131", ...',           # Client Hints
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "Referer": "https://www.coingecko.com/",               # Referer natural
}
```

**Impacto:** Imita browser real, passa verificações básicas de bot.

---

### 2. **Navegação Sequencial (Simular Humano)**
```python
# 1. Visitar homepage primeiro
session.get("https://www.coingecko.com/")
time.sleep(1.5)

# 2. Depois aceder à página da moeda
session.get(f"/en/coins/{coin_id}/historical_data")
time.sleep(1.0)

# 3. Finalmente fazer download
session.get(csv_link)
```

**Impacto:** Cookies de sessão válidos, padrão de navegação humano.

---

### 3. **Session Persistente**
```python
session = requests.Session()  # Mantém cookies entre requests
```

**Impacto:** Cloudflare/bot detection vê sessão contínua, não requests isolados.

---

### 4. **Delays Entre Requests**
```python
time.sleep(1.5)  # Homepage → página da moeda
time.sleep(1.0)  # Página → download
```

**Impacto:** Evita rate limiting, imita velocidade de leitura humana.

---

### 5. **Fallback: Selenium WebDriver** (Opção `--selenium`)
```python
# Chrome headless com anti-detecção
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})
```

**Impacto:** Executa JavaScript real, bypassa proteções JS avançadas.

**Requer:**
```bash
pip install selenium
# E ChromeDriver no PATH ou webdriver-manager
```

---

## 📋 Uso Recomendado

### Opção 1: CSV Manual (Mais Confiável) ✅
```bash
# 1. Descarregar manualmente de https://www.coingecko.com/en/coins/cardano/historical_data
# 2. Guardar como cardano/ada-usd-max.csv
# 3. Importar:
python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all
```

### Opção 2: Scraping Automático (Headers Melhorados)
```bash
python -m services.coingecko_scraper --coin bitcoin --days 30 --verbose
```

### Opção 3: Selenium (Casos Difíceis)
```bash
pip install selenium
python -m services.coingecko_scraper --coin ethereum --selenium --all
```

---

## 🚫 Limitações

### CoinGecko pode continuar a bloquear se:
1. **Cloudflare Challenge activo** - Requer resolução de CAPTCHA
2. **Rate limit agressivo** - Múltiplos requests em curto tempo
3. **IP blacklistado** - VPN/proxy pode ajudar
4. **JavaScript obfuscado** - Selenium pode não ser suficiente

### Alternativas:
- **API CoinGecko** (Demo: 10-30 req/min, Pro: ilimitado)
- **Download manual** de CSVs do site (mais fiável)
- **Outras fontes**: CoinMarketCap, Messari, CryptoCompare

---

## 🔧 Troubleshooting

### Erro: 403 Forbidden
**Causa:** Headers insuficientes ou padrão detectado como bot.

**Soluções:**
1. Usar `--selenium` (bypass com browser real)
2. Adicionar delay maior: `time.sleep(3)` antes do download
3. Usar proxy/VPN para mudar IP
4. Download manual do CSV

### Erro: Timeout
**Causa:** CoinGecko lento ou rate limit temporário.

**Soluções:**
1. Aumentar timeout: `timeout=60`
2. Tentar novamente mais tarde
3. Usar CSV existente

### Erro: HTML em vez de CSV
**Causa:** Link incorreto ou página de erro.

**Soluções:**
1. Verificar estrutura HTML do site (pode ter mudado)
2. Usar Selenium para inspecionar página
3. Download manual

---

## 📊 Resultados Actuais

### ✅ Cardano (CSV manual)
- **2941 registos** inseridos
- **2017-10-18 a 2025-11-05**
- Tempo: ~52 min (taxa USD→EUR dinâmica)
- Tempo otimizado: ~30s (taxa fixa 0.92)

### ⚠️ Bitcoin (scraping auto)
- **403 Forbidden** com headers básicos
- **Pendente teste** com headers melhorados
- **Alternativa:** CSV manual recomendado

---

## 🎯 Recomendação Final

**Para produção: usar CSV manual + import automático**

1. Descarregar CSVs manualmente 1x por semana
2. Guardar em `cardano/`, `bitcoin/`, etc.
3. Executar import automático:
   ```bash
   python -m services.coingecko_scraper --coin cardano --csv cardano/ada-usd-max.csv --all
   ```

**Vantagens:**
- ✅ 100% fiável (sem bloqueios)
- ✅ Rápido (~30s para 2941 registos)
- ✅ Sem dependências externas (Selenium)
- ✅ Não viola ToS do CoinGecko

**Desvantagens:**
- ❌ Requer intervenção manual
- ❌ Não é tempo real (mas histórico não muda)
