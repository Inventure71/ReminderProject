import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import os
import shutil
from PIL import Image, ImageTk
import base64
from database_utils import DatabaseHandler
import threading

# Create a database handler instance
db_handler = DatabaseHandler()

# Global variables
current_project = "main"
message_widgets = {}  # Store references to message widgets for actions
current_file_path = None
current_file_type = None
auto_update_active = True  # Control auto-update

def auto_update():
    """Periodically refresh the chat and project tabs."""
    if auto_update_active:
        # Refresh the current chat
        if current_project == "main":
            load_chat_history()

        # Update project tabs
        update_project_tabs()

        # Schedule the next update in 5 seconds
        root.after(5000, auto_update)






def attach_file():
    """Handle attaching a file to the message."""
    global current_file_path, current_file_type

    file_path = filedialog.askopenfilename(
        title="Select a file",
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
    )

    if file_path:
        # Get file extension to determine type
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            current_file_type = 'image'
        elif ext == '.pdf':
            current_file_type = 'pdf'
        else:
            current_file_type = 'file'

        current_file_path = file_path

        # Update the UI to show the attached file
        file_name = os.path.basename(file_path)
        attach_label.config(text=f"Attached: {file_name} ({current_file_type})")

def send_message(event=None):
    """Handle sending a message: update the UI and persist the message to the database."""
    global current_file_path, current_file_type

    message = entry.get().strip()

    # Check if we have a message or a file
    if not message and not current_file_path:
        return

    # Determine message type
    message_type = 'text'
    file_content = None

    if current_file_path:
        message_type = current_file_type

        # For simplicity, we'll store the file path in the message
        # In a real app, you might want to copy the file to a dedicated storage location
        file_content = current_file_path

        if not message:
            message = f"Sent a {message_type}: {os.path.basename(current_file_path)}"

    # Insert the message into the database
    db_handler.insert_message(
        "You", 
        message, 
        category="user_message", 
        message_type=message_type,
        project=current_project,
        file_path=file_content if file_content else ""
    )

    # Add the message to the UI
    add_message_to_chat("You", message, message_type, file_content)

    # Clear the input field and file attachment
    entry.delete(0, tk.END)
    current_file_path = None
    current_file_type = None
    attach_label.config(text="")


