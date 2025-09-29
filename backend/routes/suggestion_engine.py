from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import SuggestionsResponse
from services.suggestion_engine import get_suggestions_for_dataset

router = APIRouter()

@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    dataset_id: int = Query(..., description="ID of the dataset to analyze"),
    db: Session = Depends(get_db)
):
    """
    Generate chart and visualization suggestions for a dataset
    
    This endpoint analyzes the structure and content of a dataset to provide
    intelligent suggestions for charts and visualizations. It considers:
    - Column data types (numeric, categorical, datetime)
    - Data distributions and patterns  
    - Relationships between columns
    - Best practices for different chart types
    
    The suggestions include specific chart types, column recommendations,
    and reasoning for why each chart would be effective.
    
    Args:
        dataset_id: ID of the dataset to analyze
        db: Database session dependency
        
    Returns:
        SuggestionsResponse with chart suggestions and reasoning
        
    Raises:
        HTTPException: 404 if dataset not found, 500 for processing errors
    """
    
    try:
        success, message, suggestions_response = get_suggestions_for_dataset(db, dataset_id)
        
        if not success:
            if "not found" in message.lower():
                raise HTTPException(
                    status_code=404,
                    detail=f"Dataset with ID {dataset_id} not found"
                )
            raise HTTPException(status_code=500, detail=message)
        
        return suggestions_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error generating suggestions: {str(e)}"
        )

@router.get("/suggestions/{dataset_id}/insights")
async def get_dataset_insights(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed insights about a dataset's structure for visualization planning
    
    This endpoint provides in-depth analysis of the dataset structure,
    including column types, data quality issues, and strategic insights
    for creating effective visualizations.
    
    Args:
        dataset_id: ID of the dataset to analyze
        db: Database session dependency
        
    Returns:
        Dictionary with detailed dataset insights
        
    Raises:
        HTTPException: 404 if dataset not found, 500 for processing errors
    """
    
    try:
        from models import Dataset
        from utils.file_utils import read_file_with_pandas
        from services.suggestion_engine import analyze_column_types, get_column_insights
        
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset with ID {dataset_id} not found"
            )
        
        # Read the dataset file
        file_path: str = str(dataset.file_path)
        success, message, df = read_file_with_pandas(file_path)
        if not success or df is None:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading dataset: {message}"
            )
        
        # Analyze columns
        column_analysis = analyze_column_types(df)
        insights = get_column_insights(df)
        
        # Compile detailed insights
        detailed_insights = {
            "dataset_id": dataset_id,
            "filename": dataset.filename,
            "upload_date": dataset.upload_date.isoformat(),
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "column_analysis": column_analysis,
            "strategic_insights": insights,
            "data_quality": {
                "missing_data_percentage": round((df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2),
                "duplicate_rows": df.duplicated().sum(),
                "columns_with_missing_data": df.columns[df.isnull().any()].tolist(),
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2)
            },
            "recommendations": {
                "best_for_trends": [col for col, info in column_analysis.items() if info.get("is_datetime")],
                "best_for_categories": [col for col, info in column_analysis.items() if info.get("is_categorical") and info["unique_count"] <= 10],
                "best_for_distributions": [col for col, info in column_analysis.items() if info.get("is_continuous")],
                "best_for_correlations": [col for col, info in column_analysis.items() if info.get("is_numeric")][:5]
            }
        }
        
        return detailed_insights
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error analyzing dataset: {str(e)}"
        )

@router.get("/chart-types")
async def get_supported_chart_types():
    """
    Get information about supported chart types and their use cases
    
    This endpoint returns metadata about all chart types that the suggestion
    engine can recommend, including their ideal use cases and data requirements.
    
    Returns:
        Dictionary with chart type information and guidelines
    """
    
    chart_types = {
        "bar": {
            "name": "Bar Chart",
            "description": "Shows categorical data with rectangular bars",
            "best_for": ["Categorical data", "Frequency distributions", "Comparisons between categories"],
            "data_requirements": ["One categorical column", "Optionally one numeric column for values"],
            "ideal_categories": "2-15 unique values"
        },
        "histogram": {
            "name": "Histogram", 
            "description": "Shows distribution of continuous numerical data",
            "best_for": ["Data distributions", "Frequency of numeric ranges", "Identifying patterns and outliers"],
            "data_requirements": ["One continuous numeric column"],
            "ideal_categories": "Continuous data with many values"
        },
        "scatter": {
            "name": "Scatter Plot",
            "description": "Shows relationship between two numeric variables",
            "best_for": ["Correlation analysis", "Pattern detection", "Outlier identification"],
            "data_requirements": ["Two numeric columns"],
            "ideal_categories": "Continuous numeric data"
        },
        "line": {
            "name": "Line Chart",
            "description": "Shows trends over time or ordered categories",
            "best_for": ["Time series data", "Trend analysis", "Sequential data"],
            "data_requirements": ["One datetime/ordered column", "One numeric column"],
            "ideal_categories": "Time-based or sequential data"
        },
        "box": {
            "name": "Box Plot",
            "description": "Shows distribution summary with quartiles and outliers",
            "best_for": ["Distribution comparison", "Outlier detection", "Statistical summaries"],
            "data_requirements": ["One categorical column", "One numeric column"],
            "ideal_categories": "2-10 categories for comparison"
        },
        "pie": {
            "name": "Pie Chart",
            "description": "Shows proportional relationships as parts of a whole",
            "best_for": ["Proportional data", "Part-to-whole relationships", "Percentage breakdowns"],
            "data_requirements": ["One categorical column with frequencies"],
            "ideal_categories": "2-8 categories maximum"
        },
        "heatmap": {
            "name": "Heatmap",
            "description": "Shows correlation matrix or 2D data patterns",
            "best_for": ["Correlation analysis", "Pattern detection", "Matrix visualization"],
            "data_requirements": ["Multiple numeric columns for correlation", "Or two categorical + one numeric"],
            "ideal_categories": "3+ numeric variables"
        }
    }
    
    return {
        "supported_charts": chart_types,
        "selection_guidelines": {
            "for_exploration": ["histogram", "scatter", "box"],
            "for_comparison": ["bar", "box", "heatmap"],
            "for_trends": ["line", "scatter"],
            "for_composition": ["pie", "bar"],
            "for_correlation": ["scatter", "heatmap"]
        },
        "data_size_recommendations": {
            "small_datasets": "< 100 rows - All chart types suitable",
            "medium_datasets": "100-1000 rows - Consider sampling for scatter plots",
            "large_datasets": "> 1000 rows - Use aggregation or sampling"
        }
    }