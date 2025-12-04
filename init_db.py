import sqlite3

# Connect to the database (creates it if it doesn't exist)
conn = sqlite3.connect("database/health.db")
cursor = conn.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    age INTEGER,
    gender TEXT
);
""")

# Create health_data table
cursor.execute("""
CREATE TABLE IF NOT EXISTS health_data (
    data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    weight REAL,
    steps INTEGER,
    calories_burned INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
""")

conn.commit()
conn.close()

print("Database initialized successfully!")
