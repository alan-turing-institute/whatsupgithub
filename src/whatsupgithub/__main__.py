from github import Github
from github import Auth
from os import environ
from datetime import datetime

DEFAULT_ORG = 'alan-turing-institute'
PRIVATE = False

FILES_TO_CHECK = ["README.md", 'LICENSE']

def has_file(repo, filename):
    """Check if a file exists in a repo."""
    try:
        repo.get_contents(filename)
        return True
    except:
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

    for repo in repos:
        row = []
        row.append(repo.name)
        row.append(repo.description)
        row.append(repo.url)
        row.append(has_file(repo, 'LICENSE'))
        row.append(has_file(repo, 'README.md'))
        row.append(repo.open_issues_count)
        row.append(repo.open_pulls_count)
        row.append(repo.get_commits().totalCount)
        row.append([p.login for p in repo.get_contributors()])
        # days since last issue
        d = max([i.updated_at for i in repo.get_issues()])
        row.append((d.today() - d).days)
        # days since last commit
        c = max([datetime.strptime(a.last_modified, '%a, %d %b %Y %H:%M:%S %Z') for a in repo.get_commits()])
        row.append((c.today() - c).days)
        rows.append(row)


def main():
    token = environ['GITHUB_AUTH'] 
    auth = Auth.Token(token)
    g = Github(auth=auth)
    g.get_organization(DEFAULT_ORG).get_repos()
    if PRIVATE:
        repos = g.get_organization(DEFAULT_ORG).get_repos()
    else:
        repos = g.get_organization(DEFAULT_ORG).get_repos(type='private')

    tbl = to_table(repos)

if __name__ == "__main__":
    main()