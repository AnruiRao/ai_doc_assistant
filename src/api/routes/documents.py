from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.schemas.documents import UploadResponse, DocumentItem, DeleteResponse
from pathlib import Path
from ingestion.loader import load_document
from ingestion.cleaner import clean_text
from ingestion.chunker import Chunker
from uuid import uuid4
from retrieval.vector_store import VectorStore
from core.async_utils import run_in_thread
from datetime import datetime, timezone
import json

router = APIRouter()
UPLOAD_DIR = Path("data/uploads")
REGISTRY_PATH = Path("data/documents.json")

@router.post("/upload",response_model=UploadResponse)
async def upload(
        file: UploadFile = File(...),
        chunk_size: int = Form(500),
        chunk_overlap: int = Form(50)
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".txt", ".pdf"):
        raise HTTPException(status_code=400, detail="仅支持传入.txt与.pdf文件")
    
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    doc_id = str(uuid4())
    safe_name = f"{doc_id}_{file.filename}"
    save_path = UPLOAD_DIR / safe_name
    content = await file.read()
    save_path.write_bytes(content)

    result = await run_in_thread(
        _process_and_register,
        str(save_path),
        file.filename,
        doc_id,
        chunk_size,
        chunk_overlap,
    )

    return UploadResponse(
        id=doc_id,
        filename=file.filename,
        chunk_count=result["chunk_count"],
        message=f"文档 {file.filename} 已入库，共 {result['chunk_count']} 个片段",
    )

@router.get("/documents", response_model=list[DocumentItem])
async def documents():
    registry = _load_registry()
    docs = []
    for r in registry:
       docs.append(
            DocumentItem(
                id=r["id"],
                filename=r["filename"],
                chunk_count=r["chunk_count"],
                uploaded_at=r["uploaded_at"]
            )
        )
    return docs
   
@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str):
    registry = _load_registry()
    doc = None
    for r in registry:
        if r["id"] == doc_id:
            doc = r
            break
    if doc is None:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    VectorStore(collection_name="documents").delete_by_metadata({"source": doc["path"]})

    file_path = Path(doc["path"])
    if file_path.exists():
        file_path.unlink()

    
    registry = [r for r in registry if r["id"] != doc_id]
    _save_registry(registry)

    return DeleteResponse(
        message=f"文档 {doc['filename']} 已删除",
        chunk_count=doc["chunk_count"],
    )

def _load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

def _save_registry(registry: list[dict]):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def _process_and_register(
        path,
        filename,
        doc_id,
        chunk_size,
        chunk_overlap
):
    text = load_document(path=path)
    text = clean_text(text)
    chunks = Chunker(chunk_size, chunk_overlap).recursive_split(text,chunk_size)
    
    chunk_ids = [str(uuid4()) for _ in chunks]
    metadatas = [{"source": path, "chunk_index": i } for i in range(len(chunks))]

    VectorStore(collection_name="documents").add_documents(chunks, chunk_ids, metadatas)

    registry = _load_registry()
    registry.append({
        "id": doc_id,
        "filename": filename,
        "path": path,
        "chunk_ids": chunk_ids,
        "chunk_count": len(chunks),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_registry(registry)

    return {"chunk_count": len(chunks)}
    