import os
import datetime
import csv
import pandas as pd
from tkinter import filedialog, messagebox
import config

def export_to_excel(filename=None):
    """Export data to Excel file
    
    Args:
        filename: Optional filename to save to. If None, will prompt for location.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if data file exists
        if not os.path.exists(config.DATA_FILE):
            messagebox.showerror("Export Failed", "No data to export.")
            return False
            
        # If no filename provided, ask for save location
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Excel File"
            )
            
            if not filename:  # User canceled
                return False
                
        # Read CSV into pandas DataFrame
        df = pd.read_csv(config.DATA_FILE)
        
        # Handle column mapping issues
        # If there's a column mismatch due to schema changes, ensure we have consistent columns
        expected_columns = config.CSV_HEADER
        
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
        
        return True
        
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
        return False

def export_to_pdf(filename=None):
    """Export data to PDF file
    
    Args:
        filename: Optional filename to save to. If None, will prompt for location.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if ReportLab is available
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            import cv2
            reportlab_available = True
        except ImportError:
            reportlab_available = False
            
        # Check if data file exists
        if not os.path.exists(config.DATA_FILE):
            messagebox.showerror("Export Failed", "No data to export.")
            return False
            
        # If no filename provided, ask for save location
        if not filename:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save PDF File"
            )
            
            if not filename:  # User canceled
                return False
                
        if reportlab_available:
            # Use ReportLab for better PDF creation with images
            with open(config.DATA_FILE, 'r') as f:
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
                            front_path = os.path.join(config.IMAGES_FOLDER, front_img)
                            if os.path.exists(front_path):
                                try:
                                    # Convert the OpenCV image to a format ReportLab can use
                                    img = cv2.imread(front_path)
                                    if img is not None:
                                        # Resize image to fit in report
                                        img = cv2.resize(img, (250, 150))
                                        # Save a temporary file
                                        temp_path = os.path.join(config.IMAGES_FOLDER, f"temp_front_{vehicle_no}.jpg")
                                        cv2.imwrite(temp_path, img)
                                        # Use the temporary file in the report
                                        img_row[0] = Image(temp_path, width=2*inch, height=1.2*inch)
                                except Exception as img_err:
                                    print(f"Error processing front image: {img_err}")
                        
                        # Back image
                        if back_img:
                            back_path = os.path.join(config.IMAGES_FOLDER, back_img)
                            if os.path.exists(back_path):
                                try:
                                    # Convert the OpenCV image to a format ReportLab can use
                                    img = cv2.imread(back_path)
                                    if img is not None:
                                        # Resize image to fit in report
                                        img = cv2.resize(img, (250, 150))
                                        # Save a temporary file
                                        temp_path = os.path.join(config.IMAGES_FOLDER, f"temp_back_{vehicle_no}.jpg")
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
            for temp_file in os.listdir(config.IMAGES_FOLDER):
                if temp_file.startswith("temp_"):
                    try:
                        os.remove(os.path.join(config.IMAGES_FOLDER, temp_file))
                    except:
                        pass
                        
            return True
            
        else:
            # If ReportLab is not available, create a simpler text-based PDF
            messagebox.showinfo("PDF Creation", 
                             "For better PDF reports with images, please install ReportLab:\n"
                             "pip install reportlab\n\n"
                             "Creating a basic report file instead.")
            
            # Create a text report as a placeholder
            with open(config.DATA_FILE, 'r') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                
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
                
                return True
            
    except Exception as e:
        print(f"Error exporting to PDF: {e}")
        return False