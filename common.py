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
import re
import textwrap
from typing import Optional, Dict, Any, List


def supports_color() -> bool:
    """Checks whether the current terminal supports ANSI color escape codes."""
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def print_cli_banner(utility_title: str, what_it_is: str, how_it_works: str, width: int = 78):
    """
    Renders a solid colored block sports bullhorn logo, highly legible block
    TeamHypeAI typography, and a standardized context box explaining the utility.
    """
    use_color = supports_color()

    if use_color:
        reset = "\033[0m"
        bold = "\033[1m"
        dim = "\033[2m"
        red = "\033[38;5;196m"
        orange = "\033[38;5;208m"
        gold = "\033[38;5;220m"
        yellow = "\033[38;5;226m"
        cyan = "\033[38;5;51m"
        white = "\033[38;5;231m"
        gray = "\033[38;5;245m"
        border = "\033[38;5;69m"
    else:
        reset = bold = dim = ""
        red = orange = gold = yellow = cyan = white = gray = border = ""

    # Solid colored block bullhorn / stadium horn (centered)
    h_pad = " " * 24
    horn_lines = [
        f"{h_pad}       {orange}▄▄████{gold}██{reset}",
        f"{h_pad}    {orange}▄████████{gold}██{reset}   {cyan}▄   {white}▄{reset}",
        f"{h_pad} {red}███{orange}████████{gold}██{reset}  {cyan}██  {white}██{reset}",
        f"{h_pad} {red}███{orange}████████{gold}██{reset}  {cyan}██  {white}██{reset}",
        f"{h_pad}    {orange}▀████████{gold}██{reset}   {cyan}▀   {white}▀{reset}",
        f"{h_pad}       {orange}▀▀████{gold}██{reset}",
        f"{h_pad}     {gold}██{reset}",
        f"{h_pad}     {gold}██{reset}",
    ]

    # Clean, bold, highly legible 5-line block typography
    T = ["█████", "  █  ", "  █  ", "  █  ", "  █  "]
    E = ["█████", "█    ", "████ ", "█    ", "█████"]
    A = ["▄███▄", "█   █", "█████", "█   █", "█   █"]
    M = ["█   █", "██ ██", "█ █ █", "█   █", "█   █"]

    H = ["█   █", "█   █", "█████", "█   █", "█   █"]
    Y = ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "]
    P = ["████▄", "█   █", "████▀", "█    ", "█    "]
    I = ["█████", "  █  ", "  █  ", "  █  ", "█████"]

    t_pad = " " * 8
    text_lines = []
    for r in range(5):
        team_part = f"{bold}{gold}{T[r]} {E[r]} {A[r]} {M[r]}{reset}"
        hype_part = f"{bold}{cyan}{H[r]} {Y[r]} {P[r]} {E[r]}{reset}"
        ai_part   = f"{bold}{white}{A[r]} {I[r]}{reset}"
        text_lines.append(f"{t_pad}{team_part}  {hype_part}  {ai_part}")

    s_pad = " " * 13
    subtitle = f"{s_pad}{gray}STADIUM INTRO AUDIO ENGINE {cyan}•{gray} GOOGLE GEMINI & LYRIA{reset}"

    logo_lines = [
        *horn_lines,
        "",
        *text_lines,
        "",
        subtitle
    ]

    inner_width = width - 4
    b_top = f"{border}┏{'━' * (width - 2)}┓{reset}"
    b_bottom = f"{border}┗{'━' * (width - 2)}┛{reset}"
    b_div = f"{border}┣{'━' * (width - 2)}┫{reset}"

    def format_field(label: str, text: str):
        wrap_width = inner_width - len(label) - 2
        wrapper = textwrap.TextWrapper(width=wrap_width)
        wrapped = wrapper.wrap(text) if text else [""]
        field_lines = []
        for i, w_line in enumerate(wrapped):
            if i == 0:
                prefix = f"{white}{bold}{label}:{reset} "
                padded = w_line.ljust(wrap_width)
                field_lines.append(f"{border}┃{reset} {prefix}{gray}{padded}{reset} {border}┃{reset}")
            else:
                indent = " " * (len(label) + 2)
                padded = w_line.ljust(wrap_width)
                field_lines.append(f"{border}┃{reset} {indent}{gray}{padded}{reset} {border}┃{reset}")
        return field_lines

    box_lines = [
        b_top,
        f"{border}┃{reset} {cyan}{bold}{utility_title.center(inner_width)}{reset} {border}┃{reset}",
        b_div,
        *format_field("WHAT IT IS", what_it_is),
        *format_field("HOW IT WORKS", how_it_works),
        b_bottom
    ]

    print("\n" + "\n".join(logo_lines))
    print("\n".join(box_lines) + "\n")


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
DEFAULT_TTS_MODEL = "gemini-3.8-flash-tts"
DEFAULT_LLM_MODEL = "gemini-3.8-flash"
DEFAULT_MUSIC_MODEL = "lyria-3.5"
DEFAULT_VOICE_PERSONA = "Puck"
DEFAULT_ENHANCE_MODE = "auto"
DEFAULT_SPEECH_STYLE = "excitedly, fast-paced arena announcer"
DEFAULT_AUDIO_TAGS = DEFAULT_SPEECH_STYLE  # Backwards-compatible alias for legacy references

