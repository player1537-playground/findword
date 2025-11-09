#!/usr/bin/env python3
"""
Execute play scripts and create Jupyter notebooks with captured output.
"""
import subprocess
import json
from pathlib import Path
import sys

def create_notebook_with_output(py_file: Path, output_text: str):
    """Create a Jupyter notebook from a Python file with execution output."""

    # Read the Python file
    with open(py_file, 'r') as f:
        content = f.read()

    # Parse cells (split by # %%)
    lines = content.split('\n')
    cells = []
    current_cell = []

    for line in lines:
        if line.strip() == '# %%':
            if current_cell:
                cells.append('\n'.join(current_cell))
            current_cell = []
        else:
            current_cell.append(line)

    if current_cell:
        cells.append('\n'.join(current_cell))

    # Create notebook structure
    nb_cells = []

    for i, cell_content in enumerate(cells):
        if not cell_content.strip():
            continue

        # Skip shebang and script metadata
        if '#!/usr/bin/env' in cell_content or '# /// script' in cell_content:
            continue

        cell = {
            "cell_type": "code",
            "execution_count": i + 1,
            "metadata": {},
            "source": cell_content.strip(),
            "outputs": []
        }

        # Add output to the last cell (main execution cell)
        if i == len(cells) - 1 and output_text:
            cell["outputs"] = [{
                "output_type": "stream",
                "name": "stdout",
                "text": output_text
            }]

        nb_cells.append(cell)

    notebook = {
        "cells": nb_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11"
            },
            "jupytext": {
                "formats": "py:percent,ipynb"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    # Write notebook
    nb_file = py_file.with_suffix('.ipynb')
    with open(nb_file, 'w') as f:
        json.dump(notebook, f, indent=2)

    print(f"Created {nb_file}")

def main():
    play_dir = Path("play")

    # Execute 01_test_fasttext.py and capture output
    print("Executing 01_test_fasttext.py...")
    result = subprocess.run(
        [str(play_dir / "01_test_fasttext.py")],
        capture_output=True,
        text=True,
        timeout=180
    )

    if result.returncode == 0:
        create_notebook_with_output(
            play_dir / "01_test_fasttext.py",
            result.stdout
        )
    else:
        print(f"Error executing script: {result.stderr}")
        return 1

    print("Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
