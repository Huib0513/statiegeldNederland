from flask import Flask, request, render_template, flash, redirect, url_for
import os
import zipfile
import tempfile
from collections import defaultdict
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from sheetsmanager import update_sheet_by_search, insert_row_by_name, SheetsManager

app = Flask(__name__)
app.config.from_pyfile('flaskconfig.py')

# Ensure upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def update_sheet(processing_date: str, bags: dict) -> str:
    spreadsheet_id = '1DJmUp6qd7gZxrlHdUcjwTA1pnDFES7iYq_GfAoyNkHE'
    sheet_name = 'Blad1'
    
    try:
        sheets = SheetsManager('servicecredentials.json')
        columns = sheets.get_column_names(spreadsheet_id, sheet_name)
        
        # Validate required columns exist
        required_columns = ['Zaknummer', 'Verwerkt', 'Verwerkingsdatum', 'Bedrag']
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            return f"Error: Missing required columns in sheet: {', '.join(missing_columns)}"
        
        # Get column index for Zaknummer to use in searches
        zaknummer_col_index = ord(columns['Zaknummer']) - ord('A')
        
        for bag in bags:
            try:
                # Find existing row with this bag ID
                row_num = sheets.find_row_by_value(
                    spreadsheet_id, 
                    sheet_name, 
                    bag['id'], 
                    zaknummer_col_index
                )
                
                if row_num is not None:
                    # Update existing row
                    sheets.write_to_sheet(
                        spreadsheet_id, 
                        f'E{row_num}:G{row_num}', 
                        [['X', processing_date, bag['amount']]]
                    )
                else:
                    # Find position where to insert new row
                    position = find_insert_position(sheets, spreadsheet_id, sheet_name, 
                                                  bag['id'], zaknummer_col_index)
                    
                    # Insert new row with correct values
                    insert_row_by_name(
                        spreadsheet_id, 
                        sheet_name, 
                        row_number=position, 
                        values=[[bag['id'], '', '', '', 'X', processing_date, bag['amount']]]
                    )
                    
            except Exception as e:
                return f"Error processing bag {bag['id']}: {str(e)}"
        
        return f"Successfully processed {len(bags)} bags"
        
    except Exception as e:
        return f"Error accessing sheet: {str(e)}"


def find_insert_position(sheets: SheetsManager, spreadsheet_id: str, sheet_name: str, 
                        target_id: str, col_index: int) -> int:
    """
    Find the position where to insert a new row based on bag ID.
    Returns the row number where the new row should be inserted.
    
    Args:
        sheets: SheetsManager instance
        spreadsheet_id: The spreadsheet ID
        sheet_name: The sheet name
        target_id: The bag ID to insert
        col_index: Column index for Zaknummer column
    
    Returns:
        int: Row number where to insert (1-based)
    """
    try:
        # Read all data from the sheet
        all_data = sheets.read_sheet(spreadsheet_id, sheet_name)
        
        # Skip header row and find insertion position
        for row_idx, row in enumerate(all_data[1:], start=2):  # Start from row 2 (skip header)
            if len(row) > col_index and row[col_index]:
                try:
                    # Convert both to integers for proper numeric comparison
                    current_id = int(row[col_index])
                    target_id_int = int(target_id)
                    
                    if current_id > target_id_int:
                        return row_idx  # Insert before this row
                        
                except (ValueError, TypeError):
                    # If conversion fails, do string comparison
                    if row[col_index] > target_id:
                        return row_idx
        
        # If no higher value found, insert at the end
        return len(all_data) + 1
        
    except Exception as e:
        # If there's an error, default to inserting at the end
        print(f"Warning: Error finding insert position, inserting at end: {str(e)}")
        try:
            all_data = sheets.read_sheet(spreadsheet_id, sheet_name)
            return len(all_data) + 1
        except:
            return 2  # Default to row 2 if everything fails

def process_chr_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Processing: split into lines
        lines = content.split('\n')
        processing_date = lines[0].split(';')[7]

        processed_lines = 0
        bags = defaultdict(float)
        moneys = 0.0
        
        for line in lines:
            if line.strip():  # Skip empty lines
                processed_lines += 1
                values = line.split(';')
                if values[8][1:] != '50':
                    bags[values[5]] += float(values[10].replace(',','.'))
                    moneys += float(values[10].replace(',','.'))
        
        processed_bags = [{'id': x, 'amount':bags[x]} for x in bags.keys()]
        return processed_lines, processed_bags, moneys, processing_date
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return [f"Error processing file: {str(e)}"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'zip'

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                # Process the zip file
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Find .chr files in the extracted content
                    chr_files = []
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower().endswith('.chr'):
                                chr_files.append(os.path.join(root, file))
                    
                    if not chr_files:
                        flash('No .chr files found in the uploaded zip file')
                        return redirect(request.url)
                    
                    # Process the first .chr file found
                    chr_file_path = chr_files[0]
                    processed_lines, processed_bags, moneys, process_date = process_chr_file(chr_file_path)
                    
                    # Clean up the uploaded file
                    os.remove(file_path)
                    
                    sheet_status = update_sheet(process_date, processed_bags)
                    return render_template('result.html', 
                                         lines=processed_lines,
                                         bags=processed_bags,
                                         moneys=moneys,
                                         datum=process_date,
                                         filename=os.path.basename(chr_file_path),
                                         sheetstate=sheet_status)
            
            except zipfile.BadZipFile:
                flash('Invalid zip file')
                return redirect(request.url)
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                return redirect(request.url)
            finally:
                # Clean up uploaded file if it still exists
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        else:
            flash('Please upload a valid zip file')
            return redirect(request.url)
    
    return render_template('upload.html')

# add route for GET on http://192.168.143.32:5005/register?code=1991571059344484 to register a new bag
# it should display a web page requesting additional data: source (default Polaris, Ausnutria, Robert, free text), type (mini, small) en afgiftedatum (default: today)
#@app.route('/register', methods=['GET'])
#def register():
#    # Get the code from query parameters
#    code = request.args.get('code', '')
#    
#    # Get today's date in ISO format for the date input default
#    today = datetime.now().strftime('%Y-%m-%d')
#    
#    return render_template('register.html', code=code, today=today)

#@app.route('/submit-registration', methods=['POST'])
#def submit_registration():
#    # Get form data
#    code = request.form.get('code')
#    source = request.form.get('source')
#    custom_source = request.form.get('customSource')
#    type_value = request.form.get('type')
#    afgiftedatum = request.form.get('afgiftedatum')
#    
#    # Use custom source if "custom" was selected
#    if source == 'custom' and custom_source:
#        source = custom_source
#    
#    # Here you would typically:
#    # - Validate the data
#    # - Save to database
#    # - Process the registration
#    # - Send confirmation email, etc.
#    
#    # For now, just print to console (for debugging)
#    print(f"Registration received:")
#    print(f"  Code: {code}")
#    print(f"  Source: {source}")
#    print(f"  Type: {type_value}")
#    print(f"  Afgiftedatum: {afgiftedatum}")
#    
#    # TODO: Add your business logic here
#    # Example:
#    # db.save_registration(code, source, type_value, afgiftedatum)
#    
#    # Return success page or redirect
#    return render_template('registration_success.html', 
#                         code=code, 
#                         source=source, 
#                         type_value=type_value, 
#                         afgiftedatum=afgiftedatum)


if __name__ == '__main__':
    app.run(debug=True, port=5005, host="0.0.0.0")
