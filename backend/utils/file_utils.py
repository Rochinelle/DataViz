import os
import pandas as pd
from typing import Tuple, Optional
from pathlib import Path
import uuid
from fastapi import UploadFile

# Directory for storing uploaded files
UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

def save_uploaded_file(file: UploadFile) -> Tuple[bool, str, Optional[str]]:
    """
    Save uploaded file to disk
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple of (success, message, file_path)
    """
    try:
        # Generate unique filename to avoid conflicts
        file_extension = Path(file.filename or "").suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        
        return True, "File saved successfully", file_path
    
    except Exception as e:
        return False, f"Error saving file: {str(e)}", None

def read_file_with_pandas(file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Read file using pandas based on file extension
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Tuple of (success, message, dataframe)
    """
    try:
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_extension == '.json':
            df = pd.read_json(file_path)
        else:
            return False, f"Unsupported file type: {file_extension}", None
        
        # Basic validation
        if df.empty:
            return False, "File is empty", None
            
        return True, "File read successfully", df
    
    except Exception as e:
        return False, f"Error reading file: {str(e)}", None

def get_file_info(file_path: str) -> dict:
    """
    Get basic information about a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "extension": Path(file_path).suffix.lower(),
            "exists": True
        }
    except Exception:
        return {"exists": False}

def cleanup_file(file_path: str) -> bool:
    """
    Remove file from disk
    
    Args:
        file_path: Path to the file to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False