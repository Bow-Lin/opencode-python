import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from tools.glob_tool import GlobTool


class TestGlobTool:
    """Test cases for GlobTool functionality"""

    @pytest.fixture
    def glob_tool(self):
        """Create a GlobTool instance for testing"""
        return GlobTool()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files with different extensions
        test_files = {
            "test1.py": "print('hello')",
            "test2.py": "def test(): pass",
            "test3.js": "function test() {}",
            "test4.js": "console.log('test')",
            "test5.txt": "test content",
            "test6.html": "<html></html>",
            "test7.css": "body { color: red; }",
            "test8.ts": "const test = () => {}",
            "test9.tsx": "import React from 'react'",
            ".hidden_file": "should be ignored",
            "subdir": {
                "test10.py": "def subdir_func(): pass",
                "test11.js": "function subdir_func() {}",
                "test12.txt": "subdir content"
            }
        }
        
        def create_structure(base_path, structure):
            for name, content in structure.items():
                item_path = Path(base_path) / name
                if isinstance(content, dict):
                    item_path.mkdir(exist_ok=True)
                    create_structure(item_path, content)
                else:
                    item_path.write_text(content, encoding='utf-8')
        
        create_structure(temp_dir, test_files)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_get_tool_info(self, glob_tool):
        """Test tool info retrieval"""
        tool_info = glob_tool.get_tool_info()
        
        assert tool_info.name == "glob"
        assert "Fast file pattern matching tool" in tool_info.description
        assert "pattern" in tool_info.parameters
        assert "path" in tool_info.parameters

    @pytest.mark.asyncio
    async def test_execute_without_pattern(self, glob_tool):
        """Test execution without required pattern parameter"""
        response = await glob_tool.execute()
        
        assert not response.is_success
        assert "Parameter 'pattern' is required" in response.content

    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_path(self, glob_tool):
        """Test execution with nonexistent directory path"""
        response = await glob_tool.execute(
            pattern="*.py",
            path="/nonexistent/directory"
        )
        
        assert not response.is_success
        assert "Path not found" in response.content

    @pytest.mark.asyncio
    async def test_execute_with_file_path(self, glob_tool, temp_dir):
        """Test execution with file path instead of directory"""
        file_path = Path(temp_dir) / "test1.py"
        response = await glob_tool.execute(
            pattern="*.py",
            path=str(file_path)
        )
        
        assert not response.is_success
        assert "Path is not a directory" in response.content

    @pytest.mark.asyncio
    async def test_basic_pattern_matching(self, glob_tool, temp_dir):
        """Test basic pattern matching functionality"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.py")
        
        assert response.is_success
        assert "test1.py" in response.content
        assert "test2.py" in response.content
        # Should not include non-Python files
        assert "test3.js" not in response.content
        assert "test5.txt" not in response.content

    @pytest.mark.asyncio
    async def test_multiple_extension_pattern(self, glob_tool, temp_dir):
        """Test pattern matching with multiple extensions"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.{js,ts,tsx}")
        

        assert response.is_success
        assert "test3.js" in response.content
        assert "test4.js" in response.content
        assert "test8.ts" in response.content
        assert "test9.tsx" in response.content
        # Should not include other file types
        assert "test1.py" not in response.content
        assert "test5.txt" not in response.content

    @pytest.mark.asyncio
    async def test_recursive_pattern_matching(self, glob_tool, temp_dir):
        """Test recursive pattern matching with **"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="**/*.py")
        
        assert response.is_success
        assert "test1.py" in response.content
        assert "test2.py" in response.content
        assert "test10.py" in response.content  # From subdir
        # Should not include non-Python files
        assert "test3.js" not in response.content

    @pytest.mark.asyncio
    async def test_hidden_files_ignored(self, glob_tool, temp_dir):
        """Test that hidden files are ignored"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*")
        
        assert response.is_success
        assert ".hidden_file" not in response.content

    @pytest.mark.asyncio
    async def test_specific_directory_search(self, glob_tool, temp_dir):
        """Test searching in a specific subdirectory"""
        subdir_path = Path(temp_dir) / "subdir"
        response = await glob_tool.execute(
            pattern="*.py",
            path=str(subdir_path)
        )
        
        assert response.is_success
        assert "test10.py" in response.content
        # Should not include files from parent directory
        assert "test1.py" not in response.content
        assert "test2.py" not in response.content

    @pytest.mark.asyncio
    async def test_result_truncation(self, glob_tool, temp_dir):
        """Test result truncation when too many files"""
        # Create many files to trigger truncation
        for i in range(150):
            file_path = Path(temp_dir) / f"test_file_{i}.txt"
            file_path.write_text(f"test content {i}")
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.txt")
        
        assert response.is_success
        assert "Result truncated to 100 files" in response.content
        # Should have exactly 100 results
        lines = response.content.split('\n')
        file_lines = [line for line in lines if line.strip() and not line.startswith('(')]
        assert len(file_lines) <= 100

    @pytest.mark.asyncio
    async def test_sort_by_modification_time(self, glob_tool, temp_dir):
        """Test that results are sorted by modification time (newest first)"""
        # Create files with different modification times
        old_file = Path(temp_dir) / "old.txt"
        new_file = Path(temp_dir) / "new.txt"
        
        old_file.write_text("old content")
        new_file.write_text("new content")
        
        # Set different modification times
        old_time = 1000000000  # Old timestamp
        new_time = 2000000000  # New timestamp
        
        os.utime(old_file, (old_time, old_time))
        os.utime(new_file, (new_time, new_time))
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.txt")
        
        assert response.is_success
        lines = response.content.split('\n')
        file_lines = [line for line in lines if line.strip() and not line.startswith('(')]
        
        # New file should appear before old file
        new_file_index = -1
        old_file_index = -1
        
        for i, line in enumerate(file_lines):
            if "new.txt" in line:
                new_file_index = i
            elif "old.txt" in line:
                old_file_index = i
        
        assert new_file_index != -1
        assert old_file_index != -1
        assert new_file_index < old_file_index

    @pytest.mark.asyncio
    async def test_no_files_found(self, glob_tool, temp_dir):
        """Test when no files match the pattern"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.nonexistent")
        
        assert response.is_success
        assert "No files found" in response.content

    @pytest.mark.asyncio
    async def test_invalid_glob_pattern(self, glob_tool, temp_dir):
        """Test with invalid glob pattern"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="[invalid")
        
        assert response.is_success
        assert "No files found" in response.content

    @pytest.mark.asyncio
    async def test_metadata_in_response(self, glob_tool, temp_dir):
        """Test that response includes metadata"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.py")
        
        assert response.is_success
        assert hasattr(response, 'metadata')
        assert isinstance(response.metadata, str)
        # Metadata should contain the number of files found
        assert int(response.metadata) >= 2  # At least test1.py and test2.py

    @pytest.mark.asyncio
    async def test_question_mark_pattern(self, glob_tool, temp_dir):
        """Test pattern with question mark wildcard"""
        # Create files with specific naming pattern
        test_files = ["a.txt", "ab.txt", "abc.txt"]
        for filename in test_files:
            file_path = Path(temp_dir) / filename
            file_path.write_text("test content")
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="??.txt")
        
        assert response.is_success
        assert "ab.txt" in response.content
        # Should not include single character or three character files
        assert "a.txt" not in response.content
        assert "abc.txt" not in response.content

    @pytest.mark.asyncio
    async def test_bracket_pattern(self, glob_tool, temp_dir):
        """Test pattern with bracket wildcard"""
        # Create files with specific naming pattern
        test_files = ["file1.txt", "file2.txt", "file3.txt", "filea.txt"]
        for filename in test_files:
            file_path = Path(temp_dir) / filename
            file_path.write_text("test content")
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="file[1-3].txt")
        
        assert response.is_success
        assert "file1.txt" in response.content
        assert "file2.txt" in response.content
        assert "file3.txt" in response.content
        # Should not include filea.txt
        assert "filea.txt" not in response.content

    @pytest.mark.asyncio
    async def test_brace_expansion_simple(self, glob_tool, temp_dir):
        """Test simple brace expansion"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.{py,txt}")
        
        assert response.is_success
        assert "test1.py" in response.content
        assert "test2.py" in response.content
        assert "test5.txt" in response.content
        # Should not include other file types
        assert "test3.js" not in response.content

    @pytest.mark.asyncio
    async def test_brace_expansion_with_path(self, glob_tool, temp_dir):
        """Test brace expansion with path prefix"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="test*.{py,js}")
        
        assert response.is_success
        assert "test1.py" in response.content
        assert "test2.py" in response.content
        assert "test3.js" in response.content
        assert "test4.js" in response.content
        # Should not include other file types
        assert "test5.txt" not in response.content

    @pytest.mark.asyncio
    async def test_brace_expansion_recursive(self, glob_tool, temp_dir):
        """Test brace expansion with recursive pattern"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="**/*.{py,js}")
        
        assert response.is_success
        assert "test1.py" in response.content
        assert "test2.py" in response.content
        assert "test3.js" in response.content
        assert "test4.js" in response.content
        assert "test10.py" in response.content  # From subdir
        assert "test11.js" in response.content  # From subdir

    @pytest.mark.asyncio
    async def test_brace_expansion_multiple_options(self, glob_tool, temp_dir):
        """Test brace expansion with multiple options"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.{py,js,ts,tsx,html,css}")
        
        assert response.is_success
        assert "test1.py" in response.content
        assert "test2.py" in response.content
        assert "test3.js" in response.content
        assert "test4.js" in response.content
        assert "test8.ts" in response.content
        assert "test9.tsx" in response.content
        assert "test6.html" in response.content
        assert "test7.css" in response.content
        # Should not include other file types
        assert "test5.txt" not in response.content

    @pytest.mark.asyncio
    async def test_brace_expansion_no_matches(self, glob_tool, temp_dir):
        """Test brace expansion when no files match any pattern"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await glob_tool.execute(pattern="*.{nonexistent1,nonexistent2}")
        
        assert response.is_success
        assert "No files found" in response.content

    def test_expand_braces_method(self, glob_tool):
        """Test the _expand_braces method directly"""
        # Test simple expansion
        result = glob_tool._expand_braces("*.{js,ts}")
        assert result == ["*.js", "*.ts"]
        
        # Test with path prefix
        result = glob_tool._expand_braces("src/**/*.{py,js}")
        assert result == ["src/**/*.py", "src/**/*.js"]
        
        # Test with multiple options
        result = glob_tool._expand_braces("*.{html,css,js}")
        assert result == ["*.html", "*.css", "*.js"]
        
        # Test no braces
        result = glob_tool._expand_braces("*.py")
        assert result == ["*.py"]
        
        # Test nested braces
        result = glob_tool._expand_braces("*.{py,{js,ts}}")
        assert result == ['*.py}', '*.js', '*.ts']
        
        # Test invalid braces
        result = glob_tool._expand_braces("*.{js")
        assert result == ["*.{js"]


if __name__ == "__main__":
    pytest.main([__file__]) 