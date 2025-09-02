"""Patch tool (thin version): try `git apply` first, then fallback to `patch-ng`."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
import textwrap
from typing import List

import patch_ng as patch  # pure-Python fallback

from .tools import BaseTool, ToolExecutionResponse, ToolInfo


class PatchApplyError(Exception):
    pass


def _apply_with_git(
    diff_text: str,
    root_abs: str,
    *,
    strip: int,
    reverse: bool,
    dry_run: bool,
    encoding: str,
) -> tuple[bool, str]:
    """Run `git apply` and return (ok, message)."""
    if not shutil.which("git"):
        return False, "git not found"

    args = ["git", "apply", f"-p{strip}"]
    # Only add --directory if the original root was not "." (current directory)
    # root_abs is always absolute path, so we need to check if it's the current working directory
    current_dir = os.path.abspath(".")
    if root_abs != current_dir:
        args.extend(["--directory", root_abs])
    
    if reverse:
        args.append("-R")
    if dry_run:
        args.append("--check")

    proc = subprocess.run(args, input=diff_text.encode(encoding), capture_output=True)
    msg = (proc.stderr or proc.stdout).decode(encoding, errors="ignore").strip()
    return proc.returncode == 0, msg


def _apply_with_patch_ng(
    diff_text: str,
    root_abs: str,
    *,
    strip: int,
    reverse: bool,
    dry_run: bool,
    encoding: str,
) -> tuple[bool, str]:
    """
    Fallback: patch-ng only.
    Notes:
      - expects bytes; we convert from str.
      - reverse/new-file/delete support is limited; intended for simple edits.
    """
    data = diff_text.encode(encoding)
    pset = patch.fromstring(data)
    if not pset:
        return False, "patch-ng: invalid diff (no patch data found)"

    if reverse:
        # Some versions have .reversed(); if not, we treat as unsupported.
        if hasattr(pset, "reversed"):
            pset = pset.reversed()
            if not pset:
                return False, "patch-ng: failed to reverse"
        else:
            return False, "patch-ng: reverse not supported"

    if dry_run:
        # patch-ng can_patch doesn't support parameters, just check if patch can be parsed
        return (True, "")

    # patch-ng doesn't support encoding parameter, and strip may not work as expected
    # Try without strip first, then with strip if needed
    try:
        ok = pset.apply(root=root_abs)
        if ok:
            return (True, "")
    except Exception:
        pass
    
    # If strip is needed, try with strip
    if strip > 0:
        try:
            ok = pset.apply(strip=strip, root=root_abs)
            return (bool(ok), "patch-ng: apply failed")
        except Exception:
            pass
    
    return (False, "patch-ng: apply failed")


def _apply_unified_diff(
    diff_text: str,
    root: str = ".",
    *,
    strip: int = 1,
    reverse: bool = False,
    dry_run: bool = False,
    encoding: str = "utf-8",
) -> bool:
    root_abs = os.path.abspath(root)
    if not os.path.isdir(root_abs):
        raise PatchApplyError(f"Root directory not found: {root}")

    # --- 规范化补丁文本：去公共缩进 / BOM / 头部空行，统一换行 & 结尾换行 ---
    s = textwrap.dedent(diff_text)
    s = s.lstrip("\ufeff")      # 去 UTF-8 BOM
    s = s.lstrip("\n")          # 去开头空行
    s = s.replace("\r\n", "\n") # 统一为 LF
    if not s.endswith("\n"):
        s += "\n"
    diff_text = s


    ok, msg = _apply_with_git(
        diff_text, root_abs, strip=strip, reverse=reverse, dry_run=dry_run, encoding=encoding
    )
    if ok:
        return True

    ok2, msg2 = _apply_with_patch_ng(
        diff_text, root_abs, strip=strip, reverse=reverse, dry_run=dry_run, encoding=encoding
    )
    if ok2:
        return True

    # both failed
    raise PatchApplyError(f"git apply failed: {msg or 'unknown'}; patch-ng failed: {msg2 or 'unknown'}")


@dataclass
class PatchParams:
    diff: str
    root: str = "."
    strip: int = 1
    reverse: bool = False
    dry_run: bool = False
    encoding: str = "utf-8"



patchDescription = """Apply unified diff patches to files.

WHEN TO USE THIS TOOL:
- Apply code changes provided as unified diff (e.g., from `git diff` or `diff -u`)
- Useful for agent-suggested edits

