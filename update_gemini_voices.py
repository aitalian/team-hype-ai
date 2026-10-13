#!/usr/bin/env python3
"""
TeamHypeAI - Gemini Voice Catalog Tracker & Updater (update_gemini_voices.py)

Maintains and refreshes config/gemini_voices.json with official Google Gemini TTS
voices. Adheres strictly to DRY principles by loading all sources, personas,
featured ordering, exclusion taxonomies, and baseline catalogs directly from
cached config/gemini_voices.json as the single source of truth.

Usage:
    python update_gemini_voices.py --check
    python update_gemini_voices.py --check --all
    python update_gemini_voices.py --update
"""

import os
import sys
import json
import re
import datetime
import urllib.request
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Path resolution
PROJECT_ROOT = Path(__file__).resolve().parent
VOICES_JSON_PATH = PROJECT_ROOT / "config" / "gemini_voices.json"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

# Fallback sources if config is empty or newly created
DEFAULT_SOURCES = {
    "gemini_tts_guide": "https://ai.google.dev/gemini-api/docs/speech-generation",
    "cloud_tts_docs": "https://docs.cloud.google.com/text-to-speech/docs/gemini-tts"
}


def load_config(config_path: Path = VOICES_JSON_PATH) -> Dict[str, Any]:
    """
    Loads config/gemini_voices.json as the single source of truth.
    Strictly loads metadata, excluded taxonomies, and voice definitions.
    """
    if not config_path.exists():
        print(f"❌ Error: Configuration file '{config_path}' not found.")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error: Failed to parse '{config_path}': {e}")
        sys.exit(1)

    # Ensure required structure
    if "_meta" not in data:
        data["_meta"] = {}
    if "sources" not in data["_meta"]:
        data["_meta"]["sources"] = DEFAULT_SOURCES
    if "voices" not in data:
        data["voices"] = []
    if "excluded_voices" not in data["_meta"]:
        data["_meta"]["excluded_voices"] = {}
    if "featured_order" not in data["_meta"]:
        data["_meta"]["featured_order"] = ["Puck", "Charon", "Kore", "Fenrir", "Aoede"]

    return data


