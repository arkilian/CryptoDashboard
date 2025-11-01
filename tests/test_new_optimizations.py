"""Tests for new performance optimizations."""
import unittest
import pandas as pd
from unittest.mock import Mock, patch


class TestVectorizedHoldings(unittest.TestCase):
    """Test the new vectorized holdings calculation."""
    
    def test_calculate_holdings_vectorized(self):
        """Test that vectorized holdings calculation works correctly."""
        # Import the function (need to mock streamlit first)
        import sys
        sys.modules['streamlit'] = Mock()
        sys.modules['plotly'] = Mock()
        sys.modules['plotly.express'] = Mock()
        sys.modules['plotly.graph_objects'] = Mock()
        
        from pages.portfolio_analysis import _calculate_holdings_vectorized
        
        # Create test data
        df_tx = pd.DataFrame({
            'symbol': ['BTC', 'BTC', 'ETH', 'BTC', 'ETH'],
            'quantity': [1.0, 0.5, 10.0, 0.3, 5.0],
            'transaction_type': ['buy', 'buy', 'buy', 'sell', 'sell']
        })
        
        holdings = _calculate_holdings_vectorized(df_tx)
        
        # BTC: 1.0 + 0.5 - 0.3 = 1.2
        # ETH: 10.0 - 5.0 = 5.0
        self.assertAlmostEqual(holdings['BTC'], 1.2, places=6)
        self.assertAlmostEqual(holdings['ETH'], 5.0, places=6)
    
    def test_calculate_holdings_empty_dataframe(self):
        """Test that empty dataframe returns empty dict."""
        import sys
        sys.modules['streamlit'] = Mock()
        sys.modules['plotly'] = Mock()
        sys.modules['plotly.express'] = Mock()
        sys.modules['plotly.graph_objects'] = Mock()
        
        from pages.portfolio_analysis import _calculate_holdings_vectorized
        
        df_tx = pd.DataFrame(columns=['symbol', 'quantity', 'transaction_type'])
        holdings = _calculate_holdings_vectorized(df_tx)
        
        self.assertEqual(holdings, {})
    
    def test_calculate_holdings_filters_zero_quantities(self):
        """Test that zero or negative holdings are filtered out."""
        import sys
        sys.modules['streamlit'] = Mock()
        sys.modules['plotly'] = Mock()
        sys.modules['plotly.express'] = Mock()
        sys.modules['plotly.graph_objects'] = Mock()
        
        from pages.portfolio_analysis import _calculate_holdings_vectorized
        
        # Create data where one asset ends up with 0 quantity
        df_tx = pd.DataFrame({
            'symbol': ['BTC', 'BTC', 'ETH'],
            'quantity': [1.0, 1.0, 2.0],
            'transaction_type': ['buy', 'sell', 'buy']
        })
        
        holdings = _calculate_holdings_vectorized(df_tx)
        
        # BTC should not be in result (1.0 - 1.0 = 0)
        self.assertNotIn('BTC', holdings)
        # ETH should be in result
        self.assertIn('ETH', holdings)
        self.assertAlmostEqual(holdings['ETH'], 2.0, places=6)


class TestCachingUtilities(unittest.TestCase):
    """Test the new caching utilities."""
    
    def test_ttl_cache_basic(self):
        """Test basic TTL cache functionality."""
        from utils.caching import ttl_cache
        
        call_count = [0]
        
        @ttl_cache(ttl_seconds=1)
        def expensive_func(x):
            call_count[0] += 1
            return x * 2
        
        # First call
        result1 = expensive_func(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count[0], 1)
        
        # Second call (should use cache)
        result2 = expensive_func(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count[0], 1)  # Not incremented
        
        # Different argument (should call function)
        result3 = expensive_func(10)
        self.assertEqual(result3, 20)
        self.assertEqual(call_count[0], 2)
    
    def test_ttl_cache_expiration(self):
        """Test that cache expires after TTL."""
        import time
        from utils.caching import ttl_cache
        
        call_count = [0]
        
        @ttl_cache(ttl_seconds=0.1)  # Very short TTL
        def expensive_func(x):
            call_count[0] += 1
            return x * 2
        
        # First call
        result1 = expensive_func(5)
        self.assertEqual(call_count[0], 1)
        
        # Wait for cache to expire
        time.sleep(0.15)
        
        # Should call function again
        result2 = expensive_func(5)
        self.assertEqual(call_count[0], 2)
    
    def test_ttl_cache_clear(self):
        """Test that cache can be cleared."""
        from utils.caching import ttl_cache
        
        call_count = [0]
        
        @ttl_cache(ttl_seconds=60)
        def expensive_func(x):
            call_count[0] += 1
            return x * 2
        
        # First call
        expensive_func(5)
        self.assertEqual(call_count[0], 1)
        
        # Clear cache
        expensive_func.clear_cache()
        
        # Should call function again
        expensive_func(5)
        self.assertEqual(call_count[0], 2)


class TestSnapshotsOptimizations(unittest.TestCase):
    """Test snapshots service optimizations."""
    
    @patch('services.snapshots.get_engine')
    @patch('services.snapshots.pd.read_sql')
    def test_bulk_prices_uses_efficient_conversion(self, mock_read_sql, mock_engine):
        """Test that bulk price fetching uses efficient pandas operations."""
        from services.snapshots import get_historical_prices_bulk
        from datetime import date
        
        # Mock the database response
        mock_df = pd.DataFrame({
            'asset_id': [1, 2, 3],
            'price_eur': [50000.0, 3000.0, 2.5]
        })
        mock_read_sql.return_value = mock_df
        mock_engine.return_value = Mock()
        
        result = get_historical_prices_bulk([1, 2, 3], date(2024, 1, 1))
        
        # Should return dictionary with correct values
        self.assertEqual(result[1], 50000.0)
        self.assertEqual(result[2], 3000.0)
        self.assertEqual(result[3], 2.5)
        
        # Verify read_sql was called
        mock_read_sql.assert_called_once()


if __name__ == '__main__':
    unittest.main()