def add_message_to_chat(sender, message, message_type='text', file_path=None, message_id=None, project=None):
    """Add a message to the chat display with interactive elements."""
    global message_widgets

    # Create a frame for this message
    msg_frame = tk.Frame(messages_frame, bg="#f0f0f0", bd=1, relief=tk.RAISED)
    msg_frame.pack(fill=tk.X, padx=5, pady=5, anchor=tk.W)

    # Add sender info
    sender_label = tk.Label(msg_frame, text=f"{sender}:", font=("Arial", 10, "bold"), bg="#f0f0f0", fg="black")
    sender_label.pack(anchor=tk.W, padx=5, pady=2)

    # Add message content based on type
    if message_type == 'text':
        msg_content = tk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT, bg="#f0f0f0", fg="black")
        msg_content.pack(anchor=tk.W, padx=5, pady=2)
    elif message_type == 'image' and file_path and os.path.exists(file_path):
        try:
            # Open and resize image
            img = Image.open(file_path)
            img.thumbnail((300, 300))  # Resize to fit
            photo = ImageTk.PhotoImage(img)

            # Keep a reference to prevent garbage collection
            msg_content = tk.Label(msg_frame, image=photo, bg="#f0f0f0")
            msg_content.image = photo
            msg_content.pack(anchor=tk.W, padx=5, pady=2)

            # Add caption if there's a message
            if message and not message.startswith("Sent a "):
                caption = tk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT, bg="#f0f0f0", fg="black")
                caption.pack(anchor=tk.W, padx=5, pady=2)
        except Exception as e:
            msg_content = tk.Label(msg_frame, text=f"Error displaying image: {str(e)}", bg="#f0f0f0", fg="black")
            msg_content.pack(anchor=tk.W, padx=5, pady=2)
    elif message_type == 'pdf' and file_path and os.path.exists(file_path):
        # For PDFs, just show a link
        msg_content = tk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT, bg="#f0f0f0", fg="black")
        msg_content.pack(anchor=tk.W, padx=5, pady=2)

        def open_pdf():
            import subprocess
            import platform

            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            elif platform.system() == 'Windows':
                os.startfile(file_path)
            else:  # Linux
                subprocess.call(('xdg-open', file_path))

        open_btn = tk.Button(msg_frame, text="Open PDF", command=open_pdf)
        open_btn.pack(anchor=tk.W, padx=5, pady=2)
    else:
        # Default for other types or missing files
        msg_content = tk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT, bg="#f0f0f0")
        msg_content.pack(anchor=tk.W, padx=5, pady=2)

        if file_path:
            file_info = tk.Label(msg_frame, text=f"File: {os.path.basename(file_path)}", bg="#f0f0f0", fg="blue")
            file_info.pack(anchor=tk.W, padx=5, pady=2)

    # Add action buttons
    action_frame = tk.Frame(msg_frame, bg="#f0f0f0")
    action_frame.pack(anchor=tk.W, padx=5, pady=2)

    # Copy button
    copy_btn = tk.Button(action_frame, text="Copy", command=lambda: copy_message(message))
    copy_btn.pack(side=tk.LEFT, padx=2)

    # Delete button (only if we have a message_id)
    if message_id:
        delete_btn = tk.Button(action_frame, text="Delete", command=lambda mid=message_id, mf=msg_frame: delete_message(mid, mf))
        delete_btn.pack(side=tk.LEFT, padx=2)

    # Change project button (only if we have a message_id)
    if message_id:
        change_proj_btn = tk.Button(action_frame, text="Move to Project", command=lambda mid=message_id: change_message_project(mid))
        change_proj_btn.pack(side=tk.LEFT, padx=2)

    # Store reference to the message frame if we have an ID
    if message_id:
        message_widgets[message_id] = msg_frame

    # Update the canvas scroll region
    messages_canvas.update_idletasks()
    messages_canvas.configure(scrollregion=messages_canvas.bbox("all"))

    # Scroll to the bottom
    messages_canvas.yview_moveto(1.0)

def copy_message(message):
    """Copy message text to clipboard."""
    root.clipboard_clear()
    root.clipboard_append(message)
    messagebox.showinfo("Copied", "Message copied to clipboard!")

def delete_message(message_id, msg_frame):
    """Delete a message from the database and UI."""
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this message?"):
        if db_handler.delete_message(message_id):
            msg_frame.destroy()
            if message_id in message_widgets:
                del message_widgets[message_id]
            messagebox.showinfo("Success", "Message deleted successfully!")
        else:
            messagebox.showerror("Error", "Failed to delete message.")

def change_message_project(message_id):
    """Change the project of a message."""
    projects = db_handler.get_projects()

    # Create a simple dialog to select a project
    dialog = tk.Toplevel(root)
    dialog.title("Select Project")
    dialog.geometry("300x200")
    dialog.transient(root)
    dialog.grab_set()

    tk.Label(dialog, text="Select a project:").pack(pady=10)

    project_var = tk.StringVar(dialog)
    project_var.set(current_project)  # Default to current project

    project_menu = tk.OptionMenu(dialog, project_var, *projects)
    project_menu.pack(pady=5)

    # New project entry
    tk.Label(dialog, text="Or create a new project:").pack(pady=5)
    new_project_entry = tk.Entry(dialog, width=20)
    new_project_entry.pack(pady=5)

    def on_submit():
        new_project = new_project_entry.get().strip()
        selected_project = project_var.get()

        # Use new project if provided, otherwise use selected
        target_project = new_project if new_project else selected_project

        if db_handler.update_message_project(message_id, target_project):
            messagebox.showinfo("Success", f"Message moved to project '{target_project}'")

            # Update project tabs if a new project was created
            if new_project:
                update_project_tabs()

            # Refresh the chat if we're viewing the current project
            if current_project == target_project or current_project == "main":
                load_chat_history()
        else:
            messagebox.showerror("Error", "Failed to move message.")

        dialog.destroy()

    tk.Button(dialog, text="Move Message", command=on_submit).pack(pady=10)
    tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

