#!/usr/bin/env python3
"""
Compile all extracted TTRPG data into final output formats.
Generates:
- by_episode.json: All data organized by episode
- by_game.json: Index of which episodes mention each game
- by_guest.json: Games picked by each guest
- all_games.json: Complete list of all games mentioned
- summary.md: Human-readable summary
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
EPISODES_FILE = DATA_DIR / "episodes" / "rule_of_three_episodes.json"
EXTRACTED_DIR = DATA_DIR / "extracted"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def load_episode_metadata() -> dict:
    """Load episode metadata indexed by audio filename."""
    if not EPISODES_FILE.exists():
        return {}

    with open(EPISODES_FILE) as f:
        episodes = json.load(f)

    # Index by various keys for matching
    indexed = {}
    for ep in episodes:
        # Try to match by audio path stem
        if "local_audio_path" in ep:
            stem = Path(ep["local_audio_path"]).stem
            indexed[stem] = ep
        # Also index by title
        indexed[ep["title"]] = ep

    return indexed


def load_extractions() -> list[dict]:
    """Load all extracted game data."""
    extractions = []
    for path in sorted(EXTRACTED_DIR.glob("*_games.json")):
        with open(path) as f:
            data = json.load(f)
            data["extraction_file"] = path.name
            extractions.append(data)
    return extractions


def compile_by_episode(extractions: list[dict], episodes: dict) -> list[dict]:
    """Compile data organized by episode."""
    compiled = []

    for ext in extractions:
        audio_file = ext.get("source_audio", "")
        stem = Path(audio_file).stem if audio_file else ""

        # Find matching episode metadata
        ep_meta = episodes.get(stem, {})

        episode_data = {
            "episode": {
                "title": ep_meta.get("title", stem),
                "guest": ep_meta.get("guest", "Unknown"),
                "date": ep_meta.get("pub_date", "")[:10] if ep_meta.get("pub_date") else "",
                "duration": ep_meta.get("duration_str", ""),
                "description": ep_meta.get("description", ""),
            },
            "main_picks": [],
            "other_mentions": [],
            "extraction_method": ext.get("extraction_method", ""),
        }

        # Use LLM extraction if available, otherwise pattern matching
        if "llm_extraction" in ext:
            llm = ext["llm_extraction"]
            episode_data["main_picks"] = llm.get("main_picks", [])
            episode_data["other_mentions"] = llm.get("other_mentions", [])
            if "guest_info" in llm:
                episode_data["episode"]["guest_info"] = llm["guest_info"]
        else:
            # Deduplicate main picks by game name
            seen_games = set()
            for pick in ext.get("main_picks", []):
                game = pick["game"]
                if game not in seen_games:
                    seen_games.add(game)
                    episode_data["main_picks"].append({
                        "game": game,
                        "timestamp": pick.get("timestamp_formatted", ""),
                        "context": pick.get("context", ""),
                    })

            # Deduplicate other mentions
            seen_other = set()
            for mention in ext.get("other_mentions", []):
                game = mention["game"]
                if game not in seen_other and game not in seen_games:
                    seen_other.add(game)
                    episode_data["other_mentions"].append({
                        "game": game,
                        "timestamp": mention.get("timestamp_formatted", ""),
                        "context": mention.get("context", ""),
                    })

        compiled.append(episode_data)

    # Sort by date
    compiled.sort(key=lambda x: x["episode"].get("date", ""), reverse=True)

    return compiled


def compile_by_game(by_episode: list[dict]) -> dict:
    """Create index of games to episodes."""
    game_index = defaultdict(lambda: {"main_pick_in": [], "mentioned_in": []})

    for ep in by_episode:
        ep_info = {
            "episode": ep["episode"]["title"],
            "guest": ep["episode"]["guest"],
            "date": ep["episode"]["date"],
        }

        for pick in ep.get("main_picks", []):
            game = pick.get("game", pick) if isinstance(pick, dict) else pick
            game_index[game]["main_pick_in"].append({
                **ep_info,
                "timestamp": pick.get("timestamp", "") if isinstance(pick, dict) else "",
            })

        for mention in ep.get("other_mentions", []):
            game = mention.get("game", mention) if isinstance(mention, dict) else mention
            game_index[game]["mentioned_in"].append({
                **ep_info,
                "timestamp": mention.get("timestamp", "") if isinstance(mention, dict) else "",
            })

    # Convert to sorted list
    return dict(sorted(game_index.items()))


def compile_by_guest(by_episode: list[dict]) -> dict:
    """Organize picks by guest."""
    guest_data = {}

    for ep in by_episode:
        guest = ep["episode"].get("guest", "Unknown")
        if not guest:
            guest = "Unknown"

        if guest not in guest_data:
            guest_data[guest] = {
                "episodes": [],
                "total_picks": [],
            }

        guest_data[guest]["episodes"].append({
            "title": ep["episode"]["title"],
            "date": ep["episode"]["date"],
            "main_picks": ep.get("main_picks", []),
        })

        # Aggregate all picks
        for pick in ep.get("main_picks", []):
            game = pick.get("game", pick) if isinstance(pick, dict) else pick
            if game not in guest_data[guest]["total_picks"]:
                guest_data[guest]["total_picks"].append(game)

    return dict(sorted(guest_data.items()))


def generate_summary(by_episode: list[dict], by_game: dict, by_guest: dict) -> str:
    """Generate human-readable markdown summary."""
    lines = [
        "# Bastionland Podcast - Rule of Three: TTRPG Database",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Overview",
        "",
        f"- **Total Episodes Analyzed**: {len(by_episode)}",
        f"- **Unique Games Found**: {len(by_game)}",
        f"- **Guests Featured**: {len(by_guest)}",
        "",
        "---",
        "",
        "## Episodes by Date",
        "",
    ]

    for ep in sorted(by_episode, key=lambda x: x["episode"].get("date", ""), reverse=True):
        guest = ep["episode"].get("guest", "Unknown")
        date = ep["episode"].get("date", "Unknown")
        picks = ep.get("main_picks", [])
        pick_names = [p.get("game", p) if isinstance(p, dict) else p for p in picks[:3]]

        lines.append(f"### {guest} ({date})")
        lines.append("")
        if pick_names:
            lines.append("**Main Picks:**")
            for i, game in enumerate(pick_names, 1):
                lines.append(f"{i}. {game}")
        lines.append("")

        other = ep.get("other_mentions", [])
        if other:
            other_names = list(set(m.get("game", m) if isinstance(m, dict) else m for m in other))[:10]
            lines.append(f"*Also mentioned: {', '.join(other_names)}*")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend([
        "## All Games Mentioned",
        "",
        "| Game | Main Pick Count | Mention Count |",
        "|------|-----------------|---------------|",
    ])

    for game, data in sorted(by_game.items(), key=lambda x: len(x[1]["main_pick_in"]), reverse=True):
        main_count = len(data["main_pick_in"])
        mention_count = len(data["mentioned_in"])
        lines.append(f"| {game} | {main_count} | {mention_count} |")

    lines.extend([
        "",
        "---",
        "",
        "## Guests",
        "",
    ])

    for guest, data in sorted(by_guest.items()):
        picks = data.get("total_picks", [])
        lines.append(f"- **{guest}**: {', '.join(picks[:5])}")

    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    episodes = load_episode_metadata()
    extractions = load_extractions()

    if not extractions:
        print("No extractions found. Run 04_extract_games.py first.")
        return

    print(f"Found {len(extractions)} extractions and {len(episodes)} episode metadata entries")

    # Compile different views
    print("Compiling by episode...")
    by_episode = compile_by_episode(extractions, episodes)

    print("Compiling by game...")
    by_game = compile_by_game(by_episode)

    print("Compiling by guest...")
    by_guest = compile_by_guest(by_episode)

    # Save outputs
    outputs = [
        ("by_episode.json", by_episode),
        ("by_game.json", by_game),
        ("by_guest.json", by_guest),
        ("all_games.json", list(by_game.keys())),
    ]

    for filename, data in outputs:
        path = OUTPUT_DIR / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {path}")

    # Generate summary
    summary = generate_summary(by_episode, by_game, by_guest)
    summary_path = OUTPUT_DIR / "summary.md"
    summary_path.write_text(summary)
    print(f"Saved {summary_path}")

    # Print stats
    print("\n=== Compilation Complete ===")
    print(f"Episodes: {len(by_episode)}")
    print(f"Unique games: {len(by_game)}")
    print(f"Guests: {len(by_guest)}")

    # Top games
    print("\nTop 10 games by main pick count:")
    sorted_games = sorted(by_game.items(), key=lambda x: len(x[1]["main_pick_in"]), reverse=True)
    for game, data in sorted_games[:10]:
        print(f"  {game}: {len(data['main_pick_in'])} main picks, {len(data['mentioned_in'])} mentions")


if __name__ == "__main__":
    main()
