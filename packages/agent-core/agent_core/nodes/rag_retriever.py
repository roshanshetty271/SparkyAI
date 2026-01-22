"""
RAG Retriever Node
==================

Retrieves relevant context from the knowledge base using semantic search.
Also computes 2D projection for the Embedding Space Explorer visualization.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, List, Literal, Optional, Tuple

import numpy as np
from langchain_openai import OpenAIEmbeddings

from agent_core.state import AgentState, NodeTiming, RetrievedChunk, QueryProjection
from agent_core.config import settings


class EmbeddingStore:
    """
    Simple in-memory embedding store for RAG.
    In production, this would be Qdrant/Pinecone/etc.
    """
    
    _instance: Optional["EmbeddingStore"] = None
    _embeddings: Optional[np.ndarray] = None
    _projections: Optional[np.ndarray] = None
    _chunks: Optional[List[Dict]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, embeddings_path: str = "data/embeddings"):
        """Load embeddings from disk if not already loaded."""
        if self._embeddings is not None:
            return
            
        embeddings_dir = Path(embeddings_path)
        
        # Load embeddings
        embeddings_file = embeddings_dir / "embeddings.npy"
        if embeddings_file.exists():
            self._embeddings = np.load(str(embeddings_file))
        else:
            # Fallback: create empty store
            self._embeddings = np.array([])
            
        # Load 2D projections (for visualization)
        projections_file = embeddings_dir / "projections_2d.npy"
        if projections_file.exists():
            self._projections = np.load(str(projections_file))
        else:
            self._projections = np.array([])
            
        # Load chunk metadata
        chunks_file = embeddings_dir / "chunks.json"
        if chunks_file.exists():
            with open(chunks_file) as f:
                self._chunks = json.load(f)
        else:
            self._chunks = []
    
    @property
    def embeddings(self) -> np.ndarray:
        if self._embeddings is None:
            self.load()
        return self._embeddings
    
    @property
    def projections(self) -> np.ndarray:
        if self._projections is None:
            self.load()
        return self._projections
    
    @property
    def chunks(self) -> List[Dict]:
        if self._chunks is None:
            self.load()
        return self._chunks
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar chunks using cosine similarity.
        
        Returns:
            List of (index, similarity_score) tuples
        """
        if len(self.embeddings) == 0:
            return []
            
        # Normalize for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = self.embeddings / np.linalg.norm(
            self.embeddings, axis=1, keepdims=True
        )
        
        # Compute similarities
        similarities = np.dot(embeddings_norm, query_norm)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    def project_query(self, query_embedding: np.ndarray) -> QueryProjection:
        """
        Project query embedding to 2D using weighted average of neighbors.
        
        This approximates where the query would appear in t-SNE space
        without running full t-SNE (too slow for real-time).
        """
        if len(self.projections) == 0 or len(self.embeddings) == 0:
            return QueryProjection(x=0.0, y=0.0)
        
        # Find k nearest neighbors
        k = min(5, len(self.embeddings))
        results = self.search(query_embedding, top_k=k)
        
        if not results:
            return QueryProjection(x=0.0, y=0.0)
        
        indices = [r[0] for r in results]
        weights = np.array([r[1] for r in results])
        
        # Normalize weights
        weights = weights / weights.sum()
        
        # Weighted average of 2D positions
        x = float(np.dot(weights, self.projections[indices, 0]))
        y = float(np.dot(weights, self.projections[indices, 1]))
        
        return QueryProjection(x=x, y=y)
    
    def get_all_points_for_visualization(self) -> List[Dict]:
        """Get all knowledge points with their 2D projections for frontend."""
        points = []
        for i, chunk in enumerate(self.chunks):
            if i < len(self.projections):
                points.append({
                    "id": chunk.get("id", f"chunk_{i}"),
                    "x": float(self.projections[i, 0]),
                    "y": float(self.projections[i, 1]),
                    "content": chunk.get("content", "")[:100] + "...",
                    "source": chunk.get("source", "unknown"),
                    "category": chunk.get("category", "general"),
                })
        return points


# Global store instance
embedding_store = EmbeddingStore()


