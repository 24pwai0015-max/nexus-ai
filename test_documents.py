import sys
import io
from fastapi.testclient import TestClient
from main import app
from services.document_service import document_service

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_document_tests():
    print("==================================================")
    print("🧪 Testing Nexus AI Document Processing & Generation")
    print("==================================================")

    client = TestClient(app)

    # 1. Test Intent Detection for Documents
    print("\n[1] Testing Document Intent Detection...")
    prompts = [
        ("generate a word document about machine learning architectures", "docx"),
        ("create a pdf report on global renewable energy in 2026", "pdf"),
        ("write a docx file for project requirements", "docx"),
        ("export this as a pdf", "pdf"),
    ]
    for p, expected_fmt in prompts:
        det = document_service.detect_doc_request(p)
        assert det is not None, f"Failed to detect document request in '{p}'"
        fmt, topic = det
        assert fmt == expected_fmt
        print(f"  [PASS] '{p[:40]}...' -> Format: {fmt.upper()}, Topic: '{topic}'")

    # 2. Test PDF Generation
    print("\n[2] Testing PDF Generation (ReportLab)...")
    sample_md = """# Executive Briefing
This is a confidential summary of our **autonomous agent infrastructure**.

## Key Milestones
- High-speed multimodal routing
- Local SQLite conversation memory
- On-demand PDF and Word document synthesis

### Financial Impact
Projected efficiency gain is **35%** across all engineering workflows.
"""
    pdf_res = document_service.generate_pdf("Autonomous Architecture Brief", sample_md)
    print(f"  [PASS] Generated PDF: {pdf_res['filename']} ({pdf_res['size_bytes']} bytes)")
    assert pdf_res["size_bytes"] > 500

    # 3. Test Word DOCX Generation
    print("\n[3] Testing Word Document (.docx) Generation...")
    docx_res = document_service.generate_docx("Autonomous Architecture Brief", sample_md)
    print(f"  [PASS] Generated DOCX: {docx_res['filename']} ({docx_res['size_bytes']} bytes)")
    assert docx_res["size_bytes"] > 1000

    # 4. Test File Upload Endpoint (/api/upload)
    print("\n[4] Testing /api/upload with text file...")
    file_content = b"Nexus AI is an autonomous multimodal gateway providing LLM reasoning and real-time grounding."
    file_obj = io.BytesIO(file_content)
    r = client.post("/api/upload", files={"file": ("project_notes.txt", file_obj, "text/plain")})
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "project_notes.txt"
    assert "Nexus AI" in data["text"]
    print(f"  [PASS] Uploaded & parsed file ID: {data['file_id']} ({data['size_bytes']} bytes)")

    # 5. Test File Download Endpoint (/api/download/{filename})
    print("\n[5] Testing /api/download endpoint...")
    r_dl_pdf = client.get(f"/api/download/{pdf_res['filename']}")
    assert r_dl_pdf.status_code == 200
    assert r_dl_pdf.headers["content-type"] == "application/pdf"
    print(f"  [PASS] Successfully downloaded generated PDF ({len(r_dl_pdf.content)} bytes)")

    r_dl_docx = client.get(f"/api/download/{docx_res['filename']}")
    assert r_dl_docx.status_code == 200
    assert "wordprocessingml" in r_dl_docx.headers["content-type"]
    print(f"  [PASS] Successfully downloaded generated DOCX ({len(r_dl_docx.content)} bytes)")

    # 6. Test On-Demand Export Endpoint (/api/export)
    print("\n[6] Testing /api/export endpoint...")
    export_payload = {
        "title": "Quantum Physics Summary",
        "content": "## Superposition and Entanglement\nQuantum states exist in linear combinations.",
        "format": "docx"
    }
    r_exp = client.post("/api/export", json=export_payload)
    assert r_exp.status_code == 200
    exp_data = r_exp.json()
    assert exp_data["format"] == "docx"
    assert "download_url" in exp_data
    print(f"  [PASS] /api/export generated: {exp_data['filename']} -> {exp_data['download_url']}")

    print("\n==================================================")
    print("🎉 All Document Ingestion & Generation Tests Passed!")
    print("==================================================")

if __name__ == "__main__":
    run_document_tests()
