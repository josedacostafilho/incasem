
import subprocess

import streamlit as st
from incasem_setup import handle_exceptions


@handle_exceptions
def setup_omniboard():
    with st.echo():
        st.subheader("Setup Omniboard")
        
        st.write("Setting up Node.js environment and installing Omniboard...")
        subprocess.run("pip install nodeenv", shell=True, check=True)
        subprocess.run("cd ../; nodeenv omniboard_environment", shell=True, check=True)
        subprocess.run("source omniboard_environment/bin/activate", shell=True, check=True)
        subprocess.run("npm install -g omniboard", shell=True, check=True)
        
        st.write("Omniboard setup complete!")
