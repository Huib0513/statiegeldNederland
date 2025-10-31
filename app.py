"""
Flask application for processing CHR files and managing bags.
Refactored to separate routing from business logic.
"""
from flask import Flask, request, render_template, flash, redirect, url_for
from datetime import datetime
import zipfile

from services.file_service import FileService
from services.bag_service import BagService
from services.sheet_service import SheetService

app = Flask(__name__)
app.config.from_pyfile('flaskconfig.py')

# Configuration
UPLOAD_FOLDER = 'uploads'
SPREADSHEET_ID = '1DJmUp6qd7gZxrlHdUcjwTA1pnDFES7iYq_GfAoyNkHE'
SHEET_NAME = 'Blad1'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize services
file_service = FileService(UPLOAD_FOLDER)
bag_service = BagService()
sheet_service = SheetService()


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """Handle file upload and processing."""
    if request.method == 'POST':
        # Validate file presence
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if not file_service.is_allowed_file(file.filename):
            flash('Please upload a valid zip file')
            return redirect(request.url)
        
        file_path = None
        try:
            # Save uploaded file
            file_path = file_service.save_uploaded_file(file)
            
            # Extract CHR files
            chr_files = file_service.extract_chr_files_from_zip(file_path)
            
            # Process the first CHR file
            chr_file = chr_files[0]
            processed_lines, processed_bags, total_money, process_date = \
                bag_service.process_chr_content(chr_file['content'])
            
            # Update Google Sheet
            sheet_result = sheet_service.update_bags_in_sheet(
                SPREADSHEET_ID, SHEET_NAME, process_date, processed_bags
            )
            
            return render_template(
                'result.html',
                lines=processed_lines,
                bags=processed_bags,
                moneys=total_money,
                datum=process_date,
                filename=chr_file['name'],
                sheetstate=sheet_result['message']
            )
        
        except zipfile.BadZipFile:
            flash('Invalid zip file')
            return redirect(request.url)
        except ValueError as e:
            flash(str(e))
            return redirect(request.url)
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(request.url)
        finally:
            # Cleanup
            if file_path:
                file_service.cleanup_file(file_path)
    
    return render_template('upload.html')


@app.route('/register', methods=['GET'])
def register():
    """Display bag registration form."""
    # Get the code from query parameters (can be multiple)
    codes = request.args.getlist('code')
    
    # If single code parameter, convert to list
    if not codes:
        code_param = request.args.get('code', '')
        codes = [code_param] if code_param else ['']
    
    # Get today's date in ISO format
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('register.html', codes=codes, today=today)


@app.route('/submit-registration', methods=['POST'])
def submit_registration():
    """Process bag registration form submission."""
    # Debug: Print all form data
    #print("DEBUG: Form data received:")
    #print(f"  All form keys: {list(request.form.keys())}")
    #print(f"  codes[]: {request.form.getlist('codes[]')}")
    #print(f"  code: {request.form.get('code')}")
    
    # Get common form data
    source = request.form.get('source')
    custom_source = request.form.get('customSource')
    type_value = request.form.get('type')
    afgiftedatum = request.form.get('afgiftedatum')
    
    # Use custom source if selected
    if source == 'custom' and custom_source:
        source = custom_source
    
    # Get all bag codes (support multiple bags)
    # Try different form field names
    codes = request.form.getlist('codes[]')
    
    # Fallback to single code if codes[] not present
    if not codes or (len(codes) == 1 and not codes[0].strip()):
        single_code = request.form.get('code')
        if single_code:
            codes = [single_code]
    
    # Filter out empty codes
    codes = [code.replace("1991571", "").strip() for code in codes if code and code.strip()]
    
    #print(f"DEBUG: Processed codes: {codes}")
    
    if not codes:
        flash('No bag codes provided')
        return redirect(url_for('register'))
    
    # Validate all bags
    validation_errors = []
    for code in codes:
        errors = bag_service.validate_bag_data(code, source, type_value, afgiftedatum)
        if errors:
            validation_errors.append(f"Bag {code}: {', '.join(errors.values())}")
    
    if validation_errors:
        for error in validation_errors:
            flash(error)
        return redirect(url_for('register'))
    
    # Register all bags
    results = []
    for code in codes:
        result = sheet_service.register_bag(
            SPREADSHEET_ID, SHEET_NAME, 
            code, source, type_value, afgiftedatum
        )
        results.append({
            'code': code,
            'success': result['success'],
            'message': result['message']
        })
    
    # Check if all succeeded
    all_success = all(r['success'] for r in results)
    
    return render_template(
        'registration_success.html',
        results=results,
        all_success=all_success,
        source=source,
        type_value=type_value,
        afgiftedatum=afgiftedatum
    )


if __name__ == '__main__':
    app.run(debug=True, port=62159, host="0.0.0.0")
