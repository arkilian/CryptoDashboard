"""
Performance tests for optimized code.

These tests validate that the performance optimizations maintain correctness
while improving efficiency.
"""
import unittest
from unittest.mock import patch, MagicMock
import time
from datetime import date


class TestConnectionPooling(unittest.TestCase):
    """Test connection pooling functionality."""
    
    @patch('database.connection.psycopg2.pool.SimpleConnectionPool')
    def test_connection_pool_created_once(self, mock_pool_class):
        """Test that connection pool is created only once."""
        from database.connection import _get_pool, get_connection
        
        # Reset global pool
        import database.connection as conn_module
        conn_module._connection_pool = None
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        # Call multiple times
        pool1 = _get_pool()
        pool2 = _get_pool()
        
        # Pool should be created only once
        mock_pool_class.assert_called_once()
        self.assertIs(pool1, pool2)
    
    @patch('database.connection.psycopg2.pool.SimpleConnectionPool')
    def test_get_connection_uses_pool(self, mock_pool_class):
        """Test that get_connection uses the pool."""
        from database.connection import get_connection
        
        # Reset global pool
        import database.connection as conn_module
        conn_module._connection_pool = None
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = MagicMock()
        
        conn = get_connection()
        
        # Should call getconn on pool
        mock_pool.getconn.assert_called_once()
    
    @patch('database.connection.psycopg2.pool.SimpleConnectionPool')
    def test_context_manager_commits_on_success(self, mock_pool_class):
        """Test that context manager commits on success."""
        from database.connection import get_db_cursor
        
        # Reset global pool
        import database.connection as conn_module
        conn_module._connection_pool = None
        
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with get_db_cursor() as cur:
            self.assertIs(cur, mock_cursor)
        
        # Should commit and return connection
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)
    
    @patch('database.connection.psycopg2.pool.SimpleConnectionPool')
    def test_context_manager_rollsback_on_error(self, mock_pool_class):
        """Test that context manager rolls back on error."""
        from database.connection import get_db_cursor
        
        # Reset global pool
        import database.connection as conn_module
        conn_module._connection_pool = None
        
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        try:
            with get_db_cursor() as cur:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Should rollback and return connection
        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_pool.putconn.assert_called_once_with(mock_conn)


class TestCoinGeckoCaching(unittest.TestCase):
    """Test CoinGecko API caching improvements."""
    
    def setUp(self):
        """Reset caches before each test."""
        import services.coingecko as cg
        cg._coin_list_cache = None
        cg._symbol_to_id_cache = {k.upper(): v for k, v in cg.COMMON_SYMBOL_MAP.items()}
    
    @patch('services.coingecko.requests.get')
    def test_coin_list_cache_with_ttl(self, mock_get):
        """Test that coin list cache respects TTL."""
        from services.coingecko import _get_coin_list
        import services.coingecko as cg
        
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "bitcoin", "symbol": "btc"}]
        mock_get.return_value = mock_response
        
        # First call should fetch from API
        result1 = _get_coin_list()
        self.assertEqual(len(result1), 1)
        self.assertEqual(mock_get.call_count, 1)
        
        # Second call within TTL should use cache
        result2 = _get_coin_list()
        self.assertEqual(mock_get.call_count, 1)  # No additional call
        self.assertEqual(result1, result2)
    
    @patch('services.coingecko.requests.get')
    @patch('services.coingecko.time.time')
    def test_coin_list_cache_expires(self, mock_time, mock_get):
        """Test that coin list cache expires after TTL."""
        from services.coingecko import _get_coin_list
        import services.coingecko as cg
        
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "bitcoin", "symbol": "btc"}]
        mock_get.return_value = mock_response
        
        # First call at time 0
        mock_time.return_value = 0
        result1 = _get_coin_list()
        self.assertEqual(mock_get.call_count, 1)
        
        # Second call after TTL should fetch again
        mock_time.return_value = cg._coin_list_cache_ttl + 1
        result2 = _get_coin_list()
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('services.coingecko.requests.get')
    @patch('services.coingecko.time.time')
    def test_price_cache_in_service(self, mock_time, mock_get):
        """Test that CoinGeckoService caches prices correctly."""
        from services.coingecko import CoinGeckoService
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "bitcoin": {"eur": 50000.0}
        }
        mock_get.return_value = mock_response
        
        service = CoinGeckoService()
        
        # First call at time 0
        mock_time.return_value = 0
        result1 = service.get_prices(["BTC"], ["eur"])
        call_count_1 = mock_get.call_count
        
        # Second call within TTL should use cache
        mock_time.return_value = 15  # Within 30 second TTL
        result2 = service.get_prices(["BTC"], ["eur"])
        self.assertEqual(mock_get.call_count, call_count_1)  # No additional calls
        self.assertEqual(result1, result2)
        
        # Third call after TTL should fetch again
        mock_time.return_value = 35  # After 30 second TTL
        result3 = service.get_prices(["BTC"], ["eur"])
        self.assertGreater(mock_get.call_count, call_count_1)