def load_chat_history(project=None):
    """Load and display all past chat messages from the database."""
    global current_project

    # Update current project if specified
    if project:
        current_project = project

    # Clear existing messages
    for widget in messages_frame.winfo_children():
        widget.destroy()

    message_widgets.clear()

    # Get chat history for the current project
    # If current_project is "main", show all messages
    if current_project == "main":
        history = db_handler.get_chat_history()
    else:
        history = db_handler.get_chat_history(project=current_project)

    # Update project label
    project_label.config(text=f"Current Project: {current_project}")

    # Add messages to the chat
    for row in history:
        message_id = row[0]
        sender = row[1]
        message = row[2]
        timestamp = row[3]

        # Get message type and file path if available
        message_type = 'text'
        file_path = None

        # Check column indices based on database structure
        if len(row) > 4:  # Has category
            category = row[4]

        if len(row) > 5:  # Has message_type
            message_type = row[5]

        if len(row) > 6:  # Has project
            project = row[6]

        if len(row) > 7:  # Has file_path
            file_path = row[7]
            if file_path and not os.path.exists(file_path):
                file_path = None  # Reset if file doesn't exist

        add_message_to_chat(sender, message, message_type, file_path, message_id, project)


def create_new_project():
    """Create a new project."""
    dialog = tk.Toplevel(root)
    dialog.title("Create New Project")
    dialog.geometry("300x150")
    dialog.transient(root)
    dialog.grab_set()

    tk.Label(dialog, text="Enter new project name:").pack(pady=10)

    project_entry = tk.Entry(dialog, width=30)
    project_entry.pack(pady=5)
    project_entry.focus_set()

    def on_submit():
        project_name = project_entry.get().strip()
        if not project_name:
            messagebox.showerror("Error", "Project name cannot be empty.")
            return

        if db_handler.create_project(project_name):
            messagebox.showinfo("Success", f"Project '{project_name}' created successfully!")
            update_project_tabs()
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Project already exists or could not be created.")

    tk.Button(dialog, text="Create", command=on_submit).pack(pady=10)
    tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

def update_project_tabs():
    """Update the project tabs in the notebook."""
    # Get all projects
    projects = db_handler.get_projects()

    # Remember the current tab
    current_tab = notebook.index(notebook.select()) if notebook.index("end") > 0 else 0

    # Remove all tabs except the first one (main chat)
    for i in range(1, notebook.index("end")):
        notebook.forget(1)  # Always remove the second tab (index 1)

    # Add a tab for each project
    for project in projects:
        if project != "main":  # Skip main project as it's already the first tab
            project_frame = create_project_tab(project)
            notebook.add(project_frame, text=project)

    # Add a tab for creating a new project
    new_project_frame = ttk.Frame(notebook)
    tk.Button(new_project_frame, text="+ Create New Project", command=create_new_project).pack(expand=True)
    notebook.add(new_project_frame, text="+")

    # Try to select the previously selected tab
    try:
        notebook.select(current_tab)
    except:
        notebook.select(0)  # Default to first tab

