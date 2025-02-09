from flask import g
import sqlite3
from config import Config

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('users.db')
        g.db.row_factory = sqlite3.Row  # 行データを辞書形式で取得
    return g.db

def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
