
import logging
import os
import random
import subprocess

import streamlit as st
from incasem_setup import handle_exceptions
from utils import create_config_file, run_command, validate_tiff_filename

logging.basicConfig(filename="training.log", encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATA_CONFIG_PATH = "../scripts/02_train/data_configs/"

@handle_exceptions
def run_training(train_config_path: str, val_config_path: str, model_name: str, cell_paths: list):
    """
    Run the training process for the model.

    :param train_config_path: Path to the training configuration file.
    :param val_config_path: Path to the validation configuration file.
    :param model_name: Name of the model to be trained.
    :param cell_paths: List of cell paths.
    :func:`run_command`
    """
    st.subheader("Run Training")

    st.write("Creating metric masks...")
    for cell_path in cell_paths:
        cell_name = os.path.basename(cell_path.rstrip('/'))
        mask_cmd = f"python ../scripts/01_data_formatting/60_create_metric_mask.py -f {cell_path}/{cell_name}.zarr -d volumes/labels/er --out_dataset volumes/metric_masks/er --exclude_voxels_inwards 2 --exclude_voxels_outwards 2"
        run_command(mask_cmd, f"Metric mask created for {cell_name}!")

    st.write("Running training...")
    train_cmd = f"python ../scripts/02_train/train.py --name {model_name} with config_train.yaml 'train.data={train_config_path}' 'train.validation={val_config_path}'"
    run_command(train_cmd, "Training complete!")


def validate_path(path: str) -> bool:
    """
    Validate if the given path exists.

    :param path: Path to validate.
    :return: True if the path exists, False otherwise.
    """
    if os.path.exists(path):
        return True
    else:
        st.error(f"The path {path} does not exist. Please enter a valid path.")
        return False

def get_available_json_files(path: str):
    """
    Get a list of available JSON files in the given directory.

    :param path: Directory path to search for JSON files.
    :return: List of JSON file names.
    """
    return [f for f in os.listdir(path) if f.endswith('.json')]

@handle_exceptions
def take_input_and_create_configs():

    """
    @Title - Training Configuration Workflow
    @Description:
    This function facilitates the training configuration process for models using user-provided data. The workflow includes creating training and validation configuration entries, validating paths, and selecting configuration files for running the training process.

    Steps Involved:

    1. **Create Training and Validation Entries:**
       - User provides names, file paths, offsets, shapes, voxel sizes, raw data paths, metric masks, and labels for both training and validation entries.

    2. **Create Configuration Files:**
       - Users can create training and validation configuration files with the provided entries.

    3. **Run Training Process:**
       - Users select existing configuration files for training and validation.
       - Provide cell paths for training.
       - Validate the provided paths.
       - Run the training process with the selected configuration files and model name.

    Code Workflow:

    1. **Create Training and Validation Entries:**
       - Ask users to add training and validation entries, providing details such as names, file paths, offsets, shapes, voxel sizes, raw data paths, metric masks, and labels.

    2. **Create Configuration Files:**
       - Allow users to create configuration files with the provided entries and specify names for the configuration files.
       - Create the configuration files and display a success message.

    3. **Select Configuration Files:**
       - Display available JSON configuration files for training and validation.
       - Allow users to select the configuration files for the training process.

    4. **Provide Cell Paths:**
       - Users provide cell paths for training.
       - Validate the provided paths.

    5. **Run Training:**
       - Run the training process with the selected configuration files and model name.
    """
    st.title("Incasem Training Configuration")
    st.write("Create training and validation configuration entries")

    train_config = {}
    val_config = {}

    if 'train_entries' not in st.session_state:
        st.session_state['train_entries'] = []
    if 'val_entries' not in st.session_state:
        st.session_state['val_entries'] = []

    if st.button('Add training entry'):
        st.session_state['train_entries'].append({
            "name": "",
            "file": "",
            "offset": [0, 0, 0],
            "shape": [0, 0, 0],
            "voxel_size": [5, 5, 5],
            "raw": "",
            "metric_masks": [],
            "labels": {}
        })

    if st.button('Add validation entry'):
        st.session_state['val_entries'].append({
            "name": "",
            "file": "",
            "offset": [0, 0, 0],
            "shape": [0, 0, 0],
            "voxel_size": [5, 5, 5],
            "raw": "",
            "metric_masks": [],
            "labels": {}
        })

    for i, entry in enumerate(st.session_state['train_entries']):
        with st.expander(f"Training Entry {i+1}"):
            entry['name'] = st.text_input(f"Enter name for training entry {i+1}", entry['name'])
            entry['file'] = st.text_input(f"Enter file path for training entry {i+1}", entry['file'])
            entry['offset'] = [st.number_input(f"Offset Z for training entry {i+1}", value=entry['offset'][0]),
                               st.number_input(f"Offset Y for training entry {i+1}", value=entry['offset'][1]),
                               st.number_input(f"Offset X for training entry {i+1}", value=entry['offset'][2])]
            entry['shape'] = [st.number_input(f"Shape Z for training entry {i+1}", value=entry['shape'][0]),
                              st.number_input(f"Shape Y for training entry {i+1}", value=entry['shape'][1]),
                              st.number_input(f"Shape X for training entry {i+1}", value=entry['shape'][2])]
            entry['raw'] = st.text_input(f"Enter raw data path for training entry {i+1}", entry['raw'])
            entry['metric_masks'] = st.text_input(f"Enter metric masks for training entry {i+1} (comma-separated)", ",".join(entry['metric_masks'])).split(',')
            label_key = st.text_input(f"Enter label key for training entry {i+1}", "")
            label_value = st.number_input(f"Enter label value for training entry {i+1}", value=1)
            if label_key:
                entry['labels'][label_key] = label_value

    for i, entry in enumerate(st.session_state['val_entries']):
        with st.expander(f"Validation Entry {i+1}"):
            entry['name'] = st.text_input(f"Enter name for validation entry {i+1}", entry['name'])
            entry['file'] = st.text_input(f"Enter file path for validation entry {i+1}", entry['file'])
            entry['offset'] = [st.number_input(f"Offset Z for validation entry {i+1}", value=entry['offset'][0]),
                               st.number_input(f"Offset Y for validation entry {i+1}", value=entry['offset'][1]),
                               st.number_input(f"Offset X for validation entry {i+1}", value=entry['offset'][2])]
            entry['shape'] = [st.number_input(f"Shape Z for validation entry {i+1}", value=entry['shape'][0]),
                              st.number_input(f"Shape Y for validation entry {i+1}", value=entry['shape'][1]),
                              st.number_input(f"Shape X for validation entry {i+1}", value=entry['shape'][2])]
            entry['raw'] = st.text_input(f"Enter raw data path for validation entry {i+1}", entry['raw'])
            entry['metric_masks'] = st.text_input(f"Enter metric masks for validation entry {i+1} (comma-separated)", ",".join(entry['metric_masks'])).split(',')
            label_key = st.text_input(f"Enter label key for validation entry {i+1}", "")
            label_value = st.number_input(f"Enter label value for validation entry {i+1}", value=1)
            if label_key:
                entry['labels'][label_key] = label_value

    for entry in st.session_state['train_entries']:
        train_config[entry["name"]] = {k: v for k, v in entry.items() if k != "name"}

    for entry in st.session_state['val_entries']:
        val_config[entry["name"]] = {k: v for k, v in entry.items() if k != "name"}

    train_config_name = st.text_input("Enter the name for the training config JSON file", f"")
    val_config_name = st.text_input("Enter the name for the validation config JSON file", f"")

    if st.button('Create Configurations'):
        if train_config_name != "":
            train_config_path = create_config_file(output_path=DATA_CONFIG_PATH, config=train_config, file_name=train_config_name)
        if val_config_name != "":
            val_config_path = create_config_file(output_path=DATA_CONFIG_PATH, config=val_config, file_name=val_config_name)
        st.success("Configuration files created successfully!")
        run_training_from_configs()
        
@handle_exceptions
def run_training_from_configs():
    st.title("Run Training")
    st.write("Select existing configuration files for training and validation")

    available_train_configs = get_available_json_files(DATA_CONFIG_PATH)
    available_val_configs = get_available_json_files(DATA_CONFIG_PATH)

    selected_train_config = st.selectbox("Select a training config JSON file", available_train_configs)
    selected_val_config = st.selectbox("Select a validation config JSON file", available_val_configs)

    cell_paths = st.text_area("Enter the paths for the cells (one per line)").split("\n")
    cell_paths = [path.strip() for path in cell_paths if path.strip()]

    model_name = st.text_input("Enter the name of the model", f"model_{random.randrange(0, 1000)}")

    if st.button('Run Training'):
        if all(validate_path(path) for path in cell_paths):
            train_config_path = os.path.join(DATA_CONFIG_PATH, selected_train_config)
            val_config_path = os.path.join(DATA_CONFIG_PATH, selected_val_config)
            run_training(train_config_path=train_config_path, val_config_path=val_config_path, model_name=model_name, cell_paths=cell_paths)
            st.success("Training process is complete!")


