from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.schemas.documents import UploadResponse, DocumentItem, DeleteResponse, IngestUrlRequest, IngestUrlResponse
from pathlib import Path
from services.document_service import DocumentService
from uuid import uuid4
from ingestion import fetch_web_content, clean_text, tag_gov_sections, Chunker
from retrieval.vector_store import VectorStore
from services.document_service import CHROMA_PATH


router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".txt", ".md", ".pdf", ".py", ".yaml", ".yml", ".toml", ".json", ".cfg", ".ini"):
        raise HTTPException(status_code=400, detail="仅支持传入 .txt/.md/.py/.yaml/.toml/.json 等纯文本文件与 .pdf 文件")

    content = await file.read()
    result = DocumentService().upload(content, file.filename, chunk_size, chunk_overlap)

    return UploadResponse(
        id=result.id,
        filename=result.filename,
        chunk_count=result.chunk_count,
        message=f"文档 {result.filename} 已入库，共 {result.chunk_count} 个片段",
    )

@router.get("/documents", response_model=list[DocumentItem])
def list_documents():
    docs = DocumentService().list_documents()
    return [
        DocumentItem(id=d.id, filename=d.filename, chunk_count=d.chunk_count, uploaded_at=d.uploaded_at)
        for d in docs
    ]
    
   
@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str):
    record = DocumentService().delete_by_id(doc_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    return DeleteResponse(
        message=f"文档 {record.filename} 已删除",
        chunk_count=record.chunk_count,
    )


@router.post("/ingest-url", response_model=IngestUrlResponse)
async def ingest_url(body: IngestUrlRequest):
    """从政务公开网址导入办事指南内容到知识库"""
    try:
        text = fetch_web_content(body.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法获取网页内容：{str(e)}")

    text = clean_text(text)
    text = tag_gov_sections(text)
    chunker = Chunker(chunk_size=1000, chunk_overlap=100)
    chunks = chunker.recursive_split(text, chunk_size=1000)

    if not chunks:
        return IngestUrlResponse(message="未提取到有效内容", chunk_count=0)

    ids = [str(uuid4()) for _ in chunks]
    metadatas = [{"source": body.url, "chunk_index": i} for i in range(len(chunks))]

    VectorStore(collection_name="documents", persist_directory=CHROMA_PATH).add_documents(
        documents=chunks, ids=ids, metadatas=metadatas
    )

    return IngestUrlResponse(
        message=f"已从 {body.url} 导入，共 {len(chunks)} 个片段",
        chunk_count=len(chunks),
    )
