import sys
from typing import Type

from smolrag.codesnippet import CodeSnippet


def _cs(code: str, path: str, start: int, end: int, source: str = "", parent: CodeSnippet | None = None, total_lines: int = 0) -> CodeSnippet:
    return CodeSnippet(code=code, path=path, start_line=start, end_line=end, total_lines=total_lines, source=source, parent=parent)


def patch_prompt(monkeypatch, action_cls: Type, *values: str) -> None:
    """Replace ``prompt`` in *action_cls*'s module with a fake returning *values* in order.

    Actions import ``prompt`` from prompt_toolkit at module level, so the
    bound name inside each action module must be patched (patching
    ``builtins.input`` or ``prompt_toolkit.prompt`` has no effect).
    """
    it = iter(values)

    def _fake_prompt(_message: str = "", **_kwargs) -> str:
        return next(it)

    monkeypatch.setattr(sys.modules[action_cls.__module__], "prompt", _fake_prompt)


def _code(start: int, end: int) -> str:
    """Returns ``"line0\\nline1\\n...\\nline{end-1}"``."""
    return "\n".join("line" + str(x) for x in range(start, end))
