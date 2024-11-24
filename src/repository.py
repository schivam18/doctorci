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

    # Create Abstracts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Abstracts (
        abstract_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        abstract_text TEXT NOT NULL
    )
    ''')

    # Create Drugs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Drugs (
        drug_id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_name TEXT NOT NULL UNIQUE
    )
    ''')

    # Create Diseases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Diseases (
        disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_name TEXT NOT NULL UNIQUE
    )
    ''')

    # Create Attributes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Attributes (
        attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
        attribute_name TEXT NOT NULL UNIQUE
    )
    ''')

    # Create DrugAttributes table (junction table for drugs and attributes)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DrugAttributes (
        drug_attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_id INTEGER NOT NULL,
        attribute_id INTEGER NOT NULL,
        abstract_id INTEGER NOT NULL,
        attribute_value TEXT,
        attribute_units TEXT,
        FOREIGN KEY (drug_id) REFERENCES Drugs (drug_id),
        FOREIGN KEY (attribute_id) REFERENCES Attributes (attribute_id),
        FOREIGN KEY (abstract_id) REFERENCES Abstracts (abstract_id)
    )
    ''')

    # Create DrugDiseases table (junction table for drugs and diseases)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS DrugDiseases (
        drug_id INTEGER NOT NULL,
        disease_id INTEGER NOT NULL,
        PRIMARY KEY (drug_id, disease_id),
        FOREIGN KEY (drug_id) REFERENCES Drugs (drug_id),
        FOREIGN KEY (disease_id) REFERENCES Diseases (disease_id)
    )
    ''')

    # Create AbstractDrugs table (junction table for abstracts and drugs)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS AbstractDrugs (
        abstract_id INTEGER NOT NULL,
        drug_id INTEGER NOT NULL,
        PRIMARY KEY (abstract_id, drug_id),
        FOREIGN KEY (abstract_id) REFERENCES Abstracts (abstract_id),
        FOREIGN KEY (drug_id) REFERENCES Drugs (drug_id)
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
    abstract_id = cursor.lastrowid
    conn.close()
    return abstract_id


def insert_drug(drug_name):
    """Insert a drug into the Drugs table and return its drug_id."""
    conn = create_connection()
    cursor = conn.cursor()

    # Check if the drug already exists
    cursor.execute("SELECT drug_id FROM Drugs WHERE drug_name = ?", (drug_name,))
    result = cursor.fetchone()

    if result:
        drug_id = result[0]
    else:
        cursor.execute("INSERT INTO Drugs (drug_name) VALUES (?)", (drug_name,))
        conn.commit()
        drug_id = cursor.lastrowid

    conn.close()
    return drug_id


def insert_disease(disease_name):
    """Insert a disease into the Diseases table and return its disease_id."""
    conn = create_connection()
    cursor = conn.cursor()

    # Check if the disease already exists
    cursor.execute("SELECT disease_id FROM Diseases WHERE disease_name = ?", (disease_name,))
    result = cursor.fetchone()

    if result:
        disease_id = result[0]
    else:
        cursor.execute("INSERT INTO Diseases (disease_name) VALUES (?)", (disease_name,))
        conn.commit()
        disease_id = cursor.lastrowid

    conn.close()
    return disease_id


def link_drug_disease(drug_id, disease_id):
    """Link a drug to a disease in the DrugDiseases table."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO DrugDiseases (drug_id, disease_id)
    VALUES (?, ?)
    """, (drug_id, disease_id))

    conn.commit()
    conn.close()


def insert_attribute(attribute_name):
    """Insert an attribute into the Attributes table and return its attribute_id."""
    conn = create_connection()
    cursor = conn.cursor()

    # Check if the attribute already exists
    cursor.execute("SELECT attribute_id FROM Attributes WHERE attribute_name = ?", (attribute_name,))
    result = cursor.fetchone()

    if result:
        attribute_id = result[0]
    else:
        cursor.execute("INSERT INTO Attributes (attribute_name) VALUES (?)", (attribute_name,))
        conn.commit()
        attribute_id = cursor.lastrowid

    conn.close()
    return attribute_id


def insert_drug_attribute(drug_id, attribute_id, abstract_id, attribute_value, attribute_units=None):
    """Insert an attribute value for a drug into the DrugAttributes table."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO DrugAttributes (drug_id, attribute_id, abstract_id, attribute_value, attribute_units)
    VALUES (?, ?, ?, ?, ?)
    """, (drug_id, attribute_id, abstract_id, attribute_value, attribute_units))

    conn.commit()
    conn.close()


def link_abstract_drug(abstract_id, drug_id):
    """Link an abstract to a drug in the AbstractDrugs table."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO AbstractDrugs (abstract_id, drug_id)
    VALUES (?, ?)
    """, (abstract_id, drug_id))

    conn.commit()
    conn.close()


def get_abstract_by_id(abstract_id):
    """Retrieve an abstract from the Abstracts table by its abstract_id."""
    conn = create_connection()
    cursor = conn.cursor()

    # Execute a query to fetch the abstract with the given ID
    cursor.execute("""
    SELECT abstract_id, file_name, abstract_text
    FROM Abstracts
    WHERE abstract_id = ?
    """, (abstract_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        # Return the data as a dictionary
        abstract_data = {
            'abstract_id': result[0],
            'file_name': result[1],
            'abstract_text': result[2]
        }
        return abstract_data
    else:
        return None