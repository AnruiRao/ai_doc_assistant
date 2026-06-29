from sentence_transformers import CrossEncoder
import structlog
import torch

logger = structlog.get_logger(__name__)

DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

class Reranker:
    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL):
        self._model_name = model_name
        self._model: CrossEncoder | None = None

    def _load_model(self) -> CrossEncoder:
        if self._model is not None:
            return self._model
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info("加载 reranker 模型", model=self._model_name, device=device)
        self._model = CrossEncoder(self._model_name, device=device)
        return self._model
    
    def rerank(
            self,
            query: str,
            documents: list[str],
            top_k: int = 4
    ) -> list[tuple[str, float]]:
        if not documents:
            return []
        if len(documents) <= top_k:
            return [(doc, 0.0) for doc in documents]
        
        model = self._load_model()
        pairs = [(query, doc) for doc in documents]
        scores = model.predict(pairs,show_progress_bar=False)

        scored = list(zip(documents,scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]