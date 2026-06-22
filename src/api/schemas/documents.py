from pydantic import BaseModel

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