"""
This file contains functions for interacting with the CLI Dashboard Pull command.
"""
import src.utils as utils, src.git_manager as git_manager, logging
from src.grafana.dashboards import get_dashboards, get_dashboard, save_dashboard
from datetime import datetime
from src.files import create_folder


def pull(args):
    """
    This function pulls dashboards from Grafana using the CLI.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `args` | `argparse.Namespace` | The arguments passed to the CLI command | `None` |
    """

    # Get all the dashboards in Grafana
    DASHBOARDS_METADATA = get_dashboards()
    DASHBOARD_PATH = []
    DASHBOARDS = []
    for DASHBOARD in DASHBOARDS_METADATA:
        DASHBOARDS.append(get_dashboard(DASHBOARD))

    # Create the output folder
    create_folder(args.output)

    # Save all the dashboards
    for DASHBOARD in DASHBOARDS_METADATA:
        DASHBOARD_PATH.append(
            save_dashboard(
                args.output, DASHBOARD, DASHBOARDS[DASHBOARDS_METADATA.index(DASHBOARD)]
            )
        )

    # Git
    if args.git_commit:
        # Get the git repo
        REPO = git_manager.get_git_repo(args.output, args.branch)

        # Commit and push
        git_manager.git_commit(REPO, DASHBOARD_PATH)

        # If the user passed the --git-push flag
        if args.git_push:
            # If the git remote flag was passed
            if args.remote != "remote_name;repote_url":
                # Get the git remote
                REMOTE = git_manager.get_git_remote(REPO, args.remote)

                # Push the changes
                git_manager.git_push(REMOTE, args.branch, args.force)
            else:
                # If the git remote flag wasn't passed, raise an exception
                logging.critical(
                    "No remote specified! Set with -r remote_name;repote_url"
                )
                raise Exception("No remote specified!")

    # Send the webhook if the user passed the --webhook & --webhook-url flag
    if args.webhook:
        utils.send_webhook(
            args.webhook_url,
            {
                "msg": f"""
Grafana Dashboard Backup Alert
Status: COMPLETED
Time: {datetime.now().now().isoformat()}
"""
            },
        )
