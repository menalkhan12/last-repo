"""Hybrid RAG: ChromaDB (vector) + RankBM25 (keyword), rerank top 8, fallback query."""
import re
from typing import List, Optional

from rank_bm25 import BM25Okapi

from config import CHROMA_PERSIST_DIR, FALLBACK_QUERY, TOP_K
from app.data_loader import load_documents


class HybridRAG:
    def __init__(self):
        self._chroma = None
        self._collection = None
        self._bm25 = None
        self._documents: List[str] = []
        self._doc_sources: List[str] = []
        self._id_to_idx: dict = {}
        self._embeddings_model = None

    def _get_embedding_model(self):
        if self._embeddings_model is None:
            from sentence_transformers import SentenceTransformer
            self._embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._embeddings_model

    def build(self) -> None:
        """Load data, chunk, index in ChromaDB and BM25."""
        import chromadb
        from chromadb.config import Settings

        raw_docs = load_documents()
        self._documents = [d[0] for d in raw_docs]
        self._doc_sources = [d[1] for d in raw_docs]

        if not self._documents:
            return

        # BM25: tokenize by simple word split
        tokenized = [re.findall(r"\w+", d.lower()) for d in self._documents]
        self._bm25 = BM25Okapi(tokenized)

        # ChromaDB with persistent storage
        self._chroma = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        collection_name = "ist_admission"
        try:
            self._collection = self._chroma.get_collection(collection_name)
            # Rebuild if empty
            if self._collection.count() == 0:
                raise ValueError("empty")
        except Exception:
            self._chroma.delete_collection(collection_name)
            self._collection = self._chroma.create_collection(
                name=collection_name,
                metadata={"description": "IST admission knowledge base"},
            )
            model = self._get_embedding_model()
            embeddings = model.encode(self._documents).tolist()
            ids = [f"doc_{i}" for i in range(len(self._documents))]
            self._id_to_idx = {id_: i for i, id_ in enumerate(ids)}
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=self._documents,
                metadatas=[{"source": s} for s in self._doc_sources],
            )

    def search(self, query: str, top_k: int = TOP_K, use_fallback_if_empty: bool = True) -> List[str]:
        """
        Hybrid search: vector + keyword, rerank, return top_k chunks.
        If no good results and use_fallback_if_empty, run again with FALLBACK_QUERY.
        """
        if not self._documents:
            return []

        query = query.strip()
        if not query and use_fallback_if_empty:
            query = FALLBACK_QUERY

        # Vector search (ChromaDB)
        model = self._get_embedding_model()
        q_emb = model.encode([query]).tolist()
        vector_results = self._collection.query(
            query_embeddings=q_emb,
            n_results=min(top_k * 2, self._collection.count()),
            include=["documents", "distances", "ids"],
        )
        v_ids = vector_results["ids"][0] if vector_results.get("ids") else []
        v_docs = vector_results["documents"][0] if vector_results["documents"] else []
        v_distances = vector_results["distances"][0] if vector_results.get("distances") else []

        # BM25 keyword search
        tokenized_q = re.findall(r"\w+", query.lower())
        bm25_scores = self._bm25.get_scores(tokenized_q) if tokenized_q else [0.0] * len(self._documents)
        bm25_top = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )[: top_k * 2]

        # Combine: by doc index; Chroma L2: smaller distance = better
        doc_scores: dict = {}
        if v_docs and v_distances is not None and v_ids:
            max_d = max(v_distances) or 1
            for i, id_ in enumerate(v_ids):
                idx = self._id_to_idx.get(id_)
                if idx is not None:
                    norm_d = v_distances[i] / max_d
                    doc_scores[idx] = doc_scores.get(idx, 0) + (1.0 - norm_d)
        for idx in bm25_top:
            if bm25_scores[idx] > 0:
                max_b = max(bm25_scores) or 1
                doc_scores[idx] = doc_scores.get(idx, 0) + (bm25_scores[idx] / max_b)

        # Rerank and take top_k
        ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        out = [self._documents[i] for i, _ in ranked]

        if not out and use_fallback_if_empty and query != FALLBACK_QUERY:
            return self.search(FALLBACK_QUERY, top_k=top_k, use_fallback_if_empty=False)
        return out


# Singleton for app/agent use
_rag: Optional[HybridRAG] = None


def get_rag() -> HybridRAG:
    global _rag
    if _rag is None:
        _rag = HybridRAG()
        _rag.build()
    return _rag
