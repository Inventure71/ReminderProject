import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import os
import shutil
from PIL import Image, ImageTk
import base64
from database_utils import DatabaseHandler
import threading

class UIManager:
    def __init__(self, root):
        self.root = root
        self.db_handler = DatabaseHandler()
        self.current_project = "main"
        self.message_widgets = {}
        self.current_file_path = None
        self.current_file_type = None
        self.auto_update_active = True
        
        # Initialize UI components
        self.setup_ui()
        
        # Start auto-update
        self.auto_update()

    def setup_ui(self):
        """Initialize all UI components."""
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create project tabs
        self.project_notebook = ttk.Notebook(self.main_container)
        self.project_notebook.pack(fill=tk.BOTH, expand=True)

        # Create main chat tab
        self.main_tab = ttk.Frame(self.project_notebook)
        self.project_notebook.add(self.main_tab, text="Main")

        # Create messages area
        self.messages_canvas = tk.Canvas(self.main_tab)
        self.messages_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.messages_frame = ttk.Frame(self.messages_canvas)
        self.messages_canvas.create_window((0, 0), window=self.messages_frame, anchor=tk.NW)

        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(self.main_tab, orient=tk.VERTICAL, command=self.messages_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.messages_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create input area
        self.input_frame = ttk.Frame(self.main_container)
        self.input_frame.pack(fill=tk.X, pady=5)

        self.entry = ttk.Entry(self.input_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", self.send_message)

        self.attach_button = ttk.Button(self.input_frame, text="Attach", command=self.attach_file)
        self.attach_button.pack(side=tk.LEFT, padx=5)

        self.attach_label = ttk.Label(self.input_frame, text="")
        self.attach_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.send_button = ttk.Button(self.input_frame, text="Send", command=lambda: self.send_message())
        self.send_button.pack(side=tk.LEFT, padx=5)

        # Create menu bar
        self.create_menu()

        # Load initial chat history
        self.load_chat_history()

    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.create_new_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Search Messages", command=self.search_messages)

    def auto_update(self):
        """Periodically refresh the chat and project tabs."""
        if self.auto_update_active:
            if self.current_project == "main":
                self.load_chat_history()
            self.update_project_tabs()
            self.root.after(5000, self.auto_update)

    def attach_file(self):
        """Handle attaching a file to the message."""
        file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                self.current_file_type = 'image'
            elif ext == '.pdf':
                self.current_file_type = 'pdf'
            else:
                self.current_file_type = 'file'

            self.current_file_path = file_path
            self.attach_label.config(text=f"Attached: {os.path.basename(file_path)} ({self.current_file_type})")

    def send_message(self, event=None):
        """Handle sending a message."""
        message = self.entry.get().strip()

        if not message and not self.current_file_path:
            return

        message_type = 'text'
        file_content = None

        if self.current_file_path:
            message_type = self.current_file_type
            file_content = self.current_file_path

            if not message:
                message = f"Sent a {message_type}: {os.path.basename(self.current_file_path)}"

        message_id = self.db_handler.insert_message(
            "You", 
            message, 
            category="user_message", 
            message_type=message_type,
            project=self.current_project,
            file_path=file_content if file_content else ""
        )

        self.add_message_to_chat("You", message, message_type, file_content, message_id)

        self.entry.delete(0, tk.END)
        self.current_file_path = None
        self.current_file_type = None
        self.attach_label.config(text="")

    def add_message_to_chat(self, sender, message, message_type='text', file_path=None, message_id=None, project=None):
        """Add a message to the chat display."""
        msg_frame = ttk.Frame(self.messages_frame)
        msg_frame.pack(fill=tk.X, padx=5, pady=5)

        sender_label = ttk.Label(msg_frame, text=f"{sender}:", font=("Arial", 10, "bold"))
        sender_label.pack(anchor=tk.W, padx=5, pady=2)

        if message_type == 'text':
            msg_content = ttk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT)
            msg_content.pack(anchor=tk.W, padx=5, pady=2)
        elif message_type == 'image' and file_path and os.path.exists(file_path):
            try:
                img = Image.open(file_path)
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                msg_content = ttk.Label(msg_frame, image=photo)
                msg_content.image = photo
                msg_content.pack(anchor=tk.W, padx=5, pady=2)
            except Exception as e:
                msg_content = ttk.Label(msg_frame, text=f"Error displaying image: {str(e)}")
                msg_content.pack(anchor=tk.W, padx=5, pady=2)
        elif message_type == 'pdf' and file_path and os.path.exists(file_path):
            msg_content = ttk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT)
            msg_content.pack(anchor=tk.W, padx=5, pady=2)
            open_btn = ttk.Button(msg_frame, text="Open PDF", command=lambda: self.open_file(file_path))
            open_btn.pack(anchor=tk.W, padx=5, pady=2)
        else:
            msg_content = ttk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT)
            msg_content.pack(anchor=tk.W, padx=5, pady=2)

        action_frame = ttk.Frame(msg_frame)
        action_frame.pack(anchor=tk.W, padx=5, pady=2)

        copy_btn = ttk.Button(action_frame, text="Copy", command=lambda: self.copy_message(message))
        copy_btn.pack(side=tk.LEFT, padx=2)

        if message_id:
            delete_btn = ttk.Button(action_frame, text="Delete", 
                                  command=lambda: self.delete_message(message_id, msg_frame))
            delete_btn.pack(side=tk.LEFT, padx=2)
            change_proj_btn = ttk.Button(action_frame, text="Move to Project", 
                                       command=lambda: self.change_message_project(message_id))
            change_proj_btn.pack(side=tk.LEFT, padx=2)
            self.message_widgets[message_id] = msg_frame

        self.messages_canvas.update_idletasks()
        self.messages_canvas.configure(scrollregion=self.messages_canvas.bbox("all"))
        self.messages_canvas.yview_moveto(1.0)

    def open_file(self, file_path):
        """Open a file with the system's default application."""
        import subprocess
        import platform

        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', file_path))
        elif platform.system() == 'Windows':
            os.startfile(file_path)
        else:  # Linux
            subprocess.call(('xdg-open', file_path))

    def copy_message(self, message):
        """Copy message text to clipboard."""
        self.root.clipboard_clear()
        self.root.clipboard_append(message)
        messagebox.showinfo("Copied", "Message copied to clipboard!")

    def delete_message(self, message_id, msg_frame):
        """Delete a message from the database and UI."""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this message?"):
            if self.db_handler.delete_message(message_id):
                msg_frame.destroy()
                if message_id in self.message_widgets:
                    del self.message_widgets[message_id]
                messagebox.showinfo("Success", "Message deleted successfully!")
            else:
                messagebox.showerror("Error", "Failed to delete message.")

    def change_message_project(self, message_id):
        """Change the project of a message."""
        projects = self.db_handler.get_projects()

        dialog = tk.Toplevel(self.root)
        dialog.title("Select Project")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select a project:").pack(pady=10)

        project_var = tk.StringVar(dialog)
        project_var.set(self.current_project)

        project_menu = ttk.OptionMenu(dialog, project_var, *projects)
        project_menu.pack(pady=5)

        ttk.Label(dialog, text="Or create a new project:").pack(pady=5)
        new_project_entry = ttk.Entry(dialog, width=20)
        new_project_entry.pack(pady=5)

        def on_submit():
            new_project = new_project_entry.get().strip()
            selected_project = project_var.get()

            if new_project:
                selected_project = new_project

            if self.db_handler.update_message_project(message_id, selected_project):
                dialog.destroy()
                self.load_chat_history()
                messagebox.showinfo("Success", "Message moved successfully!")
            else:
                messagebox.showerror("Error", "Failed to move message.")

        ttk.Button(dialog, text="Submit", command=on_submit).pack(pady=10)

    def load_chat_history(self, project=None):
        """Load chat history for the current project."""
        # Clear existing messages
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.message_widgets.clear()

        # Get messages from database
        messages = self.db_handler.get_messages(project or self.current_project)

        # Add messages to chat
        for msg in messages:
            self.add_message_to_chat(
                msg['sender'],
                msg['message'],
                msg['message_type'],
                msg['file_path'],
                msg['id'],
                msg['project']
            )

    def create_new_project(self):
        """Create a new project."""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Project")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter project name:").pack(pady=10)
        project_entry = ttk.Entry(dialog, width=20)
        project_entry.pack(pady=5)

        def on_submit():
            project_name = project_entry.get().strip()
            if project_name:
                if self.db_handler.create_project(project_name):
                    dialog.destroy()
                    self.update_project_tabs()
                    messagebox.showinfo("Success", "Project created successfully!")
                else:
                    messagebox.showerror("Error", "Failed to create project.")

        ttk.Button(dialog, text="Create", command=on_submit).pack(pady=10)

    def update_project_tabs(self):
        """Update the project tabs in the notebook."""
        # Get current projects
        projects = self.db_handler.get_projects()

        # Remove existing tabs except main
        for tab in self.project_notebook.tabs()[1:]:
            self.project_notebook.forget(tab)

        # Add tabs for each project
        for project in projects:
            if project != "main":
                self.create_project_tab(project)

    def create_project_tab(self, project_name):
        """Create a new tab for a project."""
        project_tab = ttk.Frame(self.project_notebook)
        self.project_notebook.add(project_tab, text=project_name)

        # Create messages area
        messages_canvas = tk.Canvas(project_tab)
        messages_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        messages_frame = ttk.Frame(messages_canvas)
        messages_canvas.create_window((0, 0), window=messages_frame, anchor=tk.NW)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(project_tab, orient=tk.VERTICAL, command=messages_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        messages_canvas.configure(yscrollcommand=scrollbar.set)

        def load_project():
            # Clear existing messages
            for widget in messages_frame.winfo_children():
                widget.destroy()

            # Get messages for this project
            messages = self.db_handler.get_messages(project_name)

            # Add messages to chat
            for msg in messages:
                self.add_message_to_chat(
                    msg['sender'],
                    msg['message'],
                    msg['message_type'],
                    msg['file_path'],
                    msg['id'],
                    msg['project']
                )

            messages_canvas.update_idletasks()
            messages_canvas.configure(scrollregion=messages_canvas.bbox("all"))

        # Load initial messages
        load_project()

    def search_messages(self):
        """Open search dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Search Messages")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Search frame
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def perform_search():
            query = search_var.get().strip()
            if query:
                results = self.db_handler.search_messages(query)
                results_text.delete(1.0, tk.END)
                for msg in results:
                    results_text.insert(tk.END, f"Project: {msg['project']}\n")
                    results_text.insert(tk.END, f"Sender: {msg['sender']}\n")
                    results_text.insert(tk.END, f"Message: {msg['message']}\n")
                    results_text.insert(tk.END, "-" * 50 + "\n")

        search_button = ttk.Button(search_frame, text="Search", command=perform_search)
        search_button.pack(side=tk.LEFT)

        # Results area
        results_frame = ttk.Frame(dialog)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        results_text = tk.Text(results_frame, wrap=tk.WORD, height=20)
        results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        results_text.configure(yscrollcommand=results_scrollbar.set)

        # Bind Enter key to search
        search_entry.bind("<Return>", lambda e: perform_search())

    def on_closing(self):
        """Handle application closing."""
        self.auto_update_active = False
        self.root.destroy()

    def retrieve_all_projects(self):
        """Retrieve all projects and their first 10 messages."""
        projects = self.db_handler.get_projects()
        result = []
        
        for project in projects:
            result.append(f"Project: {project}")
            messages = self.db_handler.get_messages(project, limit=10)
            for msg in messages:
                result.append(f"- {msg['sender']}: {msg['message']}")
            result.append("\n")
        
        return "\n".join(result)

    def retrieve_unprocessed_messages(self):
        """Retrieve all unprocessed messages."""
        messages = self.db_handler.get_unprocessed_messages()
        result = []
        
        for i, msg in enumerate(messages, 1):
            result.append(f"{i}. Project: {msg['project']}")
            result.append(f"   Sender: {msg['sender']}")
            result.append(f"   Message: {msg['message']}")
            result.append("")
        
        return "\n".join(result) 