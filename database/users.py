from .connection import get_connection
from utils.security import hash_password, verify_password
import psycopg2
from psycopg2 import sql

def create_user(username: str, password: str, is_admin: bool = False):
    conn = get_connection()
    cur = conn.cursor()

    pwd_hash, salt = hash_password(password)
    try:
        cur.execute("""
            INSERT INTO t_users (username, password_hash, salt, is_admin)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id
        """, (username, pwd_hash, salt, is_admin))
        user_id = cur.fetchone()[0]
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        raise

    conn.commit()
    cur.close()
    conn.close()
    return user_id

def get_user_by_username(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, password_hash, salt, is_admin FROM t_users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if user and verify_password(password, user[2], user[3]):
        return {"user_id": user[0], "username": user[1], "is_admin": user[4]}
    return None
