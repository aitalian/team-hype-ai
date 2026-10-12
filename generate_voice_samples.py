#!/usr/bin/env python3
"""
TeamHypeAI - Announcer Voice Samples Generator

Generates short sample audio clips for prebuilt Google Gemini voice personas
(Puck, Charon, Kore, Fenrir, Aoede) and saves them in the `samples/` directory.
Allows users to easily audition each announcer voice persona before building their team intros.

Usage:
    python3 generate_voice_samples.py --dry-run
    python3 generate_voice_samples.py
"""

import os
import sys
import argparse

from common import (
    load_dotenv_if_present,
    load_gemini_voices,
    get_model_cost_rates,
    log_api_event,
    print_pricing_disclaimer,
    init_gemini_client,
    check_model_status,
    warn_if_inactive_models,
    DEFAULT_TTS_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_ENHANCE_MODE,
    DEFAULT_AUDIO_TAGS,
    clean_spoken_text,
    format_speech_style,
)
from generate_gemini_audio import (
    generate_audio_clip_gemini,
    enhance_announcer_script,
    format_audio_tag,
)

VOICE_DEFS = load_gemini_voices()
PREBUILT_VOICES = [v["name"] for v in VOICE_DEFS]
DEFAULT_SAMPLE_TEXT = "Welcome to DevFest Montreal! Get ready to vibe code!"
DEFAULT_PREFIX = "Say rapidly with intense, fast-paced stadium PA announcer energy, quick delivery, and high enthusiasm: "


def print_sample_cost_report(num_samples, tts_model, llm_model, num_enhanced=0, platform_desc="Google AI Studio", use_vertex=False):
    print("\n" + "=" * 60)
    print("📊 VOICE SAMPLES GENERATION COST ESTIMATE")
    print("=" * 60)
    print(f"🌐 Platform Backend:   {platform_desc}")

    # 1 sample is ~4 sec audio (~100 tokens), input ~35 tokens
    voice_input_tokens = num_samples * 35
    voice_output_tokens = num_samples * 100

    tts_rate = get_model_cost_rates(tts_model, category="voice", use_vertex=use_vertex, is_batch=False)
    tts_cost = ((voice_input_tokens / 1_000_000) * tts_rate["input_1m"]) + ((voice_output_tokens / 1_000_000) * tts_rate["output_1m"])

    if num_enhanced > 0:
        llm_input_tokens = num_enhanced * 120
        llm_output_tokens = num_enhanced * 30
        llm_rate = get_model_cost_rates(llm_model, category="voice", use_vertex=use_vertex, is_batch=False)
        llm_cost = ((llm_input_tokens / 1_000_000) * llm_rate["input_1m"]) + ((llm_output_tokens / 1_000_000) * llm_rate["output_1m"])
    else:
        llm_cost = 0.0

    total_cost = tts_cost + llm_cost

    print("🔤 Estimated Input Tokens:")
    print(f"   • Voice Prompts:      ~{voice_input_tokens:,} input tokens ({num_samples} sample clips)")
    if num_enhanced > 0:
        print(f"   • Script Synthesizer: ~{llm_input_tokens:,} input tokens ({num_enhanced} scripts enhanced via {llm_model})")
    print(f"   • Total Input:         ~{(voice_input_tokens + (num_enhanced * 120)):,} input tokens\n")

    print("🔊 Projected Output Tokens / Audio Output:")
    print(f"   • Voice Audio Output:  ~{voice_output_tokens:,} output tokens ({num_samples} clips @ ~4s/clip)")
    print(f"   • Total Output:        ~{voice_output_tokens:,} output tokens\n")

    if num_enhanced > 0:
        print(f"🧠 Script Synthesizer ({num_enhanced} scripts using {llm_model}): ~${llm_cost:.6f} USD")
    print(f"🎙️  Voice Samples ({num_samples} clips using {tts_model}): ~${tts_cost:.6f} USD")
    print("------------------------------------------------------------")
    print(f"💵 ESTIMATED TOTAL COST: ~${total_cost:.5f} USD")
    print("------------------------------------------------------------")
    print_pricing_disclaimer(
        use_vertex=use_vertex,
        has_tts=(num_samples > 0),
        has_llm=(num_enhanced > 0),
        has_music=False
    )
    print("=" * 60 + "\n")


