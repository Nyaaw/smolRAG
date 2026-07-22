import pytest

import smolrag.agent as agent_module
from smolrag.config import LLM_API_KEY
from smolrag.tools import list_tools

pytestmark = [pytest.mark.e2e, pytest.mark.lsp, pytest.mark.slow]

QUERY_EXPLORE = (
    "Search all java files, select one that is named like an animal "
    "and show its content from the start to line 27."
)
QUERY_LSP_TOOLS = (
    "Check all the 5 LSP tools you have at your disposal with this class. "
    "Show the results and report if any tool responded weirdly."
)


def _queue_prompts(monkeypatch, *values: str) -> None:
    """Feed *values* to the agent's prompt(), then EOF to end the session."""
    it = iter(values)

    def _fake_prompt(_message: str = "", **_kwargs) -> str:
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr(agent_module, "prompt", _fake_prompt)


def test_e2e_agent_covers_all_tools(fixture_project, require_lsp, monkeypatch, capsys):
    """Two-turn agent session meant to exercise all 7 tools.

    Turn 1 should use glob + read; turn 2 should use the 5 LSP tools.
    The transcript is printed for human validation; assertions only
    check that both turns completed and which tools were invoked.
    """
    if not LLM_API_KEY:
        pytest.skip("LLM_API_KEY not set")

    _queue_prompts(monkeypatch, QUERY_EXPLORE, QUERY_LSP_TOOLS)
    agent_module.run_agent(fixture_project)

    captured = capsys.readouterr()
    all_names = sorted(t.name for t in list_tools())
    used = [n for n in all_names if f"[{n}]" in captured.out]
    unused = [n for n in all_names if n not in used]

    with capsys.disabled():
        print("\n===== agent transcript =====")
        print(captured.out)
        print(f"[tools used] {', '.join(used) or 'none'}")
        print(f"[tools not used] {', '.join(unused) or 'none'}")
        print("===== END =====")

    assert captured.out.count("[response]") == 2
    assert "glob" in used
    assert "read" in used
