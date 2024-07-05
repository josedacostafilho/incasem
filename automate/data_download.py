import subprocess

import streamlit as st
from incasem_setup import handle_exceptions


@handle_exceptions
def download_data():
    st.subheader("Download Data")
    st.write("Downloading example dataset from AWS bucket: cell 6")
    subprocess.run("cd ../incasem/data", shell=True) 
    cmd = """
    import quilt3
    b = quilt3.Bucket("s3://asem-project")
    b.fetch("datasets/cell_6/cell_6_example.zarr/", "cell_6/cell_6.zarr/")
    """
    
    subprocess.run(f"python -c '{cmd}'", shell=True)
    st.write("Data download complete!")
