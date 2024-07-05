import os
import subprocess

import streamlit as st
import zarr
from incasem_setup import handle_exceptions


def find_cells(data_dir):
    """
    Find directories within the specified `data_dir` that start with 'cell'.
    Takes in data_dir as the directory path where cell directories are located and returns cells (list): List of directory names starting with 'cell'.
    """
    cells = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and d.startswith('cell')]
    return cells

def find_zarr_files(cell_dir):
    """
    Recursively find all Zarr files within the specified `cell_dir`.
    """
    zarr_files = []
    for root, dirs, files in os.walk(cell_dir):
        for dir_name in dirs:
            if dir_name.endswith('.zarr'):
                zarr_files.append(os.path.join(root, dir_name))
    return zarr_files

@handle_exceptions
def list_zarr_components(zarr_file_path):
    """
    List components (e.g., 'volumes/labels', 'volumes/predictions') within a Zarr file.
    Args:
    - zarr_file_path (str): Path to the Zarr file.
    """
    root = zarr.open(zarr_file_path, mode='r')
    volumes_path = 'volumes'
    components = []

    if volumes_path in root:
        volumes = root[volumes_path]
        for key in volumes:
            if key == 'labels' or key == 'predictions' or key.startswith('raw'):
                if isinstance(volumes[key], zarr.Group):
                    for sub_key in volumes[key]:
                        components.append(f"{volumes_path}/{key}/{sub_key}")
                else:
                    components.append(f"{volumes_path}/{key}")
    return components

@handle_exceptions
def find_segmentation_folder(selected_components:list, selected_file:str) -> str:
    """
    Find the segmentation folder path based on selected components and Zarr file.
    """
    for component in selected_components:
        if component.startswith('volumes/labels/') or component.startswith('volumes/predictions/'):
            label_key = component.split('/')[2]
            prediction_path = os.path.join(selected_file, f"volumes/predictions/{label_key}/segmentation")
            if os.path.exists(prediction_path):
                return f"volumes/predictions/{label_key}/segmentation"
    return None

@handle_exceptions
def view_cells_and_flatten_them(): 
    """
    Streamlit application to explore Zarr files, select components, and view them in Neuroglancer.

    Workflow:
    1. User inputs a data directory to search for cells.
    2. Displays found cells and allows selection.
    3. Shows Zarr files in the selected cell directory and allows selection.
    4. Lists components within the selected Zarr file and allows multi-selection.
    5. Constructs a Neuroglancer command based on selected components.
    6. Executes Neuroglancer command when requested.
    """
    st.title("See files in Neuroglancer Zarr File Explorer")

    data_dir = st.text_input("Enter the data directory:", value='../data')

    if os.path.isdir(data_dir):
        cells = find_cells(data_dir)
        if cells:
            selected_cell = st.selectbox("Select a cell:", cells)
            if selected_cell:
                cell_dir = os.path.join(data_dir, selected_cell)
                zarr_files = find_zarr_files(cell_dir)
                if zarr_files:
                    st.write("Found Zarr files:")
                    selected_file = st.selectbox("Select a Zarr file:", zarr_files)
                    if selected_file:
                        components = list_zarr_components(selected_file)
                        if components:
                            selected_components = st.multiselect("Select components:", components)
                            if selected_components:
                                st.write("Selected components:")
                                st.write(selected_components)
                                
                                segementation_folder=find_segmentation_folder(selected_components, selected_file)
                                if segementation_folder:
                                    selected_components.append(segementation_folder)

                                neuroglancer_cmd = f"neuroglancer -f {selected_file} -d " + ' '.join(selected_components)
                                st.write("Neuroglancer Command:")
                                st.code(neuroglancer_cmd, language='bash')

                                if st.button('Run Neuroglancer'):
                                    subprocess.run(neuroglancer_cmd, shell=True)
                                    st.success("Neuroglancer command executed!")
