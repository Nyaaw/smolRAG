from smolrag.tools.tool import LspTool


class LspDocumentSymbolsTool(LspTool):
    """Get all symbols in a file via LSP."""

    name = "lsp-document_symbols"
    description = (
        "Get all symbols (classes, methods, fields, etc.) declared in a file. "
        "Returns one symbol per line with file path and line range. "
        "Set include_code to true to also retrieve the source code of each symbol."
    )
    parameters = {
        "type": "object",
        "properties": {
            "relative_path": {
                "type": "string",
                "description": "Path to the file, relative to the project root.",
            },
            "include_code": {
                "type": "boolean",
                "description": "If true, include source code for each symbol. Defaults to false.",
            },
        },
        "required": ["relative_path"],
    }

    def execute(
        self, relative_path: str, include_code: bool = False
    ) -> str:
        try:
            snippets = self._lsp_client.document_symbols_code(relative_path)
        except Exception as e:
            return f"Error: {e}"

        if not snippets:
            return f"No symbols found in '{relative_path}'."

        lines = [f"Found {len(snippets)} symbols:"]
        for s in snippets:
            lines.append(s.to_tool_output(include_code))
        return "\n".join(lines)
