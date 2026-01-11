# Bastionland Podcast "Rule of Three" TTRPG Extractor

## Project Goal
Extract and compile a structured list of all TTRPGs mentioned in the Bastionland Podcast's "Rule of Three" series, including:
- The 3 featured TTRPGs each guest picks
- Any other TTRPGs mentioned in conversation
- Timestamps for each mention
- Guest details and episode metadata

## Podcast Information
- **Podcast**: Bastionland Podcast - Tabletop Roleplaying Game Design
- **Series**: "Rule of Three"
- **Host**: Chris McDowall (creator of Into the Odd, Electric Bastionland)
- **Format**: Each guest picks their 3 most important games to discuss
- **Spotify URL**: https://open.spotify.com/show/2kJ5ZSjBafhDJtlTQ8EMUV

## Known Episodes (from research)

| Guest | Known Details |
|-------|---------------|
| Gav Thorpe | Author/Game Designer - boxed set, Games Workshop gem, Kickstarter RPG |
| Reynaldo Madriñan | Designer of BREAK!! RPG |
| Brendan S | Writer at Necropraxis |
| Philippa Mort | Game designer and historian |
| Diogo Nogueira | Game Designer - games from three schools of RPGs |
| Quintin Smith | Quinns' Quest - caves, sleazy deals, "most popular RPG" |
| Alan Gerding | Tuesday Knight Games |
| Kelsey Dionne | CD-ROM character builders, GM advice book |
| Mike Hutchinson | Nostalgia, pitched battles |
| Laurie O'Connel | Sit-out game, same character game, divorce court drama RPG |
| Spencer Campbell | Adventurous raccoons, semi-domesticated hyenas |
| Andy Chambers | Deadly viruses, space bugs, flying blind |
| Luke Stratton | Brigs, Borgs, and Bagginses |
| Mark Diaz Truman | Monetary value, gender, mouse-size |
| Brad Kerr | "So Hot" and "So Not" games |
| George Bickers | Vicious dogs, hollyhock gods, gambling save points |
| Amanda Lee Franck | "Things that are probably games" |

---

## Implementation Plan

### Phase 1: Episode Discovery & Metadata Collection

**Step 1.1: Scrape full episode list**
- Use Spotify API or scrape from podcast pages
- Collect: episode title, date, duration, description, guest name
- Alternative sources: Apple Podcasts, Listen Notes, Pocket Casts

**Step 1.2: Create episode database**
- Store in JSON/CSV format
- Fields: episode_id, title, guest, date, duration, description, audio_url

### Phase 2: Audio Acquisition

**Option A: Direct download (if RSS available)**
- Find RSS feed URL (often at anchor.fm/bastionland or similar)
- Parse RSS for direct MP3 links
- Download audio files

**Option B: Spotify podcast download**
- Tools: `spotdl` (spotify-downloader) - may work for podcasts
- Or use `youtube-dl`/`yt-dlp` if episodes are on YouTube

**Option C: Manual approach**
- Use a podcast app that allows offline downloads
- Record system audio while playing (lower quality)

### Phase 3: Audio Transcription

**Option A: Whisper (OpenAI) - Recommended**
```bash
pip install openai-whisper
whisper episode.mp3 --model medium --output_format json
```
- Provides timestamps for each segment
- High accuracy for English speech
- Can run locally (free) or via API

**Option B: AssemblyAI API**
- Excellent speaker diarization (identifies who is speaking)
- Automatic chapter detection
- Paid but affordable

**Option C: Google Speech-to-Text / AWS Transcribe**
- Cloud-based, paid per minute
- Good accuracy

**Recommended: Whisper locally** - free, accurate, provides word-level timestamps

### Phase 4: TTRPG Extraction

**Step 4.1: Build TTRPG reference database**
- Compile list of known TTRPGs (from BGG, itch.io, DriveThruRPG)
- Include common abbreviations and alternate names
- Focus on OSR, indie, and classic games likely to be mentioned

**Step 4.2: Named Entity Recognition**
- Use spaCy or similar NLP for entity extraction
- Custom training for TTRPG names
- Pattern matching for "game", "system", "RPG" context

**Step 4.3: LLM-assisted extraction**
- Feed transcripts to Claude/GPT with structured prompt
- Extract: game name, timestamp, who mentioned it, context
- Classify as "main pick" vs "mentioned in passing"

**Step 4.4: Human verification**
- Review extracted games for accuracy
- Add any missed mentions
- Correct transcription errors in game names

### Phase 5: Data Compilation

**Output format (JSON)**:
```json
{
  "episode": {
    "title": "Quintin Smith's Rule of Three",
    "date": "2024-01-15",
    "guest": {
      "name": "Quintin Smith",
      "bio": "Co-founder of Shut Up & Sit Down, Quinns' Quest",
      "links": ["https://quinns.quest"]
    },
    "duration": "1:23:45"
  },
  "main_picks": [
    {
      "rank": 1,
      "game": "D&D 5th Edition",
      "timestamp": "00:15:32",
      "discussion_end": "00:28:45",
      "summary": "Discussion about the most popular RPG..."
    }
  ],
  "other_mentions": [
    {
      "game": "Call of Cthulhu",
      "timestamp": "00:42:18",
      "context": "Mentioned as influence on horror games"
    }
  ]
}
```

---

## Technical Requirements

### Dependencies
```
# Audio processing
ffmpeg

# Transcription
openai-whisper
torch

# NLP/Extraction
spacy
anthropic  # for Claude API

# Data processing
pandas
```

### Directory Structure
```
podcast-ttrpg-extractor/
├── PLAN.md
├── scripts/
│   ├── 01_fetch_episodes.py
│   ├── 02_download_audio.py
│   ├── 03_transcribe.py
│   ├── 04_extract_games.py
│   └── 05_compile_data.py
├── data/
│   ├── episodes/           # Episode metadata
│   ├── audio/              # Downloaded MP3s
│   ├── transcripts/        # Whisper output
│   └── extracted/          # Game mentions
├── output/
│   ├── all_games.json      # Complete database
│   ├── by_episode.json     # Organized by episode
│   └── by_game.json        # Organized by game
└── reference/
    └── ttrpg_database.json # Known TTRPG names
```

---

## Challenges & Mitigations

| Challenge | Mitigation |
|-----------|------------|
| No direct Spotify audio download | Find RSS feed or alternative sources |
| Transcription errors on game names | Use TTRPG database for fuzzy matching |
| Distinguishing main picks from mentions | Contextual analysis + episode structure |
| Speaker identification | AssemblyAI diarization or manual |
| Incomplete episode list | Cross-reference multiple sources |

---

## Next Steps

1. **Immediate**: Find RSS feed or audio source for the podcast
2. **This week**: Download and transcribe 1-2 test episodes
3. **Validate**: Check transcription quality and extraction accuracy
4. **Scale**: Process all Rule of Three episodes
5. **Compile**: Generate final structured database

---

## Resources

- [Bastionland Podcast on Spotify](https://open.spotify.com/show/2kJ5ZSjBafhDJtlTQ8EMUV)
- [Bastionland Podcast on Spotify for Creators](https://creators.spotify.com/pod/profile/bastionland/)
- [Whisper Documentation](https://github.com/openai/whisper)
- [Electric Bastionland](https://www.bastionland.com/)
