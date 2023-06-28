import argparse
from datetime import datetime
from os import environ

import pandas as pd
from github import Auth, Github
from tqdm.asyncio import tqdm_asyncio

DEFAULT_ORG = "alan-turing-institute"

FILES_TO_CHECK = ["README.md", "LICENSE"]


def has_file(repo, filename):
    """Check if a file exists in a repo."""
    try:
        repo.get_contents(filename)
        return True
    except Exception:
        return False


def parse_args():
    parser = argparse.ArgumentParser(description="Get stats on a GitHub org")
    parser.add_argument(
        "--org",
        type=str,
        default=DEFAULT_ORG,
        help="GitHub organisation to get stats for",
    )
    parser.add_argument(
        "--private",
        default=False,
        help="Include private repos in the stats",
    )
    return vars(parser.parse_args())


def get_repo_data(repo):
    row = []
    row.append(repo.name)
    row.append(repo.description)
    row.append(repo.url)
    row.append(has_file(repo, "LICENSE"))
    row.append(has_file(repo, "README.md"))
    row.append(repo.open_issues_count)
    row.append(len(list(repo.get_pulls())))
    row.append(repo.get_commits().totalCount)
    row.append([p.login for p in repo.get_contributors()])
    # days since last issue
    try:
        d = max([i.updated_at for i in repo.get_issues()])
        row.append((d.today() - d).days)
    except ValueError:
        d = "N/A"
        row.append("N/A")
    # days since last commit
    c = datetime.strptime(
        repo.get_commits()[0].last_modified, "%a, %d %b %Y %H:%M:%S %Z"
    )
    row.append((c.today() - c).days)
    return row


async def to_table(repos):
    """
    Generates a CSV of repos where columns should include:
    - repo name
    - repo description
    - repo url
    - repo license status
    - repo readme status
    - number of issues open
    - number of pull requests open
    - number of commits
    - contributors
    - days since last issue
    - days since last commit
    """

    rows = await tqdm_asyncio.gather(*map(get_repo_data, repos))

    return pd.DataFrame(
        rows,
        columns=[
            "name",
            "description",
            "url",
            "license",
            "readme",
            "issues",
            "pulls",
            "commits",
            "contributors",
            "days_since_last_issue",
            "days_since_last_commit",
        ],
    )


def main():
    token = environ["GITHUB_AUTH"]
    auth = Auth.Token(token)
    g = Github(auth=auth)
    args = parse_args()
    if not args["private"]:
        repos = list(g.get_organization(args["org"]).get_repos())
    else:
        repos = list(g.get_organization(args["org"]).get_repos(type="private"))

    tbl = to_table(repos)
    tbl.to_csv("repos.csv")


if __name__ == "__main__":
    main()
