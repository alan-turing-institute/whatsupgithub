from github import Github
from github import Auth
from os import environ

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
    - days since last commit
    - days since last issue
    """

def main():
    token = environ['GITHUB_AUTH'] 
    auth = Auth.Token(token)
    g = Github(auth=auth)
    g.get_organization(DEFAULT_ORG).get_repos()
    if PRIVATE:
        repos = g.get_organization(DEFAULT_ORG).get_repos()
    else:
        repos = g.get_organization(DEFAULT_ORG).get_repos(type='private')

if __name__ == "__main__":
    main()