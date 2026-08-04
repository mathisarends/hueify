"""The ``hueify`` command line entry point."""

import argparse

from hueify.onboarding.setup import setup


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hueify",
        description="Typed async client for the Philips Hue CLIP v2 API.",
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser(
        "setup",
        help="discover the bridge, register an app key and print both",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "setup":
        setup()
        return 0

    parser.print_help()
    return 1
