# 🧠 Smart Tutor KI-osk 🦉

An interactive, local-first learning demo built with **Streamlit** and **Ollama**.

Explore introductory AI topics, discover alternative explanations, and check your understanding through quizzes—all with a language model running locally.

## Learning experience

**Choose a topic → Read the lesson → Explore explanations → Take a quiz → Review your progress**

The application combines prepared lessons and quizzes with AI-generated explanations tailored to different learning preferences.

| Explanation style | What it offers |
| --- | --- |
| 📘 **Easy-to-Read** | Clearer wording and simpler structure |
| ✨ **Simple** | A shorter, more direct explanation |
| 🔄 **Examples** | Familiar real-world examples |
| 🎯 **Custom Analogies** | Connections to a domain chosen by the learner |

Alternative explanations are available before and after the first quiz. Learners can compare explanations, review their scores, and optionally complete a second quiz.

## Explore the topics

| 🧠 Neural Networks | 🏷️ Learning Approaches |
| :--- | :--- |
| **What Is a Neural Network?**<br>Explore the basic idea behind artificial neural networks. | **Supervised vs. Unsupervised Learning**<br>Discover how learning with labels differs from finding patterns without them. |

| ✨ Generative AI | 🎯 Recommendation Systems |
| :--- | :--- |
| **What is Generative AI?**<br>Understand how AI systems generate new content. | **How Recommendation Systems Work**<br>Explore how systems suggest relevant items and content. |

| 📈 Overfitting | 💬 Large Language Models |
| :--- | :--- |
| **What Is Overfitting?**<br>Learn why fitting training data closely can hurt performance on new examples. | **What Is a Large Language Model?**<br>Discover the foundations of models that process and generate language. |

| 🔍 Model Errors | 🖼️ Image Recognition |
| :--- | :--- |
| **Why Do AI Models Make Mistakes?**<br>Explore the limitations behind incorrect predictions. | **How AI Recognizes Images**<br>Learn how models identify patterns in visual information. |

## Requirements

- Git.
- Python. The application was checked with **Python 3.12**.
- Ollama with **`qwen2.5:3b`** for generating explanations.

Internet access is needed to install dependencies and download the model. Once installed, the main learning flow can run locally without a hosted LLM API or API key.

Generation speed depends on the available hardware.

## Installation

Clone the repository:

```bash
git clone https://github.com/pffaundez/smart-tutor-kiosk.git
cd smart-tutor-kiosk
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

On Windows:

```powershell
py -3.12 -m venv .venv
```

Activate the environment.

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies required by the main application:

```bash
python -m pip install streamlit requests
```

The repository's `requirements.txt` includes additional packages for retrieval and auxiliary scripts. These are not required for the current main interface.

## Set up the local model

Install and start [Ollama](https://ollama.com), then download the configured model:

```bash
ollama pull qwen2.5:3b
```

If Ollama is not already running as a background service, start it in a separate terminal:

```bash
ollama serve
```

If the address is already in use, check whether Ollama is already running.

Verify inference:

```bash
ollama run qwen2.5:3b "Explain neural networks in one sentence."
```

| Setting | Default |
| --- | --- |
| Ollama URL | `http://127.0.0.1:11434` |
| Model | `qwen2.5:3b` |
| Request timeout | 160 seconds |

## Run the application

From the repository root, with the virtual environment activated:

```bash
python -m streamlit run app/main.py
```

Open **http://localhost:8501**.

Run the command from the repository root because lesson and image paths are relative to the working directory.

To use a different port:

```bash
python -m streamlit run app/main.py --server.port 8502
```

Press `Ctrl+C` to stop the application.

> Lessons and quizzes are available without Ollama. **Generate explanation** requires the Ollama service and the configured model.

## How it works

The application loads prepared lessons and quizzes from local files.

When a learner requests another explanation, it sends the lesson and the selected style instructions to Ollama through `/api/chat`. The generated explanation is displayed alongside its request latency.

Quiz scores are calculated using stored answer keys, rather than graded by the language model.

### Retrieval status

The repository contains retrieval utilities, a FAISS index, and embedding metadata. The current main application does **not** use them.

The active flow sends the selected lesson directly to the model. Running the interface does not require FAISS, an embedding model, or rebuilding the index.

### Model configuration

The model and service URL are configured in `app/main.py`:

```python
llm3 = "qwen2.5:3b"
```

```python
base_url = "http://127.0.0.1:11434"
model_name = llm3
```

Setting `DEBUG_MODE = True` exposes model and URL controls in the interface. Download any replacement model through Ollama before selecting it.

The current application does not load these settings from a `.env` file.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| **Streamlit module not found** | Activate the virtual environment and run `python -m pip install streamlit requests`. |
| **No topics or missing images** | Launch the application from the repository root. |
| **Connection refused during generation** | Ensure Ollama is running at `http://127.0.0.1:11434`. |
| **Model not found** | Run `ollama pull qwen2.5:3b`. Use `ollama list` to inspect installed models. |
| **Slow generation or timeout** | Test inference with `ollama run`. The first request may take longer while the model loads. |
| **Streamlit port occupied** | Add `--server.port 8502` to the launch command. |

The explanation service may retry a response that appears truncated, adding another inference request.

## Current scope and limitations

- Lessons and quizzes are prepared content; alternative explanations are generated locally.
- The **“Generate (soon)”** topic-generation feature is not implemented.
- Generated explanations may contain errors or misleading analogies.
- Quiz scores provide demo feedback, not a validated assessment of learning outcomes.
- Session state is managed by Streamlit. The 120-second idle threshold is evaluated when the application reruns.
- This is an educational prototype, not a production deployment.

## Verification

The application was checked with Python 3.12:

- Streamlit started and returned a successful health response.
- All eight topics rendered through Streamlit's application-testing interface.
- All sixteen quiz datasets returned full scores when supplied with their answer keys.

These checks do not constitute a complete browser or accessibility review. Live explanation generation also requires verification with a running Ollama instance.



