# Word Lists from Gist

## Source
Downloaded from: https://gist.github.com/player1537/2caccbdd58b42d75cac473be6e9a1a71

## File Format

All files follow the naming convention:
```
pos=<part-of-speech>,lang=<language>,length=<word-length>.txt
```

Where:
- `part-of-speech`: The grammatical category (e.g., noun, verb)
- `language`: ISO language code (e.g., en for English)
- `word-length`: Number of letters in the words

## Content Format

Each file contains dictionary-style entries with one definition per line:
```
word: Definition or description of the word.
```

Some words have multiple definitions, appearing on separate lines.

## Downloaded Files

### Nouns

| Filename | Word Length | Entries | Unique Words |
|----------|-------------|---------|--------------|
| pos=noun,lang=en,length=3.txt | 3 letters | 16,569 | 6,990 |
| pos=noun,lang=en,length=4.txt | 4 letters | 201 | 41 |
| pos=noun,lang=en,length=5.txt | 5 letters | 0 | 0 |
| pos=noun,lang=en,length=6.txt | 6 letters | 0 | 0 |
| pos=noun,lang=en,length=7.txt | 7 letters | 0 | 0 |
| pos=noun,lang=en,length=8.txt | 8 letters | 55,718 | 41,606 |

**Noun Totals:**
- Files: 6
- Total entries: 72,489
- Unique words: 48,637

### Verbs

| Filename | Word Length | Entries | Unique Words |
|----------|-------------|---------|--------------|
| pos=verb,lang=en,length=3.txt | 3 letters | 2,969 | 900 |
| pos=verb,lang=en,length=4.txt | 4 letters | 10,307 | 3,185 |
| pos=verb,lang=en,length=5.txt | 5 letters | 12,535 | 6,143 |
| pos=verb,lang=en,length=6.txt | 6 letters | 17,518 | 11,495 |
| pos=verb,lang=en,length=7.txt | 7 letters | 23,773 | 18,274 |
| pos=verb,lang=en,length=8.txt | 8 letters | 25,717 | 21,751 |

**Verb Totals:**
- Files: 6
- Total entries: 92,819
- Unique words: 61,748

## Overall Statistics

- **Total files downloaded:** 12
- **Total entries:** 165,308
- **Total unique words:** 110,385
- **Parts of speech available:** noun, verb
- **Word lengths available:** 3-8 letters
- **Language:** English (en)

## Notes

- Some noun files (length 5, 6, 7) are empty
- The noun length=4 file has significantly fewer entries than expected
- Most complete data exists for 3-letter and 8-letter nouns
- Verb files have more consistent coverage across all word lengths
- Each word may have multiple definitions, so "entries" count all definitions while "unique words" counts distinct words
