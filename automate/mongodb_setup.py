import subprocess

import streamlit as st
from incasem_setup import handle_exceptions


def is_mongodb_installed() -> bool:
    """Run a subprocess to see if MongoDB is installed or not"""
    return subprocess.run(['command', '-v', 'mongod'], capture_output=True, text=True, shell=True).returncode == 0

@handle_exceptions
def setup_mongodb():
    st.subheader("Setup MongoDB")
    
    if is_mongodb_installed():
        st.write("MongoDB is already installed.")
    else:
        with st.echo():
            st.write("MongoDB is not installed. Installing MongoDB ....")
            subprocess.run("brew tap mongodb/brew", shell=True)
            subprocess.run("brew install mongodb-community@4.4", shell=True)
    
    st.write("Starting MongoDB service...")
    with st.echo():
        subprocess.run("brew services start mongodb-community", shell=True)
    
    st.write("Downloading models...")
    with st.echo():
        subprocess.run("cd ../../incasem; python download_models.py", shell=True)
    
    st.write("MongoDB setup complete!")

