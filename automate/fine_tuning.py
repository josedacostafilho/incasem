import json
import os
import random
import subprocess

import streamlit as st
from incasem_setup import handle_exceptions
from utils import (convert_tiff_to_zarr, create_config_file, run_command,
                   validate_tiff_filename)


@handle_exceptions
def prepare_annotations(input_path: str, output_path: str):
    """If the file type if tiff, users can convert them to zarr format and if they want, they can also make a metric exclusion zone"""
    st.write("Preparing annotations...")
    convert_cmd = f"python ../scripts/01_data_formatting/00_image_sequences_to_zarr.py -i {input_path} -f {output_path} -d volumes/labels/er --dtype uint32"
    run_command(convert_cmd, "Conversion to zarr format complete for annotations!")
    
    st.write("Creating metric exclusion zone...")
    exclusion_cmd = f"python ../scripts/01_data_formatting/60_create_metric_mask.py -f {output_path} -d volumes/labels/er --out_dataset volumes/metric_masks/er --exclude_voxels_inwards 2 --exclude_voxels_outwards 2"
    run_command(exclusion_cmd, "Metric exclusion zone created!")

@handle_exceptions
def run_fine_tuning(config_path: str, model_id: str, checkpoint_path: str, output_path: str):
    """Running fine tuninng: We also let users view the results on omniboard and tensorboard"""
    st.write("Running fine-tuning...")
    name=st.text_input("Enter the name of the fine tuned file ", "example_finetune", help="Default name set to example_finetune" )
    iterations=st.number_input(label="Enter the number of iterations you want to run, leave blank for default", value=15000) 
    fine_tune_cmd = f"python ../scripts/02_train/train.py --name {name} --start_from {model_id} {checkpoint_path} with config_training.yaml training.data={config_path} validation.data={config_path} torch.device=0 training.iterations={iterations}"
    run_command(fine_tune_cmd, "Fine-tuning complete!")
    with st.echo():
        st.write("Starting TensorBoard...")
        tensorboard_cmd = f"tensorboard --logdir={output_path}/tensorboard --host 0.0.0.0 --port 6006"
        subprocess.Popen(tensorboard_cmd, shell=True)
        st.write("TensorBoard running at http://localhost:6006")

        st.write("Starting Omniboard...")
        omniboard_cmd = f"omniboard -m localhost:27017:incasem_trainings"
        subprocess.Popen(omniboard_cmd, shell=True)
        st.write("Omniboard running at http://localhost:9000")

def download_training_data():
    """Code to create a text box for users to input the location of data they want to download"""
    st.write("Downloading training data...")
    path=st.text_input("Please enter the path to your dataset, eg(s3://path-to-your-dataset/cell3.zarr", "")
    download_cmd = f"aws s3 cp {path} ../data/ --recursive"
    if st.button("Run Command"):
        run_command(download_cmd, "Download complete!")
        st.success("We were successfully able to download the sample data to the location ../data/ in the codebase!")
    elif st.button("Continue without downloading.. "):
        return

@handle_exceptions
def open_config_file_to_view() -> None:
    """Let users view the configuration file"""
    with open("../scripts/02_train/data_configs/example_finetune_mito.json", "r") as f:
        data=json.load(f)
        if data is not None:
            st.json(data, expanded=True)
            st.success("Loaded JSON from ../scripts/02_train/data_configs/example_finetune_mito.json")

