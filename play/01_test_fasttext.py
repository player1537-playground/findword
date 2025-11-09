#!/usr/bin/env -S uv run --isolated --no-project --script
# %%
# /// script
# dependencies = ["fasttext-wheel", "numpy"]
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
    import fasttext
except ImportError:
    print("Error: fasttext-wheel package not found")
    sys.exit(1)

# %%
def load_fasttext_model(model_dir: Path) -> fasttext.FastText._FastText:
    """
    Load FastText model from the specified directory.

    Args:
        model_dir: Path to directory containing .bin model file

    Returns:
        Loaded FastText model

    Raises:
        FileNotFoundError: If no .bin file found in directory
    """
    bin_files = list(model_dir.glob("*.bin"))

    if not bin_files:
        raise FileNotFoundError(
            f"No .bin model file found in {model_dir}. "
            "Please download a FastText model first."
        )

    model_path = bin_files[0]
    print(f"Loading FastText model from: {model_path}")

    model = fasttext.load_model(str(model_path))
    print(f"Model loaded successfully!")
    print(f"Model vocabulary size: {len(model.words)}")

    return model

# %%
def test_embeddings(model: fasttext.FastText._FastText, words: list[str]) -> None:
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
        embedding = model.get_word_vector(word)

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
