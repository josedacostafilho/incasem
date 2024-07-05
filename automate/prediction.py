import os
import random

import streamlit as st
from incasem_setup import handle_exceptions
from utils import create_config_file, run_command, validate_tiff_filename


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
        st.write("Checking the size of the TIFF file...")
        file_size = os.path.getsize(input_path)
        st.write(f"File size: {file_size} Gigabytes [Please Enter in Gigabytes otherwise you may have issues, 1 GB = 1000MB]")

        if file_size > 10:  # 10 GB
            st.write("Large TIFF file detected. Using Dask for conversion...")
            convert_cmd = f"python ../scripts/01_data_formatting/01_image_sequences_to_zarr_with_dask.py -i {input_path} -f {output_path} -d volumes/raw --resolution 5 5 5"
        else:
            st.write("Converting TIFF to zarr format...")
            convert_cmd = f"python ../scripts/01_data_formatting/00_image_sequences_to_zarr.py -i {input_path} -f {output_path}"

        run_command(convert_cmd, "Conversion to zarr format complete!")

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
    random_file_number=random.randrange(0, 1000)
    file_name=st.text_input("Enter the name of the inference file otherwise we will generate a random file name for you", f"inference-{random_file_number}")

    if st.button('Create Configuration'):
        config_path = create_config_file(output_path=output_path, config=config, file_name=file_name)

        st.write("Configuration file created successfully!")

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

        if st.button('Run Prediction'):
            run_prediction(input_path=input_path, output_path=output_path, volume_name=volume_name, config_path=config_path, model_id=model_id, checkpoint_path=checkpoint_path, is_tiff=(file_type == 'TIFF'))
            st.success("Prediction process is complete!")


