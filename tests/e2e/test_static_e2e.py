import pytest
from openai import OpenAI

from smolrag.actions import list_actions
from smolrag.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_REASONING_EFFORT,
    DEEPSEEK_THINKING,
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
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    kwargs: dict = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": context_block}],
        "extra_body": {
            "thinking": {"type": "enabled" if DEEPSEEK_THINKING else "disabled"}
        },
    }
    if DEEPSEEK_THINKING:
        kwargs["reasoning_effort"] = DEEPSEEK_REASONING_EFFORT
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


def _multi_input(values):
    it = iter(values)

    def _input(_prompt=None):
        return next(it)

    return _input


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


def test_e2e_index(fixture_project, capsys):
    """Build the BM25 index. No LLM call -- just verify it doesn't crash."""
    if not DEEPSEEK_API_KEY:
        pytest.skip("DEEPSEEK_API_KEY not set")

    IndexAction = _get_action("index")
    action = IndexAction(fixture_project)
    action.run()

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)


def test_e2e_searchvector(fixture_project, monkeypatch, capsys):
    """debug-searchvector for 'Cat', send the retrieved context to DeepSeek."""
    if not DEEPSEEK_API_KEY:
        pytest.skip("DEEPSEEK_API_KEY not set")

    _get_action("index")(fixture_project).run()

    monkeypatch.setattr("builtins.input", lambda _: "Cat")
    _get_action("debug-searchvector")(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (debug-searchvector)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_search_lsp(fixture_project, require_lsp, monkeypatch, capsys):
    """search-lsp for 'Cat', send the retrieved context to DeepSeek."""
    if not DEEPSEEK_API_KEY:
        pytest.skip("DEEPSEEK_API_KEY not set")

    monkeypatch.setattr("builtins.input", lambda _: "Cat")
    _get_action("search-lsp")(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (search-lsp)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_explain(fixture_project, require_lsp, monkeypatch, capsys):
    """Full explain pipeline for 'Cat', send the context block to DeepSeek."""
    if not DEEPSEEK_API_KEY:
        pytest.skip("DEEPSEEK_API_KEY not set")

    _get_action("index")(fixture_project).run()

    monkeypatch.setattr("builtins.input", lambda _: "Cat")
    _get_action("explain")(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (explain)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_refactor_cost(fixture_project, require_lsp, monkeypatch, capsys):
    """RefactorCost for 'Cat' -> 'Rename scratch to claw', send to DeepSeek."""
    if not DEEPSEEK_API_KEY:
        pytest.skip("DEEPSEEK_API_KEY not set")

    monkeypatch.setattr(
        "builtins.input",
        _multi_input(["Cat", "Rename scratch to claw"]),
    )
    _get_action("refactor-cost")(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (refactor-cost)", context, reasoning, answer)


@pytest.mark.lsp
def test_e2e_debug_stacktrace(fixture_project, require_lsp, monkeypatch, capsys):
    """debug-stacktrace with the NPE from Main.java, send to DeepSeek."""
    if not DEEPSEEK_API_KEY:
        pytest.skip("DEEPSEEK_API_KEY not set")

    monkeypatch.setattr(
        "builtins.input",
        _multi_input(
            [
                "Exception in thread \"main\" java.lang.NullPointerException: "
                "Cannot invoke \"com.example.Cat.scratch()\" because \"cat\" is null",
                "\tat com.example.Veterinarian.treat(Veterinarian.java:50)",
                "\tat com.example.Main.doCheckup(Main.java:31)",
                "\tat com.example.Main.handlePet(Main.java:25)",
                "\tat com.example.Main.runScenario(Main.java:18)",
                "\tat com.example.Main.main(Main.java:12)",
                "",
            ]
        ),
    )
    _get_action("debug-stacktrace")(fixture_project).run()

    captured = capsys.readouterr()
    context = _extract_context_block(captured.out)
    if not context:
        pytest.fail("No context block found in action output")

    reasoning, answer = _call_deepseek(context)
    _print_response(capsys, "DeepSeek response (debug-stacktrace)", context, reasoning, answer)