def rag_retriever_node(state: AgentState) -> Dict[str, Any]:
    """
    Retrieve relevant context from knowledge base.
    
    This node:
    1. Generates embedding for user query
    2. Searches knowledge base for similar chunks
    3. Computes 2D projection for visualization
    4. Formats context for response generation
    
    Args:
        state: Current agent state
        
    Returns:
        Partial state update with retrieved context and projections
    """
    start_time = int(time.time() * 1000)
    
    # Update node states
    node_states = state["node_states"].copy()
    node_states["rag_retriever"] = "active"
    
    # Initialize embedding model
    embeddings_model = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )
    
    # Load embedding store
    embedding_store.load(settings.embeddings_dir)
    
    # Generate query embedding
    try:
        query_embedding = np.array(
            embeddings_model.embed_query(state["current_input"])
        )
    except Exception as e:
        # On embedding error, return empty context
        node_states["rag_retriever"] = "error"
        return {
            "retrieved_chunks": [],
            "retrieved_context": None,
            "retrieval_confidence": 0.0,
            "retrieval_scores": [],
            "retrieved_chunk_ids": [],
            "query_projection": None,
            "node_states": node_states,
            "error": f"Embedding error: {str(e)}",
        }
    
    # Search for similar chunks
    results = embedding_store.search(
        query_embedding, 
        top_k=settings.rag_top_k
    )
    
    # Process results
    retrieved_chunks: List[RetrievedChunk] = []
    retrieval_scores: List[float] = []
    chunk_ids: List[str] = []
    
    for idx, similarity in results:
        if idx < len(embedding_store.chunks):
            chunk_data = embedding_store.chunks[idx]
            chunk_id = chunk_data.get("id", f"chunk_{idx}")
            
            retrieved_chunks.append(RetrievedChunk(
                id=chunk_id,
                content=chunk_data.get("content", ""),
                source=chunk_data.get("source", "unknown"),
                similarity=similarity,
                metadata=chunk_data.get("metadata", {}),
            ))
            retrieval_scores.append(similarity)
            chunk_ids.append(chunk_id)
    
    # Compute retrieval confidence (highest score)
    retrieval_confidence = max(retrieval_scores) if retrieval_scores else 0.0
    
    # Compute 2D projection for visualization
    query_projection = embedding_store.project_query(query_embedding)
    
    # Format context string for LLM
    if retrieval_confidence >= settings.rag_similarity_threshold:
        context_parts = []
        for chunk in retrieved_chunks:
            if chunk["similarity"] >= settings.rag_similarity_threshold:
                context_parts.append(
                    f"[Source: {chunk['source']}]\n{chunk['content']}"
                )
        retrieved_context = "\n\n---\n\n".join(context_parts) if context_parts else None
    else:
        retrieved_context = None
    
    end_time = int(time.time() * 1000)
    
    # Mark node complete
    node_states["rag_retriever"] = "complete"
    
    # Record timing
    timing = NodeTiming(
        node="rag_retriever",
        start_ms=start_time,
        end_ms=end_time,
        duration_ms=end_time - start_time,
    )
    
    trace_metadata = state["trace_metadata"].copy() if state["trace_metadata"] else {}
    existing_timings = trace_metadata.get("node_timings", [])
    trace_metadata["node_timings"] = existing_timings + [timing]
    
    return {
        "retrieved_chunks": retrieved_chunks,
        "retrieved_context": retrieved_context,
        "retrieval_confidence": retrieval_confidence,
        "retrieval_scores": retrieval_scores,
        "retrieved_chunk_ids": chunk_ids,
        "query_projection": query_projection,
        "current_node": "rag_retriever",
        "node_states": node_states,
        "trace_metadata": trace_metadata,
    }


def route_after_rag(state: AgentState) -> Literal["response_generator", "fallback_response"]:
    """
    Conditional edge: decide if we have enough context to generate a response.
    
    If retrieval confidence is too low, route to fallback.
    """
    confidence = state.get("retrieval_confidence", 0.0)
    threshold = settings.rag_similarity_threshold
    
    if confidence >= threshold:
        return "response_generator"
    else:
        return "fallback_response"
