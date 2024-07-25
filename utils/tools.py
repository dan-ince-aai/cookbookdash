import requests
from bs4 import BeautifulSoup

def get_default_branch(repo_name, token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f"https://api.github.com/repos/{repo_name}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['default_branch']

def get_latest_commit_sha(repo_name, branch, token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f"https://api.github.com/repos/{repo_name}/commits/{branch}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['sha']

def get_files_list(repo_name, sha, token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f"https://api.github.com/repos/{repo_name}/git/trees/{sha}?recursive=1"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    files = response.json().get('tree', [])
    return [file['path'] for file in files if file['type'] == 'blob']

def get_file_last_commit_date(repo_name, file_path, token=None):
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f"https://api.github.com/repos/{repo_name}/commits?path={file_path}&per_page=1"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    commit = response.json()[0]
    return commit['commit']['committer']['date']

def scrape_changelog():
    url = 'https://assemblyai.com/changelog'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('article')
    changelog_text = "\n".join(article.get_text(separator="\n", strip=True) for article in articles)
    return changelog_text