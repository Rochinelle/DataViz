from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatasetBase(BaseModel):
    """Base dataset schema"""
    filename: str = Field(..., description="Name of the uploaded file")

class DatasetCreate(DatasetBase):
    """Dataset creation schema"""
    file_path: str = Field(..., description="Path where the file is stored")

class DatasetResponse(DatasetBase):
    """Dataset response schema"""
    id: int = Field(..., description="Unique identifier for the dataset")
    upload_date: datetime = Field(..., description="When the dataset was uploaded")
    
    class Config:
        from_attributes = True

class DataRecordBase(BaseModel):
    """Base data record schema"""
    json_data: str = Field(..., description="JSON string representation of the record")

class DataRecordCreate(DataRecordBase):
    """Data record creation schema"""
    dataset_id: int = Field(..., description="ID of the associated dataset")

class DataRecordResponse(DataRecordBase):
    """Data record response schema"""
    id: int = Field(..., description="Unique identifier for the record")
    dataset_id: int = Field(..., description="ID of the associated dataset")
    
    class Config:
        from_attributes = True

class SummaryResponse(BaseModel):
    """Summary response schema for dataset statistics"""
    dataset_id: int = Field(..., description="ID of the dataset")
    filename: str = Field(..., description="Name of the file")
    rows: int = Field(..., description="Number of rows in the dataset")
    columns: int = Field(..., description="Number of columns in the dataset")
    column_names: List[str] = Field(..., description="List of column names")
    chart_count: int = Field(..., description="Number of suggested charts")
    insights: List[str] = Field(..., description="Generated insights about the data")
    upload_date: datetime = Field(..., description="When the dataset was uploaded")

class ChartSuggestion(BaseModel):
    """Chart suggestion schema"""
    chart_type: str = Field(..., description="Type of chart (e.g., 'bar', 'line', 'pie')")
    title: str = Field(..., description="Suggested title for the chart")
    description: str = Field(..., description="Description of what the chart shows")
    columns: List[str] = Field(..., description="Columns to be used in the chart")
    reasoning: str = Field(..., description="Why this chart is suggested")

class SuggestionsResponse(BaseModel):
    """Response schema for chart suggestions"""
    dataset_id: int = Field(..., description="ID of the dataset")
    suggestions: List[ChartSuggestion] = Field(..., description="List of chart suggestions")
    
class UploadResponse(BaseModel):
    """File upload response schema"""
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Success or error message")
    dataset_id: Optional[int] = Field(None, description="ID of the created dataset")
    filename: Optional[str] = Field(None, description="Name of the uploaded file")

class DataResponse(BaseModel):
    """Data retrieval response schema"""
    dataset_id: int = Field(..., description="ID of the dataset")
    data: List[Dict[str, Any]] = Field(..., description="The actual data records")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata about the data")