"""Centralized category utilities for filtering by origin.

Provides UI options and SQL clause builder to filter transactions by
exchange categories (CEX, Wallet, DeFi) and explicit staking flag.

Usage:
- get_category_options() -> list[str]
- build_category_where_clause(selected, include_no_exchange, exchange_alias='e', tx_alias='t', supports_staking_column=True) -> str
"""
from typing import Iterable, List

# UI -> DB mapping (exchange categories in t_exchanges.category)
CATEGORY_UI_TO_DB = {
    "Exchange": "CEX",
    "Wallet": "Wallet",
    "DeFi": "DeFi",
}

CATEGORY_UI_OPTIONS: List[str] = ["Exchange", "Wallet", "DeFi"]


def get_category_options() -> List[str]:
    return CATEGORY_UI_OPTIONS.copy()


def build_category_where_clause(
    selected: Iterable[str],
    include_no_exchange: bool,
    exchange_alias: str = "e",
    tx_alias: str = "t",
) -> str:
    """Builds an SQL fragment (without the leading AND/WHERE) to filter by categories.

    Logic:
    - Non-staking categories (Exchange/Wallet/DeFi) map to e.category values.
    - Staking can be filtered via t.is_staking = TRUE (if column exists),
      else falls back to keyword heuristics on notes/exchange name.
    - include_no_exchange controls whether NULL exchange_id should be included
      alongside selected non-staking categories.
    - If selected covers all options and include_no_exchange is True, returns ''.
    """
    selected = set(selected or [])
    if not selected:
        # Nothing selected: match nothing (return clause that is always false)
        return "(1=0)"

    # If everything selected and nulls allowed, no filter needed
    all_opts = set(CATEGORY_UI_OPTIONS)
    if selected == all_opts and include_no_exchange:
        return ""

    subclauses: List[str] = []

    # Selected categories
    sel_mapped = [CATEGORY_UI_TO_DB[c] for c in selected if c in CATEGORY_UI_TO_DB]
    if sel_mapped:
        in_list = ",".join([f"'{c}'" for c in sel_mapped])
        base = f"{exchange_alias}.category IN ({in_list})"
        if include_no_exchange:
            base = f"({base} OR {exchange_alias}.exchange_id IS NULL)"
        subclauses.append(base)
    else:
        # None of the known categories selected
        if include_no_exchange:
            subclauses.append(f"{exchange_alias}.exchange_id IS NULL")

    if not subclauses:
        # No categories matched; if nulls not allowed, ensure we exclude them
        if not include_no_exchange:
            return f"({exchange_alias}.exchange_id IS NOT NULL)"
        return ""

    return "(" + " OR ".join(subclauses) + ")"
