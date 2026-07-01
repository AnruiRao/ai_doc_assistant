from dataclasses import dataclass
from pathlib import Path
import structlog
import json

from uuid import uuid4
from retrieval.vector_store import VectorStore
from ingestion import load_document, clean_text, Chunker, tag_gov_sections
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)

UPLOAD_DIR = Path("data/uploads")
REGISTRY_PATH = Path("data/documents.json")
CHROMA_PATH = "data/chroma"

@dataclass
class DocumentRecord:
    id: str
    filename: str
    path: str
    chunk_ids: list[str]
    chunk_count: int
    uploaded_at: str

@dataclass
class UploadResult:
    id: str
    filename: str
    chunk_count: int

class DocumentService:
    def upload(
            self,
            content: bytes,
            filename: str,
            chunk_size: int = 500,
            chunk_overlap: int =50
    ) -> UploadResult:
        record = self._find_by_filename(filename=filename)
        if record:
            self._delete_by_record(record=record)

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        doc_id = str(uuid4())
        safe_name = f"{doc_id}_{filename}"
        save_path = UPLOAD_DIR / safe_name
        save_path.write_bytes(content)

        text = load_document(str(save_path))
        text = clean_text(text)
        text = tag_gov_sections(text)
        chunks = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap).recursive_split(text, chunk_size=chunk_size)
        chunk_ids = [str(uuid4()) for _ in chunks]
        metadatas = [{"source": str(save_path), "chunk_index": i} for i in range(len(chunks))]

        if not chunks:
            return UploadResult(id=doc_id, filename=filename, chunk_count=0)

        VectorStore(collection_name="documents", persist_directory=CHROMA_PATH).add_documents(chunks,chunk_ids,metadatas)
        
        registry = self._load_registry()
        registry.append({
            "id": doc_id,
            "filename": filename,
            "path": str(save_path),
            "chunk_ids": chunk_ids,
            "chunk_count": len(chunks),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        })
        self._save_registry(registry)

        logger.info("document_uploaded", doc_id=doc_id, filename=filename, chunk_count=len(chunks))
        return UploadResult(
            id=doc_id,
            filename=filename,
            chunk_count=len(chunks)
        )
    
    def list_documents(self) -> list[DocumentRecord]:
        return [DocumentRecord(**r) for r in self._load_registry()]
    
    def delete_by_id(self, doc_id: str) -> DocumentRecord | None:
        doc = next(
            (DocumentRecord(**r) for r in self._load_registry() if r["id"] == doc_id),
            None
        )
        if doc is None:
            return None
        self._delete_by_record(doc)
        return doc

    def delete_all(self) -> int:
        """删除所有文档（文件 + Chroma + 注册表），返回删除数量。"""
        registry = self._load_registry()
        count = len(registry)

        for r in registry:
            file_path = Path(r["path"])
            if file_path.exists():
                file_path.unlink()

        vs = VectorStore(collection_name="documents", persist_directory=CHROMA_PATH)
        try:
            vs.delete_collection()
        except Exception:
            pass

        REGISTRY_PATH.write_text("[]", encoding="utf-8")
        logger.info("all_documents_deleted", count=count)
        return count

    def delete_by_source(self, source_path: str | Path) -> bool:
        doc = next(
            (DocumentRecord(**r) for r in self._load_registry() if r["path"] == str(source_path)),
            None
        )
        if doc is None:
            return False
        self._delete_by_record(doc)
        return True

    @staticmethod
    def _load_registry() -> list[dict]:
        if not REGISTRY_PATH.exists():
            return []
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    
    @staticmethod
    def _save_registry(registry: list[dict]):
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY_PATH.write_text(json.dumps(registry,ensure_ascii=False,indent=2), encoding="utf-8")

    def _find_by_filename(self, filename: str) -> DocumentRecord | None:
        for r in self._load_registry():
            if r["filename"] == filename:
                return DocumentRecord(**r)
        return None
    
    def _delete_by_record(self, record: DocumentRecord):
        source = record.path
        VectorStore(collection_name="documents", persist_directory=CHROMA_PATH).delete_by_metadata({"source": source})
        file_path = Path(source)
        if file_path.exists():
            file_path.unlink()
        docs = [doc for doc in self._load_registry() if doc["path"] != source]
        self._save_registry(docs)
        logger.info("document_deleted", doc_id=record.id, filename=record.filename)
