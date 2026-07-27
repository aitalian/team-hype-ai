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

def print_pricing_disclaimer(use_vertex=False, has_tts=True, has_llm=True, has_music=True, json_path="config/cost_rates.json"):
    """
    Prints cost estimation disclaimer displaying relevant pricing URLs sourced dynamically from config/cost_rates.json.
    """
    sources = {
        "ai_studio": "https://ai.google.dev/gemini-api/docs/pricing",
        "vertex_ai_generative": "https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing",
        "vertex_ai_tts": "https://cloud.google.com/text-to-speech/pricing"
    }
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                meta_sources = data.get("_meta", {}).get("sources", {})
                if isinstance(meta_sources, dict):
                    sources.update(meta_sources)
        except Exception:
            pass

    print("⚠️  DISCLAIMER: This figure is only an estimate based on sample")
    print("   token and duration projections for expected API calls.")
    print("   Actual API rates and billing are subject to change. The onus is on")
    print("   the user to validate expected charges on official Google pricing pages:")

    if use_vertex:
        if (has_llm or has_music) and "vertex_ai_generative" in sources:
            print(f"   🔗 Vertex AI Generative AI: {sources['vertex_ai_generative']}")
        if has_tts and "vertex_ai_tts" in sources:
            print(f"   🔗 Vertex AI Text-to-Speech: {sources['vertex_ai_tts']}")
    else:
        if "ai_studio" in sources:
            print(f"   🔗 Google AI Studio Pricing: {sources['ai_studio']}")

    print("   ℹ️  * Note: Audio tokens correspond to 25 tokens per second of generated audio.")


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


def get_model_cost_rates(model_name, category="voice", json_path="config/cost_rates.json", use_vertex=False, is_batch=False):
    """
    Retrieves pricing rate estimates for a specified model from config/cost_rates.json,
    taking into account platform (Google AI Studio vs Vertex AI) and API mode (Standard vs Batch).
    """
    data = load_json_file(json_path, description="cost rates file")

    platform_key = "vertex_ai" if use_vertex else "ai_studio"
    mode_key = "batch" if is_batch else "standard"

    cost_rates = None
    if "platforms" in data and platform_key in data["platforms"]:
        plat_data = data["platforms"][platform_key]
        if mode_key in plat_data:
            cost_rates = plat_data[mode_key]

    if not cost_rates:
        cost_rates = data.get("rates", {})

    if model_name not in cost_rates:
        default_rates = data.get("rates", {})
        if model_name in default_rates:
            rates = default_rates[model_name]
        else:
            if category == "voice":
                supported = ", ".join([m for m in cost_rates.keys() if "input_1m" in cost_rates[m]])
                print(f"\n❌ Error: Cost rate estimates for TTS/LLM model '{model_name}' are not configured on file.")
                print(f"   Supported voice models with rate estimates: {supported}")
            else:
                supported = ", ".join([m for m in cost_rates.keys() if "song_request" in cost_rates[m]])
                print(f"\n❌ Error: Cost rate estimates for Music model '{model_name}' are not configured on file.")
                print(f"   Supported music models with rate estimates: {supported}")
            sys.exit(1)
    else:
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


def init_gemini_client(api_key=None, use_vertex=None, project=None, location=None):
    """
    Initializes a google.genai.Client instance supporting both Google AI Studio and Vertex AI platforms.
    
    Resolution for Vertex AI mode:
      use_vertex: CLI flag / explicit arg > GOOGLE_GENAI_USE_VERTEXAI env var ('true'/'1') > False
      project: CLI flag / explicit arg > GOOGLE_CLOUD_PROJECT or GCP_PROJECT env var
      location: CLI flag / explicit arg > GOOGLE_CLOUD_LOCATION or GCP_LOCATION env var > 'us-central1'
    """
    load_dotenv_if_present()

    try:
        from google import genai
    except ImportError:
        print("❌ Error: google-genai library missing.")
        print("   Please install via: pip install google-genai")
        sys.exit(1)

    env_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower().strip() in ["true", "1", "yes"]
    is_vertex = use_vertex if use_vertex is not None else env_vertex

    api_key_val = api_key or os.environ.get("GEMINI_API_KEY")

    if is_vertex:
        gcp_proj = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        gcp_loc = location or os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("GCP_LOCATION") or "us-central1"

        client_kwargs = {
            "vertexai": True,
            "project": gcp_proj,
            "location": gcp_loc
        }
        if api_key_val:
            client_kwargs["api_key"] = api_key_val

        auth_desc = "GCP API Key" if api_key_val else "Application Default Credentials (ADC)"
        print(f"🔑 Google Cloud Vertex AI client initializing (Project: '{gcp_proj or 'ADC/Default'}', Region: '{gcp_loc}', Auth: {auth_desc}).")
        return genai.Client(**client_kwargs)
    else:
        if not api_key_val:
            print("\n❌ CRITICAL ERROR: GEMINI_API_KEY environment variable is missing.")
            print("   This project uses Google Gemini & Lyria AI models for audio generation.")
            print("   Please set your key in .env or environment and re-run:")
            print("     export GEMINI_API_KEY='your_google_gemini_api_key'")
            print("   Or enable Vertex AI mode via:")
            print("     python generate_gemini_audio.py --vertexai --gcp-project YOUR_PROJECT_ID")
            print("   Or preview prompts and cost estimates using:")
            print("     python generate_gemini_audio.py --dry-run\n")
            sys.exit(1)

        print("🔑 GEMINI API Key detected (sourced from environment / .env). Initializing Google AI Studio client.")
        return genai.Client(api_key=api_key_val)


