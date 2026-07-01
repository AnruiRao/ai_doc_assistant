from pydantic import BaseModel, HttpUrl

class UploadResponse(BaseModel):
    id: str
    filename: str
    chunk_count: int
    message: str

class DocumentItem(BaseModel):
    id: str
    filename: str
    chunk_count: int
    uploaded_at: str

class DeleteResponse(BaseModel):
    message: str
    chunk_count: int


class IngestUrlRequest(BaseModel):
    """从政务公开网址导入办事指南"""
    url: HttpUrl


class IngestUrlResponse(BaseModel):
    message: str
    chunk_count: int