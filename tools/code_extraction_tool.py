"""
Code extraction tool for extracting code blocks from LLM responses.
"""

import re
from typing import List, Dict, Any


class CodeExtractionTool:
    """Tool for extracting code blocks from LLM response text."""
    
    def __init__(self):
        self.code_block_patterns = [
            # ```python ... ```
            r'```python\s*\n(.*?)\n```',
            # ``` ... ```
            r'```\s*\n(.*?)\n```',
            # `code` (inline code)
            r'`([^`]+)`',
            # 4-space indented code blocks
            r'^    .*$',
        ]
    
    def extract_code_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all code blocks from the given text.
        
        Args:
            text: The text containing code blocks
            
        Returns:
            List of dictionaries with code block information
        """
        code_blocks = []
        
        # Extract Python code blocks
        python_blocks = re.findall(r'```python\s*\n(.*?)\n```', text, re.DOTALL)
        for i, code in enumerate(python_blocks):
            code_blocks.append({
                'type': 'python',
                'content': code.strip(),
                'index': i,
                'format': 'fenced'
            })
        
        # Extract generic code blocks
        generic_blocks = re.findall(r'```\s*\n(.*?)\n```', text, re.DOTALL)
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
        inline_codes = re.findall(r'`([^`]+)`', text)
        for i, code in enumerate(inline_codes):
            code_blocks.append({
                'type': 'inline',
                'content': code,
                'index': i,
                'format': 'inline'
            })
        
        return code_blocks
    
    def extract_python_code(self, text: str) -> List[str]:
        """
        Extract only Python code blocks from the given text.
        
        Args:
            text: The text containing code blocks
            
        Returns:
            List of Python code strings
        """
        code_blocks = self.extract_code_blocks(text)
        python_codes = []
        
        for block in code_blocks:
            if block['type'] == 'python':
                python_codes.append(block['content'])
        
        return python_codes
    

    
    def extract_code_with_context(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks with surrounding context.
        
        Args:
            text: The text containing code blocks
            
        Returns:
            List of dictionaries with code and context
        """
        code_blocks = []
        
        # Find all code block positions
        for match in re.finditer(r'```(?:python)?\s*\n(.*?)\n```', text, re.DOTALL):
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


def extract_code_blocks(text: str) -> List[Dict[str, Any]]:
    """
    Convenience function to extract code blocks from text.
    
    Args:
        text: The text containing code blocks
        
    Returns:
        List of code block dictionaries
    """
    tool = CodeExtractionTool()
    return tool.extract_code_blocks(text)


def extract_python_code(text: str) -> List[str]:
    """
    Convenience function to extract Python code blocks from text.
    
    Args:
        text: The text containing code blocks
        
    Returns:
        List of Python code strings
    """
    tool = CodeExtractionTool()
    return tool.extract_python_code(text)



