# Auth and Session Management

Resumo do sistema de autenticação e sessões.

- `auth/login.py` e `auth/register.py` — páginas Streamlit para login e registo.
- `auth/session_manager.py` — helpers/decorators para proteger páginas e gerir sessão.
- Passwords são guardadas com hash + salt (ver `utils/security.py`).
- `st.session_state` armazena `user_id`, `username`, `is_admin`.

Sessão persistente

- Existe lógica para persistir/restore de sessão via token (ver implementações em `auth/session_manager.py`).

Recomendações de segurança

- Usar HttpOnly cookies para tokens quando integrar com backend (Flask) — não armazenar tokens sensíveis no `st.session_state` em produção.
- Trocar `SECRET_KEY` por um valor forte em produção (ver `.env`).
