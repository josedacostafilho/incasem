import os
import random

import streamlit as st
from incasem_setup import handle_exceptions
from utils import (convert_tiff_to_zarr, create_config_file, run_command,
                   validate_tiff_filename)


@handle_exceptions
def run_prediction(input_path: str, output_path: str, volume_name: str, config_path: str, model_id: str, checkpoint_path: str, is_tiff: bool):
    """Run prediction on the given input data, converting TIFF to zarr if necessary, and optionally visualizing the data in Neuroglancer.
    
    Args:
        input_path (str): The input path for the data.
        output_path (str): The output path for the results.
        volume_name (str): The name of the volume to be predicted.
        config_path (str): The path to the prediction configuration file.
        model_id (str): The ID of the model to use for prediction.
        checkpoint_path (str): The path to the model checkpoint file.
        is_tiff (bool): Indicates whether the input data is in TIFF format.
    """
    st.subheader("Run Prediction")

    if is_tiff:
        convert_tiff_to_zarr(input_path=input_path, output_path=output_path, volume_name=volume_name) 
    else:
        st.write("Equalizing intensity histogram of the data...")
        equalize_cmd = f"python ../scripts/01_data_formatting/40_equalize_histogram.py -f {output_path} -d volumes/raw -o volumes/raw_equalized_0.02"
        run_command(equalize_cmd, "Histogram equalization complete!")

        if st.checkbox("Do you want to visualize the data in Neuroglancer?"):
            st.write("Opening Neuroglancer...")
            neuroglancer_cmd = f"neuroglancer -f {output_path} -d volumes/raw_equalized_0.02"
            run_command(neuroglancer_cmd, "Neuroglancer opened!")

        st.write("Running prediction...")
        predict_cmd = f"python ../scripts/03_predict/predict.py --run_id {model_id} --name example_prediction with config_prediction.yaml 'prediction.data={config_path}' 'prediction.checkpoint={checkpoint_path}'"
        run_command(predict_cmd, "Prediction complete!")

@handle_exceptions
def take_input_and_run_predictions():
    """Gather user inputs and run predictions based on the provided configuration.

    This function:
    1. Takes user inputs for file type, input path, output path, and volume name.
    2. Validates the TIFF filename if the input is in TIFF format.
    3. Allows users to create prediction configuration entries.
    4. Creates a configuration file and runs the prediction based on the selected model[See :func `run_prediction`].
    """
    st.title("Incasem Prediction")
    st.write("Welcome to the Incasem prediction interface")

    file_type = st.radio("Select file type", ('TIFF', 'ZARR'))
    input_path = st.text_input("Enter the input path", "")
    output_path = st.text_input("Enter the output path", "")
    volume_name = st.text_input("Enter the name of the volume", "")

    if file_type == 'TIFF' and not validate_tiff_filename(input_path):
        st.error("Invalid TIFF filename format. Please ensure the filename follows the pattern: .*_(\\d+).*\\.tif$")
        return

    st.write("Create prediction configuration entries")
    config = {}
    config_entries = []

    if 'config_entries' not in st.session_state:
        st.session_state['config_entries'] = []

    if st.button('Add configuration entry'):
        st.session_state['config_entries'].append({
            "nickname": "",
            "file":"",
            "offset":[0,0,0],
            "shape":[0,0,0],
            "voxel_size":[5,5,5],
            "raw": "volumes/raw_equalized_0.02"
        })

    for i, entry in enumerate(st.session_state['config_entries']):
        with st.expander(f"Configuration Entry {i+1}"):
            entry['nickname'] = st.text_input(f"Enter ROI nickname for entry {i+1}", entry['nickname'])
            entry['file'] = st.text_input(f"Enter file path for entry {i+1}", entry['file'])
            entry['offset'] = [st.number_input(f"Enter offset z for entry {i+1}", value=entry['offset'][0]),
                               st.number_input(f"Enter offset y for entry {i+1}", value=entry['offset'][1]),
                               st.number_input(f"Enter offset x for entry {i+1}", value=entry['offset'][2])]
            entry['shape'] = [st.number_input(f"Enter shape z for entry {i+1}", value=entry['shape'][0]),
                              st.number_input(f"Enter shape y for entry {i+1}", value=entry['shape'][1]),
                              st.number_input(f"Enter shape x for entry {i+1}", value=entry['shape'][2])]
            entry['raw'] = st.text_input(f"Enter raw data path for entry {i+1}", entry['raw'])
            entry["voxel_size"]=[st.number_input(f"Enter voxel_size z for entry {i+1}", value=entry['voxel_size'][0]),
                               st.number_input(f"Enter voxel_size y for entry {i+1}", value=entry['voxel_size'][1]),
                               st.number_input(f"Enter voxel_size x for entry {i+1}", value=entry['voxel_size'][2])]


    for entry in st.session_state['config_entries']:
        config[entry["nickname"]] = {
            "file": entry["file"],
            "offset": entry["offset"],
            "shape": entry["shape"],
            "voxel_size": entry["voxel_size"],
            "raw": entry["raw"]
        }    
    file_name=st.text_input("Enter the name of the inference file otherwise the default is prediction_inf_file__", f"prediction_inf_file__")
    with st.form("prediction_form"):
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
        submit_button = st.form_submit_button("Run Prediction")

    if submit_button:
        config_path = create_config_file(output_path=output_path, config=config, file_name=file_name)
        st.write("Configuration file created successfully!")

        model_id = model_options[model_choice]
        checkpoint_path = f"../models/pretrained_checkpoints/model_checkpoint_{model_id}_er_CF.pt"

        run_prediction(input_path=input_path, output_path=output_path, volume_name=volume_name, config_path=config_path, model_id=model_id, checkpoint_path=checkpoint_path, is_tiff=(file_type == 'TIFF'))
        st.success("Prediction process is complete!")
