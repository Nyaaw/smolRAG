from smolrag.codesnippet import CodeSnippet


def _cs(code: str, path: str, start: int, end: int, source: str = "", parent: CodeSnippet | None = None) -> CodeSnippet:
    return CodeSnippet(code=code, path=path, start_line=start, end_line=end, source=source, parent=parent)


def _code(start: int, end: int) -> str:
    """Returns ``"line0\\nline1\\n...\\nline{end-1}"``."""
    return "\n".join("line" + str(x) for x in range(start, end))
