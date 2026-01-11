#!/usr/bin/env python3
"""
Extract TTRPG mentions from podcast transcripts.
Uses pattern matching against known games + optional LLM assistance.
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
EXTRACTED_DIR = DATA_DIR / "extracted"
REFERENCE_DIR = Path(__file__).parent.parent / "reference"
EPISODES_FILE = DATA_DIR / "episodes" / "rule_of_three_episodes.json"


# Known TTRPGs and common variations
# This can be expanded significantly
KNOWN_GAMES = {
    # D&D and variants
    "dungeons and dragons": ["d&d", "dnd", "dungeons & dragons", "dungeons and dragons"],
    "d&d 5th edition": ["5e", "fifth edition", "d&d 5e", "dnd 5e"],
    "d&d 4th edition": ["4e", "fourth edition", "d&d 4e"],
    "d&d 3.5": ["3.5", "three point five", "d&d 3.5e"],
    "d&d 3rd edition": ["3e", "third edition"],
    "ad&d": ["advanced dungeons and dragons", "ad&d 2nd edition", "ad&d 1st edition"],
    "od&d": ["original d&d", "original dungeons and dragons", "0e"],
    "basic d&d": ["b/x", "basic expert", "becmi", "rules cyclopedia"],

    # OSR
    "old school essentials": ["ose"],
    "into the odd": [],
    "electric bastionland": ["bastionland"],
    "cairn": [],
    "mausritter": [],
    "knave": [],
    "the black hack": ["black hack"],
    "whitehack": [],
    "dungeon crawl classics": ["dcc"],
    "mothership": [],
    "troika": [],
    "maze rats": [],
    "worlds without number": ["wwn"],
    "stars without number": ["swn"],
    "godbound": [],
    "silent legions": [],
    "lamentations of the flame princess": ["lotfp"],
    "torchbearer": [],
    "burning wheel": [],
    "mouse guard": [],

    # Indie/Story games
    "blades in the dark": ["bitd", "blades"],
    "forged in the dark": ["fitd"],
    "apocalypse world": ["aw"],
    "powered by the apocalypse": ["pbta"],
    "dungeon world": [],
    "monster of the week": ["motw"],
    "masks": [],
    "fellowship": [],
    "ironsworn": [],
    "starforged": [],
    "fate": ["fate core", "fate accelerated", "fae"],
    "fiasco": [],
    "dread": [],
    "ten candles": [],
    "the quiet year": [],
    "microscope": [],
    "kingdom": [],
    "follow": [],
    "for the queen": [],
    "wanderhome": [],
    "dream askew": [],
    "monsterhearts": [],
    "urban shadows": [],
    "the sprawl": [],
    "hearts of wulin": [],
    "pasion de las pasiones": [],
    "thirsty sword lesbians": [],
    "agon": [],
    "polaris": [],
    "primetime adventures": [],
    "dogs in the vineyard": [],
    "lady blackbird": [],
    "lasers and feelings": ["lasers & feelings"],

    # Traditional/Popular
    "call of cthulhu": ["coc"],
    "delta green": [],
    "trail of cthulhu": [],
    "gumshoe": [],
    "night's black agents": [],
    "pathfinder": ["pf1e", "pf2e", "pathfinder 2e"],
    "starfinder": [],
    "shadowrun": [],
    "cyberpunk": ["cyberpunk 2020", "cyberpunk red"],
    "vampire the masquerade": ["vtm", "vampire"],
    "world of darkness": ["wod", "chronicles of darkness", "cod"],
    "werewolf the apocalypse": [],
    "mage the ascension": [],
    "changeling": [],
    "hunter the reckoning": [],
    "traveller": ["traveler", "mongoose traveller"],
    "warhammer fantasy roleplay": ["wfrp"],
    "warhammer 40k": ["dark heresy", "rogue trader", "deathwatch", "black crusade", "only war"],
    "star wars rpg": ["edge of the empire", "age of rebellion", "force and destiny"],
    "legend of the five rings": ["l5r"],
    "runequest": [],
    "glorantha": [],
    "pendragon": [],
    "ars magica": [],
    "unknown armies": [],
    "over the edge": [],
    "paranoia": [],
    "toon": [],
    "teenagers from outer space": ["tfos"],
    "savage worlds": [],
    "gurps": [],
    "hero system": ["champions"],
    "mutants and masterminds": ["m&m"],

    # Specific mentioned games (from research)
    "break!!": ["break rpg", "break"],
    "necropraxis": [],
    "wonder & wickedness": [],
}


def load_ttrpg_database() -> dict:
    """Load TTRPG reference database."""
    db_path = REFERENCE_DIR / "ttrpg_database.json"
    if db_path.exists():
        with open(db_path) as f:
            return json.load(f)
    return KNOWN_GAMES


def build_search_patterns(games_db: dict) -> list[tuple[str, re.Pattern]]:
    """Build regex patterns for game matching."""
    patterns = []

    for game, aliases in games_db.items():
        # Include the main name and all aliases
        all_names = [game] + (aliases if aliases else [])

        for name in all_names:
            # Create pattern that matches whole words (case insensitive)
            # Escape special regex characters
            escaped = re.escape(name)
            pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE)
            patterns.append((game, pattern))

    return patterns


def find_game_mentions(transcript: dict, patterns: list[tuple[str, re.Pattern]]) -> list[dict]:
    """Find all game mentions in transcript with timestamps."""
    mentions = []
    seen = set()  # Track (game, segment_id) to avoid duplicates

    for segment in transcript.get("segments", []):
        text = segment["text"]
        seg_id = segment["id"]
        start = segment["start"]
        start_fmt = segment["start_formatted"]

        for game_name, pattern in patterns:
            if pattern.search(text):
                key = (game_name, seg_id)
                if key not in seen:
                    seen.add(key)
                    mentions.append({
                        "game": game_name,
                        "timestamp": start,
                        "timestamp_formatted": start_fmt,
                        "context": text.strip(),
                        "segment_id": seg_id,
                    })

    # Sort by timestamp
    mentions.sort(key=lambda x: x["timestamp"])

    return mentions


def identify_main_picks(mentions: list[dict], transcript: dict) -> tuple[list[dict], list[dict]]:
    """
    Attempt to identify the 3 main picks vs other mentions.
    This is a heuristic - may need manual verification.
    """
    # Count mentions per game
    game_counts = defaultdict(int)
    first_mention = {}

    for m in mentions:
        game = m["game"]
        game_counts[game] += 1
        if game not in first_mention:
            first_mention[game] = m

    # Games mentioned multiple times are likely main picks
    # Sort by mention count, then by first mention time
    sorted_games = sorted(
        game_counts.keys(),
        key=lambda g: (-game_counts[g], first_mention[g]["timestamp"])
    )

    # Top 3 most discussed are likely main picks
    main_picks = []
    other_mentions = []

    main_game_names = set(sorted_games[:3]) if len(sorted_games) >= 3 else set(sorted_games)

    for m in mentions:
        if m["game"] in main_game_names:
            main_picks.append(m)
        else:
            other_mentions.append(m)

    return main_picks, other_mentions


def extract_with_llm(transcript: dict, api_key: str = None) -> dict:
    """
    Use Claude API to extract games from transcript.
    Returns structured extraction.
    """
    if not api_key:
        print("No API key provided - skipping LLM extraction")
        return None

    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed - skipping LLM extraction")
        return None

    # Prepare transcript text with timestamps
    text_with_timestamps = "\n".join(
        f"[{seg['start_formatted']}] {seg['text']}"
        for seg in transcript.get("segments", [])
    )

    # Truncate if too long (Claude has context limits)
    max_chars = 100000
    if len(text_with_timestamps) > max_chars:
        text_with_timestamps = text_with_timestamps[:max_chars] + "\n[TRUNCATED]"

    prompt = f"""Analyze this podcast transcript from the Bastionland Podcast "Rule of Three" series.
