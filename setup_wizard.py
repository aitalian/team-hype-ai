#!/usr/bin/env python3
"""
TeamHypeAI - Interactive First-Time Setup Wizard

A batteries-included, interactive terminal wizard that guides users step-by-step
through configuring their team name, mascot, announcer voice persona, models, intro clips, and roster.
Reads implied defaults from existing `roster_templates.json` and `run_of_show.json` files if present,
falling back to hardcoded defaults only if no such files exist.
Outputs ready-to-use configuration files.

Usage:
    python3 setup_wizard.py
"""

import os
import sys
import json
import subprocess

from common import (
    load_dotenv_if_present,
    load_gemini_voices,
    warn_if_inactive_models,
    print_cli_banner,
    DEFAULT_TTS_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_MUSIC_MODEL,
    DEFAULT_SPEECH_STYLE,
    DEFAULT_AUDIO_TAGS,
)


def prompt_string(prompt_text, default_val=""):
    suffix = f" [{default_val}]" if default_val else ""
    try:
        val = input(f"{prompt_text}{suffix}: ").strip()
        return val if val else default_val
    except (KeyboardInterrupt, EOFError):
        print("\n🛑 Setup cancelled.")
        sys.exit(0)


def prompt_choice(prompt_text, options, default_idx=0):
    print(f"\n{prompt_text}")
    for idx, opt in enumerate(options, 1):
        is_def = " (Default)" if (idx - 1) == default_idx else ""
        print(f"  {idx}. {opt}{is_def}")
    while True:
        try:
            choice = input(f"Select an option (1-{len(options)}) [{default_idx + 1}]: ").strip()
            if not choice:
                return options[default_idx]
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(options):
                    return options[num - 1]
            print("❌ Invalid selection. Please enter a valid option number.")
        except (KeyboardInterrupt, EOFError):
            print("\n🛑 Setup cancelled.")
            sys.exit(0)


def load_existing_configs():
    """
    Reads existing `roster_templates.json` and `run_of_show.json` files if present.
    Returns (existing_roster, existing_show, roster_path, show_path).
    """
    existing_roster = {}
    existing_show = {}
    roster_path = "roster_templates.json"
    show_path = "run_of_show.json"

    if os.path.exists(roster_path):
        try:
            with open(roster_path, "r", encoding="utf-8") as f:
                existing_roster = json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not read {roster_path}: {e}")

    if os.path.exists(show_path):
        try:
            with open(show_path, "r", encoding="utf-8") as f:
                existing_show = json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not read {show_path}: {e}")

    return existing_roster, existing_show, roster_path, show_path


