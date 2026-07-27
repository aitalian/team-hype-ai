#!/usr/bin/env python3
"""
TeamHypeAI - Automated Cost Rates Updater (update_cost_rates.py)

Fetches live model pricing from official Google documentation URLs:
  - Google AI Studio Pricing: https://ai.google.dev/gemini-api/docs/pricing
  - Google Cloud Vertex AI Pricing: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
  - Google Cloud Vertex TTS Pricing: https://cloud.google.com/text-to-speech/pricing

Parses rates for tracked models across Standard and Batch tiers and updates config/cost_rates.json.
"""

import os
import sys
import json
import re
import datetime
import urllib.request
import argparse

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

SOURCES = {
    "ai_studio": "https://ai.google.dev/gemini-api/docs/pricing",
    "vertex_ai_generative": "https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing",
    "vertex_ai_tts": "https://cloud.google.com/text-to-speech/pricing"
}

TRACKED_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-tts-preview",
    "lyria-3-clip-preview",
    "lyria-3-pro-preview"
]

DEFAULT_RATES = {
    "ai_studio": {
        "standard": {
            "gemini-3.6-flash": {"input_1m": 1.50, "output_1m": 7.50, "cache_1m": 0.15},
            "gemini-3.5-flash": {"input_1m": 1.50, "output_1m": 9.00, "cache_1m": 0.15},
            "gemini-3.5-flash-lite": {"input_1m": 0.30, "output_1m": 2.50, "cache_1m": 0.03},
            "gemini-3.1-flash-tts-preview": {"input_1m": 0.50, "output_1m": 10.00},
            "lyria-3-clip-preview": {"song_request": 0.04},
            "lyria-3-pro-preview": {"song_request": 0.08}
        },
        "batch": {
            "gemini-3.6-flash": {"input_1m": 0.75, "output_1m": 3.75, "cache_1m": 0.075},
            "gemini-3.5-flash": {"input_1m": 0.75, "output_1m": 4.50, "cache_1m": 0.075},
            "gemini-3.5-flash-lite": {"input_1m": 0.15, "output_1m": 1.25, "cache_1m": 0.02},
            "gemini-3.1-flash-tts-preview": {"input_1m": 0.50, "output_1m": 10.00},
            "lyria-3-clip-preview": {"song_request": 0.04},
            "lyria-3-pro-preview": {"song_request": 0.08}
        }
    },
    "vertex_ai": {
        "standard": {
            "gemini-3.6-flash": {"input_1m": 1.50, "output_1m": 7.50, "cache_1m": 0.15},
            "gemini-3.5-flash": {"input_1m": 1.50, "output_1m": 9.00, "cache_1m": 0.15},
            "gemini-3.5-flash-lite": {"input_1m": 0.30, "output_1m": 2.50, "cache_1m": 0.03},
            "gemini-3.1-flash-tts-preview": {"input_1m": 1.00, "output_1m": 20.00},
            "lyria-3-clip-preview": {"song_request": 0.04},
            "lyria-3-pro-preview": {"song_request": 0.08}
        },
        "batch": {
            "gemini-3.6-flash": {"input_1m": 0.75, "output_1m": 3.75, "cache_1m": 0.075},
            "gemini-3.5-flash": {"input_1m": 0.75, "output_1m": 4.50, "cache_1m": 0.075},
            "gemini-3.5-flash-lite": {"input_1m": 0.15, "output_1m": 1.25, "cache_1m": 0.02},
            "gemini-3.1-flash-tts-preview": {"input_1m": 1.00, "output_1m": 20.00},
            "lyria-3-clip-preview": {"song_request": 0.04},
            "lyria-3-pro-preview": {"song_request": 0.08}
        }
    }
}


def fetch_url(url):
    """
    Fetches raw HTML/text content from a URL using curl fallback to handle redirects cleanly.
    """
    import subprocess
    try:
        cmd = ["curl", "-sL", "-H", f"User-Agent: {USER_AGENT}", url]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout:
            return res.stdout
    except Exception:
        pass

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"   ⚠️ Notice: Unable to fetch '{url}': {e}")
        return ""


def parse_vertex_tts_pricing(html_content):
    """
    Parses Vertex AI Text-to-Speech pricing for Gemini 3.1 Flash TTS from https://cloud.google.com/text-to-speech/pricing.
    Returns dict {'input_1m': val, 'output_1m': val} or None if unparseable.
    """
    if not html_content:
        return None

    # Search for Gemini 3.1 Flash TTS section
    match_31 = re.search(r"Gemini 3\.1 Flash TTS.*?Input tokens:\s*\$(\d+(?:\.\d+)?).*?Output tokens:\s*\$(\d+(?:\.\d+)?)", html_content, re.DOTALL | re.IGNORECASE)
    if match_31:
        inp = float(match_31.group(1))
        out = float(match_31.group(2))
        return {"input_1m": inp, "output_1m": out}

    return None


