"""
Serviço para integração com a API CardanoScan.
Fornece funcionalidades para consultar saldos, tokens e transações de endereços Cardano.
"""
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pycardano import Address

class CardanoScanAPI:
    """Cliente para a API CardanoScan."""
    
    BASE_URL = "https://api.cardanoscan.io/api/v1"
    
    # Mapa de tokens conhecidos e suas casas decimais (por nome)
    TOKEN_DECIMALS = {
        "DjedMicroUSD": 6,  # DJED tem 6 decimais
        "DJED": 6,
        "SHEN": 6,
        "USDC": 6,
        "USDT": 6,
        "USDM": 6,
        "iUSD": 6,
        "IUSD": 6,
        "AGIX": 8,
        "WMT": 6,
        "MIN": 6,
        "SUNDAE": 6,
        "MELD": 6,
        "INDY": 6,
        "HOSKY": 0,
    }

    # Mapa de casas decimais por policyId (pode usar prefixos para corresponder)
    TOKEN_DECIMALS_BY_POLICY = {
        # Exemplo: policyId (ou prefixo) -> decimais
        # "<policyIdCompletoOuPrefixo>": 6,
        "6df63e2fdde8": 6,  # Prefixo citado pelo utilizador
        "6df63e2fdde8b2c3b3396265b0cc824aa4fb999396b1c154280f6b0c": 6,  # PolicyId completo
    }
    
    # Mapa de nomes por policyId (para tokens sem assetName ou metadata incompleta)
    TOKEN_NAMES_BY_POLICY = {
        "6df63e2fdde8b2c3b3396265b0cc824aa4fb999396b1c154280f6b0c": "FREN",  # Nome conhecido
    }
    
    def __init__(self, api_key: str):
        """
        Inicializa o cliente da API CardanoScan.
        
        Args:
            api_key: Chave de API do CardanoScan
        """
        self.api_key = api_key
        self.headers = {"apiKey": api_key}
        # Cache de metadados de assets: chave "policyId.assetNameHex" -> dict
        self._asset_meta_cache: Dict[str, Dict] = {}

    def _asset_cache_key(self, policy_id: Optional[str], asset_name_hex: Optional[str]) -> Optional[str]:
        if not policy_id:
            return None
        return f"{policy_id}.{asset_name_hex or ''}"

    def _try_fetch(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Faz uma chamada GET simples e retorna JSON como dict se sucesso.
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            if resp.status_code != 200:
                return None
            data = resp.json()
            # Alguns endpoints podem devolver lista
            if isinstance(data, list):
                return data[0] if data else None
            return data
        except Exception:
            return None

    def _decode_hex_ascii(self, s: str) -> Optional[str]:
        """Decodifica string hex para ASCII, com tratamento robusto."""
        try:
            if not s:
                return None
            # Aceitar strings hex (par ou ímpar); tentar com padding se necessário
            if all(c in '0123456789abcdefABCDEF' for c in s):
                candidates = [s]
                if len(s) % 2 != 0:
                    candidates.append('0' + s)
                for hx in candidates:
                    try:
                        decoded = bytes.fromhex(hx).decode('utf-8', errors='ignore').strip()
                        # Filtrar apenas imprimíveis
                        printable = ''.join(ch for ch in decoded if ch.isprintable())
                        printable = printable.strip()
                        if printable and len(printable) > 0:
                            return printable
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    def _extract_name_from_metadata(self, meta: Dict, fallback_hex_name: Optional[str]) -> Optional[str]:
        # Tentativas diretas
        for key in ("name", "tokenName", "assetNameAscii", "ticker", "symbol", "displayName"):
            val = meta.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        # Nested comuns
        for parent in ("onchainMetadata", "metadata", "meta"):
            inner = meta.get(parent)
            if isinstance(inner, dict):
                for key in ("name", "tokenName", "ticker", "symbol", "displayName"):
                    val = inner.get(key)
                    if isinstance(val, str) and val.strip():
                        return val.strip()
        # Tentar decodificar assetName em hex
        hex_name = meta.get("assetName") or fallback_hex_name
        if isinstance(hex_name, str):
            decoded = self._decode_hex_ascii(hex_name)
            if decoded:
                return decoded
        return None

    def _extract_decimals_from_metadata(self, meta: Dict) -> Optional[int]:
        # Padrões comuns
        for key in ("decimals", "decimalPlaces", "tokenDecimals", "numberOfDecimals"):
            val = meta.get(key)
            try:
                if val is not None:
                    return int(val)
            except Exception:
                pass
        # Nested
        for parent in ("onchainMetadata", "metadata", "meta"):
            inner = meta.get(parent)
            if isinstance(inner, dict):
                for key in ("decimals", "decimalPlaces"):
                    val = inner.get(key)
                    try:
                        if val is not None:
                            return int(val)
                    except Exception:
                        pass
        return None

    def get_asset_metadata(self, policy_id: Optional[str], asset_name_hex: Optional[str]) -> Optional[Dict]:
        """
        Consulta metadados do token no CardanoScan e memoriza o resultado.
        """
        cache_key = self._asset_cache_key(policy_id, asset_name_hex)
        if cache_key and cache_key in self._asset_meta_cache:
            return self._asset_meta_cache[cache_key]

        if not policy_id:
            return None
        params = {"policyId": policy_id}
        if asset_name_hex is not None:
            params["assetName"] = asset_name_hex

        # Tentar alguns endpoints conhecidos do CardanoScan
        meta = self._try_fetch("/token/info", params) or self._try_fetch("/token/metadata", params)
        if not meta:
            return None

        # Enriquecer com name/decimals resolvidos
        resolved_name = self._extract_name_from_metadata(meta, asset_name_hex)
        resolved_decimals = self._extract_decimals_from_metadata(meta)
        if resolved_name is not None:
            meta["resolved_name"] = resolved_name
        if resolved_decimals is not None:
            meta["resolved_decimals"] = resolved_decimals

        if cache_key:
            self._asset_meta_cache[cache_key] = meta
        return meta
    
    def _convert_to_hex(self, address_bech32: str) -> str:
        """
        Converte endereço de formato bech32 para hexadecimal.
        
        Args:
            address_bech32: Endereço no formato bech32 (addr1...)
            
        Returns:
            Endereço em formato hexadecimal
        """
        address_obj = Address.from_primitive(address_bech32)
        return address_obj.to_primitive().hex()
    
    def get_balance(self, address: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Obtém o saldo de um endereço Cardano.
        
        Args:
            address: Endereço Cardano (bech32 format)
            
        Returns:
            Tupla (dados, mensagem_erro)
        """
        url = f"{self.BASE_URL}/address/balance"
        params = {"address": address}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 404:
                return None, "Endereço não encontrado ou ainda não possui transações on-chain"
            
            if response.status_code != 200:
                return None, f"Erro HTTP {response.status_code}: {response.text}"
            
            data = response.json()
            
            # Processar dados
            lovelace = int(data.get("balance", 0))
            ada = lovelace / 1_000_000
            
            result = {
                "lovelace": lovelace,
                "ada": ada,
                "tokens": data.get("tokens", []) or data.get("assets", [])
            }
            
            return result, None
            
        except requests.exceptions.Timeout:
            return None, "Timeout ao conectar à API CardanoScan"
        except requests.exceptions.RequestException as e:
            return None, f"Erro de conexão: {str(e)}"
        except Exception as e:
            return None, f"Erro inesperado: {str(e)}"
    
    def get_transactions(
        self, 
        address: str, 
        max_pages: int = 10
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Obtém transações de um endereço Cardano.
        
        Args:
            address: Endereço Cardano (bech32 format)
            max_pages: Número máximo de páginas a buscar
            
        Returns:
            Tupla (lista de transações, mensagem_erro)
        """
        try:
            # Converter endereço para hex
            address_hex = self._convert_to_hex(address)
        except Exception as e:
            return None, f"Erro ao converter endereço: {str(e)}"
        
        url = f"{self.BASE_URL}/transaction/list"
        all_transactions = []
        
        try:
            # Primeira página para obter total
            response = requests.get(
                url, 
                headers=self.headers, 
                params={"address": address_hex, "pageNo": 1},
                timeout=10
            )
            
            if response.status_code != 200:
                return None, f"Erro HTTP {response.status_code}: {response.text}"
            
            data = response.json()
            total_pages = min(data.get("count", 1), max_pages)
            all_transactions.extend(data.get("transactions", []))
            
            # Buscar páginas restantes
            for page in range(2, total_pages + 1):
                response = requests.get(
                    url,
                    headers=self.headers,
                    params={"address": address_hex, "pageNo": page},
                    timeout=10
                )
                
                if response.status_code == 200:
                    page_data = response.json().get("transactions", [])
                    all_transactions.extend(page_data)
            
            # Processar transações para formato amigável
            processed = []
            for tx in all_transactions:
                fees_value = tx.get("fees", 0)
                # Converter fees de string para int se necessário
                if isinstance(fees_value, str):
                    fees_value = int(fees_value) if fees_value else 0
                
                processed.append({
                    "hash": tx.get("hash", ""),
                    "timestamp": tx.get("timestamp", ""),
                    "fees": fees_value / 1_000_000,  # Converter para ADA
                    "block_height": tx.get("blockHeight", 0),
                    "status": "✅ Confirmada" if tx.get("status", False) else "⏳ Pendente",
                    "inputs": tx.get("inputs", []),
                    "outputs": tx.get("outputs", []),
                    "metadata": tx.get("metadata", {}),
                })
            
            return processed, None
            
        except requests.exceptions.Timeout:
            return None, "Timeout ao buscar transações"
        except requests.exceptions.RequestException as e:
            return None, f"Erro de conexão: {str(e)}"
        except Exception as e:
            return None, f"Erro inesperado: {str(e)}"
    
    def format_timestamp(self, timestamp_str: str) -> str:
        """
        Formata timestamp ISO para formato legível.
        
        Args:
            timestamp_str: String de timestamp ISO
            
        Returns:
            String formatada
        """
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except:
            return timestamp_str
    
    def format_ada_amount(self, lovelace: int) -> str:
        """
        Formata quantidade de lovelace para ADA.
        
        Args:
            lovelace: Quantidade em lovelace
            
        Returns:
            String formatada em ADA
        """
        ada = lovelace / 1_000_000
        return f"{ada:,.6f} ₳"
    
    def get_token_name(self, token: Dict) -> str:
        """
        Extrai nome do token de forma amigável.
        
        Args:
            token: Dicionário com informações do token
            
        Returns:
            Nome do token
        """
        # Override por policyId (para tokens sem assetName ou metadata)
        policy_id = token.get("policyId") or token.get("policy")
        if policy_id:
            # Correspondência exata
            if policy_id in self.TOKEN_NAMES_BY_POLICY:
                return self.TOKEN_NAMES_BY_POLICY[policy_id]
            # Correspondência por prefixo
            for key, name in self.TOKEN_NAMES_BY_POLICY.items():
                if policy_id.lower().startswith(key.lower()):
                    return name
        
        # Tentar metadados do explorer
        asset_hex = token.get("assetName") or token.get("asset_name") or token.get("name")
        meta = self.get_asset_metadata(policy_id, asset_hex)
        if meta and isinstance(meta, dict):
            nm = meta.get("resolved_name")
            if isinstance(nm, str) and nm.strip():
                return nm

        # Candidatos a nome direto (não-hex)
        candidates = [
            token.get("ticker"), token.get("symbol"), token.get("tokenName"),
            token.get("name"), token.get("assetName"), token.get("asset_name"),
        ]
        # Primeiro: se algum for string não-hex com conteúdo, usar
        for cand in candidates:
            if isinstance(cand, str) and cand.strip():
                s = cand.strip()
                # Se não parecer hex, usar diretamente
                if not all(c in '0123456789abcdefABCDEF' for c in s):
                    return s
        
        # Depois: tentar decodificar hex
        name = token.get("name") or token.get("assetName") or token.get("asset_name") or ""
        if name:
            decoded = self._decode_hex_ascii(name)
            if decoded:
                return decoded
            # Fallback: usar o hex como está
            return name
        
        policy = token.get("policyId", "")[:12]
        return f"Token {policy}..."
    
    def _resolve_decimals(self, policy_id: Optional[str], token_name: Optional[str], asset_name_hex: Optional[str] = None) -> int:
        """
        Resolve o número de casas decimais com base no policyId (com suporte a prefixo)
        e/ou no nome do token.
        """
        # 1) Metadados do explorer, se disponíveis
        meta = self.get_asset_metadata(policy_id, asset_name_hex)
        if meta and isinstance(meta, dict):
            rd = meta.get("resolved_decimals")
            if isinstance(rd, int):
                return rd
        if policy_id:
            pid = policy_id.lower()
            # Correspondência exata
            if pid in self.TOKEN_DECIMALS_BY_POLICY:
                return self.TOKEN_DECIMALS_BY_POLICY[pid]
            # Correspondência por prefixo
            for key, dec in self.TOKEN_DECIMALS_BY_POLICY.items():
                if pid.startswith(key.lower()):
                    return dec
        # Fallback por nome
        if token_name:
            return self.TOKEN_DECIMALS.get(token_name, 0)
        return 0

    def format_token_amount(self, amount: int, token_name: str, policy_id: Optional[str] = None, asset_name_hex: Optional[str] = None) -> float:
        """
        Formata quantidade de token baseado nas casas decimais conhecidas.
        
        Args:
            amount: Quantidade bruta do token
            token_name: Nome do token
            policy_id: PolicyId do token (opcional)
            
        Returns:
            Quantidade formatada como float
        """
        decimals = self._resolve_decimals(policy_id, token_name, asset_name_hex)
        
        if decimals > 0:
            return amount / (10 ** decimals)
        else:
            # Se não conhecemos o token, assumir que não tem decimais
            return float(amount)
    
    def analyze_transaction(self, tx: Dict, user_address: str) -> Dict:
        """
        Analisa uma transação e determina se foi enviada ou recebida pelo endereço.
        
        Args:
            tx: Dicionário com dados da transação
            user_address: Endereço do utilizador (para determinar direção)
            
        Returns:
            Dicionário com análise da transação
        """
        try:
            # Converter endereço do usuário para hex para comparação
            user_address_hex = self._convert_to_hex(user_address).lower()
        except:
            user_address_hex = user_address.lower()
        
        inputs = tx.get("inputs", [])
        outputs = tx.get("outputs", [])
        
        # Calcular totais
        total_input_user = 0
        total_output_user = 0
        # Utilizamos um mapa detalhado por (policyId, assetName/name) para não perder metadados
        token_balances = {}
        
        # Analisar inputs (de onde veio o ADA)
        for inp in inputs:
            addr = inp.get("address", "").lower()
            value = int(inp.get("value", 0))
            
            if addr == user_address_hex or addr == user_address.lower():
                total_input_user += value
                # Tokens enviados
                for token in inp.get("tokens", []):
                    policy_id = token.get("policyId", token.get("policy", ""))
                    asset_name = token.get("assetName", token.get("name", ""))
                    key = (policy_id, asset_name)
                    token_qty = int(token.get("value", token.get("quantity", token.get("amount", 0))))
                    token_balances[key] = token_balances.get(key, 0) - token_qty
                    # Pré-carregar metadados em cache
                    self.get_asset_metadata(policy_id, asset_name)
        
        # Analisar outputs (para onde foi o ADA)
        for out in outputs:
            addr = out.get("address", "").lower()
            value = int(out.get("value", 0))
            
            if addr == user_address_hex or addr == user_address.lower():
                total_output_user += value
                # Tokens recebidos
                for token in out.get("tokens", []):
                    policy_id = token.get("policyId", token.get("policy", ""))
                    asset_name = token.get("assetName", token.get("name", ""))
                    key = (policy_id, asset_name)
                    token_qty = int(token.get("value", token.get("quantity", token.get("amount", 0))))
                    token_balances[key] = token_balances.get(key, 0) + token_qty
                    # Pré-carregar metadados em cache
                    self.get_asset_metadata(policy_id, asset_name)
        
        # Calcular diferença líquida
        net_change = total_output_user - total_input_user
        fees_value = tx.get("fees", 0)
        # Se fees já foi processada como float, usar diretamente, senão processar
        if isinstance(fees_value, (int, str)):
            fees = int(fees_value) if isinstance(fees_value, str) else fees_value
        else:
            fees = int(fees_value * 1_000_000)  # Já está em ADA, converter para lovelace
        
        # Determinar tipo de transação
        if total_input_user > 0 and total_output_user == 0:
            tx_type = "sent"
            icon = "📤"
            description = "Enviado"
        elif total_input_user == 0 and total_output_user > 0:
            tx_type = "received"
            icon = "📥"
            description = "Recebido"
        elif total_input_user > 0 and total_output_user > 0:
            if net_change > 0:
                tx_type = "received"
                icon = "📥"
                description = "Recebido (parcial)"
            elif net_change < 0:
                tx_type = "sent"
                icon = "📤"
                description = "Enviado (com troco)"
            else:
                tx_type = "internal"
                icon = "🔄"
                description = "Interna"
        else:
            tx_type = "other"
            icon = "ℹ️"
            description = "Outra"
        
        # Calcular tokens líquidos com metadados
        net_tokens = {}
        net_tokens_detailed = []
        for (policy_id, asset_name), net in token_balances.items():
            if net == 0:
                continue
            token_info = {"policyId": policy_id, "assetName": asset_name}
            display_name = self.get_token_name(token_info)
            decimals = self._resolve_decimals(policy_id, display_name, asset_name)
            formatted = net / (10 ** decimals) if decimals > 0 else float(net)
            net_tokens[display_name] = formatted
            net_tokens_detailed.append({
                "name": display_name,
                "policyId": policy_id,
                "assetName": asset_name,
                "amount": formatted,
                "raw": net,
                "decimals": decimals,
            })
        
        return {
            "type": tx_type,
            "icon": icon,
            "description": description,
            "net_change_lovelace": net_change,
            "net_change_ada": net_change / 1_000_000,
            "fees_lovelace": fees,
            "fees_ada": fees / 1_000_000,
            "total_sent": total_input_user / 1_000_000,
            "total_received": total_output_user / 1_000_000,
            "net_tokens": net_tokens,
            "net_tokens_detailed": net_tokens_detailed,
        }