# API Engine Constants (Interactions API preferred as of June 2026)
API_ENGINE_INTERACTIONS = "interactions"
API_ENGINE_LEGACY = "generate_content"
DEFAULT_API_ENGINE = API_ENGINE_INTERACTIONS

VALID_POINT_IN_TIME_TAGS = {
    "short pause", "pause", "breath", "cough", "sigh", "laugh", "gasp", "cheer", "groan", "shout"
}


def clean_style_directive(style: str) -> str:
    """
    Cleans a style string for Gemini 3.8 Flash TTS speech_metadata.style.
    Strips legacy enclosing brackets or angle tags if present (e.g. '[excitedly]' -> 'excitedly').
    """
    if not style:
        return ""
    s = str(style).strip()
    s = re.sub(r"[\[\]]", "", s).strip()
    s = re.sub(r"^<|>$", "", s).strip()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def format_speech_style(base_style: str, regional_accent: str = None, accent_guidance: str = None) -> str:
    """
    Combines a base delivery style string with regional accent guidance for Gemini 3.8 Flash TTS speech_metadata.style.
    Avoids duplicate phrases if the base_style already incorporates the accent.
    """
    clean_base = clean_style_directive(base_style)
    accent = (regional_accent or "").strip()
    if not accent:
        return clean_base

    # Check if accent already mentioned in base style
    if accent.lower() in clean_base.lower():
        return clean_base

    if "french" in accent.lower() or "quebec" in accent.lower():
        accent_clause = f"with a {accent} accent on French and Francophone names"
    else:
        accent_clause = f"with a {accent} accent"

    if clean_base:
        return f"{clean_base}, {accent_clause}"
    return accent_clause


def format_audio_tag(base_style: str, regional_accent: str = None, accent_guidance: str = None) -> str:
    """
    Backwards-compatible alias for format_speech_style().
    Normalizes legacy audio tags or style strings into clean delivery style strings for Gemini 3.8 Flash TTS speech_metadata.style.
    """
    return format_speech_style(base_style, regional_accent=regional_accent, accent_guidance=accent_guidance)


