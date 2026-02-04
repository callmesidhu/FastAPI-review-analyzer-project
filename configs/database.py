import sqlite3

DB_NAME = "sqlite.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    print("✅ DB Connected Successfully")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Drop existing tables to clean up (sqlite_sequence will be dropped automatically)
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT DEFAULT (lower(hex(randomblob(8)))) UNIQUE,
            product_name TEXT,
            product_url TEXT UNIQUE,
            product_image TEXT,
            product_price TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            review_title TEXT,
            review_text TEXT,
            rating REAL,
            sentiment TEXT,
            polarity REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database tables recreated successfully")