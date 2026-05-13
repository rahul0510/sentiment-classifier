# Sentiment Analysis — Frontend (Streamlit)

A clean Streamlit UI that sends text to the FastAPI backend and displays the
predicted sentiment with a confidence score.

---

## Folder Structure

```
FE/
├── app.py           # Streamlit application
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Quick Start (local, no Docker)

### Prerequisites
Make sure the **backend** is already running on `http://localhost:8000`.

### 1 — Create & activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Run the Streamlit app

```bash
streamlit run app.py
```

The frontend is now live at **http://localhost:8501**

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

Override the backend URL when running on a different host:

```bash
BACKEND_URL=http://my-server:8000 streamlit run app.py
```

---

## Running with Docker

```bash
docker build -t sentiment-fe .
docker run -p 8501:8501 -e BACKEND_URL=http://host.docker.internal:8000 sentiment-fe
```

---

## Features

- 📝 Text input area (up to 5 000 characters)
- 🚀 One-click **Analyse Sentiment** button
- 🎨 Colour-coded badge (green = Positive, blue = Neutral, red = Negative)
- 📊 Confidence progress bar
- ⚡ Sample input buttons for quick testing
- 🛠 Backend health indicator
- ⏱ Inference latency display
- ♿ Full error handling with friendly messages
