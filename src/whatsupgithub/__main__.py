import argparse
import contextlib
from datetime import datetime
from os import environ
from pathlib import Path

import pandas as pd
from github import Auth, Github, UnknownObjectException
from tqdm import tqdm

DEFAULT_ORG = "alan-turing-institute"

FILES_TO_CHECK = ["README.md", "LICENSE"]


def has_file(repo, filename):
    """Check if a file exists in a repo."""
    try:
        repo.get_contents(filename)
        return True
    except Exception:
        return False


def has_comment(repo, comment):
    """Check if a comment exists in a repo."""
    try:
        repo.get_contents(comment)
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
    parser.add_argument("--repo", default=None, help="Get stats for a single repo")
    parser.add_argument(
        "--all",
        default=False,
        help="Get stats for all repos and stores in individual csv files",
    )
    parser.add_argument("--out_folder", default="./", help="Folder to store csv files")
    return vars(parser.parse_args())


def check_user_is_in_org(g, org, user):
    try:
        g.get_user(user).get_organization_membership(org)
    except UnknownObjectException:
        return False
    return True


def get_all_contributors(repo, inc_non_code=True):
    """Get all contributors to a repo."""
    contributors = {}
    for contributor in repo.get_contributors():
        contributors[contributor.login] = ["code"]
    if inc_non_code:
        for issue in repo.get_issues():
            if issue.user.login not in contributors:
                contributors[issue.user.login] = ["issues"]
            else:
                if "issues" not in contributors[issue.user.login]:
                    contributors[issue.user.login].append("issues")
            for comment in issue.get_comments():
                if comment.user.login not in contributors:
                    contributors[comment.user.login] = ["comments"]
                else:
                    if "comments" not in contributors[comment.user.login]:
                        contributors[comment.user.login].append("comments")
    return contributors


def github_to_timestamp(s):
    return datetime.strptime(s.last_modified, "%a, %d %b %Y %H:%M:%S %Z")


def get_all_commit_issue_comments_info(repo):
    """Get all commit, issue and comment info from a repo.
    Returns a dataframe with columns:
    - user
    - timestamp
    - type (commit, issue, comment)
    """
    rows = []

    print("Doing all commits")
    for commit in tqdm(repo.get_commits()):
        try:
            row = []
            row.append(commit.author.login)
            row.append(github_to_timestamp(commit))
            row.append("commit")
            rows.append(row)
        except AttributeError:
            pass
    print("Doing all issues and comments")
    for issue in tqdm(repo.get_issues()):
        row = []
        row.append(issue.user.login)
        row.append(issue.created_at)
        row.append("issue")
        rows.append(row)

        for comment in issue.get_comments():
            row = []
            row.append(comment.user.login)
            row.append(comment.created_at)
            row.append("comment")
            rows.append(row)

    return pd.DataFrame(rows, columns=["user", "timestamp", "type"])


def repo_info_to_table(repos):
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
        c = github_to_timestamp(repo.get_commits()[0])
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
    args = parse_args()

    # Check out folder exists and make the folder if it doesn't
    if args["out_folder"] != "./":
        with contextlib.suppress(OSError):
            Path.as_urimakedirs(args["out_folder"])

    if args["repo"] is not None:
        repo = g.get_repo(args["repo"])
        tbl = get_all_commit_issue_comments_info(repo)
        tbl.to_csv(f"{args['out_folder']}/repo.csv")
    else:
        if not args["private"]:
            repos = list(g.get_organization(args["org"]).get_repos())
        else:
            repos = list(g.get_organization(args["org"]).get_repos(type="private"))

        if args["all"]:
            for repo in tqdm(repos):
                # If repo folder exists then skip
                if Path.isfile(f"{args['out_folder']}/{repo.name}.csv"):
                    continue
                tbl = get_all_commit_issue_comments_info(repo)
                tbl.to_csv(f"{args['out_folder']}/{repo.name}.csv")
        else:
            tbl = repo_info_to_table(repos)
            tbl.to_csv(f"{args['out_folder']}/repos.csv")


if __name__ == "__main__":
    main()