def clean_spoken_text(text: str, prefix: str = "", allow_vocal_tags: bool = True) -> str:
    """
    Sanitizes dialogue text before feeding into Gemini 3.8 Flash TTS speech synthesis.
    Strips:
      1. Explicit prompt prefixes (e.g. prefix parameter if matching)
      2. Any leading prompt/director directives (e.g. "Say rapidly with...", "Prompt:", "Announce with...")
      3. Any square bracketed audio tags (e.g. [excitedly], [shouting], [excitedly, fast-paced])
      4. Invalid/directorial angle tags while PRESERVING valid point-in-time vocal event tags
         (e.g. <short pause>, <sigh>, <breath>, <cheer>) per Gemini 3.8 TTS official documentation
      5. Consecutive whitespace
    Ensures Gemini 3.8 Flash TTS only vocalizes verbatim announcement dialogue.
    """
    if not text:
        return ""
    cleaned = str(text).strip()

    if prefix:
        prefix_clean = prefix.strip()
        if cleaned.startswith(prefix_clean):
            cleaned = cleaned[len(prefix_clean):].strip()

    if ":" in cleaned and any(cleaned.lower().startswith(kw) for kw in ["say ", "announce ", "speak ", "prompt:", "with ", "act ", "voice:"]):
        cleaned = cleaned.split(":", 1)[1].strip()

    # Strip square brackets completely (legacy tags e.g. [excitedly])
    cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)

    # Filter angle brackets: preserve valid vocal event tags if allow_vocal_tags is True
    if allow_vocal_tags:
        def replace_angle_tag(match):
            inner = match.group(1).lower().strip()
            if any(inner == tag or inner.startswith(tag) for tag in VALID_POINT_IN_TIME_TAGS):
                return f"<{inner}>"
            return ""
        cleaned = re.sub(r"<([^>]+)>", replace_angle_tag, cleaned)
    else:
        cleaned = re.sub(r"<[^>]*>", "", cleaned)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_mascot_slug(config_or_str) -> str:
    """
    Extracts and normalizes a clean lowercase mascot/team slug (e.g. 'canadiens', 'icebreakers')
    from a roster configuration dict or raw string.
    """
    if isinstance(config_or_str, dict):
        raw = (
            config_or_str.get("team_mascot")
            or config_or_str.get("mascot")
            or config_or_str.get("team_name")
            or ""
        )
    else:
        raw = str(config_or_str or "")
    slug = re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")
    return slug


def apply_mascot_slug_to_filename(filename: str, mascot_slug: str) -> str:
    """
    Appends '_{mascot_slug}' before the file extension for generated audio/output artifacts
    while keeping the operation idempotent and leaving shared SFX ('sfx_*') and '$ROSTER' untouched.
    """
    if not filename or not mascot_slug or filename == "$ROSTER":
        return filename
    base_name = os.path.basename(filename)
    if base_name.lower().startswith("sfx_"):
        return filename
    slug_clean = get_mascot_slug(mascot_slug)
    if not slug_clean:
        return filename
    root, ext = os.path.splitext(filename)
    if not ext:
        ext = ".wav"
    if root.lower().endswith(f"_{slug_clean}"):
        return filename
    return f"{root}_{slug_clean}{ext}"


def build_speech_part(text: str, voice_name: str = "Puck", style: str = ""):
    """
    Constructs a google.genai types.Part configured for Gemini 3.8 Flash TTS
    with types.SpeechMetadata(speaker=voice_name, style=style).
    Preserves valid angle-bracket point-in-time tags (<short pause>, etc.).
    """
    from google.genai import types
    clean_text = clean_spoken_text(text, allow_vocal_tags=True)
    part = types.Part.from_text(text=clean_text)
    if hasattr(types, "SpeechMetadata"):
        clean_style = clean_style_directive(style)
        part.speech_metadata = types.SpeechMetadata(
            speaker=voice_name or "Puck",
            style=clean_style or None
        )
    return part


