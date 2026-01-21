# Smart Tutor Kiosk

This repository contains the demo of a Smart Tutor (on development) designed for a the kiosk in HNI Entrance Hall.

The system presents short explanations of 10 curated AI-related topics, evaluates understanding through multiple-choice questions, and uses an LLM at runtime to provide adaptive reinforcement when mistakes are detected.

The project is built as a web application using Streamlit and is intended to run in a browser configured in kiosk mode on an Android 11 device.

## TEMPORARY - LLM Smoke Test (Local, CPU, Ollama)

1. Install Ollama and pull a small model:
   ```bash
   ollama pull tinyllama

2. Start the Ollama server:
      ```bash
   ollama serve
4. Install Dependencies and run Streamlit (from Project Root):
   ```bash
   pip install streamlit requests
   python -m streamlit run app/main.py

6. Open the Streamlit UI and go to the sections:
   - Compatibility Test
   - Inference Smoke Test
   - LLM Smoke Test
7. Run the tests to verify that each page returns successful responses with latency and generated text.

## Main Components

- `content/`  
  Curated educational material for each topic:
  - `source.md`: full grounding text used by the LLM
  - `lesson.md`: short explanation shown to the user
  - `quiz_1.json`, `quiz_2.json`: assessment questions
  - `meta.json`: topic metadata

- `app/`  
  Streamlit application implementing the user interface, session flow, scoring, and LLM interaction.

- `prompts/`  
  Prompt templates and guardrails used to control the model at runtime.

- `schema/`  
  JSON schemas to validate content structure and ensure consistency.

## Pipelines

The system is organized around three pipelines, illustrated in the diagram presented below:

1. **Content Pipeline**  
   Human-authored topics are validated against schemas and prepared for use by the application.

2. **Application Pipeline**  
   The Streamlit app is built and deployed to a server accessible by the kiosk device.

3. **Runtime AI Pipeline**  
   During user interaction, the LLM generates explanations and reinforcement grounded strictly in the curated topic sources.

   ----

<img width="1103" height="906" alt="image" src="https://github.com/user-attachments/assets/0801f0fa-19f6-4273-a99f-166a7fad2d08" />

----

## Purpose

The goal of this demo is to show how adaptive tutoring with large language models can be deployed in a controlled, transparent, and safe way for public educational environments, using curated content and strict runtime guardrails.



