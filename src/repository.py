import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Path to your database file
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "doctorci.db")


def create_connection() -> sqlite3.Connection:
    """
    Create a database connection to the SQLite database.

    Returns:
        sqlite3.Connection: Database connection object

    Raises:
        sqlite3.Error: If connection fails
    """
    try:
        # Ensure database directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise


def create_tables() -> None:
    """
    Create all necessary tables in the database if they don't exist.

    Raises:
        sqlite3.Error: If table creation fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Create Abstracts table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Abstracts (
            abstract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            abstract_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Create Drugs table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Drugs (
            drug_id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Create Diseases table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Diseases (
            disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Create Attributes table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Attributes (
            attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
            attribute_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Create DrugAttributes table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS DrugAttributes (
            drug_attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_id INTEGER NOT NULL,
            attribute_id INTEGER NOT NULL,
            abstract_id INTEGER NOT NULL,
            attribute_value TEXT,
            attribute_units TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (drug_id) REFERENCES Drugs (drug_id),
            FOREIGN KEY (attribute_id) REFERENCES Attributes (attribute_id),
            FOREIGN KEY (abstract_id) REFERENCES Abstracts (abstract_id)
        )
        """
        )

        # Create DrugDiseases table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS DrugDiseases (
            drug_id INTEGER NOT NULL,
            disease_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (drug_id, disease_id),
            FOREIGN KEY (drug_id) REFERENCES Drugs (drug_id),
            FOREIGN KEY (disease_id) REFERENCES Diseases (disease_id)
        )
        """
        )

        # Create AbstractDrugs table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS AbstractDrugs (
            abstract_id INTEGER NOT NULL,
            drug_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (abstract_id, drug_id),
            FOREIGN KEY (abstract_id) REFERENCES Abstracts (abstract_id),
            FOREIGN KEY (drug_id) REFERENCES Drugs (drug_id)
        )
        """
        )

        conn.commit()
        logger.info("Database tables created successfully")
    except sqlite3.Error as e:
        logger.error(f"Error creating tables: {e}")
        raise
    finally:
        conn.close()


def insert_abstract(file_name: str, abstract_text: str) -> int:
    """
    Insert a new abstract into the Abstracts table.

    Parameters:
        file_name (str): Name of the PDF file
        abstract_text (str): Text content of the abstract

    Returns:
        int: ID of the inserted abstract

    Raises:
        sqlite3.Error: If insertion fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT INTO Abstracts (file_name, abstract_text)
        VALUES (?, ?)
        """,
            (file_name, abstract_text),
        )

        abstract_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Inserted abstract for file: {file_name}")
        return abstract_id
    except sqlite3.Error as e:
        logger.error(f"Error inserting abstract: {e}")
        raise
    finally:
        conn.close()


def insert_drug(drug_name: str) -> int:
    """
    Insert a drug into the Drugs table and return its ID.

    Parameters:
        drug_name (str): Name of the drug

    Returns:
        int: ID of the drug

    Raises:
        sqlite3.Error: If insertion fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Check if drug exists
        cursor.execute("SELECT drug_id FROM Drugs WHERE drug_name = ?", (drug_name,))
        result = cursor.fetchone()

        if result:
            drug_id = result[0]
            logger.debug(f"Drug '{drug_name}' already exists with ID: {drug_id}")
        else:
            cursor.execute("INSERT INTO Drugs (drug_name) VALUES (?)", (drug_name,))
            drug_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Inserted new drug: {drug_name}")

        return drug_id
    except sqlite3.Error as e:
        logger.error(f"Error inserting drug: {e}")
        raise
    finally:
        conn.close()


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

    cursor.execute(
        """
    INSERT OR IGNORE INTO DrugDiseases (drug_id, disease_id)
    VALUES (?, ?)
    """,
        (drug_id, disease_id),
    )

    conn.commit()
    conn.close()


def insert_attribute(attribute_name: str) -> int:
    """
    Insert an attribute into the Attributes table and return its ID.

    Parameters:
        attribute_name (str): Name of the attribute

    Returns:
        int: ID of the attribute

    Raises:
        sqlite3.Error: If insertion fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Check if attribute exists
        cursor.execute("SELECT attribute_id FROM Attributes WHERE attribute_name = ?", (attribute_name,))
        result = cursor.fetchone()

        if result:
            attribute_id = result[0]
            logger.debug(f"Attribute '{attribute_name}' already exists with ID: {attribute_id}")
        else:
            cursor.execute("INSERT INTO Attributes (attribute_name) VALUES (?)", (attribute_name,))
            attribute_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Inserted new attribute: {attribute_name}")

        return attribute_id
    except sqlite3.Error as e:
        logger.error(f"Error inserting attribute: {e}")
        raise
    finally:
        conn.close()


