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
            created_at TEXT NOT NULL,
            persona TEXT DEFAULT 'Socratic',
            difficulty TEXT DEFAULT 'Normal',
            format TEXT DEFAULT 'Free Debate',
            mode TEXT DEFAULT 'solo'
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_participants (
            chat_id INTEGER,
            email TEXT,
            joined_at TEXT,
            PRIMARY KEY (chat_id, email),
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        )
    ''')
    
    # Handle schema migration for existing databases
    try:
        cursor.execute("ALTER TABLE chats ADD COLUMN persona TEXT DEFAULT 'Socratic'")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE chats ADD COLUMN difficulty TEXT DEFAULT 'Normal'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE chats ADD COLUMN format TEXT DEFAULT 'Free Debate'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE chats ADD COLUMN mode TEXT DEFAULT 'solo'")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

def create_chat(email: str, name: str, persona: str = "Socratic", difficulty: str = "Normal", format: str = "Free Debate", mode: str = "solo"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO chats (email, name, created_at, persona, difficulty, format, mode) VALUES (?, ?, ?, ?, ?, ?, ?)', (email, name, created_at, persona, difficulty, format, mode))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chat_id

def get_chats_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT c.id, c.name, c.created_at, c.persona, c.difficulty, c.format, c.mode 
        FROM chats c
        LEFT JOIN chat_participants cp ON c.id = cp.chat_id
        WHERE c.email = ? OR cp.email = ?
        ORDER BY c.created_at DESC
    ''', (email, email))
    chats = [{"id": row[0], "name": row[1], "created_at": row[2], "persona": row[3], "difficulty": row[4], "format": row[5], "mode": row[6]} for row in cursor.fetchall()]
    conn.close()
    return chats

def join_chat(chat_id: int, email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    joined_at = datetime.utcnow().isoformat()
    try:
        cursor.execute('INSERT OR IGNORE INTO chat_participants (chat_id, email, joined_at) VALUES (?, ?, ?)', (chat_id, email, joined_at))
        conn.commit()
    except sqlite3.Error:
        pass
    conn.close()

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
