import pytest
from openai import OpenAI

from smolrag.actions import list_actions
from tests.helpers import patch_prompt
from smolrag.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_REASONING_EFFORT,
    LLM_THINKING,
)

pytestmark = pytest.mark.e2e


def _get_action(name: str):
    actions = list_actions()
    if isinstance(actions, dict):
        return actions[name]
    if isinstance(actions, list):
        for cls in actions:
            if hasattr(cls, "name") and cls.name == name:
                return cls
    raise KeyError(f"Action '{name}' not found")


def _call_deepseek(context_block: str) -> tuple[str | None, str]:
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    kwargs: dict = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": context_block}],
        "extra_body": {
            "thinking": {"type": "enabled" if LLM_THINKING else "disabled"}
        },
    }
    if LLM_THINKING:
        kwargs["reasoning_effort"] = LLM_REASONING_EFFORT
    response = client.chat.completions.create(**kwargs)
    reasoning = response.choices[0].message.reasoning_content
    content = response.choices[0].message.content
    return reasoning, content


def _extract_context_block(output: str) -> str | None:
    marker = "You are a helpful assistant"
    idx = output.find(marker)
    if idx == -1:
        return None
    return output[idx:]


def _print_response(capsys, label: str, context: str, reasoning: str | None, answer: str) -> None:
    with capsys.disabled():
        print(f"\n===== {label} =====")
        print(f"\n[prompt]\n{context}")
        if reasoning:
            print(f"\n[reasoning]\n{reasoning}")
        print(f"\n[answer]\n{answer}")
        print("===== END =====")


# ---------------------------------------------------------------------------
# E2E tests (one per action)
# ---------------------------------------------------------------------------

#TODO: "no information in snippets" tests

def test_e2e_index(fixture_project, capsys):
    """Build the BM25 index. No LLM call -- just verify it doesn't crash."""
    if not LLM_API_KEY:
        pytest.skip("LLM_API_KEY not set")

    IndexAction = _get_action("index")
    action = IndexAction(fixture_project)
    action.run()

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)


def test_e2e_searchvector(fixture_project, monkeypatch, capsys):
    """debug-searchvector for 'Cat', send the retrieved context to DeepSeek."""
    if not LLM_API_KEY:
        pytest.skip("LLM_API_KEY not set")

    _get_action("index")(fixture_project).run()

    SearchVector = _get_action("search-vector")
    patch_prompt(monkeypatch, SearchVector, "Cat")
    SearchVector(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (debug-searchvector)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_search_lsp(fixture_project, require_lsp, monkeypatch, capsys):
    """search-lsp for 'Cat', send the retrieved context to DeepSeek."""
    if not LLM_API_KEY:
        pytest.skip("LLM_API_KEY not set")

    SearchLsp = _get_action("search-lsp")
    patch_prompt(monkeypatch, SearchLsp, "Cat")
    SearchLsp(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (search-lsp)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_explain(fixture_project, require_lsp, monkeypatch, capsys):
    """Full explain pipeline for 'Cat', send the context block to DeepSeek."""
    if not LLM_API_KEY:
        pytest.skip("LLM_API_KEY not set")

    _get_action("index")(fixture_project).run()

    Explain = _get_action("explain")
    patch_prompt(monkeypatch, Explain, "Cat")
    Explain(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (explain)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_refactor_cost(fixture_project, require_lsp, monkeypatch, capsys):
    """RefactorCost for 'Cat' -> 'Rename scratch to claw', send to DeepSeek."""
    if not LLM_API_KEY:
        pytest.skip("LLM_API_KEY not set")

    RefactorCost = _get_action("refactor-cost")
    patch_prompt(monkeypatch, RefactorCost, "Cat", "Rename scratch to claw")
    RefactorCost(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (refactor-cost)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_debug_stacktrace(fixture_project, require_lsp, monkeypatch, capsys):
    """debug-stacktrace with the NPE from Main.java, send to DeepSeek."""
    if not LLM_API_KEY:
        pytest.skip("LLM_API_KEY not set")

    DebugStacktrace = _get_action("debug-stacktrace")
    patch_prompt(
        monkeypatch,
        DebugStacktrace,
        "Exception in thread \"main\" java.lang.NullPointerException: "
        "Cannot invoke \"com.example.Cat.scratch()\" because \"cat\" is null",
        "\tat com.example.Veterinarian.treat(Veterinarian.java:50)",
        "\tat com.example.Main.doCheckup(Main.java:31)",
        "\tat com.example.Main.handlePet(Main.java:25)",
        "\tat com.example.Main.runScenario(Main.java:18)",
        "\tat com.example.Main.main(Main.java:12)",
        "",
    )
    DebugStacktrace(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (debug-stacktrace)", context, reasoning, answer)
