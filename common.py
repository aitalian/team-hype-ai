#!/usr/bin/env python3
"""
TeamHypeAI

Centralized module providing single-sourced constants, environment helpers,
and strict JSON configuration loaders for voice definitions and API cost rates.
"""

import os
import sys
import json
import datetime


def log_api_event(category, action, details="", log_path="logs/api_execution.log"):
    """
    Appends a timestamped, structured execution log entry to logs/api_execution.log.
    Sanitizes sensitive information (API keys) and formats detailed response metadata.
    """
    try:
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if isinstance(details, dict):
            details_str = json.dumps(details, default=str)
        else:
            details_str = str(details)

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key and api_key in details_str:
            details_str = details_str.replace(api_key, "[REDACTED_API_KEY]")

        log_entry = f"[{timestamp}] [{category}] [{action}] {details_str}\n"

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

# Default Models & Voice Persona
DEFAULT_TTS_MODEL = "gemini-3.1-flash-tts-preview"
DEFAULT_LLM_MODEL = "gemini-3.6-flash"
DEFAULT_MUSIC_MODEL = "lyria-3-clip-preview"
DEFAULT_VOICE_PERSONA = "Puck"
DEFAULT_ENHANCE_MODE = "auto"
DEFAULT_AUDIO_TAGS = "[excitedly, fast-paced]"

PRICING_DISCLAIMER_TEXT = (
    "⚠️  DISCLAIMER: This figure is only an estimate based on sample\n"
    "   token and duration projections for expected API calls.\n"
    "   Actual API rates and billing are subject to change. The onus is on\n"
    "   the user to validate expected charges on the official Google Gemini API pricing page:\n"
    "   🔗 https://ai.google.dev/gemini-api/docs/pricing\n"
    "   ℹ️  * Note: Audio tokens correspond to 25 tokens per second of generated audio."
)


def print_pricing_disclaimer():
    """
    Prints a single-sourced DRY cost estimation disclaimer across all CLI outputs.
    """
    print(PRICING_DISCLAIMER_TEXT)


def load_dotenv_if_present(env_path=".env"):
    """
    Automatically loads environment variables from a local .env file if present.
    """
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception:
            pass


def load_json_file(file_path, description="JSON configuration"):
    """
    Strictly loads a JSON file. Raises a clear error and exits if missing or unparseable.
    """
    if not os.path.exists(file_path):
        print(f"\n❌ CRITICAL ERROR: Required {description} '{file_path}' is missing.")
        print(f"   Please ensure '{file_path}' exists in the repository.")
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: Failed to parse {description} '{file_path}': {e}")
        sys.exit(1)


def load_gemini_voices(json_path="config/gemini_voices.json"):
    """
    Loads prebuilt Gemini voice persona definitions and descriptions from config/gemini_voices.json.
    """
    data = load_json_file(json_path, description="voice definitions file")
    voices = data.get("voices", [])
    if not voices:
        print(f"\n❌ CRITICAL ERROR: No 'voices' array found in '{json_path}'.")
        sys.exit(1)
    return voices


def load_cost_rates(json_path="config/cost_rates.json"):
    """
    Loads API cost rate definitions from config/cost_rates.json.
    """
    data = load_json_file(json_path, description="cost rates file")
    rates = data.get("rates", {})
    if not rates:
        print(f"\n❌ CRITICAL ERROR: No 'rates' object found in '{json_path}'.")
        sys.exit(1)
    return rates


def get_model_cost_rates(model_name, category="voice", json_path="config/cost_rates.json"):
    """
    Retrieves pricing rate estimates for a specified model from config/cost_rates.json.
    Fails and returns an error if the model or required rates are missing.
    """
    cost_rates = load_cost_rates(json_path)

    if model_name not in cost_rates:
        if category == "voice":
            supported = ", ".join([m for m in cost_rates.keys() if "input_1m" in cost_rates[m]])
            print(f"\n❌ Error: Cost rate estimates for TTS/LLM model '{model_name}' are not configured on file.")
            print(f"   Supported voice models with rate estimates: {supported}")
        else:
            supported = ", ".join([m for m in cost_rates.keys() if "song_request" in cost_rates[m]])
            print(f"\n❌ Error: Cost rate estimates for Music model '{model_name}' are not configured on file.")
            print(f"   Supported music models with rate estimates: {supported}")
        sys.exit(1)

    rates = cost_rates[model_name]

    if category == "voice":
        if "input_1m" not in rates or "output_1m" not in rates:
            print(f"\n❌ Error: Missing required 'input_1m' or 'output_1m' rate estimates for model '{model_name}'.")
            sys.exit(1)
    elif category == "music":
        if "song_request" not in rates:
            print(f"\n❌ Error: Missing required 'song_request' rate estimate for Music model '{model_name}'.")
            sys.exit(1)

    return rates

