import streamlit as st

st.set_page_config(page_title="Smart Tutor Kiosk", layout="centered")

st.title("Smart Tutor Kiosk")
st.write(
    "This is the Streamlit demo app. Use the sidebar to open the inference smoke test page."
)

st.info(
    "Next step: go to the sidebar → '00_inference_smoke_test' to test the LLM endpoint "
    "with an existing lesson file."
)
