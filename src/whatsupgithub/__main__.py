from datetime import datetime
from os import environ

import pandas as pd
from github import Auth, Github
from tqdm import tqdm

DEFAULT_ORG = "alan-turing-institute"
PRIVATE = False

FILES_TO_CHECK = ["README.md", "LICENSE"]


def has_file(repo, filename):
    """Check if a file exists in a repo."""
    try:
        repo.get_contents(filename)
        return True
    except Exception:
        return False


def to_table(repos):
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

    rows = []

    for repo in tqdm(repos):
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
        rows.append(row)
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
    if PRIVATE:
        repos = list(g.get_organization(DEFAULT_ORG).get_repos())
    else:
        repos = list(g.get_organization(DEFAULT_ORG).get_repos(type="private"))

    tbl = to_table(repos)
    tbl.to_csv("repos.csv")


if __name__ == "__main__":
    main()
