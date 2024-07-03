
import os
import random
import subprocess

import streamlit as st
from incasem_setup import handle_exceptions
from utils import create_config_file, run_command, validate_tiff_filename


@handle_exceptions
def prepare_annotations(input_path: str, output_path: str):
    st.write("Preparing annotations...")
    convert_cmd = f"python ../incasem/scripts/01_data_formatting/00_image_sequences_to_zarr.py -i {input_path} -f {output_path} -d volumes/labels/er --dtype uint32"
    run_command(convert_cmd, "Conversion to zarr format complete for annotations!")
    
    st.write("Creating metric exclusion zone...")
    exclusion_cmd = f"python ../incasem/scripts/01_data_formatting/60_create_metric_mask.py -f {output_path} -d volumes/labels/er --out_dataset volumes/metric_masks/er --exclude_voxels_inwards 2 --exclude_voxels_outwards 2"
    run_command(exclusion_cmd, "Metric exclusion zone created!")

@handle_exceptions
def run_fine_tuning(config_path: str, model_id: str, checkpoint_path: str):
    st.write("Running fine-tuning...")
    fine_tune_cmd = f"python ../incasem/scripts/02_train/train.py --name example_finetune --start_from {model_id} {checkpoint_path} with config_training.yaml training.data={config_path} validation.data={config_path} torch.device=0 training.iterations=15000"
    run_command(fine_tune_cmd, "Fine-tuning complete!")

@handle_exceptions
def take_input_and_run_fine_tuning():
    st.title("Incasem Fine-Tuning")
    st.write("Welcome to the Incasem fine-tuning interface")

    input_path = st.text_input("Enter the input path for annotations", "")
    output_path = st.text_input("Enter the output path for zarr format", "")

    if not validate_tiff_filename(input_path):
        st.error("Invalid TIFF filename format. Please ensure the filename follows the pattern: .*_(\\d+).*\\.tif$")
        return

    st.write("Create fine-tuning configuration entries")
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

        if st.button('Prepare Annotations'):
            prepare_annotations(input_path=input_path, output_path=output_path)
            st.success("Annotations prepared successfully!")

        if st.button('Run Fine-Tuning'):
            run_fine_tuning(config_path=config_path, model_id=model_id, checkpoint_path=checkpoint_path)
            st.success("Fine-tuning process is complete!")

def main():
    take_input_and_run_fine_tuning()

if __name__ == '__main__':
    main()
