"""Patch tool (thin version): try `git apply` first, then fallback to `patch-ng`."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
import textwrap

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
    # Change to the target directory before applying
    if root_abs != ".":
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
