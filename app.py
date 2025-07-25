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

def update_sheet(processing_date: str, bags: dict)->str:
    spreadsheet_id='1DJmUp6qd7gZxrlHdUcjwTA1pnDFES7iYq_GfAoyNkHE'
    sheet_name='Blad1'

    sheets = SheetsManager('servicecredentials.json')
    for bag in bags:
        columns = sheets.get_column_names(spreadsheet_id, sheet_name)
        row_num = sheets.find_row_by_value(spreadsheet_id, sheet_name, bag['id'], columns['Zaknummer'])
        if row_num != None:
            sheets.write_to_sheet(spreadsheet_id, f'E{row_num}:G{row_num}', [['X', processing_date, bag['amount']]])
        else:
            # Find row number with first value higher than bag['id'] in variable 'position'
            # Insert row with correct values on that row number
            #result = insert_row_by_name(
                #spreadsheet_id, sheet_name, 
                #row_number=position, 
                #values=[[bag['id'],'', '', '', 'X', processing_date, bag['amount']]])
    return ''

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

if __name__ == '__main__':
    app.run(debug=True, port=5005, host="0.0.0.0")
