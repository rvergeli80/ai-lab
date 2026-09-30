import argparse

from gateway_manager.cli.model import (
    run as model_command,
)
from gateway_manager.cli.models import (
    run as models_command,
)
from gateway_manager.cli.select import (
    run as select_command,
)
from gateway_manager.cli.usage import (
    run as usage_command,
)
from gateway_manager.doctor import GatewayDoctor


def main():

    parser = argparse.ArgumentParser(
        prog="gateway",
        description="Nevermine Gateway CLI",
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    subparsers.add_parser(
        "doctor",
        help=(
            "Validate Gateway configuration "
            "and runtime availability."
        ),
    )

    subparsers.add_parser(
        "usage",
        help=(
            "Show current Gateway usage "
            "and cost summary."
        ),
    )

    subparsers.add_parser(
        "models",
        help="List enabled models.",
    )

    model_parser = (
        subparsers.add_parser(
            "model",
            help="Show model details.",
        )
    )

    model_parser.add_argument(
        "name"
    )

    select_parser = (
        subparsers.add_parser(
            "select",
            help=(
                "Select a model using "
                "Gateway routing policy."
            ),
        )
    )

    select_parser.add_argument(
        "--capability",
        required=False,
    )

    select_parser.add_argument(
        "--tag",
        required=False,
    )

    args = parser.parse_args()

    match args.command:

        case "doctor":

            raise SystemExit(
                GatewayDoctor.run()
            )

        case "usage":

            usage_command()

        case "models":

            models_command()

        case "model":

            model_command(
                args.name
            )

        case "select":

            select_command(
                capability=(
                    args.capability
                ),
                tag=args.tag,
            )

        case _:

            parser.print_help()


if __name__ == "__main__":
    main()
