# 🌐 Nexus AI - Autonomous Multimodal Intelligence Platform

**Nexus AI** is a production-grade AI engine and developer platform combining **Autonomous Intent Routing**, **Real-Time Web Grounding**, **Visual Synthesis**, **Persistent Multi-Session Memory**, and **Document Ingestion & Generation (PDF & Word)** with a clean, Claude-inspired interface.

---

## ✨ Key Capabilities

### 1. 🧠 Autonomous Dynamic Mode Routing
* **Zero Manual Buttons:** Intelligently switches between **Deep Reasoning**, **Live Web Research**, and **Visual Art Synthesis** dynamically based on your prompt.
* **Real-Time Web Grounding:** Live browsing via Tavily with instant DuckDuckGo zero-cost fallback for verified source citations.
* **FLUX.1 & DALL-E Image Synthesis:** Generates high-resolution visuals directly inline.

### 2. 🗄️ Persistent SQLite Memory Engine
* **Multi-Session Conversations:** Full chat threads persisted locally in SQLite (`nexus_ai.db`).
* **Intelligent Auto-Naming:** Generates concise, 2-4 word conceptual titles using LLM intelligence (*"Casual Greeting"*, *"Quantum Cryptography"*).
* **Fresh Start on Entry:** Welcomes you with dynamic greetings (*"Good evening — Time for some coffee and coding?"*), keeping previous conversations organized in the collapsible sidebar.

### 3. 📎 Document Ingestion & Deep Dive (Claude-Style)
* **Local Parsing Engine:** Drag-and-drop or attach `.pdf`, `.docx`, `.txt`, `.py`, `.csv`, `.json`, and `.md` files.
* **Instant Analysis Without Prompt:** Drop a document (like a CV or research paper) and press Send without typing — Nexus AI automatically deep-dives into structure, key findings, and executive insights.

### 4. 📄 Autonomous Document Authoring (PDF & Word on Demand)
* **On-Demand Generation:** Ask Nexus AI to *"Generate a Word document on..."* or *"Create a PDF report about..."*.
* **Styled Compilations:** Generates styled **`.docx`** files (via `python-docx`) and **`.pdf`** files (via `reportlab`) with structured headings, tables, and download cards right in the chat.

### 5. 🔌 Developer Platform & SDK
* **OpenAI Drop-In Compatibility:** Fully compatible `/v1/chat/completions` endpoint for plug-and-play integration with LangChain, LlamaIndex, or OpenAI clients.
* **Native Python SDK:** First-party client (`nexus_sdk`) with support for chat, streaming, web search, image generation, and intent routing.
* **Authentication & Analytics:** API key security and `/v1/usage` telemetry.

---

## 📁 Repository Architecture

```
nexus ai/
├── config.py                 # Configuration & provider auto-routing
├── main.py                   # FastAPI application, SSE streaming & REST endpoints
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── .gitignore                # Security exclusions (keys, database, uploads)
├── nexus_ai.db               # Local SQLite database (gitignored)
├── services/
│   ├── router.py             # Autonomous intent classifier
│   ├── llm_service.py        # LLM client (OpenAI, Groq, OpenRouter)
│   ├── search_service.py     # Tavily & DuckDuckGo live grounding
│   ├── image_service.py      # FLUX.1 & DALL-E 3 image generation
│   ├── session_service.py    # Persistent SQLite session manager
│   ├── document_service.py   # PDF/Word parser & styled document generator
│   └── auth_service.py       # API key authentication & usage tracking
├── static/
│   └── index.html            # Claude-inspired web workspace
├── nexus_sdk/
│   └── client.py             # Official Nexus AI Python SDK
├── examples/
│   └── sdk_demo.py           # SDK integration walkthrough
└── tests/
    ├── test_gateway.py       # Gateway & router tests
    ├── test_api_platform.py  # Developer API & auth tests
    ├── test_sessions.py      # SQLite session & titling tests
    └── test_documents.py     # Document ingestion & PDF/Word generation tests
```

---

## ⚡ Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/<your-username>/nexus-ai.git
cd nexus-ai
pip install -r requirements.txt
```

### 2. Configure Keys
Copy the example configuration:
```bash
cp .env.example .env
```
Add your Groq or OpenAI key in `.env`:
```ini
OPENAI_API_KEY=gsk_your_key_here
DEFAULT_MODEL=qwen/qwen3.8-27b
```

### 3. Run Verification Tests
```bash
python test_gateway.py
python test_sessions.py
python test_documents.py
python test_api_platform.py
```

### 4. Launch Nexus AI
```bash
python main.py
```
Open your browser at:
👉 **`http://localhost:8000`** (Interactive Workspace)
👉 **`http://localhost:8000/docs`** (Swagger API Documentation)

---

## 📄 License
MIT License. Built for autonomous multimodal intelligence.
