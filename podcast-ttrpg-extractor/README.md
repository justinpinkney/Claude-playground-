# Bastionland Podcast TTRPG Extractor

Extract and compile all TTRPGs mentioned in the **Bastionland Podcast "Rule of Three"** series.

In this series, host Chris McDowall (creator of Into the Odd, Electric Bastionland) interviews guests who each pick their **3 most important tabletop RPGs** to discuss.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# For Whisper, you also need ffmpeg:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: choco install ffmpeg

# Run the pipeline
python scripts/01_fetch_episodes.py    # Get episode list from RSS
python scripts/02_download_audio.py    # Download MP3 files
python scripts/03_transcribe.py --all  # Transcribe with Whisper
python scripts/04_extract_games.py --all  # Extract game mentions
python scripts/05_compile_data.py      # Generate final outputs
```

## Pipeline Overview

```
RSS Feed → Episode Metadata → Audio Files → Transcripts → Game Extractions → Compiled Data
```

### Step 1: Fetch Episodes
```bash
python scripts/01_fetch_episodes.py
```
- Fetches RSS feed from `https://anchor.fm/s/1958fb4c/podcast/rss`
- Filters "Rule of Three" episodes
- Saves to `data/episodes/rule_of_three_episodes.json`

### Step 2: Download Audio
```bash
python scripts/02_download_audio.py
```
- Downloads MP3 files for all Rule of Three episodes
- Saves to `data/audio/YYYYMMDD_GuestName.mp3`
- Respects existing downloads (won't re-download)

### Step 3: Transcribe
```bash
# Transcribe a single episode
python scripts/03_transcribe.py --episode 20240115_Quintin_Smith.mp3

# Transcribe all episodes
python scripts/03_transcribe.py --all

# Use a different model size (tiny/base/small/medium/large)
python scripts/03_transcribe.py --all --model large
```
- Uses OpenAI Whisper for transcription
- Produces JSON with word-level timestamps
- Also generates plain text `.txt` files

**Model Selection:**
| Model | Size | Speed | Accuracy | VRAM |
|-------|------|-------|----------|------|
| tiny | 39M | ~32x | Basic | ~1GB |
| base | 74M | ~16x | Good | ~1GB |
| small | 244M | ~6x | Better | ~2GB |
| **medium** | 769M | ~2x | **Recommended** | ~5GB |
| large | 1550M | 1x | Best | ~10GB |

### Step 4: Extract Games
```bash
# Pattern matching only
python scripts/04_extract_games.py --all

# With Claude API for better accuracy
python scripts/04_extract_games.py --all --use-llm --api-key YOUR_KEY
```
- Matches against database of 100+ known TTRPGs
- Identifies main picks vs. passing mentions
- Optional LLM extraction for context-aware results

### Step 5: Compile Data
```bash
python scripts/05_compile_data.py
```
- Generates multiple output formats in `output/`:
  - `by_episode.json` - Data organized by episode
  - `by_game.json` - Which episodes mention each game
  - `by_guest.json` - What each guest picked
  - `all_games.json` - Complete game list
  - `summary.md` - Human-readable overview

## Output Format

### by_episode.json
```json
{
  "episode": {
    "title": "Quintin Smith's Rule of Three",
    "guest": "Quintin Smith",
    "date": "2024-01-15",
    "duration": "1:23:45"
  },
  "main_picks": [
    {
      "game": "Dungeons & Dragons 5th Edition",
      "timestamp": "00:15:32",
      "context": "Discussion about the most popular RPG..."
    }
  ],
  "other_mentions": [
    {
      "game": "Call of Cthulhu",
      "timestamp": "00:42:18",
      "context": "Referenced as horror game influence"
    }
  ]
}
```

## Directory Structure

```
podcast-ttrpg-extractor/
├── README.md
├── PLAN.md
├── requirements.txt
├── scripts/
│   ├── 01_fetch_episodes.py
│   ├── 02_download_audio.py
│   ├── 03_transcribe.py
│   ├── 04_extract_games.py
│   └── 05_compile_data.py
├── data/
│   ├── episodes/          # Episode metadata JSON
│   ├── audio/             # Downloaded MP3 files
│   ├── transcripts/       # Whisper JSON + TXT output
│   └── extracted/         # Per-episode game extractions
├── output/                # Final compiled data
└── reference/             # TTRPG database (optional)
```

## Expanding the Game Database

The extraction script includes ~100 known TTRPGs. To add more:

1. Create `reference/ttrpg_database.json`:
```json
{
  "game name": ["alias1", "alias2"],
  "another game": []
}
```

2. Or edit the `KNOWN_GAMES` dict in `04_extract_games.py`

## Tips

- **Transcription is slow**: `medium` model takes ~10-20 min per hour of audio on GPU
- **CPU fallback**: Whisper works on CPU but is much slower
- **Disk space**: Audio files are ~50-100MB each
- **API costs**: LLM extraction uses Claude API (optional)

## Known Guests

From research, the Rule of Three series has featured:
- Quintin Smith (Shut Up & Sit Down)
- Gav Thorpe (Games Workshop author)
- Reynaldo Madriñan (BREAK!! designer)
- Brendan S (Necropraxis)
- Amanda Lee Franck
- Mike Hutchinson
- Kelsey Dionne
- Spencer Campbell
- Andy Chambers
- Luke Stratton
- Mark Diaz Truman
- Brad Kerr
- George Bickers
- Laurie O'Connel
- Diogo Nogueira
- Philippa Mort
- Alan Gerding (Tuesday Knight Games)
- ...and more

## License

This tool is for personal/research use. Podcast content belongs to Chris McDowall / Bastionland.
