#!/usr/bin/env python3
"""
TeamHypeAI - Model & Pricing Rate Updater (update_cost_rates.py)

Fetches available Google Gemini and Lyria models, compares them against the
tracked subset loaded directly from config/cost_rates.json (DRY single source of truth),
suggests newer versions, and synchronizes config/cost_rates.json and README.md.

Usage:
    python update_cost_rates.py --check             # Compare and suggest newer models
    python update_cost_rates.py --check --json      # Output comparison in JSON format
    python update_cost_rates.py --update            # Update config/cost_rates.json and sync README.md
    python update_cost_rates.py --sync-readme       # Sync model name references in README.md
    python update_cost_rates.py --dry-run           # Preview updates without modifying files
"""

import os
import sys
import json
import re
import datetime
import urllib.request
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_PATH = PROJECT_ROOT / "config" / "cost_rates.json"
README_PATH = PROJECT_ROOT / "README.md"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

# Fallback sources if not present in config/cost_rates.json
DEFAULT_SOURCES = {
    "ai_studio": "https://ai.google.dev/pricing",
    "gemini_models": "https://ai.google.dev/gemini-api/docs/models/gemini",
    "gemini_tts": "https://ai.google.dev/gemini-api/docs/speech-generation",
    "vertex_ai_generative": "https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing",
    "vertex_ai_tts": "https://cloud.google.com/text-to-speech/pricing"
}


def load_config(config_path: Path = CONFIG_PATH) -> Dict[str, Any]:
    """
    Loads config/cost_rates.json as the single source of truth.
    Strictly loads cached tracked_models and platform rate cards.
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

    # Ensure required top-level keys exist
    if "tracked_models" not in data:
        data["tracked_models"] = {}
    if "_meta" not in data:
        data["_meta"] = {"sources": DEFAULT_SOURCES, "models_tracked": []}
    elif "sources" not in data["_meta"]:
        data["_meta"]["sources"] = DEFAULT_SOURCES

    return data


def save_config(data: Dict[str, Any], config_path: Path = CONFIG_PATH) -> None:
    """Saves updated data to config/cost_rates.json with timestamp."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["_meta"]["last_updated"] = timestamp
    data["_meta"]["models_tracked"] = list(data.get("tracked_models", {}).keys())

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Successfully updated {config_path} on {timestamp}.")


def fetch_url(url: str) -> str:
    """Fetches raw text content from a URL using curl fallback."""
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
        return ""


def parse_vertex_tts_pricing(html_content: str) -> Optional[Dict[str, float]]:
    """Parses Vertex AI Text-to-Speech pricing from cloud.google.com/text-to-speech/pricing."""
    if not html_content:
        return None
    match = re.search(r"Gemini.*?Flash TTS.*?Input tokens:\s*\$(\d+(?:\.\d+)?).*?Output tokens:\s*\$(\d+(?:\.\d+)?)",
                      html_content, re.DOTALL | re.IGNORECASE)
    if match:
        return {"input_1m": float(match.group(1)), "output_1m": float(match.group(2))}
    return None


def fetch_api_models(tracked_models: Dict[str, Any], use_vertexai: bool = False) -> List[Dict[str, Any]]:
    """
    Attempts to fetch models list from Google GenAI API.
    Falls back gracefully to the cached models loaded from config/cost_rates.json.
    """
    try:
        from common import init_gemini_client
        client = init_gemini_client(use_vertex=use_vertexai)

        models = []
        for model in client.models.list():
            m_id = getattr(model, "name", "")
            if m_id.startswith("models/"):
                m_id = m_id[len("models/"):]
            models.append({
                "id": m_id,
                "display_name": getattr(model, "display_name", m_id),
                "description": getattr(model, "description", "")
            })
        return models
    except Exception:
        # DRY Fallback: return model definitions loaded directly from config/cost_rates.json
        return [
            {
                "id": m_id,
                "display_name": meta.get("display_name", m_id),
                "description": meta.get("description", "")
            }
            for m_id, meta in tracked_models.items()
        ]


def categorize_model(model_id: str) -> Optional[str]:
    """Categorize model into relevant TeamHypeAI functional pillars."""
    m_lower = model_id.lower()
    if "tts" in m_lower or "speech" in m_lower:
        return "tts_voice"
    if "lyria" in m_lower or "music" in m_lower:
        return "music_generator"
    if "flash" in m_lower:
        return "announcer_script"
    return None


def extract_version_number(model_id: str) -> float:
    """Extract numeric version rank from model ID (e.g. 'gemini-3.8-flash' -> 3.8)."""
    match = re.search(r"(\d+(?:\.\d+)?)", model_id)
    return float(match.group(1)) if match else 1.0


