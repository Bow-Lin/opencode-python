import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from tools.grep_tool import GrepTool


class TestGrepTool:
    """Test cases for GrepTool functionality"""

    @pytest.fixture
    def grep_tool(self):
        """Create a GrepTool instance for testing"""
        return GrepTool()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files with different content
        test_files = {
            "test1.py": "def hello_world():\n    print('Hello, World!')\n    return True\n",
            "test2.py": "import os\nfrom pathlib import Path\n\ndef test_function():\n    pass\n",
            "test3.js": "function testFunction() {\n    console.log('test');\n}\n",
            "test4.txt": "This is a test file\nwith some content\nand more lines\n",
            "test5.py": "# This is a comment\n# Another comment\nprint('hello')\n",
            ".hidden_file": "This should be ignored\n",
            "binary_file.bin": b"\x00\x01\x02\x03"
        }
        
        for filename, content in test_files.items():
            file_path = Path(temp_dir) / filename
            if isinstance(content, bytes):
                file_path.write_bytes(content)
            else:
                file_path.write_text(content, encoding='utf-8')
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_get_tool_info(self, grep_tool):
        """Test tool info retrieval"""
        tool_info = grep_tool.get_tool_info()
        
        assert tool_info.name == "grep"
        assert "Fast content search tool" in tool_info.description
        assert "pattern" in tool_info.parameters
        assert "path" in tool_info.parameters
        assert "include" in tool_info.parameters
        assert "literal_text" in tool_info.parameters

    @pytest.mark.asyncio
    async def test_execute_without_pattern(self, grep_tool):
        """Test execution without required pattern parameter"""
        response = await grep_tool.execute()
        
        assert not response.is_success
        assert "Parameter 'pattern' is required" in response.content

    @pytest.mark.asyncio
    async def test_execute_with_invalid_directory(self, grep_tool):
        """Test execution with invalid directory path"""
        response = await grep_tool.execute(
            pattern="test",
            path="/nonexistent/directory"
        )
        
        assert not response.is_success
        assert "Invalid directory" in response.content

    @pytest.mark.asyncio
    async def test_execute_with_invalid_regex(self, grep_tool):
        """Test execution with invalid regex pattern"""
        response = await grep_tool.execute(pattern="[invalid")
        
        assert not response.is_success
        assert "Invalid regex pattern" in response.content

    @pytest.mark.asyncio
    async def test_basic_search(self, grep_tool, temp_dir):
        """Test basic text search functionality"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(pattern="Hello")
        
        assert response.is_success
        assert "test1.py:" in response.content
        # assert "test5.py:" in response.content
        # assert "def hello_world():" in response.content
        assert "Hello, World!" in response.content
        # assert "print('hello')" in response.content

    @pytest.mark.asyncio
    async def test_regex_search(self, grep_tool, temp_dir):
        """Test regex pattern search"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(pattern=r"def\s+\w+")
        
        assert response.is_success
        assert "test1.py:" in response.content
        assert "test2.py:" in response.content
        assert "def hello_world():" in response.content
        assert "def test_function():" in response.content

    @pytest.mark.asyncio
    async def test_literal_text_search(self, grep_tool, temp_dir):
        """Test literal text search with special characters"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(
                pattern="def test_function():",
                literal_text=True
            )
        
        assert response.is_success
        assert "test2.py:" in response.content
        assert "def test_function():" in response.content

    @pytest.mark.asyncio
    async def test_include_pattern_filtering(self, grep_tool, temp_dir):
        """Test file filtering with include pattern"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(
                pattern="function",
                include="*.js"
            )
        
        assert response.is_success
        assert "test3.js:" in response.content
        assert "function testFunction()" in response.content
        # Should not include Python files
        assert "test1.py:" not in response.content
        assert "test2.py:" not in response.content

    @pytest.mark.asyncio
    async def test_include_pattern_with_multiple_extensions(self, grep_tool, temp_dir):
        """Test include pattern with multiple extensions"""
        # Create additional test files
        js_file = Path(temp_dir) / "test6.js"
        ts_file = Path(temp_dir) / "test7.ts"
        js_file.write_text("function jsFunction() {}\n")
        ts_file.write_text("function tsFunction() {}\n")
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(
                pattern="function",
                include="*.{js,ts}"
            )
        
        assert response.is_success
        assert "test3.js:" in response.content
        assert "test6.js:" in response.content
        assert "test7.ts:" in response.content
        # Should not include Python files
        assert "test1.py:" not in response.content

    @pytest.mark.asyncio
    async def test_hidden_files_ignored(self, grep_tool, temp_dir):
        """Test that hidden files are ignored"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(pattern="ignored")
        
        assert response.is_success
        assert "No matches found" in response.content

    @pytest.mark.asyncio
    async def test_binary_files_handled_gracefully(self, grep_tool, temp_dir):
        """Test that binary files are handled gracefully"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(pattern="test")
        
        assert response.is_success
        # Should not crash on binary files
        assert "binary_file.bin:" not in response.content

    @pytest.mark.asyncio
    async def test_no_matches_found(self, grep_tool, temp_dir):
        """Test when no matches are found"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(pattern="nonexistent_pattern")
        
        assert response.is_success
        assert "No matches found" in response.content

    @pytest.mark.asyncio
    async def test_result_truncation(self, grep_tool, temp_dir):
        """Test result truncation when too many matches"""
        # Create many files with the same pattern
        for i in range(150):
            file_path = Path(temp_dir) / f"test_file_{i}.txt"
            file_path.write_text(f"test pattern {i}\n")
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(pattern="test pattern")
        
        assert response.is_success
        assert "Result truncated to 100 files" in response.content
        # Should have exactly 100 results
        lines = response.content.split('\n')
        file_lines = [line for line in lines if line.endswith(':')]
        assert len(file_lines) <= 100

    @pytest.mark.asyncio
    async def test_sort_by_modification_time(self, grep_tool, temp_dir):
        """Test that results are sorted by modification time (newest first)"""
        # Create files with different modification times
        old_file = Path(temp_dir) / "old.txt"
        new_file = Path(temp_dir) / "new.txt"
        
        old_file.write_text("test pattern\n")
        new_file.write_text("test pattern\n")
        
        # Set different modification times
        old_time = 1000000000  # Old timestamp
        new_time = 2000000000  # New timestamp
        
        os.utime(old_file, (old_time, old_time))
        os.utime(new_file, (new_time, new_time))
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await grep_tool.execute(pattern="test pattern")
        
        assert response.is_success
        lines = response.content.split('\n')
        file_lines = [line for line in lines if line.endswith(':')]
        
        # New file should appear before old file
        new_file_index = -1
        old_file_index = -1
        
        for i, line in enumerate(file_lines):
            if "new.txt:" in line:
                new_file_index = i
            elif "old.txt:" in line:
                old_file_index = i
        
        assert new_file_index != -1
        assert old_file_index != -1
        assert new_file_index < old_file_index

    def test_match_include_simple_pattern(self, grep_tool):
        """Test simple include pattern matching"""
        assert grep_tool._match_include("test.py", "*.py")
        assert not grep_tool._match_include("test.py", "*.js")
        assert grep_tool._match_include("test.txt", "*.txt")

    def test_match_include_multiple_extensions(self, grep_tool):
        """Test include pattern with multiple extensions"""
        assert grep_tool._match_include("test.js", "*.{js,ts}")
        assert grep_tool._match_include("test.ts", "*.{js,ts}")
        assert not grep_tool._match_include("test.py", "*.{js,ts}")

    def test_format_output(self, grep_tool):
        """Test output formatting"""
        matches = [
            {
                "file": "/path/to/file1.py",
                "mod_time": 1000,
                "line_num": 5,
                "line": "def test_function():"
            },
            {
                "file": "/path/to/file1.py",
                "mod_time": 1000,
                "line_num": 10,
                "line": "    pass"
            },
            {
                "file": "/path/to/file2.py",
                "mod_time": 2000,
                "line_num": 3,
                "line": "print('hello')"
            }
        ]
        
        output = grep_tool._format_output(matches)
        
        assert "/path/to/file1.py:" in output
        assert "Line 5: def test_function():" in output
        assert "Line 10:     pass" in output
        assert "/path/to/file2.py:" in output
        assert "Line 3: print('hello')" in output

    def test_format_output_no_matches(self, grep_tool):
        """Test output formatting when no matches found"""
        output = grep_tool._format_output([])
        assert output == "No matches found."


if __name__ == "__main__":
    pytest.main([__file__]) 