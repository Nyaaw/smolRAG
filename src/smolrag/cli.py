import argparse
import os
import sys
from prompt_toolkit import choice, prompt

from smolrag.actions import list_actions


def main() -> None:
    try:
            
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
        args.project = os.path.abspath(args.project) #TODO: only use pathlib

        mode_choice = choice("What would you like to do ?", options=[
            ("static", "static: prepare a prompt to copy/paste in your favorite LLM chat"),
            ("agent", "agentic: connect to an agentic LLM and let it decide what to do on your codebase")
            ("config", "configuration options")
        ])
        print()


        if(mode_choice == "config"):
            exit()
        elif(mode_choice == "agent"):
            exit()
        elif(mode_choice == "static"):
            
            actions = list_actions()
            if not actions:
                print("No actions available.")
                sys.exit(1)

            action_name = args.action
            if action_name is None:
                action_name = choice("Available actions:", options=
                                    [(action.name, action.name) for action in actions])
                print()

            action_cls = actions.get(action_name)

            action = action_cls(args.project)
            action.run()

    except KeyboardInterrupt:
        print("\nbye bye")

if __name__ == "__main__":
    sys.exit(main())
