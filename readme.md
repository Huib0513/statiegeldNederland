# Statiegeld Nederland - CHR File Processor

A Flask web application for processing CHR (deposit) files from Statiegeld Nederland and managing bag registrations via Google Sheets.

## 🎯 Features

### CHR File Processing
- Upload ZIP files containing CHR files
- Automatic extraction and processing of deposit data
- Real-time calculation of bags and amounts
- Automatic synchronization with Google Sheets

### Bag Registration
- Register single or multiple bags simultaneously
- Pre-fill functionality for easy sequential registration
- Support for custom sources and bag types
- Duplicate detection and validation
- Individual success/failure tracking per bag

### Google Sheets Integration
- Automatic updates to existing bags
- Smart insertion of new bags in sorted order
- Column mapping with validation
- Batch processing support

## 📋 Requirements

- Python 3.7+
- Google Cloud Service Account with Sheets API access
- Flask 2.3.3+

## 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/Huib0513/statiegeldNederland.git
cd statiegeldNederland
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Google Sheets credentials**
- Create a Google Cloud Service Account
- Download the credentials JSON file
- Save it as `servicecredentials.json` in the project root
- Share your Google Sheet with the service account email

5. **Create Flask configuration**
```python
# flaskconfig.py
SECRET_KEY = 'your-secret-key-here'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
```

6. **Update spreadsheet ID**
Edit `app.py` and replace the `SPREADSHEET_ID` with your Google Sheets ID:
```python
SPREADSHEET_ID = 'your-spreadsheet-id-here'
```

## 🏃 Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5005`

## 📖 Usage

### Processing CHR Files

1. Navigate to the home page (`http://localhost:5005/`)
2. Upload a ZIP file containing CHR files
3. The system will:
   - Extract the CHR file
   - Process all bag records
   - Calculate totals
   - Update Google Sheets automatically
4. View the processing results

### Registering Bags

#### Single Bag Registration
```
http://localhost:5005/register?code=12345
```
Pre-fills the form with bag ID `12345`

Using the Cognex barcode scanner app will turn your smartphone into a barcode scanner and allow you to configure the correct URL for registration.
There are probably more apps doing this, but Cognex works for me. I have no further knowledge of this app or its creators.

#### Multiple Bags Registration
```
http://localhost:5005/register?code=12345&code=67890
```
Pre-fills the form with multiple bag IDs

#### Manual Registration
1. Navigate to `http://localhost:5005/register`
2. Enter the first bag ID
3. Click "+ Voeg nog een zak toe" to add more bags
   - New fields auto-fill with the previous ID value
   - Text is auto-selected for easy editing
4. Fill in common details (source, type, date)
5. Submit to register all bags

### Bag Registration Fields

- **Zaknummer (Bag ID)**: Unique identifier for the bag
- **Source**: Origin of the bag
  - Polaris
  - Ausnutria
  - Robert
  - Custom (free text)
- **Type**: Bag size
  - Mini
  - Small
- **Afgiftedatum (Submission Date)**: Date of bag submission

## 🏗️ Project Structure

```
statiegeldNederland/
├── app.py                          # Main Flask application (routing)
├── services/                       # Business logic layer
│   ├── __init__.py                 # Package initialization
│   ├── bag_service.py              # Bag processing logic
│   ├── sheet_service.py            # Google Sheets operations
│   └── file_service.py             # File handling operations
├── sheetsmanager.py                # Google Sheets API wrapper
├── templates/                      # HTML templates
│   ├── base.html                   # Base template
│   ├── upload.html                 # File upload page
│   ├── result.html                 # Processing results
│   ├── register.html               # Bag registration form
│   └── registration_success.html   # Registration confirmation
├── uploads/                        # Temporary upload directory
├── requirements.txt                # Python dependencies
├── flaskconfig.py                  # Flask configuration (not in git)
└── servicecredentials.json         # Google credentials (not in git)
```

## 🏛️ Architecture

This project follows a clean architecture pattern with separation of concerns:

### Service Layer
- **BagService**: Business logic for CHR file processing and validation
- **SheetService**: All Google Sheets operations and data management
- **FileService**: File upload, validation, and extraction

### Benefits
- ✅ Separation of routing and business logic
- ✅ Testable and maintainable code
- ✅ Reusable service components
- ✅ Easy to extend and modify

