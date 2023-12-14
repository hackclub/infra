from git import Repo
import os
from elasticsearch import Elasticsearch

# TODO don't hardcode this
directory = 'repos'

total_commits = 0
total_defective_repos = 0

es = Elasticsearch(
    ['https://localhost:9200'],
    http_auth=('elastic', 'change_me_please'),
    verify_certs=False
)

try:
    es.indices.delete(index="search-github-contributors")
    print("Deleted old index...")
except Exception as error:
    print(error)

print("Creating new index...")
es.indices.create(index="search-github-contributors", ignore=400)


# iterate over files in
# that directory
def bulk_actions_for_commit(repo_name, commit, first_commit_times):
    commit_actions = []
    email = commit.author.email
    name = commit.author.name
    try:
        message = commit.message
        is_pr_commit = "Merge pull request" in message
        commit_doc = {
            "index": {
                "_index": "search-github-contributors",
                "_id": commit.hexsha
            }
        }
        commit_actions.append(commit_doc)
        commit_actions.append(
            {
                "email": email,
                "name": name,
                "repo": repo_name,
                "date": commit.authored_datetime,
                "first_contribution_date": first_commit_times[email],
                "message": message,
                "is_assistive": is_pr_commit
            }
        )
    except Exception as error:
        print(error)
        pass
    return commit_actions


def on_all_commits(commit_callback):
    for filename in os.listdir(directory):
        repo_name = os.path.join(directory, filename)
        # checking if it is a file
        all_commits_in_repo(repo_name, commit_callback)


def all_commits_in_repo(repo_name, commit_callback):
    if os.path.isdir(repo_name):
        try:
            repo = Repo(repo_name)
            for commit in list(repo.iter_commits(repo.active_branch, max_count=50000)):
                try:
                    commit_callback(repo_name, commit)
                except Exception as error:
                    print("Error in commit callback: " + error)
                    pass
        except:
            pass


commit_authors = {}
bulk_actions = []
authors_first_commit = {}

def preprocess(repo_name, commit):
    # Keep track of all authors
    email = commit.author.email
    commit_time = commit.committed_datetime

    # Index commit authors
    if email not in commit_authors:
        commit_authors[email] = 0
    commit_authors[email] = commit_authors[email] + 1

    # Index authors' first-commit time (oldest)
    if email not in authors_first_commit:
        authors_first_commit[email] = commit_time
    else:
        time_prev = authors_first_commit[email]
        if time_prev > commit_time:
            authors_first_commit[email] = commit_time


def index(repo_name, commit):
    # Evil but wutevs
    global bulk_actions

    # Buffer bulk upload records and upload when appropriate
    bulk_actions = bulk_actions + bulk_actions_for_commit(repo_name, commit, authors_first_commit)

    if len(bulk_actions) > 500:
        es.bulk(index="search-github-contributors", operations=bulk_actions)
        print("Successful bulk upload chunk!")
        bulk_actions = []


# This is where all the real work takes place
on_all_commits(preprocess)
on_all_commits(index)

# Complete flush of buffer
if len(bulk_actions) > 0:
    es.bulk(index="search-github-contributors", operations=bulk_actions)

print("Successful bulk upload!")