def insert_drug_attribute(
    drug_id: int, attribute_id: int, abstract_id: int, attribute_value: str, attribute_units: Optional[str] = None
) -> None:
    """
    Insert a drug attribute into the DrugAttributes table.

    Parameters:
        drug_id (int): ID of the drug
        attribute_id (int): ID of the attribute
        abstract_id (int): ID of the abstract
        attribute_value (str): Value of the attribute
        attribute_units (Optional[str]): Units of the attribute value

    Raises:
        sqlite3.Error: If insertion fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT INTO DrugAttributes (drug_id, attribute_id, abstract_id, attribute_value, attribute_units)
        VALUES (?, ?, ?, ?, ?)
        """,
            (drug_id, attribute_id, abstract_id, attribute_value, attribute_units),
        )

        conn.commit()
        logger.debug(f"Inserted drug attribute for drug_id: {drug_id}, attribute_id: {attribute_id}")
    except sqlite3.Error as e:
        logger.error(f"Error inserting drug attribute: {e}")
        raise
    finally:
        conn.close()


def link_abstract_drug(abstract_id: int, drug_id: int) -> None:
    """
    Link an abstract to a drug in the AbstractDrugs table.

    Parameters:
        abstract_id (int): ID of the abstract
        drug_id (int): ID of the drug

    Raises:
        sqlite3.Error: If linking fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT OR IGNORE INTO AbstractDrugs (abstract_id, drug_id)
        VALUES (?, ?)
        """,
            (abstract_id, drug_id),
        )

        conn.commit()
        logger.debug(f"Linked abstract {abstract_id} to drug {drug_id}")
    except sqlite3.Error as e:
        logger.error(f"Error linking abstract to drug: {e}")
        raise
    finally:
        conn.close()


def get_abstract_by_id(abstract_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve an abstract from the Abstracts table by its ID.

    Parameters:
        abstract_id (int): ID of the abstract to retrieve

    Returns:
        Optional[Dict[str, Any]]: Abstract data if found, None otherwise

    Raises:
        sqlite3.Error: If retrieval fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
        SELECT abstract_id, file_name, abstract_text, created_at
        FROM Abstracts
        WHERE abstract_id = ?
        """,
            (abstract_id,),
        )

        result = cursor.fetchone()

        if result:
            abstract_data = {
                "abstract_id": result[0],
                "file_name": result[1],
                "abstract_text": result[2],
                "created_at": result[3],
            }
            logger.debug(f"Retrieved abstract {abstract_id}")
            return abstract_data
        else:
            logger.warning(f"No abstract found with ID: {abstract_id}")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving abstract: {e}")
        raise
    finally:
        conn.close()


def clear_all_tables() -> None:
    """
    Clear all data from all tables in the database.

    Raises:
        sqlite3.Error: If clearing tables fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Clear each table
        for table in tables:
            table_name = table[0]
            if table_name != "sqlite_sequence":  # Skip sqlite_sequence table
                cursor.execute(f"DELETE FROM {table_name};")
                logger.info(f"Cleared table: {table_name}")

        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence;")

        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")

        conn.commit()
        logger.info("All tables cleared successfully")
    except sqlite3.Error as e:
        logger.error(f"Error clearing tables: {e}")
        raise
    finally:
        conn.close()


def recreate_tables() -> None:
    """
    Drop and recreate all tables in the database.

    Raises:
        sqlite3.Error: If table recreation fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Drop each table
        for table in tables:
            table_name = table[0]
            if table_name != "sqlite_sequence":  # Skip sqlite_sequence table
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                logger.info(f"Dropped table: {table_name}")

        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")

        conn.commit()
        logger.info("All tables dropped successfully")

        # Create tables with new schema
        create_tables()

    except sqlite3.Error as e:
        logger.error(f"Error recreating tables: {e}")
        raise
    finally:
        conn.close()


def get_all_abstracts() -> List[Dict[str, Any]]:
    """
    Retrieve all abstracts from the Abstracts table.

    Returns:
        List[Dict[str, Any]]: List of abstract data dictionaries

    Raises:
        sqlite3.Error: If retrieval fails
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
        SELECT abstract_id, file_name, abstract_text, created_at
        FROM Abstracts
        ORDER BY abstract_id
        """
        )

        results = cursor.fetchall()
        abstracts = []

        for result in results:
            abstract_data = {
                "id": result[0],
                "file_name": result[1],
                "abstract_text": result[2],
                "created_at": result[3],
            }
            abstracts.append(abstract_data)

        logger.info(f"Retrieved {len(abstracts)} abstracts")
        return abstracts
    except sqlite3.Error as e:
        logger.error(f"Error retrieving abstracts: {e}")
        raise
    finally:
        conn.close()
