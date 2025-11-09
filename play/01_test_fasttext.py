#!/usr/bin/env -S uv run --isolated --no-project --script
# %%
# /// script
# dependencies = ["gensim>=4.0.0", "numpy"]
# ///

"""
Test FastText model by loading it and generating embeddings for sample words.

This script demonstrates basic FastText functionality by:
- Loading a pre-trained FastText model
- Generating embeddings for sample words
- Displaying embedding dimensions and values
"""

# %%
import sys
from pathlib import Path
import numpy as np

try:
    from gensim.models import KeyedVectors
except ImportError:
    print("Error: gensim package not found")
    sys.exit(1)

# %%
def load_fasttext_model(model_dir: Path) -> KeyedVectors:
    """
    Load FastText model from the specified directory.

    Args:
        model_dir: Path to directory containing .vec model file

    Returns:
        Loaded FastText model as KeyedVectors

    Raises:
        FileNotFoundError: If no .vec file found in directory
    """
    vec_files = list(model_dir.glob("*.vec"))

    if not vec_files:
        raise FileNotFoundError(
            f"No .vec model file found in {model_dir}. "
            "Please download a FastText model first."
        )

    model_path = vec_files[0]
    print(f"Loading FastText model from: {model_path}")

    model = KeyedVectors.load_word2vec_format(str(model_path))
    print(f"Model loaded successfully!")
    print(f"Model vocabulary size: {len(model)}")

    return model

# %%
def test_embeddings(model: KeyedVectors, words: list[str]) -> None:
    """
    Generate and display embeddings for test words.

    Args:
        model: Loaded FastText model
        words: List of words to embed
    """
    print(f"\n{'='*60}")
    print("Testing FastText Embeddings")
    print(f"{'='*60}\n")

    for word in words:
        embedding = model[word]

        print(f"Word: '{word}'")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  Embedding type: {type(embedding)}")
        print(f"  Embedding shape: {embedding.shape}")
        print(f"  First 10 values: {embedding[:10]}")
        print(f"  L2 norm: {np.linalg.norm(embedding):.4f}")
        print()

# %%
def main():
    """Main execution function."""
    # Determine model directory path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    model_dir = project_root / "data" / "fasttext"

    print(f"Script directory: {script_dir}")
    print(f"Project root: {project_root}")
    print(f"Looking for model in: {model_dir}")
    print()

    try:
        # Load model
        model = load_fasttext_model(model_dir)

        # Test with sample words
        test_words = ["king", "queen"]
        test_embeddings(model, test_words)

        print(f"{'='*60}")
        print("Test completed successfully!")
        print(f"{'='*60}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nTo use this script, download a FastText model:", file=sys.stderr)
        print("  Example: wget https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

# %%
if __name__ == "__main__":
    main()