def check_model_status(model_name: str, category: str = "general", json_path: str = "config/cost_rates.json") -> dict:
    """
    Checks the lifecycle status of a model in config/cost_rates.json.
    Returns a dict with:
      - is_active: bool (True only if status == 'active')
      - status: str ('active', 'preview', 'legacy', 'unknown')
      - recommendation: Optional[str]
      - warning_message: Optional[str]
    """
    if not model_name:
        return {"is_active": True, "status": "active", "recommendation": None, "warning_message": None}

    tracked = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                tracked = data.get("tracked_models", {})
        except Exception:
            pass

    meta = tracked.get(model_name, {})
    status = meta.get("status", "unknown").lower()
    recommended_model = meta.get("recommended_replacement")

    # If no explicit recommendation, find the active model for this category
    if not recommended_model:
        if "tts" in model_name or category in ["tts", "tts_voice", "voice"]:
            recommended_model = DEFAULT_TTS_MODEL
        elif "lyria" in model_name or category in ["music", "music_generator"]:
            recommended_model = DEFAULT_MUSIC_MODEL
        else:
            recommended_model = DEFAULT_LLM_MODEL

    if status == "active":
        return {
            "is_active": True,
            "status": "active",
            "recommendation": None,
            "warning_message": None
        }

    warning_lines = []
    if status == "preview":
        warning_lines.append(f"⚠️  WARNING: Model '{model_name}' is currently in PREVIEW status.")
        warning_lines.append(f"   • Disclaimer: Preview models have experimental API surfaces and are subject to breaking changes or quota caps.")
        if recommended_model and recommended_model != model_name:
            warning_lines.append(f"   • Recommendation: Switch to active GA model '{recommended_model}' for stadium-grade stability.")
    elif status == "legacy":
        warning_lines.append(f"⚠️  WARNING: Model '{model_name}' is currently a LEGACY model.")
        warning_lines.append(f"   • Disclaimer: Legacy models may experience higher latency, older pricing rates, or future deprecation.")
        if recommended_model and recommended_model != model_name:
            warning_lines.append(f"   • Recommendation: Upgrade to active latest model '{recommended_model}'.")
    else:
        warning_lines.append(f"⚠️  NOTICE: Model '{model_name}' is not in our tracked active model catalog.")
        if recommended_model:
            warning_lines.append(f"   • Recommendation: Consider using active tracked model '{recommended_model}'.")

    return {
        "is_active": False,
        "status": status,
        "recommendation": recommended_model,
        "warning_message": "\n".join(warning_lines)
    }


def get_model_availability(model_name: str, json_path: str = "config/cost_rates.json") -> dict:
    """
    Checks platform availability for a given model from config/cost_rates.json (DRY single source of truth).
    Returns a dict with:
      - ai_studio: bool (True if available on Google AI Studio)
      - vertex_ai: bool (True if available on Google Cloud Vertex AI)
      - exclusive_to: Optional[str] ('ai_studio', 'vertex_ai', or None)
      - supported_channels: list[str]
      - vertex_model_id: Optional[str]
      - notes: Optional[str]
      - role: Optional[str]
      - display_name: str
    """
    if not model_name:
        return {
            "ai_studio": True,
            "vertex_ai": True,
            "exclusive_to": None,
            "supported_channels": ["ai_studio", "vertex_ai"],
            "vertex_model_id": None,
            "notes": None,
            "role": None,
            "display_name": model_name
        }

    tracked = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                tracked = data.get("tracked_models", {})
        except Exception:
            pass

    meta = tracked.get(model_name, {})
    avail = meta.get("availability")
    channels = meta.get("supported_channels", [])

    if isinstance(avail, dict):
        ai_studio = bool(avail.get("ai_studio", True))
        vertex_ai = bool(avail.get("vertex_ai", True))
        exclusive_to = avail.get("exclusive_to")
        vertex_model_id = avail.get("vertex_model_id")
        notes = avail.get("notes")
    else:
        # Fallback to supported_channels list if availability dict not present
        ai_studio = "ai_studio" in channels if channels else True
        vertex_ai = "vertex_ai" in channels if channels else True
        exclusive_to = "ai_studio" if (ai_studio and not vertex_ai) else ("vertex_ai" if (vertex_ai and not ai_studio) else None)
        vertex_model_id = None
        notes = None

    if not exclusive_to:
        if ai_studio and not vertex_ai:
            exclusive_to = "ai_studio"
        elif vertex_ai and not ai_studio:
            exclusive_to = "vertex_ai"

    return {
        "ai_studio": ai_studio,
        "vertex_ai": vertex_ai,
        "exclusive_to": exclusive_to,
        "supported_channels": channels or (["ai_studio"] if ai_studio else []) + (["vertex_ai"] if vertex_ai else []),
        "vertex_model_id": vertex_model_id,
        "notes": notes,
        "role": meta.get("role"),
        "display_name": meta.get("display_name", model_name)
    }


