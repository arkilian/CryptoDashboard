"""Utility helpers for tags (strategy classification) for transactions.

Provides:
- ensure_default_tags(engine)
- get_all_tags(engine) -> list[dict]
- build_tags_where_clause(selected_codes, tx_alias='t') -> str
- set_transaction_tags(engine, transaction_id, tag_codes)
"""
from typing import Iterable, List, Dict
from sqlalchemy import text

DEFAULT_TAGS = [
    ("staking", "Staking"),
    ("defi", "DeFi"),
]


def ensure_default_tags(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS t_tags (
                tag_id SERIAL PRIMARY KEY,
                tag_code TEXT UNIQUE NOT NULL,
                tag_label TEXT,
                active BOOLEAN DEFAULT TRUE
            );
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS t_transaction_tags (
                transaction_id INTEGER NOT NULL REFERENCES t_transactions(transaction_id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES t_tags(tag_id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(transaction_id, tag_id)
            );
            """
        ))
        for code, label in DEFAULT_TAGS:
            conn.execute(
                text(
                    "INSERT INTO t_tags (tag_code, tag_label) VALUES (:code, :label) "
                    "ON CONFLICT (tag_code) DO NOTHING"
                ),
                {"code": code, "label": label},
            )


def get_all_tags(engine) -> List[Dict[str, str]]:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT tag_code, COALESCE(tag_label, tag_code) AS label FROM t_tags WHERE active = TRUE ORDER BY tag_label"))
        return [{"code": r[0], "label": r[1]} for r in res.fetchall()]


def build_tags_where_clause(selected_codes: Iterable[str], tx_alias: str = "t") -> str:
    codes = [c for c in (selected_codes or []) if c]
    if not codes:
        return ""
    codes_list = ",".join([f"'{c}'" for c in codes])
    # EXISTS subquery on join table to filter transactions having any of the selected tags
    return (
        "EXISTS ("
        f"SELECT 1 FROM t_transaction_tags tt JOIN t_tags tg ON tt.tag_id = tg.tag_id "
        f"WHERE tt.transaction_id = {tx_alias}.transaction_id AND tg.tag_code IN ({codes_list})"
        ")"
    )


def set_transaction_tags(engine, transaction_id: int, tag_codes: Iterable[str]) -> None:
    codes = [c for c in (tag_codes or []) if c]
    if not codes:
        return
    with engine.begin() as conn:
        # Fetch tag_ids for codes
        res = conn.execute(
            text(
                "SELECT tag_id, tag_code FROM t_tags WHERE tag_code = ANY(:codes)"
            ),
            {"codes": codes},
        )
        tag_rows = res.fetchall()
        code_to_id = {row[1]: row[0] for row in tag_rows}
        for code in codes:
            tag_id = code_to_id.get(code)
            if tag_id:
                conn.execute(
                    text(
                        "INSERT INTO t_transaction_tags (transaction_id, tag_id) VALUES (:tx, :tag) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {"tx": int(transaction_id), "tag": int(tag_id)},
                )
