#!/usr/bin/env python3
"""
Embedding Generation Script
===========================

Generates embeddings for knowledge base documents and computes
t-SNE projections for the Embedding Space Explorer visualization.

Usage:
    python scripts/generate_embeddings.py
    
    # Or with custom paths:
    python scripts/generate_embeddings.py --knowledge-dir ./knowledge --output-dir ./data/embeddings
"""

import argparse
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import sys

import numpy as np
from sklearn.manifold import TSNE
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.agent_core.agent_core.config import settings


def load_markdown_files(knowledge_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all markdown files from the knowledge directory.
    
    Args:
        knowledge_dir: Path to knowledge directory
        
    Returns:
        List of document dicts with content and metadata
    """
    documents = []
    
    for md_file in knowledge_dir.rglob("*.md"):
        # Read content
        content = md_file.read_text(encoding="utf-8")
        
        # Get relative path as source
        relative_path = md_file.relative_to(knowledge_dir)
        
        # Determine category from parent folder
        category = relative_path.parent.name if relative_path.parent.name else "general"
        
        documents.append({
            "content": content,
            "source": str(relative_path),
            "category": category,
            "filename": md_file.name,
        })
    
    print(f"📄 Loaded {len(documents)} markdown files")
    return documents


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = 400,
    chunk_overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Split documents into chunks for embedding.
    
    Args:
        documents: List of document dicts
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunk dicts with content and metadata
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
    )
    
    chunks = []
    
    for doc in documents:
        # Split content
        texts = splitter.split_text(doc["content"])
        
        for i, text in enumerate(texts):
            # Generate unique ID
            chunk_id = hashlib.md5(
                f"{doc['source']}:{i}:{text[:50]}".encode()
            ).hexdigest()[:12]
            
            chunks.append({
                "id": chunk_id,
                "content": text,
                "source": doc["source"],
                "category": doc["category"],
                "chunk_index": i,
                "metadata": {
                    "filename": doc["filename"],
                    "total_chunks": len(texts),
                },
            })
    
    print(f"📝 Created {len(chunks)} chunks")
    return chunks


def generate_embeddings(
    chunks: List[Dict[str, Any]],
    model: str = "text-embedding-3-small",
) -> np.ndarray:
    """
    Generate embeddings for all chunks.
    
    Args:
        chunks: List of chunk dicts
        model: OpenAI embedding model
        
    Returns:
        NumPy array of embeddings (n_chunks x embedding_dim)
    """
    embeddings_model = OpenAIEmbeddings(
        model=model,
        api_key=settings.openai_api_key,
    )
    
    print(f"🔄 Generating embeddings with {model}...")
    
    # Process in batches to avoid rate limits
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["content"] for c in batch]
        
        batch_embeddings = embeddings_model.embed_documents(texts)
        all_embeddings.extend(batch_embeddings)
        
        print(f"  Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")
    
    embeddings = np.array(all_embeddings)
    print(f"✅ Generated embeddings: shape {embeddings.shape}")
    
    return embeddings


def compute_2d_projections(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute 2D projections using t-SNE for visualization.
    
    Args:
        embeddings: High-dimensional embeddings
        
    Returns:
        2D projections (n_chunks x 2)
    """
    print("🔄 Computing t-SNE projections...")
    
    # t-SNE parameters tuned for small datasets
    perplexity = min(30, len(embeddings) - 1)
    
    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        learning_rate="auto",
        init="pca",
        random_state=42,
        n_iter=1000,
    )
    
    projections = tsne.fit_transform(embeddings)
    
    # Normalize to [-1, 1] range for easier visualization
    projections = projections - projections.mean(axis=0)
    scale = np.abs(projections).max()
    if scale > 0:
        projections = projections / scale
    
    print(f"✅ Computed 2D projections: shape {projections.shape}")
    
    return projections


def save_outputs(
    chunks: List[Dict[str, Any]],
    embeddings: np.ndarray,
    projections: np.ndarray,
    output_dir: Path,
) -> None:
    """
    Save all outputs to disk.
    
    Args:
        chunks: List of chunk dicts
        embeddings: Embedding array
        projections: 2D projection array
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save embeddings
    np.save(str(output_dir / "embeddings.npy"), embeddings)
    print(f"💾 Saved embeddings to {output_dir / 'embeddings.npy'}")
    
    # Save 2D projections
    np.save(str(output_dir / "projections_2d.npy"), projections)
    print(f"💾 Saved projections to {output_dir / 'projections_2d.npy'}")
    
    # Save chunk metadata (without embeddings)
    chunks_file = output_dir / "chunks.json"
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved chunk metadata to {chunks_file}")
    
    # Save summary
    summary = {
        "total_chunks": len(chunks),
        "embedding_dim": embeddings.shape[1],
        "embedding_model": "text-embedding-3-small",
        "categories": list(set(c["category"] for c in chunks)),
        "sources": list(set(c["source"] for c in chunks)),
    }
    
    summary_file = output_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Saved summary to {summary_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for knowledge base"
    )
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=Path("knowledge"),
        help="Directory containing markdown files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/embeddings"),
        help="Directory for output files",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=400,
        help="Target chunk size in characters",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlap between chunks",
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("SparkyAI Embedding Generator")
    print("=" * 50)
    print()
    
    # Check OpenAI key
    if not settings.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Check knowledge directory
    if not args.knowledge_dir.exists():
        print(f"❌ Error: Knowledge directory not found: {args.knowledge_dir}")
        sys.exit(1)
    
    # Load and process
    documents = load_markdown_files(args.knowledge_dir)
    
    if not documents:
        print("❌ Error: No markdown files found")
        sys.exit(1)
    
    chunks = chunk_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    
    embeddings = generate_embeddings(chunks)
    projections = compute_2d_projections(embeddings)
    
    save_outputs(chunks, embeddings, projections, args.output_dir)
    
    print()
    print("✨ Done! Embeddings ready for SparkyAI.")
    print()


if __name__ == "__main__":
    main()
