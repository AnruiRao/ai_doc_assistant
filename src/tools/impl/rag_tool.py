from tools.base import Tool
from pydantic import BaseModel, Field
from typing import Literal
from ingestion.loader import load_document
from ingestion.chunker import Chunker
from retrieval.vector_store import VectorStore


class RagToolInput(BaseModel):
    """RAG 工具输入：save=存储文档，search=检索知识"""
    use_for: Literal["save", "search"] = Field(description="操作类型")
    path: str = Field(default="", description="[save 模式] 文件路径，支持 .txt 和 .pdf")
    chunk_size: int = Field(default=500, description="[save 模式] 每块字符数")
    chunk_overlap: int = Field(default=50, description="[save 模式] 相邻块重叠字符数")
    query: str = Field(default="", description="[search 模式] 检索关键词")
    k: int = Field(default=4, description="[search 模式] 返回结果数量")
    collection_name: str = Field(default="documents", description="向量库集合名称")
    persist_directory: str = Field(default="data/chroma", description="向量库持久化目录")


class RagTool(Tool):
    def __init__(self):
        super().__init__(
            name="rag_tool",
            description="RAG 知识库工具：save 模式存储文档并建立向量索引，search 模式检索相关内容",
            input_model=RagToolInput,
        )

    def run(
        self,
        use_for: Literal["save", "search"],
        path: str = "",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        collection_name: str = "documents",
        persist_directory: str = "data/chroma",
        query: str = "",
        k: int = 4,
    ) -> str:
        if use_for == "save":
            if not path:
                return "错误：save 模式需要提供 path 参数"

            text = load_document(path)
            chunker = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = chunker.chunk_text(text)

            vs = VectorStore(collection_name=collection_name, persist_directory=persist_directory)
            vs.add_documents(chunks)
            return f"已将文档存入集合 '{collection_name}'，共 {len(chunks)} 个片段"

        if use_for == "search":
            if not query:
                return "错误：search 模式需要提供 query 参数"

            vs = VectorStore(collection_name=collection_name, persist_directory=persist_directory)
            results = vs.similarity_search(query=query, k=k)
            docs = results["documents"][0] if results.get("documents") else []
            return f"检索到 {len(docs)} 条结果:\n\n" + "\n---\n".join(docs)

        return f"错误：不支持的 use_for 值 '{use_for}'，仅支持 save 和 search"
