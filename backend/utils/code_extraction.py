"""
Utilities for extracting BadCAD code from AI model responses
"""
import re
from typing import Optional


def extract_badcad_code(response_text: str) -> str:
    """
    Extract BadCAD code from AI model response.
    
    Tries multiple strategies:
    1. Look for code blocks (```python or ```)
    2. Look for lines that appear to be Python/BadCAD code
    3. Return the full response as fallback
    
    Args:
        response_text: Raw response from AI model
        
    Returns:
        Extracted BadCAD code
    """
    if not response_text:
        return ""
    
    # Strategy 1: Try to find code blocks first
    code_block_match = re.search(r'```(?:python)?\s*(.*?)\s*```', response_text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    # Strategy 2: Look for lines that look like Python code
    lines = response_text.split('\n')
    code_lines = []
    in_code = False
    
    # Patterns that indicate Python/BadCAD code
    code_patterns = [
        '=',           # Assignment
        'square(',     # BadCAD function
        'circle(',     # BadCAD function
        'cube(',       # BadCAD function
        'cylinder(',   # BadCAD function
        'sphere(',     # BadCAD function
        'extrude(',    # BadCAD method
        'move(',       # BadCAD method
        'rotate(',     # BadCAD method
        'model =',     # Common variable name
        'import',      # Import statement
        'from',        # From import
        'def ',        # Function definition
        'class ',      # Class definition
        '#',           # Comment
    ]
    
    # Patterns that indicate explanatory text (not code)
    text_patterns = [
        'create', 'generate', 'make', 'build',  # Common verbs in instructions
        'will', 'should', 'can', 'must',        # Modal verbs
        'the', 'this', 'that', 'these',         # Articles/determiners
    ]
    
    for line in lines:
        stripped = line.strip()
        
        # Empty lines are preserved if we're in code
        if not stripped:
            if in_code:
                code_lines.append(line)
            continue
        
        # Check if line looks like code
        has_code_pattern = any(pattern in stripped for pattern in code_patterns)
        
        # Check if line looks like explanatory text
        words = stripped.lower().split()
        has_text_pattern = (
            len(words) > 5 and  # Long lines are more likely to be text
            any(word in text_patterns for word in words) and
            not any(char in stripped for char in ['=', '(', ')', '[', ']', '{', '}']) and
            not stripped.startswith('#')  # Comments are part of code
        )
        
        if has_code_pattern and not has_text_pattern:
            in_code = True
            code_lines.append(line)
        elif in_code and has_text_pattern:
            # Stop collecting if we hit explanatory text after code
            break
        elif in_code:
            # Continue collecting if we're in code and it's not clearly text
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    # Strategy 3: Fallback - return the whole response
    return response_text.strip()


def validate_badcad_code(code: str) -> tuple[bool, Optional[str]]:
    """
    Validate that the code appears to be valid BadCAD code.
    
    Args:
        code: The code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not code or not code.strip():
        return False, "Code is empty"
    
    # Check for required import
    if "from badcad import" not in code and "import badcad" not in code:
        return False, "Missing BadCAD import statement"
    
    # Check for model variable
    if "model =" not in code:
        return False, "Missing 'model' variable assignment"
    
    # Basic syntax check - ensure it's parseable Python
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    
    return True, None


def clean_code(code: str) -> str:
    """
    Clean up code by removing common issues.
    
    Args:
        code: The code to clean
        
    Returns:
        Cleaned code
    """
    if not code:
        return ""
    
    # Remove any markdown formatting that might have been missed
    code = re.sub(r'^```\w*\n', '', code)
    code = re.sub(r'\n```$', '', code)
    
    # Ensure consistent line endings
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive blank lines (more than 2 in a row)
    code = re.sub(r'\n\n\n+', '\n\n', code)
    
    # Ensure the code ends with a newline
    if code and not code.endswith('\n'):
        code += '\n'
    
    return code.strip()