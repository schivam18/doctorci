import sqlite3
import os

# Path to your database file
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'doctorci.db')


def create_connection():
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    return conn


def create_tables():
    """Create tables in the database."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Abstracts (
        abstract_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        abstract_text TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()


def insert_abstract(file_name, abstract_text):
    """Insert a new abstract into the Abstracts table."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Abstracts (file_name, abstract_text)
    VALUES (?, ?)
    ''', (file_name, abstract_text))
    conn.commit()
    conn.close()
