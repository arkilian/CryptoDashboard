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
    
    def __init__(self, api_key: str):
        """
        Inicializa o cliente da API CardanoScan.
        
        Args:
            api_key: Chave de API do CardanoScan
        """
        self.api_key = api_key
        self.headers = {"apiKey": api_key}
    
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
        name = token.get("name") or token.get("assetName", "")
        if name:
            # Tentar decodificar hex para string legível
            try:
                if len(name) > 10 and all(c in '0123456789abcdefABCDEF' for c in name):
                    decoded = bytes.fromhex(name).decode('utf-8', errors='ignore')
                    if decoded.isprintable():
                        return decoded
            except:
                pass
            return name
        
        policy = token.get("policyId", "")[:12]
        return f"Token {policy}..."
    
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
        tokens_received = {}
        tokens_sent = {}
        
        # Analisar inputs (de onde veio o ADA)
        for inp in inputs:
            addr = inp.get("address", "").lower()
            value = int(inp.get("value", 0))
            
            if addr == user_address_hex or addr == user_address.lower():
                total_input_user += value
                # Tokens enviados
                for token in inp.get("tokens", []):
                    token_name = self.get_token_name(token)
                    token_qty = int(token.get("value", token.get("quantity", token.get("amount", 0))))
                    tokens_sent[token_name] = tokens_sent.get(token_name, 0) + token_qty
        
        # Analisar outputs (para onde foi o ADA)
        for out in outputs:
            addr = out.get("address", "").lower()
            value = int(out.get("value", 0))
            
            if addr == user_address_hex or addr == user_address.lower():
                total_output_user += value
                # Tokens recebidos
                for token in out.get("tokens", []):
                    token_name = self.get_token_name(token)
                    token_qty = int(token.get("value", token.get("quantity", token.get("amount", 0))))
                    tokens_received[token_name] = tokens_received.get(token_name, 0) + token_qty
        
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
        
        # Calcular tokens líquidos (recebidos - enviados)
        all_tokens = set(list(tokens_received.keys()) + list(tokens_sent.keys()))
        net_tokens = {}
        for token in all_tokens:
            received = tokens_received.get(token, 0)
            sent = tokens_sent.get(token, 0)
            net = received - sent
            if net != 0:
                net_tokens[token] = net
        
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
            "tokens_sent": tokens_sent,
            "tokens_received": tokens_received
        }