def create_project_tab(project_name):
    """Create a tab for a specific project."""
    frame = ttk.Frame(notebook)

    # Create a canvas with scrollbar for messages
    canvas_frame = tk.Frame(frame)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    canvas_scrollbar = tk.Scrollbar(canvas_frame)
    canvas_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    project_canvas = tk.Canvas(canvas_frame, yscrollcommand=canvas_scrollbar.set)
    project_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    canvas_scrollbar.config(command=project_canvas.yview)

    # Create a frame inside the canvas for messages
    project_messages_frame = tk.Frame(project_canvas)
    project_canvas.create_window((0, 0), window=project_messages_frame, anchor=tk.NW)

    # Function to load this project's messages
    def load_project():
        # Clear existing messages
        for widget in project_messages_frame.winfo_children():
            widget.destroy()

        # Get chat history for this project
        history = db_handler.get_chat_history(project=project_name)

        # Add messages to the chat
        for row in history:
            message_id = row[0]
            sender = row[1]
            message = row[2]
            timestamp = row[3]

            # Get message type and file path if available
            message_type = 'text'
            file_path = None

            # Check column indices based on database structure
            if len(row) > 4:  # Has category
                category = row[4]

            if len(row) > 5:  # Has message_type
                message_type = row[5]

            if len(row) > 6:  # Has project
                project = row[6]

            if len(row) > 7:  # Has file_path
                file_path = row[7]
                if file_path and not os.path.exists(file_path):
                    file_path = None  # Reset if file doesn't exist

            # Create a frame for this message
            msg_frame = tk.Frame(project_messages_frame, bg="#f0f0f0", bd=1, relief=tk.RAISED)
            msg_frame.pack(fill=tk.X, padx=5, pady=5, anchor=tk.W)

            # Add sender info
            sender_label = tk.Label(msg_frame, text=f"{sender}:", font=("Arial", 10, "bold"), bg="#f0f0f0", fg="black")
            sender_label.pack(anchor=tk.W, padx=5, pady=2)

            # Add message content
            msg_content = tk.Label(msg_frame, text=message, wraplength=400, justify=tk.LEFT, bg="#f0f0f0", fg="black")
            msg_content.pack(anchor=tk.W, padx=5, pady=2)

            # Add action buttons
            action_frame = tk.Frame(msg_frame, bg="#f0f0f0")
            action_frame.pack(anchor=tk.W, padx=5, pady=2)

            # Copy button
            copy_btn = tk.Button(action_frame, text="Copy", command=lambda m=message: copy_message(m))
            copy_btn.pack(side=tk.LEFT, padx=2)

            # Delete button
            delete_btn = tk.Button(action_frame, text="Delete", 
                                  command=lambda mid=message_id, mf=msg_frame: delete_message(mid, mf))
            delete_btn.pack(side=tk.LEFT, padx=2)

            # Move to Project button
            change_proj_btn = tk.Button(action_frame, text="Move to Project", 
                                       command=lambda mid=message_id: change_message_project(mid))
            change_proj_btn.pack(side=tk.LEFT, padx=2)

        # Update the canvas scroll region
        project_canvas.update_idletasks()
        project_canvas.configure(scrollregion=project_canvas.bbox("all"))

    # Load messages when tab is created
    load_project()

    # Add a refresh button
    refresh_btn = tk.Button(frame, text="Refresh", command=load_project)
    refresh_btn.pack(pady=5)

    return frame

def search_messages():
    """Search for messages containing the search term."""
    search_term = search_entry.get().strip()
    if not search_term:
        messagebox.showinfo("Search", "Please enter a search term.")
        return

    # Get search results
    results = db_handler.search_messages(search_term)

    # Display results in a new window
    results_window = tk.Toplevel(root)
    results_window.title(f"Search Results for '{search_term}'")
    results_window.geometry("600x400")

    # Create a frame with scrollbar for results
    results_frame = tk.Frame(results_window)
    results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    results_scrollbar = tk.Scrollbar(results_frame)
    results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    results_canvas = tk.Canvas(results_frame, yscrollcommand=results_scrollbar.set)
    results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    results_scrollbar.config(command=results_canvas.yview)

    # Create a frame inside the canvas for results
    results_messages_frame = tk.Frame(results_canvas)
    results_canvas.create_window((0, 0), window=results_messages_frame, anchor=tk.NW)

    # Add a label showing the number of results
    tk.Label(results_messages_frame, 
             text=f"Found {len(results)} message(s) containing '{search_term}'",
             font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=5, pady=10)

    # Add each result
    for row in results:
        message_id = row[0]
        sender = row[1]
        message = row[2]
        timestamp = row[3]

        # Get project if available
        project = "Unknown"
        if len(row) > 6:  # Has project
            project = row[6]

        # Create a frame for this result
        result_frame = tk.Frame(results_messages_frame, bg="#f5f5f5", bd=1, relief=tk.RAISED)
        result_frame.pack(fill=tk.X, padx=5, pady=5, anchor=tk.W)

        # Add header with sender and project
        header_frame = tk.Frame(result_frame, bg="#e0e0e0")
        header_frame.pack(fill=tk.X, anchor=tk.W)

        tk.Label(header_frame, text=f"{sender}", font=("Arial", 10, "bold"), 
                bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)

        tk.Label(header_frame, text=f"Project: {project}", 
                bg="#e0e0e0").pack(side=tk.RIGHT, padx=5, pady=2)

        # Add message content
        msg_content = tk.Label(result_frame, text=message, wraplength=500, 
                              justify=tk.LEFT, bg="#f5f5f5")
        msg_content.pack(anchor=tk.W, padx=5, pady=5)

        # Add timestamp
        tk.Label(result_frame, text=f"Sent: {timestamp}", 
                font=("Arial", 8), fg="gray", bg="#f5f5f5").pack(anchor=tk.E, padx=5, pady=2)

        # Add action buttons
        action_frame = tk.Frame(result_frame, bg="#f5f5f5")
        action_frame.pack(anchor=tk.W, padx=5, pady=5)

        # Go to project button
        def go_to_project(proj):
            results_window.destroy()
            load_chat_history(proj)

            # Select the appropriate tab
            if proj == "main":
                notebook.select(0)
            else:
                # Find the tab with this project
                for i in range(notebook.index("end")):
                    if notebook.tab(i, "text") == proj:
                        notebook.select(i)
                        break

        tk.Button(action_frame, text="Go to Project", 
                 command=lambda p=project: go_to_project(p)).pack(side=tk.LEFT, padx=2)

        # Copy button
        tk.Button(action_frame, text="Copy", 
                 command=lambda m=message: copy_message(m)).pack(side=tk.LEFT, padx=2)

    # Update the canvas scroll region
    results_canvas.update_idletasks()
    results_canvas.configure(scrollregion=results_canvas.bbox("all"))

