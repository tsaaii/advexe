import tkinter as tk
from tkinter import ttk, messagebox, Canvas, Frame, simpledialog, filedialog
import csv
import os
import datetime
from pathlib import Path
import threading
import time
import cv2
from PIL import Image, ImageTk
import numpy as np
import serial
import serial.tools.list_ports
from collections import defaultdict
import re
import pandas as pd
import reportlab

# Global constants
DATA_FOLDER = 'data'
DATA_FILE = os.path.join(DATA_FOLDER, 'tharuni_data.csv')
IMAGES_FOLDER = os.path.join(DATA_FOLDER, 'images')
CSV_HEADER = ['Date', 'Time', 'Site Name', 'Agency Name', 'Material', 'Ticket No', 'Vehicle No', 
              'Transfer Party Name', 'Gross Weight', 'Tare Weight', 'Net Weight', 
              'Material Type', 'Front Image', 'Back Image']

# Refreshed color scheme
COLORS = {
    "primary": "#1E88E5",         # Brighter Blue
    "primary_light": "#BBDEFB",   # Lighter Blue
    "secondary": "#00BFA5",       # Teal
    "background": "#F5F7FA",      # Light Gray
    "text": "#212529",            # Dark Gray
    "white": "#FFFFFF",           # White
    "error": "#F44336",           # Red
    "warning": "#FFA000",         # Amber
    "header_bg": "#0D47A1",       # Darker Blue
    "button_hover": "#1565C0",    # Hover Blue
    "button_text": "#FFFFFF",     # Button Text (White)
    "form_bg": "#FFFFFF",         # Form Background
    "section_bg": "#F9FAFB",      # Section Background
    "button_alt": "#546E7A",      # Alternative button color
    "button_alt_hover": "#455A64", # Alternative button hover color
    "table_header_bg": "#E3F2FD", # Table header background
    "table_row_even": "#F5F5F5",  # Even row background
    "table_row_odd": "#FFFFFF",   # Odd row background
    "table_border": "#E0E0E0"     # Table border color
}

# Standard width for UI components - reduced for smaller windows
STD_WIDTH = 20

# Ensure data folder exists
Path(DATA_FOLDER).mkdir(exist_ok=True)
Path(IMAGES_FOLDER).mkdir(exist_ok=True)

# Create CSV file with header if it doesn't exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADER)