class TestSnapshotServiceOptimizations(unittest.TestCase):
    """Test SnapshotService optimizations."""
    
    @patch('services.snapshot.get_db_cursor')
    def test_create_snapshot_uses_context_manager(self, mock_cursor_context):
        """Test that create_snapshot uses context manager."""
        from services.snapshot import SnapshotService
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [123]
        mock_cursor_context.return_value.__enter__.return_value = mock_cursor
        
        service = SnapshotService()
        snapshot_id = service.create_manual_snapshot(
            user_id=1,
            snapshot_date=date.today(),
            binance_value=1000.0,
            ledger_value=2000.0,
            defi_value=3000.0,
            other_value=500.0
        )
        
        # Should use context manager
        mock_cursor_context.assert_called_once()
        self.assertEqual(snapshot_id, 123)
    
    @patch('services.snapshot.get_connection')
    @patch('services.snapshot.return_connection')
    def test_get_latest_snapshot_returns_connection(self, mock_return, mock_get):
        """Test that get_latest_snapshot returns connection to pool."""
        from services.snapshot import SnapshotService
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get.return_value = mock_conn
        
        service = SnapshotService()
        result = service.get_latest_snapshot(1)
        
        # Should return connection to pool
        mock_return.assert_called_once_with(mock_conn)
        self.assertIsNone(result)


class TestBulkOperations(unittest.TestCase):
    """Test bulk operation optimizations."""
    
    @patch('database.portfolio.get_db_cursor')
    @patch('database.portfolio.apply_fees')
    def test_bulk_insert_assets(self, mock_apply_fees, mock_cursor_context):
        """Test that assets are inserted using executemany."""
        from database.portfolio import insert_snapshot_and_fees
        import pandas as pd
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            [1],  # snapshot_id
        ]
        mock_cursor.fetchall.return_value = [
            (2, 1000.0),  # user_id, valor_antes
        ]
        mock_cursor_context.return_value.__enter__.return_value = mock_cursor
        mock_apply_fees.return_value = (950.0, 30.0, 20.0)
        
        df_assets = pd.DataFrame({
            'asset_symbol': ['BTC', 'ETH'],
            'quantity': [1.0, 10.0],
            'price': [50000.0, 3000.0],
            'valor_total': [50000.0, 30000.0]
        })
        
        insert_snapshot_and_fees(1, date.today(), df_assets)
        
        # Check that executemany was called for bulk insert
        executemany_called = any(
            'executemany' in str(call)
            for call in mock_cursor.method_calls
        )
        self.assertTrue(executemany_called, "executemany should be used for bulk inserts")
    
    @patch('database.portfolio.get_db_cursor')
    @patch('database.portfolio.apply_fees')
    def test_optimized_user_query(self, mock_apply_fees, mock_cursor_context):
        """Test that users and their last snapshots are fetched in one query."""
        from database.portfolio import insert_snapshot_and_fees
        import pandas as pd
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            [1],  # snapshot_id
        ]
        mock_cursor.fetchall.return_value = [
            (2, 1000.0),  # user_id, valor_antes
            (3, 2000.0),
        ]
        mock_cursor_context.return_value.__enter__.return_value = mock_cursor
        mock_apply_fees.return_value = (950.0, 30.0, 20.0)
        
        df_assets = pd.DataFrame({
            'asset_symbol': ['BTC'],
            'quantity': [1.0],
            'price': [50000.0],
            'valor_total': [50000.0]
        })
        
        insert_snapshot_and_fees(1, date.today(), df_assets)
        
        # Check that execute was called with SQL containing COALESCE (optimized query)
        execute_calls = [
            call for call in mock_cursor.method_calls 
            if call[0] == 'execute' and len(call[1]) > 0
        ]
        
        # Look for the optimized user query with COALESCE
        optimized_query_found = any(
            'COALESCE' in str(call[1][0])
            for call in execute_calls
        )
        
        self.assertTrue(optimized_query_found, 
                       "Optimized user query with COALESCE should be used")


if __name__ == '__main__':
    unittest.main()
