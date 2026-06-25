from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.schemas.documents import UploadResponse, DocumentItem, DeleteResponse
from pathlib import Path
from services.document_service import DocumentService


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
