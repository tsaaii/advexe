import tkinter as tk
from tkinter import ttk, messagebox
import os
import hashlib
import json

import config
from ui_components import HoverButton

class LoginDialog:
    """Login dialog for authentication"""
    
    def __init__(self, parent, admin_panel):
        """Initialize login dialog
        
        Args:
            parent: Parent window
            admin_panel: Admin panel for authentication
        """
        self.parent = parent
        self.admin_panel = admin_panel
        self.result = False  # Login success flag
        self.is_admin = False  # Admin access flag
        
        # Create login window
        self.create_dialog()
    
    def create_dialog(self):
        """Create login dialog UI"""
        # Create top level window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Login")
        self.window.geometry("300x200")
        self.window.resizable(False, False)
        self.window.transient(self.parent)  # Make window modal
        self.window.grab_set()  # Make window modal
        
        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.parent.winfo_width() // 2) - (width // 2)
        y = (self.parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Apply style
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Advitia Labs Login", font=("Segoe UI", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Form fields
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(form_frame, textvariable=self.username_var, width=25)
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        username_entry.focus_set()  # Set focus to username
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show="*", width=25)
        password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        login_btn = HoverButton(button_frame, text="Login", 
                              bg=config.COLORS["primary"],
                              fg=config.COLORS["button_text"],
                              font=("Segoe UI", 10, "bold"),
                              padx=10, pady=3,
                              command=self.login)
        login_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = HoverButton(button_frame, text="Cancel", 
                               bg=config.COLORS["button_alt"],
                               fg=config.COLORS["button_text"],
                               padx=10, pady=3,
                               command=self.cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter key to login
        self.window.bind("<Return>", lambda event: self.login())
        
        # Wait for window to be destroyed
        self.parent.wait_window(self.window)
    
    def login(self):
        """Handle login"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.", parent=self.window)
            return
        
        # Authenticate
        success, is_admin = self.admin_panel.authenticate_user(username, password)
        
        if success:
            self.result = True
            self.is_admin = is_admin
            self.username = username  # Store authenticated username
            self.window.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.", parent=self.window)
    
    def cancel(self):
        """Cancel login"""
        self.result = False
        self.window.destroy()