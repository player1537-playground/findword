#!/usr/bin/env python3
"""
Word List Extraction Script

This script reads word list files from the gist and extracts just the words
(ignoring definitions) into a consolidated format.

Usage:
    python extract_words.py [--output OUTPUT_DIR] [--format FORMAT]

Formats:
    - json: JSON format with metadata
    - txt: Plain text, one word per line
    - csv: CSV format with word, POS, and length columns
"""

import os
import re
import json
import csv
import argparse
from collections import defaultdict
from pathlib import Path


class WordListExtractor:
    """Extract and process word lists from gist files."""

    def __init__(self, source_dir='temp/raw_words'):
        """
        Initialize the extractor.

        Args:
            source_dir: Directory containing the raw word list files
        """
        self.source_dir = Path(source_dir)
        self.words_by_pos = defaultdict(lambda: defaultdict(set))
        self.all_words = set()

    def parse_filename(self, filename):
        """
        Parse the filename to extract metadata.

        Args:
            filename: Name of the file to parse

        Returns:
            dict with 'pos', 'lang', and 'length' keys, or None if invalid
        """
        match = re.match(r'pos=(\w+),lang=(\w+),length=(\d+)\.txt', filename)
        if match:
            pos, lang, length = match.groups()
            return {
                'pos': pos,
                'lang': lang,
                'length': int(length)
            }
        return None

    def extract_word_from_line(self, line):
        """
        Extract the word from a definition line.

        Args:
            line: Line containing "word: definition"

        Returns:
            The word (before the colon), or None if invalid
        """
        line = line.strip()
        if ':' in line:
            word = line.split(':', 1)[0].strip()
            return word
        return None

    def load_file(self, filepath):
        """
        Load words from a single file.

        Args:
            filepath: Path to the file to load

        Returns:
            set of words found in the file
        """
        words = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = self.extract_word_from_line(line)
                    if word:
                        words.add(word)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        return words

    def load_all_files(self):
        """Load all word list files from the source directory."""
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        files_processed = 0
        for filepath in sorted(self.source_dir.glob('*.txt')):
            metadata = self.parse_filename(filepath.name)
            if metadata:
                words = self.load_file(filepath)
                if words:
                    pos = metadata['pos']
                    length = metadata['length']
                    self.words_by_pos[pos][length] = words
                    self.all_words.update(words)
                    files_processed += 1
                    print(f"Loaded {len(words)} words from {filepath.name}")

        print(f"\nProcessed {files_processed} files")
        print(f"Total unique words: {len(self.all_words)}")
        return files_processed

    def get_statistics(self):
        """Get statistics about the loaded words."""
        stats = {
            'total_words': len(self.all_words),
            'by_pos': {}
        }

        for pos, lengths in self.words_by_pos.items():
            total_for_pos = sum(len(words) for words in lengths.values())
            stats['by_pos'][pos] = {
                'total': total_for_pos,
                'by_length': {length: len(words) for length, words in lengths.items()}
            }

        return stats

    def export_to_json(self, output_path):
        """
        Export words to JSON format with metadata.

        Args:
            output_path: Path to write the JSON file
        """
        data = {
            'metadata': {
                'source': 'https://gist.github.com/player1537/2caccbdd58b42d75cac473be6e9a1a71',
                'total_words': len(self.all_words),
                'parts_of_speech': list(self.words_by_pos.keys())
            },
            'words': {}
        }

        for pos, lengths in self.words_by_pos.items():
            data['words'][pos] = {}
            for length, words in lengths.items():
                data['words'][pos][str(length)] = sorted(words)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"Exported to JSON: {output_path}")

    def export_to_txt(self, output_path):
        """
        Export all words to plain text format (one per line).

        Args:
            output_path: Path to write the text file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for word in sorted(self.all_words):
                f.write(f"{word}\n")

        print(f"Exported to TXT: {output_path}")

    def export_to_csv(self, output_path):
        """
        Export words to CSV format with metadata.

        Args:
            output_path: Path to write the CSV file
        """
        rows = []
        for pos, lengths in self.words_by_pos.items():
            for length, words in lengths.items():
                for word in sorted(words):
                    rows.append({
                        'word': word,
                        'pos': pos,
                        'length': length
                    })

        # Sort by word
        rows.sort(key=lambda x: x['word'])

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['word', 'pos', 'length'])
            writer.writeheader()
            writer.writerows(rows)

        print(f"Exported to CSV: {output_path}")

    def export_by_pos(self, output_dir):
        """
        Export words grouped by part of speech.

        Args:
            output_dir: Directory to write POS-specific files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for pos, lengths in self.words_by_pos.items():
            all_pos_words = set()
            for words in lengths.values():
                all_pos_words.update(words)

            output_path = output_dir / f"{pos}.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                for word in sorted(all_pos_words):
                    f.write(f"{word}\n")

            print(f"Exported {len(all_pos_words)} {pos}s to {output_path}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract words from gist word list files'
    )
    parser.add_argument(
        '--source',
        default='temp/raw_words',
        help='Source directory containing raw word files (default: temp/raw_words)'
    )
    parser.add_argument(
        '--output',
        default='temp/extracted_words',
        help='Output directory for extracted words (default: temp/extracted_words)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'txt', 'csv', 'all'],
        default='all',
        help='Output format (default: all)'
    )

    args = parser.parse_args()

    # Create extractor and load files
    extractor = WordListExtractor(source_dir=args.source)
    extractor.load_all_files()

    # Print statistics
    stats = extractor.get_statistics()
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    print(f"Total unique words: {stats['total_words']}")
    for pos, pos_stats in stats['by_pos'].items():
        print(f"\n{pos.upper()}: {pos_stats['total']} words")
        for length, count in sorted(pos_stats['by_length'].items()):
            print(f"  {length} letters: {count} words")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export in requested format(s)
    print("\n" + "=" * 60)
    print("EXPORTING")
    print("=" * 60)

    if args.format in ['json', 'all']:
        extractor.export_to_json(output_dir / 'words.json')

    if args.format in ['txt', 'all']:
        extractor.export_to_txt(output_dir / 'all_words.txt')

    if args.format in ['csv', 'all']:
        extractor.export_to_csv(output_dir / 'words.csv')

    if args.format == 'all':
        extractor.export_by_pos(output_dir / 'by_pos')

    print("\nExtraction complete!")


if __name__ == '__main__':
    main()
