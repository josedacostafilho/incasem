
import subprocess

import streamlit as st
from incasem_setup import handle_exceptions


@handle_exceptions
def setup_omniboard():
    with st.echo():
        st.subheader("Setup Omniboard")
        
        st.write("Setting up Node.js environment and installing Omniboard...")
        subprocess.run("pip install nodeenv", shell=True)
        subprocess.run("cd ../; nodeenv omniboard_environment", shell=True)
        subprocess.run("source omniboard_environment/bin/activate", shell=True)
        subprocess.run("npm install -g omniboard", shell=True)
        
        st.write("Omniboard setup complete!")
