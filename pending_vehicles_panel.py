import tkinter as tk
from tkinter import ttk, messagebox
import datetime

import config
from ui_components import HoverButton

class PendingVehiclesPanel:
    """Panel to display and manage vehicles waiting for second weighment"""
    
    def __init__(self, parent, data_manager=None, on_vehicle_select=None):
        """Initialize the pending vehicles panel
        
        Args:
            parent: Parent widget
            data_manager: Data manager instance
            on_vehicle_select: Callback for when a vehicle is selected for second weighment
        """
        self.parent = parent
        self.data_manager = data_manager
        self.on_vehicle_select = on_vehicle_select
        
        # Create panel
        self.create_panel()
    
    def create_panel(self):
        """Create the pending vehicles panel"""
        # Main frame
        main_frame = ttk.LabelFrame(self.parent, text="Vehicles Waiting for Second Weighment")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create toolbar with refresh button
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        refresh_btn = HoverButton(toolbar, 
                                text="↻ Refresh", 
                                bg=config.COLORS["primary"],
                                fg=config.COLORS["button_text"],
                                padx=5, pady=1,
                                command=self.refresh_pending_list)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Create treeview for pending vehicles
        columns = ("ticket", "vehicle", "agency", "first_weight", "timestamp")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=6)
        
        # Define column headings
        self.tree.heading("ticket", text="Ticket №")
        self.tree.heading("vehicle", text="Vehicle №")
        self.tree.heading("agency", text="Agency")
        self.tree.heading("first_weight", text="First Weight")
        self.tree.heading("timestamp", text="Time")
        
        # Define column widths
        self.tree.column("ticket", width=70)
        self.tree.column("vehicle", width=90)
        self.tree.column("agency", width=90)
        self.tree.column("first_weight", width=80)
        self.tree.column("timestamp", width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Instructions label
        instructions = ttk.Label(main_frame, 
                                text="Double-click a vehicle to complete second weighment",
                                font=("Segoe UI", 8, "italic"))
        instructions.pack(fill=tk.X, pady=2)
        
        # Populate the list initially
        self.refresh_pending_list()
    
    def refresh_pending_list(self):
        """Refresh the list of pending vehicles"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not self.data_manager:
            return
            
        # Get all records
        records = self.data_manager.get_all_records()
        
        # Filter for records with first weighment but no second weighment
        pending_records = []
        for record in records:
            if (record.get('first_weight') and record.get('first_timestamp') and 
                (not record.get('second_weight') or not record.get('second_timestamp'))):
                pending_records.append(record)
        
        # Add to treeview, most recent first
        for record in reversed(pending_records):
            self.tree.insert("", tk.END, values=(
                record.get('ticket_no', ''),
                record.get('vehicle_no', ''),
                record.get('agency_name', ''),
                record.get('first_weight', ''),
                self.format_timestamp(record.get('first_timestamp', ''))
            ))
        
        # Apply alternating row colors
        self._apply_row_colors()
    
    def format_timestamp(self, timestamp):
        """Format timestamp to show just time if it's today"""
        if not timestamp:
            return ""
            
        try:
            # Parse the timestamp
            dt = datetime.datetime.strptime(timestamp, "%d-%m-%Y %H:%M:%S")
            
            # If it's today, just show the time
            if dt.date() == datetime.datetime.now().date():
                return dt.strftime("%H:%M:%S")
            else:
                return dt.strftime("%d-%m %H:%M")
        except:
            return timestamp
    
    def _apply_row_colors(self):
        """Apply alternating row colors to treeview"""
        for i, item in enumerate(self.tree.get_children()):
            if i % 2 == 0:
                self.tree.item(item, tags=("evenrow",))
            else:
                self.tree.item(item, tags=("oddrow",))
        
        self.tree.tag_configure("evenrow", background=config.COLORS["table_row_even"])
        self.tree.tag_configure("oddrow", background=config.COLORS["table_row_odd"])
    
    def on_item_double_click(self, event):
        """Handle double-click on an item"""
        # Get the selected item
        selection = self.tree.selection()
        if not selection:
            return
            
        # Get the ticket number from the selected item
        ticket_no = self.tree.item(selection[0], "values")[0]
        
        # Call the callback if provided
        if self.on_vehicle_select and ticket_no:
            self.on_vehicle_select(ticket_no)