def main():
    print_cli_banner(
        utility_title="INTERACTIVE SETUP WIZARD (setup_wizard.py)",
        what_it_is="Guided interactive onboarding for configuring team rosters, announcer personas & audio parameters.",
        how_it_works="Inspects existing configs for implied defaults, prompts for missing values, and writes ready-to-use JSON files."
    )

    # Inspect existing configurations for implied defaults
    existing_roster, existing_show, roster_path, show_path = load_existing_configs()
    has_existing = bool(existing_roster or existing_show)

    if has_existing:
        print("📄 Existing configuration detected:")
        if existing_roster:
            print(f"   • Roster template:   {roster_path} (loaded as implied defaults)")
        if existing_show:
            print(f"   • Run of Show config: {show_path} (loaded as implied defaults)")
        print("   ℹ️  Press Enter on any prompt to keep the implied default value.\n")

    # Step 1: Environment & API Key
    print("--- STEP 1: Google Gemini API Key ---")
    load_dotenv_if_present()
    current_key = os.environ.get("GEMINI_API_KEY", "")

    if current_key:
        masked = current_key[:6] + "..." + current_key[-4:] if len(current_key) > 10 else "***"
        print(f"✅ GEMINI_API_KEY detected ({masked})")
    else:
        api_key = prompt_string("🔑 Enter your Google Gemini API Key (press Enter to skip for now)")
        if api_key:
            save_env = prompt_string("Save key to local '.env' file? (Y/n)", "Y").lower()
            if save_env in ["y", "yes"]:
                with open(".env", "a", encoding="utf-8") as f:
                    f.write(f'\nGEMINI_API_KEY="{api_key}"\n')
                print("✅ API key saved to .env")
            os.environ["GEMINI_API_KEY"] = api_key

    # Step 2: Team Identity (Implied Defaults from roster_templates.json)
    print("\n--- STEP 2: Team Identity ---")
    persona_cfg = existing_roster.get("announcer_persona", {})

    # Derive team name
    def_team_name = (
        existing_roster.get("team_name")
        or ("Montreal Canadiens" if "Canadiens" in persona_cfg.get("theme_context", "") else "Eagles")
    )
    team_name = prompt_string("🏆 Enter Team Name", def_team_name)

    # Derive team mascot / slogan
    def_team_mascot = (
        existing_roster.get("team_mascot")
        or existing_roster.get("mascot")
        or ("Canadiens" if "Canadiens" in persona_cfg.get("theme_context", "") else team_name.upper())
    )
    team_mascot = prompt_string("📣 Enter Mascot / Slogan", def_team_mascot)

    def_announcer_style = persona_cfg.get("style", "High-energy championship arena PA announcer")
    announcer_style = prompt_string("🎙️ Enter PA Announcer Style Persona", def_announcer_style)

    def_announcer_theme = persona_cfg.get("theme_context", "")
    announcer_theme = prompt_string("⚓ Optional Announcer Theme / Context (e.g. pirate, space commander, retro rockstar)", def_announcer_theme)

    def_regional_accent = persona_cfg.get("regional_accent", "")
    regional_accent = prompt_string("🌍 Optional Regional Accent (e.g. French Canadian, British, Australian)", def_regional_accent)

    def_accent_guidance = persona_cfg.get("accent_guidance", "")
    accent_guidance = prompt_string("🗣️ Optional Accent Guidance / Pronunciation notes", def_accent_guidance) if regional_accent else ""

    # Step 3: Voice Selection
    print("\n--- STEP 3: Announcer Voice Selection ---")
    def_voice_name = persona_cfg.get("voice_name", "Puck")

    sample_opt = prompt_string("Generate voice audition clips now in samples/? (y/N)", "N").lower()
    if sample_opt in ["y", "yes"]:
        print("🎙️ Launching generate_voice_samples.py --dry-run...")
        subprocess.run([sys.executable, "generate_voice_samples.py", "--dry-run"])

    voice_defs = load_gemini_voices()
    voice_options = [
        f"{'★ ' if v.get('is_featured') else '  '}{v['name']} ({v.get('gender', '')} | {v.get('announcer_style') or v.get('description', '')})"
        for v in voice_defs
    ]

    # Resolve default choice index to match existing voice
    default_voice_idx = 0
    for idx, v in enumerate(voice_defs):
        if v.get("name", "").lower() == def_voice_name.lower():
            default_voice_idx = idx
            break

    selected_voice_opt = prompt_choice("Select Announcer Voice Persona:", voice_options, default_idx=default_voice_idx)
    voice_name = selected_voice_opt.replace("★", "").strip().split(" ")[0]

    # Step 4: AI Models, Speech Style & Script Enhancement
    print("\n--- STEP 4: AI Models & Speech Style ---")
    models_cfg = existing_roster.get("models", {})

    def_tts_model = models_cfg.get("tts_model", DEFAULT_TTS_MODEL)
    def_llm_model = models_cfg.get("llm_model", DEFAULT_LLM_MODEL)
    def_music_model = models_cfg.get("music_model", DEFAULT_MUSIC_MODEL)

    tts_model = prompt_string("TTS Voice Model", def_tts_model)
    llm_model = prompt_string("Script Synthesizer Model", def_llm_model)
    music_model = prompt_string("Background Music AI Model", def_music_model)
    warn_if_inactive_models({
        "tts_voice": tts_model,
        "announcer_script": llm_model,
        "music_generator": music_model
    })

    def_speech_style = persona_cfg.get("speech_style") or persona_cfg.get("audio_tags", DEFAULT_SPEECH_STYLE)
    speech_style = prompt_string("🎙️ Gemini TTS Speech Style & Nuance (e.g. excitedly, fast-paced / shouting, hype)", def_speech_style)

    def_enhance_mode = models_cfg.get("enhance_scripts", "auto")
    enhance_options = [
        "auto (Auto-enhance items without manual phonetic overrides)",
        "always (Force LLM enhancement for all items)",
        "never (Disable LLM script enhancement)"
    ]
    enhance_idx = 0
    if def_enhance_mode == "always":
        enhance_idx = 1
    elif def_enhance_mode == "never":
        enhance_idx = 2

    enhance_mode = prompt_choice(
        "LLM Announcer Script Enhancement Mode:",
        enhance_options,
        default_idx=enhance_idx
    ).split(" ")[0]

    def_batch_script = "true" if models_cfg.get("batch_script_enhancement", True) else "false"
    batch_script_enhancement = prompt_string("Batch Script Enhancement", def_batch_script).lower() == "true"

    def_batch_tts = "true" if models_cfg.get("batch_tts", True) else "false"
    batch_tts = prompt_string("Batch TTS", def_batch_tts).lower() == "true"

    def_tts_batch_size = str(models_cfg.get("tts_batch_size", 10))
    try:
        tts_batch_size = int(prompt_string("TTS Batch Size", def_tts_batch_size))
    except ValueError:
        tts_batch_size = 10

    def_use_vertex = models_cfg.get("use_vertexai", False) or models_cfg.get("platform") == "vertex_ai"
    def_plat_choice = "2" if def_use_vertex else "1"

    print("\nBackend AI Platform:")
    print("  [1] Google AI Studio (Default - required for lyria-3.5 stadium music; uses GEMINI_API_KEY)")
    print("  [2] Google Cloud Vertex AI (Enterprise quotas - supports lyria-3-clip/pro-preview; uses GCP project)")
    plat_choice = prompt_string("Select Backend Platform [1/2]", def_plat_choice).strip()
    use_vertexai = plat_choice in ["2", "vertex", "vertexai"]

    def_gcp_project = models_cfg.get("gcp_project", "")
    gcp_project = prompt_string("GCP Project ID (optional for Vertex AI)", def_gcp_project) if use_vertexai else ""

    def_gcp_location = models_cfg.get("gcp_location", "us-central1")
    gcp_location = prompt_string("GCP Region Location", def_gcp_location) if use_vertexai else "us-central1"

    # Step 5: Background Music Prompt
    print("\n--- STEP 5: Stadium Background Music ---")
    music_cfg = existing_roster.get("music", {})
    def_music_prompt = music_cfg.get(
        "prompt",
        f"Seamless 30-second loopable high-energy arena rock {team_name} entrance music with driving drums and electric guitar"
    )
    music_prompt = prompt_string("🎵 Enter Background Music Prompt", def_music_prompt)

    # Step 6: Intro Announcement Clips
    print("\n--- STEP 6: Intro Announcement Clips ---")
    existing_clips = existing_roster.get("intro_clips")
    fallback_intro_clips = [
        {"filename": "It's Time.wav", "text": "It's time!", "speech_style": "excitedly"},
        {"filename": f"For Your {team_mascot}.wav", "text": f"For your {team_name}!", "phonetic": f"For your {team_mascot}!", "speech_style": "shouting"},
        {"filename": f"LETS GO {team_mascot}.wav", "text": f"Let's go {team_name}!", "phonetic": f"LET'S GOOOOOOOOOO {team_name}!", "speech_style": "shouting, hype"}
    ]

    if existing_clips:
        print(f"Loaded {len(existing_clips)} existing Intro Clips from {roster_path}:")
        for clip in existing_clips:
            print(f"  • {clip['filename']} -> \"{clip.get('phonetic', clip['text'])}\" (style: {clip.get('speech_style') or clip.get('audio_tags', '')})")
        keep_clips = prompt_string("Keep these existing intro clips? (Y/n)", "Y").lower()
        if keep_clips in ["y", "yes"]:
            intro_clips = existing_clips
        else:
            intro_clips = fallback_intro_clips
            print("Reverted to standard default intro clips:")
            for clip in intro_clips:
                print(f"  • {clip['filename']} -> \"{clip.get('phonetic', clip['text'])}\" (style: {clip.get('speech_style') or clip.get('audio_tags', '')})")
    else:
        intro_clips = fallback_intro_clips
        print("Default Intro Clips configured:")
        for clip in intro_clips:
            print(f"  • {clip['filename']} -> \"{clip.get('phonetic', clip['text'])}\" (style: {clip.get('speech_style') or clip.get('audio_tags', '')})")

    # Step 7: Player Roster Input
    print("\n--- STEP 7: Team Roster Entry ---")
    existing_roster_players = existing_roster.get("roster")
    roster = []

    fallback_roster = [
        {"number": "7", "name": "Alex Smith"},
        {"number": "14", "name": "Lochlane Thompson", "phonetic": "Lock-lin Tom-sun"},
        {"number": "67", "name": "Peyton Garcia", "phonetic_number": "Six. Sev-uhn."},
        {"number": "30", "name": "Dakota Harris", "phonetic": "Duh-KOH-tuh HAIR-iss", "post_delay_ms": 1500}
    ]

    if existing_roster_players:
        print(f"Found existing roster with {len(existing_roster_players)} players in {roster_path}:")
        for p in existing_roster_players[:5]:
            p_phonetic = f" ({p.get('phonetic')})" if p.get("phonetic") else ""
            print(f"  • #{p.get('number')} {p.get('name')}{p_phonetic}")
        if len(existing_roster_players) > 5:
            print(f"  ... and {len(existing_roster_players) - 5} more")

        keep_roster = prompt_string(f"Keep this existing roster of {len(existing_roster_players)} players? (Y/n)", "Y").lower()
        if keep_roster in ["y", "yes"]:
            roster = existing_roster_players

    if not roster:
        print("Enter players for your roster. Press Enter on Jersey Number when finished.")
        player_count = 1
        while True:
            num = input(f"\nPlayer #{player_count} Jersey Number (e.g. 7, or Enter to finish): ").strip()
            if not num:
                if not roster:
                    print("ℹ️  No players entered. Adding sample starting roster...")
                    roster = fallback_roster
                break
            name = prompt_string(f"Player #{player_count} Name (e.g. Alex Smith)")
            phonetic = prompt_string("Phonetic Name Override (optional, Enter to skip)")

            p_data = {"number": num, "name": name}
            if phonetic:
                p_data["phonetic"] = phonetic
            roster.append(p_data)
            player_count += 1

    # Output Filename Resolution
    mascot_slug = team_mascot.strip().lower().replace(" ", "_").replace("-", "_") if team_mascot else "team"
    def_roster_filename = f"roster_templates_{mascot_slug}.json"
    def_run_of_show_filename = f"run_of_show_{mascot_slug}.json"

    print("\n--- STEP 8: Saving Configuration Files ---")
    roster_filename = prompt_string("Roster Configuration File to Save", def_roster_filename)
    run_of_show_filename = prompt_string("Run of Show Configuration File to Save", def_run_of_show_filename)

    # Step 8: Build and Write JSON Files
    persona_dict = {
        "style": announcer_style,
        "theme_context": announcer_theme,
        "voice_name": voice_name,
        "speech_style": speech_style,
        "prompt_prefix": persona_cfg.get(
            "prompt_prefix",
            "Say rapidly with intense, fast-paced stadium PA announcer energy, quick delivery, and high enthusiasm: "
        )
    }
    if regional_accent:
        persona_dict["regional_accent"] = regional_accent
    if accent_guidance:
        persona_dict["accent_guidance"] = accent_guidance

    roster_config = {
        "team_name": team_name,
        "team_mascot": team_mascot,
        "models": {
            "api_engine": models_cfg.get("api_engine", "interactions"),
            "tts_model": tts_model,
            "llm_model": llm_model,
            "music_model": music_model,
            "enhance_scripts": enhance_mode,
            "batch_script_enhancement": batch_script_enhancement,
            "batch_tts": batch_tts,
            "tts_batch_size": tts_batch_size,
            "use_vertexai": use_vertexai,
            "gcp_project": gcp_project,
            "gcp_location": gcp_location
        },
        "announcer_persona": persona_dict,
        "player_template": existing_roster.get("player_template", "Number {number}, <short pause> {name}!"),
        "roster": roster,
        "intro_clips": intro_clips,
        "music": {
            "filename": music_cfg.get("filename", "background_music.mp3"),
            "prompt": music_prompt,
            "duration_seconds": music_cfg.get("duration_seconds", 30),
            "max_duration_seconds": music_cfg.get("max_duration_seconds", 120),
            "loopable": music_cfg.get("loopable", True)
        }
    }

    show_settings = existing_show.get("settings", {})
    def_output_file = (
        show_settings.get("output_filename")
        or f"{team_name.lower().replace(' ', '_')}_intro_assembled.mp3"
    )

    if existing_show.get("sequence") and intro_clips == existing_clips:
        sequence = existing_show["sequence"]
    else:
        sequence = [
            {"file": "It's Time.wav", "ducking": False, "pre_delay_ms": 1500, "post_delay_ms": 500, "reverb": "stadium"},
            {"file": f"For Your {team_mascot}.wav", "ducking": False, "pre_delay_ms": 0, "post_delay_ms": 500, "reverb": "stadium"},
            {"file": "$ROSTER", "ducking": True, "pre_delay_ms": 0, "post_delay_ms": 1400, "thicken": False, "reverb": "stadium"},
            {"file": f"LETS GO {team_mascot}.wav", "ducking": False, "pre_delay_ms": 0, "post_delay_ms": 500, "thicken": True, "reverb": "coliseum"}
        ]

    run_of_show_config = {
        "settings": {
            "music_folder": show_settings.get("music_folder", "music"),
            "music_file": show_settings.get("music_file", music_cfg.get("filename", "background_music.mp3")),
            "music_volume_db": show_settings.get("music_volume_db", -6),
            "input_folder": show_settings.get("input_folder", "input"),
            "output_folder": show_settings.get("output_folder", "output"),
            "output_filename": def_output_file,
            "roster_config": roster_filename,
            "normalize_output": show_settings.get("normalize_output", True),
            "default_ducking_vol_db": show_settings.get("default_ducking_vol_db", -8),
            "normalize_voice_clips": show_settings.get("normalize_voice_clips", True),
            "default_voice_boost_db": show_settings.get("default_voice_boost_db", 5),
            "reverb_preset": show_settings.get("reverb_preset", "stadium")
        },
        "sequence": sequence
    }

    with open(roster_filename, "w", encoding="utf-8") as f:
        json.dump(roster_config, f, indent=2)
    print(f"✅ Created {roster_filename}")

    with open(run_of_show_filename, "w", encoding="utf-8") as f:
        json.dump(run_of_show_config, f, indent=2)
    print(f"✅ Created {run_of_show_filename}")

    print("\n" + "=" * 65)
    print("🎉 SETUP COMPLETE!")
    print("=" * 65)
    print(f"Team:        {team_name}")
    print(f"Announcer:   {voice_name}")
    print(f"Roster Size: {len(roster)} players")
    print(f"Roster File: {roster_filename}")
    print(f"Sequence:    {run_of_show_filename}")
    print(f"Out File:    output/{run_of_show_config['settings']['output_filename']}\n")

    run_preview = prompt_string(f"🚀 Run 'python generate_gemini_audio.py -r {roster_filename} --dry-run' now? (y/N)", "N").lower()
    if run_preview in ["y", "yes"]:
        print("\n🔍 Previewing generated prompts and cost estimate...")
        subprocess.run([sys.executable, "generate_gemini_audio.py", "-r", roster_filename, "--dry-run"])


if __name__ == "__main__":
    main()
