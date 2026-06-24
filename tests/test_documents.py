from services.document_service import DocumentService
import pytest
from fastapi import FastAPI
from api.routes.documents import router
from fastapi.testclient import TestClient
import json

class TestDocumentService:

    def test_upload_and_list(self, monkeypatch, tmp_path):
        data_dir = tmp_path / "data"
        monkeypatch.setattr("services.document_service.UPLOAD_DIR", data_dir / "uploads")
        monkeypatch.setattr("services.document_service.REGISTRY_PATH", data_dir / "documents.json")
        monkeypatch.setattr("services.document_service.CHROMA_PATH", str(data_dir / "chroma"))

        service = DocumentService()
        result = service.upload(b"hello world", "text.txt")

        assert result.filename == "text.txt"
        assert result.chunk_count == 1

        docs = service.list_documents()
        assert len(docs) == 1
        assert docs[0].filename == "text.txt"

    def test_upload_and_delete(self, monkeypatch, tmp_path):
        data_dir = tmp_path / "data"
        monkeypatch.setattr("services.document_service.UPLOAD_DIR", data_dir / "uploads")
        monkeypatch.setattr("services.document_service.REGISTRY_PATH", data_dir / "documents.json")
        monkeypatch.setattr("services.document_service.CHROMA_PATH", str(data_dir / "chroma"))

        service = DocumentService()
        result = service.upload(b"content", "del.txt")

        deleted = service.delete_by_id(result.id)
        
        assert deleted is not None
        assert deleted.filename == "del.txt"

        assert service.list_documents() == []

    def test_delete_nonexistent(self):
        result = DocumentService().delete_by_id("nonexistent")
        assert result is None

    def test_upload_dedup(self, monkeypatch, tmp_path):
        data_dir = tmp_path / "data"
        monkeypatch.setattr("services.document_service.UPLOAD_DIR", data_dir / "uploads")
        monkeypatch.setattr("services.document_service.REGISTRY_PATH", data_dir / "documents.json")
        monkeypatch.setattr("services.document_service.CHROMA_PATH", str(data_dir / "chroma"))

        service = DocumentService()
        service.upload(b"first", "same.txt")
        service.upload(b"second", "same.txt")

        assert len(service.list_documents()) == 1

class TestDocumentAPI:
    @pytest.fixture
    def client(self, monkeypatch, tmp_path):
        data_dir = tmp_path / "data"
        monkeypatch.setattr("services.document_service.UPLOAD_DIR", data_dir / "uploads")
        monkeypatch.setattr("services.document_service.REGISTRY_PATH", data_dir / "documents.json")
        monkeypatch.setattr("services.document_service.CHROMA_PATH", str(data_dir / "chroma"))

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_upload_txt(self, client):
        resp = client.post("/upload", files={"file": ("test.txt", b"hello", "text/plain")})
        assert resp.status_code == 200
        assert resp.json()["filename"] == "test.txt"

    def test_upload_invalib_format(self, client):
        resp = client.post("/upload", files={"file": ("test.exe", b"data", "application/octet-stream")})
        assert resp.status_code == 400

    def test_upload_pdf(self, client):
        from io import BytesIO
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(612, 792)
        buf = BytesIO()
        writer.write(buf)
        resp = client.post("/upload", files={"file": ("test.pdf", buf.getvalue(), "application/pdf")})
        assert resp.status_code == 200

    def test_list_empty(self, client):
        assert client.get("/documents").json() == []

    def test_list_after_uploads(self, client):
        client.post("/upload", files={"file": ("a.txt", b"aaa")})
        client.post("/upload", files={"file": ("b.txt", b"bbb")})
        assert len(client.get("/documents").json()) == 2

    def test_delete_nonexistent(self, client):
        assert client.delete("/documents/no-such-id").status_code == 404