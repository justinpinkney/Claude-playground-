#!/usr/bin/env python3
"""
Download audio files for Rule of Three episodes.
Uses episode metadata from step 01.
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from tqdm import tqdm

DATA_DIR = Path(__file__).parent.parent / "data"
EPISODES_FILE = DATA_DIR / "episodes" / "rule_of_three_episodes.json"
AUDIO_DIR = DATA_DIR / "audio"


def sanitize_filename(name: str) -> str:
    """Convert string to safe filename."""
    # Remove or replace problematic characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('._')
    return name[:100]  # Limit length


def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress bar."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(dest_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=dest_path.name) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Load episode metadata
    if not EPISODES_FILE.exists():
        print(f"Error: {EPISODES_FILE} not found. Run 01_fetch_episodes.py first.")
        return

    with open(EPISODES_FILE) as f:
        episodes = json.load(f)

    print(f"Found {len(episodes)} Rule of Three episodes to download")

    # Track download status
    status = []

    for i, ep in enumerate(episodes, 1):
        title = ep["title"]
        audio_url = ep.get("audio_url", "")
        guest = ep.get("guest", "Unknown")
        pub_date = ep.get("pub_date", "")[:10]

        if not audio_url:
            print(f"[{i}/{len(episodes)}] Skipping '{title}' - no audio URL")
            status.append({"episode": title, "status": "skipped", "reason": "no_url"})
            continue

        # Create filename from date and guest
        safe_guest = sanitize_filename(guest) if guest else "Unknown"
        safe_date = pub_date.replace("-", "")
        filename = f"{safe_date}_{safe_guest}.mp3"
        dest_path = AUDIO_DIR / filename

        # Check if already downloaded
        if dest_path.exists():
            print(f"[{i}/{len(episodes)}] Already exists: {filename}")
            status.append({"episode": title, "status": "exists", "path": str(dest_path)})
            continue

        print(f"\n[{i}/{len(episodes)}] Downloading: {title}")
        print(f"  Guest: {guest}")
        print(f"  Date: {pub_date}")

        success = download_file(audio_url, dest_path)

        if success:
            status.append({"episode": title, "status": "downloaded", "path": str(dest_path)})
            # Update episode metadata with local path
            ep["local_audio_path"] = str(dest_path)
        else:
            status.append({"episode": title, "status": "failed", "url": audio_url})

        # Small delay between downloads to be polite
        time.sleep(1)

    # Save updated episode metadata with local paths
    with open(EPISODES_FILE, "w") as f:
        json.dump(episodes, f, indent=2)

    # Save download status
    status_path = AUDIO_DIR / "download_status.json"
    with open(status_path, "w") as f:
        json.dump(status, f, indent=2)

    # Print summary
    downloaded = sum(1 for s in status if s["status"] == "downloaded")
    existed = sum(1 for s in status if s["status"] == "exists")
    failed = sum(1 for s in status if s["status"] == "failed")
    skipped = sum(1 for s in status if s["status"] == "skipped")

    print(f"\n=== Download Summary ===")
    print(f"  Downloaded: {downloaded}")
    print(f"  Already existed: {existed}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")


if __name__ == "__main__":
    main()
