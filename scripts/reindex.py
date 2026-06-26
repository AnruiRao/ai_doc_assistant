"""重新索引所有项目文档到向量库（新 embedding 模型）"""

import sys
import subprocess
from pathlib import Path

# 需要索引的文件
FILES = [
    # 核心项目文档
    "PLAN.md",
    "TASKS.md",
    # 所有决策记录
    *sorted(Path("docs/decisions").glob("*.md")),
    # 核心源码
    "src/core/agent.py",
    "src/core/config.py",
    "src/core/exceptions.py",
    "src/core/llm.py",
    "src/core/retry.py",
    "src/core/logging.py",
    "src/core/async_utils.py",
    "src/agents/react_agent.py",
    "src/tools/base.py",
    "src/tools/registry.py",
    "src/tools/impl/calculator.py",
    "src/tools/impl/rag_tool.py",
    "src/ingestion/loader.py",
    "src/ingestion/cleaner.py",
    "src/ingestion/chunker.py",
    "src/retrieval/vector_store.py",
    "src/app/ui.py",
    "src/services/document_service.py",
    "src/api/__init__.py",
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/chat.py",
    "src/api/routes/documents.py",
    # 测试文件
    "tests/test_chunker.py",
    "tests/test_retrieval.py",
    "tests/test_documents.py",
    # 项目配置
    "pyproject.toml",
    "README.md",
    "run.sh",
    "run_api.sh",
]

def main():
    for f in FILES:
        path = Path(f)
        if not path.exists():
            print(f"⚠️  跳过（不存在）: {f}")
            continue
        abs_path = path.resolve()
        print(f"📄 索引: {f}")
        result = subprocess.run(
            [sys.executable, "-c", f"""
import sys; sys.path.insert(0, 'src')
from tools.impl.rag_tool import RagTool
tool = RagTool()
print(tool.run(use_for='save', path=r'{abs_path}'))
"""],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"   ❌ 失败: {result.stderr.strip()}")
        else:
            print(f"   ✅ {result.stdout.strip()}")

    # 确认总数
    result = subprocess.run(
        [sys.executable, "-c", """
import sys; sys.path.insert(0, 'src')
from retrieval.vector_store import VectorStore
vs = VectorStore()
print(f"总文档数: {vs.count()}")
"""],
        capture_output=True, text=True, timeout=30,
    )
    print(result.stdout.strip())


if __name__ == "__main__":
    main()
