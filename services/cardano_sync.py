"""
Cardano Sync Service
--------------------
DB-first synchronization of Cardano transactions for configured wallets.

Flow:
1) Read active Cardano API config (CardanoScan) and active wallets (blockchain='Cardano').
2) For each wallet, fetch recent transactions (paginated, recent-first) and persist:
   - t_cardano_transactions (one per tx)
   - t_cardano_tx_io (only IO rows that match the wallet address)
   - t_cardano_assets (metadata of tokens encountered)
3) Portfolio v3 reads deltas from DB and only calls sync on-demand (button).

Notes:
- We intentionally avoid projecting into t_transactions (V2) to keep scope minimal.
- ADA amounts are stored in lovelace; token quantities in raw integer and formatted amount (if decimals known).
"""

from __future__ import annotations

from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone
import logging

from database.connection import get_connection, return_connection
from database.api_config import get_active_apis
from database.wallets import get_active_wallets
from services.cardano_api import CardanoScanAPI
from services.snapshots import ensure_assets_and_snapshots, start_ensure_assets_and_snapshots_async
from psycopg2.extras import Json

logger = logging.getLogger(__name__)


def _get_api_client() -> Optional[CardanoScanAPI]:
    apis = get_active_apis()
    if not apis:
        return None
    api_key = apis[0].get("api_key")
    if not api_key:
        return None
    return CardanoScanAPI(api_key)


def _upsert_cardano_asset(cur, policy_id: Optional[str], asset_name_hex: Optional[str], display_name: Optional[str], decimals: Optional[int]):
    """Upsert asset metadata into t_cardano_assets."""
    if not policy_id:
        return  # ADA doesn't go here
    # Some tokens may omit assetName; normalize to empty string to satisfy PK NOT NULL
    asset_name_hex = asset_name_hex or ""
    cur.execute(
        """
        INSERT INTO t_cardano_assets (policy_id, asset_name_hex, display_name, decimals)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (policy_id, asset_name_hex)
        DO UPDATE SET display_name = COALESCE(EXCLUDED.display_name, t_cardano_assets.display_name),
                      decimals = COALESCE(EXCLUDED.decimals, t_cardano_assets.decimals)
        """,
        (policy_id, asset_name_hex, display_name, decimals),
    )


def _insert_transaction(cur, wallet_id: int, address: str, tx: Dict):
    """Insert or ignore a transaction row."""
    tx_hash = tx.get("hash")
    ts = tx.get("timestamp")
    # Normalize timestamp to TZ-aware
    if isinstance(ts, str):
        try:
            if "T" in ts:
                tx_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            else:
                tx_dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except Exception:
            tx_dt = None
    elif isinstance(ts, (int, float)):
        tx_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        tx_dt = None

    # Fees already converted to ADA in cardano_api
    fees_ada = 0.0
    fees_val = tx.get("fees")
    try:
        fees_ada = float(fees_val)
    except Exception:
        fees_ada = 0.0

    cur.execute(
        """
        INSERT INTO t_cardano_transactions (tx_hash, wallet_id, address, block_height, tx_timestamp, status, fees_ada, raw_payload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tx_hash, wallet_id) DO UPDATE SET
            block_height = EXCLUDED.block_height,
            tx_timestamp = EXCLUDED.tx_timestamp,
            status = EXCLUDED.status,
            fees_ada = EXCLUDED.fees_ada
        """,
        (
            tx_hash,
            wallet_id,
            address,
            tx.get("block_height") or tx.get("blockHeight"),
            tx_dt,
            ("confirmed" if tx.get("status") else "pending") if tx.get("status") is not None else None,
            fees_ada,
            Json(tx),  # adapt dict -> JSON for JSONB column
        ),
    )


