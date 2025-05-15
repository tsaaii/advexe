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

class TharuniApp:
    """Main application class"""
    
    def __init__(self, root):
        """Initialize the application
        
        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.root.title("Advitia Labs")
        self.root.geometry("650x480")  # Reduced size for small windows
        self.root.minsize(650, 480)    # Set minimum window size
        
        # Set up initial configuration
        config.setup()
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Initialize UI styles
        self.style = create_styles()
        
        # Initialize UI components
        self.create_widgets()
        
        # Start time update
        self.update_datetime()
        
        # Add window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
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
    
    def create_header(self, parent):
        """Create header with title and date/time"""
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
        """Create main panel with scrollable frame"""
        # Main panel to hold everything with scrollable frame for small screens
        main_panel = ttk.Frame(parent, style="TFrame")
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Add a canvas with scrollbar for small screens
        canvas = tk.Canvas(main_panel, bg=config.COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_panel, orient="vertical", command=canvas.yview)
        
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
        
        # Create the main form
        self.main_form = MainForm(
            scrollable_frame, 
            notebook=self.notebook,
            summary_update_callback=self.update_summary
        )
        
        # Configure scroll region after adding content
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
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
    
    def update_weight_from_weighbridge(self, weight):
        """Update weight from weighbridge
        
        Args:
            weight: Weight value from weighbridge
        """
        # Update gross weight in the main form
        if hasattr(self, 'main_form'):
            self.main_form.gross_weight_var.set(str(weight))
            self.main_form.calculate_net_weight()
    
    def update_camera_indices(self, front_index, back_index):
        """Update camera indices
        
        Args:
            front_index: Front camera index
            back_index: Back camera index
        """
        if hasattr(self, 'main_form'):
            # Stop cameras if running
            if hasattr(self.main_form, 'front_camera'):
                self.main_form.front_camera.stop_camera()
                self.main_form.front_camera.camera_index = front_index
            
            if hasattr(self.main_form, 'back_camera'):
                self.main_form.back_camera.stop_camera()
                self.main_form.back_camera.camera_index = back_index
    
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
            messagebox.showinfo("Success", "Record saved successfully!")
            
            # Update the summary
            self.update_summary()
            
            # Switch to summary tab
            self.notebook.select(1)
            
            # Clear form for next entry
            self.clear_form()
        else:
            messagebox.showerror("Error", "Failed to save record.")
    
    def update_summary(self):
        """Update the summary view"""
        if hasattr(self, 'summary_panel'):
            self.summary_panel.update_summary()
    
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