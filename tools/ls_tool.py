import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .tools import BaseTool, ToolInfo, ToolExecutionResponse


@dataclass
class LSParams:
    path: str
    ignore: Optional[List[str]] = None


@dataclass
class TreeNode:
    name: str
    path: str
    type: str  # "file" or "directory"
    children: Optional[List["TreeNode"]] = None

@dataclass
class MetaData:
    total_files: int
    truncated: bool

lsDescription = """Directory listing tool that shows files and subdirectories in a tree structure, helping you explore and understand the project organization.

WHEN TO USE THIS TOOL:
- Use when you need to explore the structure of a directory
- Helpful for understanding the organization of a project
- Good first step when getting familiar with a new codebase

HOW TO USE:
- Provide a path to list (defaults to current working directory)
- Optionally specify glob patterns to ignore
- Results are displayed in a tree structure

FEATURES:
- Displays a hierarchical view of files and directories
- Automatically skips hidden files/directories (starting with '.')
- Skips common system directories like __pycache__
- Can filter out files matching specific patterns

LIMITATIONS:
- Results are limited to 1000 files
- Very large directories will be truncated
- Does not show file sizes or permissions
- Cannot recursively list all directories in a large project

TIPS:
- Use Glob tool for finding files by name patterns instead of browsing
- Use Grep tool for searching file contents
- Combine with other tools for more effective exploration"""

class LSTool(BaseTool):
    MAX_FILES = 1000
    DEFAULT_IGNORES = [
        "__pycache__", "node_modules", "dist", "build", "target",
        "vendor", "bin", "obj", ".git", ".idea", ".vscode", ".DS_Store",
        "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.exe"
    ]

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="ls",
            description=lsDescription,
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the directory (default: current directory)"
                },
                "ignore": {
                    "type": "array",
                    "description": "Glob patterns to ignore",
                    "items": {"type": "string"}
                }
            }
        )

    async def execute(self, **kwargs) -> ToolExecutionResponse:
        try:
            params = LSParams(
                path=kwargs.get("path", os.getcwd()),
                ignore=kwargs.get("ignore", [])
            )

            root_path = Path(params.path).resolve()
            if not root_path.exists():
                return ToolExecutionResponse.failure(f"Path does not exist: {params.path}")

            ignore_patterns = self.DEFAULT_IGNORES + (params.ignore or [])
            all_paths, truncated = self._walk_dir(root_path, ignore_patterns)

            tree = self._build_tree(all_paths, root_path)
            output = self._render_tree(tree, str(root_path))

            if truncated:
                output = f"[Truncated to {self.MAX_FILES} entries]\n\n" + output

            return ToolExecutionResponse.success(output, metadata=str(len(all_paths)))
        except Exception as e:
            return ToolExecutionResponse.failure(f"Error: {e}")

    def _walk_dir(self, root: Path, ignore_patterns: List[str]) -> Tuple[List[Path], bool]:
        results = []
        for dirpath, dirnames, filenames in os.walk(root):
            current_dir = Path(dirpath)
            rel_dir = current_dir.relative_to(root)

            # 过滤目录
            dirnames[:] = [d for d in dirnames if not self._should_ignore(rel_dir / d, ignore_patterns)]

            for name in dirnames + filenames:
                rel_path = rel_dir / name
                if self._should_ignore(rel_path, ignore_patterns):
                    continue
                results.append(root / rel_path)
                if len(results) >= self.MAX_FILES:
                    return results, True
        return results, False

    def _should_ignore(self, path: Path, patterns: List[str]) -> bool:
        name = path.name
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return name.startswith(".")

    def _build_tree(self, paths: List[Path], root: Path) -> List[TreeNode]:
        tree_map: Dict[str, TreeNode] = {}
        roots: List[TreeNode] = []

        for path in sorted(paths):
            rel_parts = path.relative_to(root).parts
            current_path = ""
            parent_node = None

            for i, part in enumerate(rel_parts):
                current_path = os.path.join(current_path, part) if current_path else part
                if current_path not in tree_map:
                    node_type = "directory" if (i < len(rel_parts) - 1 or path.is_dir()) else "file"
                    node = TreeNode(name=part, path=current_path, type=node_type, children=[])
                    tree_map[current_path] = node
                    if parent_node:
                        parent_node.children.append(node)
                    else:
                        roots.append(node)
                parent_node = tree_map[current_path]

        return roots

    def _render_tree(self, nodes: List[TreeNode], root_path: str, level: int = 0) -> str:
        lines = [f"- {root_path}/"]
        for node in nodes:
            lines.extend(self._render_node(node, level + 1))
        return "\n".join(lines)

    def _render_node(self, node: TreeNode, level: int) -> List[str]:
        prefix = "  " * level + "- "
        line = prefix + (node.name + "/" if node.type == "directory" else node.name)
        lines = [line]
        if node.type == "directory" and node.children:
            for child in sorted(node.children, key=lambda x: x.name):
                lines.extend(self._render_node(child, level + 1))
        return lines
