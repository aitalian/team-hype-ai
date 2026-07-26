import json
import os
import argparse
from pydub import AudioSegment
from pydub.effects import normalize

from common import load_json_file

# --- DEFAULTS ---
DEFAULT_CONFIG_FILE = "run_of_show.json"
DEFAULT_MUSIC_VOL = -3
DEFAULT_DUCKING_VOL = -15
DEFAULT_PRE_SEQUENCE = 3000

def apply_thickening(audio_clip):
    """
    Applies the pitch-shift effect to make voices sound deeper/larger.
    """
    new_sample_rate = int(audio_clip.frame_rate * 0.95)
    thickened = audio_clip._spawn(audio_clip.raw_data, overrides={'frame_rate': new_sample_rate})
    return thickened.set_frame_rate(44100)

def ensure_music_length(music, required_len, current_cursor, loop_enabled=True):
    target_length = current_cursor + required_len
    if len(music) >= target_length:
        return music

    missing_time = target_length - len(music)
    
    if loop_enabled:
        print("   (Looping music track extended...)")
        while len(music) < target_length:
            music = music + music
    else:
        print(f"   (Music ended. Extending timeline with {missing_time}ms of silence...)")
        silence_padding = AudioSegment.silent(duration=missing_time + 5000)
        music = music + silence_padding
        
    return music

def expand_sequence(sequence, roster_config_path="roster_templates.json"):
    """
    Expands $ROSTER macro placeholders in sequence with entries from roster_templates.json.
    """
    expanded = []
    roster_data = []
    if os.path.exists(roster_config_path):
        t_data = load_json_file(roster_config_path, description="roster config template")
        roster_data = t_data.get("roster", [])

    for event in sequence:
        file_val = event.get("file", "")
        if file_val == "$ROSTER" or event.get("expand_roster"):
            override_keys = ("pre_delay_ms", "post_delay_ms", "ducking", "thicken", "voice_boost_db", "ducking_vol_db")

            for player in roster_data:
                p_num = player.get("number", "")
                p_name = player.get("name", "")

                p_event = dict(event)
                p_event["file"] = f"#{p_num} {p_name}.wav"

                for key in override_keys:
                    if player.get(key) is not None:
                        p_event[key] = player[key]

                expanded.append(p_event)
        else:
            expanded.append(event)

    return expanded

