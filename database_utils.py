import sqlite3



class DatabaseHandler:
    def __init__(self, db_name="chat.db"):
        """Initialize the database connection."""
        # Define the database file.
        self.db_name = db_name
        self.connect()

    def connect(self):
        """Establish a connection to the database."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self.conn, self.cursor

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def commit(self):
        """Commit changes to the database."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.commit()

    def create_table(self, table_name, columns):
        """
        Create a table if it doesn't exist.

        Args:
            table_name (str): Name of the table to create
            columns (dict): Dictionary mapping column names to their SQL definitions
        """
        columns_str = ', '.join([f"{name} {definition}" for name, definition in columns.items()])
        query = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns_str}
            )
        '''
        self.cursor.execute(query)
        self.commit()

    def add_column_if_not_exists(self, table_name, column_name, column_type):
        """
        Add a new column to a table if it doesn't already exist.

        Args:
            table_name (str): Name of the table to modify
            column_name (str): Name of the column to add
            column_type (str): SQL type definition for the column
        """
        # Check if column exists
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in self.cursor.fetchall()]

        if column_name not in columns:
            self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            self.commit()
            return True
        return False

    def init_db(self, table_name="messages", columns=None):
        """Initialize the database and create the specified table if it doesn't exist."""
        if columns is None:
            columns = {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "sender": "TEXT NOT NULL",
                "message": "TEXT NOT NULL",
                "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP"
            }
        self.create_table(table_name, columns)

    def insert_message(self, sender, message, table_name="messages", **additional_columns):
        """
        Insert a message into the database.

        Args:
            sender (str): The sender of the message
            message (str): The message content
            table_name (str, optional): The table to insert into. Defaults to "messages".
            **additional_columns: Additional column values to insert (e.g., category="question")
        """
        # Build the SQL query dynamically based on the columns provided
        columns = ["sender", "message"]
        values = [sender, message]

        # Add any additional columns
        for column, value in additional_columns.items():
            columns.append(column)
            values.append(value)

        # Construct the SQL query
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))

        self.cursor.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})", values)
        self.commit()

    def get_chat_history(self, table_name="messages"):
        """Retrieve all messages from the database, ordered by their ID."""
        # Check if category column exists
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in self.cursor.fetchall()]

        if "category" in columns:
            self.cursor.execute(f"SELECT sender, message, timestamp, category FROM {table_name} ORDER BY id")
        else:
            self.cursor.execute(f"SELECT sender, message, timestamp FROM {table_name} ORDER BY id")

        rows = self.cursor.fetchall()
        return rows
