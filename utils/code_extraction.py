"""
Code extraction utilities for extracting code blocks from LLM responses.
"""

import re
from typing import List, Dict, Any

# Code block patterns for different formats
CODE_BLOCK_PATTERNS = {
    'python_fenced': r'```python\s*\n(.*?)\n```',
    'generic_fenced': r'```\s*\n(.*?)\n```',
    'inline': r'`([^`]+)`',
    'indented': r'^    .*$',
}


def extract_code_blocks(text: str) -> List[Dict[str, Any]]:
    """
    Extract all code blocks from the given text.
    
    Args:
        text: The text containing code blocks
        
    Returns:
        List of dictionaries with code block information
    """
    code_blocks = []
    
    # Extract Python code blocks
    python_blocks = re.findall(CODE_BLOCK_PATTERNS['python_fenced'], text, re.DOTALL)
    for i, code in enumerate(python_blocks):
        code_blocks.append({
            'type': 'python',
            'content': code.strip(),
            'index': i,
            'format': 'fenced'
        })
    
    # Extract generic code blocks
    generic_blocks = re.findall(CODE_BLOCK_PATTERNS['generic_fenced'], text, re.DOTALL)
    for i, code in enumerate(generic_blocks):
        # Skip if already captured as Python block
        if code.strip() not in [block['content'] for block in code_blocks]:
            code_blocks.append({
                'type': 'generic',
                'content': code.strip(),
                'index': i,
                'format': 'fenced'
            })
    
    # Extract inline code
    inline_codes = re.findall(CODE_BLOCK_PATTERNS['inline'], text)
    for i, code in enumerate(inline_codes):
        code_blocks.append({
            'type': 'inline',
            'content': code,
            'index': i,
            'format': 'inline'
        })
    
    # Extract indented code blocks (4 spaces)
    lines = text.split('\n')
    indented_lines = []
    for line in lines:
        if re.match(CODE_BLOCK_PATTERNS['indented'], line):
            indented_lines.append(line[4:])  # Remove the 4 spaces
    
    if indented_lines:
        code_blocks.append({
            'type': 'indented',
            'content': '\n'.join(indented_lines),
            'index': len(code_blocks),
            'format': 'indented'
        })
    
    return code_blocks


def extract_python_code(text: str) -> List[str]:
    """
    Extract only Python code blocks from the given text.
    
    Args:
        text: The text containing code blocks
        
    Returns:
        List of Python code strings
    """
    code_blocks = extract_code_blocks(text)
    python_codes = []
    
    for block in code_blocks:
        if block['type'] == 'python':
            python_codes.append(block['content'])
    
    return python_codes


def extract_code_with_context(text: str) -> List[Dict[str, Any]]:
    """
    Extract code blocks with surrounding context.
    
    Args:
        text: The text containing code blocks
        
    Returns:
        List of dictionaries with code and context
    """
    code_blocks = []
    
    # Find all code block positions using the patterns
    python_pattern = CODE_BLOCK_PATTERNS['python_fenced']
    generic_pattern = CODE_BLOCK_PATTERNS['generic_fenced']
    
    # Combined pattern for both Python and generic fenced blocks
    combined_pattern = r'```(?:python)?\s*\n(.*?)\n```'
    
    for match in re.finditer(combined_pattern, text, re.DOTALL):
        start_pos = match.start()
        end_pos = match.end()
        
        # Get context before and after
        context_before = text[max(0, start_pos-100):start_pos].strip()
        context_after = text[end_pos:min(len(text), end_pos+100)].strip()
        
        code_blocks.append({
            'type': 'python' if '```python' in match.group(0) else 'generic',
            'content': match.group(1).strip(),
            'start_pos': start_pos,
            'end_pos': end_pos,
            'context_before': context_before,
            'context_after': context_after
        })
    
    return code_blocks



