import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="smolrag",
        description="Local codebase analysis via LSPs and sparse retrieval.",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # sub.add_parser("index", help="Index a codebase for retrieval")
    # sub.add_parser("query", help="Search the index and build a context block")
    # sub.add_parser("serve", help="Start MCP server for agentic LLMs")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
    else:
        print(f"Command '{args.command}' not yet implemented.")


if __name__ == "__main__":
    sys.exit(main())