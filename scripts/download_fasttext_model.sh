#!/bin/bash
# Download FastText pre-trained model
# Model: wiki-news-300d-1M (English, 1M words, 300 dimensions)

set -e

MODEL_DIR="data/fasttext"
MODEL_URL="https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip"
MODEL_NAME="wiki-news-300d-1M"

echo "Downloading FastText model: ${MODEL_NAME}"
echo "This may take a few minutes..."

# Create model directory if it doesn't exist
mkdir -p "${MODEL_DIR}"

# Download the model
echo "Downloading from ${MODEL_URL}"
curl -L "${MODEL_URL}" -o "${MODEL_DIR}/${MODEL_NAME}.vec.zip"

# Extract the model
echo "Extracting model..."
unzip -o "${MODEL_DIR}/${MODEL_NAME}.vec.zip" -d "${MODEL_DIR}"

# Remove the zip file
rm "${MODEL_DIR}/${MODEL_NAME}.vec.zip"

echo "Model downloaded successfully to ${MODEL_DIR}/${MODEL_NAME}.vec"
echo "File size:"
ls -lh "${MODEL_DIR}/${MODEL_NAME}.vec"
