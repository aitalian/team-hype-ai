#!/usr/bin/env python3
"""
TeamHypeAI - Stadium Sound Effects Generator

Generates original stadium sound effects (goal horns, crowd cheers, organ stings, etc.)
with Google Lyria AI from text prompts defined in `sfx_templates.json`, then trims and
fades each clip with Pydub and saves it into `input/` as a drop-in `sfx_*` asset for
`assemble_show.py`. Generating your own SFX avoids redistributing third-party recordings.

Usage:
    python3 generate_sfx.py --dry-run
    python3 generate_sfx.py
    python3 generate_sfx.py --only sfx_goal-horn.mp3 --force
"""

import os
import sys
import argparse

from common import (
    load_dotenv_if_present,
    load_json_file,
    get_model_cost_rates,
    print_pricing_disclaimer,
    init_gemini_client,
    warn_if_inactive_models,
    print_cli_banner,
    resolve_platform_backend,
    resolve_api_engine,
    DEFAULT_MUSIC_MODEL,
)
from generate_gemini_audio import generate_music_clip_lyria

DEFAULT_SFX_CONFIG = "sfx_templates.json"
DEFAULT_SFX_DURATION_SEC = 10


def build_sfx_input_text(prompt, duration_sec):
    """Wraps a user SFX prompt so Lyria returns a short sound effect rather than a song."""
    return (
        f"Short stadium sound effect, not a song ({duration_sec} seconds, no melody development, "
        f"strictly NO singing, NO intelligible speech, NO lyrics): {prompt}"
    )


def finalize_sfx_clip(raw_path, out_path, max_duration_ms=0, fade_in_ms=0, fade_out_ms=0):
    """Trims and fades the raw Lyria output with Pydub and exports it in the format implied by out_path."""
    from pydub import AudioSegment

    clip = AudioSegment.from_file(raw_path)
    if max_duration_ms and max_duration_ms > 0:
        clip = clip[:max_duration_ms]
    if fade_in_ms and fade_in_ms > 0:
        clip = clip.fade_in(min(fade_in_ms, len(clip)))
    if fade_out_ms and fade_out_ms > 0:
        clip = clip.fade_out(min(fade_out_ms, len(clip)))

    out_format = os.path.splitext(out_path)[1].lstrip(".").lower() or "wav"
    clip.export(out_path, format=out_format)
    return len(clip)


def print_sfx_cost_report(num_clips, music_model, platform_desc="Google AI Studio", use_vertex=False):
    print("\n" + "=" * 60)
    print("📊 SOUND EFFECTS GENERATION COST ESTIMATE")
    print("=" * 60)
    print(f"🌐 Platform Backend:   {platform_desc}")

    music_rate = get_model_cost_rates(music_model, category="music", use_vertex=use_vertex, is_batch=False)
    total_cost = num_clips * music_rate["song_request"]

    print(f"🔊 Sound Effects ({num_clips} clips using {music_model} @ ${music_rate['song_request']:.2f}/request): ~${total_cost:.2f} USD")
    print("------------------------------------------------------------")
    print(f"💵 ESTIMATED TOTAL COST: ~${total_cost:.2f} USD")
    print("------------------------------------------------------------")
    print_pricing_disclaimer(use_vertex=use_vertex, has_tts=False, has_llm=False, has_music=True)
    print("=" * 60 + "\n")


