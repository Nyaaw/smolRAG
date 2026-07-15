from pathlib import Path

from smolrag.tools.tool import Tool
from smolrag.codesnippet import CodeSnippet


class ReadTool(Tool):
    """Read file contents within a project, with optional line range."""

    name = "read"
    description = (
        "Read the contents of a file within the project. "
        "Optionally specify a line range with start (inclusive) and end (inclusive), "
        "both 0-based. If start is omitted, reading starts from the beginning. "
        "If end is omitted, reading goes to the end of the file. "
        "Line numbers are included in the output."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file, relative to the project root.",
            },
            "start": {
                "type": "integer",
                "description": "Start line number (0-based, inclusive). Defaults to 0.",
            },
            "end": {
                "type": "integer",
                "description": (
                    "End line number (0-based, inclusive). Defaults to end of file."
                ),
            },
        },
        "required": ["path"],
    }

    def execute(
        self, path: str, start: int | None = None, end: int | None = None
    ) -> str:
        root = Path(self.project_root).resolve()
        abs_path = (root / path).resolve()
        if not abs_path.is_relative_to(root):
            return f"Error: path '{path}' escapes the project root."

        try:
            with open(str(abs_path), "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            return f"Error: file '{path}' not found."
        except IsADirectoryError:
            return f"Error: '{path}' is a directory, not a file."
        except UnicodeDecodeError:
            return f"Error: '{path}' is not a text file."
        except OSError as e:
            return f"Error reading '{path}': {e}"

        start_line = start or 0
        end_line = end if end is not None else len(lines) - 1

        if start_line < 0:
            return f"Error: start line {start_line} is negative."
        if start_line >= len(lines):
            return f"Error: start line {start_line} is out of range (file has {len(lines)} lines)."
        if end_line < start_line:
            return f"Error: end line {end_line} is before start line {start_line}."
        if end_line >= len(lines):
            end_line = len(lines) - 1

        selected = "".join(lines[start_line : end_line + 1]).rstrip("\n")
        return CodeSnippet.with_line_numbers(selected)
