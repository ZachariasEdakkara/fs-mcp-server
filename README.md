# Filesystem MCP Server

A local MCP server that gives Claude Desktop the ability to read and search your filesystem.

## Tools
- `list_files` — list files and folders in a directory
- `read_file` — read the contents of a text file
- `search_files` — recursively search for files by pattern (e.g. `*.py`)

## Setup

1. Clone the repo
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install mcp`
5. Add to your `claude_desktop_config.json` (see below)

## Claude Desktop config

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\server.py"]
    }
  }
}
```
