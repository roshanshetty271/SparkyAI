from pathlib import Path
import os

cwd = os.getcwd()
print(f"CWD: {cwd}")

rel_path = "../../data/embeddings"
p = Path(rel_path)
print(f"Resolved path: {p.resolve()}")
print(f"Exists: {p.exists()}")

emb_file = p / "embeddings.npy"
print(f"Embeddings file: {emb_file.resolve()}")
print(f"Exists: {emb_file.exists()}")
