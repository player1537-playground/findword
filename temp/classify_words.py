#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "tqdm",
# ]
# ///
"""
Word Classification Script

This script processes word files from a gist download and classifies each word
as a noun and/or verb based on which part-of-speech files it appears in.

Input: Word files from temp/raw_words/ with format "pos=<part>,lang=en,length=<n>.txt"
Output: temp/words_classified.csv with columns: word, noun, verb

Author: Claude
"""

import argparse
import re
from pathlib import Path
from typing import Dict, Set, Tuple
from collections import defaultdict
import pandas as pd
from tqdm import tqdm


def parse_filename(filename: str) -> Tuple[str, str, int]:
    """
    Parse filename to extract part-of-speech, language, and word length.

    Args:
        filename: Filename in format "pos=<part>,lang=<lang>,length=<n>.txt"

    Returns:
        Tuple of (pos, lang, length)

    Example:
        >>> parse_filename("pos=noun,lang=en,length=3.txt")
        ('noun', 'en', 3)
    """
    pattern = r"pos=(\w+),lang=(\w+),length=(\d+)\.txt"
    match = re.match(pattern, filename)

    if not match:
        raise ValueError(f"Invalid filename format: {filename}")

    pos, lang, length = match.groups()
    return pos, lang, int(length)


def extract_word_from_line(line: str) -> str:
    """
    Extract the word from a line in format "word: definition".

    Args:
        line: A line from the word file

    Returns:
        The word (lowercase, stripped)

    Example:
        >>> extract_word_from_line("run: To move quickly on foot")
        'run'
    """
    if ':' not in line:
        return None

    word = line.split(':', 1)[0].strip().lower()
    return word if word else None


def process_word_files(input_dir: Path) -> Dict[str, Set[str]]:
    """
    Process all word files and track which parts of speech each word appears in.

    Args:
        input_dir: Directory containing word files

    Returns:
        Dictionary mapping each word to a set of parts of speech it can be
    """
    word_pos_map = defaultdict(set)

    # Get all .txt files in the directory
    word_files = sorted(input_dir.glob("*.txt"))

    if not word_files:
        raise FileNotFoundError(f"No word files found in {input_dir}")

    print(f"Found {len(word_files)} word files to process")

    for filepath in tqdm(word_files, desc="Processing files"):
        # Skip empty files
        if filepath.stat().st_size == 0:
            continue

        try:
            pos, lang, length = parse_filename(filepath.name)
        except ValueError as e:
            print(f"Warning: {e}")
            continue

        # Only process English words and noun/verb classifications
        if lang != 'en' or pos not in ['noun', 'verb']:
            continue

        # Read and process the file
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                word = extract_word_from_line(line.strip())
                if word:
                    word_pos_map[word].add(pos)

    return dict(word_pos_map)


def classify_words(word_pos_map: Dict[str, Set[str]]) -> pd.DataFrame:
    """
    Convert word-to-POS mapping into a classified DataFrame.

    Args:
        word_pos_map: Dictionary mapping words to their parts of speech

    Returns:
        DataFrame with columns: word, noun, verb
    """
    records = []

    for word in tqdm(sorted(word_pos_map.keys()), desc="Classifying words"):
        pos_set = word_pos_map[word]

        records.append({
            'word': word,
            'noun': 'Y' if 'noun' in pos_set else 'N',
            'verb': 'Y' if 'verb' in pos_set else 'N'
        })

    return pd.DataFrame(records)


def print_statistics(df: pd.DataFrame) -> None:
    """
    Print statistics about the classified words.

    Args:
        df: DataFrame with classified words
    """
    total_words = len(df)
    nouns_only = len(df[(df['noun'] == 'Y') & (df['verb'] == 'N')])
    verbs_only = len(df[(df['noun'] == 'N') & (df['verb'] == 'Y')])
    both = len(df[(df['noun'] == 'Y') & (df['verb'] == 'Y')])

    print("\n" + "="*60)
    print("WORD CLASSIFICATION STATISTICS")
    print("="*60)
    print(f"Total unique words:     {total_words:,}")
    print(f"Nouns only:             {nouns_only:,} ({nouns_only/total_words*100:.1f}%)")
    print(f"Verbs only:             {verbs_only:,} ({verbs_only/total_words*100:.1f}%)")
    print(f"Both noun and verb:     {both:,} ({both/total_words*100:.1f}%)")
    print("="*60)

    # Print sample words that are both noun and verb
    both_words = df[(df['noun'] == 'Y') & (df['verb'] == 'Y')]['word'].tolist()
    if both_words:
        print(f"\nSample words that are both noun and verb (first 20):")
        print(", ".join(both_words[:20]))

    print()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Classify words as nouns and/or verbs based on POS files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --input-dir data/words --output results.csv
  %(prog)s --verbose
        """
    )

    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path(__file__).parent / 'raw_words',
        help='Directory containing word files (default: temp/raw_words/)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path(__file__).parent / 'words_classified.csv',
        help='Output CSV file path (default: temp/words_classified.csv)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print verbose output'
    )

    args = parser.parse_args()

    # Validate input directory exists
    if not args.input_dir.exists():
        parser.error(f"Input directory does not exist: {args.input_dir}")

    print(f"Input directory: {args.input_dir}")
    print(f"Output file: {args.output}")
    print()

    # Process word files
    word_pos_map = process_word_files(args.input_dir)

    if not word_pos_map:
        print("Error: No words were extracted from the files")
        return 1

    # Classify words
    df = classify_words(word_pos_map)

    # Print statistics
    print_statistics(df)

    # Save to CSV
    print(f"Saving results to {args.output}...")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Successfully saved {len(df):,} words to {args.output}")

    # Print sample of the output
    print("\nFirst 10 rows of output:")
    print(df.head(10).to_string(index=False))

    return 0


if __name__ == '__main__':
    exit(main())
