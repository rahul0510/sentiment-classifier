# app.py  — Streamlit frontend for the Sentiment Analysis API
#
# Run with:
#   streamlit run app.py
#
# The app sends POST requests to the FastAPI backend and renders the result
# with a colour-coded badge, confidence gauge, and sample input buttons.

import time

import requests
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

# When running locally, the backend is at http://localhost:8000.
# When running via docker-compose, the backend service is named "backend" and
# Docker's internal DNS resolves it automatically.
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PREDICT_ENDPOINT = f"{BACKEND_URL}/predict"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"

REQUEST_TIMEOUT = 30  # seconds

# Colour palette for each sentiment label
SENTIMENT_COLOURS = {
    "Positive": "#2ecc71",   # green
    "Neutral":  "#3498db",   # blue
    "Negative": "#e74c3c",   # red
}

SENTIMENT_EMOJIS = {
    "Positive": "😊",
    "Neutral":  "😐",
    "Negative": "😞",
}

# Sample inputs the user can click to auto-fill the text area
SAMPLE_INPUTS = [
    "I absolutely love this product — it exceeded every expectation!",
    "The delivery was okay, nothing special but nothing bad either.",
    "Terrible experience. The customer support was rude and unhelpful.",
    "Just received my order. It arrived on time as promised.",
    "This is hands-down the best coffee I've ever tasted!",
    "I'm extremely disappointed. The item broke after one day of use.",
]


# ──────────────────────────────────────────────────────────────────────────────
# Page configuration (must be the first Streamlit call)
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Sentiment Analyser",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS — minimal modern styling
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
        /* Page background */
        .stApp { background-color: #f8f9fa; }

        /* Card-style result box */
        .result-card {
            background: white;
            border-radius: 12px;
            padding: 24px 32px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            text-align: center;
            margin-top: 16px;
        }

        /* Sentiment badge */
        .badge {
            display: inline-block;
            padding: 6px 20px;
            border-radius: 999px;
            font-size: 1.1rem;
            font-weight: 700;
            color: white;
            letter-spacing: 0.5px;
        }

        /* Progress bar label */
        .conf-label {
            font-size: 0.85rem;
            color: #6c757d;
            margin-bottom: 4px;
        }

        /* Subtitle / info text */
        .sub { color: #6c757d; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: call the backend
# ──────────────────────────────────────────────────────────────────────────────

def call_predict(text: str) -> dict:
    """
    POST the text to the FastAPI backend and return the parsed JSON response.

    Raises:
        requests.RequestException: On network / timeout errors.
        ValueError: If the backend returns a non-200 status.
    """
    payload = {"text": text}
    response = requests.post(PREDICT_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)

    if response.status_code != 200:
        detail = response.json().get("detail", response.text)
        raise ValueError(f"Backend error {response.status_code}: {detail}")

    return response.json()


def check_backend_health() -> bool:
    """Return True if the backend health endpoint responds with 200."""
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# UI Layout
# ──────────────────────────────────────────────────────────────────────────────

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔍 Sentiment Analyser")
st.markdown(
    "<p class='sub'>Powered by <strong>Llama 3.1 (Groq API)</strong> "
    "via a FastAPI backend.</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── Backend health indicator ──────────────────────────────────────────────────
with st.expander("🛠 Backend Status", expanded=False):
    if check_backend_health():
        st.success(f"✅ Backend is reachable at `{BACKEND_URL}`")
    else:
        st.error(
            f"❌ Cannot reach backend at `{BACKEND_URL}`. "
            "Make sure the FastAPI server is running on port 8000."
        )

# ── Sample input buttons ──────────────────────────────────────────────────────
st.markdown("**Try a sample input:**")
cols = st.columns(3)
for idx, sample in enumerate(SAMPLE_INPUTS):
    col = cols[idx % 3]
    # Truncate button label for display
    label = sample[:40] + "…" if len(sample) > 40 else sample
    if col.button(label, key=f"sample_{idx}"):
        st.session_state["input_text"] = sample

st.markdown("")  # spacer

# ── Text input ────────────────────────────────────────────────────────────────
user_text: str = st.text_area(
    label="Enter text to analyse",
    value=st.session_state.get("input_text", ""),
    height=140,
    max_chars=5000,
    placeholder="Type or paste text here… e.g. 'I love this!'",
    key="text_area",
)

char_count = len(user_text)
st.caption(f"{char_count} / 5000 characters")

# ── Predict button ────────────────────────────────────────────────────────────
predict_clicked = st.button(
    "🚀 Analyse Sentiment",
    type="primary",
    use_container_width=True,
    disabled=(char_count == 0),
)

# ── Inference & Result ────────────────────────────────────────────────────────
if predict_clicked:
    if not user_text.strip():
        st.warning("⚠️ Please enter some text before analysing.")
    else:
        with st.spinner("Analysing sentiment…"):
            try:
                t0 = time.perf_counter()
                result = call_predict(user_text.strip())
                elapsed = time.perf_counter() - t0

                sentiment: str = result["sentiment"]
                confidence: float = result["confidence"]
                colour = SENTIMENT_COLOURS.get(sentiment, "#95a5a6")
                emoji = SENTIMENT_EMOJIS.get(sentiment, "❓")

                # Result card
                st.markdown(
                    f"""
                    <div class="result-card">
                        <p style="font-size:0.9rem;color:#6c757d;margin-bottom:8px;">
                            Sentiment
                        </p>
                        <span class="badge" style="background:{colour};">
                            {emoji} {sentiment}
                        </span>
                        <p class="conf-label" style="margin-top:20px;">
                            Confidence
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Confidence progress bar (Streamlit native — renders below the card)
                st.progress(confidence, text=f"{confidence * 100:.1f}%")

                st.caption(f"⏱ Inference completed in {elapsed:.2f} s")

            except requests.exceptions.ConnectionError:
                st.error(
                    "🔌 **Connection refused.** The backend does not appear to be running. "
                    f"Start it with `uvicorn app.main:app --port 8000` and try again."
                )
            except requests.exceptions.Timeout:
                st.error(
                    f"⏳ **Request timed out** after {REQUEST_TIMEOUT} s. "
                    "The model may still be loading — please wait a moment and retry."
                )
            except ValueError as exc:
                st.error(f"🚨 **Backend returned an error:** {exc}")
            except Exception as exc:
                st.error(f"💥 **Unexpected error:** {exc}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p class='sub' style='text-align:center;'>"
    "Sentiment Analysis App · FastAPI + Streamlit · Llama 3.1 via Groq"
    "</p>",
    unsafe_allow_html=True,
)
