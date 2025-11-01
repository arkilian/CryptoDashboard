"""Caching utilities for performance optimization."""
import functools
import time
import threading
from typing import Callable, Any, Optional


def ttl_cache(ttl_seconds: int = 60):
    """Thread-safe TTL cache decorator.
    
    Args:
        ttl_seconds: Time-to-live in seconds
        
    Usage:
        @ttl_cache(ttl_seconds=30)
        def expensive_function(arg1, arg2):
            return result
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}
        cache_lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key - use repr for consistent hashing
            # frozenset is more efficient for kwargs
            if kwargs:
                kwargs_key = frozenset(kwargs.items())
            else:
                kwargs_key = frozenset()
            key = (args, kwargs_key)
            
            current_time = time.time()
            
            # Thread-safe cache check
            with cache_lock:
                # Check if cached and not expired
                if key in cache and key in cache_time:
                    if current_time - cache_time[key] < ttl_seconds:
                        return cache[key]
            
            # Call function (outside lock to avoid blocking)
            result = func(*args, **kwargs)
            
            # Thread-safe cache update
            with cache_lock:
                cache[key] = result
                cache_time[key] = current_time
            
            return result
        
        # Add cache clearing function
        def clear_cache():
            with cache_lock:
                cache.clear()
                cache_time.clear()
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator


def session_cache(session_state, cache_key: str, ttl_seconds: Optional[int] = None):
    """Streamlit session state cache decorator.
    
    Args:
        session_state: Streamlit session_state object
        cache_key: Key to use in session_state
        ttl_seconds: Optional time-to-live in seconds
        
    Usage:
        @session_cache(st.session_state, "my_data", ttl_seconds=30)
        def get_data():
            return expensive_query()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_time_key = f"{cache_key}_time"
            current_time = time.time()
            
            # Check if cached
            if cache_key in session_state:
                # Check TTL if specified
                if ttl_seconds is not None:
                    if cache_time_key in session_state:
                        if current_time - session_state[cache_time_key] < ttl_seconds:
                            return session_state[cache_key]
                else:
                    # No TTL, cache is valid
                    return session_state[cache_key]
            
            # Call function and cache result
            result = func(*args, **kwargs)
            session_state[cache_key] = result
            if ttl_seconds is not None:
                session_state[cache_time_key] = current_time
            
            return result
        
        return wrapper
    
    return decorator
