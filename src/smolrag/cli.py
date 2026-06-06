import argparse
import os
import sys

from smolrag.actions import list_actions


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="smolrag",
        description="Local codebase analysis via LSPs and sparse retrieval.",
    )
    parser.add_argument(
        "--project",
        default=os.getcwd(),
        help="Absolute path to the project root (default: current directory)",
    )
    parser.add_argument(
        "action",
        nargs="?",
        help="Action to run (omit to choose interactively)",
    )
    args = parser.parse_args()

    actions = list_actions()
    if not actions:
        print("No actions available.")
        sys.exit(1)

    action_name = args.action
    if action_name is None:
        print("Available actions:")
        for name in sorted(actions):
            print(f"  {name}")
        action_name = input("\nAction: ").strip()

    action_cls = actions.get(action_name)
    if action_cls is None:
        print(f"Unknown action: '{action_name}'")
        print(f"Available: {', '.join(sorted(actions))}")
        sys.exit(1)

    action = action_cls(args.project)
    action.run()


if __name__ == "__main__":
    sys.exit(main())