def is_model_available_on_platform(model_name: str, use_vertex: bool, json_path: str = "config/cost_rates.json") -> bool:
    """
    Returns True if the model is available on the specified backend platform
    (Google Cloud Vertex AI if use_vertex=True, else Google AI Studio).
    """
    avail = get_model_availability(model_name, json_path=json_path)
    return avail.get("vertex_ai", True) if use_vertex else avail.get("ai_studio", True)


def get_available_models_for_role(role: str, platform: str = "ai_studio", json_path: str = "config/cost_rates.json") -> list:
    """
    Returns a list of model IDs matching a given role (e.g. 'music_generator', 'announcer_script', 'tts_voice')
    that are available on the specified platform ('ai_studio' or 'vertex_ai') from config/cost_rates.json.
    """
    tracked = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                tracked = data.get("tracked_models", {})
        except Exception:
            pass

    plat_key = "vertex_ai" if (platform in ["vertex", "vertex_ai", "vertexai"]) else "ai_studio"
    models = []
    for m_id, meta in tracked.items():
        if meta.get("role") != role:
            continue
        avail = meta.get("availability", {})
        if isinstance(avail, dict):
            is_avail = avail.get(plat_key, plat_key in meta.get("supported_channels", []))
        else:
            is_avail = plat_key in meta.get("supported_channels", [])
        if is_avail:
            models.append(m_id)
    return models


def warn_if_inactive_models(models_dict: dict, json_path: str = "config/cost_rates.json", use_vertex: Optional[bool] = None) -> bool:
    """
    Checks a dictionary of {role_or_category: model_name} and prints formatted warnings
    if any selected model is not in 'active' status or is incompatible with the selected platform.
    Returns True if any non-active or incompatible model was detected.
    """
    warnings = []
    for role, model_name in models_dict.items():
        if not model_name:
            continue
        info = check_model_status(model_name, category=role, json_path=json_path)
        if not info["is_active"] and info["warning_message"]:
            warnings.append(info["warning_message"])

        # Check platform compatibility if use_vertex is specified
        if use_vertex is not None:
            avail = get_model_availability(model_name, json_path=json_path)
            model_role = avail.get("role") or role
            if use_vertex and not avail.get("vertex_ai", True):
                vtx_models = get_available_models_for_role(model_role, platform="vertex_ai", json_path=json_path)
                rec = f"Available Vertex AI models: {', '.join(vtx_models)}" if vtx_models else "Run without --vertexai to auto-route to Google AI Studio"
                warnings.append(
                    f"⚠️  PLATFORM COMPATIBILITY: Model '{model_name}' ({role}) is not supported on Google Cloud Vertex AI.\n"
                    f"   • Limitation: This model is exclusive to Google AI Studio.\n"
                    f"   • Recommendation: {rec}."
                )
            elif not use_vertex and not avail.get("ai_studio", True):
                ais_models = get_available_models_for_role(model_role, platform="ai_studio", json_path=json_path)
                rec = f"Available AI Studio models: {', '.join(ais_models)}" if ais_models else "Run with --vertexai"
                warnings.append(
                    f"⚠️  PLATFORM COMPATIBILITY: Model '{model_name}' ({role}) is not supported on Google AI Studio.\n"
                    f"   • Limitation: This model is exclusive to Google Cloud Vertex AI Model Garden.\n"
                    f"   • Recommendation: {rec}."
                )

    if warnings:
        print("\n" + "=" * 70)
        print("🚨 MODEL SELECTION & PLATFORM COMPATIBILITY DISCLAIMER")
        print("=" * 70)
        for w in warnings:
            print(w)
            print()
        print("=" * 70 + "\n")
        return True
    return False

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


