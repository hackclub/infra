"""
This file contains functions for interacting with the CLI Dashboard Push command.
"""

import sys, difflib, json, datetime
from src.files import walk_dir_with_dashboard
from src.grafana.dashboards import dashboard_exists, get_dashboard, import_dashboard
from src.utils import send_webhook


def push(args):
    """
    This function pushes dashboards to Grafana using the CLI.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `args` | `argparse.Namespace` | The arguments passed to the CLI command | `None` |
    """

    # Get all the dashboards in the input directory
    DASHBOARDS = list(walk_dir_with_dashboard(args.input))

    # Push all the dashboards
    for index, dashboard in enumerate(DASHBOARDS):
        # Open and read the dashboard file
        dashboard = open(dashboard).read()

        # Check if the dashboard exists
        if dashboard_exists(dashboard):
            # If it exists
            # Get the dashboard from Grafana
            GRAFANA_FILE = f'{json.loads(dashboard)["dashboard"]["title"]}.json'
            GRAFANA_DASHBOARD = json.dumps(
                get_dashboard(json.loads(dashboard)["dashboard"]), indent=2
            )

            # Print the diff number
            print(f"Showing Dashboard Diff ({index + 1}/{len(DASHBOARDS)})")
            # If the dashboard is different and the user didn't pass the --yes flag
            if GRAFANA_DASHBOARD != dashboard and not args.yes:
                # Print the diff
                for l in difflib.unified_diff(
                    GRAFANA_DASHBOARD.splitlines(),
                    dashboard.splitlines(),
                    fromfile=GRAFANA_FILE,
                    tofile=GRAFANA_FILE,
                ):
                    print(l)

                # Ask the user if they want to continue
                if input("Continue? [y/N] ").lower() != "y":
                    # If they don't want to continue, exit
                    sys.exit(1)

            # Import the dashboard to Grafana
            import_dashboard(json.loads(dashboard), new=False)
        else:
            # If it doesn't exist, import it
            import_dashboard(json.loads(dashboard))

    # Send the webhook if the user passed the --webhook & --webhook-url flag
    if args.webhook:
        send_webhook(
            args.webhook_url,
            {
                "msg": f"""
Grafana Dashboard Backup Restore Alert
Status: COMPLETED
Time: {datetime.now().now().isoformat()}
"""
            },
        )
