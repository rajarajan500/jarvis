import sqlite3

DB_PATH = "hub/history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create a table for chat history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_recent_history(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    # Reverse so it's in chronological order for the AI
    return [{"role": r, "content": c} for r, c in reversed(rows)]