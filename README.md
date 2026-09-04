<div align="center">

# 🌐 Nexus AI
### Autonomous Multimodal Intelligence Platform & Developer Gateway

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Groq & OpenAI](https://img.shields.io/badge/Providers-Groq%20%7C%20OpenAI%20%7C%20OpenRouter-F55036?style=for-the-badge)](https://groq.com)
[![SQLite Memory](https://img.shields.io/badge/Memory-SQLite%20Persistent-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

<p align="center">
  <b>Unified LLM Reasoning • Real-Time Web Grounding • FLUX.1 Visual Synthesis • Document Ingestion (PDF/Word) • Autonomous PDF & Word (.docx) Authoring • Claude-Inspired Workspace</b>
</p>

[Explore Workspace](#-interactive-web-workspace) • [Key Capabilities](#-key-capabilities) • [Quick Start](#-quick-start) • [Python SDK](#-python-sdk) • [Developer API](#-developer-api-reference) • [Architecture](#-architecture)

</div>

---

## 🌟 What is Nexus AI?

**Nexus AI** is an autonomous AI engine and developer gateway built from scratch to challenge monolithic AI platforms. Instead of requiring users to manually select modes with buttons or switch tools, Nexus AI **autonomously routes intents in real-time** between:

1. 🧠 **Deep Reasoning** (Groq / Qwen / Llama / OpenAI)
2. 🔍 **Real-Time Live Web Search** (Tavily + DuckDuckGo fallback with source citations)
3. 🎨 **Visual Art Synthesis** (FLUX.1 Schnell & DALL-E 3)
4. 📄 **Document Intelligence & Authoring** (Local parsing of PDF/Word and on-demand `.docx`/`.pdf` generation)

All wrapped inside a minimalist, distraction-free **Claude-inspired aesthetic** with persistent multi-session SQLite memory.

---

## 🚀 Key Capabilities

| Feature | Description | Engine / Provider |
| :--- | :--- | :--- |
| **Autonomous Routing** | Zero manual mode buttons; dynamically detects if prompt requires chat, search, or image synthesis. | `services/router.py` |
| **Live Web Grounding** | Real-time web research with multi-source verified citations (`[1]`, `[2]`). | Tavily API + DuckDuckGo |
| **Visual Synthesis** | Generates photorealistic and concept art directly inline in chat. | Pollinations FLUX.1 / DALL-E 3 |
| **Document Ingestion** | Drag-and-drop `.pdf`, `.docx`, `.txt`, `.py`, `.csv`, `.json` for immediate deep-dive analysis. | `pypdf`, `python-docx` |
| **PDF & Word Authoring** | Generates styled, downloadable **`.docx`** and **`.pdf`** documents on demand. | `reportlab`, `python-docx` |
| **Persistent Memory** | Full multi-session history, intelligent LLM auto-naming, and time-aware dynamic greetings. | SQLite (`nexus_ai.db`) |
| **Developer API** | Drop-in OpenAI `/v1/chat/completions`, usage telemetry, and API key authentication. | FastAPI + SSE Streaming |
| **Native Python SDK** | First-party client for programmatic interaction in Python applications. | `nexus_sdk/client.py` |

---

## 🎨 Interactive Web Workspace

Nexus AI ships with a production-grade web dashboard served locally at `http://localhost:8000`:

* **Claude-Inspired Styling:** Warm terracotta accents (`#da7756`), dark charcoal background (`#1a1917`), and clean typography.
* **Dynamic Welcome:** Welcomes you with contextual phrases (*"Good evening — Time for some coffee and coding?"*).
* **Paperclip & Global Drag-Drop:** Drag any file directly from your PC into the chat window to begin an instant deep-dive.
* **Dynamic Status Phrases:** Smooth, box-free natural status words (*"Browsing the web..."*, *"Drafting Word document..."*) during generation.

---

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/24pwai0015-max/nexus-ai.git
cd nexus-ai
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment
Copy the configuration template:
```bash
cp .env.example .env
```

Edit `.env` with your API key:
```ini
# Groq key (auto-detected with ultra-fast inference) or OpenAI key
OPENAI_API_KEY=gsk_your_groq_or_openai_key_here
DEFAULT_MODEL=qwen/qwen3.8-27b

# Real-Time Web Grounding (Optional - DuckDuckGo fallback is active by default)
TAVILY_API_KEY=

# Image Generation ('pollinations' for free FLUX.1 or 'openai' for DALL-E 3)
IMAGE_PROVIDER=pollinations
```

### 4. Run the Verification Suite
```bash
python test_gateway.py
python test_sessions.py
python test_documents.py
python test_api_platform.py
```

### 5. Launch the Platform
```bash
python main.py
```

Open your browser:
* 🖥️ **Web Workspace:** [http://localhost:8000](http://localhost:8000)
* 📖 **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🐍 Python SDK

Nexus AI includes an official, native Python SDK located in `nexus_sdk/`:

```python
from nexus_sdk import NexusClient

client = NexusClient(
    base_url="http://localhost:8000",
    api_key="nexus_dev_master_key"
)

# 1. Autonomous Chat (Auto-routing between chat, search, or image)
response = client.chat(
    messages=[{"role": "user", "content": "Explain how Transformer attention works"}],
    stream=False
)
print(response.content)

# 2. Live Web Grounded Search
results = client.search("Latest clean energy breakthroughs in 2026", max_results=3)
for r in results:
    print(f"[{r.title}]: {r.url}")

# 3. Direct Image Generation (FLUX.1)
img = client.generate_image("A futuristic server room floating in deep space, 8k cinematic")
print("Image URL:", img.image_url)
```

---

## 🔌 Developer API Reference

### 1. OpenAI Drop-In Streaming (`POST /v1/chat/completions`)
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer nexus_dev_master_key" \
  -d '{
    "model": "nexus-omni-1",
    "messages": [{"role": "user", "content": "Search the latest news on fusion reactors"}],
    "stream": true
  }'
```

### 2. Document Upload (`POST /api/upload`)
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/research.pdf"
```

### 3. On-Demand Document Export (`POST /api/export`)
```bash
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Quantum Physics Summary",
    "content": "# Executive Summary\nQuantum computing utilizes qubits...",
    "format": "docx"
  }'
```

---

## 📁 Architecture

```
nexus ai/
├── config.py                 # Provider auto-detection & settings
├── main.py                   # FastAPI core, SSE engine & REST routes
├── requirements.txt          # Production dependencies
├── .env.example              # Configuration template
├── .gitignore                # Security & data exclusions
├── services/
│   ├── router.py             # Autonomous intent classification (Zero latency)
│   ├── llm_service.py        # LLM streaming client (Groq, OpenAI, OpenRouter)
│   ├── search_service.py     # Tavily + DuckDuckGo live grounding engine
│   ├── image_service.py      # FLUX.1 Schnell & DALL-E 3 synthesis
│   ├── session_service.py    # Persistent SQLite conversation manager
│   ├── document_service.py   # PDF/Word text extractor & document compiler
│   └── auth_service.py       # API key authentication & usage telemetry
├── static/
│   └── index.html            # Claude-style workspace (Tailwind + Lucide)
├── nexus_sdk/
│   └── client.py             # Official Nexus AI Python SDK
├── examples/
│   └── sdk_demo.py           # SDK demonstration walkthrough
└── tests/
    ├── test_gateway.py       # Gateway & router tests
    ├── test_sessions.py      # SQLite memory & smart title tests
    ├── test_documents.py     # Ingestion & PDF/Word generation tests
    └── test_api_platform.py  # Developer API endpoint verification
```

---

## 🛡️ Security & Privacy

* **Local Document Parsing:** All uploaded PDFs, Word docs, and code files are processed locally on your host.
* **Isolated Environment:** Secrets and persistent SQLite databases are strictly excluded from version control via `.gitignore`.
* **API Key Guards:** Endpoints under `/v1` are protected by bearer token authentication.

---

## 📄 License

This project is licensed under the **MIT License**.
Distributed freely for developers building autonomous multimodal agent systems.