def assemble_mix(config, roster_config_override=None):
    settings = config.get("settings", {})
    raw_sequence = config.get("sequence", [])
    roster_config = roster_config_override or settings.get("roster_config", "roster_templates.json")
    sequence = expand_sequence(raw_sequence, roster_config)

    input_folder = settings.get("input_folder", ".")
    output_folder = settings.get("output_folder", ".")
    music_folder = settings.get("music_folder", ".")
    
    music_filename = settings.get("music_file", "music.mp3")
    output_filename = settings.get("output_filename", "final_mix.mp3")
    
    # Audio Levels
    music_vol = settings.get("music_volume_db", DEFAULT_MUSIC_VOL)
    global_ducking_vol = settings.get("default_ducking_vol_db", DEFAULT_DUCKING_VOL)
    
    # Voice Controls
    normalize_clips = settings.get("normalize_voice_clips", True)
    global_voice_boost = settings.get("default_voice_boost_db", 0)

    # Output Controls
    normalize_output = settings.get("normalize_output", True)

    # Music Timing
    music_start_time = settings.get("music_start_time_ms", 0)
    music_end_time = settings.get("music_end_time_ms", 0)
    music_loop = settings.get("music_loop", True)
    
    # Sequence Timing
    initial_silence = settings.get("initial_silence_ms", 0)
    pre_sequence_duration = settings.get("pre_sequence_music_ms", DEFAULT_PRE_SEQUENCE)

    # Load Music
    full_music_path = os.path.join(music_folder, music_filename)
    if not os.path.exists(full_music_path):
        alt_path = full_music_path.rsplit('.', 1)[0] + '.wav' if '.' in full_music_path else full_music_path + '.wav'
        if os.path.exists(alt_path):
            full_music_path = alt_path
        else:
            raise FileNotFoundError(f"❌ Missing background music: {full_music_path}")

    print(f"🎧 Loading music: {full_music_path}")
    music = AudioSegment.from_file(full_music_path)

    # Slice Music
    start_ms = music_start_time
    end_ms = music_end_time if (music_end_time > 0 and music_end_time < len(music)) else len(music)
    
    if start_ms >= end_ms:
        start_ms = 0
        end_ms = len(music)

    if start_ms > 0 or end_ms < len(music):
        print(f"✂️  Trimming Music: {start_ms}ms to {end_ms}ms")
        music = music[start_ms:end_ms]

    music = music + music_vol
    
    # --- START MIXING ---
    final_mix = AudioSegment.silent(duration=0)
    music_cursor = 0
    
    if initial_silence > 0:
        final_mix += AudioSegment.silent(duration=initial_silence)

    if pre_sequence_duration > 0:
        music = ensure_music_length(music, pre_sequence_duration, music_cursor, music_loop)
        final_mix += music[:pre_sequence_duration]
        music_cursor += pre_sequence_duration

    print("🎚️  Stitching audio events...")

    for i, event in enumerate(sequence):
        filename = event.get('file')
        should_duck = event.get('ducking', True)
        item_ducking_vol = event.get('ducking_vol_db', global_ducking_vol)
        
        pre_delay = event.get('pre_delay_ms', 0)
        post_delay = event.get('post_delay_ms', 0)
        should_thicken = event.get('thicken', False)
        clip_max_duration = event.get('clip_duration_ms', 0)
        
        # Per-clip boost override
        item_voice_boost = event.get('voice_boost_db', global_voice_boost)

        full_clip_path = os.path.join(input_folder, filename)
        if not os.path.exists(full_clip_path):
            print(f"⚠️ Warning: File '{filename}' not found. Skipping.")
            continue

        # --- PROCESS CLIP ---
        clip = AudioSegment.from_file(full_clip_path)

        if clip_max_duration > 0:
            clip = clip[:clip_max_duration]

        if should_thicken:
            clip = apply_thickening(clip)

        # 1. NORMALIZE CLIP (Maximize Volume)
        if normalize_clips:
            clip = normalize(clip)

        # 2. APPLY BOOST (Push it even louder)
        if item_voice_boost != 0:
            clip = clip + item_voice_boost

        clip_duration = len(clip)

        # --- PRE-DELAY ---
        if pre_delay > 0:
            music = ensure_music_length(music, pre_delay, music_cursor, music_loop)
            final_mix += music[music_cursor : music_cursor + pre_delay]
            music_cursor += pre_delay

        # --- MIXING CLIP ---
        music = ensure_music_length(music, clip_duration, music_cursor, music_loop)
        music_segment = music[music_cursor : music_cursor + clip_duration]
        
        if should_duck:
            music_segment = music_segment + item_ducking_vol
        
        mixed_part = music_segment.overlay(clip)
        final_mix += mixed_part
        music_cursor += clip_duration

        # --- POST-DELAY ---
        if post_delay > 0:
            music = ensure_music_length(music, post_delay, music_cursor, music_loop)
            final_mix += music[music_cursor : music_cursor + post_delay]
            music_cursor += post_delay

        print(f"   [{i+1}/{len(sequence)}] Added {filename} (Vol Boost: {item_voice_boost}dB)")

    # Tail
    tail_duration = 4000
    music = ensure_music_length(music, tail_duration, music_cursor, music_loop)
    tail = music[music_cursor : music_cursor + tail_duration]
    final_mix += tail.fade_out(3000)

    # --- FINAL NORMALIZATION ---
    if normalize_output:
        print("🔊 Normalizing final mix...")
        final_mix = normalize(final_mix, headroom=0.1)

    return final_mix, output_folder, output_filename

def main():
    parser = argparse.ArgumentParser(description="Assemble sports audio intro mix from Run of Show config.")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG_FILE, help="Path to Run of Show JSON config (default: run_of_show.json)")
    parser.add_argument("-r", "--roster-config", help="Path to roster template config JSON (overrides roster_config in run_of_show settings)")
    parser.add_argument("-f", "--force", action="store_true", help="Force re-assembly even if output file already exists")
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ Error: Config file '{args.config}' not found.")
        return

    try:
        with open(args.config, 'r') as f:
            config = json.load(f)

        settings = config.get("settings", {})
        out_folder = settings.get("output_folder", ".")
        out_file = settings.get("output_filename", "final_mix.mp3")
        target_path = os.path.join(out_folder, out_file)

        if not args.force and os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            print("\n" + "=" * 60)
            print(f"✨ Target output mix file already exists: {target_path}")
            print("   Nothing to assemble! (Pass --force or -f to re-assemble)")
            print("=" * 60 + "\n")
            return

        final_mix, out_folder, out_file = assemble_mix(config, roster_config_override=args.roster_config)

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        path = os.path.join(out_folder, out_file)
        final_mix.export(path, format="mp3")
        print(f"\n✅ DONE! File saved to: {path}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

