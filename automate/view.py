import os

import streamlit as st
import zarr


def find_cells(data_dir):
    cells = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and d.startswith('cell')]
    return cells

def find_zarr_files(cell_dir):
    zarr_files = []
    for root, dirs, files in os.walk(cell_dir):
        for dir_name in dirs:
            if dir_name.endswith('.zarr'):
                zarr_files.append(os.path.join(root, dir_name))
    return zarr_files

def list_zarr_components(zarr_file_path):
    root = zarr.open(zarr_file_path, mode='r')
    volumes_path = 'volumes'
    components = []

    if volumes_path in root:
        volumes = root[volumes_path]
        for key in volumes:
            if key == 'labels' or key == 'predictions' or key.startswith('raw_'):
                if isinstance(volumes[key], zarr.Group):
                    for sub_key in volumes[key]:
                        components.append(f"{volumes_path}/{key}/{sub_key}")
                else:
                    components.append(f"{volumes_path}/{key}")
    return components

def view_cells_and_flatten_them(): 
    st.title("Zarr File Explorer")

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

