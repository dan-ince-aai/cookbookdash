import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from utils.tools import get_default_branch, get_latest_commit_sha, get_files_list, get_file_last_commit_date

repo_url = "https://github.com/AssemblyAI/cookbook"
repo_name = "/".join(repo_url.split("/")[-2:])
token = st.secrets["gh_token"]

st.title("Stats Page")

with st.spinner('Fetching data...'):
        try:
            branch = get_default_branch(repo_name, token)
            sha = get_latest_commit_sha(repo_name, branch, token)
            files_list = get_files_list(repo_name, sha, token)
            
            commit_dates = []
            for file in files_list:
                commit_date = get_file_last_commit_date(repo_name, file, token)
                commit_dates.append(commit_date)

            commit_dates.sort()
            commit_dates = pd.to_datetime(commit_dates)

            df = pd.DataFrame(commit_dates, columns=['date'])
            df['count'] = 1
            df = df.set_index('date').resample('D').count()

            st.subheader('Commit Activity Timeline')
            st.line_chart(df)

            st.success('Data fetched and plotted successfully!')

        except Exception as e:
            st.error(f'Error: {e}')