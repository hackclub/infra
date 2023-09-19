"""
This file contains functions for working with files.  
i.e. creating folders, walking directories, etc.
"""

import logging, os
from src.grafana.dashboards import is_dashboard


def create_folder(NAME: str):
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


def walk_dir_with_dashboard(dir: str):
    """
    This function walks a directory and yields the path of the files that are dashboards.\n
    It uses the `is_dashboard` function from `src.grafana.dashboards` to check if the file is a dashboard.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `dir` | `str` | The directory to walk. | `None` |
    \n
    Returns a `generator` with the paths of the files that are dashboards.
    """
    for root, _, files in os.walk(dir):
        for file in files:
            if file.endswith(f".json") and is_dashboard(
                open(os.path.join(root, file)).read()
            ):
                yield os.path.join(root, file)