def resolve_platform_backend(cli_vertexai=None, cli_aistudio=None, config=None, gcp_project=None, gcp_location=None, music_model=None):
    """
    Centrally resolves whether to target Google Cloud Vertex AI or Google AI Studio across all CLI tools.
    
    Precedence:
      1. Explicit CLI flag (Highest Precedence):
         - cli_aistudio (True) -> False (Google AI Studio, strictly overrides .env)
         - cli_vertexai (True) -> True (Google Cloud Vertex AI)
      2. Model Availability Auto-Routing:
         - Dynamically checks model availability from config/cost_rates.json (DRY source of truth).
         - If configured model is exclusive to Google AI Studio and cli_vertexai is NOT True,
           routes entire pipeline to Google AI Studio.
         - If configured model is exclusive to Vertex AI and cli_aistudio is NOT True,
           routes entire pipeline to Vertex AI.
      3. Config file settings (config):
         - config.models.platform / config.platform == 'aistudio' -> False
         - config.models.platform / config.platform in ['vertexai', 'vertex'] -> True
         - config.models.vertexai / config.models.use_vertexai / config.vertexai -> bool
      4. Environment variables:
         - GOOGLE_GENAI_PLATFORM == 'aistudio' -> False
         - GOOGLE_GENAI_PLATFORM in ['vertexai', 'vertex'] -> True
         - GOOGLE_GENAI_USE_VERTEXAI in ['true', '1', 'yes'] -> True
      5. Default: False (Google AI Studio)
      
    Returns:
      tuple: (use_vertex: bool, platform_desc: str, project: Optional[str], location: Optional[str])
    """
    load_dotenv_if_present()

    # 1. CLI flags take highest priority
    if cli_aistudio:
        use_vertex = False
    elif cli_vertexai:
        use_vertex = True
    else:
        # 2. Model Availability Auto-Routing:
        # Dynamically checks model availability from config/cost_rates.json (DRY single source of truth).
        cfg = config or {}
        models_cfg = cfg.get("models", {}) if isinstance(cfg, dict) else {}
        music_cfg = cfg.get("music", {}) if isinstance(cfg, dict) else {}
        eff_music = str(music_model or models_cfg.get("music_model") or music_cfg.get("model") or cfg.get("music_model") or DEFAULT_MUSIC_MODEL).lower().strip()

        music_avail = get_model_availability(eff_music)
        if music_avail.get("ai_studio") and not music_avail.get("vertex_ai"):
            use_vertex = False
            platform_desc = f"Google AI Studio (Auto-routed for {eff_music})"
            return use_vertex, platform_desc, None, "us-central1"
        elif music_avail.get("vertex_ai") and not music_avail.get("ai_studio") and not cli_aistudio:
            use_vertex = True
            resolved_proj = gcp_project or cfg.get("gcp_project", models_cfg.get("gcp_project")) or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
            resolved_loc = gcp_location or cfg.get("gcp_location", models_cfg.get("gcp_location")) or os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("GCP_LOCATION", "us-central1")
            proj_str = f" (Project: {resolved_proj}, Region: {resolved_loc})" if resolved_proj else f" (Region: {resolved_loc})"
            platform_desc = f"Google Cloud Vertex AI (Auto-routed for {eff_music}){proj_str}"
            return use_vertex, platform_desc, resolved_proj, resolved_loc

        # 3. Config file settings
        plat_cfg = str(cfg.get("platform") or models_cfg.get("platform") or "").lower().strip()

        if plat_cfg in ["aistudio", "ai_studio", "studio"]:
            use_vertex = False
        elif plat_cfg in ["vertex", "vertexai", "vertex_ai"]:
            use_vertex = True
        else:
            raw_cfg_vertex = cfg.get("vertexai", models_cfg.get("vertexai", models_cfg.get("use_vertexai", None)))
            if raw_cfg_vertex is not None:
                use_vertex = bool(raw_cfg_vertex)
            else:
                # 4. Environment variables
                env_plat = os.environ.get("GOOGLE_GENAI_PLATFORM", "").lower().strip()
                if env_plat in ["aistudio", "ai_studio", "studio"]:
                    use_vertex = False
                elif env_plat in ["vertex", "vertexai", "vertex_ai"]:
                    use_vertex = True
                else:
                    env_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower().strip() in ["true", "1", "yes"]
                    use_vertex = env_vertex

    # Resolve GCP project & location parameters
    cfg_obj = config or {}
    m_cfg = cfg_obj.get("models", {}) if isinstance(cfg_obj, dict) else {}
    resolved_proj = gcp_project or cfg_obj.get("gcp_project", m_cfg.get("gcp_project")) or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
    resolved_loc = gcp_location or cfg_obj.get("gcp_location", m_cfg.get("gcp_location")) or os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("GCP_LOCATION", "us-central1")

    if use_vertex:
        proj_str = f" (Project: {resolved_proj}, Region: {resolved_loc})" if resolved_proj else f" (Region: {resolved_loc})"
        platform_desc = f"Google Cloud Vertex AI{proj_str}"
    else:
        platform_desc = "Google AI Studio"

    return use_vertex, platform_desc, resolved_proj, resolved_loc


