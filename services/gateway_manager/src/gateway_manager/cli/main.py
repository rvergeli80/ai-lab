import argparse

from gateway_manager.cli.model import run as model_command
from gateway_manager.cli.models import run as models_command
from gateway_manager.cli.select import run as select_command
from gateway_manager.doctor import GatewayDoctor


def main():

    parser = argparse.ArgumentParser(
        prog="gateway",
        description="Nevermine Gateway CLI",
    )

    subparsers = parser.add_subparsers(dest="command")

    # doctor
    subparsers.add_parser("doctor")

    # models
    subparsers.add_parser("models")

    # model
    model_parser = subparsers.add_parser("model")
    model_parser.add_argument("name")

    # select
    select_parser = subparsers.add_parser("select")
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
            GatewayDoctor.run()

        case "models":
            models_command()

        case "model":
            model_command(args.name)

        case "select":
            select_command(
                capability=args.capability,
                tag=args.tag,
            )

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()