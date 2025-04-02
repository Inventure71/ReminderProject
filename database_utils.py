import sqlite3



class DatabaseHandler:
    def __init__(self, db_name="chat.db"):
        """Initialize the database connection."""
        # Define the database file.
        self.db_name = db_name

        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()


    def init_db(self):
        """Initialize the database and create the messages table if it doesn't exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def insert_message(self, sender, message):
        """Insert a message into the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender, message) VALUES (?, ?)", (sender, message))
        conn.commit()
        conn.close()

    def get_chat_history(self):
        """Retrieve all messages from the database, ordered by their ID."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT sender, message, timestamp FROM messages ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return rows

