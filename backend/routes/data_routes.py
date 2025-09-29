from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import (
    DatasetResponse, SummaryResponse, UploadResponse, 
    DataResponse, DataRecordResponse
)
from services.data_processing import (
    process_uploaded_file, store_dataset_in_db, 
    get_dataset_summary, get_dataset_data
)
from utils.file_utils import save_uploaded_file
import os

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a data file (CSV, Excel, or JSON)
    
    This endpoint accepts file uploads, processes them with pandas,
    and stores the results in the database for later analysis.
    
    Args:
        file: The uploaded file (CSV, Excel, or JSON)
        db: Database session dependency
        
    Returns:
        UploadResponse with success status and dataset information
    """
    
    # Validate file type
    allowed_extensions = {'.csv', '.xlsx', '.xls', '.json'}
    file_extension = os.path.splitext(str(file.filename))[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    success, message, file_path = save_uploaded_file(file)
    if not success:
        raise HTTPException(status_code=500, detail=message)
    
    try:


        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file or filename provided")
        if not file_path:
            raise HTTPException(status_code=400, detail="Invalid file path")


        # Process the file
        success, message, data_info = process_uploaded_file(file_path, file.filename)
        if not success:
            # Clean up file on processing error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=message)
        
        # Store in database
        success, message, dataset_id = store_dataset_in_db(db, data_info)
        if not success:
            # Clean up file on database error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=message)
        
        return UploadResponse(
            success=True,
            message=f"File uploaded and processed successfully. {data_info['rows']} rows and {data_info['columns']} columns detected.",
            dataset_id=dataset_id,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file on unexpected error
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics and metadata for a dataset
    
    This endpoint returns comprehensive information about a dataset including
    row/column counts, data types, missing values, and basic insights.
    
    Args:
        dataset_id: ID of the dataset to analyze
        db: Database session dependency
        
    Returns:
        SummaryResponse with dataset statistics and insights
    """
    
    success, message, summary = get_dataset_summary(db, dataset_id)
    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=500, detail=message)
    
    return summary

@router.get("/data", response_model=DataResponse)
async def get_data(
    dataset_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve processed dataset for visualization
    
    This endpoint returns the actual data records from a dataset,
    formatted and ready for frontend visualization components.
    
    Args:
        dataset_id: ID of the dataset to retrieve
        limit: Maximum number of records to return (default: 100, max: 1000)
        db: Database session dependency
        
    Returns:
        DataResponse with data records and metadata
    """
    
    # Validate limit
    if limit > 1000:
        limit = 1000
    elif limit < 1:
        limit = 1
    
    success, message, data_list = get_dataset_data(db, dataset_id, limit)
    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=500, detail=message)
    
    # Get dataset info for metadata
    from models import Dataset
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    metadata = {
        "filename": dataset.filename,
        "upload_date": dataset.upload_date.isoformat(),
        "total_records_returned": len(data_list),
        "limit_applied": limit
    }
    
    return DataResponse(
        dataset_id=dataset_id,
        data=data_list,
        metadata=metadata
    )

@router.get("/datasets", response_model=List[DatasetResponse])
async def list_datasets(db: Session = Depends(get_db)):
    """
    List all uploaded datasets
    
    Returns a list of all datasets that have been uploaded to the system
    with their basic information.
    
    Args:
        db: Database session dependency
        
    Returns:
        List of DatasetResponse objects
    """
    
    from models import Dataset
    
    try:
        datasets = db.query(Dataset).order_by(Dataset.upload_date.desc()).all()
        return [
            DatasetResponse(
                id=dataset.id,
                filename=dataset.filename,
                upload_date=dataset.upload_date
            )
            for dataset in datasets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving datasets: {str(e)}")

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a dataset and its associated data
    
    This endpoint removes a dataset from the database and cleans up
    the associated file from disk.
    
    Args:
        dataset_id: ID of the dataset to delete
        db: Database session dependency
        
    Returns:
        Success message
    """
    
    from models import Dataset
    from utils.file_utils import cleanup_file
    
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Clean up file
        if os.path.exists(dataset.file_path):
            cleanup_file(dataset.file_path)
        
        # Delete from database (cascade will handle related records)
        db.delete(dataset)
        db.commit()
        
        return {"success": True, "message": "Dataset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting dataset: {str(e)}")