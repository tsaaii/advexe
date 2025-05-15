import tkinter as tk
import os
import datetime
import threading
from tkinter import ttk, messagebox

import config
from ui_components import HoverButton, create_styles
from camera import CameraView
from main_form import MainForm
from summary_panel import SummaryPanel
from settings_panel import SettingsPanel
from data_management import DataManager
from reports import export_to_excel, export_to_pdf
from admin_panel import AdminPanel
from app_login import LoginDialog
from pending_vehicles_panel import PendingVehiclesPanel

class TharuniApp:
    """Main application class with admin functionality"""
    
    def __init__(self, root):
        """Initialize the application with authentication
        
        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.root.title("Advitia Labs")
        self.root.geometry("900x580")  # Increased size to accommodate pending vehicles panel
        self.root.minsize(900, 580)    # Set minimum window size
        
        # Set up initial configuration
        config.setup()
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Initialize UI styles
        self.style = create_styles()
        
        # Initialize admin panel (for authentication)
        self.admin_panel = AdminPanel(None, self)
        
        # Show login dialog
        self.logged_in_user = None
        self.is_admin = False
        self.authenticate_user()
        
        # Initialize UI components if login successful
        if self.logged_in_user:
            self.create_widgets()
            
            # Start time update
            self.update_datetime()
            
            # Start periodic refresh for pending vehicles
            self.periodic_refresh()
            
            # Add window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def authenticate_user(self):
        """Show login dialog and authenticate user"""
        login = LoginDialog(self.root, self.admin_panel)
        
        if login.result:
            self.logged_in_user = login.username
            self.is_admin = login.is_admin
        else:
            # Exit application if login failed or canceled
            self.root.quit()
    
    def create_widgets(self):
        """Create all widgets and layout for the application"""
        # Create main container frame
        main_container = ttk.Frame(self.root, padding="5", style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title and header section
        self.create_header(main_container)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create tabs
        main_tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(main_tab, text="Vehicle Entry")
        
        summary_tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(summary_tab, text="Recent Entries")
        
        settings_tab = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(settings_tab, text="Settings")
        
        # Admin tab - only visible to admin users
        if self.is_admin:
            admin_tab = ttk.Frame(self.notebook, style="TFrame")
            self.notebook.add(admin_tab, text="Administration")
            
            # Create admin panel
            self.admin_panel = AdminPanel(admin_tab, self)
        
        # Main panel with scrollable frame for small screens
        self.create_main_panel(main_tab)
        
        # Create summary panel
        self.summary_panel = SummaryPanel(summary_tab, self.data_manager)
        
        # Create settings panel
        self.settings_panel = SettingsPanel(
            settings_tab, 
            weighbridge_callback=self.update_weight_from_weighbridge,
            update_cameras_callback=self.update_camera_indices
        )
        
        # Buttons at the bottom
        button_container = ttk.Frame(self.root, style="TFrame")
        button_container.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        self.create_buttons(button_container)
        
        # Update form options from admin settings
        self.update_form_options()
    
    def create_header(self, parent):
        """Create header with title, user info, and date/time"""
        # Title with company logo effect
        header_frame = ttk.Frame(parent, style="TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create a styled header with gradient-like background
        title_box = tk.Frame(header_frame, bg=config.COLORS["header_bg"], padx=10, pady=5)
        title_box.pack(fill=tk.X)
        
        title_label = tk.Label(title_box, 
                              text="Advitia Labs", 
                              font=("Segoe UI", 14, "bold"),
                              fg=config.COLORS["white"],
                              bg=config.COLORS["header_bg"])
        title_label.pack(side=tk.LEFT)
        
        # User info
        user_frame = tk.Frame(title_box, bg=config.COLORS["header_bg"])
        user_frame.pack(side=tk.LEFT, padx=20)
        
        user_label = tk.Label(user_frame, 
                           text=f"User: {self.logged_in_user}" + (" (Admin)" if self.is_admin else ""),
                           font=("Segoe UI", 9, "italic"),
                           fg=config.COLORS["white"],
                           bg=config.COLORS["header_bg"])
        user_label.pack(side=tk.LEFT)
        
        # Add logout button
        logout_btn = HoverButton(title_box, 
                               text="Logout", 
                               font=("Segoe UI", 9),
                               bg=config.COLORS["button_alt"],
                               fg=config.COLORS["white"],
                               padx=5, pady=1,
                               command=self.logout)
        logout_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Date and time frame (right side of header)
        datetime_frame = tk.Frame(title_box, bg=config.COLORS["header_bg"])
        datetime_frame.pack(side=tk.RIGHT)
        
        # Date and time variables
        self.date_var = tk.StringVar()
        self.time_var = tk.StringVar()
        
        date_label_desc = tk.Label(datetime_frame, text="Date:", 
                                  font=("Segoe UI", 9),
                                  fg=config.COLORS["white"],
                                  bg=config.COLORS["header_bg"])
        date_label_desc.grid(row=0, column=0, sticky="w", padx=(0, 2))
        
        date_label = tk.Label(datetime_frame, textvariable=self.date_var, 
                             font=("Segoe UI", 9, "bold"),
                             fg=config.COLORS["white"],
                             bg=config.COLORS["header_bg"])
        date_label.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        time_label_desc = tk.Label(datetime_frame, text="Time:", 
                                  font=("Segoe UI", 9),
                                  fg=config.COLORS["white"],
                                  bg=config.COLORS["header_bg"])
        time_label_desc.grid(row=0, column=2, sticky="w", padx=(0, 2))
        
        time_label = tk.Label(datetime_frame, textvariable=self.time_var, 
                             font=("Segoe UI", 9, "bold"),
                             fg=config.COLORS["white"],
                             bg=config.COLORS["header_bg"])
        time_label.grid(row=0, column=3, sticky="w")
    
    def create_main_panel(self, parent):
        """Create main panel with form and pending vehicles list"""
        # Main panel to hold everything with scrollable frame for small screens
        main_panel = ttk.Frame(parent, style="TFrame")
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Split the main panel into two parts: form and pending vehicles
        left_panel = ttk.Frame(main_panel, style="TFrame")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_panel = ttk.Frame(main_panel, style="TFrame")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        # Add a canvas with scrollbar for small screens on the left panel
        canvas = tk.Canvas(left_panel, bg=config.COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        
        # Create a frame that will contain the form and cameras
        scrollable_frame = ttk.Frame(canvas, style="TFrame")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Add the frame to the canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create the main form - pass data manager for ticket lookup
        self.main_form = MainForm(
            scrollable_frame, 
            notebook=self.notebook,
            summary_update_callback=self.update_summary,
            data_manager=self.data_manager
        )
        
        # Create the pending vehicles panel on the right
        self.pending_vehicles = PendingVehiclesPanel(
            right_panel,
            data_manager=self.data_manager,
            on_vehicle_select=self.load_pending_vehicle
        )
        
        # Configure scroll region after adding content
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def load_pending_vehicle(self, ticket_no):
        """Load a pending vehicle when selected from the pending vehicles panel"""
        if hasattr(self, 'main_form'):
            # Switch to main tab
            self.notebook.select(0)
            
            # Set the ticket number in the form
            self.main_form.rst_var.set(ticket_no)
            
            # Trigger the ticket existence check
            self.main_form.check_ticket_exists()
    
    def create_buttons(self, parent):
        """Create action buttons"""
        # Button bar
        button_frame = ttk.Frame(parent, style="TFrame")
        button_frame.pack(fill=tk.X, padx=10, pady=3)
        
        # Single row for buttons
        save_btn = HoverButton(button_frame, 
                              text="Save Record", 
                              font=("Segoe UI", 10, "bold"),
                              bg=config.COLORS["secondary"],
                              fg=config.COLORS["button_text"],
                              padx=8, pady=3,
                              command=self.save_record)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        view_btn = HoverButton(button_frame, 
                              text="View Records", 
                              font=("Segoe UI", 10),
                              bg=config.COLORS["primary"],
                              fg=config.COLORS["button_text"],
                              padx=8, pady=3,
                              command=self.view_records)
        view_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = HoverButton(button_frame, 
                               text="Clear", 
                               font=("Segoe UI", 10),
                               bg=config.COLORS["button_alt"],
                               fg=config.COLORS["button_text"],
                               padx=8, pady=3,
                               command=self.clear_form)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = HoverButton(button_frame, 
                              text="Exit", 
                              font=("Segoe UI", 10),
                              bg=config.COLORS["error"],
                              fg=config.COLORS["button_text"],
                              padx=8, pady=3,
                              command=self.on_closing)
        exit_btn.pack(side=tk.LEFT, padx=5)
    
    def update_datetime(self):
        """Update date and time display"""
        now = datetime.datetime.now()
        self.date_var.set(now.strftime("%d-%m-%Y"))
        self.time_var.set(now.strftime("%H:%M:%S"))
        self.root.after(1000, self.update_datetime)  # Update every second
    
    def periodic_refresh(self):
        """Periodically refresh data displays"""
        # Update pending vehicles list
        self.update_pending_vehicles()
        
        # Schedule next refresh
        self.root.after(60000, self.periodic_refresh)  # Refresh every minute
    
    def update_weight_from_weighbridge(self, weight):
        """Update weight from weighbridge"""
        # Make the weight available to the main form
        if hasattr(self, 'settings_panel'):
            self.settings_panel.current_weight_var.set(f"{weight} kg")
            
        # Notify the settings panel to update its display
        if hasattr(self, 'settings_panel'):
            self.settings_panel.update_weight_display(weight)
    
    def update_camera_indices(self, front_index, back_index):
        """Update camera indices"""
        if hasattr(self, 'main_form'):
            # Stop cameras if running
            if hasattr(self.main_form, 'front_camera'):
                self.main_form.front_camera.stop_camera()
                self.main_form.front_camera.camera_index = front_index
            
            if hasattr(self.main_form, 'back_camera'):
                self.main_form.back_camera.stop_camera()
                self.main_form.back_camera.camera_index = back_index
    
    def update_form_options(self, site_names=None, agency_names=None):
        """Update form dropdown options from admin settings"""
        # Get settings if not provided
        if site_names is None or agency_names is None:
            settings = self.admin_panel.get_settings()
            site_names = settings.get('site_names', ['Guntur'])
            agency_names = settings.get('agency_names', [])
        
        # Update main form if it exists
        if hasattr(self, 'main_form'):
            # Look for the form_frame (LabelFrame containing form components)
            form_frame = None
            for child in self.main_form.parent.winfo_children():
                if isinstance(child, ttk.LabelFrame) and "Vehicle Information" in child.cget("text"):
                    form_frame = child
                    break
            
            # If we found the form frame, look for its inner frame
            if form_frame:
                for child in form_frame.winfo_children():
                    if isinstance(child, ttk.Frame):
                        form_inner = child
                        
                        # Update site combobox - find it in row 1, column 0
                        for widget in form_inner.grid_slaves(row=1, column=0):
                            if isinstance(widget, ttk.Combobox):
                                # Update values
                                widget['values'] = tuple(site_names)
                                
                                # Store reference to this combo box
                                self.main_form.site_combo = widget
                                
                                # Set to first site if current value not in list
                                if self.main_form.site_var.get() not in site_names and site_names:
                                    self.main_form.site_var.set(site_names[0])
                                
                                break
                        
                        # Update agency field - find it in row 1, column 1
                        if agency_names:
                            for widget in form_inner.grid_slaves(row=1, column=1):
                                if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Combobox):
                                    # Get current value
                                    current_value = self.main_form.agency_var.get()
                                    
                                    # If entry, convert to combobox
                                    if isinstance(widget, ttk.Entry):
                                        # Destroy the entry
                                        widget.destroy()
                                        
                                        # Create combobox
                                        agency_combo = ttk.Combobox(
                                            form_inner, 
                                            textvariable=self.main_form.agency_var,
                                            values=tuple(agency_names),
                                            width=config.STD_WIDTH
                                        )
                                        agency_combo.grid(row=1, column=1, sticky=tk.W, padx=3, pady=3)
                                        
                                        # Store reference
                                        self.main_form.agency_combo = agency_combo
                                    else:
                                        # Just update values for existing combobox
                                        widget['values'] = tuple(agency_names)
                                        self.main_form.agency_combo = widget
                                    
                                    # Restore value if in new list
                                    if current_value in agency_names:
                                        self.main_form.agency_var.set(current_value)
                                    elif agency_names:
                                        self.main_form.agency_var.set(agency_names[0])
                                    
                                    break
                        
                        break
    
    def save_record(self):
        """Save current record to database"""
        # Validate form first
        if not self.main_form.validate_form():
            return
        
        # Get form data
        record_data = self.main_form.get_form_data()
        
        # Save to database
        if self.data_manager.save_record(record_data):
            # Show success message
            if record_data.get('second_weight') and record_data.get('second_timestamp'):
                # Both weighments complete
                messagebox.showinfo("Success", "Record completed with both weighments!")
            else:
                # Only first weighment
                messagebox.showinfo("Success", "First weighment saved! Vehicle added to pending queue.")
            
            # Update the summary and pending vehicles
            self.update_summary()
            self.update_pending_vehicles()
            
            # Generate a new ticket number for the next entry
            self.main_form.generate_next_ticket_number()
            
            # If second weighment is done, clear form for next entry
            if record_data.get('second_weight') and record_data.get('second_timestamp'):
                self.clear_form()
                # Switch to summary tab
                self.notebook.select(1)
            else:
                # For first weighment, just clear the vehicle number and images
                # but keep the ticket number and agency information
                self.main_form.vehicle_var.set("")
                self.main_form.front_image_path = None
                self.main_form.back_image_path = None
                self.main_form.front_image_status_var.set("Front: ✗")
                self.main_form.back_image_status_var.set("Back: ✗")
                self.main_form.front_image_status.config(foreground="red")
                self.main_form.back_image_status.config(foreground="red")
                
                # Reset camera displays if they were used
                if hasattr(self.main_form, 'front_camera'):
                    self.main_form.front_camera.stop_camera()
                    self.main_form.front_camera.captured_image = None
                    self.main_form.front_camera.canvas.delete("all")
                    self.main_form.front_camera.canvas.create_text(75, 60, text="Click Capture", fill="white", justify=tk.CENTER)
                    self.main_form.front_camera.capture_button.config(text="Capture")
                    
                if hasattr(self.main_form, 'back_camera'):
                    self.main_form.back_camera.stop_camera()
                    self.main_form.back_camera.captured_image = None
                    self.main_form.back_camera.canvas.delete("all")
                    self.main_form.back_camera.canvas.create_text(75, 60, text="Click Capture", fill="white", justify=tk.CENTER)
                    self.main_form.back_camera.capture_button.config(text="Capture")
                
                # Reset weighment state for next entry
                self.main_form.current_weighment = "first"
                self.main_form.first_weight_var.set("")
                self.main_form.first_timestamp_var.set("")
                self.main_form.second_weight_var.set("")
                self.main_form.second_timestamp_var.set("")
                self.main_form.net_weight_var.set("")
                self.main_form.first_weighment_btn.config(state=tk.NORMAL)
                self.main_form.second_weighment_btn.config(state=tk.DISABLED)
                
        else:
            messagebox.showerror("Error", "Failed to save record.")
    
    def update_summary(self):
        """Update the summary view"""
        if hasattr(self, 'summary_panel'):
            self.summary_panel.update_summary()
    
    def update_pending_vehicles(self):
        """Update the pending vehicles panel"""
        if hasattr(self, 'pending_vehicles'):
            self.pending_vehicles.refresh_pending_list()
    
    def view_records(self):
        """View all records in a separate window"""
        # Switch to the summary tab
        self.notebook.select(1)
        
        # Refresh the summary
        self.update_summary()
    
    def clear_form(self):
        """Clear the main form"""
        if hasattr(self, 'main_form'):
            self.main_form.clear_form()
    
    def logout(self):
        """Logout current user and show login dialog"""
        # Reset user info
        self.logged_in_user = None
        self.is_admin = False
        
        # Show login dialog
        self.authenticate_user()
        
        # Recreate UI if login successful
        if self.logged_in_user:
            # Destroy existing widgets
            for widget in self.root.winfo_children():
                widget.destroy()
                
            # Reinitialize UI
            self.create_widgets()
        else:
            # Exit application if login failed or canceled
            self.root.quit()
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Clean up resources
            if hasattr(self, 'main_form'):
                self.main_form.on_closing()
            
            if hasattr(self, 'settings_panel'):
                self.settings_panel.on_closing()
            
            # Close the application
            self.root.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            self.root.destroy()

# Main entry point
if __name__ == "__main__":
    # Create root window
    root = tk.Tk()
    
    # Create application instance
    app = TharuniApp(root)
    
    # Start the application
    root.mainloop()