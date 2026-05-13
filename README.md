# Sentiment Analysis — Backend (FastAPI)

A production-structured REST API that exposes a single `POST /predict` endpoint
powered by the **cardiffnlp/twitter-roberta-base-sentiment** HuggingFace model.

---

## Folder Structure

```
BE/
├── app/
│   ├── __init__.py   # Package marker
│   ├── main.py       # FastAPI app, CORS, routes, lifespan
│   ├── model.py      # Model loading & inference logic
│   ├── schemas.py    # Pydantic request/response models
│   └── utils.py      # Logger setup & label mapping
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Quick Start (local, no Docker)

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

> **Note:** The first run downloads the RoBERTa model weights (~500 MB) from
> HuggingFace Hub. Subsequent runs use the local cache.

### 3 — Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now live at **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

---

## API Reference

### `GET /health`
Returns `200 OK` with a JSON health payload.

### `POST /predict`

**Request body:**
```json
{ "text": "I really enjoyed this movie, highly recommend it!" }
```

**Response:**
```json
{ "sentiment": "Positive", "confidence": 0.9823 }
```

**Possible sentiment values:** `Positive`, `Neutral`, `Negative`

**Sample test inputs:**
| Text | Expected |
|------|----------|
| `"I love this product, works perfectly!"` | Positive |
| `"The weather today is okay."` | Neutral |
| `"This is the worst experience I've ever had."` | Negative |
| `"Just got my order, it arrived on time."` | Neutral |
| `"Absolutely terrible service, never coming back!"` | Negative |

---

## Running with Docker

```bash
# Build the image (downloads model weights during build)
docker build -t sentiment-be .

# Run the container
docker run -p 8000:8000 sentiment-be
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Override the listening port |

---

## Tech Stack

- **Python 3.11**
- **FastAPI 0.111** — async web framework
- **Uvicorn** — ASGI server
- **HuggingFace Transformers 4.41** — model inference
- **PyTorch 2.3** — deep-learning backend (CPU by default)
- **Pydantic v2** — schema validation
