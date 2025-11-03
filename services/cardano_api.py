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
                processed.append({
                    "hash": tx.get("hash", ""),
                    "timestamp": tx.get("timestamp", ""),
                    "fees": int(tx.get("fees", 0)) / 1_000_000,  # Converter para ADA
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
