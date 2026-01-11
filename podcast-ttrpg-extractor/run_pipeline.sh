#!/bin/bash
# Run the full TTRPG extraction pipeline
# Usage: ./run_pipeline.sh [--skip-download] [--skip-transcribe] [--use-llm]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SKIP_DOWNLOAD=false
SKIP_TRANSCRIBE=false
USE_LLM=false
WHISPER_MODEL="medium"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-download)
            SKIP_DOWNLOAD=true
            shift
            ;;
        --skip-transcribe)
            SKIP_TRANSCRIBE=true
            shift
            ;;
        --use-llm)
            USE_LLM=true
            shift
            ;;
        --model)
            WHISPER_MODEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=== Bastionland Podcast TTRPG Extractor ==="
echo ""

# Step 1: Fetch episodes
echo "Step 1: Fetching episode list..."
python scripts/01_fetch_episodes.py
echo ""

# Step 2: Download audio
if [ "$SKIP_DOWNLOAD" = false ]; then
    echo "Step 2: Downloading audio files..."
    python scripts/02_download_audio.py
else
    echo "Step 2: Skipping audio download"
fi
echo ""

# Step 3: Transcribe
if [ "$SKIP_TRANSCRIBE" = false ]; then
    echo "Step 3: Transcribing with Whisper (model: $WHISPER_MODEL)..."
    python scripts/03_transcribe.py --all --model "$WHISPER_MODEL"
else
    echo "Step 3: Skipping transcription"
fi
echo ""

# Step 4: Extract games
echo "Step 4: Extracting TTRPG mentions..."
if [ "$USE_LLM" = true ]; then
    python scripts/04_extract_games.py --all --use-llm
else
    python scripts/04_extract_games.py --all
fi
echo ""

# Step 5: Compile data
echo "Step 5: Compiling final data..."
python scripts/05_compile_data.py
echo ""

echo "=== Pipeline Complete ==="
echo "Check output/ directory for results"
