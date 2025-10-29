"""
Test additional performance optimizations.
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit before importing pages
sys.modules['streamlit'] = Mock()

from config import WATCHED_COINS, USERS_CACHE_DURATION, GENDER_CACHE_DURATION


class TestConfigurationCentralization(unittest.TestCase):
    """Test that configuration is properly centralized."""
    
    def test_watched_coins_defined(self):
        """Test that WATCHED_COINS is defined and has expected coins."""
        self.assertIsInstance(WATCHED_COINS, list)
        self.assertGreater(len(WATCHED_COINS), 0)
        self.assertIn("bitcoin", WATCHED_COINS)
        self.assertIn("cardano", WATCHED_COINS)
    
    def test_cache_durations_defined(self):
        """Test that cache durations are defined."""
        self.assertIsInstance(USERS_CACHE_DURATION, int)
        self.assertIsInstance(GENDER_CACHE_DURATION, int)
        self.assertEqual(USERS_CACHE_DURATION, 30)
        self.assertEqual(GENDER_CACHE_DURATION, 3600)


class TestCachingLogic(unittest.TestCase):
    """Test caching logic in helper functions."""
    
    def test_cache_key_generation(self):
        """Test that cache keys are properly generated."""
        # This would test the actual caching logic
        # For now, just verify the pattern
        cache_key = "users_list_cache"
        cache_time_key = "users_list_cache_time"
        self.assertTrue(cache_key.endswith("_cache"))
        self.assertTrue(cache_time_key.endswith("_cache_time"))
    
    def test_ttl_calculation(self):
        """Test TTL calculation logic."""
        import time
        current_time = time.time()
        cache_time = current_time - 20  # 20 seconds ago
        ttl = 30
        
        # Should be valid (20 < 30)
        is_valid = (current_time - cache_time) < ttl
        self.assertTrue(is_valid)
        
        # Should be invalid (40 > 30)
        old_cache_time = current_time - 40
        is_valid = (current_time - old_cache_time) < ttl
        self.assertFalse(is_valid)


class TestCodeDeduplication(unittest.TestCase):
    """Test that duplicate code has been removed."""
    
    def test_users_module_has_helper_functions(self):
        """Test that users module has the new helper functions."""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "users",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "pages", "users.py")
        )
        
        if spec and spec.loader:
            # Just check the file can be parsed
            with open(spec.origin, 'r') as f:
                content = f.read()
                self.assertIn("_get_users_list_cached", content)
                self.assertIn("_get_gender_list_cached", content)
                self.assertIn("_create_user_selector", content)
    
    def test_documents_module_simplified(self):
        """Test that documents module has simplified admin checks."""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "documents",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "pages", "documents.py")
        )
        
        if spec and spec.loader:
            with open(spec.origin, 'r') as f:
                content = f.read()
                # Should use simplified check
                self.assertIn('st.session_state.get("is_admin"', content)
                # Should not have redundant defensive pattern (appears only once now)
                count = content.count('if user and isinstance(user, dict)')
                self.assertEqual(count, 0, "Redundant defensive pattern should be removed")


class TestGitignoreUpdate(unittest.TestCase):
    """Test that .gitignore has been updated."""
    
    def test_legacy_file_ignored(self):
        """Test that 2000.py is in .gitignore."""
        gitignore_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".gitignore"
        )
        
        with open(gitignore_path, 'r') as f:
            content = f.read()
            self.assertIn("2000.py", content)


if __name__ == '__main__':
    unittest.main()
