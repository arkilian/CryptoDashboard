from typing import Optional
from datetime import date
from database.connection import get_db_connection

class SnapshotService:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def create_manual_snapshot(
        self,
        user_id: int,
        snapshot_date: date,
        binance_value: float,
        ledger_value: float,
        defi_value: float,
        other_value: float
    ) -> int:
        """
        Create a new manual snapshot of user's assets across different wallets
        """
        total_value = binance_value + ledger_value + defi_value + other_value
        
        try:
            self.cursor.execute("""
                INSERT INTO t_user_manual_snapshots 
                (user_id, snapshot_date, binance_value, ledger_value, defi_value, other_value, total_value)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING snapshot_id
            """, (user_id, snapshot_date, binance_value, ledger_value, defi_value, other_value, total_value))
            
            snapshot_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return snapshot_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_user_snapshots(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None):
        """
        Get all snapshots for a user within the optional date range
        """
        query = """
            SELECT snapshot_date, binance_value, ledger_value, defi_value, other_value, total_value
            FROM t_user_manual_snapshots
            WHERE user_id = %s
        """
        params = [user_id]

        if start_date:
            query += " AND snapshot_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND snapshot_date <= %s"
            params.append(end_date)

        query += " ORDER BY snapshot_date DESC"
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_latest_snapshot(self, user_id: int) -> Optional[dict]:
        """
        Get the most recent snapshot for a user
        """
        self.cursor.execute("""
            SELECT snapshot_date, binance_value, ledger_value, defi_value, other_value, total_value
            FROM t_user_manual_snapshots
            WHERE user_id = %s
            ORDER BY snapshot_date DESC
            LIMIT 1
        """, (user_id,))
        
        result = self.cursor.fetchone()
        if result:
            return {
                'snapshot_date': result[0],
                'binance_value': result[1],
                'ledger_value': result[2],
                'defi_value': result[3],
                'other_value': result[4],
                'total_value': result[5]
            }
        return None

    def __del__(self):
        self.cursor.close()
        self.conn.close()