from pathlib import Path
from pypdf import PdfReader

def load_text(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {p}")
    return p.read_text(encoding="utf-8")

def load_pdf(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {p}")
    reader = PdfReader(str(p))
    texts = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n".join(texts)

def load_document(path: str | Path) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".txt":
        return load_text(p)
    elif suffix == ".pdf":
        return load_pdf(p)
    else:
        raise ValueError(f"不支持的文件类型: {suffix}，仅支持 .txt 和 .pdf")