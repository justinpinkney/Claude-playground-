#!/usr/bin/env python3
"""
Transcribe podcast audio using OpenAI Whisper.
Produces JSON output with word-level timestamps.
"""

import json
import argparse
from pathlib import Path
from datetime import timedelta

DATA_DIR = Path(__file__).parent.parent / "data"
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
EPISODES_FILE = DATA_DIR / "episodes" / "rule_of_three_episodes.json"


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def transcribe_audio(audio_path: Path, model_name: str = "medium") -> dict:
    """Transcribe audio file using Whisper."""
    import whisper

    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)

    print(f"Transcribing {audio_path.name}...")
    result = model.transcribe(
        str(audio_path),
        language="en",
        word_timestamps=True,
        verbose=False
    )

    return result


def process_transcript(result: dict) -> dict:
    """Process Whisper output into structured format."""
    segments = []

    for seg in result.get("segments", []):
        segment = {
            "id": seg["id"],
            "start": seg["start"],
            "end": seg["end"],
            "start_formatted": format_timestamp(seg["start"]),
            "end_formatted": format_timestamp(seg["end"]),
            "text": seg["text"].strip(),
        }

        # Include word-level timestamps if available
        if "words" in seg:
            segment["words"] = [
                {
                    "word": w["word"],
                    "start": w["start"],
                    "end": w["end"],
                    "start_formatted": format_timestamp(w["start"]),
                }
                for w in seg["words"]
            ]

        segments.append(segment)

    return {
        "text": result.get("text", ""),
        "language": result.get("language", "en"),
        "segments": segments,
    }


def main():
    parser = argparse.ArgumentParser(description="Transcribe podcast episodes with Whisper")
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: medium)")
    parser.add_argument("--episode", type=str, help="Specific episode filename to transcribe")
    parser.add_argument("--all", action="store_true", help="Transcribe all episodes")
    parser.add_argument("--force", action="store_true", help="Re-transcribe even if transcript exists")
    args = parser.parse_args()

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # Find audio files to process
    if args.episode:
        audio_files = [AUDIO_DIR / args.episode]
        if not audio_files[0].exists():
            print(f"Error: Audio file not found: {args.episode}")
            return
    elif args.all:
        audio_files = sorted(AUDIO_DIR.glob("*.mp3"))
    else:
        print("Specify --episode <filename> or --all")
        print(f"\nAvailable audio files in {AUDIO_DIR}:")
        for f in sorted(AUDIO_DIR.glob("*.mp3")):
            print(f"  {f.name}")
        return

    print(f"Found {len(audio_files)} audio files to process")

    for i, audio_path in enumerate(audio_files, 1):
        transcript_path = TRANSCRIPTS_DIR / f"{audio_path.stem}.json"

        # Skip if already transcribed
        if transcript_path.exists() and not args.force:
            print(f"[{i}/{len(audio_files)}] Skipping {audio_path.name} - transcript exists")
            continue

        print(f"\n[{i}/{len(audio_files)}] Processing {audio_path.name}")

        try:
            # Transcribe
            raw_result = transcribe_audio(audio_path, args.model)

            # Process into structured format
            transcript = process_transcript(raw_result)
            transcript["source_file"] = audio_path.name

            # Save transcript
            with open(transcript_path, "w") as f:
                json.dump(transcript, f, indent=2)

            print(f"  Saved transcript to {transcript_path}")

            # Also save a plain text version
            txt_path = TRANSCRIPTS_DIR / f"{audio_path.stem}.txt"
            with open(txt_path, "w") as f:
                for seg in transcript["segments"]:
                    f.write(f"[{seg['start_formatted']}] {seg['text']}\n")
            print(f"  Saved text to {txt_path}")

        except Exception as e:
            print(f"  Error processing {audio_path.name}: {e}")

    print("\n=== Transcription Complete ===")


if __name__ == "__main__":
    main()
