import json
import time
import sys
import os
import re
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Request, Depends, Security, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import settings
from services.router import router, Intent
from services.search_service import search_service
from services.image_service import image_service
from services.llm_service import llm_service
from services.auth_service import auth_service
from services.session_service import session_service
from services.document_service import document_service

app = FastAPI(
    title="Nexus AI Developer Platform & Gateway",
    description=(
        "Production-grade Multimodal AI Platform & Developer API. "
        "Provides autonomous intent routing, real-time web search grounding, "
        "FLUX/DALL-E image synthesis, and streaming completions."
    ),
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin developer clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = Field(None, description="Optional persistent conversation session ID")
    mode: Optional[str] = Field("auto", description="Execution mode: 'auto', 'chat', 'search', or 'image'")
    model: Optional[str] = Field(None, description="Optional target model identifier")
    stream: Optional[bool] = Field(True, description="Whether to stream via SSE")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="List of uploaded document attachments")

class ExportRequest(BaseModel):
    title: Optional[str] = Field("Nexus AI Document", description="Document title")
    content: str = Field(..., description="Markdown content to export")
    format: Optional[str] = Field("pdf", description="Export format: 'pdf' or 'docx'")

class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Initial conversation title")
    mode: Optional[str] = Field("auto", description="Default mode for session")

class SessionUpdateRequest(BaseModel):
    title: str = Field(..., description="New title for the conversation")

class OpenAICompletionRequest(BaseModel):
    model: Optional[str] = "nexus-omni-1"
    messages: List[ChatMessage]
    mode: Optional[str] = "auto"
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    max_results: Optional[int] = Field(5, description="Maximum number of search results to return (1-10)")

class ImageRequest(BaseModel):
    prompt: str = Field(..., description="Description of the image to generate")
    size: Optional[str] = Field("1024x1024", description="Image resolution (e.g. '1024x1024')")

class RouteRequest(BaseModel):
    text: str = Field(..., description="Prompt or query to analyze and classify")

# -------------------------------------------------------------
# System & Playground Endpoints
# -------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "online",
        "system": "Nexus AI Platform",
        "version": "1.1.0",
        "timestamp": time.time()
    }

@app.get("/api/config", tags=["System"])
async def get_config():
    return {
        "default_model": settings.DEFAULT_MODEL,
        "has_llm_key": settings.has_openai_key,
        "has_search_key": settings.has_tavily_key,
        "search_backend": "Tavily" if settings.has_tavily_key else "DuckDuckGo / DDGS",
        "image_provider": "DALL-E 3" if (settings.IMAGE_PROVIDER == "openai" or (settings.IMAGE_PROVIDER == "auto" and settings.has_openai_key)) else "Pollinations FLUX.1",
        "api_keys_registered": len(settings.valid_api_keys)
    }

# -------------------------------------------------------------
# Conversation Sessions API
# -------------------------------------------------------------
@app.get("/api/sessions", tags=["Sessions"])
async def list_sessions():
    """Returns all saved conversation threads ordered by recent activity."""
    return session_service.list_sessions()

@app.post("/api/sessions", tags=["Sessions"])
async def create_session(request: Optional[SessionCreateRequest] = None):
    """Creates a new conversation session."""
    title = request.title if request else None
    mode = request.mode if request else "auto"
    return session_service.create_session(title=title, mode=mode)

@app.get("/api/sessions/{session_id}", tags=["Sessions"])
async def get_session_history(session_id: str):
    """Retrieves full conversation messages and metadata for a session."""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = session_service.get_session_messages(session_id)
    return {
        "session": session,
        "messages": messages
    }

@app.patch("/api/sessions/{session_id}", tags=["Sessions"])
async def rename_session(session_id: str, request: SessionUpdateRequest):
    """Renames a conversation session title."""
    success = session_service.update_session_title(session_id, request.title)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or title invalid")
    return {"status": "ok", "session_id": session_id, "title": request.title}

@app.delete("/api/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """Deletes a conversation session and all its messages."""
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "ok", "deleted_session_id": session_id}

# -------------------------------------------------------------
# Document Upload & Generation API
# -------------------------------------------------------------
@app.post("/api/upload", tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads and extracts text from documents (.pdf, .docx, .txt, .csv, .md, .py, .json).
    """
    try:
        raw_name = file.filename or "uploaded_file"
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', raw_name)
        file_id = f"doc_{uuid.uuid4().hex[:10]}"
        stored_name = f"{file_id}_{safe_name}"
        dest_path = document_service.upload_dir / stored_name

        contents = await file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)

        parsed = document_service.extract_text(dest_path, safe_name)
        return {
            "file_id": file_id,
            "filename": safe_name,
            "size_bytes": len(contents),
            "extension": dest_path.suffix.lower(),
            "text": parsed["text"],
            "metadata": parsed["metadata"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/download/{filename}", tags=["Documents"])
async def download_document(filename: str):
    """
    Serves generated PDF and Word (.docx) documents for instant download.
    """
    clean_name = os.path.basename(filename)
    target_path = document_service.generated_dir / clean_name
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="Requested document not found.")

    if clean_name.lower().endswith(".pdf"):
        media_type = "application/pdf"
    elif clean_name.lower().endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(target_path),
        filename=clean_name,
        media_type=media_type
    )

