# 🔍 Sentiment Classifier

A full-stack AI-powered sentiment analysis web app that classifies any text as **Positive**, **Negative**, or **Neutral** — deployed live on AWS EC2.

---

## 🌐 Live Demo

| Service | URL |
|---|---|
| **Frontend (Streamlit)** | http://3.111.36.4:8501 |
| **Backend (FastAPI)** | http://3.111.36.4:8000 |
| **API Docs (Swagger)** | http://3.111.36.4:8000/docs |

---

## 🧠 What Does This App Do?

You type any sentence → the app tells you the **emotional tone** of that text.

**Examples:**
```
"I love this product!"          → Positive  (99% confidence)
"This is the worst experience." → Negative  (98% confidence)
"The package arrived on time."  → Neutral   (80% confidence)
```

This is called **Sentiment Analysis** — a Natural Language Processing (NLP) task widely used in:
- Product review analysis
- Customer feedback systems
- Social media monitoring
- Chatbot emotion detection

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Browser)                        │
│                   http://3.111.36.4:8501                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ Opens web app
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            AWS EC2 - t3.micro (Mumbai - ap-south-1)          │
│                    Public IP: 3.111.36.4                     │
│                                                             │
│  ┌──────────────────────────┐  ┌──────────────────────────┐ │
│  │  FRONTEND  (Port 8501)   │  │   BACKEND  (Port 8000)   │ │
│  │  Streamlit               │  │   FastAPI + Uvicorn      │ │
│  │  - Text input box        │─►│   - /predict endpoint    │ │
│  │  - Sample buttons        │  │   - /health endpoint     │ │
│  │  - Result badge          │  │   - Input validation     │ │
│  │  - Confidence bar        │  │   - Error handling       │ │
│  └──────────────────────────┘  └────────────┬─────────────┘ │
└───────────────────────────────────────────── │ ─────────────┘
                                               │ HTTPS API call
                                               ▼
                          ┌────────────────────────────────────┐
                          │          GROQ API (Free)            │
                          │       api.groq.com                  │
                          │   Model: llama-3.1-8b-instant       │
                          │   (Meta's Llama 3.1 - 8B params)    │
                          │                                     │
                          │   Input : "I love this product!"    │
                          │   Output: {"sentiment": "Positive", │
                          │            "confidence": 0.99}      │
                          └────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | [Streamlit](https://streamlit.io) | Python-based web UI framework |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com) | High-performance REST API framework |
| **Server** | [Uvicorn](https://www.uvicorn.org) | ASGI server that runs FastAPI |
| **AI Model** | [Llama 3.1 8B](https://groq.com) via Groq | Large Language Model for classification |
| **Deployment** | [AWS EC2](https://aws.amazon.com/ec2) | Cloud virtual server (free tier) |
| **Process Manager** | systemd | Keeps services running 24/7 |
| **Infrastructure** | boto3 (AWS SDK) | Automates EC2 setup via Python |

---

## 📁 Project Structure

```
sentiment-classifier/
│
├── BE/                         ← Backend (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             ← FastAPI app, routes (/predict, /health)
│   │   ├── model.py            ← Groq API call + sentiment parsing
│   │   ├── schemas.py          ← Pydantic request/response models
│   │   └── utils.py            ← Logger utility
│   ├── requirements.txt        ← Python dependencies
│   ├── Dockerfile              ← Docker config (optional)
│   └── .env                    ← API keys (NOT in git)
│
├── FE/                         ← Frontend (Streamlit)
│   ├── app.py                  ← Streamlit UI
│   └── requirements.txt
│
├── deploy/                     ← Deployment scripts
│   ├── deploy_ec2.py           ← Provisions EC2 instance on AWS
│   └── setup_instance.py       ← Copies code + installs on EC2
│
├── .gitignore                  ← Excludes .env, .pem, secrets
└── README.md                   ← This file
```

---

## ☁️ AWS Infrastructure (For Beginners)

### What is AWS EC2?
EC2 (Elastic Compute Cloud) is like **renting a computer** from Amazon. Instead of buying a physical server, you get a virtual machine running in Amazon's data center. Our instance is in **Mumbai, India (ap-south-1)**.

### What resources are running?

| Resource | Name/ID | What it does |
|---|---|---|
| **EC2 Instance** | `i-04352b7d3e81bd049` | The virtual server running our app |
| **Instance Type** | `t3.micro` | Size of the server (2 CPU, 1GB RAM) — free tier |
| **Region** | `ap-south-1` (Mumbai) | Physical location of the server |
| **Security Group** | `classifier-sg` | Firewall rules — opens ports 22, 8000, 8501 |
| **Key Pair** | `classifier-key.pem` | SSH private key to access the server |
| **IAM User** | `classifier-deploy` | AWS sub-account with EC2 permissions |

### What are Ports?
Think of a port like a **door number** on a building. The server has many doors:

```
Server IP: 3.111.36.4
    ├── :22    → SSH door   (for developers to manage the server)
    ├── :8000  → API door   (FastAPI backend)
    └── :8501  → Web door   (Streamlit frontend — users go here)
```

### What is IAM?
IAM (Identity and Access Management) is AWS's **permission system**. Instead of using the root admin account for everything, we create a sub-user (`classifier-deploy`) with only the permissions it needs (EC2 access). This is safer — if the key leaks, damage is limited.

### What is a Security Group?
A Security Group is a **virtual firewall**. By default, ALL ports are blocked. We explicitly opened only 3 ports:
- **Port 22** — so we can SSH in to manage the server
- **Port 8000** — so the frontend can talk to the backend
- **Port 8501** — so users can access the Streamlit app

### What is systemd?
systemd is Linux's **service manager**. It ensures our apps:
- ✅ Start automatically when the server reboots
- ✅ Restart automatically if they crash
- ✅ Run in the background (not tied to a terminal session)

```bash
# Check service status
sudo systemctl status classifier-be
sudo systemctl status classifier-fe

# View logs
sudo journalctl -u classifier-be -f
sudo journalctl -u classifier-fe -f
```

---

## 🚀 How a Request Flows (Step by Step)

```
Step 1: User opens http://3.111.36.4:8501 in their browser
Step 2: Streamlit renders the UI — text box, buttons, etc.
Step 3: User types "I love this!" and clicks Analyse Sentiment
Step 4: Streamlit sends HTTP POST to http://localhost:8000/predict
         Body: {"text": "I love this!"}
Step 5: FastAPI validates the request (text length, not empty, etc.)
Step 6: model.py sends HTTPS POST to api.groq.com with:
         - System prompt: "You are a sentiment classifier. Return JSON only."
         - User message: "Text: I love this!"
Step 7: Groq's Llama 3.1 model processes the text and returns:
         {"sentiment": "Positive", "confidence": 0.99}
Step 8: FastAPI sends this JSON back to Streamlit
Step 9: Streamlit displays green badge "😊 Positive" + 99% progress bar
```

---

## 🔧 Run Locally

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repo
```bash
git clone https://github.com/rahul0510/sentiment-classifier.git
cd sentiment-classifier
```

### 2. Set up Backend
```bash
cd BE
pip install -r requirements.txt
```

Create a `.env` file in the `BE/` folder:
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Start the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Set up Frontend
Open a new terminal:
```bash
cd FE
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### 4. Open the app
Visit 👉 http://localhost:8501

---

## 📡 API Reference

### `POST /predict`
Classify the sentiment of a text.

**Request:**
```json
{
  "text": "I absolutely love this product!"
}
```

**Response:**
```json
{
  "sentiment": "Positive",
  "confidence": 0.99
}
```

### `GET /health`
Check if the backend is running.

**Response:**
```json
{
  "status": "ok",
  "backend": "Groq API",
  "model": "llama-3.1-8b-instant"
}
```

---

## 🔐 Security Notes

- `.env` files (containing API keys) are in `.gitignore` — never committed
- `.pem` files (SSH private keys) are in `.gitignore` — never committed
- IAM user `classifier-deploy` has minimal permissions (EC2 only)
- Security group only opens the 3 required ports

---

## 💰 Cost

| Resource | Free Tier | Our Usage | Cost |
|---|---|---|---|
| EC2 t3.micro | 750 hrs/month | ~744 hrs/month | **$0** |
| EBS Storage | 30 GB/month | ~8 GB | **$0** |
| Groq API | 14,400 req/day | Low | **$0** |
| **Total** | | | **$0/month** |

> Free tier lasts **12 months** from AWS account creation date.

---

## 🔄 Redeploy After Code Changes

If you change the code locally and want to push to EC2:

```bash
# From the project root
python deploy/setup_instance.py
```

This will SCP updated files to EC2 and restart the services automatically.

---

## 📌 Journey / Why We Made These Choices

| Attempt | Problem | Solution |
|---|---|---|
| Local RoBERTa model | Too large (~500MB), RAM issues | Use hosted API instead |
| AWS Bedrock (Claude Haiku) | Requires payment instrument | Use free alternative |
| HuggingFace Inference API | Subdomain blocked by network DNS | Use Groq API |
| **Groq API (Llama 3.1)** | ✅ Works perfectly | **Final choice** |

---

## 👨‍💻 Author

Built as a personal research project to learn:
- FastAPI backend development
- Streamlit frontend development  
- AWS EC2 deployment
- LLM-based NLP classification
- Infrastructure automation with boto3
