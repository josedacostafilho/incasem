import json

import streamlit as st

with open("../scripts/02_train/data_configs/example_finetune_mito.json", "r") as f:
    data=json.load(f)
    if data is not None:
        st.json(data, expanded=True)

