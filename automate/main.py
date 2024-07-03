import logging

import streamlit as st
from data_download import download_data
from fine_tuning import take_input_and_run_fine_tuning
from incasem_setup import (export_env, handle_exceptions, setup_conda,
                           setup_environment)
from mongodb_setup import setup_mongodb
from omniboard_setup import setup_omniboard
from prediction import take_input_and_run_predictions
from view import view_cells_and_flatten_them

logging.basicConfig(filename="main_workflow_errors.log",encoding='utf-8',level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

@handle_exceptions
def main():
    st.sidebar.title("Incasem Navigation")
    app_mode = st.sidebar.selectbox("Choose the app mode",
        ["Setup", "Data Download", "MongoDB Setup", "Omniboard Setup", "Prediction", "Fine Tuning", "View Cells"])

    if app_mode == "Setup":
        st.title("Incasem Setup")
        st.write("Welcome to the Incasem setup")
        
        if st.button('Setup Conda'):
            setup_conda() 
        
        env_name = st.text_input("Enter environment name", "incasem")
        
        if st.button('Setup Environment'):
            setup_environment(env_name)
        
        if st.button('Export Environment'):
            export_env()
        
    elif app_mode == "Data Download":
        st.title("Data Download")
        download_data()
        
    elif app_mode == "MongoDB Setup":
        st.title("MongoDB Setup")
        setup_mongodb()
        
    elif app_mode == "Omniboard Setup":
        st.title("Omniboard Setup")
        setup_omniboard()
    elif app_mode == "Prediction":
        take_input_and_run_predictions()
    elif app_mode == "View Cells":
        view_cells_and_flatten_them()
    elif app_mode == "Fine Tuning":
        take_input_and_run_fine_tuning()

    # Display workflow
    st.sidebar.title("Workflow Overview")
    st.sidebar.markdown("### Step-by-Step Guide")
    st.sidebar.write("1) a) Setup Conda")
    st.sidebar.write("1) b) Setup Environment")
    st.sidebar.write("1) c) Export Environment")
    st.sidebar.write("2) Data Download")
    st.sidebar.write("3) MongoDB Setup")
    st.sidebar.write("4) Omniboard Setup")
    st.sidebar.write("5) Prediction")
    st.sidebar.write("6) View Cells")
    st.sidebar.write("7) Fine Tuning")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")

