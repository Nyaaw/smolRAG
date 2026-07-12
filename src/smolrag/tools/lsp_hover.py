from smolrag.tools.tool import LspTool


class LspHoverTool(LspTool):
    """Get hover documentation and type information for a symbol via LSP."""

    _MAX_CHARS = 500

    name = "lsp/hover"
    description = (
        "Get hover documentation, type information, and signature "
        "for the symbol at the given file, line, and column. "
        "Returns a text string with the hover contents (truncated to ${_MAX_CHARS} characters)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "relative_path": {
                "type": "string",
                "description": "Path to the file, relative to the project root.",
            },
            "line": {
                "type": "integer",
                "description": "0-based line number of the symbol.",
            },
            "column": {
                "type": "integer",
                "description": "0-based column number of the symbol.",
            },
        },
        "required": ["relative_path", "line", "column"],
    }


    def execute(
        self,
        relative_path: str,
        line: int,
        column: int,
    ) -> str:
        try:
            result = self._lsp_client.hover(relative_path, line, column)
        except Exception as e:
            return f"Error: {e}"

        if result is None:
            return f"No hover information at {relative_path}:{line}:{column}."

        contents = result.get("contents")
        if contents is None:
            return f"No hover information at {relative_path}:{line}:{column}."

        text = self._extract_text(contents)
        if len(text) > self._MAX_CHARS:
            text = text[: self._MAX_CHARS] + "..."
        return text

    @staticmethod
    def _extract_text(contents) -> str:
        if isinstance(contents, str):
            return contents
        if isinstance(contents, dict) and "value" in contents:
            return str(contents["value"])
        if isinstance(contents, list):
            parts = []
            for item in contents:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "value" in item:
                    parts.append(item["value"])
            return "\n".join(parts)
        return str(contents)
