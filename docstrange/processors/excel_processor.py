"""Excel file processor."""

import os
import logging
from typing import Dict, Any

from .base import BaseProcessor
from ..result import ConversionResult
from ..exceptions import ConversionError, FileNotFoundError

# Configure logging
logger = logging.getLogger(__name__)


class ExcelProcessor(BaseProcessor):
    """Processor for Excel files (XLSX, XLS) and CSV files."""
    
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this processor can handle the file
        """
        if not os.path.exists(file_path):
            return False
        
        # Check file extension - ensure file_path is a string
        file_path_str = str(file_path)
        _, ext = os.path.splitext(file_path_str.lower())
        return ext in ['.xlsx', '.xls', '.csv']
    
    def process(self, file_path: str) -> ConversionResult:
        """Process the Excel file and return a conversion result.
        
        Args:
            file_path: Path to the Excel file to process
            
        Returns:
            ConversionResult containing the processed content
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ConversionError: If processing fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file extension - ensure file_path is a string
        file_path_str = str(file_path)
        _, ext = os.path.splitext(file_path_str.lower())
        
        if ext == '.csv':
            return self._process_csv(file_path)
        else:
            return self._process_excel(file_path)
    
    def _process_csv(self, file_path: str) -> ConversionResult:
        """Process a CSV file and return a conversion result.
        
        Args:
            file_path: Path to the CSV file to process
            
        Returns:
            ConversionResult containing the processed content
        """
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            content_parts = []
            
            content_parts.append(f"# CSV Data: {os.path.basename(file_path)}")
            content_parts.append("")
            
            # Convert DataFrame to markdown table
            table_md = self._dataframe_to_markdown(df, pd)
            content_parts.append(table_md)
            
            metadata = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "extractor": "pandas"
            }
            
            content = '\n'.join(content_parts)
            
            return ConversionResult(content, metadata)
            
        except ImportError:
            raise ConversionError("pandas is required for CSV processing. Install it with: pip install pandas")
        except Exception as e:
            raise ConversionError(f"Failed to process CSV file {file_path}: {str(e)}")
    
    def _process_excel(self, file_path: str) -> ConversionResult:
        """Process an Excel file and return a conversion result.
        
        Args:
            file_path: Path to the Excel file to process
            
        Returns:
            ConversionResult containing the processed content
        """
        try:
            import pandas as pd
            
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            metadata = {
                "sheet_count": len(sheet_names),
                "sheet_names": sheet_names,
                "extractor": "pandas"
            }
            
            content_parts = []
            
            for sheet_name in sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                if not df.empty:
                    content_parts.append(f"\n## Sheet: {sheet_name}")
                    content_parts.append("")
                    
                    # Convert DataFrame to markdown table
                    table_md = self._dataframe_to_markdown(df, pd)
                    content_parts.append(table_md)
                    content_parts.append("")
                    
                    # Add metadata for this sheet
                    metadata.update({
                        f"sheet_{sheet_name}_rows": len(df),
                        f"sheet_{sheet_name}_columns": len(df.columns),
                        f"sheet_{sheet_name}_columns_list": df.columns.tolist()
                    })
            
            content = '\n'.join(content_parts)
            
            return ConversionResult(content, metadata)
            
        except ImportError:
            raise ConversionError("pandas and openpyxl are required for Excel processing. Install them with: pip install pandas openpyxl")
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ConversionError)):
                raise
            raise ConversionError(f"Failed to process Excel file {file_path}: {str(e)}")
    
    def _dataframe_to_markdown(self, df, pd) -> str:
        """Convert pandas DataFrame to markdown table.
        
        Args:
            df: pandas DataFrame
            pd: pandas module reference
            
        Returns:
            Markdown table string
        """
        if df.empty:
            return "*No data available*"
        
        # Convert DataFrame to markdown table
        markdown_parts = []
        
        # Header
        markdown_parts.append("| " + " | ".join(str(col) for col in df.columns) + " |")
        markdown_parts.append("| " + " | ".join(["---"] * len(df.columns)) + " |")
        
        # Data rows
        for _, row in df.iterrows():
            row_data = []
            for cell in row:
                if pd.isna(cell):
                    row_data.append("")
                else:
                    row_data.append(str(cell))
            markdown_parts.append("| " + " | ".join(row_data) + " |")
        
        return "\n".join(markdown_parts)
    
    def _clean_content(self, content: str) -> str:
        """Clean up the extracted Excel content.
        
        Args:
            content: Raw Excel text content
            
        Returns:
            Cleaned text content
        """
        # Remove excessive whitespace and normalize
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove excessive whitespace
            line = ' '.join(line.split())
            if line.strip():
                cleaned_lines.append(line)
        
        # Join lines and add proper spacing
        content = '\n'.join(cleaned_lines)
        
        # Add spacing around headers
        content = content.replace('# ', '\n# ')
        content = content.replace('## ', '\n## ')
        
        return content.strip() 