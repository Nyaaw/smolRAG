from smolrag.actions.action import Action
from smolrag.lsp import JavaLSPClient
from smolrag.context_builder import ContextBuilder


class ExplainAction(Action):
    """Find a symbol via LSP and build a context block explaining it."""

    name = "explain-lsp"

    def run(self) -> None:
        client = JavaLSPClient(self.project_root)
        with client.start():
            # FIXME: wait for the server to be fully initialized before proceeding. Or fix multilspy.
            import time
            time.sleep(5)
            symbol = input("Symbol name: ").strip()
            if not symbol:
                print("No symbol provided.")
                return

            snippets = client.find_symbols(symbol)

        if not snippets:
            print(f"No symbol matching '{symbol}' found.")
            return

        builder = ContextBuilder()
        print(builder.build(symbol, snippets))
