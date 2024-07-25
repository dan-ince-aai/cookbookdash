import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import assemblyai as aai
from utils.tools import scrape_changelog, get_default_branch, get_latest_commit_sha, get_files_list, get_file_last_commit_date

st.title("Cookbook Scanner")
st.text("The scanner scrapes our changelog updates and passes this through Claude 3.5")
st.text("along with our cookbook titles and recent commit dates.")
st.text("This is to scan for any new changelog updates which may render")
st.text("some of our cookbooks out-of-date.")
repo_url = "https://github.com/AssemblyAI/cookbook"
repo_name = "/".join(repo_url.split("/")[-2:])
token = st.secrets["gh_token"]

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
