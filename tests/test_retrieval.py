import pytest
from pathlib import Path
from ingestion.loader import load_document, load_text, load_pdf
from ingestion.chunker import Chunker
from retrieval.vector_store import VectorStore


class TestLoader:
    def test_load_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        assert load_document(f) == "hello world"

    def test_load_document_auto_detect(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("some text content", encoding="utf-8")
        assert load_document(f) == "some text content"

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="不支持的文件类型"):
            load_document("test.xyz")

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_text("/nonexistent/file.txt")

    def test_load_pdf_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_pdf("/nonexistent/file.pdf")


class TestChunker:
    def test_basic_chunking(self):
        chunker = Chunker(chunk_size=10, chunk_overlap=2)
        text = "abcdefghijklmnopqrstuvwxyz"
        chunks = chunker.chunk_text(text)
        assert chunks == ["abcdefghij", "ijklmnopqr", "qrstuvwxyz"]

    def test_overlap_validation(self):
        with pytest.raises(ValueError):
            Chunker(chunk_size=10, chunk_overlap=10)

    def test_smaller_than_chunk(self):
        chunker = Chunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk_text("short")
        assert chunks == ["short"]

    def test_exact_chunk_size(self):
        chunker = Chunker(chunk_size=5, chunk_overlap=1)
        text = "12345"
        chunks = chunker.chunk_text(text)
        assert chunks == ["12345"]

    def test_empty_text(self):
        chunker = Chunker(chunk_size=10, chunk_overlap=2)
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_overlap_content(self):
        chunker = Chunker(chunk_size=5, chunk_overlap=2)
        text = "abcdefghij"
        chunks = chunker.chunk_text(text)
        assert chunks[0] == "abcde"
        assert chunks[1] == "defgh"
        assert chunks[2] == "ghij"


class TestVectorStore:
    def test_add_and_search(self, tmp_path):
        persist_dir = str(tmp_path / "chroma")
        vs = VectorStore(
            collection_name="test_docs",
            persist_directory=persist_dir,
        )
        vs.add_documents(
            ["苹果是一种水果", "香蕉是一种水果", "Python是一种编程语言"],
            ids=["1", "2", "3"],
        )
        assert vs.count() == 3

        results = vs.similarity_search("水果", k=2)
        assert len(results["documents"][0]) == 2
        vs.delete_collection()

    def test_add_with_metadata(self, tmp_path):
        persist_dir = str(tmp_path / "chroma_meta")
        vs = VectorStore(
            collection_name="test_meta",
            persist_directory=persist_dir,
        )
        vs.add_documents(
            ["深度学习", "机器学习"],
            ids=["a", "b"],
            metadatas=[{"source": "book"}, {"source": "paper"}],
        )
        results = vs.similarity_search("学习", k=2)
        assert len(results["documents"][0]) == 2
        assert results["metadatas"][0][0]["source"] == "book"
        vs.delete_collection()

    def test_empty_store(self, tmp_path):
        persist_dir = str(tmp_path / "chroma_empty")
        vs = VectorStore(
            collection_name="test_empty",
            persist_directory=persist_dir,
        )
        assert vs.count() == 0
        vs.delete_collection()

    def test_recreate_collection(self, tmp_path):
        persist_dir = str(tmp_path / "chroma_recreate")
        vs = VectorStore(
            collection_name="test_recreate",
            persist_directory=persist_dir,
        )
        vs.add_documents(["doc1"], ids=["1"])
        assert vs.count() == 1
        vs.delete_collection()

        vs2 = VectorStore(
            collection_name="test_recreate",
            persist_directory=persist_dir,
        )
        assert vs2.count() == 0
        vs2.delete_collection()
