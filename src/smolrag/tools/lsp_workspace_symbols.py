from smolrag.tools.tool import LspTool


class LspWorkspaceSymbolsTool(LspTool):
    """Search for symbols across the workspace via LSP."""

    name = "lsp-workspace_symbols"
    description = (
        "Search for symbols across the entire workspace by name. "
        "Uses camel-case prefix matching (e.g. 'OutputRed' finds 'OutputRedirector'). "
        "Use substring queries like 'redirector' for non-prefix searches. "
        "Set include_code to true to also retrieve the source code of each symbol."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Symbol name to search for. Camel-case prefix matching.",
            },
            "include_code": {
                "type": "boolean",
                "description": "If true, include source code for each symbol. Defaults to false.",
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, include_code: bool = False) -> str:
        try:
            snippets = self._lsp_client.workspace_symbols_code(query)
        except Exception as e:
            return f"Error: {e}"

        if not snippets:
            return f"No symbols found for '{query}'."

        lines = [f"Found {len(snippets)} symbols:"]
        for s in snippets:
            lines.append(s.to_tool_output(include_code))
        return "\n".join(lines)