def fetch_upstream_voices(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetches upstream voices by querying official documentation sources defined in config,
    falling back to the upstream_baseline embedded in config/_meta.
    """
    meta = config.get("_meta", {})
    sources = meta.get("sources", DEFAULT_SOURCES)
    baseline = meta.get("upstream_baseline", [])

    # Seed with upstream baseline loaded from config
    voices_by_name = {v["name"]: dict(v) for v in baseline}

    # If baseline was empty, seed with known voices + excluded voices from config
    if not voices_by_name:
        for v in config.get("voices", []):
            voices_by_name[v["name"]] = {
                "name": v["name"],
                "tone": v.get("tone", "Upbeat"),
                "gender": v.get("gender", "Unspecified"),
                "category": v.get("category", "High-Energy Arena")
            }
        for name in meta.get("excluded_voices", {}).keys():
            if name not in voices_by_name:
                voices_by_name[name] = {
                    "name": name,
                    "tone": "Unknown",
                    "gender": "Unspecified",
                    "category": "Unspecified"
                }

    # 1. Fetch Cloud TTS docs for gender mappings
    cloud_url = sources.get("cloud_tts_docs")
    if cloud_url:
        try:
            req = urllib.request.Request(cloud_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8")
                matches = re.findall(r"<td>([A-Za-z]+)</td>\s*<td>(Male|Female)</td>", html)
                for name, gender in matches:
                    if name in voices_by_name:
                        voices_by_name[name]["gender"] = gender
                    else:
                        voices_by_name[name] = {
                            "name": name,
                            "gender": gender,
                            "tone": "Unknown",
                            "category": "Unspecified"
                        }
        except Exception:
            pass

    # 2. Fetch AI Studio guide for tone descriptors
    guide_url = sources.get("gemini_tts_guide")
    if guide_url:
        try:
            req = urllib.request.Request(guide_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8")
                matches = re.findall(r"<b>([A-Za-z]+)</b>\s*--\s*<em>([A-Za-z\-]+)</em>", html)
                for name, tone in matches:
                    if name in voices_by_name:
                        voices_by_name[name]["tone"] = tone
                    else:
                        voices_by_name[name] = {
                            "name": name,
                            "tone": tone,
                            "gender": "Unknown",
                            "category": "Unspecified"
                        }
        except Exception:
            pass

    return list(voices_by_name.values())


def is_high_energy_english(voice_info: Dict[str, Any], config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Evaluates whether a voice qualifies for high-energy sports announcements,
    using the curated entries and exclusion taxonomy loaded from config.
    """
    name = voice_info["name"]
    meta = config.get("_meta", {})
    vetted_voices = {v["name"]: v for v in config.get("voices", [])}
    excluded_voices = meta.get("excluded_voices", {})

    # 1. Check if already vetted in config
    if name in vetted_voices:
        v = vetted_voices[name]
        return True, v.get("notes") or f"Vetted high-energy stadium PA persona ({v.get('announcer_style')})"

    # 2. Check if explicitly in exclusion taxonomy
    if name in excluded_voices:
        return False, excluded_voices[name]

    # 3. Dynamic keyword heuristics for newly discovered upstream voices
    tone = voice_info.get("tone", "").lower()
    category = voice_info.get("category", "").lower()

    unsuitable_keywords = ["soft", "gentle", "breathy", "casual", "easy-going", "even", "warm", "laid-back"]
    if any(k in tone or k in category for k in unsuitable_keywords):
        return False, f"Tone '{voice_info.get('tone')}' lacks high-energy stadium acoustic presence"

    suitable_keywords = ["upbeat", "excitable", "firm", "bright", "gravelly", "lively", "forward", "bold", "dynamic", "punchy"]
    if any(k in tone or k in category for k in suitable_keywords):
        return True, f"Positive match on tone '{voice_info.get('tone')}'"

    return False, f"Tone '{voice_info.get('tone')}' is neutral/unverified for arena announcements"


def build_curated_voices_json(upstream_voices: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the updated config/gemini_voices.json data structure by preserving
    existing rich configurations while syncing with discovered upstream models.
    """
    meta = config.get("_meta", {})
    featured_order = meta.get("featured_order", ["Puck", "Charon", "Kore", "Fenrir", "Aoede"])
    existing_voices = {v["name"]: dict(v) for v in config.get("voices", [])}
    existing_excluded = dict(meta.get("excluded_voices", {}))

    curated = []
    excluded = dict(existing_excluded)

    for v in upstream_voices:
        name = v["name"]
        qualifies, reason = is_high_energy_english(v, config)

        if qualifies:
            if name in existing_voices:
                entry = dict(existing_voices[name])
                # Update attributes if discovered from upstream
                if v.get("gender") and v["gender"] != "Unknown":
                    entry["gender"] = v["gender"]
                if v.get("tone") and v["tone"] != "Unknown":
                    entry["tone"] = v["tone"]
                    entry["description"] = v["tone"]
                if v.get("category") and v["category"] != "Unspecified":
                    entry["category"] = v["category"]
            else:
                # Newly qualified voice
                is_feat = name in featured_order
                entry = {
                    "name": name,
                    "description": v.get("tone", "Dynamic"),
                    "tone": v.get("tone", "Upbeat"),
                    "gender": v.get("gender", "Unspecified"),
                    "category": v.get("category", "High-Energy Arena"),
                    "language": "en",
                    "is_featured": is_feat,
                    "announcer_style": f"{v.get('tone', 'Dynamic')} Sports Announcer",
                    "energy_rating": "high",
                    "recommended_style": "excitedly, fast-paced",
                    "recommended_tags": "excitedly, fast-paced",
                    "notes": f"Discovered high-energy voice persona ({v.get('tone')})."
                }
            curated.append(entry)
        else:
            excluded[name] = reason

    # Sort: Featured voices first by featured_order, then alphabetically
    curated.sort(key=lambda x: (
        0 if x["name"] in featured_order else 1,
        featured_order.index(x["name"]) if x["name"] in featured_order else x["name"]
    ))

    # Update upstream_baseline in _meta to reflect latest upstream state
    upstream_baseline = []
    for uv in upstream_voices:
        upstream_baseline.append({
            "name": uv["name"],
            "tone": uv.get("tone", "Upbeat"),
            "gender": uv.get("gender", "Unspecified"),
            "category": uv.get("category", "Other Unique Profiles")
        })

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    meta["last_updated"] = timestamp
    meta["total_vetted_voices"] = len(curated)
    meta["excluded_voices"] = excluded
    meta["upstream_baseline"] = upstream_baseline

    return {
        "_meta": meta,
        "voices": curated
    }


def audit_voice_catalog(config: Dict[str, Any], show_all: bool = False) -> None:
    """
    Prints an audit comparing the cached local configuration with upstream data.
    """
    print("\n" + "=" * 70)
    print("🎙️  TEAMHYPEAI - GEMINI VOICE CATALOG AUDIT & TRACKER")
    print("=" * 70)
    print("🎯 Curation Filter: English language only, high-energy stadium announcements")
    print(f"📁 Local Config:    {VOICES_JSON_PATH}\n")

    current_voices = config.get("voices", [])
    current_names = [v["name"] for v in current_voices]
    print(f"📌 CURRENT LOCAL VOICES ({len(current_names)}):")
    for v in current_voices:
        feat = "★ FEATURED" if v.get("is_featured") else "  vetted  "
        print(f"  • {v['name']:<14} [{v.get('gender', 'M/F'):<6}] Tone: {v.get('tone', v.get('description', '')):<12} ({feat}) -> {v.get('announcer_style', v.get('category', ''))}")

    upstream = fetch_upstream_voices(config)
    print(f"\n🌐 UPSTREAM GOOGLE GEMINI TTS CATALOG ({len(upstream)} total voices discovered):")

    vetted_count = 0
    excluded_count = 0
    new_candidates = []

    for v in upstream:
        qualifies, reason = is_high_energy_english(v, config)
        if qualifies:
            vetted_count += 1
            if v["name"] not in current_names:
                new_candidates.append((v, reason))
        else:
            excluded_count += 1

    print(f"  • Qualifying High-Energy English: {vetted_count}")
    print(f"  • Excluded (Low-energy / soft / calm): {excluded_count}")

    if new_candidates:
        print(f"\n✨ NEW CANDIDATE VOICES FOR ADDITION ({len(new_candidates)}):")
        for v, reason in new_candidates:
            print(f"  + {v['name']} ({v.get('gender')}) - Tone: {v.get('tone')} - Reason: {reason}")
    else:
        print("\n✅ All qualifying upstream high-energy voices are accounted for!")

    if show_all:
        print("\n📋 FULL EXCLUDED VOICES AUDIT:")
        for v in upstream:
            qualifies, reason = is_high_energy_english(v, config)
            if not qualifies:
                print(f"  ✗ {v['name']:<14} ({v.get('gender', 'M/F'):<6} | {v.get('tone', ''):<12}) -> {reason}")

    print("\n💡 Run 'python update_gemini_voices.py --update' to refresh config/gemini_voices.json.")
    print("=" * 70 + "\n")


def update_voice_catalog(config: Dict[str, Any]) -> None:
    """
    Fetches upstream catalog, updates config/gemini_voices.json, and prints summary.
    """
    upstream = fetch_upstream_voices(config)
    curated_data = build_curated_voices_json(upstream, config)

    VOICES_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VOICES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(curated_data, f, indent=2)

    print("\n" + "=" * 70)
    print("✨ GEMINI VOICES CONFIGURATION REFRESHED")
    print("=" * 70)
    print(f"📁 Target File:           {VOICES_JSON_PATH}")
    print(f"✅ Vetted English Voices: {curated_data['_meta']['total_vetted_voices']}")
    print(f"🚫 Excluded Voices:       {len(curated_data['_meta']['excluded_voices'])}")
    print(f"🕒 Timestamp:             {curated_data['_meta']['last_updated']}")

    print("\n🌟 Featured Personas in Catalog:")
    for v in curated_data["voices"]:
        if v.get("is_featured"):
            style_cue = v.get("recommended_style") or v.get("recommended_tags", "")
            print(f"  • {v['name']:<10} ({v['gender']}, {v['tone']}) -> {v.get('announcer_style', '')} [{style_cue}]")

    print("\n🎙️  Additional Vetted Announcer Personas:")
    for v in curated_data["voices"]:
        if not v.get("is_featured"):
            print(f"  • {v['name']:<10} ({v['gender']}, {v['tone']}) -> {v.get('announcer_style', '')}")

    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Refresh and audit Google Gemini TTS voices for TeamHypeAI sports announcements."
    )
    parser.add_argument("--check", action="store_true", help="Audit local voice config against upstream catalog (default)")
    parser.add_argument("--update", action="store_true", help="Fetch and save curated high-energy English voices to config/gemini_voices.json")
    parser.add_argument("--all", action="store_true", help="Include full list of excluded voices in audit report")

    args = parser.parse_args()
    config = load_config(VOICES_JSON_PATH)

    if args.update:
        update_voice_catalog(config)
    else:
        audit_voice_catalog(config, show_all=args.all)


if __name__ == "__main__":
    main()
