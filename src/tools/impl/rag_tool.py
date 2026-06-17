from uuid import uuid4
from tools.base import Tool
from pydantic import BaseModel, Field
from typing import Literal
from ingestion.loader import load_document
from ingestion.chunker import Chunker
from retrieval.vector_store import VectorStore


class RagToolInput(BaseModel):
    """RAG 工具输入：save=存储文档，search=检索知识"""
    use_for: Literal["save", "search", "delete"] = Field(description="操作类型")
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
            description="RAG 知识库工具：save 模式存储文档并建立向量索引，search 模式检索相关内容， delete 模式删除向量库",
            input_model=RagToolInput,
        )

    def run(
        self,
        use_for: Literal["save", "search", "delete"],
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

            ids = [str(uuid4()) for _ in chunks]
            metadatas = [{"source": path, "chunk_index": i} for i in range(len(chunks))]

            vs = VectorStore(collection_name=collection_name, persist_directory=persist_directory)
            vs.add_documents(documents=chunks, ids=ids, metadatas=metadatas)
            return f"已将文档存入集合 '{collection_name}'，共 {len(chunks)} 个片段"

        if use_for == "search":
            if not query:
                return "错误：search 模式需要提供 query 参数"

            vs = VectorStore(collection_name=collection_name, persist_directory=persist_directory)
            results = vs.similarity_search(query=query, k=k)
            docs = results["documents"][0] if results.get("documents") else []
            if not docs:
                return "未检索到相关内容"

            metas = results["metadatas"][0] if results.get("metadatas") else [None] * len(docs)
            lines = []
            for doc, meta in zip(docs, metas):
                source = meta.get("source", "未知来源") if meta else "未知来源"
                lines.append(f"[来源: {source}]\n{doc}")
            return f"检索到 {len(docs)} 条结果:\n\n" + "\n---\n".join(lines)
        
        if use_for == "delete":
            vs = VectorStore(collection_name=collection_name, persist_directory=persist_directory)
            count = vs.count()
            if count == 0:
                return f"集合 '{collection_name}' 不存在或已为空"
            vs.delete_collection()
            return f"已删除向量库集合：{collection_name}（共 {count} 个片段）"

        return f"错误：不支持的 use_for 值 '{use_for}'，仅支持 save、search、delete"
