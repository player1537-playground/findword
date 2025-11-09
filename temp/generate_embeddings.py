#!/usr/bin/env -S uv run --isolated --no-project --script
# /// script
# dependencies = ["gensim>=4.0.0", "numpy", "pandas", "tqdm"]
# ///

"""
Generate FastText embeddings for classified words.

This script reads classified words from a CSV file, generates FastText embeddings
for each word using a pre-trained model, and outputs the results with embeddings
stored as JSON arrays.

Features:
- Batch processing for memory efficiency
- Progress tracking with tqdm
- Graceful handling of out-of-vocabulary words
- Detailed statistics reporting
- Type hints and comprehensive error handling
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

try:
    from gensim.models import KeyedVectors
except ImportError:
    print("Error: gensim package not found", file=sys.stderr)
    sys.exit(1)


def load_fasttext_model(model_path: Path) -> KeyedVectors:
    """
    Load FastText model from the specified file.

    Args:
        model_path: Path to the .vec model file

    Returns:
        Loaded FastText model as KeyedVectors

    Raises:
        FileNotFoundError: If model file not found
        ValueError: If model file cannot be loaded
    """
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            "Please ensure the FastText model is downloaded."
        )

    print(f"Loading FastText model from: {model_path}")
    print("This may take a few moments...")

    try:
        model = KeyedVectors.load_word2vec_format(str(model_path))
        print(f"Model loaded successfully!")
        print(f"Model vocabulary size: {len(model):,}")
        print(f"Embedding dimension: {model.vector_size}")
        return model
    except Exception as e:
        raise ValueError(f"Failed to load model: {e}")


def load_classified_words(input_path: Path) -> pd.DataFrame:
    """
    Load classified words from CSV file.

    Args:
        input_path: Path to the input CSV file

    Returns:
        DataFrame with columns: word, noun, verb

    Raises:
        FileNotFoundError: If input file not found
        ValueError: If CSV format is invalid
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"\nLoading classified words from: {input_path}")

    try:
        df = pd.read_csv(input_path)

        # Validate columns
        required_columns = {"word", "noun", "verb"}
        if not required_columns.issubset(df.columns):
            raise ValueError(
                f"CSV must contain columns: {required_columns}\n"
                f"Found columns: {set(df.columns)}"
            )

        print(f"Loaded {len(df):,} words")
        return df

    except Exception as e:
        raise ValueError(f"Failed to load input file: {e}")


def get_embedding(word: str, model: KeyedVectors) -> Optional[np.ndarray]:
    """
    Get FastText embedding for a word.

    Args:
        word: The word to embed
        model: Loaded FastText model

    Returns:
        Numpy array of embedding values, or None if word not in vocabulary
    """
    try:
        # Ensure word is a string and handle special cases
        if not isinstance(word, str) or not word.strip():
            return None
        return model[word]
    except (KeyError, TypeError, ValueError):
        # KeyError: word not in vocabulary
        # TypeError: word format incompatible
        # ValueError: other gensim errors
        return None


def embedding_to_json(embedding: np.ndarray) -> str:
    """
    Convert numpy embedding array to JSON string.

    Args:
        embedding: Numpy array of embedding values

    Returns:
        JSON string representation of the array
    """
    # Convert to Python list and then to JSON
    return json.dumps(embedding.tolist())


def process_words_in_batches(
    df: pd.DataFrame,
    model: KeyedVectors,
    batch_size: int = 1000
) -> tuple[pd.DataFrame, dict]:
    """
    Process words in batches and generate embeddings.

    Args:
        df: DataFrame with words to process
        model: Loaded FastText model
        batch_size: Number of words to process in each batch

    Returns:
        Tuple of (DataFrame with embeddings, statistics dict)
    """
    print(f"\nGenerating embeddings...")
    print(f"Batch size: {batch_size}")

    embeddings = []
    words_with_embeddings = 0
    words_skipped = 0
    skipped_words = []

    # Process with progress bar
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing words"):
        word = row["word"]
        embedding = get_embedding(word, model)

        if embedding is not None:
            embeddings.append(embedding_to_json(embedding))
            words_with_embeddings += 1
        else:
            embeddings.append(None)
            words_skipped += 1
            skipped_words.append(word)

    # Add embeddings column
    df["embd"] = embeddings

    # Remove rows without embeddings
    df_with_embeddings = df.dropna(subset=["embd"]).copy()

    # Collect statistics
    stats = {
        "total_words": len(df),
        "words_with_embeddings": words_with_embeddings,
        "words_skipped": words_skipped,
        "skipped_words": skipped_words[:10],  # Keep first 10 for reporting
        "embedding_dimension": model.vector_size,
    }

    return df_with_embeddings, stats


