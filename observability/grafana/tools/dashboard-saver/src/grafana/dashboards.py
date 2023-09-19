"""
This file contains functions for interacting with Grafana Dashboard API.  
It contains functions for getting, saving, importing, and checking if a dashboard exists in Grafana.  
"""
import logging, requests, json, os
from src.utils import get_env, create_headers, filter_invalid_chars


def create_dash_folder(NAME: str):
    """
    This function creates a folder with the specified name.\n
    If the folder already exists, it will skip creating it.\n
    It also supports creating nested folders.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `NAME` | `str` | The name of the folder to create. | `None` |
    \n
    Returns `None`.
    """
    logging.info(f"Creating Folder: {NAME}...")
    if not os.path.exists(NAME):
        os.makedirs(NAME)
        logging.info(f"Folder Created: {NAME}!")
    else:
        logging.info(f"Folder, {NAME}, Exists, Skipping...")


def get_dashboards():
    """
    This function gets all the dashboards from the Grafana API.
    \n
    Returns a `list<dict>` of dashboards.
    """
    logging.info("Querying Grafana API for Dashboards...")

    dashboards = requests.get(
        f"{get_env('GRAFANA_URL')}/api/search?query=&type=dash-db",
        headers=create_headers(grafana_auth=True),
    ).json()

    logging.info(f"Dashboards Queried, {len(dashboards)} Dashboards Found!")
    return dashboards


def get_dashboard(dashboard):
    """
    This function gets a dashboard from the Grafana API.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `dashboard` | `dict` | The dashboard to get. It must have a `title` and a `uid` key | `None` |
    \n
    Returns a `dict` of the dashboard.
    """

    logging.info(f"Querying Grafana API for Dashboard: {dashboard['title']}...")

    dashboard = requests.get(
        f"{get_env('GRAFANA_URL')}/api/dashboards/uid/{dashboard['uid']}",
        headers=create_headers(grafana_auth=True),
    ).json()

    logging.info(f"Dashboard Queried, {dashboard['dashboard']['title']} Found!")
    return dashboard


def save_dashboard(dir: str, dashboard_meta, dashboard):
    """
    This function saves a dashboard to the specified directory.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `dir` | `str` | The directory to save the dashboard to | `None` |
    | `dashboard_meta` | `dict` | The dashboard metadata. It must have a `title` and a `folderTitle` key. | `None` |
    | `dashboard` | `dict` | The dashboard returned from `get_dashboard` | `None` |
    \n
    Returns the path to the saved dashboard.
    """
    DASH_TITLE = filter_invalid_chars(dashboard_meta["title"])
    DASH_FOLDER = (
        filter_invalid_chars(dashboard_meta["folderTitle"])
        if "folderTitle" in dashboard_meta
        else "General"
    )
    FOLDER = f"{ dir[:-1] if dir.endswith('/') else dir}/{DASH_FOLDER}"

    create_dash_folder(FOLDER)
    with open(f"{FOLDER}/{DASH_TITLE}.json", "w") as f:
        logging.info(f"Saving Dashboard: {DASH_FOLDER}/{DASH_TITLE}...")
        json.dump(dashboard, f, indent=2)
        logging.info(f"Dashboard Saved: {DASH_FOLDER}/{DASH_TITLE}!")

    return f"{DASH_FOLDER}/{DASH_TITLE}.json"


def import_dashboard(dashboard, new=True):
    """
    This function imports a dashboard to the Grafana API.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `dashboard` | `dict` | The dashboard to import, returned from `get_dashboard` | `None` |
    | `new` | `bool` | Whether to import the dashboard as a new dashboard or overwrite the existing one. | `True` |
    \n
    Returns `None`
    """
    logging.info(f"Importing Dashboard: {dashboard['dashboard']['title']}...")

    body = {
        "dashboard": dashboard["dashboard"],
        "overwrite": True,
        "inputs": [],
        "folderUid": ""
        if "folderUid" not in dashboard["meta"]
        else dashboard["meta"]["folderUid"],
    }

    if new:
        body["dashboard"]["id"] = None
        body["dashboard"]["version"] = None

    requests.post(
        f"{get_env('GRAFANA_URL')}/api/dashboards/import",
        headers=create_headers(grafana_auth=True),
        json=body,
    )

    logging.info(f"Dashboard Imported: {dashboard['dashboard']['title']}!")


def is_dashboard(dashboard):
    """
    This function checks if the dashboard is a Grafana dashboard, via the `meta.type` key.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `dashboard` | `dict` | The dashboard to check | `None` |
    \n
    Returns the result of the check (`bool`).
    """
    return json.loads(dashboard)["meta"]["type"] == "db"


def dashboard_exists(dashboard):
    """
    This function checks if the dashboard exists in Grafana.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `dashboard` | `dict` | The dashboard to check. It must have a `dashboard.title` and a `dashboard.uid` key. | `None` |
    \n
    Returns the result of the check (`bool`).
    """
    dashboard = json.loads(dashboard)
    logging.info(
        f"Testing if Grafana Dashboard, {dashboard['dashboard']['title']}, exists..."
    )

    status = requests.get(
        f"{get_env('GRAFANA_URL')}/api/dashboards/uid/{dashboard['dashboard']['uid']}",
        headers=create_headers(grafana_auth=True),
    ).status_code

    logging.info(f"Grafana Dashboard Exist Test Completed")
    return status != 404
