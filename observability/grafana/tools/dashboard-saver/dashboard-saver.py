#!/usr/bin/env python
"""
This file contains the main entrypoint for the CLI.  
It parses the arguments and calls the appropriate subcommand.  
It also sets the logging level based on the verbose flag.  
View more information about the CLI by running `python grafana-dashboard.py --help`
"""

import argparse, logging, src.utils as utils
from src.cli.dashboards.pull import pull as pullCommand
from src.cli.dashboards.push import push as pushCommand

if __name__ == "__main__":
    # Create the top-level parser
    grafana = argparse.ArgumentParser(
        prog="Grafana Dashboard",
        description="Grafana Python CLI by Marios Mitsios",
        epilog="WARNING: GRAFANA_APIKEY & GRAFANA_URL environment variable must be set",
        allow_abbrev=False,
    )

    # Create subparsers
    dashboards = grafana.add_subparsers(title="Subcommand List", dest="subcommand")
    pull = dashboards.add_parser(name="pull", help="Pull a dashboard")
    push = dashboards.add_parser(name="push", help="Push a dashboard")

    # Create arguments for subcommand
    pull.add_argument(
        "-o",
        "--output",
        default="grafana-dashboards-backup/",
        help="Output directory for the backup",
    )
    pull.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="Verbose output for the backup. -v -> STDOUT, -vv -> FILE, -vvv -> STDOUT + FILE",
    )

    push.add_argument(
        "-i",
        "--input",
        default="grafana-dashboards-backup/",
        help="Input directory for the dashboard imports",
    )
    push.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="Verbose output for the backup. -v -> STDOUT, -vv -> FILE, -vvv -> STDOUT + FILE",
    )
    push.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )

    # Git Related
    pull.add_argument(
        "--git-commit", action="store_true", help="Commit the files to a git repository"
    )
    pull.add_argument(
        "--git-push", action="store_true", help="Push the files to a git repository"
    )
    pull.add_argument(
        "-b", "--branch", default="master", help="Git branch to push the backup to"
    )
    pull.add_argument(
        "-r",
        "--remote",
        default="remote_name;repote_url",
        help="Git remote to push to (name:url)",
    )
    pull.add_argument("-f", "--force", action="store_true", help="Force push to git")

    # Webhook Related
    pull.add_argument(
        "--webhook",
        action="store_true",
        help="Send the backup to a webhook (requires --webhook-url)",
    )
    pull.add_argument(
        "--webhook-url",
        default="http://127.0.0.1",
        help="Webhook URL to send the backup to",
    )

    push.add_argument(
        "--webhook",
        action="store_true",
        help="Send the backup to a webhook (requires --webhook-url)",
    )
    push.add_argument(
        "--webhook-url",
        default="http://127.0.0.1",
        help="Webhook URL to send the backup to",
    )

    args = grafana.parse_args()

    # Set logging level
    HANDLERS = []
    if args.subcommand != None and hasattr(args, "verbose"):
        if args.verbose == 1:
            HANDLERS.append(logging.StreamHandler())
        elif args.verbose == 2:
            HANDLERS.append(logging.FileHandler("grafana-dashboard.log"))
        elif args.verbose == 3:
            HANDLERS.append(logging.StreamHandler())
            HANDLERS.append(logging.FileHandler("grafana-dashboard.log"))

    logging.basicConfig(
        level=logging.INFO
        if args.subcommand != None and args.verbose is not None
        else logging.CRITICAL,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=HANDLERS,
    )

    # Check if required environment variables are set
    if utils.has_required_env():
        # Check if subcommand is set
        if args.subcommand == "pull":
            pullCommand(args)
        elif args.subcommand == "push":
            pushCommand(args)
        else:
            grafana.print_help()
    else:
        grafana.print_help()