def compare_and_suggest_models(available_models: List[Dict[str, Any]],
                               tracked_models: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares the available models list against the manually tracked subset
    loaded from config/cost_rates.json and suggests if newer versions are available.
    """
    by_category_tracked: Dict[str, List[Tuple[str, float]]] = {
        "announcer_script": [],
        "tts_voice": [],
        "music_generator": []
    }

    for m_id, meta in tracked_models.items():
        role = meta.get("role") or categorize_model(m_id)
        if role in by_category_tracked:
            v_rank = meta.get("version_rank", extract_version_number(m_id))
            by_category_tracked[role].append((m_id, v_rank))

    suggestions = []
    # Identify highest tracked version per role
    max_tracked = {}
    for role, items in by_category_tracked.items():
        if items:
            max_tracked[role] = max(items, key=lambda x: x[1])

    # Check available models against tracked max
    for m in available_models:
        m_id = m["id"]
        role = categorize_model(m_id)
        if not role:
            continue

        m_rank = extract_version_number(m_id)
        current_max = max_tracked.get(role)

        # If model is not tracked or has a higher/newer version
        if current_max and m_rank > current_max[1]:
            suggestions.append({
                "model_id": m_id,
                "role": role,
                "display_name": m.get("display_name", m_id),
                "current_tracked_model": current_max[0],
                "current_version": current_max[1],
                "newer_version": m_rank,
                "recommendation": f"Newer {role} generation available: '{m_id}' (v{m_rank}) supersedes '{current_max[0]}' (v{current_max[1]})."
            })

    # Check if active project defaults in common.py are behind top tracked models
    try:
        from common import DEFAULT_LLM_MODEL, DEFAULT_TTS_MODEL, DEFAULT_MUSIC_MODEL
        active_defaults = {
            "announcer_script": DEFAULT_LLM_MODEL,
            "tts_voice": DEFAULT_TTS_MODEL,
            "music_generator": DEFAULT_MUSIC_MODEL
        }
        for role, active_model in active_defaults.items():
            active_rank = extract_version_number(active_model)
            top = max_tracked.get(role)
            if top and (top[1] > active_rank or ("preview" in active_model and "preview" not in top[0])):
                suggestions.append({
                    "model_id": top[0],
                    "role": role,
                    "display_name": tracked_models[top[0]]["display_name"],
                    "current_tracked_model": active_model,
                    "current_version": active_rank,
                    "newer_version": top[1],
                    "recommendation": f"Active default '{active_model}' can be upgraded to '{top[0]}' (v{top[1]})."
                })
    except Exception:
        pass

    return {
        "tracked_count": len(tracked_models),
        "available_count": len(available_models),
        "suggestions": suggestions
    }


def sync_readme_models(replacements: Optional[Dict[str, str]] = None) -> bool:
    """
    Synchronizes model references in README.md to ensure documentation
    reflects the tracked models and defaults.
    """
    if not README_PATH.exists():
        print(f"⚠️ Warning: README.md not found at {README_PATH}")
        return False

    content = README_PATH.read_text(encoding="utf-8")
    original = content

    if replacements is None:
        replacements = {
            "gemini-3.6-flash": "gemini-3.8-flash",
            "gemini-3.1-flash-tts-preview": "gemini-3.8-flash-tts",
            "lyria-3-clip-preview": "lyria-3.5"
        }

    updated_keys = []
    for old_m, new_m in replacements.items():
        if old_m in content:
            content = content.replace(old_m, new_m)
            updated_keys.append(f"{old_m} ➔ {new_m}")

    if content != original:
        README_PATH.write_text(content, encoding="utf-8")
        print("📄 README.md Model Reference Updates:")
        for u in updated_keys:
            print(f"   • Updated reference: {u}")
        print("✅ Successfully synchronized README.md model references.")
        return True
    else:
        print("ℹ️ README.md is already up to date with tracked model references.")
        return False


def sync_platforms_and_rates(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronizes the platforms matrix and rates tables dynamically
    from the loaded tracked_models without hardcoding.
    """
    tracked_models = config_data.get("tracked_models", {})

    platforms = {
        "ai_studio": {"standard": {}, "batch": {}},
        "vertex_ai": {"standard": {}, "batch": {}}
    }
    rates_flat = {}

    for m_id, meta in tracked_models.items():
        m_rates = meta.get("rates", {})
        ais = m_rates.get("ai_studio", {})
        vtx = m_rates.get("vertex_ai", {})

        ais_std = ais.get("standard", {})
        ais_bat = ais.get("batch", {})
        vtx_std = vtx.get("standard", {})
        vtx_bat = vtx.get("batch", {})

        if ais_std:
            platforms["ai_studio"]["standard"][m_id] = ais_std
            rates_flat[m_id] = ais_std
        if ais_bat:
            platforms["ai_studio"]["batch"][m_id] = ais_bat
        if vtx_std:
            platforms["vertex_ai"]["standard"][m_id] = vtx_std
        if vtx_bat:
            platforms["vertex_ai"]["batch"][m_id] = vtx_bat

    config_data["platforms"] = platforms
    config_data["rates"] = rates_flat
    return config_data


def print_comparison_report(comparison: Dict[str, Any], tracked_models: Dict[str, Any]):
    """Prints a clear, formatted comparison and suggestion report from cached config."""
    print("\n" + "=" * 70)
    print("📊 TEAMHYPEAI - MODEL & PRICING TRACKING REPORT")
    print("=" * 70)

    print("\n📌 CURRENTLY TRACKED MODELS SUBSET (from config/cost_rates.json):")
    for m_id, meta in tracked_models.items():
        role = meta.get("role", "general")
        status = meta.get("status", "active")
        channels = ", ".join(meta.get("supported_channels", ["ai_studio"]))
        print(f"  • {m_id:<30} [{role:<17}] Status: {status:<7} Channels: ({channels})")

    suggestions = comparison.get("suggestions", [])
    print(f"\n💡 VERSION UPGRADE RECOMMENDATIONS ({len(suggestions)}):")
    if not suggestions:
        print("  • All tracked models are at their latest known generation! No upgrades pending.")
    else:
        for s in suggestions:
            print(f"  ✨ {s['role'].upper()}: {s['recommendation']}")
            print(f"     Candidate Model: {s['model_id']} | Display: {s['display_name']}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Update and track models and pricing for TeamHypeAI.")
    parser.add_argument("-c", "--config", default=str(CONFIG_PATH), help=f"Path to cost_rates.json (default: {CONFIG_PATH})")
    parser.add_argument("--check", action="store_true", help="Compare models against tracked subset and suggest newer versions.")
    parser.add_argument("--update", action="store_true", help="Update config/cost_rates.json with latest models, info, documentation, and pricing.")
    parser.add_argument("--sync-readme", action="store_true", help="Synchronize model name references in README.md.")
    parser.add_argument("--dry-run", action="store_true", help="Preview pricing matrix updates without modifying files.")
    parser.add_argument("--json", action="store_true", help="Output comparison report in JSON format.")
    platform_group = parser.add_mutually_exclusive_group()
    platform_group.add_argument("--vertexai", action="store_true", default=None, help="Query models using Google Cloud Vertex AI infrastructure.")
    platform_group.add_argument("--aistudio", "--ai-studio", "--no-vertexai", action="store_true", default=None, help="Force Google AI Studio infrastructure (overrides GOOGLE_GENAI_USE_VERTEXAI in .env).")
    args = parser.parse_args()

    # Default to check if no action specified
    if not (args.check or args.update or args.sync_readme or args.json or args.dry_run):
        args.check = True

    config_path = Path(args.config)
    config_data = load_config(config_path)
    tracked_models = config_data.get("tracked_models", {})

    from common import resolve_platform_backend
    use_vertex, _, _, _ = resolve_platform_backend(cli_vertexai=args.vertexai, cli_aistudio=args.aistudio, config=config_data)
    available_models = fetch_api_models(tracked_models=tracked_models, use_vertexai=use_vertex)
    comparison = compare_and_suggest_models(available_models, tracked_models)

    if args.json:
        print(json.dumps(comparison, indent=2))
        return

    print_comparison_report(comparison, tracked_models)

    if args.sync_readme:
        sync_readme_models()

    if args.update or args.dry_run:
        # Check live sources for any rate updates
        sources = config_data.get("_meta", {}).get("sources", DEFAULT_SOURCES)
        if "vertex_ai_tts" in sources:
            tts_html = fetch_url(sources["vertex_ai_tts"])
            tts_rates = parse_vertex_tts_pricing(tts_html)
            if tts_rates:
                # Update Vertex AI TTS rates in tracked models
                for m_id, meta in tracked_models.items():
                    if meta.get("role") == "tts_voice" and "vertex_ai" in meta.get("supported_channels", []):
                        meta.setdefault("rates", {}).setdefault("vertex_ai", {}).setdefault("standard", {}).update(tts_rates)
                        meta["rates"]["vertex_ai"].setdefault("batch", {}).update(tts_rates)

        # Synchronize platform matrices and rates lookup table
        config_data = sync_platforms_and_rates(config_data)

        if args.dry_run:
            print(f"🔍 DRY RUN MODE -- Skipping file write to '{config_path}' and README.md.")
        else:
            save_config(config_data, config_path)
            sync_readme_models()


if __name__ == "__main__":
    main()
