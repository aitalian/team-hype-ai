#!/usr/bin/env python3
"""
TeamHypeAI - Interactive Live Demo & First-Time Setup Wizard

A batteries-included, interactive terminal wizard designed for both quick crowd-polled
live demos and first-time project onboarding. Guides users through configuring their
team name, mascot, announcer voice persona, speech style, music prompt, intro clips,
and player roster while keeping sensible implied defaults from existing configs.

Automatically tags all generated audio clips and output files with the mascot slug
(`_<mascot_slug>.wav` / `_<mascot_slug>.mp3`) so new runs never overwrite existing
team artifacts, and runs the entire pipeline start-to-finish (config generation ->
Gemini TTS & Lyria music synthesis -> DSP show assembly & mastering).

Usage:
    python3 setup_wizard.py
"""

import os
import re
import sys
import copy
import json
import argparse
import subprocess

from common import (
    load_dotenv_if_present,
    load_gemini_voices,
    warn_if_inactive_models,
    print_cli_banner,
    get_mascot_slug,
    apply_mascot_slug_to_filename,
    DEFAULT_TTS_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_MUSIC_MODEL,
    DEFAULT_SPEECH_STYLE,
)


def prompt_string(prompt_text, default_val=""):
    suffix = f" [{default_val}]" if default_val != "" else ""
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


def load_existing_configs(roster_path="roster_templates.json", show_path="run_of_show.json"):
    """
    Reads existing roster and run_of_show JSON template files if present.
    Returns (existing_roster, existing_show, roster_path, show_path).
    """
    existing_roster = {}
    existing_show = {}

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


def derive_default_mascot(team_name: str, def_team_name: str, existing_roster: dict) -> str:
    """
    Derives a default mascot/slogan based on whether the user kept the template's team name
    or entered a new team name.
    """
    existing_mascot = (
        existing_roster.get("team_mascot")
        or existing_roster.get("mascot")
        or ""
    )
    if team_name.strip().lower() == def_team_name.strip().lower() and existing_mascot:
        return existing_mascot

    words = team_name.strip().split()
    if len(words) > 1:
        return words[-1]
    return team_name.strip() or "Team"


def replace_template_tokens(text: str, old_team: str, old_mascot: str, new_team: str, new_mascot: str) -> str:
    """
    Generically replaces references to the template's original team_name and team_mascot
    with the newly configured team_name and team_mascot, preserving case (UPPERCASE vs Title/normal).
    """
    if not text:
        return text
    result = text

    for old_val, new_val in [(old_team, new_team), (old_mascot, new_mascot)]:
        old_clean = (old_val or "").strip()
        new_clean = (new_val or "").strip()
        if not old_clean or not new_clean or old_clean.lower() == new_clean.lower():
            continue

        def _repl(match):
            matched = match.group(0)
            if matched.isupper():
                return new_clean.upper()
            if matched.islower():
                return new_clean.lower()
            return new_clean

        result = re.sub(re.escape(old_clean), _repl, result, flags=re.IGNORECASE)

    return result


def build_adapted_intro_clips(existing_clips: list, team_name: str, team_mascot: str, def_team_name: str, def_team_mascot: str, mascot_slug: str):
    """
    Clones existing intro clips from the JSON template, generically replaces any references to
    the template's team_name/team_mascot if changed, and suffixes every clip filename with _{mascot_slug}.wav.
    Returns (adapted_clips, filename_map) where filename_map maps original filename -> new slugged filename.
    """
    adapted = []
    filename_map = {}
    team_changed = (
        team_name.strip().lower() != def_team_name.strip().lower()
        or team_mascot.strip().lower() != def_team_mascot.strip().lower()
    )

    for raw_clip in existing_clips:
        clip = copy.deepcopy(raw_clip)
        orig_fname = clip.get("filename", "Intro.wav")

        if team_changed:
            updated_fname = replace_template_tokens(orig_fname, def_team_name, def_team_mascot, team_name, team_mascot)
            clip["filename"] = apply_mascot_slug_to_filename(updated_fname, mascot_slug)
            if "text" in clip:
                clip["text"] = replace_template_tokens(clip["text"], def_team_name, def_team_mascot, team_name, team_mascot)
            if "phonetic" in clip:
                clip["phonetic"] = replace_template_tokens(clip["phonetic"], def_team_name, def_team_mascot, team_name, team_mascot)
        else:
            clip["filename"] = apply_mascot_slug_to_filename(orig_fname, mascot_slug)

        filename_map[orig_fname] = clip["filename"]
        adapted.append(clip)

    return adapted, filename_map


