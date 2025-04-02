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
                "message_type": "TEXT DEFAULT 'text'",
                "project": "TEXT DEFAULT 'main'",
                "file_path": "TEXT DEFAULT ''",
                "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP"
            }
        self.create_table(table_name, columns)

        # Create projects table if it doesn't exist
        projects_columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL UNIQUE",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        }
        self.create_table("projects", projects_columns)

        # Insert default project if it doesn't exist
        self.cursor.execute("SELECT COUNT(*) FROM projects WHERE name = 'main'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO projects (name) VALUES ('main')")
            self.commit()

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

    def get_chat_history(self, table_name="messages", project=None):
        """
        Retrieve all messages from the database, ordered by their ID.

        Args:
            table_name (str, optional): The table to query. Defaults to "messages".
            project (str, optional): Filter messages by project. Defaults to None (all projects).
        """
        # Check which columns exist
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = self.cursor.fetchall()
        columns = [info[1] for info in columns_info]

        # Build SELECT clause
        select_columns = ["id", "sender", "message", "timestamp"]
        if "category" in columns:
            select_columns.append("category")
        if "message_type" in columns:
            select_columns.append("message_type")
        if "project" in columns:
            select_columns.append("project")

        select_clause = ", ".join(select_columns)

        # Build WHERE clause if project is specified
        where_clause = ""
        params = []
        if project and "project" in columns:
            where_clause = " WHERE project = ?"
            params.append(project)

        # Execute query
        query = f"SELECT {select_clause} FROM {table_name}{where_clause} ORDER BY id"
        self.cursor.execute(query, params)

        rows = self.cursor.fetchall()
        return rows

    def delete_message(self, message_id, table_name="messages"):
        """
        Delete a message from the database.

        Args:
            message_id (int): The ID of the message to delete
            table_name (str, optional): The table to delete from. Defaults to "messages".
        """
        self.cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (message_id,))
        self.commit()
        return self.cursor.rowcount > 0

    def update_message_project(self, message_id, new_project, table_name="messages"):
        """
        Update the project of a message.

        Args:
            message_id (int): The ID of the message to update
            new_project (str): The new project name
            table_name (str, optional): The table to update. Defaults to "messages".
        """
        # Ensure the project exists
        self.cursor.execute("SELECT COUNT(*) FROM projects WHERE name = ?", (new_project,))
        if self.cursor.fetchone()[0] == 0:
            # Create the project if it doesn't exist
            self.cursor.execute("INSERT INTO projects (name) VALUES (?)", (new_project,))

        # Update the message
        self.cursor.execute(f"UPDATE {table_name} SET project = ? WHERE id = ?", (new_project, message_id))
        self.commit()
        return self.cursor.rowcount > 0

    def search_messages(self, search_term, table_name="messages", project=None):
        """
        Search for messages containing the search term.

        Args:
            search_term (str): The term to search for
            table_name (str, optional): The table to search in. Defaults to "messages".
            project (str, optional): Filter by project. Defaults to None (all projects).
        """
        # Check which columns exist
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in self.cursor.fetchall()]

        # Build SELECT clause
        select_columns = ["id", "sender", "message", "timestamp"]
        if "category" in columns:
            select_columns.append("category")
        if "message_type" in columns:
            select_columns.append("message_type")
        if "project" in columns:
            select_columns.append("project")

        select_clause = ", ".join(select_columns)

        # Build WHERE clause
        where_clause = " WHERE message LIKE ?"
        params = [f"%{search_term}%"]

        if project and "project" in columns:
            where_clause += " AND project = ?"
            params.append(project)

        # Execute query
        query = f"SELECT {select_clause} FROM {table_name}{where_clause} ORDER BY id"
        self.cursor.execute(query, params)

        rows = self.cursor.fetchall()
        return rows

    def get_projects(self):
        """Get all projects from the database."""
        self.cursor.execute("SELECT name FROM projects ORDER BY name")
        return [row[0] for row in self.cursor.fetchall()]

    def create_project(self, project_name):
        """
        Create a new project.

        Args:
            project_name (str): The name of the project to create
        """
        try:
            self.cursor.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
            self.commit()
            return True
        except sqlite3.IntegrityError:
            # Project already exists
            return False
