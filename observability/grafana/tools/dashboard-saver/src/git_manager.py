"""
This file contains the functions to manage git repositories.
i.e. getting the repo, committing changes, pushing changes, etc.
"""

import logging
from git import Repo
from datetime import datetime


def get_git_repo(folder, branch):
    """
    This function gets the git repo from the specified folder and git branch.\n
    If the folder is not a git repo, it will initialize a new one.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `folder` | `str` | The folder to get the git repo from. | `None` |
    | `branch` | `str` | The git branch to use. | `None` |
    \n
    Returns a `Repo` object from the `git` library.
    """
    logging.info("Getting Git Repo...")
    REPO = Repo.init(folder, initial_branch=branch)
    logging.info("Git Repo Found!")
    return REPO


def git_commit(repo: Repo, files):
    """
    This function commits the changes to the git repo.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `repo` | `Repo` | The git repo to commit the changes to. | `None` |
    | `files` | `list<str>` | The files to commit. | `None` |
    \n
    Returns `None`.
    """
    logging.info("Committing Changes...")
    repo.index.add(files)
    repo.index.commit(f"Grafana Dashboard Backup - {datetime.now().isoformat()}")
    logging.info("Changes Committed!")


def get_git_remote(repo: Repo, remote):
    """
    This function gets the git remote from the specified repo and remote.\n
    If the remote does not exist, it will add it.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `repo` | `Repo` | The git repo to get the remote from. | `None` |
    | `remote` | `str` | The git remote to use. | `None` |
    \n
    Returns a `Remote` object from the `git` library.
    """
    logging.info("Getting Git Remote...")
    REMOTE = repo.create_remote(remote.split(";")[0], remote.split(";")[1])
    logging.info("Git Remote Found!")
    return REMOTE


def git_push(remote, branch, force):
    """
    This function pushes the changes to the git remote.\n
    \n
    | Argument | Type | Description | Default |
    | -------- | ---- | ----------- | ------- |
    | `remote` | `Remote` | The git remote to push the changes to. | `None` |
    | `branch` | `str` | The git branch to push the changes to. | `None` |
    | `force` | `bool` | Whether or not to force push the changes. | `False` |
    \n
    Returns `None`.
    """
    logging.info("Pushing Changes to Git...")
    remote.push(refspec=f"{branch}:{branch}", force=force).raise_if_error()
    logging.info("Changes Pushed to Git!")
