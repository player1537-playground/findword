"""
Django management command to load words from CSV into the database.

This command reads words.csv and populates the Word model with words,
their part-of-speech tags, and embeddings.
"""
import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm

from findword_api.models import Word


class Command(BaseCommand):
    """
    Management command to load words from CSV file into the database.

    Usage:
        python manage.py loadwords
        python manage.py loadwords --dry-run --limit 10
        python manage.py loadwords --clear
        python manage.py loadwords --file path/to/custom.csv
    """
    help = 'Load words from CSV file into the database'

    def __init__(self):
        super().__init__()
        self.stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
        }
        self.error_logger = None

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            '--file',
            type=str,
            default='data/words.csv',
            help='Path to CSV file (default: data/words.csv)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing words before loading'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be loaded without actually loading'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Only load first N words (for testing)'
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch (default: 1000)'
        )

    def setup_error_logging(self):
        """Set up error logging to file."""
        log_dir = Path('temp')
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'loadwords_errors.log'

        # Create logger
        self.error_logger = logging.getLogger('loadwords')
        self.error_logger.setLevel(logging.ERROR)

        # Create file handler
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.ERROR)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        # Add handler to logger
        self.error_logger.addHandler(file_handler)

        return log_file

    def parse_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse a CSV row into word data.

        Args:
            row: Dictionary with keys: word, noun, verb, embd

        Returns:
            Dictionary with parsed data

        Raises:
            ValueError: If row data is invalid
        """
        # Get word (remove surrounding quotes if present)
        word = row['word'].strip().strip("'\"")
        if not word:
            raise ValueError("Empty word")

        # Parse noun/verb flags
        noun = row['noun'].strip().upper()
        verb = row['verb'].strip().upper()

        if noun not in ('Y', 'N'):
            raise ValueError(f"Invalid noun value: {noun}")
        if verb not in ('Y', 'N'):
            raise ValueError(f"Invalid verb value: {verb}")

        is_noun = noun == 'Y'
        is_verb = verb == 'Y'

        # Parse embedding
        embd_str = row['embd'].strip()
        try:
            embedding = json.loads(embd_str)
            if not isinstance(embedding, list):
                raise ValueError("Embedding must be a list")
            if not embedding:
                raise ValueError("Embedding cannot be empty")
            # Validate all elements are numbers
            if not all(isinstance(x, (int, float)) for x in embedding):
                raise ValueError("Embedding must contain only numbers")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in embedding: {e}")

        return {
            'word': word,
            'is_noun': is_noun,
            'is_verb': is_verb,
            'embedding': embedding,
        }

    def read_csv_file(self, file_path: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Read and parse CSV file.

        Args:
            file_path: Path to CSV file
            limit: Maximum number of rows to read

        Returns:
            List of parsed word data dictionaries

        Raises:
            CommandError: If file cannot be read
        """
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(f"Reading CSV file: {file_path}")

        words_data = []
        errors = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers
            required_headers = {'word', 'noun', 'verb', 'embd'}
            if not required_headers.issubset(reader.fieldnames):
                raise CommandError(
                    f"CSV must have headers: {required_headers}. "
                    f"Found: {reader.fieldnames}"
                )

            for idx, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                if limit and len(words_data) >= limit:
                    break

                try:
                    word_data = self.parse_csv_row(row)
                    words_data.append(word_data)
                except (ValueError, KeyError) as e:
                    error_msg = f"Line {idx}: {e} - Row: {row}"
                    errors.append(error_msg)
                    self.error_logger.error(error_msg)
                    self.stats['errors'] += 1

        if errors:
            self.stdout.write(
                self.style.WARNING(
                    f"Encountered {len(errors)} errors while parsing CSV. "
                    f"Check temp/loadwords_errors.log for details."
                )
            )

        return words_data

    def load_words_batch(self, words_data: List[Dict[str, Any]], dry_run: bool = False):
        """
        Load words into database using update_or_create for each word.

        Args:
            words_data: List of word data dictionaries
            dry_run: If True, don't actually save to database
        """
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}Processing {len(words_data)} words..."
        )

        with tqdm(total=len(words_data), desc="Loading words", ncols=80) as pbar:
            for word_data in words_data:
                try:
                    if dry_run:
                        # Just check if word exists
                        exists = Word.objects.filter(word=word_data['word']).exists()
                        if exists:
                            self.stats['updated'] += 1
                        else:
                            self.stats['created'] += 1
                    else:
                        # Actually create or update
                        word, created = Word.objects.update_or_create(
                            word=word_data['word'],
                            defaults={
                                'is_noun': word_data['is_noun'],
                                'is_verb': word_data['is_verb'],
                                'embedding': word_data['embedding'],
                            }
                        )
                        if created:
                            self.stats['created'] += 1
                        else:
                            self.stats['updated'] += 1

                except Exception as e:
                    error_msg = f"Error processing word '{word_data['word']}': {e}"
                    self.error_logger.error(error_msg)
                    self.stats['errors'] += 1
                    if not dry_run:
                        self.stdout.write(self.style.ERROR(f"  {error_msg}"))

                pbar.update(1)

    def print_summary(self, dry_run: bool = False):
        """Print summary of operations."""
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f"{'[DRY RUN] ' if dry_run else ''}Load Complete!"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  Created:  {self.stats['created']}")
        self.stdout.write(f"  Updated:  {self.stats['updated']}")
        self.stdout.write(f"  Errors:   {self.stats['errors']}")
        self.stdout.write(f"  Total:    {self.stats['created'] + self.stats['updated']}")

        if self.stats['errors'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\nCheck temp/loadwords_errors.log for error details."
                )
            )

        # Print database statistics
        if not dry_run:
            total_words = Word.objects.count()
            noun_count = Word.objects.filter(is_noun=True).count()
            verb_count = Word.objects.filter(is_verb=True).count()
            both_count = Word.objects.filter(is_noun=True, is_verb=True).count()

            self.stdout.write(self.style.SUCCESS("\nDatabase Statistics:"))
            self.stdout.write(f"  Total words:     {total_words}")
            self.stdout.write(f"  Nouns:           {noun_count}")
            self.stdout.write(f"  Verbs:           {verb_count}")
            self.stdout.write(f"  Both noun/verb:  {both_count}")

    def handle(self, *args, **options):
        """Main command handler."""
        file_path = options['file']
        clear = options['clear']
        dry_run = options['dry_run']
        limit = options['limit']
        chunk_size = options['chunk_size']

        # Setup error logging
        log_file = self.setup_error_logging()
        self.stdout.write(f"Error logging to: {log_file}")

        # Display options
        self.stdout.write(self.style.SUCCESS("\nLoad Words Command"))
        self.stdout.write(f"  File:       {file_path}")
        self.stdout.write(f"  Clear:      {clear}")
        self.stdout.write(f"  Dry run:    {dry_run}")
        self.stdout.write(f"  Limit:      {limit if limit else 'None (all rows)'}")
        self.stdout.write(f"  Chunk size: {chunk_size}")
        self.stdout.write("")

        # Clear database if requested
        if clear and not dry_run:
            confirm = input(
                "Are you sure you want to delete all existing words? (yes/no): "
            )
            if confirm.lower() == 'yes':
                count = Word.objects.count()
                Word.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f"Deleted {count} existing words.")
                )
            else:
                self.stdout.write("Clear operation cancelled.")
                return

        try:
            # Read CSV file
            words_data = self.read_csv_file(file_path, limit)

            if not words_data:
                self.stdout.write(self.style.WARNING("No valid words to load."))
                return

            self.stdout.write(
                self.style.SUCCESS(f"Successfully parsed {len(words_data)} words.")
            )

            # Load words into database
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "\n*** DRY RUN MODE - No data will be saved ***\n"
                    )
                )

            self.load_words_batch(words_data, dry_run)

            # Print summary
            self.print_summary(dry_run)

        except CommandError:
            raise
        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR("\n\nOperation cancelled by user."))
            self.stdout.write(f"  Created: {self.stats['created']}")
            self.stdout.write(f"  Updated: {self.stats['updated']}")
            self.stdout.write(f"  Errors:  {self.stats['errors']}")
            raise
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nUnexpected error: {e}"))
            raise CommandError(str(e))