def _insert_io_rows(cur, wallet_id: int, bech32_address: str, api: CardanoScanAPI, tx: Dict, symbols_accum: Optional[set] = None):
    """Insert per-IO rows for the specific wallet address.

    Only records rows where the IO address equals the tracked wallet address.
    """
    tx_hash = tx.get("hash")
    # compare addresses in hex
    try:
        wallet_hex = api._convert_to_hex(bech32_address).lower()
    except Exception:
        wallet_hex = bech32_address.lower()

    # Clean previous IO rows for idempotency
    cur.execute("DELETE FROM t_cardano_tx_io WHERE tx_hash = %s AND wallet_id = %s", (tx_hash, wallet_id))

    def _handle_side(side_list: List[Dict], io_type: str):
        if not isinstance(side_list, list):
            return
        for it in side_list:
            addr = (it.get("address") or "").lower()
            if addr != wallet_hex:
                continue
            # ADA lovelace
            lovelace = None
            try:
                lovelace = int(it.get("value", 0))
            except Exception:
                lovelace = None

            # Insert one row for ADA if present
            if lovelace is not None:
                cur.execute(
                    """
                    INSERT INTO t_cardano_tx_io (tx_hash, wallet_id, io_type, address, lovelace)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (tx_hash, wallet_id, io_type, bech32_address, lovelace),
                )
                if symbols_accum is not None and lovelace != 0:
                    symbols_accum.add("ADA")

            # Tokens (optional)
            tokens = it.get("tokens", [])
            if isinstance(tokens, list):
                for tk in tokens:
                    policy_id = tk.get("policyId") or tk.get("policy")
                    # Some APIs may omit assetName; use empty string for key consistency
                    asset_name_hex = (tk.get("assetName") or tk.get("name") or "")
                    raw_val = tk.get("value", tk.get("quantity", tk.get("amount", 0)))
                    try:
                        raw_val_int = int(raw_val)
                    except Exception:
                        raw_val_int = 0

                    # Resolve display name and decimals for formatted amount
                    display_name = api.get_token_name({
                        "policyId": policy_id,
                        "assetName": asset_name_hex,
                    })
                    decimals = api._resolve_decimals(policy_id, display_name, asset_name_hex)
                    formatted = (raw_val_int / (10 ** decimals)) if decimals and decimals > 0 else float(raw_val_int)

                    # Upsert token metadata
                    _upsert_cardano_asset(cur, policy_id, asset_name_hex, display_name, decimals)

                    # Insert IO row per token
                    cur.execute(
                        """
                        INSERT INTO t_cardano_tx_io (
                            tx_hash, wallet_id, io_type, address, policy_id, asset_name_hex, token_value_raw, token_amount
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            tx_hash,
                            wallet_id,
                            io_type,
                            bech32_address,
                            policy_id,
                            asset_name_hex,
                            raw_val_int,
                            formatted,
                        ),
                    )
                    if symbols_accum is not None and display_name:
                        symbols_accum.add(str(display_name).upper())

    _handle_side(tx.get("inputs", []), "input")
    _handle_side(tx.get("outputs", []), "output")


