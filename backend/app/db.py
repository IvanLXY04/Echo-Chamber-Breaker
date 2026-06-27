import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'chats.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            a2ui_payload TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def create_chat(email: str, name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO chats (email, name, created_at) VALUES (?, ?, ?)', (email, name, created_at))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chat_id

def get_chats_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, created_at FROM chats WHERE email = ? ORDER BY created_at DESC', (email,))
    chats = [{"id": row[0], "name": row[1], "created_at": row[2]} for row in cursor.fetchall()]
    conn.close()
    return chats

def update_chat_name(chat_id: int, new_name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE chats SET name = ? WHERE id = ?', (new_name, chat_id))
    conn.commit()
    conn.close()

def add_message(chat_id: int, sender: str, text: str, a2ui_payload: dict = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    payload_str = json.dumps(a2ui_payload) if a2ui_payload else None
    cursor.execute('INSERT INTO messages (chat_id, sender, text, a2ui_payload, timestamp) VALUES (?, ?, ?, ?, ?)',
                   (chat_id, sender, text, payload_str, timestamp))
    conn.commit()
    conn.close()

def get_messages(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT sender, text, a2ui_payload, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC', (chat_id,))
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "sender": row[0],
            "text": row[1],
            "a2ui_payload": json.loads(row[2]) if row[2] else None,
            "timestamp": row[3]
        })
    conn.close()
    return messages

def delete_chat(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()