def prompt_players_interactive(starting_roster=None):
    """
    Prompts interactively to add 1 or more players to the roster.
    """
    roster = list(starting_roster) if starting_roster else []
    print("\nEnter player details (press Enter on Jersey Number when finished):")
    player_count = len(roster) + 1
    while True:
        try:
            num = input(f"\n  Player #{player_count} Jersey Number (e.g. 7, or Enter to finish): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n🛑 Setup cancelled.")
            sys.exit(0)
        if not num:
            break
        name = prompt_string(f"  Player #{player_count} Name (e.g. Alex Smith)")
        if not name:
            continue
        phonetic = prompt_string("  Phonetic Name Override (optional, Enter to skip)")
        custom_intro = prompt_string("  Optional Nickname / Custom Intro (e.g. 'The Code Wizard, wearing number {number}, {name}!', Enter to skip)")

        p_data = {"number": num, "name": name}
        if phonetic:
            p_data["phonetic"] = phonetic
        if custom_intro:
            p_data["custom_intro"] = custom_intro
        roster.append(p_data)
        player_count += 1
    return roster


def main():
    parser = argparse.ArgumentParser(description="Interactive Setup & Live Demo Wizard for TeamHypeAI.")
    parser.add_argument("-r", "--roster-template", default="roster_templates.json", help="Baseline roster template JSON to read defaults from (default: roster_templates.json)")
    parser.add_argument("-c", "--show-template", default="run_of_show.json", help="Baseline run of show JSON to read defaults from (default: run_of_show.json)")
    args = parser.parse_args()

    print_cli_banner(
        utility_title="INTERACTIVE SETUP & LIVE DEMO WIZARD (setup_wizard.py)",
        what_it_is="End-to-end interactive wizard for crowd-polling team identity, voice personas, rosters & full show generation.",
        how_it_works="Prompts for key creative inputs (keeping smart defaults), tags artifacts with your mascot slug, and runs generation + assembly."
    )

    existing_roster, existing_show, roster_path, show_path = load_existing_configs(
        roster_path=args.roster_template,
        show_path=args.show_template,
    )
    has_existing = bool(existing_roster or existing_show)

    if has_existing:
        print("📄 Loaded baseline defaults from:")
        if existing_roster:
            print(f"   • Roster template:    {roster_path}")
        if existing_show:
            print(f"   • Run of Show config: {show_path}")
        print("   ℹ️  Press Enter on any prompt to accept the [default] value.\n")

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

    # Step 2: Team Identity (Crowd Poll)
    print("\n--- STEP 2: Team Identity & Announcer Persona ---")
    persona_cfg = existing_roster.get("announcer_persona", {})

    def_team_name = existing_roster.get("team_name") or "Team"
    team_name = prompt_string("🏆 Enter Team Name", def_team_name)

    def_team_mascot = derive_default_mascot(team_name, def_team_name, existing_roster)
    team_mascot = prompt_string("📣 Enter Mascot / Slogan", def_team_mascot)
    mascot_slug = get_mascot_slug(team_mascot or team_name) or "team"
    print(f"   🏷️  Artifact filename slug: _{mascot_slug}")

    def_announcer_style = persona_cfg.get("style", "High-energy championship arena PA announcer")
    announcer_style = prompt_string("🎙️ Enter PA Announcer Style Persona", def_announcer_style)

    def_announcer_theme = persona_cfg.get("theme_context", "")
    announcer_theme = prompt_string("⚓ Optional Announcer Theme / Context", def_announcer_theme)

    def_regional_accent = persona_cfg.get("regional_accent", "")
    regional_accent = prompt_string("🌍 Optional Regional Accent (e.g. French Canadian, British)", def_regional_accent)

    def_accent_guidance = persona_cfg.get("accent_guidance", "")
    if regional_accent:
        if regional_accent.strip().lower() == def_regional_accent.strip().lower() and def_accent_guidance:
            accent_guidance = def_accent_guidance
        else:
            accent_guidance = prompt_string("🗣️ Optional Accent Guidance / Pronunciation notes", def_accent_guidance)
    else:
        accent_guidance = ""

    # Step 3: Voice Selection (Crowd Poll)
    print("\n--- STEP 3: Announcer Voice Selection ---")
    def_voice_name = persona_cfg.get("voice_name", "Puck")
    voice_defs = load_gemini_voices()
    voice_options = [
        f"{'★ ' if v.get('is_featured') else '  '}{v['name']} ({v.get('gender', '')} | {v.get('announcer_style') or v.get('description', '')})"
        for v in voice_defs
    ]

    default_voice_idx = 0
    for idx, v in enumerate(voice_defs):
        if v.get("name", "").lower() == def_voice_name.lower():
            default_voice_idx = idx
            break

    selected_voice_opt = prompt_choice("Select Announcer Voice Persona:", voice_options, default_idx=default_voice_idx)
    voice_name = selected_voice_opt.replace("★", "").strip().split(" ")[0]

    # Step 4: Speech Style & AI Models (Fast Default with Optional Advanced Toggle)
    print("\n--- STEP 4: Speech Style & AI Model Configuration ---")
    def_speech_style = persona_cfg.get("speech_style") or persona_cfg.get("audio_tags", DEFAULT_SPEECH_STYLE)
    speech_style = prompt_string("🎙️ Gemini TTS Speech Style & Nuance", def_speech_style)

    models_cfg = existing_roster.get("models", {})
    tts_model = models_cfg.get("tts_model", DEFAULT_TTS_MODEL)
    llm_model = models_cfg.get("llm_model", DEFAULT_LLM_MODEL)
    music_model = models_cfg.get("music_model", DEFAULT_MUSIC_MODEL)
    enhance_mode = models_cfg.get("enhance_scripts", "auto")
    batch_script_enhancement = bool(models_cfg.get("batch_script_enhancement", True))
    batch_tts = bool(models_cfg.get("batch_tts", True))
    tts_batch_size = int(models_cfg.get("tts_batch_size", 10))
    use_vertexai = bool(models_cfg.get("use_vertexai", False) or models_cfg.get("platform") == "vertex_ai")
    gcp_project = models_cfg.get("gcp_project", "")
    gcp_location = models_cfg.get("gcp_location", "us-central1")

    plat_label = "Vertex AI" if use_vertexai else "Google AI Studio"
    print(f"\n   ℹ️  AI Pipeline Defaults: TTS={tts_model} | Script={llm_model} ({enhance_mode}, batched) | Music={music_model} | Platform={plat_label}")
    customize_models = prompt_string("⚙️  Customize advanced AI model & batching settings? (y/N)", "N").lower()

    if customize_models in ["y", "yes"]:
        tts_model = prompt_string("TTS Voice Model", tts_model)
        llm_model = prompt_string("Script Synthesizer Model", llm_model)
        music_model = prompt_string("Background Music AI Model", music_model)
        warn_if_inactive_models({
            "tts_voice": tts_model,
            "announcer_script": llm_model,
            "music_generator": music_model
        })

        enhance_options = [
            "auto (Auto-enhance items without manual phonetic overrides)",
            "always (Force LLM enhancement for all items)",
            "never (Disable LLM script enhancement)"
        ]
        enhance_idx = 1 if enhance_mode == "always" else (2 if enhance_mode == "never" else 0)
        enhance_mode = prompt_choice(
            "LLM Announcer Script Enhancement Mode:",
            enhance_options,
            default_idx=enhance_idx
        ).split(" ")[0]

        def_batch_script = "true" if batch_script_enhancement else "false"
        batch_script_enhancement = prompt_string("Batch Script Enhancement", def_batch_script).lower() == "true"

        def_batch_tts = "true" if batch_tts else "false"
        batch_tts = prompt_string("Batch TTS", def_batch_tts).lower() == "true"

        try:
            tts_batch_size = int(prompt_string("TTS Batch Size", str(tts_batch_size)))
        except ValueError:
            tts_batch_size = 10

        def_plat_choice = "2" if use_vertexai else "1"
        print("\nBackend AI Platform:")
        print("  [1] Google AI Studio (Default - required for lyria-3.5 stadium music; uses GEMINI_API_KEY)")
        print("  [2] Google Cloud Vertex AI (Enterprise quotas - supports lyria-3-clip/pro-preview; uses GCP project)")
        plat_choice = prompt_string("Select Backend Platform [1/2]", def_plat_choice).strip()
        use_vertexai = plat_choice in ["2", "vertex", "vertexai"]
        gcp_project = prompt_string("GCP Project ID (optional for Vertex AI)", gcp_project) if use_vertexai else ""
        gcp_location = prompt_string("GCP Region Location", gcp_location) if use_vertexai else "us-central1"

    # Step 5: Stadium Background Music
    print("\n--- STEP 5: Stadium Background Music ---")
    music_cfg = existing_roster.get("music", {})
    def_music_prompt = music_cfg.get(
        "prompt",
        f"Seamless 30-second loopable high-energy arena rock {team_name} entrance music with driving drums and electric guitar"
    )
    music_prompt = prompt_string("🎵 Enter Background Music Prompt", def_music_prompt)

    existing_music_file = music_cfg.get("filename", "background_music.mp3")
    existing_music_path = os.path.join("music", existing_music_file)
    slugged_music_file = apply_mascot_slug_to_filename("background_music.mp3", mascot_slug)

    if music_prompt.strip() != def_music_prompt.strip():
        music_filename = slugged_music_file
        print(f"   🎵 Custom music prompt entered -> will generate 'music/{music_filename}'")
    elif os.path.exists(existing_music_path) and os.path.getsize(existing_music_path) > 0:
        reuse_music = prompt_string(
            f"⏩ Reuse existing cached music track ('{existing_music_file}') for faster demo? (Y/n)",
            "Y"
        ).lower()
        if reuse_music in ["y", "yes"]:
            music_filename = existing_music_file
        else:
            music_filename = slugged_music_file
            print(f"   🎵 Will generate fresh music track -> 'music/{music_filename}'")
    else:
        music_filename = slugged_music_file

    # Step 6: Intro Announcement Clips (Mascot-Slugged)
    print("\n--- STEP 6: Intro Announcement Clips ---")
    existing_clips = existing_roster.get("intro_clips")
    fallback_intro_clips = [
        {
            "filename": apply_mascot_slug_to_filename("It's Time.wav", mascot_slug),
            "text": "It's time!",
            "speech_style": "excitedly"
        },
        {
            "filename": apply_mascot_slug_to_filename(f"For Your {team_mascot}.wav", mascot_slug),
            "text": f"For your {team_name}!",
            "phonetic": f"For your {team_mascot}!",
            "speech_style": "shouting"
        },
        {
            "filename": apply_mascot_slug_to_filename(f"LETS GO {team_mascot}.wav", mascot_slug),
            "text": f"Let's go {team_name}!",
            "phonetic": f"LET'S GOOOOOOOOOO {team_name}!",
            "speech_style": "shouting, hype"
        }
    ]

    intro_filename_map = {}
    used_adapted_existing = False

    if existing_clips:
        adapted_clips, intro_filename_map = build_adapted_intro_clips(
            existing_clips,
            team_name=team_name,
            team_mascot=team_mascot,
            def_team_name=def_team_name,
            def_team_mascot=existing_roster.get("team_mascot") or existing_roster.get("mascot") or def_team_name,
            mascot_slug=mascot_slug,
        )
        print(f"Configured {len(adapted_clips)} Intro Clips (tagged with _{mascot_slug}):")
        for clip in adapted_clips:
            print(f"  • {clip['filename']} -> \"{clip.get('phonetic', clip['text'])}\"")

        clip_choice = prompt_string(
            "Intro clips option: [Y]es keep these / [s]tandard 3-clip intro / [c]ustomize text (Y/s/c)",
            "Y"
        ).lower()

        if clip_choice in ["s", "standard"]:
            intro_clips = fallback_intro_clips
            print("Selected standard 3-clip intro:")
            for clip in intro_clips:
                print(f"  • {clip['filename']} -> \"{clip.get('phonetic', clip['text'])}\"")
        elif clip_choice in ["c", "custom", "customize"]:
            intro_clips = []
            for clip in adapted_clips:
                new_txt = prompt_string(f"  Spoken text for {clip['filename']}", clip.get("phonetic") or clip.get("text", ""))
                c_copy = dict(clip)
                c_copy["text"] = new_txt
                c_copy["phonetic"] = new_txt
                intro_clips.append(c_copy)
            used_adapted_existing = True
        else:
            intro_clips = adapted_clips
            used_adapted_existing = True
    else:
        intro_clips = fallback_intro_clips
        print("Default Intro Clips configured:")
        for clip in intro_clips:
            print(f"  • {clip['filename']} -> \"{clip.get('phonetic', clip['text'])}\"")

    # Step 7: Player Roster Input (Crowd Poll)
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
        print(f"Found {len(existing_roster_players)} players in {roster_path} (will generate as #Num Name_{mascot_slug}.wav):")
        for p in existing_roster_players[:6]:
            p_phonetic = f" ({p.get('phonetic')})" if p.get("phonetic") else ""
            p_file = apply_mascot_slug_to_filename(f"#{p.get('number')} {p.get('name')}.wav", mascot_slug)
            print(f"  • {p_file}{p_phonetic}")
        if len(existing_roster_players) > 6:
            print(f"  ... and {len(existing_roster_players) - 6} more")

        roster_mode = prompt_string(
            f"Roster options: [K]eep existing {len(existing_roster_players)} players / [A]dd crowd players / [N]ew roster (K/a/n)",
            "K"
        ).lower()

        if roster_mode in ["a", "add"]:
            roster = prompt_players_interactive(starting_roster=copy.deepcopy(existing_roster_players))
        elif roster_mode in ["n", "new", "no"]:
            roster = prompt_players_interactive(starting_roster=[])
        else:
            roster = copy.deepcopy(existing_roster_players)

    if not roster:
        roster = prompt_players_interactive(starting_roster=[])
        if not roster:
            print("ℹ️  No players entered. Adding sample starting roster...")
            roster = fallback_roster

    # Step 8: Output Filename Resolution & Saving Configs
    roster_filename = f"roster_templates_{mascot_slug}.json"
    run_of_show_filename = f"run_of_show_{mascot_slug}.json"

    print("\n--- STEP 8: Saving Configuration Files ---")

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
            "filename": music_filename,
            "prompt": music_prompt,
            "duration_seconds": music_cfg.get("duration_seconds", 30),
            "max_duration_seconds": music_cfg.get("max_duration_seconds", 120),
            "loopable": music_cfg.get("loopable", True)
        }
    }

    show_settings = existing_show.get("settings", {})
    raw_base_out = show_settings.get("output_filename") or f"{get_mascot_slug(team_name) or 'team'}_intro_assembled.mp3"
    def_output_file = apply_mascot_slug_to_filename(raw_base_out, mascot_slug)

    if existing_show.get("sequence") and used_adapted_existing:
        sequence = []
        for ev in existing_show["sequence"]:
            ev_copy = copy.deepcopy(ev)
            orig_f = ev_copy.get("file", "")
            if orig_f in intro_filename_map:
                ev_copy["file"] = intro_filename_map[orig_f]
            elif orig_f and orig_f != "$ROSTER" and not orig_f.lower().startswith("sfx_"):
                ev_copy["file"] = apply_mascot_slug_to_filename(orig_f, mascot_slug)
            sequence.append(ev_copy)
    else:
        sequence = [
            {"file": intro_clips[0]["filename"], "ducking": False, "pre_delay_ms": 1500, "post_delay_ms": 500, "reverb": "stadium"},
            {"file": intro_clips[1]["filename"], "ducking": False, "pre_delay_ms": 0, "post_delay_ms": 500, "reverb": "stadium"},
            {"file": "$ROSTER", "ducking": True, "pre_delay_ms": 0, "post_delay_ms": 1400, "thicken": False, "reverb": "stadium"},
            {"file": intro_clips[2]["filename"], "ducking": False, "pre_delay_ms": 0, "post_delay_ms": 500, "thicken": True, "reverb": "coliseum"}
        ]

    run_of_show_config = {
        "settings": {
            "music_folder": show_settings.get("music_folder", "music"),
            "music_file": music_filename,
            "music_volume_db": show_settings.get("music_volume_db", -6),
            "input_folder": show_settings.get("input_folder", "input"),
            "output_folder": show_settings.get("output_folder", "output"),
            "output_filename": def_output_file,
            "roster_config": roster_filename,
            "normalize_output": show_settings.get("normalize_output", True),
            "default_ducking_vol_db": show_settings.get("default_ducking_vol_db", -9),
            "normalize_voice_clips": show_settings.get("normalize_voice_clips", True),
            "default_voice_boost_db": show_settings.get("default_voice_boost_db", 0),
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

    final_output_path = os.path.join(
        run_of_show_config["settings"]["output_folder"],
        run_of_show_config["settings"]["output_filename"]
    )

    print("\n" + "=" * 68)
    print("🎉 CONFIGURATION READY!")
    print("=" * 68)
    print(f"Team:          {team_name} ({team_mascot})")
    print(f"Artifact Slug: _{mascot_slug}")
    print(f"Announcer:     {voice_name}")
    print(f"Roster Size:   {len(roster)} players")
    print(f"Roster Config: {roster_filename}")
    print(f"Run of Show:   {run_of_show_filename}")
    print(f"Target Audio:  {final_output_path}")
    print("=" * 68 + "\n")

    # Step 9: Start-to-Finish Execution (Generate AI Audio + Assemble Final Mix)
    run_action = prompt_string(
        "🚀 Generate AI audio clips & assemble final stadium show now? ([Y]es full pipeline / [d]ry-run preview / [n]o)",
        "Y"
    ).lower()

    if run_action in ["d", "dry", "dry-run"]:
        print(f"\n🔍 Running dry-run preview for {roster_filename}...")
        subprocess.run([sys.executable, "generate_gemini_audio.py", "-r", roster_filename, "--dry-run"])
    elif run_action in ["y", "yes"]:
        print(f"\n🎙️  [1/2] Generating AI voice clips & music via generate_gemini_audio.py (-r {roster_filename})...")
        gen_res = subprocess.run([sys.executable, "generate_gemini_audio.py", "-r", roster_filename, "-y"])
        if gen_res.returncode != 0:
            print(f"\n❌ Audio generation exited with code {gen_res.returncode}. Skipping show assembly.")
            sys.exit(gen_res.returncode)

        print(f"\n🎚️  [2/2] Assembling & mastering final stadium show via assemble_show.py (-c {run_of_show_filename})...")
        asm_res = subprocess.run([
            sys.executable,
            "assemble_show.py",
            "-c",
            run_of_show_filename,
            "-r",
            roster_filename,
            "-f"
        ])
        if asm_res.returncode == 0 and os.path.exists(final_output_path):
            print("\n" + "=" * 68)
            print("🏟️  START-TO-FINISH SHOW PRODUCTION COMPLETE!")
            print("=" * 68)
            print(f"🎧 Final Assembled MP3: {final_output_path}")
            print("=" * 68)

            if sys.platform == "darwin" and sys.stdin.isatty():
                play_now = prompt_string(f"\n🔊 Play '{final_output_path}' now over speaker output? (y/N)", "N").lower()
                if play_now in ["y", "yes"]:
                    print(f"▶️  Playing {final_output_path} (Press Ctrl+C to stop playback)...")
                    try:
                        subprocess.run(["afplay", final_output_path])
                    except KeyboardInterrupt:
                        print("\n⏹️  Playback stopped.")


if __name__ == "__main__":
    main()
