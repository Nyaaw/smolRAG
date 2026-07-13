from smolrag.tools.tool import LspTool


class LspDefinitionTool(LspTool):
    """Find the definition of a symbol via LSP."""

    name = "lsp-definition"
    description = (
        "Find where the symbol at the given file, line, and column is defined. "
        "Returns the definition location(s) with optional source code. "
        "Set include_code to true to also retrieve the source code."
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
            "include_code": {
                "type": "boolean",
                "description": "If true, include source code. Defaults to true.",
            },
        },
        "required": ["relative_path", "line", "column"],
    }

    def execute(
        self,
        relative_path: str,
        line: int,
        column: int,
        include_code: bool = True,
    ) -> str:
        try:
            snippets = self._lsp_client.definition_code(
                relative_path, line, column
            )
        except Exception as e:
            return f"Error: {e}"

        if not snippets:
            return f"No definition found at {relative_path}:{line}:{column}."

        lines = [f"Found {len(snippets)} definition(s):"]
        for s in snippets:
            lines.append(s.to_tool_output(include_code))
        return "\n".join(lines)