@handle_exceptions
def take_input_and_run_fine_tuning() -> None:
    """
    @Title - Fine Tuning Workflow
    @Description:
    1) Copy annotation data into project directory, activate environment, convert tiff to zarr.
    2) View in Neuroglancer if needed, create a metric exclusion zone
    3) We give the users the option to download the training data if needed from the s3 bucket
    4) Allow users to create a config file (relative path for test is ../scripts/02_train/data_configs/example_finetune_mito.json)
    5) Once the config is made users can launch the training and view it using tensorboard and omniboard 

    @@ Code Workflow:
    1) Ask users for the input path for annotations and output path for zarr files
    2) Ask the users if they want to download sample data [See :func `download_training_data`]
    3) Show them a samle configuration [See :func `open_config_file_to_view`]
    4) Let them create a config, with indefinite amounts of additional objects to be added
    5) Once done, they can pick out of 7 models which one they want to run
    6) Users can choose to convert the Tiffs to zarrs and also make a metric exclusion zone [See :func `prepare_annotations`]
    7) Finally they can run a prediction [See :func `run_fine_tuning`]
    """
    st.title("Incasem Fine-Tuning")
    st.write("Welcome to the Incasem fine-tuning interface")
    
    file_type = st.radio("Select file type", ('TIFF', 'ZARR'))

    input_path = st.text_input("Enter the input path for annotations","", help=" You can have it on your local machine, in the ../scripts/02_train/data_configs folder or on the cloud, its empty by default")
    output_path = st.text_input("Enter the output path for zarr format", "", help=" normally its ../scripts/02_train/data_configs")

    if st.button('Download Training Data', help="If you want to download some test data, you can choose a path to enter once you click this button"):
        download_training_data()

    if file_type == 'TIFF':
        if not validate_tiff_filename(input_path):
            st.error("Invalid TIFF filename format. Please ensure the filename follows the pattern: .*_(\\d+).*\\.tif$")
        else:
            volume_name=st.text_input("Enter the volume name you want to use, default=volumes/raw ", "volumes/raw")
            convert_tiff_to_zarr(input_path=input_path, output_path=output_path, volume_name=volume_name) 

    st.write("Create fine-tuning configuration entries")
    config = {}
    config_entries = []

    st.write("Here is an example file for you to view: ")
    open_config_file_to_view()

    if 'config_entries' not in st.session_state:
        st.session_state['config_entries'] = []

    if st.button('Add configuration entry'):
        st.session_state['config_entries'].append({
            "path": "",
            "name": "",
            "raw": "",
            "labels": {}
        })

    for i, entry in enumerate(st.session_state['config_entries']):
        with st.expander(f"Configuration Entry {i+1}"):
            entry['path'] = st.text_input(f"Enter file path for entry {i+1}", entry['path'])
            entry['name'] = st.text_input(f"Enter ROI name for entry {i+1}", entry['name'])
            entry['raw'] = st.text_input(f"Enter raw data path for entry {i+1}", entry['raw'])
            label_key = st.text_input(f"Enter label key for entry {i+1}", "")
            label_value = st.number_input(f"Enter label value for entry {i+1}", value=1)
            if label_key:
                entry['labels'][label_key] = label_value

    for entry in st.session_state['config_entries']:
        config[entry["path"]] = {
            "name": entry["name"],
            "raw": entry["raw"],
            "labels": entry["labels"]
        }

    file_name = st.text_input("Enter the name of the inference file, default is inference__", f"inference__")

    if st.button('Create Configuration'):
        config_path = create_config_file(output_path=output_path, config=config, file_name=file_name)
        st.success("Configuration file created successfully!")

        st.write("Choose a model")
        model_options = {
            "FIB-SEM Chemical Fixation Mitochondria (CF, 5x5x5)": "1847",
            "FIB-SEM Chemical Fixation Golgi Apparatus (CF, 5x5x5)": "1837",
            "FIB-SEM Chemical Fixation Endoplasmic Reticulum (CF, 5x5x5)": "1841",
            "FIB-SEM High-Pressure Freezing Mitochondria (HPF, 4x4x4)": "1675",
            "FIB-SEM High-Pressure Freezing Endoplasmic Reticulum (HPF, 4x4x4)": "1669",
            "FIB-SEM High-Pressure Freezing Clathrin-Coated Pits (HPF, 5x5x5)": "1986",
            "FIB-SEM High-Pressure Freezing Nuclear Pores (HPF, 5x5x5)": "2000"
        }
        model_choice = st.selectbox("Select a model", list(model_options.keys()))
        model_id = model_options[model_choice]
        checkpoint_path = f"../models/pretrained_checkpoints/model_checkpoint_{model_id}_er_CF.pt"

        if st.button('Prepare Annotations', help="For converting tiff to zarr and making a metric exclusion done"):
            prepare_annotations(input_path=input_path, output_path=output_path)
            st.success("Annotations prepared successfully!")

        if st.button('Run Fine-Tuning', help="Run the fine tuning"):
            run_fine_tuning(config_path=config_path, model_id=model_id, checkpoint_path=checkpoint_path, output_path=output_path)
            st.success("Fine-tuning process is complete!")

