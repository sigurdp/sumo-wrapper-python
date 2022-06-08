import os
import sys
import logging

from argparse import ArgumentParser
from sumo.wrapper import CallSumoApi, SumoClient


logger = logging.getLogger("sumo.wrapper")
logger.setLevel(level="CRITICAL")


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Login to Sumo on azure")

    parser.add_argument(
        "--env",
        dest="env",
        action="store",
        default="prod",
        help="Environment to log into",
    )

    parser.add_argument(
        "--verbosity",
        dest="verbosity",
        default="CRITICAL",
        help="Set the verbosity level",
    )

    parser.add_argument(
        "--interactive",
        dest="interactive",
        action="store_true",
        default=False,
        help="Login interactively (True/False)",
    )

    return parser


def main():
    args = get_parser().parse_args()
    logger.setLevel(level=args.verbosity)
    env = args.env
    logger.debug("env is %s", env)

    print("Login to Sumo environment: " + env)

    sumo = SumoClient(args.env, interactive=args.interactive)
    sumo.authenticate()


if __name__ == "__main__":
    main()
