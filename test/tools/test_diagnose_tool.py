import os
import subprocess
from pathlib import Path
import re
import tempfile

import pytest

pytest.importorskip("pydantic")

from tools.diagnose_tool import DiagnoseTool


class TestDiagnoseTool:
    """Tests for DiagnoseTool"""

    @pytest.fixture
    def diagnose_tool(self):
        return DiagnoseTool()

    @pytest.mark.asyncio
    async def test_get_tool_info(self, diagnose_tool):
        info = diagnose_tool.get_tool_info()
        assert info.name == "diagnose"
        assert "Code diagnostics tool" in info.description
        assert "path" in info.parameters

    @pytest.mark.asyncio
    async def test_execute_basic_file(self, diagnose_tool):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("a = 1\n")
            temp_path = f.name
        try:
            response = await diagnose_tool.execute(path=temp_path)
            # print(response)
            assert response.is_success
            assert "File:" in response.content
            assert ("No diagnostics" in response.content) or ("Diagnostics:" in response.content)
        finally:
            os.remove(temp_path)

    @pytest.mark.asyncio
    async def test_execute_bug_file(self, diagnose_tool):
        test_path = "/home/deming/work/opencode-python/agents/runner.py"
        try:
            # LSP-based diagnostics
            response = await diagnose_tool.execute(path=test_path)
            assert response.is_success
            assert ("Diagnostics:" in response.content) or ("No diagnostics found" in response.content)
            print(f"response: {response}")
            metadata = response.metadata
            diagnostics_count = 0
            if isinstance(metadata, dict):
                if isinstance(metadata.get("diagnostics"), list):
                    diagnostics_count = len(metadata["diagnostics"])
                elif isinstance(metadata.get("num_diagnostics"), int):
                    diagnostics_count = metadata["num_diagnostics"]
            elif isinstance(metadata, str):
                try:
                    diagnostics_count = int(metadata)
                except ValueError:
                    diagnostics_count = 0
            
            # 如果LSP服务器可用且有诊断信息，则检查数量
            if "Diagnostics:" in response.content:
                assert diagnostics_count > 0
        finally:
            pass