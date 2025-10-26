import hashlib
import os

def hash_password(password: str, salt: str = None) -> (str, str):
    """
    Retorna (hash, salt).
    Se n�o houver salt, gera um novo.
    """
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pwd_hash, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifica se a senha corresponde ao hash armazenado."""
    return hash_password(password, salt)[0] == stored_hash
