import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from schemas import ChartSuggestion, SuggestionsResponse
from models import Dataset
from utils.file_utils import read_file_with_pandas
from pandas.api.types import is_categorical_dtype  # type: ignore



def analyze_column_types(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Analyze columns to determine their characteristics for chart suggestions
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        Dictionary with column analysis
    """
    column_analysis = {}
    
    for col in df.columns:
        analysis = {
            "name": col,
            "dtype": str(df[col].dtype),
            "unique_count": df[col].nunique(),
            "null_count": df[col].isnull().sum(),
            "total_count": len(df),
            "is_numeric": pd.api.types.is_numeric_dtype(df[col]),
            "is_categorical": is_categorical_dtype(df[col]),
            "is_datetime": False,
            "is_continuous": False
        }
        
        # Determine if categorical
        if df[col].dtype == 'object' or is_categorical_dtype(df[col]):
            analysis["is_categorical"] = True
        elif analysis["is_numeric"] and analysis["unique_count"] < 20:
            analysis["is_categorical"] = True
        
        # Check for datetime patterns
        if df[col].dtype == 'object':
            sample_vals = df[col].dropna().astype(str).head(10)
            datetime_indicators = 0
            for val in sample_vals:
                if any(char in val for char in ['/', '-', ':']):
                    datetime_indicators += 1
            if datetime_indicators >= 5:  # Heuristic
                analysis["is_datetime"] = True
        
        # Determine if continuous numeric
        if analysis["is_numeric"] and not analysis["is_categorical"]:
            analysis["is_continuous"] = True
        
        # Calculate statistics if numeric
        if analysis["is_numeric"]:
            analysis.update({
                "mean": df[col].mean() if not df[col].isnull().all() else None,
                "std": df[col].std() if not df[col].isnull().all() else None,
                "min": df[col].min() if not df[col].isnull().all() else None,
                "max": df[col].max() if not df[col].isnull().all() else None
            })
        
        column_analysis[col] = analysis
    
    return column_analysis

def generate_chart_suggestions(column_analysis: Dict[str, Dict[str, Any]]) -> List[ChartSuggestion]:
    """
    Generate chart suggestions based on column analysis
    
    Args:
        column_analysis: Dictionary with column analysis results
        
    Returns:
        List of ChartSuggestion objects
    """
    suggestions = []
    
    # Get lists of different column types
    numeric_cols = [col for col, info in column_analysis.items() if info["is_numeric"]]
    categorical_cols = [col for col, info in column_analysis.items() if info["is_categorical"]]
    continuous_cols = [col for col, info in column_analysis.items() if info["is_continuous"]]
    datetime_cols = [col for col, info in column_analysis.items() if info["is_datetime"]]
    
    # Bar charts for categorical data
    for col in categorical_cols[:3]:  # Limit suggestions
        if column_analysis[col]["unique_count"] <= 15:  # Reasonable for bar chart
            suggestions.append(ChartSuggestion(
                chart_type="bar",
                title=f"Distribution of {col}",
                description=f"Bar chart showing the frequency of different values in {col}",
                columns=[col],
                reasoning=f"Column '{col}' is categorical with {column_analysis[col]['unique_count']} unique values, suitable for bar chart visualization"
            ))
    
    # Histograms for continuous numeric data
    for col in continuous_cols[:2]:  # Limit suggestions
        suggestions.append(ChartSuggestion(
            chart_type="histogram",
            title=f"Distribution of {col}",
            description=f"Histogram showing the distribution of values in {col}",
            columns=[col],
            reasoning=f"Column '{col}' is numeric and continuous, perfect for histogram to show data distribution"
        ))
    
    # Scatter plots for pairs of numeric columns
    if len(numeric_cols) >= 2:
        col1, col2 = numeric_cols[0], numeric_cols[1]
        suggestions.append(ChartSuggestion(
            chart_type="scatter",
            title=f"{col1} vs {col2}",
            description=f"Scatter plot showing the relationship between {col1} and {col2}",
            columns=[col1, col2],
            reasoning=f"Both '{col1}' and '{col2}' are numeric columns, ideal for exploring correlation with scatter plot"
        ))
    
    # Line charts for time series data
    if datetime_cols and numeric_cols:
        datetime_col = datetime_cols[0]
        numeric_col = numeric_cols[0]
        suggestions.append(ChartSuggestion(
            chart_type="line",
            title=f"{numeric_col} over {datetime_col}",
            description=f"Line chart showing how {numeric_col} changes over {datetime_col}",
            columns=[datetime_col, numeric_col],
            reasoning=f"Column '{datetime_col}' appears to be temporal and '{numeric_col}' is numeric, perfect for time series visualization"
        ))
    
    # Box plots for numeric data grouped by categorical
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        if column_analysis[cat_col]["unique_count"] <= 10:  # Reasonable for box plot
            suggestions.append(ChartSuggestion(
                chart_type="box",
                title=f"{num_col} by {cat_col}",
                description=f"Box plot showing the distribution of {num_col} across different {cat_col} categories",
                columns=[cat_col, num_col],
                reasoning=f"Column '{cat_col}' is categorical with few unique values, and '{num_col}' is numeric - ideal for comparing distributions"
            ))
    
    # Pie chart for categorical data with few categories
    for col in categorical_cols:
        if 2 <= column_analysis[col]["unique_count"] <= 8:  # Good range for pie chart
            suggestions.append(ChartSuggestion(
                chart_type="pie",
                title=f"Composition of {col}",
                description=f"Pie chart showing the proportional breakdown of {col}",
                columns=[col],
                reasoning=f"Column '{col}' has {column_analysis[col]['unique_count']} categories, suitable for showing proportions in a pie chart"
            ))
            break  # Only suggest one pie chart
    
    # Correlation heatmap if multiple numeric columns
    if len(numeric_cols) >= 3:
        suggestions.append(ChartSuggestion(
            chart_type="heatmap",
            title="Correlation Matrix",
            description="Heatmap showing correlations between numeric variables",
            columns=numeric_cols[:5],  # Limit to first 5 numeric columns
            reasoning="Multiple numeric columns detected - correlation heatmap will reveal relationships between variables"
        ))
    
    return suggestions

def get_suggestions_for_dataset(db: Session, dataset_id: int) -> Tuple[bool, str, Optional[SuggestionsResponse]]:
    """
    Generate chart suggestions for a specific dataset
    
    Args:
        db: Database session
        dataset_id: ID of the dataset
        
    Returns:
        Tuple of (success, message, suggestions_response)
    """
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return False, "Dataset not found", None
        
        # Read the dataset file
        file_path: str = str(dataset.file_path)
        success, message, df = read_file_with_pandas(file_path)
        if not success or df is None:
            return False, f"Error reading dataset: {message}", None
        
        # Analyze columns
        column_analysis = analyze_column_types(df)
        
        # Generate suggestions
        suggestions = generate_chart_suggestions(column_analysis)

        # Create response
        response = SuggestionsResponse(
            dataset_id=dataset_id,
            suggestions=suggestions
        )
        
        return True, f"Generated {len(suggestions)} chart suggestions", response
    
    except Exception as e:
        return False, f"Error generating suggestions: {str(e)}", None

def get_column_insights(df: pd.DataFrame) -> List[str]:
    """
    Generate insights about columns for suggestion context
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        List of insight strings
    """
    insights = []
    
    try:
        column_analysis = analyze_column_types(df)
        
        # Count different types
        numeric_count = sum(1 for info in column_analysis.values() if info["is_numeric"])
        categorical_count = sum(1 for info in column_analysis.values() if info["is_categorical"])
        datetime_count = sum(1 for info in column_analysis.values() if info["is_datetime"])
        
        if numeric_count > 0:
            insights.append(f"Dataset has {numeric_count} numeric column{'s' if numeric_count != 1 else ''} suitable for quantitative analysis")
        
        if categorical_count > 0:
            insights.append(f"Dataset has {categorical_count} categorical column{'s' if categorical_count != 1 else ''} good for grouping and comparison")
        
        if datetime_count > 0:
            insights.append(f"Dataset contains time-based data, enabling trend analysis over time")
        
        # Check for high cardinality categorical columns
        high_cardinality = [col for col, info in column_analysis.items() 
                          if info["is_categorical"] and info["unique_count"] > 20]
        if high_cardinality:
            insights.append(f"Columns {', '.join(high_cardinality[:2])} have high cardinality - consider filtering or grouping")
        
        # Check for columns with missing data
        missing_cols = [col for col, info in column_analysis.items() 
                       if info["null_count"] > 0]
        if missing_cols:
            insights.append(f"Missing data detected in {len(missing_cols)} column{'s' if len(missing_cols) != 1 else ''} - consider data cleaning")
    
    except Exception:
        insights.append("Column analysis completed")
    
    return insights