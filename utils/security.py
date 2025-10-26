"""Segurança de passwords.

Substituí o esquema caseiro (SHA-256 + salt) por bcrypt, que é
projetado especificamente para armazenar passwords de forma segura.

Contractos:
- hash_password(password) -> (hash_str, salt_str)
  (retorna salt vazio porque o bcrypt embute o salt no hash)
- verify_password(password, stored_hash, salt='') -> bool
"""
import bcrypt


def hash_password(password: str) -> (str, str):
    """Gera um hash bcrypt para a password.

    Retorna (hash, salt). O salt é deixado vazio porque o bcrypt
    inclui o salt no próprio hash (formato `$2b$...`).
    """
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8'), ""


def verify_password(password: str, stored_hash: str, salt: str = "") -> bool:
    """Verifica se a password corresponde ao hash armazenado.

    Aceita o parâmetro `salt` por compatibilidade com o esquema anterior,
    mas ignora-o porque o bcrypt embute o salt no hash.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception:
        return False
