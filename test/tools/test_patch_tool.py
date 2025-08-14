# test/tools/test_patch_tool.py
import textwrap
import shutil
import pytest

from tools.patch_tool import _apply_unified_diff, PatchApplyError, PatchTool

has_git = shutil.which("git") is not None

def make_git_style_diff(old_path, new_path, hunk):
    """Minimal git diff wrapper."""
    return f"""diff --git a/{old_path} b/{new_path}
--- a/{old_path}
+++ b/{new_path}
{hunk}"""

def make_minimal_unified_diff(path, hunk):
    """Diff without diff --git header."""
    return f"""--- {path}
+++ {path}
{hunk}"""

def test_apply_simple_patch(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello\n", encoding="utf-8")
    hunk = "@@ -1,1 +1,2 @@\n hello\n+world\n"
    diff = make_git_style_diff("file.txt", "file.txt", hunk)
    assert _apply_unified_diff(diff, root=str(tmp_path), strip=1)
    assert file_path.read_text(encoding="utf-8").splitlines() == ["hello", "world"]

def test_dry_run_only(tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("A\n", encoding="utf-8")
    hunk = "@@ -1,1 +1,2 @@\n A\n+B\n"
    diff = make_git_style_diff("a.txt", "a.txt", hunk)
    assert _apply_unified_diff(diff, root=str(tmp_path), dry_run=True, strip=1)
    # 内容应未改变
    assert file_path.read_text(encoding="utf-8") == "A\n"

@pytest.mark.skipif(not has_git, reason="requires git for new file")
def test_new_file_created(tmp_path):
    diff = """diff --git a/new.txt b/new.txt
new file mode 100644
--- /dev/null
+++ b/new.txt
@@ -0,0 +1 @@
+hello
"""
    assert _apply_unified_diff(diff, root=str(tmp_path), strip=1)
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "hello\n"

@pytest.mark.skipif(not has_git, reason="requires git for delete file")
def test_delete_file(tmp_path):
    f = tmp_path / "rm.txt"
    f.write_text("gone\n", encoding="utf-8")
    diff = """diff --git a/rm.txt b/rm.txt
deleted file mode 100644
--- a/rm.txt
+++ /dev/null
@@ -1 +0,0 @@
-gone
"""
    assert _apply_unified_diff(diff, root=str(tmp_path), strip=1)
    assert not f.exists()

def test_git_fail_patch_ng_success(tmp_path):
    """构造极简 diff，git apply 会失败，但 patch-ng 可成功。"""
    file_path = tmp_path / "m.txt"
    file_path.write_text("foo\n", encoding="utf-8")
    hunk = "@@ -1,1 +1,2 @@\n foo\n+bar\n"
    diff = make_minimal_unified_diff("m.txt", hunk)
    ok = _apply_unified_diff(diff, root=str(tmp_path), strip=0)
    assert ok
    assert "bar" in file_path.read_text(encoding="utf-8")

def test_both_fail(tmp_path):
    """构造无效 diff，git apply 与 patch-ng 都应失败。"""
    bad_diff = "this is not a diff"
    with pytest.raises(PatchApplyError):
        _apply_unified_diff(bad_diff, root=str(tmp_path))

@pytest.mark.asyncio
async def test_patch_tool_execute_success(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("A\n", encoding="utf-8")
    hunk = "@@ -1,1 +1,2 @@\n A\n+B\n"
    diff = make_git_style_diff("f.txt", "f.txt", hunk)
    tool = PatchTool()
    resp = await tool.execute(diff=diff, root=str(tmp_path), strip=1)
    assert resp.is_success
    assert "successfully" in resp.content.lower()
    assert "B" in f.read_text(encoding="utf-8")

@pytest.mark.asyncio
async def test_patch_tool_execute_failure(tmp_path):
    tool = PatchTool()
    resp = await tool.execute(diff="invalid diff", root=str(tmp_path))
    assert not resp.is_success
    assert "error applying patch" in resp.content.lower()