@app.post("/api/export", tags=["Documents"])
async def export_document(request: ExportRequest):
    """
    On-demand export of any Markdown content into a downloadable PDF or Word .docx.
    """
    fmt = (request.format or "pdf").lower()
    title = request.title or "Nexus AI Document"
    if fmt in ["word", "docx"]:
        res = document_service.generate_docx(title, request.content)
    else:
        res = document_service.generate_pdf(title, request.content)
    return res

@app.post("/api/chat", tags=["Playground"])
async def playground_chat_endpoint(request: ChatRequest):
    """
    Unified SSE streaming endpoint consumed by the Nexus Web Playground.
    Supports persistent sessions, document ingestion (PDF, Word, Code),
    and autonomous PDF/Word generation.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty.")

    last_user_message = request.messages[-1].content
    raw_history = [{"role": m.role, "content": m.content} for m in request.messages]

    # Resolve or create persistent session
    active_session_id = request.session_id
    current_session = None
    if active_session_id:
        current_session = session_service.get_session(active_session_id)
    if not current_session:
        current_session = session_service.create_session(mode=request.mode or "auto")
        active_session_id = current_session["id"]

    # Persist user message
    session_service.add_message(active_session_id, "user", last_user_message)

    # Ingest attached documents into context
    doc_context = ""
    primary_doc_name = ""
    if request.attachments:
        doc_parts = []
        for att in request.attachments:
            fname = att.get("filename", "Uploaded File")
            if not primary_doc_name:
                primary_doc_name = fname
            ftext = att.get("text", "")
            if ftext:
                doc_parts.append(f"=== ATTACHED DOCUMENT: {fname} ===\n{ftext}")
        if doc_parts:
            doc_context = (
                "You are Nexus AI, equipped with world-class document comprehension capabilities like Claude.\n"
                "The user has provided the attached document. Deep-dive into this document with high intellectual rigor: "
                "provide an executive overview, break down its core structure and sections, extract key findings or qualifications, "
                "and explain everything clearly and thoroughly to the user.\n\n"
                + "\n\n".join(doc_parts)
            )

    async def event_generator():
        # First notify client of the active session
        yield f"event: session\ndata: {json.dumps(current_session)}\n\n"

        # Check for autonomous Document Generation requests (PDF / Word)
        doc_request = document_service.detect_doc_request(last_user_message)
        if doc_request:
            fmt, topic = doc_request
            doc_type_name = "Word Document" if fmt == "docx" else "PDF Document"
            yield f"event: status\ndata: {json.dumps({'message': f'Drafting structured {doc_type_name} on {topic}...' })}\n\n"

            # Use LLM to write a comprehensive, well-structured document body
            prompt_for_doc = [
                {"role": "system", "content": "You are Nexus AI's Document Authoring Engine. Write a well-structured, professional, comprehensive document with clear headings (# and ##), bullet points, and analytical sections based on the user's topic."},
                {"role": "user", "content": f"Write a complete, professional document about: {topic}."}
            ]
            doc_body = await llm_service.complete_chat(prompt_for_doc, search_context=doc_context, model=request.model)

            yield f"event: status\ndata: {json.dumps({'message': f'Compiling and styling {doc_type_name}...' })}\n\n"

            doc_title = f"{topic.title()} - Nexus Document" if topic else "Nexus AI Document"
            if fmt == "docx":
                doc_file = document_service.generate_docx(doc_title, doc_body)
            else:
                doc_file = document_service.generate_pdf(doc_title, doc_body)

            yield f"event: document\ndata: {json.dumps(doc_file)}\n\n"

            # Stream the generated text and provide the download card
            download_card = (
                f"\n\n---\n"
                f"### 📄 Download Your Generated {doc_file['format'].upper()}\n"
                f"**[{doc_file['filename']}]({doc_file['download_url']})** &bull; {round(doc_file['size_bytes']/1024, 1)} KB\n\n"
                f"[⬇️ **Download {doc_file['format'].upper()} Document**]({doc_file['download_url']})\n\n"
                f"*Generated by Nexus AI Document Engine*\n"
            )

            full_reply = doc_body + download_card
            yield f"event: token\ndata: {json.dumps({'token': full_reply})}\n\n"

            # Persist assistant message
            session_service.add_message(active_session_id, "assistant", full_reply, intent="document")

            # Smart title
            new_title = f"{fmt.upper()}: {topic[:20]}"
            session_service.update_session_title(active_session_id, new_title)
            yield f"event: done\ndata: {json.dumps({'status': 'completed', 'session_id': active_session_id, 'title': new_title})}\n\n"
            return

        # Normal routing (Chat / Search / Image)
        intent, target_prompt = router.classify(last_user_message, explicit_mode=request.mode or "auto")
        yield f"event: intent\ndata: {json.dumps({'intent': intent, 'query': target_prompt})}\n\n"

        accumulated_text = ""
        captured_sources = []

        if intent == Intent.IMAGE:
            yield f"event: status\ndata: {json.dumps({'message': 'Synthesizing image with ' + settings.IMAGE_PROVIDER + '...'})}\n\n"
            img_result = await image_service.generate(target_prompt)
            yield f"event: image\ndata: {json.dumps(img_result)}\n\n"
            markdown_token = f"\n\n![{img_result['prompt']}]({img_result['image_url']})\n\n*Generated with {img_result['provider']}*"
            accumulated_text = markdown_token
            yield f"event: token\ndata: {json.dumps({'token': markdown_token})}\n\n"

        elif intent == Intent.SEARCH:
            yield f"event: status\ndata: {json.dumps({'message': 'Browsing live web...'})}\n\n"
            captured_sources = await search_service.search(target_prompt, max_results=5)
            yield f"event: sources\ndata: {json.dumps({'sources': captured_sources})}\n\n"
            search_context = search_service.format_search_context(captured_sources)
            if doc_context:
                search_context = f"{doc_context}\n\n{search_context}"
            yield f"event: status\ndata: {json.dumps({'message': 'Synthesizing verified findings...'})}\n\n"
            async for token in llm_service.stream_chat(raw_history, search_context=search_context, model=request.model):
                accumulated_text += token
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        else:
            if primary_doc_name:
                yield f"event: status\ndata: {json.dumps({'message': f'Analyzing {primary_doc_name}...' })}\n\n"
            else:
                yield f"event: status\ndata: {json.dumps({'message': 'Thinking...'})}\n\n"
            async for token in llm_service.stream_chat(raw_history, search_context=doc_context, model=request.model):
                accumulated_text += token
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        # Persist assistant message to SQLite
        session_service.add_message(
            active_session_id,
            "assistant",
            accumulated_text,
            intent=intent,
            sources=captured_sources
        )

        # Auto-title session if it's the first turn or default title using LLM intelligence
        all_msgs = session_service.get_session_messages(active_session_id)
        current_title = current_session.get("title", "")
        new_title = current_title
        if len(all_msgs) <= 2 or current_title in ["New Conversation", "New Chat", ""]:
            new_title = await session_service.generate_smart_title(last_user_message)
            session_service.update_session_title(active_session_id, new_title)

        yield f"event: done\ndata: {json.dumps({'status': 'completed', 'session_id': active_session_id, 'title': new_title})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -------------------------------------------------------------
# Official Nexus Developer API (/v1)
# -------------------------------------------------------------
@app.post("/v1/chat/completions", tags=["Developer API"])
async def v1_chat_completions(
    request: OpenAICompletionRequest,
    api_key: str = Depends(auth_service.verify_api_key)
):
    """
    Flagship Multimodal Chat Endpoint.
    Autonomous intent routing, web search grounding, and image generation.
    Supports standard JSON responses (stream=False) and SSE chunks (stream=True).
    """
    auth_service.record_usage(api_key, "/v1/chat/completions")
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages array cannot be empty.")

    last_user_message = request.messages[-1].content
    raw_history = [{"role": m.role, "content": m.content} for m in request.messages]
    created_ts = int(time.time())

    # 1. Classify intent
    intent, target_prompt = router.classify(last_user_message, explicit_mode=request.mode or "auto")

    # Map virtual platform models (e.g. nexus-omni-1) to configured engine model
    backend_model = settings.DEFAULT_MODEL if (not request.model or request.model.startswith("nexus-")) else request.model

    # STREAMING MODE
    if request.stream:
        async def sse_stream():
            search_context = ""
            if intent == Intent.IMAGE:
                img_result = await image_service.generate(target_prompt)
                markdown_content = f"![{img_result['prompt']}]({img_result['image_url']})"
                chunk = {
                    "id": f"nexus-{created_ts}",
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": markdown_content, "image": img_result},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
                return

            if intent == Intent.SEARCH:
                results = await search_service.search(target_prompt, max_results=4)
                search_context = search_service.format_search_context(results)

            async for token in llm_service.stream_chat(raw_history, search_context=search_context, model=backend_model):
                chunk = {
                    "id": f"nexus-{created_ts}",
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(sse_stream(), media_type="text/event-stream")

    # NON-STREAMING MODE
    else:
        if intent == Intent.IMAGE:
            img_result = await image_service.generate(target_prompt)
            content = f"![{img_result['prompt']}]({img_result['image_url']})\n\n*Generated by {img_result['provider']}*"
            return {
                "id": f"nexus-{created_ts}",
                "object": "chat.completion",
                "created": created_ts,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop"
                }],
                "nexus_metadata": {
                    "intent": intent,
                    "image": img_result
                }
            }

        search_results = []
        search_context = ""
        if intent == Intent.SEARCH:
            search_results = await search_service.search(target_prompt, max_results=4)
            search_context = search_service.format_search_context(search_results)

        full_content = await llm_service.complete_chat(raw_history, search_context=search_context, model=backend_model)
        return {
            "id": f"nexus-{created_ts}",
            "object": "chat.completion",
            "created": created_ts,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": full_content},
                "finish_reason": "stop"
            }],
            "nexus_metadata": {
                "intent": intent,
                "sources": search_results
            }
        }

@app.post("/v1/search", tags=["Developer API"])
async def v1_search(
    request: SearchRequest,
    api_key: str = Depends(auth_service.verify_api_key)
):
    """
    Dedicated Web Search API. Queries the live web and returns structured sources and snippets.
    """
    auth_service.record_usage(api_key, "/v1/search")
    results = await search_service.search(request.query, max_results=request.max_results or 5)
    return {
        "query": request.query,
        "count": len(results),
        "results": results
    }

@app.post("/v1/images/generations", tags=["Developer API"])
async def v1_image_generation(
    request: ImageRequest,
    api_key: str = Depends(auth_service.verify_api_key)
):
    """
    Dedicated Image Synthesis API. Synthesizes visuals using FLUX or DALL-E 3.
    """
    auth_service.record_usage(api_key, "/v1/images/generations")
    img_result = await image_service.generate(request.prompt, size=request.size or "1024x1024")
    return {
        "created": int(time.time()),
        "data": [{
            "url": img_result["image_url"],
            "revised_prompt": img_result["prompt"]
        }],
        "provider": img_result["provider"]
    }

@app.post("/v1/route", tags=["Developer API"])
async def v1_route(
    request: RouteRequest,
    api_key: str = Depends(auth_service.verify_api_key)
):
    """
    Dedicated Intent Classification API. Classifies queries into CHAT, SEARCH, or IMAGE.
    """
    auth_service.record_usage(api_key, "/v1/route")
    intent, target = router.classify(request.text)
    return {
        "intent": intent,
        "target_prompt": target
    }

@app.get("/v1/models", tags=["Developer API"])
async def v1_models(api_key: str = Depends(auth_service.verify_api_key)):
    """
    Lists virtual model capabilities available in the Nexus AI platform.
    """
    auth_service.record_usage(api_key, "/v1/models")
    return {
        "object": "list",
        "data": [
            {"id": "nexus-omni-1", "object": "model", "owned_by": "nexus", "description": "Autonomous multimodal routing (Chat + Web Grounding + Image)"},
            {"id": "nexus-search-1", "object": "model", "owned_by": "nexus", "description": "Dedicated real-time web search and citation synthesis"},
            {"id": "nexus-flux-1", "object": "model", "owned_by": "nexus", "description": "High-fidelity visual generation engine"},
            {"id": "nexus-router-1", "object": "model", "owned_by": "nexus", "description": "High-speed intent classification engine"}
        ]
    }

@app.get("/v1/usage", tags=["Developer API"])
async def v1_usage(api_key: str = Depends(auth_service.verify_api_key)):
    """
    Returns platform usage metrics, endpoint counters, and uptime.
    """
    return auth_service.get_metrics()

# -------------------------------------------------------------
# Static Web Dashboard Mount
# -------------------------------------------------------------
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
if (static_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("==================================================")
    print("🚀 Nexus AI Developer Platform (Level 1.1) online")
    print(f"👉 Web Playground: http://localhost:{settings.PORT}")
    print(f"👉 API Docs & Swagger: http://localhost:{settings.PORT}/docs")
    print(f"🔑 Default Dev API Key: nexus_dev_master_key")
    print("==================================================")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
