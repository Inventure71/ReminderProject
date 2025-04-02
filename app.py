import tkinter as tk
from ui_manager import UIManager
from database_utils import DatabaseHandler

class ReminderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Reminder Project")
        self.root.geometry("800x600")
        
        # Initialize database
        self.db_handler = DatabaseHandler()
        self.db_handler.init_db()
        
        # Make sure all necessary columns exist
        self.db_handler.add_column_if_not_exists("messages", "category", "TEXT")
        self.db_handler.add_column_if_not_exists("messages", "message_type", "TEXT DEFAULT 'text'")
        self.db_handler.add_column_if_not_exists("messages", "project", "TEXT DEFAULT 'main'")
        self.db_handler.add_column_if_not_exists("messages", "file_path", "TEXT DEFAULT ''")
        
        # Initialize UI
        self.ui_manager = UIManager(self.root, self.db_handler)
        
        # Set up closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing."""
        self.ui_manager.auto_update_active = False
        self.root.destroy()

def main():
    app = ReminderApp()
    app.run()

if __name__ == "__main__":
    main() 