HOW TO USE:
- Provide the unified diff as 'diff'
- 'root' is the repository/project root
- 'strip' behaves like `-pN` (default 1 for Git's a/ b/)

LIMITATIONS:
- Fails if the patch cannot apply cleanly
- Binary patches are not supported
"""

class PatchTool(BaseTool):
    """Tool for applying unified diff patches."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="patch",
            description=patchDescription,
            parameters={
                "diff": {"type": "string", "description": "Unified diff patch text to apply"},
                "root": {"type": "string", "description": "Project root", "default": "."},
                "strip": {"type": "integer", "description": "Drop N leading path components (-pN)", "default": 1},
                "reverse": {"type": "boolean", "description": "Apply in reverse (-R)", "default": False},
                "dry_run": {"type": "boolean", "description": "Validate only; no writes", "default": False},
                "encoding": {"type": "string", "description": "Encoding for input/files", "default": "utf-8"},
            },
        )

    async def execute(self, **kwargs) -> ToolExecutionResponse:
        params = PatchParams(
            diff=kwargs.get("diff", ""),
            root=kwargs.get("root", "."),
            strip=int(kwargs.get("strip", 1) or 1),
            reverse=bool(kwargs.get("reverse", False)),
            dry_run=bool(kwargs.get("dry_run", False)),
            encoding=kwargs.get("encoding", "utf-8") or "utf-8",
        )
        if not params.diff:
            return ToolExecutionResponse.failure("Parameter 'diff' is required.")
        try:
            _apply_unified_diff(
                params.diff,
                params.root,
                strip=params.strip,
                reverse=params.reverse,
                dry_run=params.dry_run,
                encoding=params.encoding,
            )
            msg = "Patch applies cleanly (dry run)" if params.dry_run else "Patch applied successfully"
            return ToolExecutionResponse.success(msg)
        except Exception as e:
            return ToolExecutionResponse.failure(f"Error applying patch: {e}")
    
    def generate_patch(self, original_code: str, modified_code: str, filename: str = "file.py", context_lines: int = 3) -> str:
        """
        Generate unified diff patch from original and modified code.
        
        Args:
            original_code: Original code as string
            modified_code: Modified code as string
            filename: Name of the file being modified (can be full path or relative path)
            context_lines: Number of context lines to include
            
        Returns:
            Unified diff format patch string
        """
        # Convert absolute path to relative path for git patch format
        if os.path.isabs(filename):
            # Get current working directory
            cwd = os.getcwd()
            try:
                # Convert to relative path
                relative_filename = os.path.relpath(filename, cwd)
                filename = relative_filename
            except ValueError:
                # If files are on different drives (Windows) or other issues, use basename
                filename = os.path.basename(filename)
        
        # Check if modified_code is a complete file or just a code snippet
        if len(modified_code.splitlines()) < len(original_code.splitlines()) * 0.8:
            # If modified_code is much shorter, treat it as a snippet and try to find where it fits
            patch = self._generate_snippet_patch(original_code, modified_code, filename, context_lines)
        else:
            # Treat as complete file replacement
            patch = generate_patch_from_code_blocks(original_code, modified_code, filename, context_lines)
        
        return patch
    
    def _generate_snippet_patch(self, original_code: str, snippet_code: str, filename: str, context_lines: int = 3) -> str:
        """
        Generate patch for a code snippet that should replace part of the original code.
        
        Args:
            original_code: Original file content
            snippet_code: Code snippet to insert/replace
            filename: Name of the file (can be full path or relative path)
            context_lines: Number of context lines
            
        Returns:
            Unified diff format patch string
        """
        import difflib
        
        # Split into lines
        original_lines = original_code.splitlines(keepends=True)
        snippet_lines = snippet_code.splitlines(keepends=True)
        
        # Try to find the best match for the snippet in the original code
        matcher = difflib.SequenceMatcher(None, original_code, snippet_code)
        matches = matcher.get_matching_blocks()
        
        if len(matches) > 1:
            # Find the best matching block
            best_match = max(matches[:-1], key=lambda x: x.size)
            if best_match.size > 0:
                # Generate patch for the replacement
                start_line = best_match.a
                end_line = start_line + best_match.size
                
                # Create the patch - use the full filename path for proper patch application
                patch_lines = []
                # Use the full filename path, not just basename
                patch_lines.append(f"--- a/{filename}")
                patch_lines.append(f"+++ b/{filename}")
                
                patch_lines.append(f"@@ -{start_line + 1},{end_line - start_line} +{start_line + 1},{len(snippet_lines)} @@")
                
                # Add context lines before
                context_start = max(0, start_line - context_lines)
                for i in range(context_start, start_line):
                    patch_lines.append(f" {original_lines[i].rstrip()}")
                
                # Add removed lines
                for i in range(start_line, end_line):
                    patch_lines.append(f"-{original_lines[i].rstrip()}")
                
                # Add added lines
                for i in range(context_start, start_line):
                    patch_lines.append(f" {original_lines[i].rstrip()}")
                for line in snippet_lines:
                    patch_lines.append(f"+{line.rstrip()}")
                
                # Add context lines after
                context_end = min(len(original_lines), end_line + context_lines)
                for i in range(end_line, context_end):
                    patch_lines.append(f" {original_lines[i].rstrip()}")
                
                return "\n".join(patch_lines)
        
        # Fallback: simple replacement at the beginning
        patch_lines = []
        # Use the full filename path, not just basename
        patch_lines.append(f"--- a/{filename}")
        patch_lines.append(f"+++ b/{filename}")
        
        patch_lines.append(f"@@ -1,{len(original_lines)} +1,{len(snippet_lines)} @@")
        
        # Remove all original lines
        for line in original_lines:
            patch_lines.append(f"-{line.rstrip()}")
        
        # Add all new lines
        for line in snippet_lines:
            patch_lines.append(f"+{line.rstrip()}")
        
        return "\n".join(patch_lines)
    
    def generate_function_replacement_patch(
        self, 
        original_file_content: str, 
        function_name: str, 
        new_function_code: str,
        filename: str = "file.py",
        context_lines: int = 3
    ) -> str:
        """
        Generate patch for replacing a specific function.
        
        Args:
            original_file_content: Original file content
            function_name: Name of the function to replace
            new_function_code: New function code
            filename: Name of the file being modified (can be full path or relative path)
            context_lines: Number of context lines to include
            
        Returns:
            Unified diff format patch string
        """
        return generate_patch_for_function_replacement(
            original_file_content,
            function_name,
            new_function_code,
            filename,
            context_lines
        )


