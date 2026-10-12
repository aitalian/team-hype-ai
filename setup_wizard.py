#!/usr/bin/env python3
"""
TeamHypeAI - Interactive First-Time Setup Wizard

A batteries-included, interactive terminal wizard that guides first-time users step-by-step
through configuring their team name, mascot, announcer voice persona, models, intro clips, and roster.
Outputs ready-to-use `roster_templates.json` and `run_of_show.json` files.

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
    check_model_status,
    warn_if_inactive_models,
    DEFAULT_TTS_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_MUSIC_MODEL,
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


def main():
    print("=" * 65)
    print("🚀 TeamHypeAI - Interactive First-Time Setup Wizard")
    print("=" * 65)
    print("Welcome! This wizard will help you set up your sports team intro audio")
    print("pipeline in just a few quick steps.\n")

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

    # Step 2: Team Identity
    print("\n--- STEP 2: Team Identity ---")
    team_name = prompt_string("🏆 Enter Team Name", "Eagles")
    team_mascot = prompt_string("📣 Enter Mascot / Slogan", team_name.upper())
    announcer_style = prompt_string("🎙️ Enter PA Announcer Style Persona", "High-energy championship arena PA announcer")
    announcer_theme = prompt_string("⚓ Optional Announcer Theme / Context (e.g. pirate, space commander, retro rockstar)", "")

    # Step 3: Voice Selection
    print("\n--- STEP 3: Announcer Voice Selection ---")
    print("Sample clips can be generated into `samples/` for auditioning voices.")
    sample_opt = prompt_string("Generate voice audition clips now in samples/? (y/N)", "N").lower()
    if sample_opt in ["y", "yes"]:
        print("🎙️ Launching generate_voice_samples.py --dry-run...")
        subprocess.run([sys.executable, "generate_voice_samples.py", "--dry-run"])

    voice_defs = load_gemini_voices()
    voice_options = [
        f"{'★ ' if v.get('is_featured') else '  '}{v['name']} ({v.get('gender', '')} | {v.get('announcer_style') or v.get('description', '')})"
        for v in voice_defs
    ]

    selected_voice_opt = prompt_choice("Select Announcer Voice Persona:", voice_options, default_idx=0)
    voice_name = selected_voice_opt.replace("★", "").strip().split(" ")[0]

    # Step 4: AI Models, Audio Tags & Script Enhancement
    print("\n--- STEP 4: AI Models & Audio Tags ---")
    tts_model = prompt_string("TTS Voice Model", DEFAULT_TTS_MODEL)
    llm_model = prompt_string("Script Synthesizer Model", DEFAULT_LLM_MODEL)
    music_model = prompt_string("Background Music AI Model", DEFAULT_MUSIC_MODEL)
    warn_if_inactive_models({
        "tts_voice": tts_model,
        "announcer_script": llm_model,
        "music_generator": music_model
    })
    audio_tags = prompt_string("🔊 Gemini TTS Audio Tags (e.g. [excitedly], [shouting], [excitedly, fast-paced])", DEFAULT_AUDIO_TAGS)
    enhance_mode = prompt_choice(
        "LLM Announcer Script Enhancement Mode:",
        [
            "auto (Auto-enhance items without manual phonetic overrides)",
            "always (Force LLM enhancement for all items)",
            "never (Disable LLM script enhancement)"
        ],
        default_idx=0
    ).split(" ")[0]
    batch_script_enhancement = prompt_string("Batch Script Enhancement", "true").lower() == "true"
    batch_tts = prompt_string("Batch TTS", "true").lower() == "true"
    try:
        tts_batch_size = int(prompt_string("TTS Batch Size", "10"))
    except ValueError:
        tts_batch_size = 10
    use_vertexai = prompt_string("Use Google Cloud Vertex AI Platform? (y/N)", "N").lower() in ["y", "yes"]
    gcp_project = prompt_string("GCP Project ID (optional for Vertex AI)", "") if use_vertexai else ""
    gcp_location = prompt_string("GCP Region Location", "us-central1") if use_vertexai else "us-central1"

    # Step 5: Background Music Prompt
    print("\n--- STEP 5: Stadium Background Music ---")
    music_prompt = prompt_string(
        "🎵 Enter Background Music Prompt",
        f"Seamless 30-second loopable high-energy arena rock {team_name} entrance music with driving drums and electric guitar"
    )

    # Step 6: Intro Clips
    print("\n--- STEP 6: Intro Announcement Clips ---")
    intro_clips = [
        {"filename": "It's Time.wav", "text": "It's time!", "audio_tags": "[excitedly]"},
        {"filename": f"For Your {team_mascot}.wav", "text": f"For your {team_name}!", "phonetic": f"For your {team_mascot}!", "audio_tags": "[shouting]"},
        {"filename": f"LETS GO {team_mascot}.wav", "text": f"Let's go {team_name}!", "phonetic": f"LET'S GOOOOOOOOOO {team_name}!", "audio_tags": "[shouting, hype]"}
    ]
    print("Default Intro Clips configured:")
    for clip in intro_clips:
        print(f"  • {clip['filename']} -> \"{clip.get('phonetic', clip['text'])}\" (tags: {clip.get('audio_tags', '')})")

    # Step 7: Player Roster Input
    print("\n--- STEP 7: Team Roster Entry ---")
    print("Enter players for your roster. Press Enter on Jersey Number when finished.")
    roster = []
    player_count = 1
    while True:
        num = input(f"\nPlayer #{player_count} Jersey Number (e.g. 7, or Enter to finish): ").strip()
        if not num:
            if not roster:
                print("ℹ️  No players entered. Adding sample starting roster...")
                roster = [
                    {"number": "7", "name": "Alex Smith"},
                    {"number": "14", "name": "Lochlane Thompson", "phonetic": "Lock-lin Tom-sun"},
                    {"number": "67", "name": "Peyton Garcia", "phonetic_number": "Six. Sev-uhn."},
                    {"number": "30", "name": "Dakota Harris", "phonetic": "Duh-KOH-tuh HAIR-iss", "post_delay_ms": 1500}
                ]
            break
        name = prompt_string(f"Player #{player_count} Name (e.g. Alex Smith)")
        phonetic = prompt_string(f"Phonetic Name Override (optional, Enter to skip)")
        
        p_data = {"number": num, "name": name}
        if phonetic:
            p_data["phonetic"] = phonetic
        roster.append(p_data)
        player_count += 1

    mascot_slug = team_mascot.strip().lower().replace(" ", "_").replace("-", "_") if team_mascot else "team"
    roster_filename = f"roster_templates_{mascot_slug}.json"
    run_of_show_filename = f"run_of_show_{mascot_slug}.json"

    # Step 8: Build and Write JSON Files
    roster_config = {
        "models": {
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
        "announcer_persona": {
            "style": announcer_style,
            "theme_context": announcer_theme,
            "voice_name": voice_name,
            "audio_tags": audio_tags,
            "prompt_prefix": "Say rapidly with intense, fast-paced stadium PA announcer energy, quick delivery, and high enthusiasm: "
        },
        "player_template": "Number {number}, {name}!",
        "roster": roster,
        "intro_clips": intro_clips,
        "music": {
            "filename": "background_music.mp3",
            "prompt": music_prompt,
            "duration_seconds": 30,
            "max_duration_seconds": 120,
            "loopable": True
        }
    }

    run_of_show_config = {
        "settings": {
            "music_folder": "music",
            "music_file": "background_music.mp3",
            "music_volume_db": -6,
            "input_folder": "input",
            "output_folder": "output",
            "output_filename": f"{team_name.lower().replace(' ', '_')}_intro_assembled.mp3",
            "roster_config": roster_filename,
            "normalize_output": True,
            "default_ducking_vol_db": -8,
            "normalize_voice_clips": True,
            "default_voice_boost_db": 5
        },
        "sequence": [
            {"file": "It's Time.wav", "ducking": False, "pre_delay_ms": 1500, "post_delay_ms": 500},
            {"file": f"For Your {team_mascot}.wav", "ducking": False, "pre_delay_ms": 0, "post_delay_ms": 500},
            {"file": "$ROSTER", "ducking": True, "pre_delay_ms": 0, "post_delay_ms": 1400, "thicken": False},
            {"file": f"LETS GO {team_mascot}.wav", "ducking": False, "pre_delay_ms": 0, "post_delay_ms": 500, "thicken": True}
        ]
    }

    print("\n--- STEP 8: Saving Configuration Files ---")
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

    run_preview = prompt_string(f"🚀 Run 'python generate_gemini_audio.py -r {roster_filename} --dry-run' now? (Y/n)", "Y").lower()
    if run_preview in ["y", "yes"]:
        print("\n🔍 Previewing generated prompts and cost estimate...")
        subprocess.run([sys.executable, "generate_gemini_audio.py", "-r", roster_filename, "--dry-run"])


if __name__ == "__main__":
    main()
