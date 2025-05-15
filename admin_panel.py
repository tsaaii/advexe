import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import hashlib
import re

import config
from ui_components import HoverButton

class AdminPanel:
    """Admin panel for user management and application settings"""
    
    def __init__(self, parent, app=None):
        """Initialize admin panel
        
        Args:
            parent: Parent widget
            app: Main application instance
        """
        self.parent = parent
        self.app = app
        self.current_user = None
        self.is_admin = False
        
        # Initialize user and settings data
        self.users_file = os.path.join(config.DATA_FOLDER, 'users.json')
        self.settings_file = os.path.join(config.DATA_FOLDER, 'settings.json')
        self.initialize_data_files()
        
        # Create UI
        self.create_panel()
    
    def initialize_data_files(self):
        """Initialize data files if they don't exist"""
        # Create users file with default admin user if it doesn't exist
        if not os.path.exists(self.users_file):
            default_users = {
                "admin": {
                    "password": self.hash_password("admin"),
                    "is_admin": True,
                    "name": "Administrator"
                }
            }
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w') as f:
                json.dump(default_users, f, indent=4)
        
        # Create settings file if it doesn't exist
        if not os.path.exists(self.settings_file):
            default_settings = {
                "site_names": ["Guntur"],
                "agency_names": []
            }
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(default_settings, f, indent=4)
    
    def create_panel(self):
        """Create admin panel with tabs"""
        # Create admin notebook for tabs
        self.admin_notebook = ttk.Notebook(self.parent)
        self.admin_notebook.pack(fill=tk.BOTH, expand=True)
        
        # User Management tab
        user_tab = ttk.Frame(self.admin_notebook, style="TFrame")
        self.admin_notebook.add(user_tab, text="User Management")
        
        # Settings tab
        settings_tab = ttk.Frame(self.admin_notebook, style="TFrame")
        self.admin_notebook.add(settings_tab, text="Settings")
        
        # Create tab contents
        self.create_user_management(user_tab)
        self.create_settings_management(settings_tab)
    
    def create_user_management(self, parent):
        """Create user management UI"""
        # Main container
        main_frame = ttk.Frame(parent, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Split into two sides - left for list, right for details
        left_frame = ttk.LabelFrame(main_frame, text="Users")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)
        
        right_frame = ttk.LabelFrame(main_frame, text="User Details")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        
        # User list (left side)
        self.create_user_list(left_frame)
        
        # User details (right side)
        self.create_user_form(right_frame)
    
    def create_user_list(self, parent):
        """Create user list with controls"""
        # List frame
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create listbox for users
        columns = ("username", "name", "admin")
        self.users_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # Define headings
        self.users_tree.heading("username", text="Username")
        self.users_tree.heading("name", text="Name")
        self.users_tree.heading("admin", text="Admin")
        
        # Define column widths
        self.users_tree.column("username", width=100)
        self.users_tree.column("name", width=150)
        self.users_tree.column("admin", width=50)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.users_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.users_tree.bind("<<TreeviewSelect>>", self.on_user_select)
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add buttons
        new_btn = HoverButton(buttons_frame, 
                            text="New User", 
                            bg=config.COLORS["primary"],
                            fg=config.COLORS["button_text"],
                            padx=5, pady=2,
                            command=self.new_user)
        new_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = HoverButton(buttons_frame, 
                               text="Delete User",
                               bg=config.COLORS["error"],
                               fg=config.COLORS["button_text"],
                               padx=5, pady=2,
                               command=self.delete_user)
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = HoverButton(buttons_frame, 
                                text="Refresh", 
                                bg=config.COLORS["secondary"],
                                fg=config.COLORS["button_text"],
                                padx=5, pady=2,
                                command=self.load_users)
        refresh_btn.pack(side=tk.RIGHT, padx=2)
        
        # Load users
        self.load_users()
    
    def create_user_form(self, parent):
        """Create user details form"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(form_frame, textvariable=self.username_var, width=20)
        self.username_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Full Name
        ttk.Label(form_frame, text="Full Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.fullname_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.fullname_var, width=30).grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.password_var, show="*", width=20).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Confirm Password
        ttk.Label(form_frame, text="Confirm Password:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.confirm_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.confirm_password_var, show="*", width=20).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Admin checkbox
        self.is_admin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_frame, text="Admin User", variable=self.is_admin_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.save_btn = HoverButton(buttons_frame, 
                                  text="Save User", 
                                  bg=config.COLORS["secondary"],
                                  fg=config.COLORS["button_text"],
                                  padx=5, pady=2,
                                  command=self.save_user)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = HoverButton(buttons_frame, 
                                    text="Cancel", 
                                    bg=config.COLORS["button_alt"],
                                    fg=config.COLORS["button_text"],
                                    padx=5, pady=2,
                                    command=self.clear_form)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar()
        status_label = ttk.Label(form_frame, textvariable=self.status_var, foreground="blue")
        status_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Initially disable username field (for editing existing user)
        self.username_entry.configure(state="disabled")
        
        # Set edit mode flag
        self.edit_mode = False
    
    def create_settings_management(self, parent):
        """Create settings management UI"""
        main_frame = ttk.Frame(parent, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Site Names Section
        site_frame = ttk.LabelFrame(main_frame, text="Site Names")
        site_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        
        # Site list and entry
        site_list_frame = ttk.Frame(site_frame)
        site_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Site listbox
        columns = ("site",)
        self.site_tree = ttk.Treeview(site_list_frame, columns=columns, show="headings", height=5)
        self.site_tree.heading("site", text="Site Name")
        self.site_tree.column("site", width=250)
        
        # Add scrollbar
        site_scrollbar = ttk.Scrollbar(site_list_frame, orient=tk.VERTICAL, command=self.site_tree.yview)
        self.site_tree.configure(yscroll=site_scrollbar.set)
        
        # Pack widgets
        site_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.site_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Site controls
        site_controls = ttk.Frame(site_frame)
        site_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # New site entry
        ttk.Label(site_controls, text="New Site Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.site_name_var = tk.StringVar()
        ttk.Entry(site_controls, textvariable=self.site_name_var, width=25).pack(side=tk.LEFT, padx=5)
        
        # Add and Delete buttons
        add_site_btn = HoverButton(site_controls,
                                 text="Add Site",
                                 bg=config.COLORS["primary"],
                                 fg=config.COLORS["button_text"],
                                 padx=5, pady=2,
                                 command=self.add_site)
        add_site_btn.pack(side=tk.LEFT, padx=5)
        
        delete_site_btn = HoverButton(site_controls,
                                    text="Delete Site",
                                    bg=config.COLORS["error"],
                                    fg=config.COLORS["button_text"],
                                    padx=5, pady=2,
                                    command=self.delete_site)
        delete_site_btn.pack(side=tk.LEFT, padx=5)
        
        # Agency Names Section
        agency_frame = ttk.LabelFrame(main_frame, text="Agency Names")
        agency_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        
        # Agency list and entry
        agency_list_frame = ttk.Frame(agency_frame)
        agency_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Agency listbox
        columns = ("agency",)
        self.agency_tree = ttk.Treeview(agency_list_frame, columns=columns, show="headings", height=5)
        self.agency_tree.heading("agency", text="Agency Name")
        self.agency_tree.column("agency", width=250)
        
        # Add scrollbar
        agency_scrollbar = ttk.Scrollbar(agency_list_frame, orient=tk.VERTICAL, command=self.agency_tree.yview)
        self.agency_tree.configure(yscroll=agency_scrollbar.set)
        
        # Pack widgets
        agency_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.agency_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Agency controls
        agency_controls = ttk.Frame(agency_frame)
        agency_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # New agency entry
        ttk.Label(agency_controls, text="New Agency Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.agency_name_var = tk.StringVar()
        ttk.Entry(agency_controls, textvariable=self.agency_name_var, width=25).pack(side=tk.LEFT, padx=5)
        
        # Add and Delete buttons
        add_agency_btn = HoverButton(agency_controls,
                                   text="Add Agency",
                                   bg=config.COLORS["primary"],
                                   fg=config.COLORS["button_text"],
                                   padx=5, pady=2,
                                   command=self.add_agency)
        add_agency_btn.pack(side=tk.LEFT, padx=5)
        
        delete_agency_btn = HoverButton(agency_controls,
                                      text="Delete Agency",
                                      bg=config.COLORS["error"],
                                      fg=config.COLORS["button_text"],
                                      padx=5, pady=2,
                                      command=self.delete_agency)
        delete_agency_btn.pack(side=tk.LEFT, padx=5)
        
        # Save Settings button
        save_settings_frame = ttk.Frame(main_frame)
        save_settings_frame.pack(fill=tk.X, padx=5, pady=10)
        
        save_settings_btn = HoverButton(save_settings_frame,
                                      text="Save Settings",
                                      bg=config.COLORS["secondary"],
                                      fg=config.COLORS["button_text"],
                                      padx=8, pady=3,
                                      command=self.save_settings)
        save_settings_btn.pack(side=tk.RIGHT, padx=5)
        
        # Load settings
        self.load_settings()
    
    def load_users(self):
        """Load users into the tree view"""
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
            
        try:
            # Load users from file
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    users = json.load(f)
                    
                # Add to treeview
                for username, user_data in users.items():
                    is_admin = user_data.get('is_admin', False)
                    name = user_data.get('name', '')
                    
                    self.users_tree.insert("", tk.END, values=(
                        username,
                        name,
                        "Yes" if is_admin else "No"
                    ))
                    
                # Apply alternating row colors
                self._apply_row_colors(self.users_tree)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users: {str(e)}")
    
    def load_settings(self):
        """Load settings into the UI"""
        try:
            # Clear existing items
            for item in self.site_tree.get_children():
                self.site_tree.delete(item)
                
            for item in self.agency_tree.get_children():
                self.agency_tree.delete(item)
                
            # Load settings from file
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    
                # Add site names to treeview
                for site in settings.get('site_names', []):
                    self.site_tree.insert("", tk.END, values=(site,))
                    
                # Add agency names to treeview
                for agency in settings.get('agency_names', []):
                    self.agency_tree.insert("", tk.END, values=(agency,))
                    
                # Apply alternating row colors
                self._apply_row_colors(self.site_tree)
                self._apply_row_colors(self.agency_tree)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
    
    def _apply_row_colors(self, tree):
        """Apply alternating row colors to treeview"""
        for i, item in enumerate(tree.get_children()):
            if i % 2 == 0:
                tree.item(item, tags=("evenrow",))
            else:
                tree.item(item, tags=("oddrow",))
        
        tree.tag_configure("evenrow", background=config.COLORS["table_row_even"])
        tree.tag_configure("oddrow", background=config.COLORS["table_row_odd"])
    
    def on_user_select(self, event):
        """Handle user selection in the treeview"""
        selected_items = self.users_tree.selection()
        if not selected_items:
            return
            
        # Get user data
        item = selected_items[0]
        username = self.users_tree.item(item, 'values')[0]
        
        try:
            # Load user details
            with open(self.users_file, 'r') as f:
                users = json.load(f)
                
            if username in users:
                user_data = users[username]
                
                # Set form fields
                self.username_var.set(username)
                self.fullname_var.set(user_data.get('name', ''))
                self.is_admin_var.set(user_data.get('is_admin', False))
                
                # Clear password fields
                self.password_var.set("")
                self.confirm_password_var.set("")
                
                # Disable username field for editing
                self.username_entry.configure(state="disabled")
                
                # Set edit mode
                self.edit_mode = True
                
                # Set status
                self.status_var.set("Editing user: " + username)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load user details: {str(e)}")
    
    def new_user(self):
        """Set up form for a new user"""
        # Clear form
        self.clear_form()
        
        # Enable username field
        self.username_entry.configure(state="normal")
        
        # Set edit mode
        self.edit_mode = False
        
        # Set status
        self.status_var.set("Creating new user")
    
    def save_user(self):
        """Save user to file"""
        # Get form data
        username = self.username_var.get().strip()
        fullname = self.fullname_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()
        is_admin = self.is_admin_var.get()
        
        # Validate inputs
        if not username:
            messagebox.showerror("Validation Error", "Username is required")
            return
            
        if not fullname:
            messagebox.showerror("Validation Error", "Full name is required")
            return
            
        # Check username format (alphanumeric)
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            messagebox.showerror("Validation Error", "Username must be alphanumeric")
            return
            
        # Check if password is required (new user or password change)
        if not self.edit_mode or password:
            if not password:
                messagebox.showerror("Validation Error", "Password is required")
                return
                
            if password != confirm_password:
                messagebox.showerror("Validation Error", "Passwords do not match")
                return
                
            if len(password) < 4:
                messagebox.showerror("Validation Error", "Password must be at least 4 characters")
                return
        
        try:
            # Load existing users
            users = {}
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    users = json.load(f)
            
            # Check if username exists (for new user)
            if not self.edit_mode and username in users:
                messagebox.showerror("Error", "Username already exists")
                return
                
            # Prepare user data
            user_data = {
                "name": fullname,
                "is_admin": is_admin
            }
            
            # Set password if provided
            if password:
                user_data["password"] = self.hash_password(password)
            elif self.edit_mode and username in users:
                # Keep existing password
                user_data["password"] = users[username]["password"]
            
            # Save user
            users[username] = user_data
            
            # Write to file
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=4)
            
            # Refresh user list
            self.load_users()
            
            # Clear form
            self.clear_form()
            
            # Show success message
            messagebox.showinfo("Success", f"User '{username}' saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save user: {str(e)}")
    
    def delete_user(self):
        """Delete selected user"""
        selected_items = self.users_tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select a user to delete")
            return
            
        # Get user data
        item = selected_items[0]
        username = self.users_tree.item(item, 'values')[0]
        
        # Prevent deleting the last admin user
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
                
            # Count admin users
            admin_count = sum(1 for u, data in users.items() if data.get('is_admin', False))
            
            # Check if attempting to delete the last admin
            if users.get(username, {}).get('is_admin', False) and admin_count <= 1:
                messagebox.showerror("Error", "Cannot delete the last admin user")
                return
                
            # Confirm deletion
            confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete user '{username}'?")
            if not confirm:
                return
                
            # Delete user
            if username in users:
                del users[username]
                
                # Write to file
                with open(self.users_file, 'w') as f:
                    json.dump(users, f, indent=4)
                
                # Refresh user list
                self.load_users()
                
                # Clear form if deleted user was being edited
                if self.username_var.get() == username:
                    self.clear_form()
                
                # Show success message
                messagebox.showinfo("Success", f"User '{username}' deleted successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
    
    def clear_form(self):
        """Clear user form"""
        # Clear variables
        self.username_var.set("")
        self.fullname_var.set("")
        self.password_var.set("")
        self.confirm_password_var.set("")
        self.is_admin_var.set(False)
        
        # Reset edit mode
        self.edit_mode = False
        
        # Enable username field for new user
        self.username_entry.configure(state="normal")
        
        # Clear status
        self.status_var.set("")
    
    def add_site(self):
        """Add a new site to the list"""
        site_name = self.site_name_var.get().strip()
        if not site_name:
            messagebox.showerror("Error", "Site name cannot be empty")
            return
            
        # Check if site already exists
        for item in self.site_tree.get_children():
            if self.site_tree.item(item, 'values')[0] == site_name:
                messagebox.showerror("Error", "Site name already exists")
                return
                
        # Add to treeview
        self.site_tree.insert("", tk.END, values=(site_name,))
        
        # Apply alternating row colors
        self._apply_row_colors(self.site_tree)
        
        # Clear entry
        self.site_name_var.set("")
    
    def delete_site(self):
        """Delete selected site"""
        selected_items = self.site_tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select a site to delete")
            return
            
        # Prevent deleting the last site
        if len(self.site_tree.get_children()) <= 1:
            messagebox.showerror("Error", "Cannot delete the last site")
            return
            
        # Delete selected site
        for item in selected_items:
            self.site_tree.delete(item)
            
        # Apply alternating row colors
        self._apply_row_colors(self.site_tree)
    
    def add_agency(self):
        """Add a new agency to the list"""
        agency_name = self.agency_name_var.get().strip()
        if not agency_name:
            messagebox.showerror("Error", "Agency name cannot be empty")
            return
            
        # Check if agency already exists
        for item in self.agency_tree.get_children():
            if self.agency_tree.item(item, 'values')[0] == agency_name:
                messagebox.showerror("Error", "Agency name already exists")
                return
                
        # Add to treeview
        self.agency_tree.insert("", tk.END, values=(agency_name,))
        
        # Apply alternating row colors
        self._apply_row_colors(self.agency_tree)
        
        # Clear entry
        self.agency_name_var.set("")
    
    def delete_agency(self):
        """Delete selected agency"""
        selected_items = self.agency_tree.selection()
        if not selected_items:
            messagebox.showinfo("Selection", "Please select an agency to delete")
            return
            
        # Delete selected agency
        for item in selected_items:
            self.agency_tree.delete(item)
            
        # Apply alternating row colors
        self._apply_row_colors(self.agency_tree)
    
    def save_settings(self):
        """Save settings to file"""
        try:
            # Get site names
            site_names = []
            for item in self.site_tree.get_children():
                site_names.append(self.site_tree.item(item, 'values')[0])
                
            # Get agency names
            agency_names = []
            for item in self.agency_tree.get_children():
                agency_names.append(self.agency_tree.item(item, 'values')[0])
                
            # Save settings
            settings = {
                "site_names": site_names,
                "agency_names": agency_names
            }
            
            # Write to file
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
                
            # If app instance is available, update form dropdowns
            if self.app and hasattr(self.app, 'update_form_options'):
                self.app.update_form_options(site_names, agency_names)
                
            # Show success message
            messagebox.showinfo("Success", "Settings saved successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username, password):
        """Authenticate user with username and password
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            tuple: (success, is_admin)
        """
        try:
            # Load users
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    users = json.load(f)
                    
                # Check if user exists
                if username in users:
                    user_data = users[username]
                    stored_hash = user_data.get('password', '')
                    
                    # Verify password
                    if stored_hash == self.hash_password(password):
                        # Set current user
                        self.current_user = username
                        self.is_admin = user_data.get('is_admin', False)
                        return True, self.is_admin
                    
            # Authentication failed
            return False, False
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False, False
    
    def get_settings(self):
        """Get current settings
        
        Returns:
            dict: Settings dictionary
        """
        settings = {
            "site_names": ["Guntur"],  # Default
            "agency_names": []
        }
        
        try:
            # Load settings from file
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            
        return settings