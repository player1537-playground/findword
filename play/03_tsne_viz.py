#!/usr/bin/env -S uv run --isolated --no-project --script
# %%
# /// script
# dependencies = ["fasttext-wheel", "numpy", "scikit-learn", "matplotlib", "pandas"]
# ///

"""
Visualize word embeddings using t-SNE dimensionality reduction.

This script reads words from a text file, generates FastText embeddings,
applies PCA and t-SNE for dimensionality reduction, and creates a 2D
scatter plot visualization with word labels.
"""

# %%
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

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
    print()

    return model

# %%
def read_words(input_file: Path, line_limit: int) -> List[str]:
    """
    Read words from input file with optional line limit.

    Args:
        input_file: Path to input text file
        line_limit: Maximum number of words to read (0 = no limit)

    Returns:
        List of words (whitespace stripped)

    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    words = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line_limit > 0 and i >= line_limit:
                break
            word = line.strip()
            if word:
                words.append(word)

    print(f"Read {len(words)} words from {input_file}")
    if line_limit > 0:
        print(f"  (limited to first {line_limit} lines)")
    print()

    return words

# %%
def generate_embeddings(
    model: fasttext.FastText._FastText,
    words: List[str]
) -> Tuple[List[str], np.ndarray]:
    """
    Generate embeddings for a list of words.

    Args:
        model: Loaded FastText model
        words: List of words to embed

    Returns:
        Tuple of (words, embeddings_matrix)
    """
    print(f"Generating embeddings for {len(words)} words...")

    embeddings = []
    for word in words:
        embedding = model.get_word_vector(word)
        embeddings.append(embedding)

    embeddings_matrix = np.array(embeddings)

    print(f"Generated embeddings matrix:")
    print(f"  Shape: {embeddings_matrix.shape}")
    print(f"  Dimensions: {embeddings_matrix.shape[1]}")
    print(f"  Number of words: {embeddings_matrix.shape[0]}")
    print()

    return words, embeddings_matrix

# %%
def reduce_dimensions(embeddings: np.ndarray, n_components: int = 8) -> np.ndarray:
    """
    Apply PCA to reduce embedding dimensions.

    Args:
        embeddings: Original embeddings matrix
        n_components: Target number of dimensions

    Returns:
        Reduced embeddings matrix
    """
    print(f"Applying PCA to reduce dimensions...")
    print(f"  Original dimensions: {embeddings.shape[1]}")
    print(f"  Target dimensions: {n_components}")

    pca = PCA(n_components=n_components)
    reduced = pca.fit_transform(embeddings)

    variance_explained = pca.explained_variance_ratio_.sum()
    print(f"  Reduced dimensions: {reduced.shape[1]}")
    print(f"  Variance explained: {variance_explained:.2%}")
    print()

    return reduced

# %%
def apply_tsne(embeddings: np.ndarray, perplexity: int = 30) -> np.ndarray:
    """
    Apply t-SNE for 2D visualization.

    Args:
        embeddings: Input embeddings matrix
        perplexity: t-SNE perplexity parameter

    Returns:
        2D coordinates for visualization
    """
    print(f"Applying t-SNE for 2D visualization...")
    print(f"  Input dimensions: {embeddings.shape[1]}")
    print(f"  Number of samples: {embeddings.shape[0]}")
    print(f"  Perplexity: {perplexity}")

    # Adjust perplexity if necessary
    max_perplexity = (embeddings.shape[0] - 1) // 3
    if perplexity > max_perplexity:
        perplexity = max_perplexity
        print(f"  Adjusted perplexity to: {perplexity}")

    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        random_state=42,
        n_iter=1000
    )
    coords_2d = tsne.fit_transform(embeddings)

    print(f"  Output dimensions: {coords_2d.shape[1]}")
    print(f"  Final shape: {coords_2d.shape}")
    print()

    return coords_2d

# %%
def create_visualization(
    words: List[str],
    coords_2d: np.ndarray,
    output_file: Path
) -> None:
    """
    Create and save scatter plot visualization.

    Args:
        words: List of words
        coords_2d: 2D coordinates for each word
        output_file: Path to save the visualization
    """
    print(f"Creating visualization...")

    plt.figure(figsize=(12, 10))

    # Scatter plot
    plt.scatter(coords_2d[:, 0], coords_2d[:, 1], alpha=0.6, s=100)

    # Add word labels
    for i, word in enumerate(words):
        plt.annotate(
            word,
            xy=(coords_2d[i, 0], coords_2d[i, 1]),
            xytext=(5, 2),
            textcoords='offset points',
            fontsize=9,
            alpha=0.8
        )

    plt.title(
        f't-SNE Visualization of FastText Word Embeddings\n({len(words)} words)',
        fontsize=14,
        fontweight='bold'
    )
    plt.xlabel('t-SNE Dimension 1', fontsize=12)
    plt.ylabel('t-SNE Dimension 2', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved visualization to: {output_file}")
    print(f"  Format: {output_file.suffix}")
    print(f"  File size: {output_file.stat().st_size / 1024:.2f} KB")

# %%
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Visualize word embeddings using t-SNE",
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
        '-l', '--line-limit',
        type=int,
        dest='line_limit',
        default=100,
        help="Maximum number of words to visualize (0 = no limit)"
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        dest='output_image',
        default=Path('tsne_visualization.png'),
        help="Output image file path"
    )

    parser.add_argument(
        '-m', '--model-dir',
        type=Path,
        dest='model_dir',
        default=None,
        help="Directory containing FastText .bin model (default: data/fasttext/)"
    )

    parser.add_argument(
        '-p', '--perplexity',
        type=int,
        default=30,
        help="t-SNE perplexity parameter"
    )

    parser.add_argument(
        '--pca-dims',
        type=int,
        default=8,
        dest='pca_dims',
        help="Number of PCA dimensions before t-SNE"
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
    print("FastText Word Embedding t-SNE Visualization")
    print(f"{'='*60}")
    print(f"Input file: {args.input_file}")
    print(f"Line limit: {args.line_limit if args.line_limit > 0 else 'No limit'}")
    print(f"Output image: {args.output_image}")
    print(f"Model directory: {model_dir}")
    print(f"PCA dimensions: {args.pca_dims}")
    print(f"t-SNE perplexity: {args.perplexity}")
    print(f"{'='*60}\n")

    try:
        # Load model
        model = load_fasttext_model(model_dir)

        # Read words
        words = read_words(args.input_file, args.line_limit)

        if len(words) == 0:
            print("Error: No words found in input file", file=sys.stderr)
            sys.exit(1)

        if len(words) < 3:
            print("Error: Need at least 3 words for visualization", file=sys.stderr)
            sys.exit(1)

        # Generate embeddings
        words, embeddings = generate_embeddings(model, words)

        # Reduce dimensions with PCA
        embeddings_pca = reduce_dimensions(embeddings, args.pca_dims)

        # Apply t-SNE
        coords_2d = apply_tsne(embeddings_pca, args.perplexity)

        # Create visualization
        create_visualization(words, coords_2d, args.output_image)

        print(f"\n{'='*60}")
        print("Visualization completed successfully!")
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
