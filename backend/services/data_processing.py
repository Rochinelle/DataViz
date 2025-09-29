import json
import pandas as pd
from typing import Tuple, Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models import Dataset, DataRecord
from schemas import DatasetCreate, DataRecordCreate, SummaryResponse
from utils.file_utils import read_file_with_pandas
from pandas.api.types import is_categorical_dtype  # type: ignore
from sqlalchemy.orm import Session
from typing import cast
from datetime import datetime


def process_uploaded_file(file_path: str, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Process uploaded file and extract basic information
    
    Args:
        file_path: Path to the uploaded file
        filename: Original filename
        
    Returns:
        Tuple of (success, message, data_info)
    """
    try:
        # Read file with pandas
        success, message, df = read_file_with_pandas(file_path)
        if not success or df is None:
            return False, message, {}
        
        # Extract basic information
        data_info = {
            "filename": filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "sample_data": df.head().to_dict('records'),
            "null_counts": df.isnull().sum().to_dict(),
            "file_path": file_path
        }
        
        return True, "File processed successfully", data_info
    
    except Exception as e:
        return False, f"Error processing file: {str(e)}", {}

def get_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for a DataFrame
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        Dictionary containing summary statistics
    """
    try:
        summary = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "column_info": {},
            "missing_data": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict(),
        }
        
        # Analyze each column
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "null_count": df[col].isnull().sum(),
                "unique_count": df[col].nunique(),
            }
            
            # Add statistics based on data type
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update({
                    "mean": df[col].mean() if not df[col].isnull().all() else None,
                    "std": df[col].std() if not df[col].isnull().all() else None,
                    "min": df[col].min() if not df[col].isnull().all() else None,
                    "max": df[col].max() if not df[col].isnull().all() else None,
                })
            elif is_categorical_dtype(df[col]) or df[col].dtype == 'object':
                # Get top categories
                top_values = df[col].value_counts().head().to_dict()
                col_info["top_values"] = top_values
            
            summary["column_info"][col] = col_info
        
        return summary
    
    except Exception as e:
        return {"error": f"Error generating summary: {str(e)}"}

def store_dataset_in_db(db: Session, data_info: Dict[str, Any]) -> Tuple[bool, str, int]:
    """
    Store dataset information in database
    
    Args:
        db: Database session
        data_info: Dictionary containing dataset information
        
    Returns:
        Tuple of (success, message, dataset_id)
    """
    try:
        # Create dataset record
        dataset = Dataset(
            filename=data_info["filename"],
            file_path=data_info["file_path"]
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Read the actual data file again to store records
        success, message, df = read_file_with_pandas(data_info["file_path"])
        if not success or df is None:
            return False, f"Error reading file for storage: {message}", 0
        
        # Store data records (limit to first 1000 rows for performance)
        records_to_store = min(1000, len(df))
        for idx, row in df.head(records_to_store).iterrows():
            record_data = row.to_dict()
            # Handle NaN values
            for key, value in record_data.items():
                if pd.isna(value):
                    record_data[key] = None
            
            data_record = DataRecord(
                dataset_id=dataset.id,
                json_data=json.dumps(record_data, default=str)
            )
            db.add(data_record)
        
        db.commit()
        return True, f"Dataset stored successfully with {records_to_store} records", cast(int, dataset.id)
    
    except Exception as e:
        db.rollback()
        return False, f"Error storing dataset: {str(e)}", 0

def get_dataset_summary(db: Session, dataset_id: int) -> Tuple[bool, str, Optional[SummaryResponse]]:
    """
    Get summary information for a dataset
    
    Args:
        db: Database session
        dataset_id: ID of the dataset
        
    Returns:
        Tuple of (success, message, summary_response)
    """
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return False, "Dataset not found", None
        
        # Read file to get current statistics
        file_path: str = str(dataset.file_path)
        success, message, df = read_file_with_pandas(file_path)
        if not success or df is None:
            return False, f"Error reading dataset file: {message}", None
        
        # Generate insights
        insights = generate_basic_insights(df)
        summary = SummaryResponse(
            dataset_id=int(getattr(dataset, "id", 0)),
            filename=str(dataset.filename),
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
            chart_count=min(len(df.columns), 5),  # Basic estimation
            insights=insights,
            upload_date=getattr(dataset, "upload_date", datetime.now())
        )
        
        
        return True, "Summary generated successfully", summary
    
    except Exception as e:
        return False, f"Error generating summary: {str(e)}", None

def get_dataset_data(db: Session, dataset_id: int, limit: int = 100) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Get actual data from a dataset
    
    Args:
        db: Database session
        dataset_id: ID of the dataset
        limit: Maximum number of records to return
        
    Returns:
        Tuple of (success, message, data_list)
    """
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return False, "Dataset not found", []
        
        # Get data records from database
        records = db.query(DataRecord).filter(
            DataRecord.dataset_id == dataset_id
        ).limit(limit).all()
        
        # Convert to list of dictionaries
        data_list = []
        for record in records:
            try:

                json_str = str(record.json_data)
                data = json.loads(json_str)
                data_list.append(data)
            except json.JSONDecodeError:
                continue
        
        return True, f"Retrieved {len(data_list)} records", data_list
    
    except Exception as e:
        return False, f"Error retrieving data: {str(e)}", []

def generate_basic_insights(df: pd.DataFrame) -> List[str]:
    """
    Generate basic insights about the dataset
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        List of insight strings
    """
    insights = []
    
    try:
        # Basic statistics
        insights.append(f"Dataset contains {len(df)} rows and {len(df.columns)} columns")
        
        # Check for missing data
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_pct > 10:
            insights.append(f"Dataset has {missing_pct:.1f}% missing values")
        elif missing_pct > 0:
            insights.append(f"Dataset has {missing_pct:.1f}% missing values")
        else:
            insights.append("Dataset has no missing values")
        
        # Analyze column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if numeric_cols:
            insights.append(f"Found {len(numeric_cols)} numeric columns: {', '.join(numeric_cols[:3])}{'...' if len(numeric_cols) > 3 else ''}")
        
        if categorical_cols:
            insights.append(f"Found {len(categorical_cols)} categorical columns: {', '.join(categorical_cols[:3])}{'...' if len(categorical_cols) > 3 else ''}")
        
        # Check for potential date columns
        date_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                sample_values = df[col].dropna().astype(str).head()
                if any('/' in str(val) or '-' in str(val) for val in sample_values):
                    date_columns.append(col)
        
        if date_columns:
            insights.append(f"Potential date columns detected: {', '.join(date_columns[:2])}")
        
    except Exception:
        insights.append("Basic dataset analysis completed")
    
    return insights