def init_gemini_client(api_key=None, use_vertex=None, project=None, location=None):
    """
    Initializes a google.genai.Client instance supporting both Google AI Studio and Vertex AI platforms.
    
    Resolution for Vertex AI mode:
      use_vertex: Explicit bool > GOOGLE_GENAI_PLATFORM > GOOGLE_GENAI_USE_VERTEXAI env var ('true'/'1') > False
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

    if use_vertex is not None:
        is_vertex = bool(use_vertex)
    else:
        env_plat = os.environ.get("GOOGLE_GENAI_PLATFORM", "").lower().strip()
        if env_plat in ["aistudio", "ai_studio", "studio"]:
            is_vertex = False
        elif env_plat in ["vertex", "vertexai", "vertex_ai"]:
            is_vertex = True
        else:
            is_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower().strip() in ["true", "1", "yes"]

    api_key_val = api_key or os.environ.get("GEMINI_API_KEY")

    if is_vertex:
        gcp_proj = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        gcp_loc = location or os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("GCP_LOCATION") or "us-central1"

        if api_key_val:
            # When API key is provided for Vertex AI, project and location must be omitted
            # as they are mutually exclusive in google-genai Client initializer.
            client_kwargs = {
                "vertexai": True,
                "api_key": api_key_val
            }
            auth_desc = "GCP API Key"
            print(f"🔑 Google Cloud Vertex AI client initializing (Auth: {auth_desc}).")
        else:
            client_kwargs = {
                "vertexai": True,
                "project": gcp_proj,
                "location": gcp_loc
            }
            auth_desc = "Application Default Credentials (ADC)"
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
        return genai.Client(vertexai=False, api_key=api_key_val)


def format_error_brief(error: Exception, max_len: int = 150) -> str:
    """
    Sanitizes API exception messages, stripping raw HTML response dumps
    and truncating verbose error bodies for clean CLI presentation.
    """
    if not error:
        return "Unknown error"
    err_str = str(error)
    if "<!DOCTYPE" in err_str or "<html" in err_str:
        if "404" in err_str or "Not Found" in err_str:
            return "404 Not Found (endpoint not available on this platform)"
        elif "403" in err_str or "Permission" in err_str:
            return "403 Forbidden / Permission Denied"
        elif "500" in err_str:
            return "500 Internal Server Error"
        return "HTTP error response from server"

    cleaned = " ".join(err_str.split())
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "..."
    return cleaned


def resolve_api_engine(cli_legacy_api: bool = False, cli_api_engine: str = None, config: dict = None, use_vertex: bool = False) -> tuple:
    """
    Resolves the model interaction API engine with strict platform-aware precedence:
      1. Explicit CLI flag --legacy-api / --use-generate-content forces 'generate_content'
      2. Explicit CLI flag --api-engine ('interactions' or 'generate_content')
      3. If use_vertex is True: Vertex AI natively standardizes on 'generate_content'
         (Interactions API is an AI Studio endpoint at generativelanguage.googleapis.com)
      4. Team config: models.api_engine ('interactions' or 'generate_content')
      5. Environment variable: GEMINI_API_ENGINE ('interactions' or 'generate_content')
      6. Default: 'interactions' on Google AI Studio per June 2026 standard

    Returns:
      tuple: (api_engine: str, engine_desc: str)
        e.g. ("interactions", "Interactions API (Preferred)") or ("generate_content", "generateContent API (Vertex AI Standard)")
    """
    load_dotenv_if_present()

    if cli_legacy_api:
        return API_ENGINE_LEGACY, "Legacy generateContent API"

    if cli_api_engine:
        val = str(cli_api_engine).lower().strip()
        if val in ["interactions", "interaction", "new"]:
            if use_vertex:
                return API_ENGINE_INTERACTIONS, "Interactions API (Warning: not natively hosted on Vertex AI)"
            return API_ENGINE_INTERACTIONS, "Interactions API (Preferred)"
        elif val in ["generate_content", "generatecontent", "legacy", "models"]:
            if use_vertex:
                return API_ENGINE_LEGACY, "generateContent API (Vertex AI Standard)"
            return API_ENGINE_LEGACY, "Legacy generateContent API"

    # Platform default: Vertex AI natively uses generate_content, while AI Studio uses interactions
    if use_vertex:
        return API_ENGINE_LEGACY, "generateContent API (Vertex AI Standard)"

    cfg = config or {}
    m_cfg = cfg.get("models", {}) if isinstance(cfg, dict) else {}
    cfg_val = str(
        cfg.get("api_engine")
        or cfg.get("api_mode")
        or m_cfg.get("api_engine")
        or m_cfg.get("api_mode")
        or ""
    ).lower().strip()
    if cfg_val in ["interactions", "interaction", "new"]:
        return API_ENGINE_INTERACTIONS, "Interactions API (Preferred)"
    elif cfg_val in ["generate_content", "generatecontent", "legacy", "models"]:
        return API_ENGINE_LEGACY, "Legacy generateContent API (from config)"

    env_val = os.environ.get("GEMINI_API_ENGINE", "").lower().strip()
    if env_val in ["interactions", "interaction", "new"]:
        return API_ENGINE_INTERACTIONS, "Interactions API (Preferred)"
    elif env_val in ["generate_content", "generatecontent", "legacy", "models"]:
        return API_ENGINE_LEGACY, "Legacy generateContent API (from env)"

    return API_ENGINE_INTERACTIONS, "Interactions API (Preferred)"


def extract_audio_bytes_from_interaction(interaction) -> tuple:
    """
    Extracts raw audio bytes and MIME type from an Interaction object returned by client.interactions.create().
    Supports both direct output_audio attribute (AudioContent.data base64 string or bytes)
    and timeline model_output steps content blocks.
    
    Returns:
      tuple: (audio_bytes: Optional[bytes], mime_type: str)
    """
    import base64

    if not interaction:
        return None, "audio/mp3"

    audio_bytes = None
    mime_type = "audio/mp3"

    # 1. Check direct output_audio helper attribute
    out_audio = getattr(interaction, "output_audio", None)
    if out_audio:
        mime_type = getattr(out_audio, "mime_type", "audio/mp3") or "audio/mp3"
        if isinstance(out_audio, (bytes, bytearray)):
            return bytes(out_audio), mime_type
        if hasattr(out_audio, "data") and out_audio.data:
            data_val = out_audio.data
            if isinstance(data_val, str):
                try:
                    audio_bytes = base64.b64decode(data_val)
                except Exception:
                    audio_bytes = data_val.encode("utf-8")
            elif isinstance(data_val, (bytes, bytearray)):
                audio_bytes = bytes(data_val)
        if audio_bytes:
            return audio_bytes, mime_type

    # 2. Check steps timeline
    steps = getattr(interaction, "steps", None)
    if steps and isinstance(steps, list):
        for step in reversed(steps):
            if getattr(step, "type", None) == "model_output":
                content = getattr(step, "content", None)
                if isinstance(content, list):
                    for item in content:
                        item_type = getattr(item, "type", None)
                        if item_type == "audio":
                            mime_type = getattr(item, "mime_type", mime_type) or mime_type
                            if hasattr(item, "data") and item.data:
                                data_val = item.data
                                if isinstance(data_val, str):
                                    try:
                                        audio_bytes = base64.b64decode(data_val)
                                    except Exception:
                                        audio_bytes = data_val.encode("utf-8")
                                elif isinstance(data_val, (bytes, bytearray)):
                                    audio_bytes = bytes(data_val)
                            if audio_bytes:
                                return audio_bytes, mime_type

    return audio_bytes, mime_type




