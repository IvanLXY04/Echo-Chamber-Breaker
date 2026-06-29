import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL')
if not DB_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it in a .env file.")

def get_db_connection():
    conn = psycopg2.connect(DB_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            a2ui_payload TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_participants (
            chat_id INTEGER,
            email TEXT,
            joined_at TEXT,
            PRIMARY KEY (chat_id, email),
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        )
    ''')
    
    # Handle schema migration for existing databases
    columns = [
        ("persona", "TEXT DEFAULT 'Socratic'"),
        ("difficulty", "TEXT DEFAULT 'Normal'"),
        ("format", "TEXT DEFAULT 'Free Debate'"),
        ("mode", "TEXT DEFAULT 'solo'")
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE chats ADD COLUMN {col_name} {col_type}")
        except psycopg2.Error:
            conn.rollback()
        else:
            conn.commit()

    conn.commit()
    conn.close()

init_db()

def create_chat(email: str, name: str, persona: str = "Socratic", difficulty: str = "Normal", format: str = "Free Debate", mode: str = "solo"):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cursor.execute('INSERT INTO chats (email, name, created_at, persona, difficulty, format, mode) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id', 
                   (email, name, created_at, persona, difficulty, format, mode))
    chat_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return chat_id

def get_chats_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('''
        SELECT DISTINCT c.id, c.name, c.created_at, c.persona, c.difficulty, c.format, c.mode 
        FROM chats c
        LEFT JOIN chat_participants cp ON c.id = cp.chat_id
        WHERE c.email = %s OR cp.email = %s
        ORDER BY c.created_at DESC
    ''', (email, email))
    chats = [{"id": row['id'], "name": row['name'], "created_at": row['created_at'], "persona": row['persona'], "difficulty": row['difficulty'], "format": row['format'], "mode": row['mode']} for row in cursor.fetchall()]
    conn.close()
    return chats

def join_chat(chat_id: int, email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    joined_at = datetime.utcnow().isoformat()
    try:
        cursor.execute('INSERT INTO chat_participants (chat_id, email, joined_at) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING', (chat_id, email, joined_at))
        conn.commit()
    except psycopg2.Error:
        conn.rollback()
    conn.close()

def update_chat_name(chat_id: int, new_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE chats SET name = %s WHERE id = %s', (new_name, chat_id))
    conn.commit()
    conn.close()

def add_message(chat_id: int, sender: str, text: str, a2ui_payload: dict = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    payload_str = json.dumps(a2ui_payload) if a2ui_payload else None
    cursor.execute('INSERT INTO messages (chat_id, sender, text, a2ui_payload, timestamp) VALUES (%s, %s, %s, %s, %s)',
                   (chat_id, sender, text, payload_str, timestamp))
    conn.commit()
    conn.close()

def get_messages(chat_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT sender, text, a2ui_payload, timestamp FROM messages WHERE chat_id = %s ORDER BY id ASC', (chat_id,))
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "sender": row['sender'],
            "text": row['text'],
            "a2ui_payload": json.loads(row['a2ui_payload']) if row['a2ui_payload'] else None,
            "timestamp": row['timestamp']
        })
    conn.close()
    return messages

def delete_chat(chat_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE chat_id = %s', (chat_id,))
    cursor.execute('DELETE FROM chats WHERE id = %s', (chat_id,))
    conn.commit()
    conn.close()