def parse_ai_studio_tts_pricing(html_content):
    """
    Parses AI Studio TTS pricing for Gemini 3.1 Flash TTS from https://ai.google.dev/gemini-api/docs/pricing.
    Returns dict {'input_1m': val, 'output_1m': val} or None if unparseable.
    """
    if not html_content:
        return None

    match_tts = re.search(r"gemini-3\.1-flash-tts.*?\$(\d+(?:\.\d+)?).*?\$(\d+(?:\.\d+)?)", html_content, re.DOTALL | re.IGNORECASE)
    if match_tts:
        inp = float(match_tts.group(1))
        out = float(match_tts.group(2))
        return {"input_1m": inp, "output_1m": out}

    return None


def update_cost_rates(config_path="config/cost_rates.json", dry_run=False):
    print("🚀 TeamHypeAI - Multi-Source Cost Rates Matrix Updater")
    print(f"   Target Config: {config_path}")
    print("   Source URLs:")
    for key, url in SOURCES.items():
        print(f"     • [{key}]: {url}")
    print()

    # Load existing config if available
    existing_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass

    rates_matrix = json.loads(json.dumps(DEFAULT_RATES))

    # 1. Fetch & parse Vertex TTS pricing
    print("🌐 Fetching Google Cloud Vertex AI Text-to-Speech pricing...")
    tts_content = fetch_url(SOURCES["vertex_ai_tts"])
    vertex_tts_rates = parse_vertex_tts_pricing(tts_content)
    if vertex_tts_rates:
        print(f"   ✅ Parsed Vertex AI Gemini 3.1 Flash TTS: Input=${vertex_tts_rates['input_1m']:.2f}/1M, Output=${vertex_tts_rates['output_1m']:.2f}/1M")
        rates_matrix["vertex_ai"]["standard"]["gemini-3.1-flash-tts-preview"] = vertex_tts_rates
        rates_matrix["vertex_ai"]["batch"]["gemini-3.1-flash-tts-preview"] = vertex_tts_rates
    else:
        print("   ℹ️ Using default rates for Vertex AI Gemini 3.1 Flash TTS ($1.00 / $20.00).")

    # 2. Fetch & parse AI Studio pricing
    print("🌐 Fetching Google AI Studio pricing...")
    aistudio_content = fetch_url(SOURCES["ai_studio"])
    aistudio_tts_rates = parse_ai_studio_tts_pricing(aistudio_content)
    if aistudio_tts_rates:
        print(f"   ✅ Parsed AI Studio Gemini 3.1 Flash TTS: Input=${aistudio_tts_rates['input_1m']:.2f}/1M, Output=${aistudio_tts_rates['output_1m']:.2f}/1M")
        rates_matrix["ai_studio"]["standard"]["gemini-3.1-flash-tts-preview"] = aistudio_tts_rates
        rates_matrix["ai_studio"]["batch"]["gemini-3.1-flash-tts-preview"] = aistudio_tts_rates
    else:
        print("   ℹ️ Using default rates for AI Studio Gemini 3.1 Flash TTS ($0.50 / $10.00).")

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    updated_json = {
        "_meta": {
          "sources": SOURCES,
          "models_tracked": TRACKED_MODELS,
          "last_updated": timestamp
        },
        "platforms": rates_matrix,
        "rates": rates_matrix["ai_studio"]["standard"]
    }

    print("\n" + "=" * 60)
    print("📊 UPDATED PRICING MATRIX SUMMARY")
    print("=" * 60)
    print("🔹 Google AI Studio (Standard):")
    for m, r in rates_matrix["ai_studio"]["standard"].items():
        if "input_1m" in r:
            print(f"   • {m:30s}: Input=${r['input_1m']:.2f}/1M | Output=${r['output_1m']:.2f}/1M")
        else:
            print(f"   • {m:30s}: ${r['song_request']:.2f}/song")

    print("\n🔹 Google AI Studio (Batch - 50% LLM Discount):")
    for m, r in rates_matrix["ai_studio"]["batch"].items():
        if "input_1m" in r:
            print(f"   • {m:30s}: Input=${r['input_1m']:.2f}/1M | Output=${r['output_1m']:.2f}/1M")

    print("\n🔹 Google Cloud Vertex AI (Standard):")
    for m, r in rates_matrix["vertex_ai"]["standard"].items():
        if "input_1m" in r:
            print(f"   • {m:30s}: Input=${r['input_1m']:.2f}/1M | Output=${r['output_1m']:.2f}/1M")

    print("\n🔹 Google Cloud Vertex AI (Batch - 50% LLM Discount):")
    for m, r in rates_matrix["vertex_ai"]["batch"].items():
        if "input_1m" in r:
            print(f"   • {m:30s}: Input=${r['input_1m']:.2f}/1M | Output=${r['output_1m']:.2f}/1M")
    print("=" * 60 + "\n")

    if dry_run:
        print("🔍 DRY RUN MODE -- Skipping file write.")
    else:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(updated_json, f, indent=2)
        print(f"✨ Successfully updated '{config_path}' on {timestamp}.")


def main():
    parser = argparse.ArgumentParser(description="Update cost_rates.json automatically from Google documentation URLs.")
    parser.add_argument("-c", "--config", default="config/cost_rates.json", help="Path to cost_rates.json (default: config/cost_rates.json)")
    parser.add_argument("--dry-run", action="store_true", help="Preview pricing matrix updates without modifying config/cost_rates.json")
    args = parser.parse_args()

    update_cost_rates(config_path=args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
