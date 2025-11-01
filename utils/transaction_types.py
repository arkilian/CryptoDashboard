"""
Definição e lógica de tipos de transação para o modelo V2.
"""

# Mapeamento de tipos de transação para UI
TRANSACTION_TYPES = {
    # Categoria: FIAT Movements
    'deposit': {
        'label': '💶 Depósito (Banco → Exchange)',
        'category': 'FIAT',
        'fields': ['from_account', 'to_account', 'amount_eur', 'fee_eur', 'date', 'notes'],
        'description': 'Depositar EUR do banco para uma exchange'
    },
    'withdrawal': {
        'label': '💶 Levantamento (Exchange → Banco)',
        'category': 'FIAT',
        'fields': ['from_account', 'to_account', 'amount_eur', 'fee_eur', 'date', 'notes'],
        'description': 'Levantar EUR da exchange para o banco'
    },
    
    # Categoria: Basic Trading
    'buy': {
        'label': '🟢 Compra (EUR → Cripto)',
        'category': 'Trading',
        'fields': ['asset', 'quantity', 'price_eur', 'fee_eur', 'exchange', 'account', 'date', 'notes'],
        'description': 'Comprar criptomoeda com EUR'
    },
    'sell': {
        'label': '🔴 Venda (Cripto → EUR)',
        'category': 'Trading',
        'fields': ['asset', 'quantity', 'price_eur', 'fee_eur', 'exchange', 'account', 'date', 'notes'],
        'description': 'Vender criptomoeda por EUR'
    },
    'swap': {
        'label': '🔄 Swap (Cripto ↔ Cripto)',
        'category': 'Trading',
        'fields': ['from_asset', 'from_quantity', 'to_asset', 'to_quantity', 'fee_asset', 'fee_quantity', 'exchange', 'account', 'date', 'notes'],
        'description': 'Trocar uma criptomoeda por outra'
    },
    
    # Categoria: Transfers
    'transfer': {
        'label': '➡️ Transferência (Conta A → Conta B)',
        'category': 'Transfer',
        'fields': ['asset', 'quantity', 'from_account', 'to_account', 'fee_asset', 'fee_quantity', 'date', 'notes'],
        'description': 'Mover ativos entre contas/wallets'
    },
    
    # Categoria: Staking
    'stake': {
        'label': '🔒 Stake (Lock em Staking/Earn)',
        'category': 'Staking',
        'fields': ['asset', 'quantity', 'from_account', 'to_account', 'date', 'notes'],
        'description': 'Colocar ativos em staking/earn'
    },
    'unstake': {
        'label': '🔓 Unstake (Unlock de Staking/Earn)',
        'category': 'Staking',
        'fields': ['asset', 'quantity', 'from_account', 'to_account', 'date', 'notes'],
        'description': 'Remover ativos de staking/earn'
    },
    'reward': {
        'label': '🎁 Recompensa (Staking/Airdrop)',
        'category': 'Staking',
        'fields': ['asset', 'quantity', 'to_account', 'date', 'notes'],
        'description': 'Receber recompensas de staking ou airdrops'
    },
    
    # Categoria: DeFi
    'lend': {
        'label': '🏦 Lend (Fornecer Liquidez)',
        'category': 'DeFi',
        'fields': ['asset', 'quantity', 'from_account', 'to_account', 'fee_asset', 'fee_quantity', 'date', 'notes'],
        'description': 'Emprestar ativos a protocolo DeFi'
    },
    'borrow': {
        'label': '🏦 Borrow (Pedir Emprestado)',
        'category': 'DeFi',
        'fields': ['asset', 'quantity', 'to_account', 'fee_asset', 'fee_quantity', 'date', 'notes'],
        'description': 'Pedir emprestado de protocolo DeFi'
    },
    'repay': {
        'label': '💳 Repay (Pagar Empréstimo)',
        'category': 'DeFi',
        'fields': ['asset', 'quantity', 'from_account', 'fee_asset', 'fee_quantity', 'date', 'notes'],
        'description': 'Devolver empréstimo a protocolo DeFi'
    },
    'liquidate': {
        'label': '⚠️ Liquidação (Perda de Colateral)',
        'category': 'DeFi',
        'fields': ['asset', 'quantity', 'from_account', 'date', 'notes'],
        'description': 'Registar liquidação/perda de colateral'
    },
}


