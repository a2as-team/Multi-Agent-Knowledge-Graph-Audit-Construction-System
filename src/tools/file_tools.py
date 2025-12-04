"""
File operation tools for agents.
These tools handle file listing and sampling operations.
"""
import os
from pathlib import Path
from itertools import islice
from typing import Dict, Any

from google.adk.tools import ToolContext

from src.utils.constants import ALL_AVAILABLE_FILES
from src.utils.config import get_neo4j_import_dir
from src.utils.logger import logger
from src.neo4j.neo4j_for_adk import tool_success, tool_error


def get_data_directory() -> Path:
    """
    Get the data directory path for file operations.
    
    For Story 1, we use data/story1/ directly.
    Can be configured via environment variable or defaults to data/story1/
    
    Returns:
        Path object pointing to the data directory
    """
    # Try to get from Neo4j import directory first (if configured)
    neo4j_import_dir = get_neo4j_import_dir()
    if neo4j_import_dir:
        return Path(neo4j_import_dir)
    
    # Try to get from environment variable
    data_dir = os.getenv("DATA_DIRECTORY")
    if data_dir:
        return Path(data_dir)
    
    # Default to data/story1/ for Story 1
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data" / "story1"


def list_available_files(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Lists files available for knowledge graph construction.
    All files are relative to the data directory.
    
    For structured data agent, focuses on CSV/JSON files.
    The agent will filter based on file extensions.
    
    Args:
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and list of file names or error message.
        If 'success', includes 'all_available_files' key with list of file names.
        If 'error', includes 'error_message' key.
    """
    try:
        data_dir = get_data_directory()
        
        if not data_dir.exists():
            return tool_error(
                f"Data directory does not exist: {data_dir}. "
                "Please ensure the data directory is set up correctly."
            )
        
        # Get a list of relative file names, so files must be rooted at the data dir
        file_names = [
            str(x.relative_to(data_dir)) 
            for x in data_dir.rglob("*") 
            if x.is_file()
        ]
        
        # Save the list to state so we can inspect it later
        tool_context.state[ALL_AVAILABLE_FILES] = file_names
        
        logger.info(f"Listed {len(file_names)} files from {data_dir}")
        return tool_success(ALL_AVAILABLE_FILES, file_names)
    
    except Exception as e:
        error_msg = f"Error listing available files: {e}"
        logger.error(error_msg)
        return tool_error(error_msg)


def sample_file(file_path: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Samples a file by reading its content as text.
    
    Treats any file as text and reads up to a maximum of 100 lines.
    This tool works for CSV, JSON, Markdown, and other text files.
    
    Args:
        file_path: File to sample, relative to the data directory
        tool_context: ADK ToolContext containing state and other context
    
    Returns:
        Dictionary with status and file content or error message.
        If 'success', includes 'content' key with textual file content (up to 100 lines).
        If 'error', includes 'error_message' key.
    """
    # Trust, but verify. The agent may invent absolute file paths.
    if Path(file_path).is_absolute():
        return tool_error(
            "File path must be relative to the data directory. "
            "Make sure the file is from the list of available files."
        )
    
    try:
        data_dir = get_data_directory()
        
        # Create the full path by extending from the data_dir
        full_path_to_file = data_dir / file_path
        
        # Verify that the file exists
        if not full_path_to_file.exists():
            return tool_error(
                f"File does not exist in data directory: {file_path}. "
                "Make sure {file_path} is from the list of available files."
            )
        
        # Treat all files as text
        with open(full_path_to_file, 'r', encoding='utf-8') as file:
            # Read up to 100 lines
            lines = list(islice(file, 100))
            content = ''.join(lines)
            
            logger.info(f"Sampled file: {file_path} ({len(lines)} lines)")
            return tool_success("content", content)
    
    except UnicodeDecodeError:
        return tool_error(
            f"File {file_path} is not a text file or uses unsupported encoding. "
            "Only text files (CSV, JSON, Markdown, TXT) are supported."
        )
    except Exception as e:
        error_msg = f"Error reading or processing file {file_path}: {e}"
        logger.error(error_msg)
        return tool_error(error_msg)


def search_file(file_path: str, query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Searches any text file (markdown, csv, txt) for lines containing the given query string.
    Simple grep-like functionality that works with any text file.
    Search is always case insensitive.
    
    This tool is useful for verifying that columns exist in CSV files or finding specific content.

    Args:
        file_path: Path to the file, relative to the data directory.
        query: The string to search for.
        tool_context: ADK ToolContext containing state and other context

    Returns:
        Dictionary with status and search results or error message.
        If 'success', includes 'search_results' containing:
            - 'metadata': dict with path, query, lines_found
            - 'matching_lines': list of dicts with 'line_number' and 'content' keys
        If 'error', includes 'error_message' key.
    """
    # Trust, but verify. The agent may invent absolute file paths.
    if Path(file_path).is_absolute():
        return tool_error(
            "File path must be relative to the data directory. "
            "Make sure the file is from the list of available files."
        )
    
    try:
        data_dir = get_data_directory()
        full_path_to_file = data_dir / file_path

        if not full_path_to_file.exists():
            return tool_error(f"File does not exist: {file_path}")
        if not full_path_to_file.is_file():
            return tool_error(f"Path is not a file: {file_path}")

        # Handle empty query - return no results
        if not query:
            return tool_success("search_results", {
                "metadata": {
                    "path": file_path,
                    "query": query,
                    "lines_found": 0
                },
                "matching_lines": []
            })

        matching_lines = []
        search_query = query.lower()
        
        with open(full_path_to_file, 'r', encoding='utf-8') as file:
            # Process the file line by line
            for i, line in enumerate(file, 1):
                line_to_check = line.lower()
                if search_query in line_to_check:
                    matching_lines.append({
                        "line_number": i,
                        "content": line.strip()  # Remove trailing newlines
                    })
                        
    except UnicodeDecodeError:
        return tool_error(
            f"File {file_path} is not a text file or uses unsupported encoding. "
            "Only text files (CSV, JSON, Markdown, TXT) are supported."
        )
    except Exception as e:
        return tool_error(f"Error reading or searching file {file_path}: {e}")

    # Prepare basic metadata
    metadata = {
        "path": file_path,
        "query": query,
        "lines_found": len(matching_lines)
    }
    
    result_data = {
        "metadata": metadata,
        "matching_lines": matching_lines
    }
    
    logger.info(f"Searched file {file_path} for '{query}': {len(matching_lines)} matches")
    return tool_success("search_results", result_data)
