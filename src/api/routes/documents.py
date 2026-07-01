from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from api.schemas.documents import UploadResponse, DocumentItem, DeleteResponse, IngestUrlRequest
from pathlib import Path
from services.document_service import DocumentService
from ingestion import fetch_web_content


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


@router.post("/ingest-url", response_model=UploadResponse)
async def ingest_url(body: IngestUrlRequest):
    """从政务公开网址导入办事指南内容到知识库（通过 DocumentService）"""
    from uuid import uuid4

    try:
        text = fetch_web_content(str(body.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法获取网页内容：{str(e)}")

    # 提取标题作为文件名
    first_line = text.strip().split('\n')[0][:50] if text.strip() else "web_import"
    safe_name = f"{first_line}_{uuid4().hex[:8]}.txt"
    safe_name = "".join(c if c.isalnum() or c in ('-', '_', '.') else '_' for c in safe_name)

    # 保存后通过 DocumentService 处理（获得去重+注册表+可删除）
    result = DocumentService().upload(content=text.encode('utf-8'), filename=safe_name)

    return UploadResponse(
        id=result.id,
        filename=result.filename,
        chunk_count=result.chunk_count,
        message=f"已从 {body.url} 导入，共 {result.chunk_count} 个片段",
    )
