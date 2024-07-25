import streamlit as st
import pandas as pd
import assemblyai as aai
from utils.tools import get_default_branch, get_file_last_commit_date, get_latest_commit_sha, get_files_list, scrape_changelog

st.title("Cookbook Dashboard")
aai.settings.api_key = st.secrets["aai_api_key"]

repo_url = "https://github.com/AssemblyAI/cookbook"
repo_name = "/".join(repo_url.split("/")[-2:])
token = st.secrets["gh_token"]

with st.spinner("Fetching repo data..."):
    try:
        conn = st.connection("cookbook_db", type = "sql")
        with conn.session as s:
            s.execute('CREATE TABLE IF NOT EXISTS cookbooks (title TEXT, lastupdated TEXT);')
            s.commit()
        
        cookbooks = conn.query("select * from cookbooks")
        st.table(cookbooks)

        if st.button("Update List"):
            with st.spinner("Updating..."):
                default_branch = get_default_branch(repo_name, token)
                latest_commit_sha = get_latest_commit_sha(repo_name, default_branch, token)
                files_list = get_files_list(repo_name, latest_commit_sha, token)
                
                exclude_files = {".gitmodules", "LICENSE", "README.md", "guide-images/make-create-doc.png", "guide-images/make-final-transcript.png", "CONTRIBUTING.md", "guide-images/make-get-id.png", "guide-images/make-get-transcript.png", "guide-images/make-insert-paragraph.png", "guide-images/make-iterator.png", "guide-images/make-run.png", "guide-images/make-scenario.png", "guide-images/make-transcribe-audio.png", "guide-images/make-wait-for-completion.png"}
                files_list = [file for file in files_list if file not in exclude_files]
                
                if files_list:
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
                    
                    s.execute("DELETE FROM cookbooks")
                    for cookbook in data:
                        s.execute(
                            "INSERT INTO cookbooks (title, lastupdated) VALUES (:titles, :updatetimes);",
                            params=dict(titles=cookbook, updatetimes=cookbook[updated_time])
                        )
                else:
                    st.warning("No files found in the repository.")

    except Exception as e:
        st.error(f"Error fetching data: {e}")
