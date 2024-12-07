# copied and modified from https://github.com/ServiceNow/BrowserGym
import playwright.sync_api
import playwright.sync_api
from abc import ABC, abstractmethod
import ast
import sys
import os
import importlib.util
import logging
from typing import Any, Callable, Optional, Tuple
from pathlib import Path
import ast
from typing import Any, Callable, Dict, Optional
import playwright.sync_api
import os
from datetime import datetime
import sys
from typing import Any, Callable, Optional
import importlib.util

logger = logging.getLogger(__name__)

def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate Python code syntax using AST parser.
    
    Args:
        code: String containing Python code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        error_msg = f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"
        return False, error_msg
    except Exception as e:
        return False, f"Parsing error: {str(e)}"

def execute_python_code_safely(
    code: str,
    page: 'playwright.sync_api.Page',
    context: Any,
    log_folder: str,
    send_message_to_user: Optional[Callable[[str], None]] = None,
    report_infeasible_instructions: Optional[Callable[[str], None]] = None
) -> str:
    """
    Execute Python code from file with provided context, after validating syntax.
    
    Args:
        code: String containing Python code to execute
        page: Playwright page object
        context: Execution context
        log_folder: Folder for logging and temporary files
        send_message_to_user: Optional callback to send messages to user
        report_infeasible_instructions: Optional callback to report infeasible instructions
        
    Returns:
        Path to the executed code file
    
    Raises:
        SyntaxError: If code contains syntax errors
        ImportError: If module cannot be loaded
        Exception: For other execution errors
    """
    # First validate the syntax
    is_valid, error_msg = validate_python_syntax(code)
    if not is_valid:
        logger.error(f"Code validation failed: {error_msg}")
        raise SyntaxError(error_msg)

    # Save the code to a file
    file_path = save_code_to_file(code, log_folder)
    
    try:
        # Add the code directory to Python path
        sys.path.insert(0, os.path.dirname(file_path))
        
        # Import the module using importlib
        spec = importlib.util.spec_from_file_location("generated_code", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {file_path}")
            
        module = importlib.util.module_from_spec(spec)
        
        # Set the global variables in the module
        module.page = page
        module.context = context
        module.send_message_to_user = send_message_to_user
        module.report_infeasible_instructions = report_infeasible_instructions
        
        # Execute the module
        spec.loader.exec_module(module)
        
    except Exception as e:
        logger.error(f"Error executing code: {e}")
        raise
        
    finally:
        # Remove the directory from sys.path
        if os.path.dirname(file_path) in sys.path:
            sys.path.remove(os.path.dirname(file_path))
    
    return file_path


class AbstractActionSet(ABC):
    def __init__(self, strict: bool = False):
        self.strict = strict

    @abstractmethod
    def describe(self, with_long_description: bool = True, with_examples: bool = True) -> str:
        """
        Returns a textual description of this action space.
        """

    @abstractmethod
    def example_action(self, abstract: bool) -> str:
        """
        Returns an example action as a string.
        """

    @abstractmethod
    def to_python_code(self, action) -> str:
        """
        Converts the given action to browsergym-compatible python code.

        Args:
            action: the action to convert.

        Returns:
            Executable python code that performs the action in a browsergym environment.
        """


def save_code_to_file(code: str, log_folder: str) -> str:
    """Save code to a file and return the file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    code_logs_dir = os.path.join(log_folder, "code_logs")
    os.makedirs(code_logs_dir, exist_ok=True)
    filename = f"code_{timestamp}.py"
    file_path = os.path.join(code_logs_dir, filename)
    
    header = f"""# Generated Code
# Timestamp: {datetime.now().isoformat()}
# File: {filename}
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(header + '\n' + code)
    
    logger.info(f"Saved code to: {file_path}")
    return file_path


def execute_python_code_safely(
    code: str,
    page: 'playwright.sync_api.Page',
    context: Any,
    log_folder: str,
    send_message_to_user: Optional[Callable[[str], None]] = None,
    report_infeasible_instructions: Optional[Callable[[str], None]] = None
) -> str:
    """Execute Python code from file with provided context."""
    
    # Save the code to a file
    file_path = save_code_to_file(code, log_folder)
    
    try:
        # Add the code directory to Python path
        sys.path.insert(0, os.path.dirname(file_path))
        
        # Import the module using importlib
        spec = importlib.util.spec_from_file_location("generated_code", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {file_path}")
            
        module = importlib.util.module_from_spec(spec)
        
        # Set the global variables in the module
        module.page = page
        module.context = context
        module.send_message_to_user = send_message_to_user
        module.report_infeasible_instructions = report_infeasible_instructions
        
        # Execute the module
        spec.loader.exec_module(module)
        
    except Exception as e:
        logger.error(f"Error executing code: {e}")
        raise
        
    finally:
        # Remove the directory from sys.path
        if os.path.dirname(file_path) in sys.path:
            sys.path.remove(os.path.dirname(file_path))
    
    return file_path