class HoverButton(tk.Button):
    """Button that changes color on hover"""
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.defaultBackground = self["background"]
        self.defaultForeground = self["foreground"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        """Mouse enters button"""
        if self["state"] != "disabled":
            if self.defaultBackground == COLORS["primary"]:
                self["background"] = COLORS["button_hover"]
            elif self.defaultBackground == COLORS["secondary"]:
                self["background"] = "#00A896"  # Darker teal
            elif self.defaultBackground == COLORS["button_alt"]:
                self["background"] = COLORS["button_alt_hover"]
            elif self.defaultBackground == COLORS["error"]:
                self["background"] = "#D32F2F"  # Darker red

    def on_leave(self, e):
        """Mouse leaves button"""
        if self["state"] != "disabled":
            self["background"] = self.defaultBackground

class CameraView:
    """Camera view widget with simplified interface"""
    def __init__(self, parent, camera_index=0):
        self.parent = parent
        self.camera_index = camera_index
        self.is_running = False
        self.captured_image = None
        self.cap = None
        
        # Create frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Video display - compact size
        self.canvas = tk.Canvas(self.frame, bg="black", width=150, height=120)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Draw message on canvas
        self.canvas.create_text(75, 60, text="Click Capture", fill="white", justify=tk.CENTER)
        
        # Controls frame
        controls = ttk.Frame(self.frame)
        controls.pack(fill=tk.X, padx=2, pady=2)
        
        # Buttons - using grid for better organization
        self.capture_button = HoverButton(controls, text="Capture", 
                                        bg=COLORS["primary"], fg=COLORS["button_text"],
                                        padx=2, pady=1, width=6,
                                        command=self.toggle_camera)
        self.capture_button.grid(row=0, column=0, padx=1, pady=1, sticky="ew")
        
        self.save_button = HoverButton(controls, text="Save", 
                                     bg=COLORS["secondary"], fg=COLORS["button_text"],
                                     padx=2, pady=1, width=6,
                                     command=self.save_image,
                                     state=tk.DISABLED)
        self.save_button.grid(row=0, column=1, padx=1, pady=1, sticky="ew")
        
        # Configure grid columns to be equal
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X, padx=2, pady=2)
        
        # Video thread
        self.video_thread = None
        
        # Save function reference - will be set by the main app
        self.save_function = None
        
    def toggle_camera(self):
        """Start or stop the camera"""
        if not self.is_running:
            self.start_camera()
            self.capture_button.config(text="Stop")
        else:
            self.stop_camera()
            self.capture_button.config(text="Capture")
    
    def start_camera(self):
        """Start the camera feed"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                messagebox.showerror("Camera Error", "Failed to open camera.")
                return
            
            # Set status
            self.status_var.set("Camera active")
            
            # Start video thread
            self.is_running = True
            self.video_thread = threading.Thread(target=self.update_frame)
            self.video_thread.daemon = True
            self.video_thread.start()
            
        except Exception as e:
            messagebox.showerror("Camera Error", f"Error starting camera: {str(e)}")
    
    def update_frame(self):
        """Update the video frame in a separate thread"""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    # Capture frame
                    self.captured_image = frame.copy()
                    
                    # Convert to RGB for tkinter
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Resize to fit smaller canvas
                    frame_resized = cv2.resize(frame_rgb, (150, 120))
                    # Convert to PhotoImage
                    img = Image.fromarray(frame_resized)
                    img_tk = ImageTk.PhotoImage(image=img)
                    
                    # Update canvas in main thread
                    if self.is_running:
                        self.parent.after_idle(lambda i=img_tk: self._update_canvas(i) if self.is_running else None)
                    
                    # Enable save button
                    if self.is_running:
                        self.parent.after_idle(self._enable_save)
                    
                    # Short delay
                    time.sleep(0.05)
                else:
                    # Camera disconnected
                    self.is_running = False
                    if self.parent.winfo_exists():
                        self.parent.after_idle(self._camera_error)
                    break
            except Exception as e:
                print(f"Camera error: {str(e)}")
                self.is_running = False
                if self.parent.winfo_exists():
                    self.parent.after_idle(self._camera_error)
                break
    
    def _enable_save(self):
        """Enable the save button from main thread"""
        if self.is_running:
            self.save_button.config(state=tk.NORMAL)
    
    def _update_canvas(self, img_tk):
        """Update canvas with new image (called from main thread)"""
        if self.is_running and self.parent.winfo_exists():
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            self.canvas.image = img_tk  # Keep reference
    
    def _camera_error(self):
        """Handle camera errors (called from main thread)"""
        if self.parent.winfo_exists():
            self.status_var.set("Camera error - please try again")
            self.stop_camera()
            self.capture_button.config(text="Capture")
    
    def save_image(self):
        """Call the save function provided by main app"""
        if self.save_function and self.captured_image is not None:
            if self.save_function(self.captured_image):
                # Stop the camera after successful save
                self.stop_camera()
                self.capture_button.config(text="Capture")
                self.save_button.config(state=tk.DISABLED)
                # Clear canvas and show saved message
                self.canvas.delete("all")
                self.canvas.create_text(75, 60, text="Image Saved\nClick Capture for new", 
                                      fill="white", justify=tk.CENTER)
        else:
            self.status_var.set("Please capture an image first")
    
    def stop_camera(self):
        """Stop the camera feed"""
        self.is_running = False
        
        # Wait for thread to complete
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(0.5)
        
        # Release camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Update status
        self.status_var.set("Ready")
        self.save_button.config(state=tk.DISABLED)

class TharuniApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advitia Labs")
        self.root.geometry("650x480")  # Reduced size for small windows
        self.root.minsize(650, 480)    # Set minimum window size
        
        # Initialize all attributes first
        self.initialize_attributes()
        
        # Set up styles with modern look
        self.create_styles()
        
        # Initialize UI
        self.create_widgets()
        
        # Start time update
        self.update_datetime()
        
        # Add window close handler to properly close camera
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def initialize_attributes(self):
        """Initialize all class attributes"""
        # Create variables for form fields
        self.site_var = tk.StringVar(value="Guntur")
        self.agency_var = tk.StringVar()  # Renamed from party_var
        self.material_var = tk.StringVar(value="MSW")
        self.rst_var = tk.StringVar()
        self.vehicle_var = tk.StringVar()
        self.tpt_var = tk.StringVar(value="Advitia Labs")  # Now "Transfer Party Name"
        self.gross_weight_var = tk.StringVar()
        self.tare_weight_var = tk.StringVar()
        self.net_weight_var = tk.StringVar()
        
        # Material type tracking
        self.material_type_var = tk.StringVar(value="Inert")
        
        # Date and time variables
        self.date_var = tk.StringVar()
        self.time_var = tk.StringVar()
        
        # Weighbridge settings
        self.weighbridge_connected = False
        self.serial_port = None
        self.weight_buffer = []
        self.weight_processing = False
        self.weight_thread = None
        self.weight_update_thread = None
        
        # Saved image paths
        self.front_image_path = None
        self.back_image_path = None
        
        # Camera lock to prevent both cameras from being used simultaneously
        self.camera_lock = threading.Lock()
        
    def create_styles(self):
        """Create styles for widgets"""
        self.style = ttk.Style()
        
        # Configure theme
        self.style.theme_use('clam')
        
        # Label styles
        self.style.configure("TLabel", 
                            font=("Segoe UI", 9),
                            background=COLORS["background"],
                            foreground=COLORS["text"])
        
        # Title label style
        self.style.configure("Title.TLabel", 
                           font=("Segoe UI", 14, "bold"),
                           foreground=COLORS["primary"],
                           background=COLORS["background"])
        
        # Subtitle label style
        self.style.configure("Subtitle.TLabel", 
                           font=("Segoe UI", 11, "bold"),
                           foreground=COLORS["primary"],
                           background=COLORS["background"])
        
        # Entry style
        self.style.configure("TEntry", 
                           font=("Segoe UI", 9),
                           fieldbackground=COLORS["white"])
        self.style.map("TEntry",
                     fieldbackground=[("readonly", COLORS["primary_light"])])
        
        # Combobox style
        self.style.configure("TCombobox", 
                           font=("Segoe UI", 9))
        
        # Button style
        self.style.configure("TButton", 
                           font=("Segoe UI", 9, "bold"),
                           background=COLORS["primary"],
                           foreground=COLORS["button_text"])
        self.style.map("TButton",
                     background=[("active", COLORS["button_hover"])])
        
        # Frame style
        self.style.configure("TFrame", 
                           background=COLORS["background"])
        
        # LabelFrame style
        self.style.configure("TLabelframe", 
                           font=("Segoe UI", 9, "bold"),
                           background=COLORS["form_bg"])
        self.style.configure("TLabelframe.Label", 
                           font=("Segoe UI", 9, "bold"),
                           foreground=COLORS["primary"],
                           background=COLORS["background"])
                           
        # Notebook style
        self.style.configure("TNotebook", 
                          background=COLORS["background"],
                          tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", 
                          font=("Segoe UI", 9),
                          background=COLORS["primary_light"],
                          foreground=COLORS["text"],
                          padding=[8, 3])
        self.style.map("TNotebook.Tab",
                    background=[("selected", COLORS["primary"])],
                    foreground=[("selected", COLORS["white"])])
        
        # Treeview style
        self.style.configure("Treeview", 
                          font=("Segoe UI", 9),
                          background=COLORS["white"],
                          foreground=COLORS["text"],
                          fieldbackground=COLORS["white"])
        self.style.configure("Treeview.Heading", 
                          font=("Segoe UI", 9, "bold"),
                          background=COLORS["table_header_bg"],
                          foreground=COLORS["text"])
        self.style.map("Treeview",
                    background=[("selected", COLORS["primary_light"])],
                    foreground=[("selected", COLORS["primary"])])
        
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
        
        # Create the main form layout with better organization
        self.create_main_form_layout(main_tab)
        
        # Create summary in summary tab
        self.create_summary_panel(summary_tab)
        
        # Create settings panel
        self.create_settings_panel(settings_tab)
        
        # Buttons at the bottom in their own frame to ensure visibility
        button_container = ttk.Frame(self.root, style="TFrame")
        button_container.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        self.create_buttons(button_container)
        
    def create_header(self, parent):
        """Create compact title and date/time display"""
        # Title with company logo effect
        header_frame = ttk.Frame(parent, style="TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create a styled header with gradient-like background
        title_box = tk.Frame(header_frame, bg=COLORS["header_bg"], padx=10, pady=5)
        title_box.pack(fill=tk.X)
        
        title_label = tk.Label(title_box, 
                              text="Advitia Labs", 
                              font=("Segoe UI", 14, "bold"),
                              fg=COLORS["white"],
                              bg=COLORS["header_bg"])
        title_label.pack(side=tk.LEFT)
        
        # Date and time frame (right side of header)
        datetime_frame = tk.Frame(title_box, bg=COLORS["header_bg"])
        datetime_frame.pack(side=tk.RIGHT)
        
        date_label_desc = tk.Label(datetime_frame, text="Date:", 
                                  font=("Segoe UI", 9),
                                  fg=COLORS["white"],
                                  bg=COLORS["header_bg"])
        date_label_desc.grid(row=0, column=0, sticky="w", padx=(0, 2))
        
        date_label = tk.Label(datetime_frame, textvariable=self.date_var, 
                             font=("Segoe UI", 9, "bold"),
                             fg=COLORS["white"],
                             bg=COLORS["header_bg"])
        date_label.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        time_label_desc = tk.Label(datetime_frame, text="Time:", 
                                  font=("Segoe UI", 9),
                                  fg=COLORS["white"],
                                  bg=COLORS["header_bg"])
        time_label_desc.grid(row=0, column=2, sticky="w", padx=(0, 2))
        
        time_label = tk.Label(datetime_frame, textvariable=self.time_var, 
                             font=("Segoe UI", 9, "bold"),
                             fg=COLORS["white"],
                             bg=COLORS["header_bg"])
        time_label.grid(row=0, column=3, sticky="w")
    
    def create_main_form_layout(self, parent):
        """Create a better organized main form with cameras below"""
        # Main panel to hold everything with scrollable frame for small screens
        main_panel = ttk.Frame(parent, style="TFrame")
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Add a canvas with scrollbar for small screens
        canvas = tk.Canvas(main_panel, bg=COLORS["background"], highlightthickness=0)
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
        
        # Create vehicle information form (optimized layout)
        self.create_form(scrollable_frame)
        
        # Create cameras panel below form
        self.create_cameras_panel(scrollable_frame)
        
        # Configure scroll region after adding content
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))


    def create_form(self, parent):
        """Create the main data entry form with 3x3 layout"""
        # Vehicle Information Frame
        form_frame = ttk.LabelFrame(parent, text="Vehicle Information")
        form_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Set background color for better visibility
        form_inner = ttk.Frame(form_frame, style="TFrame")
        form_inner.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # Create 3x3 grid layout
        # Configure grid columns for better distribution
        for i in range(3):  # 3 columns
            form_inner.columnconfigure(i, weight=1)  # Equal weight
        
        # Row 0: First row of labels
        # Site Name - Column 0
        ttk.Label(form_inner, text="Site Name:").grid(row=0, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Agency Name (moved from row 4) - Column 1
        ttk.Label(form_inner, text="Agency Name:").grid(row=0, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Material - Column 2
        ttk.Label(form_inner, text="Input Material").grid(row=0, column=2, sticky=tk.W, padx=3, pady=3)
        
        # Row 1: First row of entries
        # Site Name Entry - Column 0
        site_combo = ttk.Combobox(form_inner, textvariable=self.site_var, state="readonly", width=STD_WIDTH)
        site_combo['values'] = ('Guntur',)
        site_combo.grid(row=1, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Agency Name Entry (moved from row 5) - Column 1
        ttk.Entry(form_inner, textvariable=self.agency_var, width=STD_WIDTH).grid(row=1, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Material Combo Box - Column 2
        material_combo = ttk.Combobox(form_inner, textvariable=self.material_var, state="readonly", width=STD_WIDTH)
        material_combo['values'] = ('MSW')
        material_combo.grid(row=1, column=2, sticky=tk.W, padx=3, pady=3)
        
        # Row 2: Second row of labels
        # Ticket No - Column 0
        ttk.Label(form_inner, text="Ticket No:").grid(row=2, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Vehicle No - Column 1
        ttk.Label(form_inner, text="Vehicle No:").grid(row=2, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Transfer Party Name (renamed from TPT) - Column 2
        ttk.Label(form_inner, text="Transfer Party Name:").grid(row=2, column=2, sticky=tk.W, padx=3, pady=3)
        
        # Row 3: Second row of entries
        # Ticket No Entry - Column 0
        ttk.Entry(form_inner, textvariable=self.rst_var, width=STD_WIDTH).grid(row=3, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Vehicle No Entry - Column 1
        vehicle_entry = ttk.Entry(form_inner, textvariable=self.vehicle_var, width=STD_WIDTH)
        vehicle_entry.grid(row=3, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Transfer Party Name Entry - Column 2
        tpt_entry = ttk.Entry(form_inner, textvariable=self.tpt_var, width=STD_WIDTH)
        tpt_entry.grid(row=3, column=2, sticky=tk.W, padx=3, pady=3)
        tpt_entry.configure(state="readonly")
        
        # Row 4: Third row of labels
        # Material Type - Column 0
        ttk.Label(form_inner, text="Material Type:").grid(row=4, column=0, sticky=tk.W, padx=3, pady=3)
        
        # GROSS WEIGHT - Column 1
        ttk.Label(form_inner, text="GROSS WEIGHT:").grid(row=4, column=1, sticky=tk.W, padx=3, pady=3)
        
        # TARE WEIGHT - Column 2
        ttk.Label(form_inner, text="TARE WEIGHT:").grid(row=4, column=2, sticky=tk.W, padx=3, pady=3)
        
        # Row 5: Third row of entries
        # Material Type Combo - Column 0
        material_type_combo = ttk.Combobox(form_inner, 
                                         textvariable=self.material_type_var, 
                                         state="readonly", 
                                         width=STD_WIDTH)
        # Removed 'Scrap' from the list of material types
        material_type_combo['values'] = ('Inert', 'Soil', 'Construction and Demolition', 
                                       'RDF(REFUSE DERIVED FUEL)')
        material_type_combo.grid(row=5, column=0, sticky=tk.W, padx=3, pady=3)
        
        # GROSS WEIGHT Entry - Column 1
        gross_entry = ttk.Entry(form_inner, width=STD_WIDTH)
        gross_entry.grid(row=5, column=1, sticky=tk.W, padx=3, pady=3)
        gross_entry.config(textvariable=self.gross_weight_var)
        gross_entry.bind("<KeyRelease>", self.calculate_net_weight)
        
        # TARE WEIGHT Entry - Column 2
        tare_entry = ttk.Entry(form_inner, width=STD_WIDTH)
        tare_entry.grid(row=5, column=2, sticky=tk.W, padx=3, pady=3)
        tare_entry.config(textvariable=self.tare_weight_var)
        tare_entry.bind("<KeyRelease>", self.calculate_net_weight)
        
        # Row 6: NET WEIGHT label
        ttk.Label(form_inner, text="NET WEIGHT:").grid(row=6, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Row 7: NET WEIGHT entry
        net_entry = ttk.Entry(form_inner, textvariable=self.net_weight_var, state="readonly", width=STD_WIDTH)
        net_entry.grid(row=7, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Image status indicators
        image_status_frame = ttk.Frame(form_inner)
        image_status_frame.grid(row=8, column=0, columnspan=3, sticky=tk.W, padx=3, pady=3)
        
        ttk.Label(image_status_frame, text="Images:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.front_image_status_var = tk.StringVar(value="Front: ✗")
        self.front_image_status = ttk.Label(image_status_frame, textvariable=self.front_image_status_var, foreground="red")
        self.front_image_status.pack(side=tk.LEFT, padx=(0, 5))
        
        self.back_image_status_var = tk.StringVar(value="Back: ✗")
        self.back_image_status = ttk.Label(image_status_frame, textvariable=self.back_image_status_var, foreground="red")
        self.back_image_status.pack(side=tk.LEFT)
    
    def create_cameras_panel(self, parent):
        """Create the cameras panel with cameras side by side"""
        # Camera container with compact layout
        camera_frame = ttk.LabelFrame(parent, text="Camera Capture")
        camera_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Container for both cameras side by side
        cameras_container = ttk.Frame(camera_frame, style="TFrame")
        cameras_container.pack(fill=tk.X, padx=5, pady=5)
        cameras_container.columnconfigure(0, weight=1)
        cameras_container.columnconfigure(1, weight=1)
        
        # Front camera
        front_panel = ttk.Frame(cameras_container, style="TFrame")
        front_panel.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
        
        # Front camera title
        ttk.Label(front_panel, text="Front Camera").pack(anchor=tk.W, pady=2)
        
        # Create front camera (without redundant title in camera view)
        self.front_camera = CameraView(front_panel)
        self.front_camera.save_function = self.save_front_image
        
        # Back camera
        back_panel = ttk.Frame(cameras_container, style="TFrame")
        back_panel.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
        
        # Back Camera title
        ttk.Label(back_panel, text="Back Camera").pack(anchor=tk.W, pady=2)
        
        # Create back camera (without redundant title in camera view)
        self.back_camera = CameraView(back_panel)
        self.back_camera.save_function = self.save_back_image

    def create_settings_panel(self, parent):
        """Create settings panel for camera and weighbridge configuration"""
        # Main settings frame
        settings_frame = ttk.Frame(parent, style="TFrame")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook for different settings sections
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Weighbridge settings tab
        weighbridge_tab = ttk.Frame(settings_notebook, style="TFrame")
        settings_notebook.add(weighbridge_tab, text="Weighbridge")
        
        # Camera settings tab
        camera_tab = ttk.Frame(settings_notebook, style="TFrame")
        settings_notebook.add(camera_tab, text="Cameras")
        
        # Create weighbridge settings
        self.create_weighbridge_settings(weighbridge_tab)
        
        # Create camera settings
        self.create_camera_settings(camera_tab)
    
    def create_weighbridge_settings(self, parent):
        """Create weighbridge configuration settings"""
        # Weighbridge settings frame
        wb_frame = ttk.LabelFrame(parent, text="Weighbridge Configuration", padding=10)
        wb_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # COM Port selection
        ttk.Label(wb_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.com_port_var = tk.StringVar()
        self.com_port_combo = ttk.Combobox(wb_frame, textvariable=self.com_port_var, state="readonly")
        self.com_port_combo.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        self.refresh_com_ports()
        
        # Refresh COM ports button
        refresh_btn = HoverButton(wb_frame, text="Refresh Ports", bg=COLORS["primary_light"], 
                                 fg=COLORS["text"], padx=5, pady=2,
                                 command=self.refresh_com_ports)
        refresh_btn.grid(row=0, column=2, padx=5, pady=2)
        
        # Baud rate
        ttk.Label(wb_frame, text="Baud Rate:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.baud_rate_var = tk.IntVar(value=9600)
        baud_rates = [600, 1200, 2400, 4800, 9600, 14400, 19200, 57600, 115200]
        ttk.Combobox(wb_frame, textvariable=self.baud_rate_var, values=baud_rates, 
                    state="readonly").grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Data bits
        ttk.Label(wb_frame, text="Data Bits:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.data_bits_var = tk.IntVar(value=8)
        ttk.Combobox(wb_frame, textvariable=self.data_bits_var, values=[5, 6, 7, 8], 
                    state="readonly").grid(row=2, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Parity
        ttk.Label(wb_frame, text="Parity:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.parity_var = tk.StringVar(value="None")
        ttk.Combobox(wb_frame, textvariable=self.parity_var, 
                    values=["None", "Odd", "Even", "Mark", "Space"], 
                    state="readonly").grid(row=3, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Stop bits
        ttk.Label(wb_frame, text="Stop Bits:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.stop_bits_var = tk.DoubleVar(value=1.0)
        ttk.Combobox(wb_frame, textvariable=self.stop_bits_var, values=[1.0, 1.5, 2.0], 
                    state="readonly").grid(row=4, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Connection buttons
        btn_frame = ttk.Frame(wb_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.connect_btn = HoverButton(btn_frame, text="Connect", bg=COLORS["secondary"], 
                                     fg=COLORS["button_text"], padx=10, pady=3,
                                     command=self.connect_weighbridge)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = HoverButton(btn_frame, text="Disconnect", bg=COLORS["error"], 
                                        fg=COLORS["button_text"], padx=10, pady=3,
                                        command=self.disconnect_weighbridge, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.wb_status_var = tk.StringVar(value="Status: Disconnected")
        ttk.Label(wb_frame, textvariable=self.wb_status_var, 
                foreground="red").grid(row=6, column=0, columnspan=3, sticky=tk.W)
        
        # Test weight display
        ttk.Label(wb_frame, text="Current Weight:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.current_weight_var = tk.StringVar(value="0 kg")
        ttk.Label(wb_frame, textvariable=self.current_weight_var, 
                 font=("Segoe UI", 10, "bold")).grid(row=7, column=1, sticky=tk.W, pady=2)
    
    def create_camera_settings(self, parent):
        """Create camera configuration settings"""
        # Camera settings frame
        cam_frame = ttk.LabelFrame(parent, text="Camera Configuration", padding=10)
        cam_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Front camera index
        ttk.Label(cam_frame, text="Front Camera Index:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.front_cam_index_var = tk.IntVar(value=0)
        ttk.Combobox(cam_frame, textvariable=self.front_cam_index_var, 
                    values=[0, 1, 2, 3], state="readonly").grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Back camera index
        ttk.Label(cam_frame, text="Back Camera Index:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.back_cam_index_var = tk.IntVar(value=0)
        ttk.Combobox(cam_frame, textvariable=self.back_cam_index_var, 
                    values=[0, 1, 2, 3], state="readonly").grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Apply button
        apply_btn = HoverButton(cam_frame, text="Apply Settings", bg=COLORS["primary"], 
                               fg=COLORS["button_text"], padx=10, pady=3,
                               command=self.apply_camera_settings)
        apply_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Status message
        self.cam_status_var = tk.StringVar()
        ttk.Label(cam_frame, textvariable=self.cam_status_var, 
                foreground=COLORS["primary"]).grid(row=3, column=0, columnspan=2, sticky=tk.W)
    
    def refresh_com_ports(self):
        """Refresh available COM ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_port_combo['values'] = ports
        if ports:
            self.com_port_combo.current(0)
    
    def connect_weighbridge(self):
        """Connect to weighbridge with current settings"""
        com_port = self.com_port_var.get()
        if not com_port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        
        try:
            # Get serial connection parameters
            baud_rate = self.baud_rate_var.get()
            data_bits = self.data_bits_var.get()
            parity = self.parity_var.get().upper()[0]  # Convert to serial.PARITY_* format
            stop_bits = self.stop_bits_var.get()
            
            # Convert parity to serial.PARITY_* value
            parity_map = {
                'N': serial.PARITY_NONE,
                'O': serial.PARITY_ODD,
                'E': serial.PARITY_EVEN,
                'M': serial.PARITY_MARK,
                'S': serial.PARITY_SPACE
            }
            parity = parity_map.get(parity, serial.PARITY_NONE)
            
            # Convert stop bits
            stop_bits_map = {
                1.0: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2.0: serial.STOPBITS_TWO
            }
            stop_bits = stop_bits_map.get(stop_bits, serial.STOPBITS_ONE)
            
            # Create serial connection
            self.serial_port = serial.Serial(
                port=com_port,
                baudrate=baud_rate,
                bytesize=data_bits,
                parity=parity,
                stopbits=stop_bits,
                timeout=1
            )
            
            # Update UI
            self.weighbridge_connected = True
            self.wb_status_var.set("Status: Connected")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            
            # Start weight reading thread
            self.weight_thread = threading.Thread(target=self.read_weighbridge_data, daemon=True)
            self.weight_thread.start()
            
            # Start weight processing thread
            self.weight_processing = True
            self.weight_update_thread = threading.Thread(target=self.process_weighbridge_data, daemon=True)
            self.weight_update_thread.start()
            
            messagebox.showinfo("Success", "Weighbridge connected successfully!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to weighbridge:\n{str(e)}")
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None

    def disconnect_weighbridge(self):
        """Disconnect from weighbridge"""
        try:
            self.weight_processing = False
            self.weighbridge_connected = False
            
            if self.weight_thread and self.weight_thread.is_alive():
                self.weight_thread.join(1.0)
                
            if self.weight_update_thread and self.weight_update_thread.is_alive():
                self.weight_update_thread.join(1.0)
                
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
                
            # Update UI
            self.wb_status_var.set("Status: Disconnected")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.current_weight_var.set("0 kg")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error disconnecting weighbridge:\n{str(e)}")
    
    def read_weighbridge_data(self):
        """Read data from weighbridge in a separate thread"""
        while self.weighbridge_connected and self.serial_port:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        self.weight_buffer.append(line)
            except Exception as e:
                print(f"Weighbridge read error: {str(e)}")
                time.sleep(0.1)
    
    def process_weighbridge_data(self):
        """Process weighbridge data to find most common valid weight"""
        while self.weight_processing:
            try:
                if not self.weight_buffer:
                    time.sleep(0.1)
                    continue
                
                # Process data in 20-second windows
                start_time = time.time()
                window_data = []
                
                while time.time() - start_time < 20 and self.weight_processing:
                    if self.weight_buffer:
                        line = self.weight_buffer.pop(0)
                        # Clean the line - remove special characters
                        cleaned = re.sub(r'[^\d.]', '', line)
                        # Find all sequences of digits (with optional decimal point)
                        matches = re.findall(r'\d+\.?\d*', cleaned)
                        for match in matches:
                            if len(match) >= 6:  # At least 6 digits
                                try:
                                    weight = float(match)
                                    window_data.append(weight)
                                except ValueError:
                                    pass
                    time.sleep(0.05)
                
                if window_data:
                    # Find the most common weight in the window
                    freq = defaultdict(int)
                    for weight in window_data:
                        freq[weight] += 1
                    
                    if freq:
                        most_common = max(freq.items(), key=lambda x: x[1])[0]
                        # Update the UI with the new weight
                        self.root.after(0, self.update_weight_display, most_common)
                
            except Exception as e:
                print(f"Weight processing error: {str(e)}")
                time.sleep(1)
    
    def update_weight_display(self, weight):
        """Update the weight display in the UI"""
        self.current_weight_var.set(f"{weight:.2f} kg")
        self.gross_weight_var.set(str(weight))
        self.calculate_net_weight()
    
    def apply_camera_settings(self):
        """Apply camera index settings"""
        front_index = self.front_cam_index_var.get()
        back_index = self.back_cam_index_var.get()
        
        # Stop any running cameras
        if hasattr(self, 'front_camera'):
            self.front_camera.stop_camera()
        if hasattr(self, 'back_camera'):
            self.back_camera.stop_camera()
        
        # Update camera indices
        self.front_camera.camera_index = front_index
        self.back_camera.camera_index = back_index
        
        self.cam_status_var.set("Camera settings applied. Changes take effect on next capture.")
    
    def create_buttons(self, parent):
        """Create action buttons in a single row with fixed location at bottom"""
        # Fixed position button bar
        button_frame = ttk.Frame(parent, style="TFrame")
        button_frame.pack(fill=tk.X, padx=10, pady=3)
        
        # Single row for buttons
        save_btn = HoverButton(button_frame, 
                              text="Save Record", 
                              font=("Segoe UI", 10, "bold"),
                              bg=COLORS["secondary"],
                              fg=COLORS["button_text"],
                              padx=8, pady=3,
                              command=self.save_record)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        view_btn = HoverButton(button_frame, 
                              text="View Records", 
                              font=("Segoe UI", 10),
                              bg=COLORS["primary"],
                              fg=COLORS["button_text"],
                              padx=8, pady=3,
                              command=self.view_records)
        view_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = HoverButton(button_frame, 
                               text="Clear", 
                               font=("Segoe UI", 10),
                               bg=COLORS["button_alt"],
                               fg=COLORS["button_text"],
                               padx=8, pady=3,
                               command=self.clear_form)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = HoverButton(button_frame, 
                              text="Exit", 
                              font=("Segoe UI", 10),
                              bg=COLORS["error"],
                              fg=COLORS["button_text"],
                              padx=8, pady=3,
                              command=self.on_closing)
        exit_btn.pack(side=tk.LEFT, padx=5)
    
    def update_datetime(self):
        """Update date and time display"""
        now = datetime.datetime.now()
        self.date_var.set(now.strftime("%d-%m-%Y"))
        self.time_var.set(now.strftime("%H:%M:%S"))
        self.root.after(1000, self.update_datetime)  # Update every second
    
    def calculate_net_weight(self, event=None):
        """Calculate net weight from gross and tare weight"""
        try:
            gross = float(self.gross_weight_var.get() or 0)
            tare = float(self.tare_weight_var.get() or 0)
            net = gross - tare
            self.net_weight_var.set(str(net))
        except ValueError:
            # Handle non-numeric input
            self.net_weight_var.set("")
    
    def add_watermark(self, image, text):
        """Add a watermark to an image with sitename, vehicle number and timestamp"""
        # Create a copy of the image
        result = image.copy()
        
        # Get image dimensions
        height, width = result.shape[:2]
        
        # Set up watermark text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (255, 255, 255)  # White color
        thickness = 2
        
        # Add semi-transparent overlay for better text visibility
        overlay = result.copy()
        cv2.rectangle(overlay, (0, height - 40), (width, height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, result, 0.5, 0, result)
        
        # Add text
        cv2.putText(result, text, (10, height - 15), font, font_scale, color, thickness)
        
        return result
    
    def save_front_image(self, captured_image=None):
        """Save the front view camera image with watermark"""
        if not self.validate_vehicle_number():
            return False
        
        # Use captured image or get from camera
        image = captured_image if captured_image is not None else self.front_camera.captured_image
        
        if image is not None:
            # Generate filename and watermark text
            site_name = self.site_var.get().replace(" ", "_")
            vehicle_no = self.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Watermark text
            watermark_text = f"{site_name} - {vehicle_no} - {timestamp}"
            
            # Add watermark
            watermarked_image = self.add_watermark(image, watermark_text)
            
            # Save file path
            filename = f"{site_name}_{vehicle_no}_{timestamp}_front.jpg"
            filepath = os.path.join(IMAGES_FOLDER, filename)
            
            # Save the image
            cv2.imwrite(filepath, watermarked_image)
            
            # Update status
            self.front_image_path = filepath
            self.front_image_status_var.set("Front: ✓")
            self.front_image_status.config(foreground="green")
            
            messagebox.showinfo("Success", "Front image saved!")
            return True
            
        return False
    
    def save_back_image(self, captured_image=None):
        """Save the back view camera image with watermark"""
        if not self.validate_vehicle_number():
            return False
        
        # Use captured image or get from camera
        image = captured_image if captured_image is not None else self.back_camera.captured_image
        
        if image is not None:
            # Generate filename and watermark text
            site_name = self.site_var.get().replace(" ", "_")
            vehicle_no = self.vehicle_var.get().replace(" ", "_")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Watermark text
            watermark_text = f"{site_name} - {vehicle_no} - {timestamp}"
            
            # Add watermark
            watermarked_image = self.add_watermark(image, watermark_text)
            
            # Save file path
            filename = f"{site_name}_{vehicle_no}_{timestamp}_back.jpg"
            filepath = os.path.join(IMAGES_FOLDER, filename)
            
            # Save the image
            cv2.imwrite(filepath, watermarked_image)
            
            # Update status
            self.back_image_path = filepath
            self.back_image_status_var.set("Back: ✓")
            self.back_image_status.config(foreground="green")
            
            messagebox.showinfo("Success", "Back image saved!")
            return True
            
        return False
    
    def validate_vehicle_number(self):
        """Validate that vehicle number is entered before capturing images"""
        if not self.vehicle_var.get().strip():
            messagebox.showerror("Error", "Please enter a vehicle number before capturing images.")
            return False
        return True
    
    def save_record(self):
        """Save current form data to CSV"""
        # Validate required fields
        if not self.validate_form():
            return
            
        # Prepare record
        now = datetime.datetime.now()
        
        # Relative image paths for storage in CSV
        front_image_rel_path = os.path.basename(self.front_image_path) if self.front_image_path else ""
        back_image_rel_path = os.path.basename(self.back_image_path) if self.back_image_path else ""
        
        record = [
            now.strftime("%d-%m-%Y"),
            now.strftime("%H:%M:%S"),
            self.site_var.get(),
            self.agency_var.get(),  # Renamed from party_var
            self.material_var.get(),
            self.rst_var.get(),
            self.vehicle_var.get(),
            self.tpt_var.get(),      # Now "Transfer Party Name"
            self.gross_weight_var.get(),
            self.tare_weight_var.get(),
            self.net_weight_var.get(),
            self.material_type_var.get(),
            front_image_rel_path,
            back_image_rel_path
        ]
        
        # Save to CSV
        with open(DATA_FILE, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(record)
        
        # Show success message
        messagebox.showinfo("Success", "Record saved successfully!")
        
        # Update the summary
        self.update_summary()
        
        # Switch to summary tab
        self.notebook.select(1)
        
        # Clear form for next entry
        self.clear_form()
        
    def validate_form(self):
        """Validate required form fields"""
        required_fields = {
            "Ticket No": self.rst_var.get(),
            "Vehicle No": self.vehicle_var.get(),
            "Agency Name": self.agency_var.get(),
            "Gross Weight": self.gross_weight_var.get(),
            "Tare Weight": self.tare_weight_var.get()
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value.strip()]
        
        if missing_fields:
            messagebox.showerror("Validation Error", 
                            f"Please fill in the following required fields: {', '.join(missing_fields)}")
            return False
        
        # Validate at least one image is captured
        if not self.front_image_path and not self.back_image_path:
            result = messagebox.askyesno("Missing Images", 
                                    "No images have been captured. Continue without images?")
            if not result:
                return False
            
        return True
        
    def clear_form(self):
        """Reset form fields except site and Transfer Party Name"""
        # Reset variables
        self.rst_var.set("")
        self.vehicle_var.set("")
        self.agency_var.set("")  # Renamed from party_var
        self.gross_weight_var.set("")
        self.tare_weight_var.set("")
        self.net_weight_var.set("")
        self.material_type_var.set("Inert")
        
        # Reset image paths
        self.front_image_path = None
        self.back_image_path = None
        self.front_image_status_var.set("Front: ✗")
        self.back_image_status_var.set("Back: ✗")
        self.front_image_status.config(foreground="red")
        self.back_image_status.config(foreground="red")
        
        # Reset camera displays if they were used
        if hasattr(self, 'front_camera'):
            self.front_camera.stop_camera()
            self.front_camera.captured_image = None
            self.front_camera.canvas.delete("all")
            self.front_camera.canvas.create_text(75, 60, text="Click Capture", fill="white", justify=tk.CENTER)
            self.front_camera.capture_button.config(text="Capture")
            
        if hasattr(self, 'back_camera'):
            self.back_camera.stop_camera()
            self.back_camera.captured_image = None
            self.back_camera.canvas.delete("all")
            self.back_camera.canvas.create_text(75, 60, text="Click Capture", fill="white", justify=tk.CENTER)
            self.back_camera.capture_button.config(text="Capture")


    def create_summary_panel(self, parent):
        """Create summary panel in its own tab with table view and export options"""
        # Add recent transactions summary
        summary_label = ttk.Label(parent, text="Recent Transactions", style="Subtitle.TLabel")
        summary_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Top control frame
        control_frame = ttk.Frame(parent, style="TFrame")
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Filter entry (could be enhanced later)
        ttk.Label(control_frame, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.filter_var, width=20).pack(side=tk.LEFT, padx=(0, 10))
        self.filter_var.trace_add("write", self.apply_filter)
        
        # Export options
        ttk.Label(control_frame, text="Export:").pack(side=tk.LEFT, padx=(20, 5))
        
        # Excel export button
        excel_btn = HoverButton(control_frame, 
                              text="Excel", 
                              bg=COLORS["secondary"],
                              fg=COLORS["button_text"],
                              padx=5, pady=2,
                              command=self.export_to_excel)
        excel_btn.pack(side=tk.LEFT, padx=2)
        
        # PDF export button
        pdf_btn = HoverButton(control_frame, 
                            text="PDF", 
                            bg=COLORS["primary"],
                            fg=COLORS["button_text"],
                            padx=5, pady=2,
                            command=self.export_to_pdf)
        pdf_btn.pack(side=tk.LEFT, padx=2)
        
        # Summary frame with table
        summary_frame = ttk.LabelFrame(parent, text="Recent Entries")
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create treeview for table
        columns = ("date", "vehicle", "agency", "material", "type", "weight", "images")
        self.summary_tree = ttk.Treeview(summary_frame, columns=columns, show="headings", height=10)
        
        # Define column headings
        self.summary_tree.heading("date", text="Date")
        self.summary_tree.heading("vehicle", text="Vehicle No")
        self.summary_tree.heading("agency", text="Agency Name")
        self.summary_tree.heading("material", text="Material")
        self.summary_tree.heading("type", text="Type")
        self.summary_tree.heading("weight", text="Net Weight")
        self.summary_tree.heading("images", text="Images")
        
        # Define column widths
        self.summary_tree.column("date", width=80)
        self.summary_tree.column("vehicle", width=100)
        self.summary_tree.column("agency", width=100)
        self.summary_tree.column("material", width=100)
        self.summary_tree.column("type", width=100)
        self.summary_tree.column("weight", width=80)
        self.summary_tree.column("images", width=60)
        
        # Add scrollbar
        summary_scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscroll=summary_scrollbar.set)
        
        # Pack widgets
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent, style="TFrame")
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Refresh button
        refresh_btn = HoverButton(buttons_frame, 
                                text="Refresh", 
                                bg=COLORS["primary"],
                                fg=COLORS["button_text"],
                                padx=8, pady=3,
                                command=self.update_summary)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # View details button
        details_btn = HoverButton(buttons_frame, 
                                text="View Details", 
                                bg=COLORS["primary"],
                                fg=COLORS["button_text"],
                                padx=8, pady=3,
                                command=self.view_entry_details)
        details_btn.pack(side=tk.LEFT, padx=5)
        
        # Load initial summary
        self.update_summary()
    
    def view_entry_details(self):
        """View details of the selected entry"""
        selected_item = self.summary_tree.selection()
        if not selected_item:
            messagebox.showinfo("Selection", "Please select a record to view details.")
            return
        
        # Get vehicle number from the selected item
        vehicle_no = self.summary_tree.item(selected_item, "values")[1]  # Vehicle No is index 1
        
        # Find record in CSV and display details with images
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                reader = csv.reader(f)
                # Skip header
                header = next(reader, None)
                
                # Find matching record
                for record in reader:
                    if len(record) >= 7 and record[6] == vehicle_no:  # Vehicle No index
                        # Display record details and images
                        self.display_record_details(record)
                        return
            
            messagebox.showinfo("Not Found", f"Details for vehicle {vehicle_no} not found.")
    
    def display_record_details(self, record):
        """Display full details of a record in a popup window"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Entry Details - {record[6]}")  # Vehicle No
        details_window.geometry("650x450")
        details_window.configure(bg=COLORS["background"])
        
        # Details frame
        details_frame = ttk.LabelFrame(details_window, text="Entry Information")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create two columns for details
        left_frame = ttk.Frame(details_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(details_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Display all fields in two columns
        # Left column
        row = 0
        for label, value in [
            ("Date:", record[0]),
            ("Time:", record[1]),
            ("Site Name:", record[2]),
            ("Agency Name:", record[3]),
            ("Input Material", record[4]),
            ("Ticket No:", record[5]),
            ("Vehicle No:", record[6])
        ]:
            ttk.Label(left_frame, text=label, font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky=tk.W, pady=2)
            ttk.Label(left_frame, text=value).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
            row += 1
        
        # Right column
        row = 0
        for label, value in [
            ("Transfer Party:", record[7]),
            ("Gross Weight:", record[8]),
            ("Tare Weight:", record[9]),
            ("Net Weight:", record[10]),
            ("Material Type:", record[11])
        ]:
            ttk.Label(right_frame, text=label, font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky=tk.W, pady=2)
            ttk.Label(right_frame, text=value).grid(row=row, column=1, sticky=tk.W, pady=2, padx=5)
            row += 1
        
        # Images frame
        images_frame = ttk.LabelFrame(details_window, text="Vehicle Images")
        images_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Display images in a row
        if len(record) >= 14:  # Check if image fields exist
            front_img_name = record[12]
            back_img_name = record[13]
            
            images_inner = ttk.Frame(images_frame)
            images_inner.pack(fill=tk.X, padx=5, pady=5)
            
            # Front image
            front_frame = ttk.LabelFrame(images_inner, text="Front")
            front_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
            
            self.display_image_in_frame(front_frame, front_img_name, 200, 150)
            
            # Back image
            back_frame = ttk.LabelFrame(images_inner, text="Back")
            back_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2)
            
            self.display_image_in_frame(back_frame, back_img_name, 200, 150)
        
        # Close button
        close_btn = HoverButton(details_window, 
                               text="Close", 
                               bg=COLORS["primary"],
                               fg=COLORS["button_text"],
                               padx=10, pady=3,
                               command=details_window.destroy)
        close_btn.pack(pady=5)
    
    def display_image_in_frame(self, parent, image_name, width, height):
        """Display an image in the given frame with specified size"""
        if image_name:
            image_path = os.path.join(IMAGES_FOLDER, image_name)
            if os.path.exists(image_path):
                try:
                    # Read image and resize
                    img = cv2.imread(image_path)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.resize(img, (width, height))
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(image=Image.fromarray(img))
                    
                    # Display
                    label = tk.Label(parent, image=photo)
                    label.image = photo  # Keep reference
                    label.pack(fill=tk.BOTH, expand=True)
                except Exception as e:
                    ttk.Label(parent, text=f"Error: {str(e)}").pack(pady=20)
            else:
                ttk.Label(parent, text="Image not found").pack(pady=20)
        else:
            ttk.Label(parent, text="No image").pack(pady=20)


    def apply_filter(self, *args):
        """Apply filter to the summary treeview"""
        self.update_summary()
    
    def export_to_excel(self):
        """Export summary data to Excel with fixed column mapping"""
        try:
            # Get data from CSV file
            if os.path.exists(DATA_FILE):
                # Ask for save location
                filename = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                    title="Save Excel File"
                )
                
                if not filename:
                    return  # User cancelled
                
                # Read CSV into pandas DataFrame
                df = pd.read_csv(DATA_FILE)
                
                # Handle column mapping issues
                # If there's a column mismatch due to schema changes, ensure we have consistent columns
                expected_columns = CSV_HEADER
                
                # Check if we need to fix the columns
                if list(df.columns) != expected_columns:
                    # Create a new DataFrame with expected columns
                    new_df = pd.DataFrame(columns=expected_columns)
                    
                    # Map existing columns to expected columns
                    for col in df.columns:
                        if col in expected_columns:
                            new_df[col] = df[col]
                    
                    # Fill missing columns with empty values
                    for col in expected_columns:
                        if col not in df.columns:
                            new_df[col] = ""
                    
                    df = new_df
                
                # Export to Excel
                df.to_excel(filename, index=False)
                
                messagebox.showinfo("Export Successful", 
                                 f"Data successfully exported to {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting to Excel: {str(e)}")
    
    def export_to_pdf(self):
        """Export summary data to PDF with images and improved formatting"""
        try:
            # Check if ReportLab is available, if not, use a simpler approach
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                reportlab_available = True
            except ImportError:
                reportlab_available = False
                
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save PDF File"
            )
            
            if not filename:
                return  # User cancelled
            
            if reportlab_available:
                # Use ReportLab for better PDF creation with images
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r') as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        data = list(reader)
                    
                    # Create the PDF document
                    doc = SimpleDocTemplate(filename, pagesize=A4)
                    styles = getSampleStyleSheet()
                    
                    # Create a custom style for the title
                    title_style = ParagraphStyle(
                        'TitleStyle',
                        parent=styles['Heading1'],
                        fontSize=16,
                        alignment=1,  # Center aligned
                        spaceAfter=12
                    )
                    
                    # Create elements to add to the PDF
                    elements = []
                    
                    # Add title
                    title = Paragraph("ADVITIA LABS - VEHICLE ENTRY REPORT", title_style)
                    elements.append(title)
                    elements.append(Spacer(1, 0.25*inch))
                    
                    # Add date and time
                    date_style = ParagraphStyle(
                        'DateStyle',
                        parent=styles['Normal'],
                        fontSize=10,
                        alignment=1,  # Center aligned
                    )
                    current_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    date_text = Paragraph(f"Report generated on: {current_date}", date_style)
                    elements.append(date_text)
                    elements.append(Spacer(1, 0.25*inch))
                    
                    # Create a table for the data
                    # Select only relevant columns for the report
                    visible_header = ["Date", "Vehicle No", "Agency Name", "Material", "Type", "Net Weight"]
                    column_indices = [0, 6, 3, 4, 11, 10]  # Indices of columns to display
                    
                    # Extract the relevant data
                    table_data = [[header[i] for i in column_indices]]
                    for row in data:
                        if len(row) >= max(column_indices) + 1:
                            table_data.append([row[i] for i in column_indices])
                    
                    # Create the table
                    table = Table(table_data, repeatRows=1)
                    
                    # Add style to the table
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    
                    elements.append(table)
                    elements.append(Spacer(1, 0.5*inch))
                    
                    # Add detailed entries for the most recent 5 records with images
                    elements.append(Paragraph("Recent Vehicle Entries with Images", styles['Heading2']))
                    elements.append(Spacer(1, 0.25*inch))
                    
                    # Display the most recent 5 records
                    recent_records = data[-5:] if len(data) >= 5 else data
                    
                    for record in reversed(recent_records):  # Most recent first
                        if len(record) >= 14:  # Ensure we have all fields including images
                            vehicle_no = record[6]
                            date_time = f"{record[0]} {record[1]}"
                            agency = record[3]
                            material = record[4]
                            material_type = record[11]
                            weights = f"Gross: {record[8]} kg | Tare: {record[9]} kg | Net: {record[10]} kg"
                            
                            # Create a detail section for this record
                            elements.append(Paragraph(f"Vehicle: {vehicle_no}", styles['Heading3']))
                            elements.append(Paragraph(f"Date/Time: {date_time}", styles['Normal']))
                            elements.append(Paragraph(f"Agency: {agency} | Material: {material} | Type: {material_type}", styles['Normal']))
                            elements.append(Paragraph(f"Weights: {weights}", styles['Normal']))
                            
                            # Try to add images if available
                            front_img = record[12]
                            back_img = record[13]
                            
                            if front_img or back_img:
                                # Create a mini table for the images
                                img_data = [["Front Image", "Back Image"]]
                                img_row = ["No Image", "No Image"]  # Default if images not found
                                
                                # Front image
                                if front_img:
                                    front_path = os.path.join(IMAGES_FOLDER, front_img)
                                    if os.path.exists(front_path):
                                        try:
                                            # Convert the OpenCV image to a format ReportLab can use
                                            img = cv2.imread(front_path)
                                            if img is not None:
                                                # Resize image to fit in report
                                                img = cv2.resize(img, (250, 150))
                                                # Save a temporary file
                                                temp_path = os.path.join(IMAGES_FOLDER, f"temp_front_{vehicle_no}.jpg")
                                                cv2.imwrite(temp_path, img)
                                                # Use the temporary file in the report
                                                img_row[0] = Image(temp_path, width=2*inch, height=1.2*inch)
                                        except Exception as img_err:
                                            print(f"Error processing front image: {img_err}")
                                
                                # Back image
                                if back_img:
                                    back_path = os.path.join(IMAGES_FOLDER, back_img)
                                    if os.path.exists(back_path):
                                        try:
                                            # Convert the OpenCV image to a format ReportLab can use
                                            img = cv2.imread(back_path)
                                            if img is not None:
                                                # Resize image to fit in report
                                                img = cv2.resize(img, (250, 150))
                                                # Save a temporary file
                                                temp_path = os.path.join(IMAGES_FOLDER, f"temp_back_{vehicle_no}.jpg")
                                                cv2.imwrite(temp_path, img)
                                                # Use the temporary file in the report
                                                img_row[1] = Image(temp_path, width=2*inch, height=1.2*inch)
                                        except Exception as img_err:
                                            print(f"Error processing back image: {img_err}")
                                
                                img_data.append(img_row)
                                
                                # Create and style the image table
                                img_table = Table(img_data, colWidths=[2.5*inch, 2.5*inch])
                                img_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))
                                
                                elements.append(img_table)
                            
                            elements.append(Spacer(1, 0.25*inch))
                            elements.append(Paragraph("-" * 65, styles['Normal']))
                            elements.append(Spacer(1, 0.25*inch))
                    
                    # Build the PDF document
                    doc.build(elements)
                    
                    # Clean up temporary files
                    for temp_file in os.listdir(IMAGES_FOLDER):
                        if temp_file.startswith("temp_"):
                            try:
                                os.remove(os.path.join(IMAGES_FOLDER, temp_file))
                            except:
                                pass
                    
                    messagebox.showinfo("Export Successful", 
                                     f"PDF report successfully generated: {os.path.basename(filename)}")
            else:
                # If ReportLab is not available, create a simpler text-based PDF
                # Since we can't easily create PDFs without ReportLab, we'll create a text report
                # and recommend installing ReportLab for better PDF output
                messagebox.showinfo("PDF Creation", 
                                 "For better PDF reports with images, please install ReportLab:\n"
                                 "pip install reportlab\n\n"
                                 "Creating a basic report file instead.")
                
                # Create a text report as a placeholder
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r') as f:
                        reader = csv.reader(f)
                        header = next(reader)
                        
                        # Create a DataFrame for easier handling
                        df = pd.DataFrame(list(reader), columns=header)
                        
                        # Save as text file
                        with open(filename, 'w') as text_file:
                            text_file.write("ADVITIA LABS - VEHICLE ENTRY REPORT\n")
                            text_file.write("="*50 + "\n\n")
                            
                            # Write each record
                            for _, row in df.iterrows():
                                for col, value in zip(header, row):
                                    text_file.write(f"{col}: {value}\n")
                                text_file.write("-"*50 + "\n")
                    
                    messagebox.showinfo("Basic Report Created", 
                                     f"Basic report file created: {os.path.basename(filename)}\n"
                                     "Install ReportLab for better PDF reports with images.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting to PDF: {str(e)}")
    def update_summary(self):
        """Update the recent transactions summary with table view"""
        # Clear existing items
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
            
        if not os.path.exists(DATA_FILE):
            return
            
        try:
            with open(DATA_FILE, 'r') as f:
                reader = csv.reader(f)
                # Skip header
                next(reader, None)
                
                # Get all records
                rows = list(reader)
                
                # Apply filter if any
                filter_text = self.filter_var.get().lower()
                if filter_text:
                    filtered_rows = []
                    for row in rows:
                        if any(filter_text in cell.lower() for cell in row):
                            filtered_rows.append(row)
                    rows = filtered_rows
                
                # Show most recent first (limited to 100 for performance)
                for i, record in enumerate(reversed(rows[-100:])):
                    if len(record) >= 12:  # Ensure record has all fields
                        # Check for images
                        image_info = "None"
                        if len(record) >= 14:  # New format with image fields
                            front_img = record[12]
                            back_img = record[13]
                            if front_img and back_img:
                                image_info = "F & B"
                            elif front_img:
                                image_info = "Front"
                            elif back_img:
                                image_info = "Back"
                        
                        # Add to treeview
                        self.summary_tree.insert("", tk.END, values=(
                            record[0],      # Date
                            record[6],      # Vehicle No
                            record[3],      # Agency Name (renamed from Party Name)
                            record[4],      # Material
                            record[11],     # Material Type
                            record[10],     # Net Weight
                            image_info      # Image info
                        ))
                
                # Alternate row colors
                for i, item in enumerate(self.summary_tree.get_children()):
                    if i % 2 == 0:
                        self.summary_tree.item(item, tags=("evenrow",))
                    else:
                        self.summary_tree.item(item, tags=("oddrow",))
                
                self.summary_tree.tag_configure("evenrow", background=COLORS["table_row_even"])
                self.summary_tree.tag_configure("oddrow", background=COLORS["table_row_odd"])
                
        except Exception as e:
            print(f"Error updating summary: {e}")


    def view_records(self):
        """Open a window to view all records with improved UI"""
        # Create new window - smaller size
        records_window = tk.Toplevel(self.root)
        records_window.title("All Records - Advitia Labs")
        records_window.geometry("750x400")  # Smaller size for 13" screens
        records_window.configure(bg=COLORS["background"])
        
        # Create a frame for the window content
        content_frame = ttk.Frame(records_window, style="TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Title label with improved styling
        title_frame = tk.Frame(content_frame, bg=COLORS["primary"])
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        title_label = tk.Label(title_frame, 
                              text="Transaction Records", 
                              font=("Segoe UI", 11, "bold"),
                              fg=COLORS["white"],
                              bg=COLORS["primary"],
                              padx=10, pady=5)
        title_label.pack(side=tk.LEFT)
        
        # Search and filter frame
        filter_frame = ttk.Frame(content_frame, style="TFrame")
        filter_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        search_btn = HoverButton(filter_frame, 
                               text="Search", 
                               bg=COLORS["primary"],
                               fg=COLORS["button_text"],
                               padx=5, pady=2,
                               command=lambda: self.filter_records(tree, search_var.get()))
        search_btn.pack(side=tk.LEFT, padx=2)
        
        # Export buttons
        export_frame = ttk.Frame(filter_frame, style="TFrame")
        export_frame.pack(side=tk.RIGHT)
        
        ttk.Label(export_frame, text="Export:").pack(side=tk.LEFT, padx=(0, 5))
        
        excel_btn = HoverButton(export_frame, 
                              text="Excel", 
                              bg=COLORS["secondary"],
                              fg=COLORS["button_text"],
                              padx=5, pady=2,
                              command=self.export_to_excel)
        excel_btn.pack(side=tk.LEFT, padx=2)
        
        pdf_btn = HoverButton(export_frame, 
                            text="PDF", 
                            bg=COLORS["primary"],
                            fg=COLORS["button_text"],
                            padx=5, pady=2,
                            command=self.export_to_pdf)
        pdf_btn.pack(side=tk.LEFT, padx=2)
        
        # Create a treeview to display data
        tree_frame = ttk.Frame(content_frame, style="TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Date", "Vehicle", "Agency", "Material", "Type", "Weight", "Images")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Configure column headings
        for col in columns:
            tree.heading(col, text=col)
            # Adjust column width based on content
            if col == "Date":
                tree.column(col, width=70)
            elif col in ["Vehicle", "Agency", "Material", "Type"]:
                tree.column(col, width=95)
            elif col == "Weight":
                tree.column(col, width=60)
            elif col == "Images":
                tree.column(col, width=60)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Load data
        self.load_records_data(tree)
        
        # Add buttons frame
        buttons_frame = ttk.Frame(content_frame, style="TFrame")
        buttons_frame.pack(pady=5)
        
        view_images_btn = HoverButton(buttons_frame, 
                                    text="View Details", 
                                    bg=COLORS["primary"],
                                    fg=COLORS["button_text"],
                                    padx=8, pady=3,
                                    command=lambda: self.view_record_details_from_tree(tree))
        view_images_btn.pack(side=tk.LEFT, padx=5)
        
        # Add close button
        close_btn = HoverButton(buttons_frame, 
                               text="Close", 
                               bg=COLORS["error"],
                               fg=COLORS["button_text"],
                               padx=8, pady=3,
                               command=records_window.destroy)
        close_btn.pack(side=tk.LEFT, padx=5)
    
    def filter_records(self, tree, search_text):
        """Filter records in treeview based on search text"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Load filtered data
        self.load_records_data(tree, search_text)
    
    def load_records_data(self, tree, search_text=""):
        """Load data into treeview with optional filtering"""
        search_text = search_text.lower()
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                reader = csv.reader(f)
                # Skip header
                next(reader, None)
                
                # Filter and add records to treeview
                for i, record in enumerate(reader):
                    if len(record) >= 12:  # Ensure record has enough fields
                        # Apply search filter if provided
                        if search_text and not any(search_text in str(cell).lower() for cell in record):
                            continue
                        
                        # Check for images
                        image_info = "None"
                        if len(record) >= 14:  # New format with image fields
                            front_img = record[12] if len(record) > 12 else ""
                            back_img = record[13] if len(record) > 13 else ""
                            if front_img and back_img:
                                image_info = "F & B"
                            elif front_img:
                                image_info = "Front"
                            elif back_img:
                                image_info = "Back"
                        
                        tree.insert("", tk.END, values=(
                            record[0],     # Date
                            record[6],     # Vehicle No
                            record[3],     # Agency Name
                            record[4],     # Material
                            record[11],    # Material Type
                            record[10],    # Net Weight
                            image_info     # Image info
                        ))
                
                # Alternate row colors
                for i, item in enumerate(tree.get_children()):
                    if i % 2 == 0:
                        tree.item(item, tags=("evenrow",))
                    else:
                        tree.item(item, tags=("oddrow",))
                
                tree.tag_configure("evenrow", background=COLORS["table_row_even"])
                tree.tag_configure("oddrow", background=COLORS["table_row_odd"])
    
    def view_record_details_from_tree(self, tree):
        """View details of the selected record"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showinfo("Selection", "Please select a record to view details.")
            return
        
        # Get selected vehicle number
        vehicle_no = tree.item(selected_item, "values")[1]  # Vehicle is index 1
        
        # Find record in CSV and display details
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                reader = csv.reader(f)
                # Skip header
                next(reader, None)
                
                # Find matching record
                for record in reader:
                    if len(record) >= 7 and record[6] == vehicle_no:  # Match vehicle number
                        # Display record details
                        self.display_record_details(record)
                        return
            
            messagebox.showinfo("Not Found", f"Details for vehicle {vehicle_no} not found.")

    def view_record_images(self, tree):
        """View images for selected record - updated to show detailed info"""
        # This function is now mostly handled by view_record_details_from_tree
        # but is kept for backward compatibility with existing button references
        self.view_record_details_from_tree(tree)
        
    def display_images(self, vehicle_no, front_img_name, back_img_name):
        """Display images in a new window - enhanced with better layout"""
        images_window = tk.Toplevel(self.root)
        images_window.title(f"Vehicle Images - {vehicle_no}")
        images_window.geometry("650x350")  # Smaller for 13" screens
        images_window.configure(bg=COLORS["background"])
        
        # Create image frames
        image_container = ttk.Frame(images_window, style="TFrame")
        image_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Front image frame
        front_frame = ttk.LabelFrame(image_container, text="Front Image")
        front_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        # Back image frame
        back_frame = ttk.LabelFrame(image_container, text="Back Image")
        back_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        # Load and display front image
        self.display_image_in_frame(front_frame, front_img_name, 300, 250)
        
        # Load and display back image
        self.display_image_in_frame(back_frame, back_img_name, 300, 250)
        
        # Close button with improved styling
        close_btn = HoverButton(images_window, 
                               text="Close", 
                               bg=COLORS["primary"],
                               fg=COLORS["button_text"],
                               padx=10, pady=3,
                               command=images_window.destroy)
        close_btn.pack(pady=5)
        
    def on_closing(self):
        """Handle window closing - stop cameras properly"""
        try:
            if hasattr(self, 'front_camera'):
                self.front_camera.stop_camera()
            if hasattr(self, 'back_camera'):
                self.back_camera.stop_camera()
            if self.weighbridge_connected:
                self.disconnect_weighbridge()
        except:
            pass
        self.root.destroy()

# Main script to run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = TharuniApp(root)
    root.mainloop()

    