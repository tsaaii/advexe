import serial
import serial.tools.list_ports
import threading
import time
import re
from collections import defaultdict
from tkinter import messagebox


class WeighbridgeManager:
    """Class to manage weighbridge connection and data processing"""
    
    def __init__(self, update_callback=None):
        """Initialize weighbridge manager
        
        Args:
            update_callback: Function to call when weight is updated
        """
        self.serial_port = None
        self.weighbridge_connected = False
        self.weight_buffer = []
        self.weight_processing = False
        self.weight_thread = None
        self.weight_update_thread = None
        self.update_callback = update_callback
    
    def get_available_ports(self):
        """Get list of available COM ports"""
        return [port.device for port in serial.tools.list_ports.comports()]
    
    def connect(self, com_port, baud_rate, data_bits, parity, stop_bits):
        """Connect to weighbridge with specified parameters
        
        Args:
            com_port: COM port name
            baud_rate: Baud rate (int)
            data_bits: Data bits (int)
            parity: Parity setting (string, first letter used)
            stop_bits: Stop bits (float)
            
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if not com_port:
            return False
        
        try:
            # Convert parity to serial.PARITY_* value
            parity_map = {
                'N': serial.PARITY_NONE,
                'O': serial.PARITY_ODD,
                'E': serial.PARITY_EVEN,
                'M': serial.PARITY_MARK,
                'S': serial.PARITY_SPACE
            }
            parity = parity_map.get(parity[0].upper(), serial.PARITY_NONE)
            
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
            
            # Start processing
            self.weighbridge_connected = True
            
            # Start weight reading thread
            self.weight_thread = threading.Thread(target=self._read_weighbridge_data, daemon=True)
            self.weight_thread.start()
            
            # Start weight processing thread
            self.weight_processing = True
            self.weight_update_thread = threading.Thread(target=self._process_weighbridge_data, daemon=True)
            self.weight_update_thread.start()
            
            return True
            
        except Exception as e:
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None
            raise e
    
    def disconnect(self):
        """Disconnect from weighbridge
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
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
                
            return True
                
        except Exception as e:
            print(f"Error disconnecting weighbridge: {e}")
            return False
    
    def _read_weighbridge_data(self):
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
    
    def _process_weighbridge_data(self):
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
                        # Update with the new weight through callback
                        if self.update_callback:
                            self.update_callback(most_common)
                
            except Exception as e:
                print(f"Weight processing error: {str(e)}")
                time.sleep(1)