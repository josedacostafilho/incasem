import json
import logging
import os
import re
import subprocess

import streamlit as st
from incasem_setup import handle_exceptions

logging.basicConfig(level=logging.INFO)
logging.basicConfig(filename="prediction.log", encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger(__name__)

@handle_exceptions
def run_prediction(input_path: str, output_path: str, volume_name:str, config_path: str, model_id: str, checkpoint_path: str, is_tiff: bool):
    st.subheader("Run Prediction")

    if is_tiff:
        st.write("Checking the size of the TIFF file...")
        file_size = os.path.getsize(input_path)
        st.write(f"File size: {file_size} bytes")

        if file_size > 10 * 1024 * 1024:  # 10 GB
            st.write("Large TIFF file detected. Using Dask for conversion...")
            # TODO: ask users for the TIFF Volume name
            convert_cmd = f"python ../incasem/scripts/01_data_formatting/01_image_sequences_to_zarr_with_dask.py -i {input_path} -f {output_path} -d volumes/raw --resolution 5 5 5"
        else:
            st.write("Converting TIFF to zarr format...")
            convert_cmd = f"python ../incasem/scripts/01_data_formatting/00_image_sequences_to_zarr.py -i {input_path} -f {output_path}"

        subprocess.run(convert_cmd, shell=True, check=True)
        st.write("Conversion to zarr format complete!")

    st.write("Equalizing intensity histogram of the data...")
    equalize_cmd = f"python ../incasem/scripts/01_data_formatting/40_equalize_histogram.py -f {output_path} -d volumes/raw -o volumes/raw_equalized_0.02"
    subprocess.run(equalize_cmd, shell=True, check=True)
    st.write("Histogram equalization complete!")

    if st.checkbox("Do you want to visualize the data in Neuroglancer?"):
        st.write("Opening Neuroglancer...")
        neuroglancer_cmd = f"neuroglancer -f {output_path} -d volumes/raw_equalized_0.02"
        subprocess.run(neuroglancer_cmd, shell=True, check=True)

    st.write("Running prediction...")
    predict_cmd = f"python ../incasem/scripts/03_predict/predict.py --run_id {model_id} --name example_prediction with config_prediction.yaml 'prediction.data={config_path}' 'prediction.checkpoint={checkpoint_path}'"
    subprocess.run(predict_cmd, shell=True, check=True)
    st.success("Prediction complete!")

 
@handle_exceptions
def create_config_file(output_path: str, config: dict) -> str:
    config_path = os.path.join(output_path, "data_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    return config_path

@handle_exceptions
def validate_tiff_filename(filename: str) -> bool:
    return bool(re.match(r'.*_(\d+).*\.tif$', filename))


@handle_exceptions
def take_input_and_run_predictions() -> None:
    st.title("Incasem Prediction")
    st.write("Welcome to the Incasem prediction interface")

    file_type = st.radio("Select file type", ('TIFF', 'ZARR'))
    input_path = st.text_input("Enter the input path for images", "")
    output_path = st.text_input("Enter the output path for zarr format", "")
    volume_name=st.text_input("Enter the volume name", "")
    if file_type == 'TIFF':
        if not validate_tiff_filename(input_path):
            st.error("Invalid TIFF filename format. Please ensure the filename follows the pattern: .*_(\\d+).*\\.tif$")
            return

    st.write("Create data configuration entries")
    config = {}
    config_entries = []

    if 'config_entries' not in st.session_state:
        st.session_state['config_entries'] = []

    if st.button('Add configuration entry'):
        st.session_state['config_entries'].append({
            "path": "",
            "name": "",
            "raw": "",
            "mask": "",
            "labels": {}
        })

    for i, entry in enumerate(st.session_state['config_entries']):
        with st.expander(f"Configuration Entry {i+1}"):
            entry['path'] = st.text_input(f"Enter file path for entry {i+1}", entry['path'])
            entry['name'] = st.text_input(f"Enter ROI name for entry {i+1}", entry['name'])
            entry['raw'] = st.text_input(f"Enter raw data path for entry {i+1}", entry['raw'])
            entry['mask'] = st.text_input(f"Enter mask path for entry {i+1}", entry['mask'])
            label_key = st.text_input(f"Enter label key for entry {i+1}", "")
            label_value = st.number_input(f"Enter label value for entry {i+1}", value=1)
            if label_key:
                entry['labels'][label_key] = label_value

    for entry in st.session_state['config_entries']:
        config[entry["path"]] = {
            "name": entry["name"],
            "raw": entry["raw"],
            "mask": entry["mask"],
            "labels": entry["labels"]
        }

    if st.button('Create Configuration'):
        config_path = create_config_file(output_path, config)
        st.write("Configuration file created successfully!")

        st.write("Choose a model")
        model_options = {
            "FIB-SEM Chemical Fixation          Mitochondria (CF, 5x5x5)": "1847",
            "FIB-SEM Chemical Fixation          Golgi Apparatus (CF, 5x5x5)": "1837",
            "FIB-SEM Chemical Fixation          Endoplasmic Reticulum (CF, 5x5x5)": "1841",
            "FIB-SEM High-Pressure Freezing     Mitochondria (HPF, 4x4x4)": "1675",
            "FIB-SEM High-Pressure Freezing     Endoplasmic Reticulum (HPF, 4x4x4)": "1669",
            "FIB-SEM High-Pressure Freezing     Clathrin-Coated Pits (HPF, 5x5x5)": "1986",
            "FIB-SEM High-Pressure Freezing     Nuclear Pores (HPF, 5x5x5)": "2000"
        }
        model_choice = st.selectbox("Select a model", list(model_options.keys()))
        model_id = model_options[model_choice]
        checkpoint_path = f"../models/pretrained_checkpoints/model_checkpoint_1841_er_CF.pt"

        if st.button('Run Prediction'):
            run_prediction(input_path=input_path, output_path=output_path, volume_name=volume_name,config_path=config_path, model_id=model_id, checkpoint_path=checkpoint_path, file_type == 'TIFF')
            st.success("Prediction process is complete!")


