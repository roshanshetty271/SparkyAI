"""Tests for the embedding store and RAG retrieval."""

import pytest
import numpy as np
import json
import tempfile
from pathlib import Path

from agent_core.nodes.rag_retriever import EmbeddingStore, embedding_store


class TestEmbeddingStore:
    """Test suite for EmbeddingStore class."""
    
    @pytest.fixture
    def temp_embeddings_dir(self):
        """Create temporary directory with test embeddings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            embeddings_path = Path(tmpdir)
            
            # Create test embeddings (3D for simplicity)
            embeddings = np.array([
                [1.0, 0.0, 0.0],  # Chunk 0
                [0.0, 1.0, 0.0],  # Chunk 1
                [0.0, 0.0, 1.0],  # Chunk 2
                [0.7, 0.7, 0.0],  # Chunk 3 - between 0 and 1
            ])
            np.save(str(embeddings_path / "embeddings.npy"), embeddings)
            
            # Create 2D projections
            projections = np.array([
                [0.0, 0.0],
                [1.0, 0.0],
                [0.0, 1.0],
                [0.5, 0.5],
            ])
            np.save(str(embeddings_path / "projections_2d.npy"), projections)
            
            # Create chunk metadata
            chunks = [
                {
                    "id": "chunk_0",
                    "content": "I have experience with React and TypeScript.",
                    "source": "skills.md",
                    "category": "frontend",
                    "metadata": {"years": 3},
                },
                {
                    "id": "chunk_1",
                    "content": "I built a full-stack e-commerce application.",
                    "source": "projects.md",
                    "category": "projects",
                    "metadata": {"stack": "MERN"},
                },
                {
                    "id": "chunk_2",
                    "content": "I worked as a Senior Software Engineer at TechCorp.",
                    "source": "experience.md",
                    "category": "experience",
                    "metadata": {"years": 2},
                },
                {
                    "id": "chunk_3",
                    "content": "I specialize in React, Next.js, and modern frontend development.",
                    "source": "skills.md",
                    "category": "frontend",
                    "metadata": {"level": "expert"},
                },
            ]
            
            with open(embeddings_path / "chunks.json", "w") as f:
                json.dump(chunks, f)
            
            yield embeddings_path
    
    def test_singleton_pattern(self):
        """Test that EmbeddingStore is a singleton."""
        store1 = EmbeddingStore()
        store2 = EmbeddingStore()
        assert store1 is store2
    
    def test_load_embeddings(self, temp_embeddings_dir):
        """Test loading embeddings from disk."""
        store = EmbeddingStore()
        
        # Reset state
        store._embeddings = None
        store._projections = None
        store._chunks = None
        
        # Load from temp dir
        store.load(str(temp_embeddings_dir))
        
        assert store.embeddings is not None
        assert store.embeddings.shape == (4, 3)
        assert store.projections is not None
        assert store.projections.shape == (4, 2)
        assert len(store.chunks) == 4
    
    def test_search_exact_match(self, temp_embeddings_dir):
        """Test searching for exact embedding match."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        # Query with exact match to chunk 0
        query = np.array([1.0, 0.0, 0.0])
        results = store.search(query, top_k=2)
        
        assert len(results) == 2
        assert results[0][0] == 0  # Chunk 0 should be first
        assert results[0][1] > 0.99  # Perfect match
    
    def test_search_similarity(self, temp_embeddings_dir):
        """Test searching for similar embeddings."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        # Query similar to chunk 3 (between 0 and 1)
        query = np.array([0.6, 0.8, 0.0])
        results = store.search(query, top_k=2)
        
        assert len(results) == 2
        # Should return chunk 3 and 1 (or 0) as most similar
        top_chunk_id = results[0][0]
        assert top_chunk_id in [1, 3]  # Either chunk 1 or 3
        assert results[0][1] > 0.5  # Reasonable similarity
    
    def test_search_empty_store(self):
        """Test searching in empty store."""
        store = EmbeddingStore()
        store._embeddings = np.array([])
        store._projections = np.array([])
        store._chunks = []
        
        query = np.array([1.0, 0.0, 0.0])
        results = store.search(query, top_k=5)
        
        assert results == []
    
    def test_search_top_k(self, temp_embeddings_dir):
        """Test that search returns correct number of results."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        query = np.array([1.0, 0.0, 0.0])
        
        # Test different top_k values
        results_k1 = store.search(query, top_k=1)
        assert len(results_k1) == 1
        
        results_k3 = store.search(query, top_k=3)
        assert len(results_k3) == 3
        
        results_k10 = store.search(query, top_k=10)
        assert len(results_k10) == 4  # Only 4 chunks available
    
    def test_project_query_weighted_average(self, temp_embeddings_dir):
        """Test query projection to 2D space."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        # Query close to chunk 0
        query = np.array([1.0, 0.0, 0.0])
        projection = store.project_query(query)
        
        assert projection.x is not None
        assert projection.y is not None
        # Should be close to chunk 0's projection (0.0, 0.0)
        assert abs(projection.x) < 0.5
        assert abs(projection.y) < 0.5
    
    def test_project_query_between_chunks(self, temp_embeddings_dir):
        """Test query projection between multiple chunks."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        # Query exactly like chunk 3 (between 0 and 1)
        query = np.array([0.7, 0.7, 0.0])
        projection = store.project_query(query)
        
        # Should be close to chunk 3's projection (0.5, 0.5)
        assert 0.3 < projection.x < 0.7
        assert 0.3 < projection.y < 0.7
    
    def test_project_query_empty_store(self):
        """Test query projection on empty store."""
        store = EmbeddingStore()
        store._embeddings = np.array([])
        store._projections = np.array([])
        store._chunks = []
        
        query = np.array([1.0, 0.0, 0.0])
        projection = store.project_query(query)
        
        assert projection.x == 0.0
        assert projection.y == 0.0
    
    def test_get_all_points_for_visualization(self, temp_embeddings_dir):
        """Test getting all points for frontend visualization."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        points = store.get_all_points_for_visualization()
        
        assert len(points) == 4
        
        # Check first point
        point = points[0]
        assert "id" in point
        assert "x" in point
        assert "y" in point
        assert "content" in point
        assert "source" in point
        assert "category" in point
        
        # Verify coordinates match projections
        assert point["x"] == 0.0
        assert point["y"] == 0.0
        assert point["id"] == "chunk_0"
        assert point["category"] == "frontend"
    
    def test_get_all_points_truncates_content(self, temp_embeddings_dir):
        """Test that content is truncated for visualization."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        points = store.get_all_points_for_visualization()
        
        for point in points:
            # Content should be truncated to ~100 chars with "..."
            assert len(point["content"]) <= 104  # 100 + "..."
    
    def test_cosine_similarity_normalization(self, temp_embeddings_dir):
        """Test that cosine similarity is normalized correctly."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        # Query with non-unit vector
        query = np.array([2.0, 0.0, 0.0])
        results = store.search(query, top_k=1)
        
        # Despite different magnitude, should still find chunk 0 with high similarity
        assert results[0][0] == 0
        assert results[0][1] > 0.99
    
    def test_chunks_metadata_structure(self, temp_embeddings_dir):
        """Test that chunk metadata has correct structure."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        store.load(str(temp_embeddings_dir))
        
        for chunk in store.chunks:
            assert "id" in chunk
            assert "content" in chunk
            assert "source" in chunk
            assert "category" in chunk
            assert "metadata" in chunk
            assert isinstance(chunk["metadata"], dict)