In this format, each guest picks their 3 most important tabletop RPGs to discuss.

Extract ALL tabletop RPGs, board games, and related games mentioned. For each game, provide:
1. The exact game name
2. The timestamp when it's first mentioned
3. Whether it's one of the guest's 3 main picks or just mentioned in passing
4. Brief context about why it was mentioned

Transcript:
{text_with_timestamps}

Respond in JSON format:
{{
  "main_picks": [
    {{"rank": 1, "game": "Game Name", "timestamp": "HH:MM:SS", "reason": "Why guest chose it"}},
    ...
  ],
  "other_mentions": [
    {{"game": "Game Name", "timestamp": "HH:MM:SS", "context": "Brief context"}}
  ],
  "guest_info": {{
    "name": "Guest name if mentioned",
    "bio": "Any bio/background mentioned"
  }}
}}"""

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse JSON from response
    response_text = response.content[0].text
    # Try to extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        return json.loads(json_match.group())

    return None


def main():
    parser = argparse.ArgumentParser(description="Extract TTRPG mentions from transcripts")
    parser.add_argument("--transcript", type=str, help="Specific transcript to process")
    parser.add_argument("--all", action="store_true", help="Process all transcripts")
    parser.add_argument("--use-llm", action="store_true", help="Use Claude API for extraction")
    parser.add_argument("--api-key", type=str, help="Anthropic API key")
    args = parser.parse_args()

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    # Load game database
    games_db = load_ttrpg_database()
    patterns = build_search_patterns(games_db)
    print(f"Loaded {len(games_db)} games with {len(patterns)} search patterns")

    # Find transcripts to process
    if args.transcript:
        transcript_files = [TRANSCRIPTS_DIR / args.transcript]
        if not transcript_files[0].exists():
            print(f"Error: Transcript not found: {args.transcript}")
            return
    elif args.all:
        transcript_files = sorted(TRANSCRIPTS_DIR.glob("*.json"))
    else:
        print("Specify --transcript <filename> or --all")
        print(f"\nAvailable transcripts in {TRANSCRIPTS_DIR}:")
        for f in sorted(TRANSCRIPTS_DIR.glob("*.json")):
            print(f"  {f.name}")
        return

    print(f"Processing {len(transcript_files)} transcripts")

    for i, transcript_path in enumerate(transcript_files, 1):
        print(f"\n[{i}/{len(transcript_files)}] Processing {transcript_path.name}")

        with open(transcript_path) as f:
            transcript = json.load(f)

        # Pattern-based extraction
        mentions = find_game_mentions(transcript, patterns)
        main_picks, other_mentions = identify_main_picks(mentions, transcript)

        result = {
            "source_transcript": transcript_path.name,
            "source_audio": transcript.get("source_file", ""),
            "extraction_method": "pattern_matching",
            "main_picks": main_picks,
            "other_mentions": other_mentions,
            "all_games_found": list(set(m["game"] for m in mentions)),
        }

        # Optional LLM extraction
        if args.use_llm:
            api_key = args.api_key or None
            llm_result = extract_with_llm(transcript, api_key)
            if llm_result:
                result["llm_extraction"] = llm_result
                result["extraction_method"] = "pattern_matching + llm"

        # Save extraction
        output_path = EXTRACTED_DIR / f"{transcript_path.stem}_games.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"  Found {len(mentions)} total mentions")
        print(f"  Main picks (estimated): {len(set(m['game'] for m in main_picks))} games")
        print(f"  Other mentions: {len(set(m['game'] for m in other_mentions))} games")
        print(f"  Saved to {output_path}")

    print("\n=== Extraction Complete ===")


if __name__ == "__main__":
    main()