def get_transaction_types_by_category():
    """Retorna tipos de transação agrupados por categoria."""
    categories = {}
    for tx_type, config in TRANSACTION_TYPES.items():
        cat = config['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((tx_type, config['label']))
    return categories


def get_required_fields(transaction_type):
    """Retorna lista de campos obrigatórios para um tipo de transação."""
    if transaction_type not in TRANSACTION_TYPES:
        return []
    return TRANSACTION_TYPES[transaction_type]['fields']


def needs_from_asset(transaction_type):
    """Verifica se o tipo de transação precisa de from_asset."""
    required = get_required_fields(transaction_type)
    return 'from_asset' in required or transaction_type in ['buy', 'sell', 'swap', 'transfer', 'stake', 'unstake', 'lend', 'repay', 'liquidate']


def needs_to_asset(transaction_type):
    """Verifica se o tipo de transação precisa de to_asset."""
    required = get_required_fields(transaction_type)
    return 'to_asset' in required or transaction_type in ['buy', 'sell', 'swap', 'transfer', 'stake', 'unstake', 'reward', 'lend', 'borrow']


def needs_from_account(transaction_type):
    """Verifica se o tipo de transação precisa de from_account."""
    return transaction_type in ['deposit', 'withdrawal', 'transfer', 'stake', 'unstake', 'lend', 'repay', 'liquidate']


def needs_to_account(transaction_type):
    """Verifica se o tipo de transação precisa de to_account."""
    return transaction_type in ['deposit', 'withdrawal', 'transfer', 'stake', 'unstake', 'reward', 'lend', 'borrow']


def needs_fee_asset(transaction_type):
    """Verifica se o tipo de transação pode ter fee em asset diferente de EUR."""
    return transaction_type in ['swap', 'transfer', 'lend', 'borrow', 'repay']


def build_transaction_params(transaction_type, form_data):
    """
    Constrói parâmetros para INSERT baseado no tipo de transação.
    
    Args:
        transaction_type: Tipo de transação
        form_data: Dict com dados do formulário
        
    Returns:
        Dict com parâmetros prontos para SQL
    """
    params = {
        'transaction_type': transaction_type,
        'transaction_date': form_data.get('transaction_date'),
        'executed_by': form_data.get('executed_by'),
        'notes': form_data.get('notes'),
    }
    
    # Mapear campos conforme tipo
    if transaction_type in ['deposit', 'withdrawal']:
        # EUR movement
        eur_id = form_data.get('eur_asset_id')
        amount = form_data.get('amount_eur')
        params.update({
            'from_asset_id': eur_id,
            'to_asset_id': eur_id,
            'from_quantity': amount,
            'to_quantity': amount,
            'from_account_id': form_data.get('from_account_id'),
            'to_account_id': form_data.get('to_account_id'),
            'fee_eur': form_data.get('fee_eur', 0),
            'fee_asset_id': eur_id,
            'fee_quantity': form_data.get('fee_eur', 0),
        })
        
    elif transaction_type == 'buy':
        # EUR → Cripto
        eur_id = form_data.get('eur_asset_id')
        asset_id = form_data.get('asset_id')
        quantity = form_data.get('quantity')
        price_eur = form_data.get('price_eur')
        total_eur = quantity * price_eur
        fee_eur = form_data.get('fee_eur', 0)
        
        params.update({
            'from_asset_id': eur_id,
            'to_asset_id': asset_id,
            'from_quantity': total_eur + fee_eur,
            'to_quantity': quantity,
            'account_id': form_data.get('account_id'),
            'exchange_id': form_data.get('exchange_id'),
            'fee_eur': fee_eur,
            'fee_asset_id': eur_id,
            'fee_quantity': fee_eur,
            # Legacy fields
            'asset_id': asset_id,
            'quantity': quantity,
            'price_eur': price_eur,
            'total_eur': total_eur,
        })
        
    elif transaction_type == 'sell':
        # Cripto → EUR
        eur_id = form_data.get('eur_asset_id')
        asset_id = form_data.get('asset_id')
        quantity = form_data.get('quantity')
        price_eur = form_data.get('price_eur')
        total_eur = quantity * price_eur
        fee_eur = form_data.get('fee_eur', 0)
        
        params.update({
            'from_asset_id': asset_id,
            'to_asset_id': eur_id,
            'from_quantity': quantity,
            'to_quantity': total_eur - fee_eur,
            'account_id': form_data.get('account_id'),
            'exchange_id': form_data.get('exchange_id'),
            'fee_eur': fee_eur,
            'fee_asset_id': eur_id,
            'fee_quantity': fee_eur,
            # Legacy fields
            'asset_id': asset_id,
            'quantity': quantity,
            'price_eur': price_eur,
            'total_eur': total_eur,
        })
        
    elif transaction_type == 'swap':
        # Cripto A → Cripto B
        params.update({
            'from_asset_id': form_data.get('from_asset_id'),
            'to_asset_id': form_data.get('to_asset_id'),
            'from_quantity': form_data.get('from_quantity'),
            'to_quantity': form_data.get('to_quantity'),
            'account_id': form_data.get('account_id'),
            'exchange_id': form_data.get('exchange_id'),
            'fee_asset_id': form_data.get('fee_asset_id'),
            'fee_quantity': form_data.get('fee_quantity', 0),
        })
        
    elif transaction_type == 'transfer':
        # Conta A → Conta B
        params.update({
            'from_asset_id': form_data.get('asset_id'),
            'to_asset_id': form_data.get('asset_id'),
            'from_quantity': form_data.get('quantity'),
            'to_quantity': form_data.get('quantity') - form_data.get('fee_quantity', 0),
            'from_account_id': form_data.get('from_account_id'),
            'to_account_id': form_data.get('to_account_id'),
            'fee_asset_id': form_data.get('fee_asset_id') or form_data.get('asset_id'),
            'fee_quantity': form_data.get('fee_quantity', 0),
        })
        
    elif transaction_type in ['stake', 'unstake']:
        # Lock/Unlock
        params.update({
            'from_asset_id': form_data.get('asset_id'),
            'to_asset_id': form_data.get('asset_id'),
            'from_quantity': form_data.get('quantity'),
            'to_quantity': form_data.get('quantity'),
            'from_account_id': form_data.get('from_account_id'),
            'to_account_id': form_data.get('to_account_id'),
        })
        
    elif transaction_type == 'reward':
        # Recompensa recebida
        params.update({
            'to_asset_id': form_data.get('asset_id'),
            'to_quantity': form_data.get('quantity'),
            'to_account_id': form_data.get('to_account_id'),
        })
        
    elif transaction_type == 'lend':
        # Lending
        params.update({
            'from_asset_id': form_data.get('asset_id'),
            'to_asset_id': form_data.get('asset_id'),
            'from_quantity': form_data.get('quantity'),
            'to_quantity': form_data.get('quantity'),
            'from_account_id': form_data.get('from_account_id'),
            'to_account_id': form_data.get('to_account_id'),
            'fee_asset_id': form_data.get('fee_asset_id'),
            'fee_quantity': form_data.get('fee_quantity', 0),
        })
        
    elif transaction_type == 'borrow':
        # Borrowing
        params.update({
            'to_asset_id': form_data.get('asset_id'),
            'to_quantity': form_data.get('quantity'),
            'to_account_id': form_data.get('to_account_id'),
            'fee_asset_id': form_data.get('fee_asset_id'),
            'fee_quantity': form_data.get('fee_quantity', 0),
        })
        
    elif transaction_type == 'repay':
        # Repayment
        params.update({
            'from_asset_id': form_data.get('asset_id'),
            'from_quantity': form_data.get('quantity'),
            'from_account_id': form_data.get('from_account_id'),
            'fee_asset_id': form_data.get('fee_asset_id'),
            'fee_quantity': form_data.get('fee_quantity', 0),
        })
        
    elif transaction_type == 'liquidate':
        # Liquidation
        params.update({
            'from_asset_id': form_data.get('asset_id'),
            'from_quantity': form_data.get('quantity'),
            'from_account_id': form_data.get('from_account_id'),
        })
    
    return params