# Integration tests (would require actual embeddings)
class TestEmbeddingStoreIntegration:
    """Integration tests for embedding store with real data."""
    
    def test_load_actual_embeddings_if_exists(self):
        """Test loading actual embeddings if they exist."""
        store = EmbeddingStore()
        store._embeddings = None
        store._projections = None
        store._chunks = None
        
        try:
            store.load("data/embeddings")
            
            # If embeddings exist, verify structure
            if len(store.chunks) > 0:
                assert store.embeddings.shape[0] == len(store.chunks)
                assert store.projections.shape[0] == len(store.chunks)
                assert store.embeddings.shape[1] > 0  # Has embedding dimensions
                assert store.projections.shape[1] == 2  # 2D projections
        except Exception:
            # If embeddings don't exist, that's okay for this test
            pytest.skip("No actual embeddings found")
    
    def test_search_performance(self, temp_embeddings_dir):
        """Test that search performs reasonably on larger dataset."""
        import time
        
        # Create larger dataset
        n_chunks = 100
        dim = 384  # Standard embedding dimension
        
        store = EmbeddingStore()
        store._embeddings = np.random.rand(n_chunks, dim)
        store._projections = np.random.rand(n_chunks, 2)
        store._chunks = [
            {
                "id": f"chunk_{i}",
                "content": f"Content {i}",
                "source": "test.md",
                "category": "test",
                "metadata": {},
            }
            for i in range(n_chunks)
        ]
        
        # Test search performance
        query = np.random.rand(dim)
        
        start = time.time()
        results = store.search(query, top_k=5)
        duration = time.time() - start
        
        assert len(results) == 5
        assert duration < 0.1  # Should complete in <100ms
