#!/bin/sh

if ! command -v gh &> /dev/null
then
    echo "gh not found - please install the github cli utility"
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "You need to login: gh auth login"
    exit 1
fi

if [ $# -ne 1 ]; then
    echo "You must supply an organization"
    exit 1
fi

echo "Querying github..."
gh api graphql -F organization=$1 --paginate -q ".data.organization.repositories.edges[].node.name" -f query='
query($endCursor: String, $organization: String!) {
  organization(login: $organization) {
    repositories (first:25, after: $endCursor) {
      pageInfo {
        endCursor
        hasNextPage
      }
      edges {
	      cursor
        node {
          name
        }
      }
    }
  }
}' | sort > /tmp/repos.txt

if [ ! -d "repos" ]; then
  echo "Creating \"./repos\" directory"
  mkdir repos
fi

while read p; do
  if [ ! -d "repos/$p" ]; then
    pushd repos >/dev/null 2>&1
    echo "Checking out \"$p\""
    git clone git@github.com:$1/$p.git >/dev/null 2>&1
    popd >/dev/null 2>&1
  else
    pushd repos/$p >/dev/null 2>&1
    echo "Refreshing \"$p\""
    git pull >/dev/null 2>&1
    popd >/dev/null 2>&1
  fi
done </tmp/repos.txt