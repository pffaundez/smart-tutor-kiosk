<img width="1721" height="144" alt="Screenshot from 2026-10-06 15-16-15" src="https://github.com/user-attachments/assets/cc56a1db-0e3d-47f2-ab2b-b4b40b74bebe" />

# Smart Tutor KI-osk

Smart Tutor Kiosk is an interactive, local-first AI tutoring demo designed for the kiosk in the HNI Entrance Hall.

The application presents short, curated lessons about artificial intelligence, lets visitors test their understanding with multiple-choice quizzes, and uses a local Large Language Model (LLM) to re-explain the same lesson in different ways. The goal is to demonstrate adaptive tutoring while keeping the educational content controlled and grounded in curated material.

The application is built with Streamlit and is designed for a public touchscreen/kiosk experience.

## Current Demo

The current learning flow is:

1. **Choose a topic** from the curated topic library.
2. **Read the lesson** in a focused lesson card.
3. **Re-explain the lesson** immediately if another explanation would help.
4. **Take Quiz 1** to test understanding.
5. **Review the result** and receive a suggested re-explanation style based on quiz performance.
6. **Generate another explanation** if desired.
7. **Optionally take Quiz 2** as a reinforcement/backup quiz.
8. **Review the final result** and return to the topic library or start over.

Re-explanation is intentionally available before Quiz 1. It is a central part of the demo rather than a feature unlocked only after making mistakes.

## Adaptive Re-explanations

Smart Tutor currently provides four re-explanation modes:

- **Easy-to-Read** — clearer wording and simpler sentence structure.
- **Simple** — a shorter and more direct explanation.
- **Everyday Analogies** — explains the lesson through familiar real-world analogies.
- **Custom Domain Analogies** — lets the visitor choose a domain such as sports, cooking, retail, or music and generates an analogy-based explanation around it.

Generated explanations are constrained to the lesson as their factual source. The prompts instruct the model to rephrase the lesson rather than introduce new facts.

After Quiz 1, the application recommends a re-explanation mode according to quiz performance. Visitors can still select any of the available modes.

The generated explanation can be viewed next to the original lesson for comparison or on its own. Generation latency is also shown in the interface.

## Quiz Experience

Each topic includes two multiple-choice quizzes:

- **Quiz 1** is the main knowledge check.
- **Quiz 2** is an optional reinforcement quiz.

Questions are presented one at a time in a carousel-style flow so the interface remains suitable for a touchscreen kiosk. Users can navigate between questions before submitting their answers.

After Quiz 1, the score is used to recommend an explanation style. The final screen summarizes the session and, when Quiz 2 was taken, shows both quiz results.

## Curated Topics

The repository currently contains eight topics:

| ID | Topic |
| --- | --- |
| topic001 | What Is a Neural Network? |
| topic002 | Supervised vs. Unsupervised Learning |
| topic003 | What is Generative AI? |
| topic004 | How Recommendation Systems Work |
| topic005 | What Is Overfitting? |
| topic006 | What Is a Large Language Model? |
| topic007 | Why Do AI Models Make Mistakes? |
| topic008 | How AI Recognizes Images |

Each topic lives under `content/topics/topicXXX/` and contains the lesson, metadata, two quizzes, and supporting source material.

The topic-selection screen also includes a disabled **Coming Soon** preview for a future feature in which visitors will be able to enter their own topic and generate a lesson and quiz.

## Local LLM

The runtime re-explanation feature currently uses **Ollama** through its local `/api/chat` endpoint.

The default model configured in the application is:

```text
qwen2.5:3b
```

The default Ollama endpoint is:

```text
http://127.0.0.1:11434
```

Inference is non-streaming and runs locally. The application displays the generation latency after a re-explanation is produced.

## Running the Demo Locally

### 1. Clone the repository

```bash
git clone https://github.com/pffaundez/smart-tutor-kiosk.git
cd smart-tutor-kiosk
```

### 2. Create and activate a Python environment

Using a dedicated virtual or Conda environment is recommended.

For example:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

The current requirements include Streamlit, Requests, NumPy, Datasets, Sentence Transformers, and FAISS CPU.

### 4. Install Ollama and pull the model

Install Ollama separately, then pull the model used by the demo:

```bash
ollama pull qwen2.5:3b
```

Make sure the Ollama service is running and available at `http://127.0.0.1:11434`.

For example:

```bash
ollama serve
```