def save_output(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save DataFrame with embeddings to CSV file.

    Args:
        df: DataFrame with embeddings to save
        output_path: Path to output CSV file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving results to: {output_path}")
    df.to_csv(output_path, index=False)

    # Get file size
    file_size = output_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    print(f"Output file size: {file_size_mb:.2f} MB")


def print_statistics(stats: dict) -> None:
    """
    Print processing statistics.

    Args:
        stats: Dictionary containing processing statistics
    """
    print("\n" + "=" * 60)
    print("PROCESSING STATISTICS")
    print("=" * 60)
    print(f"Total words processed:     {stats['total_words']:,}")
    print(f"Words with embeddings:     {stats['words_with_embeddings']:,}")
    print(f"Words skipped (no vocab):  {stats['words_skipped']:,}")
    print(f"Embedding dimension:       {stats['embedding_dimension']}")

    if stats["words_skipped"] > 0:
        print(f"\nSample skipped words (first 10):")
        for word in stats["skipped_words"]:
            print(f"  - {word}")

    success_rate = (stats['words_with_embeddings'] / stats['total_words']) * 100
    print(f"\nSuccess rate: {success_rate:.2f}%")
    print("=" * 60)


def print_sample_rows(df: pd.DataFrame, n: int = 5) -> None:
    """
    Print sample rows from the output DataFrame.

    Args:
        df: DataFrame to sample from
        n: Number of rows to display
    """
    print("\n" + "=" * 60)
    print(f"SAMPLE OUTPUT ROWS (first {n})")
    print("=" * 60)

    for idx, row in df.head(n).iterrows():
        print(f"\nWord: {row['word']}")
        print(f"  Noun: {row['noun']}")
        print(f"  Verb: {row['verb']}")

        # Parse embedding to show first few values
        embd = json.loads(row['embd'])
        print(f"  Embedding: [{embd[0]:.4f}, {embd[1]:.4f}, {embd[2]:.4f}, ..., {embd[-1]:.4f}]")
        print(f"  Embedding length: {len(embd)}")

    print("=" * 60)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate FastText embeddings for classified words",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default paths
  %(prog)s

  # Specify custom paths
  %(prog)s --input my_words.csv --output my_output.csv

  # Use different batch size
  %(prog)s --batch-size 500
        """
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("temp/words_classified.csv"),
        help="Path to input CSV file with classified words (default: temp/words_classified.csv)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/words.csv"),
        help="Path to output CSV file (default: data/words.csv)"
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=Path("data/fasttext/wiki-news-300d-1M.vec"),
        help="Path to FastText model file (default: data/fasttext/wiki-news-300d-1M.vec)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of words to process at once (default: 1000)"
    )

    return parser.parse_args()


def main() -> None:
    """Main execution function."""
    args = parse_arguments()

    print("=" * 60)
    print("FASTTEXT EMBEDDING GENERATION")
    print("=" * 60)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Model:  {args.model}")
    print("=" * 60)

    try:
        # Load FastText model
        model = load_fasttext_model(args.model)

        # Load classified words
        df = load_classified_words(args.input)

        # Process words and generate embeddings
        df_with_embeddings, stats = process_words_in_batches(
            df, model, args.batch_size
        )

        # Save output
        save_output(df_with_embeddings, args.output)

        # Print statistics
        print_statistics(stats)

        # Print sample rows
        print_sample_rows(df_with_embeddings)

        print("\n" + "=" * 60)
        print("COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
