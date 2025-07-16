from flask import Flask, request, render_template, flash, redirect, url_for
import os
import zipfile
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

app = Flask(__name__)
app.config.from_pyfile('flaskconfig.py')
#app.config['SECRET_KEY'] = '10e41f90aee93e80ad364d942f54483f0af3d5d8be1c2a771c88186cbf72cdd6'
#d740fae4a2f67d0d62aaa7d209b01aa7750b8678b3ab58793024365d00c96eb4
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def process_chr_file(file_path):
    """
    Process a .chr file and return the result as lines of text.
    Modify this function according to your specific processing needs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Example processing: split into lines and add line numbers
        lines = content.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines, 1):
            if line.strip():  # Skip empty lines
                processed_lines.append(f"Line {i}: {line}")
        
        return processed_lines
        
    except UnicodeDecodeError:
        # Try binary mode if UTF-8 fails
        try:
            with open(file_path, 'rb') as file:
                content = file.read()
            
            # Convert binary content to hex representation
            hex_lines = []
            for i in range(0, len(content), 16):
                chunk = content[i:i+16]
                hex_str = ' '.join(f'{b:02x}' for b in chunk)
                hex_lines.append(f"Offset {i:04x}: {hex_str}")
            
            return hex_lines
            
        except Exception as e:
            return [f"Error processing file: {str(e)}"]
    
    except Exception as e:
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
                    processed_lines = process_chr_file(chr_file_path)
                    
                    # Clean up the uploaded file
                    os.remove(file_path)
                    
                    return render_template('result.html', 
                                         lines=processed_lines,
                                         filename=os.path.basename(chr_file_path))
            
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