### 5. Start Smart Tutor

Run the command from the project root:

```bash
python -m streamlit run app/main.py
```

Streamlit normally makes the application available at:

```text
http://localhost:8501
```

## Project Structure

```text
smart-tutor-kiosk/
├── app/
│   ├── assets/                 # Kiosk and project visual assets
│   ├── core/
│   │   ├── content_loader.py   # Loads curated topic content
│   │   ├── reexplain_service.py
│   │   ├── retrieval/
│   │   ├── scoring.py          # Quiz scoring
│   │   ├── session.py          # Session state and timeout handling
│   │   └── text_processor.py   # Text rendering/processing helpers
│   ├── llm/
│   │   └── client.py           # Ollama /api/chat client
│   ├── prompts/
│   │   └── reexplain_modes.py  # Re-explanation prompts and guardrails
│   ├── styles/
│   │   └── main.css            # Main kiosk UI styling
│   ├── pages/
│   └── main.py                 # Streamlit application entry point
├── content/
│   ├── index/
│   ├── lesson_generator/
│   └── topics/
│       ├── topic001/
│       ├── ...
│       └── topic008/
├── ui/                         # Additional/reusable UI modules
├── benchmark_qwen_100.py       # Qwen benchmark utility
├── requirements.txt
└── README.md
```

## Topic Content Structure

A topic normally contains:

```text
topicXXX/
├── lesson.md
├── meta.json
├── quiz_1.json
├── quiz_2.json
└── source.md
```

- `lesson.md` contains the explanation displayed to the visitor.
- `meta.json` contains topic metadata such as title, level, learning objectives, and key concepts.
- `quiz_1.json` contains the main knowledge check.
- `quiz_2.json` contains the optional reinforcement quiz.
- `source.md` contains supporting/grounding material associated with the topic.

## Application Architecture

The project separates the main responsibilities of the demo:

### Content layer

Curated educational material is stored independently from application logic under `content/topics/`. This makes topics easy to review and extend without embedding lesson content directly in the Streamlit application.

### Application layer

`app/main.py` controls the kiosk learning flow, topic selection, lesson presentation, quizzes, re-explanation selection, recommendations, results, and navigation.

Session state keeps the visitor inside the current learning flow and provides reset/navigation behavior appropriate for a shared public kiosk.

### Runtime AI layer

`app/core/reexplain_service.py` builds the re-explanation request, while `app/prompts/reexplain_modes.py` defines the behavior and guardrails for each explanation style.

`app/llm/client.py` sends the request to the local Ollama server. The current configuration uses Qwen 2.5 3B.

### Presentation layer

The interface uses Streamlit plus custom CSS in `app/styles/main.css`. The current UI includes lesson cards, explanation-mode cards, loading feedback during inference, side-by-side lesson/re-explanation comparison, quiz navigation, recommendation banners, score cards, and result summaries.

Project branding assets are stored in `app/assets/`.

## System Overview

The original project architecture is illustrated below. The implementation has evolved since this diagram was created, but the high-level separation between curated content, the application, and runtime AI remains useful.

<img width="1103" height="906" alt="Smart Tutor system overview" src="https://github.com/user-attachments/assets/0801f0fa-19f6-4273-a99f-166a7fad2d08" />

## Design Principles

Smart Tutor is built around a few core principles:

- **Curated first:** lessons and quizzes are prepared content rather than unrestricted generation.
- **Grounded re-explanation:** runtime generation is instructed to stay within the factual content of the lesson.
- **Adaptive but user-controlled:** quiz performance can suggest a mode, but the visitor remains free to choose another explanation.
- **Local-first inference:** the current demo talks to a local Ollama instance rather than requiring a cloud LLM API.
- **Kiosk-friendly interaction:** large controls, simple navigation, clear feedback, and short learning sessions are prioritized.
- **Transparent comparison:** visitors can compare the original lesson with the generated explanation.

## Purpose

The goal of Smart Tutor Kiosk is to explore how adaptive tutoring with Large Language Models can be deployed in a controlled and understandable way for public educational environments.

The demo combines curated AI-literacy content, lightweight assessment, adaptive re-explanation, and local inference to demonstrate how an AI tutor can respond to different learning needs without giving up control over the underlying educational material.

## Status

Smart Tutor Kiosk is an active prototype. The current repository represents the demo implementation and continues to evolve based on testing and user feedback.