def main():
    load_dotenv_if_present()
    parser = argparse.ArgumentParser(
        description="Generate sample audio clips for prebuilt Google Gemini voice personas."
    )
    parser.add_argument("-o", "--output-dir", default="samples", help="Directory for voice samples (default: samples)")
    parser.add_argument("--sample-text", default=DEFAULT_SAMPLE_TEXT, help=f"Sample announcement text (default: '{DEFAULT_SAMPLE_TEXT}')")
    parser.add_argument("--tts-model", default=DEFAULT_TTS_MODEL, help=f"Gemini TTS model (default: {DEFAULT_TTS_MODEL})")
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL, help=f"Gemini LLM model (default: {DEFAULT_LLM_MODEL})")
    parser.add_argument("--voices", default=",".join(PREBUILT_VOICES), help=f"Comma-separated list of voices (default: {','.join(PREBUILT_VOICES)})")
    parser.add_argument("--featured-only", action="store_true", default=False, help="Only generate samples for core featured stadium voice personas (Puck, Charon, Kore, Fenrir, Aoede)")
    parser.add_argument("--audio-tags", default=DEFAULT_AUDIO_TAGS, help=f"Gemini TTS Audio Tags (default: {DEFAULT_AUDIO_TAGS})")
    parser.add_argument("--theme-context", "--announcer-theme", default=None, help="Optional theme/personality context for script synthesis (e.g. pirate, space commander)")
    parser.add_argument("--regional-accent", "--accent", default=None, help="Optional regional accent guidance (e.g. 'French Canadian')")
    parser.add_argument("--enhance-scripts", choices=["auto", "always", "never"], default=DEFAULT_ENHANCE_MODE, help="LLM script enhancement mode (default: auto)")
    parser.add_argument("--vertexai", action="store_true", default=False, help="Use Google Cloud Vertex AI backend platform instead of Google AI Studio")
    parser.add_argument("--gcp-project", "--project", default=None, help="Google Cloud Project ID for Vertex AI (default: GOOGLE_CLOUD_PROJECT or GCP_PROJECT env var)")
    parser.add_argument("--gcp-location", "--location", default=None, help="Google Cloud Region for Vertex AI (default: GOOGLE_CLOUD_LOCATION, GCP_LOCATION, or us-central1)")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically accept cost estimate and bypass confirmation prompt")
    parser.add_argument("--force", action="store_true", help="Force regeneration of existing sample files")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts and cost estimate without calling API")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    voice_list = [v.strip() for v in args.voices.split(",") if v.strip()]
    if args.featured_only:
        featured_names = [v["name"] for v in VOICE_DEFS if v.get("is_featured", False)]
        if not featured_names:
            featured_names = ["Puck", "Charon", "Kore", "Fenrir", "Aoede"]
        voice_list = [v for v in voice_list if v in featured_names]
    regional_accent = args.regional_accent or ""
    raw_audio_tag = format_audio_tag(args.audio_tags)
    audio_tag = format_speech_style(raw_audio_tag, regional_accent=regional_accent)

    is_vertex = args.vertexai or os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower().strip() in ["true", "1", "yes"]
    if is_vertex:
        gcp_proj = args.gcp_project or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        gcp_loc = args.gcp_location or os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("GCP_LOCATION") or "us-central1"
        proj_str = f" (Project: {gcp_proj}, Region: {gcp_loc})" if gcp_proj else f" (Region: {gcp_loc})"
        platform_desc = f"Google Cloud Vertex AI{proj_str}"
    else:
        platform_desc = "Google AI Studio"

    # Filter voices that need generation
    to_generate = []
    for voice in voice_list:
        out_file = os.path.join(args.output_dir, f"{voice}.wav")
        if args.force or not (os.path.exists(out_file) and os.path.getsize(out_file) > 0):
            to_generate.append(voice)

    print("🚀 TeamHypeAI - Announcer Voice Preview Generator")
    print(f"   Platform Backend: {platform_desc}")
    print(f"   Output Directory: {args.output_dir}")
    print(f"   TTS Model:        {args.tts_model}")
    print(f"   LLM Model:        {args.llm_model}")
    print(f"   Audio Tags:       {audio_tag}")
    if regional_accent:
        print(f"   Regional Accent:  {regional_accent}")
    print(f"   Sample Script:    \"{args.sample_text}\"")

    warn_if_inactive_models({
        "tts_voice": args.tts_model,
        "announcer_script": args.llm_model
    })

    if not to_generate and not args.dry_run:
        print("\n" + "=" * 60)
        print(f"✨ All requested voice samples are present in '{args.output_dir}/'.")
        print("   Nothing to generate! (Pass --force to regenerate existing samples)")
        print("=" * 60 + "\n")
        return

    num_samples = len(to_generate)
    should_enhance = args.enhance_scripts in ["auto", "always"]
    num_enhanced = num_samples if should_enhance else 0

    print_sample_cost_report(
        num_samples=num_samples,
        tts_model=args.tts_model,
        llm_model=args.llm_model,
        num_enhanced=num_enhanced,
        platform_desc=platform_desc,
        use_vertex=is_vertex
    )

    clean_sample_text = clean_spoken_text(args.sample_text)

    if args.dry_run:
        print("🔍 DRY RUN MODE -- Voice Sample Prompts Preview:")
        for voice in voice_list:
            fname = f"{voice}.wav"
            status = " [Will Generate]" if voice in to_generate else " [Existing File Cached]"
            enhance_tag = f" 🧠 [LLM Enhanced via {args.llm_model}]" if should_enhance else ""
            tag_info = f" [Tone: {audio_tag}]" if audio_tag else ""
            print(f"📁 {os.path.join(args.output_dir, fname)} ({voice}){status}")
            print(f"   Dialogue: \"{clean_sample_text}\"{tag_info}{enhance_tag}\n")
        return

    if not args.yes and sys.stdin.isatty():
        try:
            confirm = input("⚠️  Do you accept the estimated API charges and wish to proceed with generating voice samples? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("🛑 Voice sample generation cancelled by user.")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\n🛑 Voice sample generation cancelled by user.")
            sys.exit(0)

    client = init_gemini_client(
        api_key=os.environ.get("GEMINI_API_KEY"),
        use_vertex=args.vertexai,
        project=args.gcp_project,
        location=args.gcp_location
    )

    print("\n🎙️ Generating Announcer Voice Samples...")
    for voice in to_generate:
        fname = f"{voice}.wav"
        out_path = os.path.join(args.output_dir, fname)
        if not args.force and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f"   ⏩ Skipping existing voice sample: {out_path}")
            continue

        if should_enhance:
            print(f"🧠 Enhancing script for '{voice}' via {args.llm_model}...")
            voice_def = next((v for v in VOICE_DEFS if v["name"] == voice), {})
            persona_style = voice_def.get("style", "High-energy stadium PA announcer")
            prompt_text = enhance_announcer_script(
                client,
                clean_sample_text,
                args.llm_model,
                persona_style=persona_style,
                theme_context=args.theme_context or "",
                delivery_instructions=DEFAULT_PREFIX,
                audio_tag=audio_tag,
                regional_accent=regional_accent
            )
        else:
            prompt_text = clean_sample_text

        print(f"🎙️ Synthesizing voice sample for '{voice}'...")
        generate_audio_clip_gemini(
            client,
            text=clean_spoken_text(prompt_text, allow_vocal_tags=True),
            filename=fname,
            output_dir=args.output_dir,
            model_name=args.tts_model,
            voice_name=voice,
            style=audio_tag or DEFAULT_AUDIO_TAGS,
            force=args.force
        )

    print(f"\n✅ All announcer voice samples generated in '{args.output_dir}/'!")


if __name__ == "__main__":
    main()
