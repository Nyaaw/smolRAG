import glob as glob_module
import os

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
        try:
            #TODO: prevent path traversal
            matches = glob_module.glob(
                pattern, root_dir=self.project_root, recursive=True
            )
            if not matches:
                return f"No files matched pattern '{pattern}'."
            return "\n".join(sorted(matches))
        except Exception as e:
            return f"Error running glob '{pattern}': {e}"
