import streamlit as st
import requests
import pandas as pd
import assemblyai as aai
from bs4 import BeautifulSoup

aai.settings.api_key = "" 

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
    print(files)
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
    print(changelog_text)
    return changelog_text

st.title("Cookbook Dashboard")

repo_url = st.text_input("Enter the GitHub Repository URL", "https://github.com/AssemblyAI/cookbook")

if repo_url:
    repo_name = "/".join(repo_url.split("/")[-2:])
    token = ""
    
    if st.button("Fetch Last Updated Times"):
        with st.spinner("Fetching data..."):
            try:
                default_branch = get_default_branch(repo_name, token)
                latest_commit_sha = get_latest_commit_sha(repo_name, default_branch, token)
                files_list = get_files_list(repo_name, latest_commit_sha, token)
                
                exclude_files = {".gitmodules", "LICENSE", "README.md"}
                files_list = [file for file in files_list if file not in exclude_files]
                
                if files_list:
                    st.success("Fetched file list successfully!")
                    file_update_times = {}
                    for file_path in files_list:
                        last_commit_date = get_file_last_commit_date(repo_name, file_path, token)
                        file_update_times[file_path] = last_commit_date
                    
                    sorted_files = sorted(file_update_times.items(), key=lambda x: x[1])
                    
                    data = []
                    for file, updated_time in sorted_files:
                        data.append({
                            "File": file,
                            "Last Updated": updated_time
                        })
                    
                    df = pd.DataFrame(data)
                    df['Last Updated'] = pd.to_datetime(df['Last Updated'])
                    
                    st.table(df)
                else:
                    st.warning("No files found in the repository.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")

    if st.button("Scan Cookbooks"):
        with st.spinner("Scanning cookbooks..."):
            try:
                changelog_text = scrape_changelog()
                st.success("Fetched changelog updates successfully!")

                default_branch = get_default_branch(repo_name, token)
                latest_commit_sha = get_latest_commit_sha(repo_name, default_branch, token)
                files_list = get_files_list(repo_name, latest_commit_sha, token)
                
                exclude_files = {".gitmodules", "LICENSE", "README.md"}
                files_list = [file for file in files_list if file not in exclude_files]
                
                if files_list:
                    file_update_times = {}
                    for file_path in files_list:
                        last_commit_date = get_file_last_commit_date(repo_name, file_path, token)
                        file_update_times[file_path] = last_commit_date
                    
                    sorted_files = sorted(file_update_times.items(), key=lambda x: x[1])
                    
                    github_updates = []
                    for file, updated_time in sorted_files:
                        github_updates.append({
                            "File": file,
                            "Last Updated": updated_time
                        })

                    github_text = "\n".join([f"{update['File']} - {update['Last Updated']}" for update in github_updates])
                    combined_text = f"Changelog Updates:\n{changelog_text}\n\nGitHub Cookbook Updates:\n{github_text}"

                    prompt = "Compare the changelog dates and titles to the cookbook titles and update times, to see if any of the cookbooks may be out of date due to new changes in the changelog. For example if the title of a new update is LeMUR then look for any cookbook titles containing LeMUR and flag them up. For the output, simply put the name of the cookbook, the time it was last updated and the reason it may be out of date considering the changelog updates. It is fine if none of them are potentially out of date, that's what we want, and if this is the case then leave a short message explaining this!"
                    result = aai.Lemur().task(
                        prompt,
                        input_text=combined_text
                    )

                    st.success("Cookbook scan completed.")
                    st.write(result.response)
                else:
                    st.warning("No files found in the repository.")
            except Exception as e:
                st.error(f"Error scanning cookbooks: {e}")

st.write("""
### Instructions
1. Enter the GitHub repository URL.
2. (Optional) Enter a GitHub token if you encounter rate limits.
3. Click on "Fetch Last Updated Times" to see the last updated times of files in the repository.
4. Click on "Scan Cookbooks" to check if any cookbooks might be out of date based on the AssemblyAI changelog.
""")