# Initialize the database.
db_handler.init_db()

# Make sure all necessary columns exist
db_handler.add_column_if_not_exists("messages", "category", "TEXT")
db_handler.add_column_if_not_exists("messages", "message_type", "TEXT DEFAULT 'text'")
db_handler.add_column_if_not_exists("messages", "project", "TEXT DEFAULT 'main'")
db_handler.add_column_if_not_exists("messages", "file_path", "TEXT DEFAULT ''")

# Set up the main window.
root = tk.Tk()
root.title("Advanced Chat UI")
root.geometry("800x600")

# Create a notebook for tabs
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create the main chat tab
main_tab = ttk.Frame(notebook)
notebook.add(main_tab, text="Main Chat")

# Create a frame for the project label and search
header_frame = tk.Frame(main_tab)
header_frame.pack(fill=tk.X, padx=10, pady=5)

# Project label
project_label = tk.Label(header_frame, text="Current Project: main", font=("Arial", 12, "bold"))
project_label.pack(side=tk.LEFT)

# Search frame
search_frame = tk.Frame(header_frame)
search_frame.pack(side=tk.RIGHT)

search_entry = tk.Entry(search_frame, width=20)
search_entry.pack(side=tk.LEFT, padx=5)

search_button = tk.Button(search_frame, text="Search", command=search_messages)
search_button.pack(side=tk.LEFT)

# Create a canvas with scrollbar for messages
messages_canvas_frame = tk.Frame(main_tab)
messages_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

messages_scrollbar = tk.Scrollbar(messages_canvas_frame)
messages_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

messages_canvas = tk.Canvas(messages_canvas_frame, yscrollcommand=messages_scrollbar.set)
messages_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

messages_scrollbar.config(command=messages_canvas.yview)

# Create a frame inside the canvas for messages
messages_frame = tk.Frame(messages_canvas)
messages_canvas.create_window((0, 0), window=messages_frame, anchor=tk.NW)

# Create a frame for input controls
input_frame = tk.Frame(main_tab)
input_frame.pack(fill=tk.X, padx=10, pady=5)

# Attachment label
attach_label = tk.Label(input_frame, text="", fg="blue")
attach_label.pack(anchor=tk.W, pady=2)

# Message entry
entry = tk.Entry(input_frame, width=50)
entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
entry.bind("<Return>", send_message)

# Attach file button
attach_button = tk.Button(input_frame, text="Attach File", command=attach_file)
attach_button.pack(side=tk.LEFT, padx=5)

# Send button
send_button = tk.Button(input_frame, text="Send", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

# Update project tabs
update_project_tabs()

# Load previous chat history into the chat display
load_chat_history()

# Define a function to handle the application closing
def on_closing():
    """Handle the application closing event."""
    global auto_update_active
    auto_update_active = False  # Stop auto-update
    root.destroy()

# Set up the closing event handler
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the auto-update mechanism
auto_update()

# Start the Tkinter event loop
root.mainloop()
