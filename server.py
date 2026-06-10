import os
import fnmatch
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────
# 1. Create the server
#    "filesystem" is the name Claude will see.
# ─────────────────────────────────────────────
mcp = FastMCP("filesystem")

# Safety: only allow access inside this root.
# Change this to any folder you want to expose.
ALLOWED_ROOT = Path.home()


def safe_path(raw: str) -> Path:
    """Resolve a path and block anything outside ALLOWED_ROOT."""
    p = Path(raw).expanduser().resolve()
    if not p.is_relative_to(ALLOWED_ROOT):
        raise ValueError(f"Access denied: {p} is outside the allowed root directory.")
    return p


# ─────────────────────────────────────────────
# 2. Tool: list_files
#    Lists files and folders inside a directory.
# ─────────────────────────────────────────────
@mcp.tool()
def list_files(directory: str = "~") -> str:
    """
    List files and directories at the given path.
    Defaults to the user's home directory.
    """
    path = safe_path(directory)

    if not path.exists():
        return f"Error: '{directory}' does not exist."
    if not path.is_dir():
        return f"Error: '{directory}' is not a directory."

    entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    lines = []
    for entry in entries:
        kind = "FILE" if entry.is_file() else "DIR "
        size = f"{entry.stat().st_size:>10} bytes" if entry.is_file() else ""
        lines.append(f"[{kind}] {entry.name:<40} {size}")

    if not lines:
        return f"Directory '{directory}' is empty."

    return f"Contents of {path}:\n\n" + "\n".join(lines)


# ─────────────────────────────────────────────
# 3. Tool: read_file
#    Returns the text content of a file.
# ─────────────────────────────────────────────
@mcp.tool()
def read_file(filepath: str, max_lines: int = 200) -> str:
    """
    Read and return the contents of a text file.
    Caps at max_lines lines to avoid huge context dumps.
    """
    path = safe_path(filepath)

    if not path.exists():
        return f"Error: '{filepath}' does not exist."
    if not path.is_file():
        return f"Error: '{filepath}' is not a file."

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"

    lines = text.splitlines()
    truncated = len(lines) > max_lines
    output = "\n".join(lines[:max_lines])

    header = f"File: {path}\nSize: {path.stat().st_size} bytes\nLines shown: {min(len(lines), max_lines)}/{len(lines)}\n\n"
    footer = f"\n\n[Truncated — {len(lines) - max_lines} more lines not shown]" if truncated else ""
    return header + output + footer


# ─────────────────────────────────────────────
# 4. Tool: search_files
#    Recursively finds files matching a pattern.
# ─────────────────────────────────────────────
@mcp.tool()
def search_files(
    pattern: str,
    directory: str = "~",
    max_results: int = 50,
) -> str:
    """
    Search recursively for files matching a glob pattern.
    Examples: '*.py', '*.md', 'README*', 'config.*'
    """
    path = safe_path(directory)

    if not path.exists():
        return f"Error: '{directory}' does not exist."

    matches = []
    try:
        for root, dirs, files in os.walk(path):
            # Skip hidden directories like .git, .venv, node_modules
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    full = Path(root) / filename
                    rel = full.relative_to(path)
                    matches.append(str(rel))
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break
    except PermissionError as e:
        return f"Permission error while searching: {e}"

    if not matches:
        return f"No files matching '{pattern}' found in {path}."

    result = f"Found {len(matches)} file(s) matching '{pattern}' in {path}:\n\n"
    result += "\n".join(f"  {m}" for m in sorted(matches))
    if len(matches) == max_results:
        result += f"\n\n[Stopped at {max_results} results — narrow your search for more precision]"
    return result


# ─────────────────────────────────────────────
# 5. Run the server over stdio
#    Claude Desktop launches this as a subprocess
#    and communicates via stdin/stdout.
# ─────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")