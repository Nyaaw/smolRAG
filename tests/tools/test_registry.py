import re

from smolrag.tools import list_tools
from smolrag.tools.tool import LspTool, Tool

EXPECTED_NAMES = {
    "glob",
    "read",
    "lsp-document_symbols",
    "lsp-workspace_symbols",
    "lsp-definition",
    "lsp-hover",
    "lsp-references",
}

LSP_TOOL_NAMES = {n for n in EXPECTED_NAMES if n.startswith("lsp-")}


def test_list_tools_discovers_all():
    """Auto-discovery registers exactly the 7 known tools."""
    assert {t.name for t in list_tools()} == EXPECTED_NAMES


def test_list_tools_no_duplicates():
    """No tool class is registered twice."""
    names = [t.name for t in list_tools()]
    assert len(names) == len(set(names))


def test_list_tools_returns_copy():
    """Mutating the returned list does not affect the registry."""
    tools = list_tools()
    tools.clear()
    assert {t.name for t in list_tools()} == EXPECTED_NAMES


def test_all_tools_subclass_tool():
    """Every registered class is a concrete Tool subclass."""
    for t in list_tools():
        assert issubclass(t, Tool)
        assert t is not Tool
        assert t is not LspTool


def test_lsp_tools_subclass_lsptool():
    """lsp-* tools extend LspTool; glob and read do not."""
    for t in list_tools():
        if t.name in LSP_TOOL_NAMES:
            assert issubclass(t, LspTool)
        else:
            assert not issubclass(t, LspTool)


def test_tool_names_follow_openai_rules():
    """Tool names match the OpenAI function-name character set."""
    for t in list_tools():
        assert re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", t.name)


def test_tool_schemas_are_valid_function_parameters():
    """Each tool declares description and a draft-7 object schema."""
    for t in list_tools():
        assert isinstance(t.description, str) and t.description
        schema = t.parameters
        assert schema["type"] == "object"
        assert isinstance(schema["properties"], dict)
        for req in schema.get("required", []):
            assert req in schema["properties"]
