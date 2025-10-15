"""
Business logic for file handling operations.
Handles file uploads, validation, and extraction.
"""
import os
import zipfile
import tempfile
from typing import List, Optional
from werkzeug.utils import secure_filename


class FileService:
    """Service class for file operations."""
    
    def __init__(self, upload_folder: str):
        """
        Initialize the file service.
        
        Args:
            upload_folder: Path to the upload folder
        """
        self.upload_folder = upload_folder
        self._ensure_upload_folder()
    
    def _ensure_upload_folder(self):
        """Ensure upload folder exists."""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """
        Check if the file has an allowed extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file is allowed, False otherwise
        """
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'zip'
    
    def save_uploaded_file(self, file) -> str:
        """
        Save uploaded file to the upload folder.
        
        Args:
            file: Werkzeug FileStorage object
            
        Returns:
            Path to the saved file
        """
        filename = secure_filename(file.filename)
        file_path = os.path.join(self.upload_folder, filename)
        file.save(file_path)
        return file_path
    
    @staticmethod
    def extract_chr_files_from_zip(zip_path: str) -> List[str]:
        """
        Extract CHR files from a zip archive.
        
        Args:
            zip_path: Path to the zip file
            
        Returns:
            List of paths to extracted CHR files
            
        Raises:
            zipfile.BadZipFile: If the zip file is invalid
            ValueError: If no CHR files found
        """
        chr_files = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find .chr files in the extracted content
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith('.chr'):
                        chr_file_path = os.path.join(root, file)
                        
                        # Read the content and store it (since temp_dir will be deleted)
                        with open(chr_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        chr_files.append({
                            'name': file,
                            'content': content
                        })
        
        if not chr_files:
            raise ValueError("No .chr files found in the uploaded zip file")
        
        return chr_files
    
    @staticmethod
    def cleanup_file(file_path: str):
        """
        Delete a file if it exists.
        
        Args:
            file_path: Path to the file to delete
        """
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {str(e)}")
