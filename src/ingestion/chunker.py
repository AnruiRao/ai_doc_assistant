class Chunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError(f"重叠长度({chunk_overlap})不能大于等于块大小({chunk_size})")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - self.chunk_overlap
        return chunks
    
    def recursive_split(self, text: str, chunk_size: int = 500) -> list[str]:
        chunks = []
        for paragraph in text.split("\n\n"):
            if not paragraph:
                continue
            if len(paragraph) <= chunk_size:
                chunks.append(paragraph)
                continue
            
            lines = paragraph.split("\n")
            current = ""
            for line in lines:
                if len(line) > chunk_size:
                    if current:
                        chunks.append(current)
                        current = ""
                    chunker = Chunker(chunk_size, chunk_overlap=0)
                    chunks.extend(chunker.chunk_text(line))
                elif not current:
                    current = line
                elif len(current) + 1 + len(line) <= chunk_size:
                    current += "\n" + line
                else:
                    chunks.append(current)
                    current = line
            if current:
                chunks.append(current)
        return chunks