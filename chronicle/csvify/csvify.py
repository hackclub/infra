#! /usr/bin/env python3

"""
A script that converts different formats, and databases, to CSV.
"""

import argparse

parser = argparse.ArgumentParser(
    prog="csvify",
    description="A script that converts different formats, and databases, to CSV.",
    epilog="Created for Chronicle, Hackclub",
    allow_abbrev=False,
)

services = parser.add_subparsers(title="Subcommand List", dest="subcommand")
airtable = services.add_parser(name="airtable", help="Airtable to CSV")

# Add airtable arguments
airtable.add_argument("--api-key", "-k", help="Airtable API Key", required=True)
airtable.add_argument("--base", "-b", help="Airtable Base ID", required=True)
airtable.add_argument("--table", "-t", help="Airtable Table Name", required=True)
airtable.add_argument("--output", "-o", help="Output file name", required=True)
airtable.add_argument(
    "--verbose",
    "-v",
)
args = parser.parse_args()

# If no subcommand, print help
if args.subcommand == None:
    parser.print_help()
    exit(1)

if args.subcommand == "airtable":
    from src.airtable import get_airtable_records

    get_airtable_records(args.api_key, args.base, args.table, args.output)
