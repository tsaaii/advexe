
import tkinter as tk
from tkinter import ttk, messagebox
import os
import datetime
import cv2
from PIL import Image, ImageTk
import threading

import config
from ui_components import HoverButton
from camera import CameraView, add_watermark

class MainForm:
    """Main data entry form for vehicle information"""
    
    def __init__(self, parent, notebook=None, summary_update_callback=None):
        """Initialize the main form
        
        Args:
            parent: Parent widget
            notebook: Notebook for tab switching
            summary_update_callback: Function to call to update summary view
        """
        self.parent = parent
        self.notebook = notebook
        self.summary_update_callback = summary_update_callback
        
        # Create form variables
        self.init_variables()
        
        # Camera lock to prevent both cameras from being used simultaneously
        self.camera_lock = threading.Lock()
        
        # Create UI elements
        self.create_form(parent)
        self.create_cameras_panel(parent)
        
    def init_variables(self):
        """Initialize form variables"""
        # Create variables for form fields
        self.site_var = tk.StringVar(value="Guntur")
        self.agency_var = tk.StringVar()
        self.material_var = tk.StringVar(value="MSW")
        self.rst_var = tk.StringVar()
        self.vehicle_var = tk.StringVar()
        self.tpt_var = tk.StringVar(value="Advitia Labs")
        self.gross_weight_var = tk.StringVar()
        self.tare_weight_var = tk.StringVar()
        self.net_weight_var = tk.StringVar()
        
        # Material type tracking
        self.material_type_var = tk.StringVar(value="Inert")
        
        # Saved image paths
        self.front_image_path = None
        self.back_image_path = None
        
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
        
        # Agency Name - Column 1
        ttk.Label(form_inner, text="Agency Name:").grid(row=0, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Material - Column 2
        ttk.Label(form_inner, text="Input Material").grid(row=0, column=2, sticky=tk.W, padx=3, pady=3)
        
        # Row 1: First row of entries
        # Site Name Entry - Column 0
        site_combo = ttk.Combobox(form_inner, textvariable=self.site_var, state="readonly", width=config.STD_WIDTH)
        site_combo['values'] = ('Guntur',)
        site_combo.grid(row=1, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Agency Name Entry - Column 1
        ttk.Entry(form_inner, textvariable=self.agency_var, width=config.STD_WIDTH).grid(row=1, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Material Combo Box - Column 2
        material_combo = ttk.Combobox(form_inner, textvariable=self.material_var, state="readonly", width=config.STD_WIDTH)
        material_combo['values'] = ('MSW')
        material_combo.grid(row=1, column=2, sticky=tk.W, padx=3, pady=3)
        
        # Row 2: Second row of labels
        # Ticket No - Column 0
        ttk.Label(form_inner, text="Ticket No:").grid(row=2, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Vehicle No - Column 1
        ttk.Label(form_inner, text="Vehicle No:").grid(row=2, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Transfer Party Name - Column 2
        ttk.Label(form_inner, text="Transfer Party Name:").grid(row=2, column=2, sticky=tk.W, padx=3, pady=3)
        
        # Row 3: Second row of entries
        # Ticket No Entry - Column 0
        ttk.Entry(form_inner, textvariable=self.rst_var, width=config.STD_WIDTH).grid(row=3, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Vehicle No Entry - Column 1
        vehicle_entry = ttk.Entry(form_inner, textvariable=self.vehicle_var, width=config.STD_WIDTH)
        vehicle_entry.grid(row=3, column=1, sticky=tk.W, padx=3, pady=3)
        
        # Transfer Party Name Entry - Column 2
        tpt_entry = ttk.Entry(form_inner, textvariable=self.tpt_var, width=config.STD_WIDTH)
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
                                         width=config.STD_WIDTH)
        # Material type options
        material_type_combo['values'] = ('Inert', 'Soil', 'Construction and Demolition', 
                                       'RDF(REFUSE DERIVED FUEL)')
        material_type_combo.grid(row=5, column=0, sticky=tk.W, padx=3, pady=3)
        
        # GROSS WEIGHT Entry - Column 1
        gross_entry = ttk.Entry(form_inner, width=config.STD_WIDTH)
        gross_entry.grid(row=5, column=1, sticky=tk.W, padx=3, pady=3)
        gross_entry.config(textvariable=self.gross_weight_var)
        gross_entry.bind("<KeyRelease>", self.calculate_net_weight)
        
        # TARE WEIGHT Entry - Column 2
        tare_entry = ttk.Entry(form_inner, width=config.STD_WIDTH)
        tare_entry.grid(row=5, column=2, sticky=tk.W, padx=3, pady=3)
        tare_entry.config(textvariable=self.tare_weight_var)
        tare_entry.bind("<KeyRelease>", self.calculate_net_weight)
        
        # Row 6: NET WEIGHT label
        ttk.Label(form_inner, text="NET WEIGHT:").grid(row=6, column=0, sticky=tk.W, padx=3, pady=3)
        
        # Row 7: NET WEIGHT entry
        net_entry = ttk.Entry(form_inner, textvariable=self.net_weight_var, state="readonly", width=config.STD_WIDTH)
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
        
        # Create front camera
        self.front_camera = CameraView(front_panel)
        self.front_camera.save_function = self.save_front_image
        
        # Back camera
        back_panel = ttk.Frame(cameras_container, style="TFrame")
        back_panel.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
        
        # Back Camera title
        ttk.Label(back_panel, text="Back Camera").pack(anchor=tk.W, pady=2)
        
        # Create back camera
        self.back_camera = CameraView(back_panel)
        self.back_camera.save_function = self.save_back_image
    
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
    
    def validate_vehicle_number(self):
        """Validate that vehicle number is entered before capturing images"""
        if not self.vehicle_var.get().strip():
            messagebox.showerror("Error", "Please enter a vehicle number before capturing images.")
            return False
        return True
    
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
            watermarked_image = add_watermark(image, watermark_text)
            
            # Save file path
            filename = f"{site_name}_{vehicle_no}_{timestamp}_front.jpg"
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
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
            watermarked_image = add_watermark(image, watermark_text)
            
            # Save file path
            filename = f"{site_name}_{vehicle_no}_{timestamp}_back.jpg"
            filepath = os.path.join(config.IMAGES_FOLDER, filename)
            
            # Save the image
            cv2.imwrite(filepath, watermarked_image)
            
            # Update status
            self.back_image_path = filepath
            self.back_image_status_var.set("Back: ✓")
            self.back_image_status.config(foreground="green")
            
            messagebox.showinfo("Success", "Back image saved!")
            return True
            
        return False
    
    def get_form_data(self):
        """Get form data as a dictionary"""
        # Get current date and time
        now = datetime.datetime.now()
        
        # Prepare data dictionary
        data = {
            'date': now.strftime("%d-%m-%Y"),
            'time': now.strftime("%H:%M:%S"),
            'site_name': self.site_var.get(),
            'agency_name': self.agency_var.get(),
            'material': self.material_var.get(),
            'ticket_no': self.rst_var.get(),
            'vehicle_no': self.vehicle_var.get(),
            'transfer_party_name': self.tpt_var.get(),
            'gross_weight': self.gross_weight_var.get(),
            'tare_weight': self.tare_weight_var.get(),
            'net_weight': self.net_weight_var.get(),
            'material_type': self.material_type_var.get(),
            'front_image': os.path.basename(self.front_image_path) if self.front_image_path else "",
            'back_image': os.path.basename(self.back_image_path) if self.back_image_path else ""
        }
        
        return data
    
    def validate_form(self):
        """Validate form fields"""
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
        self.agency_var.set("")
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
    
    def on_closing(self):
        """Handle cleanup when closing"""
        if hasattr(self, 'front_camera'):
            self.front_camera.stop_camera()
        if hasattr(self, 'back_camera'):
            self.back_camera.stop_camera()