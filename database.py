import sqlite3
import hashlib
import os
import json
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('e2ee_users.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # User configurations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            user_id INTEGER PRIMARY KEY,
            chat_id TEXT,
            name_prefix TEXT,
            delay INTEGER DEFAULT 10,
            cookies TEXT,
            messages TEXT,
            automation_running BOOLEAN DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Admin E2EE threads table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admin_threads (
            user_id INTEGER PRIMARY KEY,
            thread_id TEXT,
            cookies TEXT,
            chat_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    """Create new user"""
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db_connection()
        
        conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        
        user_id = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()['id']
        
        # Create default config
        conn.execute(
            'INSERT INTO user_configs (user_id, chat_id, name_prefix, delay, cookies, messages) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, '', '[END TO END]', 10, '', 'Hello!\nHow are you?\nNice to meet you!')
        )
        
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def verify_user(username, password):
    """Verify user credentials"""
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db_connection()
        
        user = conn.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ? AND is_active = 1',
            (username, password_hash)
        ).fetchone()
        
        conn.close()
        return user['id'] if user else None
    except:
        return None

def get_user_config(user_id):
    """Get user configuration"""
    try:
        conn = get_db_connection()
        config = conn.execute(
            'SELECT chat_id, name_prefix, delay, cookies, messages FROM user_configs WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        
        conn.close()
        
        if config:
            return {
                'chat_id': config['chat_id'],
                'name_prefix': config['name_prefix'],
                'delay': config['delay'],
                'cookies': config['cookies'],
                'messages': config['messages']
            }
        return None
    except:
        return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    """Update user configuration"""
    try:
        conn = get_db_connection()
        
        conn.execute(
            '''UPDATE user_configs 
               SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE user_id = ?''',
            (chat_id, name_prefix, delay, cookies, messages, user_id)
        )
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def set_automation_running(user_id, running):
    """Set automation running status"""
    try:
        conn = get_db_connection()
        
        conn.execute(
            'UPDATE user_configs SET automation_running = ? WHERE user_id = ?',
            (1 if running else 0, user_id)
        )
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_automation_running(user_id):
    """Get automation running status"""
    try:
        conn = get_db_connection()
        
        result = conn.execute(
            'SELECT automation_running FROM user_configs WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        
        conn.close()
        return result['automation_running'] if result else False
    except:
        return False

def get_username(user_id):
    """Get username by user ID"""
    try:
        conn = get_db_connection()
        
        user = conn.execute(
            'SELECT username FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        
        conn.close()
        return user['username'] if user else None
    except:
        return None

def set_admin_e2ee_thread_id(user_id, thread_id, cookies, chat_type):
    """Set admin E2EE thread ID for user"""
    try:
        conn = get_db_connection()
        
        # Check if exists
        existing = conn.execute(
            'SELECT user_id FROM admin_threads WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        
        if existing:
            conn.execute(
                'UPDATE admin_threads SET thread_id = ?, cookies = ?, chat_type = ?, created_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                (thread_id, cookies, chat_type, user_id)
            )
        else:
            conn.execute(
                'INSERT INTO admin_threads (user_id, thread_id, cookies, chat_type) VALUES (?, ?, ?, ?)',
                (user_id, thread_id, cookies, chat_type)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error setting admin thread: {e}")
        return False

def get_admin_e2ee_thread_id(user_id):
    """Get admin E2EE thread ID for user"""
    try:
        conn = get_db_connection()
        
        result = conn.execute(
            'SELECT thread_id FROM admin_threads WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        
        conn.close()
        return result['thread_id'] if result else None
    except:
        return None

# Initialize database when module is imported
init_db()
