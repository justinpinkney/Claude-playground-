#!/usr/bin/env python3
"""
Fetch episode list from Bastionland Podcast RSS feed.
Filters for "Rule of Three" episodes and saves metadata.
"""

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import requests

RSS_URL = "https://anchor.fm/s/1958fb4c/podcast/rss"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "episodes"


def parse_duration(duration_str: str) -> int:
    """Convert duration string to seconds."""
    if not duration_str:
        return 0

    parts = duration_str.split(":")
    if len(parts) == 3:
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m, s = map(int, parts)
        return m * 60 + s
    return int(parts[0])


def fetch_rss() -> str:
    """Fetch RSS feed content."""
    print(f"Fetching RSS from {RSS_URL}...")
    response = requests.get(RSS_URL, timeout=30)
    response.raise_for_status()
    return response.text


def parse_episodes(rss_content: str) -> list[dict]:
    """Parse RSS XML and extract episode information."""
    # Register iTunes namespace
    namespaces = {
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }

    root = ET.fromstring(rss_content)
    channel = root.find('channel')

    episodes = []
    for item in channel.findall('item'):
        title = item.find('title').text or ""

        # Get description
        description = ""
        desc_elem = item.find('description')
        if desc_elem is not None and desc_elem.text:
            description = desc_elem.text

        # Get content:encoded if available (often has more detail)
        content_elem = item.find('content:encoded', namespaces)
        if content_elem is not None and content_elem.text:
            description = content_elem.text

        # Get publication date
        pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ""
        pub_date = None
        if pub_date_str:
            try:
                pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                try:
                    pub_date = datetime.strptime(pub_date_str.rsplit(' ', 1)[0], "%a, %d %b %Y %H:%M:%S")
                except ValueError:
                    pass

        # Get duration
        duration_elem = item.find('itunes:duration', namespaces)
        duration_str = duration_elem.text if duration_elem is not None else ""
        duration_seconds = parse_duration(duration_str)

        # Get audio URL from enclosure
        enclosure = item.find('enclosure')
        audio_url = enclosure.get('url') if enclosure is not None else ""

        # Get GUID
        guid_elem = item.find('guid')
        guid = guid_elem.text if guid_elem is not None else ""

        episode = {
            "title": title,
            "description": description,
            "pub_date": pub_date.isoformat() if pub_date else "",
            "duration_str": duration_str,
            "duration_seconds": duration_seconds,
            "audio_url": audio_url,
            "guid": guid,
        }
        episodes.append(episode)

    return episodes


def filter_rule_of_three(episodes: list[dict]) -> list[dict]:
    """Filter episodes that are part of the Rule of Three series."""
    rule_of_three = []

    for ep in episodes:
        title = ep["title"].lower()
        # Match patterns like "Rule of Three", "Rule of 3", "'s Rule of Three"
        if "rule of three" in title or "rule of 3" in title:
            # Extract guest name from title
            # Pattern: "Guest Name's Rule of Three" or "Rule of Three - Guest Name"
            guest = ""
            title_orig = ep["title"]

            if "'s rule of three" in title:
                guest = title_orig.split("'s")[0].strip()
            elif "rule of three -" in title:
                guest = title_orig.split("-")[1].strip()
            elif "- rule of three" in title:
                guest = title_orig.split("-")[0].strip()

            ep["guest"] = guest
            ep["is_rule_of_three"] = True
            rule_of_three.append(ep)
        else:
            ep["guest"] = ""
            ep["is_rule_of_three"] = False

    return rule_of_three


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch and parse RSS
    rss_content = fetch_rss()

    # Save raw RSS for reference
    rss_path = OUTPUT_DIR / "raw_rss.xml"
    rss_path.write_text(rss_content)
    print(f"Saved raw RSS to {rss_path}")

    # Parse all episodes
    all_episodes = parse_episodes(rss_content)
    print(f"Found {len(all_episodes)} total episodes")

    # Save all episodes
    all_path = OUTPUT_DIR / "all_episodes.json"
    with open(all_path, "w") as f:
        json.dump(all_episodes, f, indent=2)
    print(f"Saved all episodes to {all_path}")

    # Filter Rule of Three episodes
    rule_of_three = filter_rule_of_three(all_episodes)
    print(f"Found {len(rule_of_three)} Rule of Three episodes")

    # Save Rule of Three episodes
    rot_path = OUTPUT_DIR / "rule_of_three_episodes.json"
    with open(rot_path, "w") as f:
        json.dump(rule_of_three, f, indent=2)
    print(f"Saved Rule of Three episodes to {rot_path}")

    # Print summary
    print("\n=== Rule of Three Episodes ===")
    for ep in sorted(rule_of_three, key=lambda x: x["pub_date"]):
        guest = ep.get("guest", "Unknown")
        date = ep["pub_date"][:10] if ep["pub_date"] else "Unknown"
        print(f"  {date}: {guest} - {ep['title']}")


if __name__ == "__main__":
    main()