def sync_wallet_transactions(wallet_id: int, bech32_address: str, max_pages: int = 5) -> Tuple[int, int]:
    """Sync most recent transactions for a given Cardano wallet.

    Returns: (num_tx_processed, num_io_rows)
    """
    api = _get_api_client()
    if not api:
        raise RuntimeError("Nenhuma API Cardano ativa configurada.")

    transactions, error = api.get_transactions(bech32_address, max_pages=max_pages)
    if error:
        raise RuntimeError(f"Erro ao buscar transações: {error}")

    if not transactions:
        return (0, 0)

    conn = get_connection()
    try:
        cur = conn.cursor()
        # Ensure schema (migration) exists
        cur.execute(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema='public' AND table_name IN (
                't_cardano_transactions','t_cardano_tx_io','t_cardano_assets','t_cardano_sync_state'
            )
            """
        )
        cnt = cur.fetchone()[0] or 0
        if cnt < 4:
            raise RuntimeError(
                "Esquema Cardano v3 em falta. Aplique a migration database/migrations/20251103_cardano_tx_v3.sql."
            )
        total_io = 0
        symbols_seen: set = set()
        min_tx_date = None
        max_tx_date = None
        for tx in transactions:
            _insert_transaction(cur, wallet_id, bech32_address, tx)
            _insert_io_rows(cur, wallet_id, bech32_address, api, tx, symbols_accum=symbols_seen)
            # Track tx date range
            ts = tx.get("timestamp")
            tx_dt = None
            if isinstance(ts, str):
                try:
                    if "T" in ts:
                        tx_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    else:
                        tx_dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                except Exception:
                    tx_dt = None
            elif isinstance(ts, (int, float)):
                tx_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            if tx_dt is not None:
                d = tx_dt.date()
                if min_tx_date is None or d < min_tx_date:
                    min_tx_date = d
                if max_tx_date is None or d > max_tx_date:
                    max_tx_date = d
            # count IO rows inserted for this tx (rough estimate via rowcount not reliable as multiple inserts)
            # We'll recompute at the end.

        # Update sync state
        last_tx = transactions[0]  # transactions are sorted recent-first in our client
        ts = last_tx.get("timestamp")
        if isinstance(ts, str):
            try:
                if "T" in ts:
                    last_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                else:
                    last_dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            except Exception:
                last_dt = None
        else:
            try:
                last_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                last_dt = None

        cur.execute(
            """
            INSERT INTO t_cardano_sync_state (wallet_id, last_block_height, last_tx_timestamp, last_synced_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (wallet_id)
            DO UPDATE SET last_block_height = EXCLUDED.last_block_height,
                          last_tx_timestamp = EXCLUDED.last_tx_timestamp,
                          last_synced_at = CURRENT_TIMESTAMP
            """,
            (
                wallet_id,
                last_tx.get("block_height") or last_tx.get("blockHeight"),
                last_dt,
            ),
        )

        # Compute IO rows count
        cur.execute("SELECT COUNT(*) FROM t_cardano_tx_io WHERE wallet_id = %s", (wallet_id,))
        total_io = cur.fetchone()[0] or 0
        conn.commit()
        # After commit, trigger snapshot filling in background to avoid blocking UI
        try:
            if symbols_seen and min_tx_date and max_tx_date:
                logger.info(
                    f"📊 Sync concluído: {len(symbols_seen)} símbolos detectados, datas TX: {min_tx_date} até {max_tx_date}"
                )
                started = start_ensure_assets_and_snapshots_async(sorted(symbols_seen), min_tx_date, max_tx_date)
                if started:
                    logger.info(
                        f"🧵 Snapshots de preços iniciados em background para {len(symbols_seen)} símbolos ({min_tx_date}..{max_tx_date})"
                    )
                else:
                    logger.info(
                        f"📊 Snapshots não iniciados em background; tentando inline para {len(symbols_seen)} símbolos"
                    )
                    ensure_assets_and_snapshots(sorted(symbols_seen), min_tx_date, max_tx_date)
        except Exception as e:
            # Don't fail sync if pricing prep fails
            logger.warning(f"⚠️ Sync Cardano concluído mas preços podem estar incompletos: {e}")
        return (len(transactions), int(total_io))
    except Exception:
        conn.rollback()
        raise
    finally:
        return_connection(conn)


def sync_all_cardano_wallets_for_user(user_id: Optional[int] = None, max_pages: int = 5, wallet_ids: Optional[List[int]] = None) -> Dict:
    """Sync active Cardano wallets.
    
    Args:
        user_id: Filter by user (optional)
        max_pages: Number of recent transaction pages to fetch
        wallet_ids: Optional list of specific wallet_ids to sync. If provided, only these wallets are synced.
    
    Returns:
        Dict with sync results: wallets count, synced count, io_rows, errors
    """
    wallets = get_active_wallets(user_id)
    wallets = [w for w in wallets if (w.get("blockchain") or "").lower() == "cardano"]
    
    # Filter by specific wallet_ids if provided
    if wallet_ids is not None:
        wallets = [w for w in wallets if int(w.get("wallet_id")) in wallet_ids]
        logger.info(f"🎯 Filtro aplicado: sincronizando apenas {len(wallets)} wallet(s) selecionada(s)")
    
    if not wallets:
        return {"wallets": 0, "synced": 0, "io_rows": 0}

    results = {"wallets": len(wallets), "synced": 0, "io_rows": 0, "errors": []}
    for w in wallets:
        wid = int(w["wallet_id"]) if w.get("wallet_id") is not None else None
        addr = w.get("address")
        if not wid or not addr:
            continue
        try:
            tx_count, io_total = sync_wallet_transactions(wid, addr, max_pages=max_pages)
            if tx_count >= 0:
                results["synced"] += 1
            results["io_rows"] += io_total
        except Exception as e:
            # Collect error details but continue
            results["errors"].append({
                "wallet_id": wid,
                "address": addr,
                "error": str(e),
            })
    return results
