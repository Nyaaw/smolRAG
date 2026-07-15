import glob as glob_module
from pathlib import Path

from smolrag.tools.tool import Tool


class GlobTool(Tool):
    """Find files matching a glob pattern within the project directory."""

    name = "glob"
    description = (
        "Find files matching a glob pattern within the project directory. "
        "Supports recursive patterns like **/*.py. "
        "Returns one file path per line, sorted alphabetically, "
        "or a message if no files match."
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": (
                    "Glob pattern to match against project files. "
                    "Examples: '**/*.py', 'src/**/*.java', '*.md'"
                ),
            }
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str) -> str:
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            return f"Error: pattern '{pattern}' escapes the project root."
        try:
            root = Path(self.project_root).resolve()
            matches = glob_module.glob(
                pattern, root_dir=str(root), recursive=True
            )
            safe = [
                m
                for m in matches
                if (root / m).resolve().is_relative_to(root)
            ]
            if not safe:
                return f"No files matched pattern '{pattern}'."
            return "\n".join(sorted(safe))
        except Exception as e:
            return f"Error running glob '{pattern}': {e}"
