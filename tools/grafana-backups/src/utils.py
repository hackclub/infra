"""
This file contains utility functions used throughout the project.  
i.e. environment variable checks, webhook sending, etc.
"""
import os, logging, requests


def has_required_env():
    """
    This function checks if the required environment variables are set.\n
    If they are not set, it will return `False`, otherwise it will return `True`.
    """
    return (
        os.environ.get("GRAFANA_APIKEY") is not None
        and os.environ.get("GRAFANA_URL") is not None
    )


def create_headers(grafana_auth=False):
    """
    This function creates the headers for the API calls.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `grafana_auth` | `bool` | Whether to add the `Authorization: Bearer` header with the `GRAFANA_APIKEY`. | `False` |
    \n
    Returns a `dict` with headers.
    """
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    if grafana_auth:
        headers["Authorization"] = "Bearer " + get_env("GRAFANA_APIKEY")

    return headers


def filter_invalid_chars(string: str):
    """
    This function filters out invalid characters from a string.\n
    For example is used to create a valid filename, by replacing invalid characters with `_`.
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `string` | `str` | The string to filter | `None` |
    \n
    Returns a `str` with the filtered string.
    """
    return (
        string.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )


def get_env(key: str):
    """
    This function returns the value of an environment variable.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `key` | `str` | The key of the environment variable to get | `None` |
    \n
    Returns a `str` with the value of the environment variable.
    """
    return os.environ[key]


def send_webhook(url: str, data: str):
    """
    This function sends a webhook to the specified URL with the specified data.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `url` | `str` | The URL to send the webhook to | `None` |
    | `data` | `dict` | The data to send in the webhook | `None` |
    """
    logging.info("Sending Webhook...")
    requests.post(url, data=data, headers=create_headers())
    logging.info("Webhook Sent!")
