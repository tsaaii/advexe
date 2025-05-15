import os
import csv
import pandas as pd
import datetime
from tkinter import messagebox, filedialog
import config

class DataManager:
    """Class for managing data operations with the CSV file"""
    
    def __init__(self):
        """Initialize data manager"""
        self.data_file = config.DATA_FILE
        
    def save_record(self, data):
        """Save record to CSV file
        
        Args:
            data: Dictionary of data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format data as a row
            record = [
                data.get('date', datetime.datetime.now().strftime("%d-%m-%Y")),
                data.get('time', datetime.datetime.now().strftime("%H:%M:%S")),
                data.get('site_name', ''),
                data.get('agency_name', ''),
                data.get('material', ''),
                data.get('ticket_no', ''),
                data.get('vehicle_no', ''),
                data.get('transfer_party_name', ''),
                data.get('gross_weight', ''),
                data.get('tare_weight', ''),
                data.get('net_weight', ''),
                data.get('material_type', ''),
                data.get('front_image', ''),
                data.get('back_image', '')
            ]
            
            # Write to CSV
            with open(self.data_file, 'a', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(record)
                
            return True
            
        except Exception as e:
            print(f"Error saving record: {e}")
            return False
            
    def get_all_records(self):
        """Get all records from CSV file
        
        Returns:
            list: List of records as dictionaries
        """
        records = []
        
        if not os.path.exists(self.data_file):
            return records
            
        try:
            with open(self.data_file, 'r', newline='') as csv_file:
                reader = csv.reader(csv_file)
                
                # Skip header
                header = next(reader, None)
                
                for row in reader:
                    if len(row) >= 12:  # Minimum fields required
                        record = {
                            'date': row[0],
                            'time': row[1],
                            'site_name': row[2],
                            'agency_name': row[3],
                            'material': row[4],
                            'ticket_no': row[5],
                            'vehicle_no': row[6],
                            'transfer_party_name': row[7],
                            'gross_weight': row[8],
                            'tare_weight': row[9],
                            'net_weight': row[10],
                            'material_type': row[11],
                            'front_image': row[12] if len(row) > 12 else '',
                            'back_image': row[13] if len(row) > 13 else ''
                        }
                        records.append(record)
                        
            return records
                
        except Exception as e:
            print(f"Error reading records: {e}")
            return []
    
    def get_record_by_vehicle(self, vehicle_no):
        """Get a specific record by vehicle number
        
        Args:
            vehicle_no: Vehicle number to search for
            
        Returns:
            dict: Record as dictionary or None if not found
        """
        if not os.path.exists(self.data_file):
            return None
            
        try:
            with open(self.data_file, 'r', newline='') as csv_file:
                reader = csv.reader(csv_file)
                
                # Skip header
                next(reader, None)
                
                for row in reader:
                    if len(row) >= 7 and row[6] == vehicle_no:  # Vehicle number is index 6
                        record = {
                            'date': row[0],
                            'time': row[1],
                            'site_name': row[2],
                            'agency_name': row[3],
                            'material': row[4],
                            'ticket_no': row[5],
                            'vehicle_no': row[6],
                            'transfer_party_name': row[7],
                            'gross_weight': row[8],
                            'tare_weight': row[9],
                            'net_weight': row[10],
                            'material_type': row[11],
                            'front_image': row[12] if len(row) > 12 else '',
                            'back_image': row[13] if len(row) > 13 else ''
                        }
                        return record
                        
            return None
                
        except Exception as e:
            print(f"Error finding record: {e}")
            return None
    
    def get_filtered_records(self, filter_text=""):
        """Get records filtered by text
        
        Args:
            filter_text: Text to filter records by
            
        Returns:
            list: Filtered records
        """
        all_records = self.get_all_records()
        
        if not filter_text:
            return all_records
            
        filter_text = filter_text.lower()
        filtered_records = []
        
        for record in all_records:
            # Check if filter text exists in any field
            if any(filter_text in str(value).lower() for value in record.values()):
                filtered_records.append(record)
                
        return filtered_records
    
    def validate_record(self, data):
        """Validate record data
        
        Args:
            data: Record data
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = {
            "Ticket No": data.get('ticket_no', ''),
            "Vehicle No": data.get('vehicle_no', ''),
            "Agency Name": data.get('agency_name', ''),
            "Gross Weight": data.get('gross_weight', ''),
            "Tare Weight": data.get('tare_weight', '')
        }
        
        missing_fields = [field for field, value in required_fields.items() 
                         if not str(value).strip()]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate images if specified in validation
        front_image = data.get('front_image', '')
        back_image = data.get('back_image', '')
        
        if not front_image and not back_image:
            return False, "No images captured"
            
        return True, ""