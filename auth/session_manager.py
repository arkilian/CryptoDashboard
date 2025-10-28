import functools
import streamlit as st
from typing import Callable, Any, Optional


def login_user(user: dict) -> None:
	"""Mark user as logged in in Streamlit session state.

	user should be a dict containing at least: user_id, user_name or username, is_admin (bool)
	"""
	st.session_state['user'] = user
	st.session_state['user_id'] = user.get('user_id')
	st.session_state['username'] = user.get('user_name') or user.get('username')
	st.session_state['is_admin'] = bool(user.get('is_admin', False))


def logout_user() -> None:
	"""Clear user session state."""
	keys = ['user', 'user_id', 'username', 'is_admin']
	for k in keys:
		if k in st.session_state:
			del st.session_state[k]


def get_current_user() -> Optional[dict]:
	"""Return the full user dict stored in session, or None."""
	return st.session_state.get('user')


def require_auth(func: Callable) -> Callable:
	"""Decorator for Streamlit page functions that require an authenticated user.

	If no user is logged in, redirects to the login page by setting
	`st.session_state['page'] = 'login'` and re-running the app.
	"""

	@functools.wraps(func)
	def wrapper(*args: Any, **kwargs: Any):
		# If user info exists in session_state, allow
		if st.session_state.get('user') or st.session_state.get('user_id'):
			return func(*args, **kwargs)

		# Otherwise, request login
		st.warning("🔐 Por favor inicie sessão para aceder a esta página.")
		# Try to redirect to login page if the app uses that convention
		try:
			st.session_state['page'] = 'login'
		except Exception:
			pass
		st.experimental_rerun()

	return wrapper


def require_role(role: str):
	"""Return a decorator that requires a boolean flag like `is_admin` in session_state."""

	def _decorator(func: Callable) -> Callable:
		@functools.wraps(func)
		def _wrapper(*args: Any, **kwargs: Any):
			if st.session_state.get(role):
				return func(*args, **kwargs)
			st.error("Acesso negado: permissões insuficientes.")
			st.stop()

		return _wrapper

	return _decorator

