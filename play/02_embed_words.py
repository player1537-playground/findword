#!/usr/bin/env -S uv run --isolated --no-project --script
# %%
# /// script
# dependencies = ["gensim>=4.0.0", "numpy", "pandas"]
# ///

"""
Generate FastText embeddings for a list of words and save to CSV.

This script reads words from a text file (one per line), generates embeddings
using a pre-trained FastText model, and saves the results to a CSV file with
word and embedding columns.
"""

# %%
import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

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
    print()

    return model

# %%
def read_words(input_file: Path) -> List[str]:
    """
    Read words from input file, one word per line.

    Args:
        input_file: Path to input text file

    Returns:
        List of words (whitespace stripped)

    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]

    print(f"Read {len(words)} words from {input_file}")
    return words

# %%
def generate_embeddings(
    model: KeyedVectors,
    words: List[str]
) -> List[Tuple[str, np.ndarray]]:
    """
    Generate embeddings for a list of words with progress indication.

    Args:
        model: Loaded FastText model
        words: List of words to embed

    Returns:
        List of (word, embedding) tuples
    """
    embeddings = []
    total = len(words)

    print(f"Generating embeddings for {total} words...")

    for i, word in enumerate(words, 1):
        embedding = model[word]
        embeddings.append((word, embedding))

        # Progress indication
        if i % 100 == 0 or i == total:
            print(f"  Progress: {i}/{total} ({100*i/total:.1f}%)")

    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0][1])}")
    print()

    return embeddings

# %%
def save_embeddings(
    embeddings: List[Tuple[str, np.ndarray]],
    output_file: Path
) -> None:
    """
    Save embeddings to CSV file.

    Args:
        embeddings: List of (word, embedding) tuples
        output_file: Path to output CSV file
    """
    # Convert embeddings to JSON arrays for CSV storage
    data = {
        'word': [word for word, _ in embeddings],
        'embedding': [json.dumps(emb.tolist()) for _, emb in embeddings]
    }

    df = pd.DataFrame(data)

    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_file, index=False)
    print(f"Saved embeddings to: {output_file}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  File size: {output_file.stat().st_size / 1024:.2f} KB")

# %%
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate FastText embeddings for words from a text file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'input_file',
        type=Path,
        nargs='?',
        default=Path('words.txt'),
        help="Input text file with words (one per line)"
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        dest='output_file',
        default=Path('embeddings.csv'),
        help="Output CSV file for embeddings"
    )

    parser.add_argument(
        '-m', '--model-dir',
        type=Path,
        dest='model_dir',
        default=None,
        help="Directory containing FastText .vec model (default: data/fasttext/)"
    )

    return parser.parse_args()

# %%
def main():
    """Main execution function."""
    args = parse_args()

    # Determine model directory
    if args.model_dir is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        model_dir = project_root / "data" / "fasttext"
    else:
        model_dir = args.model_dir

    print(f"{'='*60}")
    print("FastText Word Embedding Generator")
    print(f"{'='*60}")
    print(f"Input file: {args.input_file}")
    print(f"Output file: {args.output_file}")
    print(f"Model directory: {model_dir}")
    print(f"{'='*60}\n")

    try:
        # Load model
        model = load_fasttext_model(model_dir)

        # Read words
        words = read_words(args.input_file)

        # Generate embeddings
        embeddings = generate_embeddings(model, words)

        # Save to CSV
        save_embeddings(embeddings, args.output_file)

        print(f"\n{'='*60}")
        print("Embedding generation completed successfully!")
        print(f"{'='*60}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

# %%
if __name__ == "__main__":
    main()