## 🔒 Security Notes

**Never commit these files to version control:**
- `flaskconfig.py` - Contains secret keys
- `servicecredentials.json` - Contains Google Cloud credentials

These files are already listed in `.gitignore`

## 📊 Google Sheets Format

Your Google Sheet should have the following columns:

| Column | Name | Description |
|--------|------|-------------|
| A | Zaknummer | Bag ID (unique identifier) |
| B | Source | Origin of the bag |
| C | Type | Bag type (mini/small) |
| D | Afgiftedatum | Submission date |
| E | Verwerkt | Processing status (X when processed) |
| F | Verwerkingsdatum | Processing date |
| G | Bedrag | Amount in euros |

## 🔧 Configuration

### Changing the Spreadsheet
Edit `app.py`:
```python
SPREADSHEET_ID = 'your-new-spreadsheet-id'
SHEET_NAME = 'your-sheet-name'  # Default: 'Blad1'
```

### Changing Upload Settings
Edit `flaskconfig.py`:
```python
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # Change to 32MB
```

### Changing Port
Edit `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=8080, host="0.0.0.0")  # Change port to 8080
```

## 🧪 Testing

### Manual Testing Checklist

#### CHR Processing
- [ ] Upload valid ZIP with CHR file
- [ ] Upload invalid ZIP file
- [ ] Upload ZIP without CHR files
- [ ] Verify bag counts and amounts
- [ ] Check Google Sheets updates
- [ ] Test with large CHR files

#### Bag Registration
- [ ] Register single bag
- [ ] Register multiple bags at once
- [ ] Use custom source option
- [ ] Try registering duplicate bag (should fail)
- [ ] Verify auto-fill on adding bags
- [ ] Check data appears correctly in Google Sheets

## 🐛 Troubleshooting

### Import Errors
**Problem**: `ModuleNotFoundError: No module named 'services'`

**Solution**: Ensure `services/__init__.py` exists and the directory structure is correct

### Google Sheets Authentication Failed
**Problem**: Cannot connect to Google Sheets

**Solutions**:
- Verify `servicecredentials.json` exists and is valid
- Check the service account has access to the spreadsheet
- Ensure Google Sheets API is enabled in Google Cloud Console

### File Upload Fails
**Problem**: File upload returns error

**Solutions**:
- Check file is a valid ZIP file
- Verify file size is under the limit (16MB default)
- Ensure ZIP contains at least one `.chr` file
- Check `uploads/` directory has write permissions

### Multiple Bag Registration Not Working
**Problem**: Only first bag is registered

**Solution**: Verify form inputs use `name="codes[]"` with brackets

### Bags Inserted in Wrong Position
**Problem**: New bags appear in wrong order in sheet

**Solution**: Ensure Zaknummer column contains numeric IDs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards
- Keep business logic in service classes
- Keep routes thin (HTTP concerns only)
- Add docstrings to all functions
- Follow PEP 8 style guide
- Write meaningful commit messages

## 📝 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 👥 Authors

- **Huib0513** - [GitHub Profile](https://github.com/Huib0513)

## 🙏 Acknowledgments

- Google Sheets API team
- Flask framework
- Contributors and testers

## 📞 Support

For questions or issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Search existing [Issues](https://github.com/Huib0513/statiegeldNederland/issues)
3. Open a new issue with detailed information

## 🗺️ Roadmap

Future enhancements planned:
- [ ] Database integration for local storage
- [ ] User authentication and permissions
- [ ] Email notifications on registration
- [ ] Bulk CHR file processing
- [ ] Export functionality (CSV/Excel)
- [ ] REST API endpoints
- [ ] Dashboard with statistics
- [ ] Mobile-responsive design improvements

## 📈 Changelog

### Version 2.0.0 (Current)
- ✨ Refactored architecture with service layer
- ✨ Multiple bag registration support
- ✨ Auto-fill functionality for sequential IDs
- ✨ Improved error handling and validation
- ✨ Individual success/failure tracking
- 🐛 Fixed insert position calculation
- 📝 Comprehensive documentation

### Version 1.0.0
- Initial release
- CHR file processing
- Single bag registration
- Google Sheets integration

---

Made with ❤️ for Statiegeld Nederland
