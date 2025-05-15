import tkinter as tk
from tkinter import ttk, messagebox
import serial.tools.list_ports

import config
from ui_components import HoverButton
from weighbridge import WeighbridgeManager

class SettingsPanel:
    """Settings panel for camera and weighbridge configuration"""
    
    def __init__(self, parent, weighbridge_callback=None, update_cameras_callback=None):
        """Initialize settings panel
        
        Args:
            parent: Parent widget
            weighbridge_callback: Callback for weighbridge weight updates
            update_cameras_callback: Callback for camera updates
        """
        self.parent = parent
        self.weighbridge_callback = weighbridge_callback
        self.update_cameras_callback = update_cameras_callback
        
        # Initialize variables
        self.init_variables()
        
        # Initialize weighbridge manager
        self.weighbridge = WeighbridgeManager(self.weighbridge_callback)
        
        # Create UI components
        self.create_panel()
    
    def init_variables(self):
        """Initialize settings variables"""
        # Weighbridge settings
        self.com_port_var = tk.StringVar()
        self.baud_rate_var = tk.IntVar(value=9600)
        self.data_bits_var = tk.IntVar(value=8)
        self.parity_var = tk.StringVar(value="None")
        self.stop_bits_var = tk.DoubleVar(value=1.0)
        self.wb_status_var = tk.StringVar(value="Status: Disconnected")
        self.current_weight_var = tk.StringVar(value="0 kg")
        
        # Camera settings
        self.front_cam_index_var = tk.IntVar(value=0)
        self.back_cam_index_var = tk.IntVar(value=1)
        self.cam_status_var = tk.StringVar()
    
    def create_panel(self):
        """Create settings panel with tabs"""
        # Create settings notebook
        self.settings_notebook = ttk.Notebook(self.parent)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Weighbridge settings tab
        weighbridge_tab = ttk.Frame(self.settings_notebook, style="TFrame")
        self.settings_notebook.add(weighbridge_tab, text="Weighbridge")
        
        # Camera settings tab
        camera_tab = ttk.Frame(self.settings_notebook, style="TFrame")
        self.settings_notebook.add(camera_tab, text="Cameras")
        
        # Create tab contents
        self.create_weighbridge_settings(weighbridge_tab)
        self.create_camera_settings(camera_tab)
    
    def create_weighbridge_settings(self, parent):
        """Create weighbridge configuration settings"""
        # Weighbridge settings frame
        wb_frame = ttk.LabelFrame(parent, text="Weighbridge Configuration", padding=10)
        wb_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # COM Port selection
        ttk.Label(wb_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.com_port_combo = ttk.Combobox(wb_frame, textvariable=self.com_port_var, state="readonly")
        self.com_port_combo.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        self.refresh_com_ports()
        
        # Refresh COM ports button
        refresh_btn = HoverButton(wb_frame, text="Refresh Ports", bg=config.COLORS["primary_light"], 
                                 fg=config.COLORS["text"], padx=5, pady=2,
                                 command=self.refresh_com_ports)
        refresh_btn.grid(row=0, column=2, padx=5, pady=2)
        
        # Baud rate
        ttk.Label(wb_frame, text="Baud Rate:").grid(row=1, column=0, sticky=tk.W, pady=2)
        baud_rates = [600, 1200, 2400, 4800, 9600, 14400, 19200, 57600, 115200]
        ttk.Combobox(wb_frame, textvariable=self.baud_rate_var, values=baud_rates, 
                    state="readonly").grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Data bits
        ttk.Label(wb_frame, text="Data Bits:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(wb_frame, textvariable=self.data_bits_var, values=[5, 6, 7, 8], 
                    state="readonly").grid(row=2, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Parity
        ttk.Label(wb_frame, text="Parity:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(wb_frame, textvariable=self.parity_var, 
                    values=["None", "Odd", "Even", "Mark", "Space"], 
                    state="readonly").grid(row=3, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Stop bits
        ttk.Label(wb_frame, text="Stop Bits:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(wb_frame, textvariable=self.stop_bits_var, values=[1.0, 1.5, 2.0], 
                    state="readonly").grid(row=4, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Connection buttons
        btn_frame = ttk.Frame(wb_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.connect_btn = HoverButton(btn_frame, text="Connect", bg=config.COLORS["secondary"], 
                                     fg=config.COLORS["button_text"], padx=10, pady=3,
                                     command=self.connect_weighbridge)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = HoverButton(btn_frame, text="Disconnect", bg=config.COLORS["error"], 
                                        fg=config.COLORS["button_text"], padx=10, pady=3,
                                        command=self.disconnect_weighbridge, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        ttk.Label(wb_frame, textvariable=self.wb_status_var, 
                foreground="red").grid(row=6, column=0, columnspan=3, sticky=tk.W)
        
        # Test weight display
        ttk.Label(wb_frame, text="Current Weight:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.weight_label = ttk.Label(wb_frame, textvariable=self.current_weight_var, 
                                    font=("Segoe UI", 10, "bold"))
        self.weight_label.grid(row=7, column=1, sticky=tk.W, pady=2)
    
    def create_camera_settings(self, parent):
        """Create camera configuration settings"""
        # Camera settings frame
        cam_frame = ttk.LabelFrame(parent, text="Camera Configuration", padding=10)
        cam_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Front camera index
        ttk.Label(cam_frame, text="Front Camera Index:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(cam_frame, textvariable=self.front_cam_index_var, 
                    values=[0, 1, 2, 3], state="readonly").grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Back camera index
        ttk.Label(cam_frame, text="Back Camera Index:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(cam_frame, textvariable=self.back_cam_index_var, 
                    values=[0, 1, 2, 3], state="readonly").grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Apply button
        apply_btn = HoverButton(cam_frame, text="Apply Settings", bg=config.COLORS["primary"], 
                               fg=config.COLORS["button_text"], padx=10, pady=3,
                               command=self.apply_camera_settings)
        apply_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Status message
        ttk.Label(cam_frame, textvariable=self.cam_status_var, 
                foreground=config.COLORS["primary"]).grid(row=3, column=0, columnspan=2, sticky=tk.W)
    
    def refresh_com_ports(self):
        """Refresh available COM ports"""
        ports = self.weighbridge.get_available_ports()
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
            # Get connection parameters
            baud_rate = self.baud_rate_var.get()
            data_bits = self.data_bits_var.get()
            parity = self.parity_var.get()
            stop_bits = self.stop_bits_var.get()
            
            # Connect to weighbridge
            if self.weighbridge.connect(com_port, baud_rate, data_bits, parity, stop_bits):
                # Update UI
                self.wb_status_var.set("Status: Connected")
                self.weight_label.config(foreground="green")
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                messagebox.showinfo("Success", "Weighbridge connected successfully!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to weighbridge:\n{str(e)}")
    
    def disconnect_weighbridge(self):
        """Disconnect from weighbridge"""
        if self.weighbridge.disconnect():
            # Update UI
            self.wb_status_var.set("Status: Disconnected")
            self.weight_label.config(foreground="red")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.current_weight_var.set("0 kg")
    
    def update_weight_display(self, weight):
        """Update weight display (callback for weighbridge)
        
        Args:
            weight: Weight value to display
        """
        self.current_weight_var.set(f"{weight:.2f} kg")
        
        # Update weight label color based on connection status
        if self.wb_status_var.get() == "Status: Connected":
            self.weight_label.config(foreground="green")
        else:
            self.weight_label.config(foreground="red")
        
        # Propagate weight update to form if callback is set
        if self.weighbridge_callback:
            self.weighbridge_callback(weight)
    
    def apply_camera_settings(self):
        """Apply camera index settings"""
        front_index = self.front_cam_index_var.get()
        back_index = self.back_cam_index_var.get()
        
        # Update camera indices through callback
        if self.update_cameras_callback:
            self.update_cameras_callback(front_index, back_index)
        
        self.cam_status_var.set("Camera settings applied. Changes take effect on next capture.")
    
    def on_closing(self):
        """Handle cleanup when closing"""
        if self.weighbridge:
            self.weighbridge.disconnect()