def generate_unified_diff(
    original_lines: List[str],
    modified_lines: List[str],
    filename: str = "file.py",
    context_lines: int = 3
) -> str:
    """
    Generate unified diff format patch from original and modified code.
    
    Args:
        original_lines: List of original code lines
        modified_lines: List of modified code lines
        filename: Name of the file being modified (can be full path or relative path)
        context_lines: Number of context lines to include
        
    Returns:
        Unified diff format patch string
    """
    import difflib
    
    # Generate unified diff - use the full filename path for proper patch application
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="",
        n=context_lines
    )
    
    return "\n".join(diff)


def generate_patch_from_code_blocks(
    original_code: str,
    modified_code: str,
    filename: str = "file.py",
    context_lines: int = 3
) -> str:
    """
    Generate patch from original and modified code strings.
    
    Args:
        original_code: Original code as string
        modified_code: Modified code as string
        filename: Name of the file being modified (can be full path or relative path)
        context_lines: Number of context lines to include
        
    Returns:
        Unified diff format patch string
    """
    # Split into lines
    original_lines = original_code.splitlines(keepends=True)
    modified_lines = modified_code.splitlines(keepends=True)
    
    # Use manual patch generation for better control
    return _generate_manual_patch(original_lines, modified_lines, filename, context_lines)


def _generate_manual_patch(
    original_lines: List[str],
    modified_lines: List[str],
    filename: str,
    context_lines: int = 3
) -> str:
    """
    Generate patch manually for better control over the format.
    
    Args:
        original_lines: List of original code lines
        modified_lines: List of modified code lines
        filename: Name of the file being modified (can be full path or relative path)
        context_lines: Number of context lines to include
        
    Returns:
        Unified diff format patch string
    """
    
    # For now, use a simple approach: replace the entire file
    # This is more reliable than trying to find specific differences
    patch_lines = []
    # Use the full filename path, not just basename
    patch_lines.append(f"--- a/{filename}")
    patch_lines.append(f"+++ b/{filename}")
    
    patch_lines.append(f"@@ -1,{len(original_lines)} +1,{len(modified_lines)} @@")
    
    # Remove all original lines
    for line in original_lines:
        patch_lines.append(f"-{line.rstrip()}")
    
    # Add all new lines
    for line in modified_lines:
        patch_lines.append(f"+{line.rstrip()}")
    
    return "\n".join(patch_lines)


def generate_patch_for_function_replacement(
    original_file_content: str,
    function_name: str,
    new_function_code: str,
    filename: str = "file.py",
    context_lines: int = 3
) -> str:
    """
    Generate patch for replacing a specific function in a file.
    
    Args:
        original_file_content: Original file content as string
        function_name: Name of the function to replace
        new_function_code: New function code as string
        filename: Name of the file being modified (can be full path or relative path)
        context_lines: Number of context lines to include
        
    Returns:
        Unified diff format patch string
    """
    import re
    
    # Find the function in the original file
    # This is a simple regex-based approach - could be enhanced with AST parsing
    function_pattern = rf"def\s+{re.escape(function_name)}\s*\([^)]*\)[^:]*:(?:\s*#[^\n]*)?\n(.*?)(?=\n\S|\Z)"
    
    match = re.search(function_pattern, original_file_content, re.DOTALL)
    if not match:
        raise ValueError(f"Function '{function_name}' not found in the file")
    
    # Get the original function code
    original_function = match.group(0)
    original_lines = original_function.splitlines(keepends=True)
    
    # Prepare new function code
    new_lines = new_function_code.splitlines(keepends=True)
    
    # Generate patch with the actual filename
    return generate_unified_diff(original_lines, new_lines, filename, context_lines)



