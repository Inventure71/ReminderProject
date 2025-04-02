import tkinter as tk

from datetime import datetime






def send_message(event=None):
    """Handle sending a message: update the UI and persist the message to the database."""
    message = entry.get().strip()
    if message:
        # Insert the user's message into the database.
        insert_message("You", message)

        # Update the chat display.
        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"You: {message}\n")

        # For demonstration, the bot echoes the user's message.
        bot_response = message
        insert_message("Bot", bot_response)
        chat_box.insert(tk.END, f"Bot: {bot_response}\n\n")

        chat_box.see(tk.END)
        chat_box.config(state=tk.DISABLED)

        # Clear the input field.
        entry.delete(0, tk.END)


def load_chat_history():
    """Load and display all past chat messages from the database."""
    history = get_chat_history()
    chat_box.config(state=tk.NORMAL)
    for sender, message, timestamp in history:
        # Optionally, you can format the timestamp if needed.
        chat_box.insert(tk.END, f"{sender}: {message}\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


# Initialize the database.
init_db()

# Set up the main window.
root = tk.Tk()
root.title("Persistent Chat UI")

# Create a frame to hold the chat display.
chat_frame = tk.Frame(root)
chat_frame.pack(padx=10, pady=10)

# Add a scrollbar to the chat display.
scrollbar = tk.Scrollbar(chat_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Create a text widget for displaying chat messages.
chat_box = tk.Text(chat_frame, wrap=tk.WORD, state=tk.DISABLED, width=50, height=15, yscrollcommand=scrollbar.set)
chat_box.pack(side=tk.LEFT, fill=tk.BOTH)
scrollbar.config(command=chat_box.yview)

# Create an entry widget for user input.
entry = tk.Entry(root, width=50)
entry.pack(padx=10, pady=5)
entry.bind("<Return>", send_message)

# Create a button to send the message.
send_button = tk.Button(root, text="Send", command=send_message)
send_button.pack(padx=10, pady=5)

# Load previous chat history into the chat display.
load_chat_history()

# Start the Tkinter event loop.
root.mainloop()
