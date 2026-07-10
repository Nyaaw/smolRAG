import json
import sys

import openai
from smolrag.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_REASONING_EFFORT,
    DEEPSEEK_THINKING,
)
from smolrag.lsp import JavaLSPClient
from smolrag.tools import list_tools
from smolrag.tools.tool import LspTool, Tool


def run_agent(project_root: str) -> None:
    """Run the agentic loop: read user queries from stdin, call DeepSeek
    with tools, execute tool calls, and print the final answer."""

    if not DEEPSEEK_API_KEY:
        print("Error: DEEPSEEK_API_KEY is not set.")
        print("Set it in ~/.config/smolrag/.env or as an environment variable.")
        sys.exit(1)

    client = openai.OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    lsp_client = JavaLSPClient(project_root)
    with lsp_client.start():
        tool_defs: list[dict] = []
        tool_registry: dict[str, Tool] = {}
        for tool_cls in list_tools():
            if issubclass(tool_cls, LspTool):
                tool = tool_cls(project_root, lsp_client=lsp_client)
            else:
                tool = tool_cls(project_root)
            tool_registry[tool.name] = tool
            tool_defs.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )

        messages: list[dict] = []

        print("Agent mode. Type your query (Ctrl+C or Ctrl+D to exit).")
        print(f"Model: {DEEPSEEK_MODEL}")
        print(f"Thinking: {'on' if DEEPSEEK_THINKING else 'off'}")
        print(f"Tools available: {', '.join(sorted(tool_registry.keys())) or 'none'}")
        print()

        while True:
            try:
                user_input = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})

            while True:
                kwargs: dict = {
                    "model": DEEPSEEK_MODEL,
                    "messages": messages,
                    "tools": tool_defs if tool_defs else openai.NOT_GIVEN,
                }

                if DEEPSEEK_THINKING:
                    kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
                    kwargs["reasoning_effort"] = DEEPSEEK_REASONING_EFFORT

                response = client.chat.completions.create(**kwargs)

                msg = response.choices[0].message
                messages.append(msg)

                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool = tool_registry.get(tool_call.function.name)
                        if tool is None:
                            tool_result = f"Error: unknown tool '{tool_call.function.name}'"
                        else:
                            try:
                                args = json.loads(tool_call.function.arguments)
                                tool_result = tool.execute(**args)
                            except Exception as e:
                                tool_result = f"Error: {e}"

                        print(
                            f"[{tool_call.function.name}] {tool_call.function.arguments}"
                            f" ->\n{tool_result}"
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_result,
                            }
                        )
                else:
                    if DEEPSEEK_THINKING and hasattr(msg, "reasoning_content") and msg.reasoning_content:
                        print(f"[reasoning] {msg.reasoning_content}")
                    print()
                    print(msg.content)
                    print()
                    break