def main():
    load_dotenv_if_present()
    parser = argparse.ArgumentParser(
        description="Generate original stadium sound effects (goal horns, crowd cheers) with Google Lyria AI."
    )
    parser.add_argument("-c", "--config", default=DEFAULT_SFX_CONFIG, help=f"Path to SFX template JSON (default: {DEFAULT_SFX_CONFIG})")
    parser.add_argument("-o", "--output-dir", default=None, help="Directory for generated SFX (default: config 'sfx_folder' or input)")
    parser.add_argument("--music-model", default=None, help=f"Lyria model used for SFX (default: config 'music_model' or {DEFAULT_MUSIC_MODEL})")
    parser.add_argument("--only", default=None, help="Comma-separated list of SFX filenames to generate (default: all clips in config)")
    parser.add_argument("--legacy-api", "--use-generate-content", action="store_true", default=False, help="Use legacy generateContent API instead of the preferred Interactions API (June 2026 standard)")
    parser.add_argument("--api-engine", choices=["interactions", "generate_content", "auto"], default=None, help="Explicitly choose model API engine: 'interactions' (default) or 'generate_content'")
    platform_group = parser.add_mutually_exclusive_group()
    platform_group.add_argument("--vertexai", action="store_true", default=None, help="Use Google Cloud Vertex AI backend platform instead of Google AI Studio")
    platform_group.add_argument("--aistudio", "--ai-studio", "--no-vertexai", action="store_true", default=None, help="Force Google AI Studio backend platform (overrides GOOGLE_GENAI_USE_VERTEXAI in .env)")
    parser.add_argument("--gcp-project", "--project", default=None, help="Google Cloud Project ID for Vertex AI (default: GOOGLE_CLOUD_PROJECT or GCP_PROJECT env var)")
    parser.add_argument("--gcp-location", "--location", default=None, help="Google Cloud Region for Vertex AI (default: GOOGLE_CLOUD_LOCATION, GCP_LOCATION, or us-central1)")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically accept cost estimate and bypass confirmation prompt")
    parser.add_argument("-f", "--force", action="store_true", help="Force regeneration of existing SFX files")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts and cost estimate without calling API")

    args = parser.parse_args()

    config = load_json_file(args.config, description="SFX template")
    output_dir = args.output_dir or config.get("sfx_folder", "input")
    music_model = args.music_model or config.get("music_model", DEFAULT_MUSIC_MODEL)
    clips = config.get("clips", [])
    if args.only:
        wanted = {name.strip() for name in args.only.split(",") if name.strip()}
        clips = [c for c in clips if c.get("filename") in wanted]
    os.makedirs(output_dir, exist_ok=True)

    use_vertex, platform_desc, gcp_project, gcp_location = resolve_platform_backend(
        cli_vertexai=args.vertexai,
        cli_aistudio=args.aistudio,
        config=config,
        gcp_project=args.gcp_project,
        gcp_location=args.gcp_location,
        music_model=music_model
    )

    api_engine, api_engine_desc = resolve_api_engine(
        cli_legacy_api=args.legacy_api,
        cli_api_engine=args.api_engine,
        config=config,
        use_vertex=use_vertex
    )

    print_cli_banner(
        utility_title="STADIUM SOUND EFFECTS GENERATOR (generate_sfx.py)",
        what_it_is="Generates original goal horns, crowd cheers and other stadium SFX so shows never depend on third-party recordings.",
        how_it_works="Sends each sfx_templates.json prompt to Google Lyria, then trims and fades the clip with Pydub into input/sfx_*."
    )
    print(f"   Platform Backend: {platform_desc}")
    print(f"   API Engine:       {api_engine_desc}")
    print(f"   Output Directory: {output_dir}")
    print(f"   SFX Model:        {music_model}")

    warn_if_inactive_models({"music_generator": music_model}, use_vertex=use_vertex)

    to_generate = []
    for clip in clips:
        out_path = os.path.join(output_dir, clip["filename"])
        if args.force or not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
            to_generate.append(clip)

    if not to_generate and not args.dry_run:
        print("\n" + "=" * 60)
        print(f"✨ All requested sound effects are present in '{output_dir}/'.")
        print("   Nothing to generate! (Pass --force to regenerate existing SFX)")
        print("=" * 60 + "\n")
        return

    print_sfx_cost_report(len(to_generate), music_model, platform_desc=platform_desc, use_vertex=use_vertex)

    if args.dry_run:
        print("🔍 DRY RUN MODE -- Sound Effect Prompts Preview:")
        for clip in clips:
            out_path = os.path.join(output_dir, clip["filename"])
            status = " [Will Generate]" if clip in to_generate else " [Existing File Cached]"
            duration_sec = clip.get("duration_seconds", DEFAULT_SFX_DURATION_SEC)
            print(f"📁 {out_path}{status}")
            print(f"   Prompt: \"{build_sfx_input_text(clip['prompt'], duration_sec)}\"")
            print(f"   Post-processing: trim to {clip.get('max_duration_ms', 0) or 'full length'} ms, "
                  f"fade in {clip.get('fade_in_ms', 0)} ms, fade out {clip.get('fade_out_ms', 0)} ms\n")
        return

    if not args.yes and sys.stdin.isatty():
        try:
            confirm = input("⚠️  Do you accept the estimated API charges and wish to proceed with generating sound effects? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("🛑 Sound effects generation cancelled by user.")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\n🛑 Sound effects generation cancelled by user.")
            sys.exit(0)

    client = init_gemini_client(
        api_key=os.environ.get("GEMINI_API_KEY"),
        use_vertex=use_vertex,
        project=gcp_project,
        location=gcp_location
    )

    print("\n🔊 Generating Stadium Sound Effects via Google Lyria AI...")
    failures = 0
    for clip in to_generate:
        out_path = os.path.join(output_dir, clip["filename"])
        raw_filename = f".raw_{os.path.splitext(clip['filename'])[0]}"
        raw_path = os.path.join(output_dir, raw_filename)
        duration_sec = clip.get("duration_seconds", DEFAULT_SFX_DURATION_SEC)

        ok = generate_music_clip_lyria(
            client,
            clip["prompt"],
            raw_filename,
            output_dir,
            music_model,
            duration_sec=duration_sec,
            force=True,
            api_engine=api_engine,
            use_vertex=use_vertex,
            input_text=build_sfx_input_text(clip["prompt"], duration_sec)
        )
        try:
            if ok and os.path.exists(raw_path):
                length_ms = finalize_sfx_clip(
                    raw_path,
                    out_path,
                    max_duration_ms=clip.get("max_duration_ms", 0),
                    fade_in_ms=clip.get("fade_in_ms", 0),
                    fade_out_ms=clip.get("fade_out_ms", 0)
                )
                print(f"   ✅ Sound effect ready ({length_ms / 1000:.1f}s): {out_path}")
            else:
                failures += 1
                print(f"   ❌ Could not generate '{clip['filename']}'.")
        finally:
            if os.path.exists(raw_path):
                os.remove(raw_path)

    if failures:
        print(f"\n⚠️  {failures} sound effect(s) failed. Re-run to retry, or drop your own licensed audio into '{output_dir}/'.")
        sys.exit(1)
    print(f"\n✅ All sound effects generated in '{output_dir}/'! Reference them by filename in your run_of_show.json.")


if __name__ == "__main__":
    main()
