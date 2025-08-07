import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from tools.ls_tool import LSTool, TreeNode


class TestLSTool:
    """Test cases for LSTool functionality"""

    @pytest.fixture
    def ls_tool(self):
        """Create a LSTool instance for testing"""
        return LSTool()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files and subdirectories"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test directory structure
        test_structure = {
            "file1.py": "print('hello')",
            "file2.txt": "test content",
            "subdir1": {
                "file3.py": "def test(): pass",
                "file4.js": "function test() {}",
                "subdir2": {
                    "file5.py": "class Test: pass"
                }
            },
            "subdir3": {
                "file6.txt": "another test file"
            },
            ".hidden_file": "should be ignored",
            ".hidden_dir": {
                "file7.py": "should be ignored"
            },
            "__pycache__": {
                "file8.pyc": "compiled file"
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
        
        create_structure(temp_dir, test_structure)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_get_tool_info(self, ls_tool):
        """Test tool info retrieval"""
        tool_info = ls_tool.get_tool_info()
        
        assert tool_info.name == "ls"
        assert "Directory listing tool" in tool_info.description
        assert "path" in tool_info.parameters
        assert "ignore" in tool_info.parameters

    @pytest.mark.asyncio
    async def test_execute_with_nonexistent_path(self, ls_tool):
        """Test execution with nonexistent directory path"""
        response = await ls_tool.execute(path="/nonexistent/directory")
        
        assert not response.is_success
        assert "Path does not exist" in response.content

    @pytest.mark.asyncio
    async def test_basic_directory_listing(self, ls_tool, temp_dir):
        """Test basic directory listing functionality"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute()
        
        assert response.is_success
        assert "file1.py" in response.content
        assert "file2.txt" in response.content
        assert "subdir1/" in response.content
        assert "subdir3/" in response.content

    @pytest.mark.asyncio
    async def test_directory_structure_with_subdirectories(self, ls_tool, temp_dir):
        """Test listing with nested subdirectories"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute()
        
        assert response.is_success
        # Check main directory structure
        assert "file1.py" in response.content
        assert "subdir1/" in response.content
        # Check subdirectory structure
        assert "file3.py" in response.content
        assert "file4.js" in response.content
        assert "subdir2/" in response.content
        assert "file5.py" in response.content

    @pytest.mark.asyncio
    async def test_hidden_files_ignored(self, ls_tool, temp_dir):
        """Test that hidden files and directories are ignored"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute()
        
        assert response.is_success
        assert ".hidden_file" not in response.content
        assert ".hidden_dir" not in response.content

    @pytest.mark.asyncio
    async def test_system_directories_ignored(self, ls_tool, temp_dir):
        """Test that system directories like __pycache__ are ignored"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute()
        
        assert response.is_success
        assert "__pycache__" not in response.content

    @pytest.mark.asyncio
    async def test_custom_ignore_patterns(self, ls_tool, temp_dir):
        """Test custom ignore patterns"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute(ignore=["*.txt"])
        
        assert response.is_success
        assert "file1.py" in response.content
        assert "file2.txt" not in response.content
        assert "file6.txt" not in response.content

    @pytest.mark.asyncio
    async def test_multiple_ignore_patterns(self, ls_tool, temp_dir):
        """Test multiple ignore patterns"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute(ignore=["*.txt", "*.js"])
        
        assert response.is_success
        assert "file1.py" in response.content
        assert "file2.txt" not in response.content
        assert "file4.js" not in response.content
        assert "file6.txt" not in response.content

    @pytest.mark.asyncio
    async def test_specific_path_listing(self, ls_tool, temp_dir):
        """Test listing a specific subdirectory"""
        subdir_path = Path(temp_dir) / "subdir1"
        response = await ls_tool.execute(path=str(subdir_path))
        
        assert response.is_success
        assert "file3.py" in response.content
        assert "file4.js" in response.content
        assert "subdir2/" in response.content
        # Should not include files from parent directory
        assert "file1.py" not in response.content

    @pytest.mark.asyncio
    async def test_result_truncation(self, ls_tool, temp_dir):
        """Test result truncation when too many files"""
        # Create many files to trigger truncation
        for i in range(1500):
            file_path = Path(temp_dir) / f"test_file_{i}.txt"
            file_path.write_text(f"test content {i}")
        
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute()
        
        assert response.is_success
        assert "Truncated to 1000 entries" in response.content

    @pytest.mark.asyncio
    async def test_tree_structure_formatting(self, ls_tool, temp_dir):
        """Test that output is formatted as a tree structure"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute()
        
        assert response.is_success
        lines = response.content.split('\n')
        
        # Check tree structure indicators
        assert any(line.startswith('- ') for line in lines)
        assert any(line.startswith('  - ') for line in lines)
        
        # Check directory indicators
        assert any(line.endswith('/') for line in lines)

    @pytest.mark.asyncio
    async def test_metadata_in_response(self, ls_tool, temp_dir):
        """Test that response includes metadata"""
        with patch('os.getcwd', return_value=temp_dir):
            response = await ls_tool.execute()
        
        assert response.is_success
        assert hasattr(response, 'metadata')
        assert hasattr(response.metadata, 'total_files')
        assert hasattr(response.metadata, 'truncated')

    def test_should_ignore_hidden_files(self, ls_tool):
        """Test _should_ignore method with hidden files"""
        assert ls_tool._should_ignore(Path(".hidden"), [])
        assert ls_tool._should_ignore(Path("normal_file"), []) is False

    def test_should_ignore_pattern_matching(self, ls_tool):
        """Test _should_ignore method with pattern matching"""
        patterns = ["*.py", "*.txt"]
        
        assert ls_tool._should_ignore(Path("test.py"), patterns)
        assert ls_tool._should_ignore(Path("test.txt"), patterns)
        assert not ls_tool._should_ignore(Path("test.js"), patterns)

    def test_build_tree_structure(self, ls_tool):
        """Test _build_tree method"""
        root = Path("/test")
        paths = [
            root / "file1.py",
            root / "subdir" / "file2.py",
            root / "subdir" / "subsubdir" / "file3.py"
        ]
        
        tree = ls_tool._build_tree(paths, root)
        
        assert len(tree) > 0
        # Check that directories are properly structured
        for node in tree:
            if node.name == "subdir":
                assert node.type == "directory"
                assert len(node.children) > 0

    def test_render_tree_output(self, ls_tool):
        """Test _render_tree method"""
        nodes = [
            TreeNode(name="file1.py", path="file1.py", type="file", children=[]),
            TreeNode(name="subdir", path="subdir", type="directory", children=[
                TreeNode(name="file2.py", path="subdir/file2.py", type="file", children=[])
            ])
        ]
        
        output = ls_tool._render_tree(nodes, "/test")
        
        assert "file1.py" in output
        assert "subdir/" in output
        assert "file2.py" in output
        assert output.count("- ") >= 3  # At least 3 items in tree


if __name__ == "__main__":
    pytest.main([__file__]) 