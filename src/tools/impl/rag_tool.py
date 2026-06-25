from uuid import uuid4
from tools.base import Tool
from pydantic import BaseModel, Field
from typing import Literal
from ingestion.loader import load_document
from ingestion.cleaner import clean_text
from ingestion.chunker import Chunker
from retrieval.vector_store import VectorStore
import structlog
from services.document_service import DocumentService

logger = structlog.get_logger(__name__)

class RagToolInput(BaseModel):
    """RAG 工具输入：save=存储文档，search=检索知识"""
    use_for: Literal["save", "search", "delete", "list"] = Field(description="操作类型")
    path: str = Field(default="", description="[save 模式] 文件路径，支持 .txt/.md/.py/.yaml/.toml/.json 等纯文本文件和 .pdf")
    chunk_size: int = Field(default=1000, description="[save 模式] 每块字符数")
    chunk_overlap: int = Field(default=100, description="[save 模式] 相邻块重叠字符数")
    query: str = Field(default="", description="[search 模式] 检索关键词")
    k: int = Field(default=4, description="[search 模式] 返回结果数量")
    collection_name: str = Field(default="documents", description="向量库集合名称")
    persist_directory: str = Field(default="data/chroma", description="向量库持久化目录")
    source: str = Field(default="",description="[delete 模式] 按 source 路径删除指定文档，不传则清空整个集合")


class RagTool(Tool):
    def __init__(self):
        super().__init__(
            name="rag_tool",
            description="RAG 知识库工具：save 模式存储文档并建立向量索引，search 模式检索相关内容， delete 模式删除向量库",
            input_model=RagToolInput,
        )
        
    def run(
        self,
        use_for: Literal["save", "search", "delete", "list"],
        path: str = "",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        collection_name: str = "documents",
        persist_directory: str = "data/chroma",
        query: str = "",
        k: int = 4,
        source: str = ""
    ) -> str:
        if use_for == "save":
            if not path:
                return "错误：save 模式需要提供 path 参数"

            text = load_document(path)
            text = clean_text(text)
            chunker = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = chunker.recursive_split(text, chunk_size=chunk_size)

            ids = [str(uuid4()) for _ in chunks]
            metadatas = [{"source": path, "chunk_index": i} for i in range(len(chunks))]

            vs = VectorStore(collection_name=collection_name, persist_directory=persist_directory)
            vs.add_documents(documents=chunks, ids=ids, metadatas=metadatas)
            
            logger.info("调用工具成功",use_for = use_for)
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
            seen_ids = set()
            for doc, meta in zip(docs, metas):
                source = meta.get("source", "未知来源") if meta else "未知来源"
                chunk_index = meta.get("chunk_index") if meta else None

                # 滑动窗口：取命中 chunk 前后各 N 个相邻 chunk，帮助模型理解上下文
                context_window = 2
                if source and chunk_index is not None:
                    neighbors = vs.collection.get(
                        where={
                            "$and": [
                                {"source": {"$eq": source}},
                                {"chunk_index": {"$gte": chunk_index - context_window}},
                                {"chunk_index": {"$lte": chunk_index + context_window}},
                            ]
                        }
                    )
                    neighbor_texts = neighbors.get("documents", [])
                    neighbor_metas = neighbors.get("metadatas", [])
                    neighbor_ids = neighbors.get("ids", [])
                    # 按 chunk_index 排序，组装成带上下文的文档块
                    neighbor_pairs = sorted(
                        [
                            (m.get("chunk_index", 0) if m else 0, nid, txt, m.get("source", source) if m else source)
                            for txt, m, nid in zip(neighbor_texts, neighbor_metas, neighbor_ids)
                            if nid not in seen_ids
                        ],
                        key=lambda x: x[0],
                    )
                    for ci, nid, txt, src in neighbor_pairs:
                        seen_ids.add(nid)
                        lines.append(f"[来源: {src} 片段 {ci}]\n{txt}")
                else:
                    lines.append(f"[来源: {source}]\n{doc}")

            logger.info("调用工具成功", use_for=use_for)
            return f"检索到 {len(docs)} 条结果（含上下文）:\n\n" + "\n---\n".join(lines)
        
        if use_for == "delete":
            vs = VectorStore(collection_name=collection_name, persist_directory=persist_directory)
            count = vs.count()
            if count == 0:
                return f"集合 '{collection_name}' 不存在或已为空"
            if not source:
                DocumentService().delete_all()
                logger.info("调用工具成功", use_for=use_for)
                return f"已删除所有文档（共 {count} 个片段）"
            else:
                # TODO: 按名称删除文档（docs/decisions/008-tool-parameter-semantic-mismatch.md）
                # 方案：工具入参对齐 filename，内部精确匹配优先+模糊匹配+多条命中时返回列表让 Agent 追问
                return "聊天中暂时不支持按名称删除文档，请前往文档管理页面操作"

        if use_for == "list":
            record = DocumentService().list_documents()
            files = []
            for doc in record:
                if doc.filename is not None:
                    files.append(f"[来源:{doc.path}]\n{doc.filename}")
            logger.info("调用工具成功",use_for = use_for)
            return f"已找到文档 {len(record)} 条:\n\n" + "\n---\n".join(files)

        return f"错误：不支持的 use_for 值 '{use_for}'，仅支持 save、search、delete、list"
