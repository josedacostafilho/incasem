import json
import logging
import os
import re
import subprocess

import streamlit as st
from incasem_setup import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@handle_exceptions
def run_command(command: str, success_message: str) -> None:
    """Wrapper function to run commands"""
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info(success_message)
        st.success(success_message)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {command}\n{e}")
        st.error(f"Error executing command: {command}")

def create_config_file(output_path: str, config: dict, file_name:str) -> str:
    """Wrapper to make configuration files at the given path"""
    config_path = os.path.join(output_path, file_name +".json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    return config_path

def validate_tiff_filename(filename: str) -> bool:
    """Validate Tiff names according to the regex"""
    st.write("We are validating the filename using the proper naming convensions for our code base, if your file has the wrong name, please check our documentation and change it otherwise it will fail to run")
    return bool(re.match(r'.*_(\d+).*\.tif$', filename))

def convert_tiff_to_zarr(input_path:str, output_path:str, volume_name:str):
    st.write("Checking the size of the TIFF file...")
    file_size = os.path.getsize(input_path)
    st.write(f"File size: {file_size} Gigabytes [Please Enter in Gigabytes otherwise you may have issues, 1 GB = 1000MB]")

    if file_size > 10:  # 10 GB
        st.write("Large TIFF file detected. Using Dask for conversion...")
        convert_cmd = f"python ../scripts/01_data_formatting/01_image_sequences_to_zarr_with_dask.py -i {input_path} -f {output_path} -d volumes/{volume_name} --resolution 5 5 5"
    else:
        st.write("Converting TIFF to zarr format...")
        convert_cmd = f"python ../scripts/01_data_formatting/00_image_sequences_to_zarr.py -i {input_path} -f {output_path}"

    run_command(convert_cmd, "Conversion to zarr format complete!")
    st.success("To view the resulting file on neuroglancer, you can go under the cells folder and select our required files")

