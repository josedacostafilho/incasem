import json
import logging
import os
import subprocess
from functools import wraps
from typing import List

import streamlit as st

logging.basicConfig(filename='debug_incasem.log', encoding='utf-8', level=logging.DEBUG)
logger=logging.getLogger(__name__)

def handle_exceptions(input_func):
    """Decorator for handling exceptions"""
    @wraps(input_func)
    def wrapper(*args, **kwargs):
        try:
            return input_func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found in {input_func.__name__}: {str(e)}| Args: {args} | Kwargs: {kwargs} | Annotations: {input_func.__annotations__} | Code: {input_func.__code__} ")
            st.error(f"File not found in {input_func.__name__}: {str(e)}")
            raise FileNotFoundError(f"File not found in {input_func.__name__}: {str(e)}| Args: {args} | Kwargs: {kwargs} | Annotations: {input_func.__annotations__} | Code: {input_func.__code__} ")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {input_func.__name__}: {str(e)} | Args: {args} | Kwargs: {kwargs} | Annotations: {input_func.__annotations__} | Code: {input_func.__code__}")
            st.error(f"JSON decode error in  {input_func.__name__}: {str(e)}")
            raise json.JSONDecodeError(f"File not found in {input_func.__name__}: {str(e)}")
        except ValueError as e:
            logger.error(f"Value Error in {input_func.__name__}: {str(e)} | Args: {args} | Kwargs: {kwargs} | Annotations: {input_func.__annotations__} | Code: {input_func.__code__}")
            st.error(f"Value Error in {input_func.__name__}: {str(e)}")
            raise ValueError(f"value error in {input_func.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Error in {input_func.__name__}: {str(e)}| Args: {args} | Kwargs: {kwargs} | Annotations: {input_func.__annotations__} | Code: {input_func.__code__} ")
            st.error(f"An error occurred: {str(e)}")
            raise RuntimeError(f"The function {input_func.__name__} failed with the error {str(e)}  | Args: {args} | Kwargs: {kwargs} | Annotations: {input_func.__annotations__} | Code: {input_func.__code__}" )
    return wrapper


def is_conda_installed() -> bool:
    """Run a subprocess to see if conda is installled or not"""
    return subprocess.run(['command', '-v', 'conda'], capture_output=True, text=True, shell=True, check=True).returncode == 0

def is_env_active(env_name) -> bool:
    """Use conda env list to check active environments"""
    cmd="conda env list"
    result=subprocess.run(cmd, capture_output=True, text=True, shell=True, check=True)
    return f"{env_name}" in result.stdout

@handle_exceptions
def setup_conda():
    st.subheader("Conda Installation")
    if is_conda_installed():
        st.write("Conda is already installled.")
    else:
        st.write("Conda is not installed. Installing conda ....")
        subprocess.run("wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh", shell=True, check=True)
        subprocess.run("chmod +x Miniconda3-latest-Linux-x86_64.sh", shell=True, check=True)
        subprocess.run("bash Miniconda3-latest-Linux-x86_64.sh", shell=True, check=True)
        subprocess.run("export PATH=~/miniconda3/bin:$PATH", shell=True, check=True)
        subprocess.run("source ~/.bashrc", shell=True, check=True)

@handle_exceptions
def setup_environment(env_name: str) -> None:
    st.subheader(f"Setting up the conda environment: {env_name}")
    cmd=f"conda init" 
    cmd2="conda activate {env_name}"
    if is_env_active(env_name):
        st.write(f"Environment {env_name} exists")
        subprocess.run(cmd, shell=True)
        output=subprocess.run(cmd, shell=True)
        st.success(output.stdout)
    else:
        st.write("Creating the conda environment with name: {env_name} (This may take a few minutes)")
        subprocess.run(f"conda create --name {env_name} python=3.11 -y", shell=True, check=True)
        subprocess.run(cmd, shell=True)
        subprocess.run(cmd2, shell=True)
        install_cmd=f"pip3 quilt3 install configargparse pipreqs watchdog streamlit bandit[toml] logging" 
        get_reqs="pipreqs ../."
        install_reqs="python3 -m pip install -r ../requirements.txt"
        subprocess.run(install_cmd, shell=True)
        subprocess.run(get_reqs, shell=True )
        subprocess.run(install_reqs, shell=True)

@handle_exceptions
def export_env():
    generate_env="conda env export > environment.yml && mv environment.yml ../"
    subprocess.run(generate_env, shell=True)
    st.write("Environment setup is complete!")
