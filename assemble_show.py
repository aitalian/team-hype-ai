import json
import os
import argparse
from pydub import AudioSegment
from pydub.effects import normalize

from common import load_json_file, print_cli_banner

# --- DEFAULTS ---
DEFAULT_CONFIG_FILE = "run_of_show.json"
DEFAULT_MUSIC_VOL = -3
DEFAULT_DUCKING_VOL = -15
DEFAULT_PRE_SEQUENCE = 3000

# Stadium Echo / Reverb Presets:
# Each preset defines multi-tap acoustic reflections (delay_ms, gain_db, low_pass_hz)
# plus optional bass_boost_db (low-end stadium warmth) and tail_ms (extra acoustic tail padding).
REVERB_PRESETS = {
    "none": {
        "description": "Dry signal (no echo or reverb)",
        "taps": [],
        "bass_boost_db": 0,
        "tail_ms": 0,
    },
    "subtle": {
        "description": "Tight indoor gym / studio PA slapback",
        "taps": [
            {"delay_ms": 65, "gain_db": -10.0, "low_pass_hz": 4200},
            {"delay_ms": 135, "gain_db": -15.0, "low_pass_hz": 3200},
            {"delay_ms": 220, "gain_db": -21.0, "low_pass_hz": 2400},
        ],
        "bass_boost_db": 1.5,
        "tail_ms": 250,
    },
    "arena": {
        "description": "Classic indoor hockey arena / basketball bowl reverb",
        "taps": [
            {"delay_ms": 55, "gain_db": -8.5, "low_pass_hz": 4500},
            {"delay_ms": 115, "gain_db": -11.0, "low_pass_hz": 3600},
            {"delay_ms": 190, "gain_db": -14.5, "low_pass_hz": 2800},
            {"delay_ms": 280, "gain_db": -18.5, "low_pass_hz": 2200},
            {"delay_ms": 390, "gain_db": -23.0, "low_pass_hz": 1700},
        ],
        "bass_boost_db": 2.5,
        "tail_ms": 420,
    },
    "stadium": {
        "description": "Loud, booming championship sports stadium PA echo & reverb",
        "taps": [
            {"delay_ms": 45, "gain_db": -7.5, "low_pass_hz": 4800},
            {"delay_ms": 95, "gain_db": -9.5, "low_pass_hz": 3800},
            {"delay_ms": 165, "gain_db": -12.0, "low_pass_hz": 3000},
            {"delay_ms": 250, "gain_db": -15.0, "low_pass_hz": 2400},
            {"delay_ms": 350, "gain_db": -18.5, "low_pass_hz": 1900},
            {"delay_ms": 470, "gain_db": -22.5, "low_pass_hz": 1500},
            {"delay_ms": 600, "gain_db": -27.0, "low_pass_hz": 1200},
        ],
        "bass_boost_db": 3.5,
        "tail_ms": 600,
    },
    "coliseum": {
        "description": "Massive open-air coliseum / canyon echo with dramatic long tail",
        "taps": [
            {"delay_ms": 55, "gain_db": -6.5, "low_pass_hz": 4800},
            {"delay_ms": 120, "gain_db": -8.5, "low_pass_hz": 3800},
            {"delay_ms": 210, "gain_db": -11.0, "low_pass_hz": 3000},
            {"delay_ms": 320, "gain_db": -13.5, "low_pass_hz": 2400},
            {"delay_ms": 450, "gain_db": -16.5, "low_pass_hz": 1900},
            {"delay_ms": 600, "gain_db": -20.0, "low_pass_hz": 1500},
            {"delay_ms": 770, "gain_db": -24.0, "low_pass_hz": 1200},
            {"delay_ms": 950, "gain_db": -28.5, "low_pass_hz": 1000},
        ],
        "bass_boost_db": 4.5,
        "tail_ms": 900,
    },
}
DEFAULT_REVERB_PRESET = "stadium"


def resolve_reverb_config(reverb_val, default_preset=DEFAULT_REVERB_PRESET, custom_wet_mix=None, custom_bass_boost=None):
    """
    Resolves an event or global reverb setting into an active DSP parameter dictionary.
    Supports:
      - False / None / "none" / "off" -> disabled
      - True -> uses default_preset (fallback to 'stadium')
      - String preset name ('subtle', 'arena', 'stadium', 'coliseum')
      - Dict with custom parameters: {"enabled": true, "preset": "stadium", "wet_gain_offset_db": 0, "bass_boost_db": 3.5, "tail_ms": 600, "taps": [...]}
    """
    if reverb_val is False or reverb_val is None:
        return None
    if isinstance(reverb_val, str):
        norm = reverb_val.strip().lower()
        if norm in ("none", "off", "false", "0", "dry"):
            return None
        preset_key = norm if norm in REVERB_PRESETS else default_preset
        base = dict(REVERB_PRESETS.get(preset_key, REVERB_PRESETS[DEFAULT_REVERB_PRESET]))
        base["preset_name"] = preset_key
    elif reverb_val is True:
        eff_key = default_preset if (default_preset and default_preset in REVERB_PRESETS and default_preset != "none") else DEFAULT_REVERB_PRESET
        base = dict(REVERB_PRESETS[eff_key])
        base["preset_name"] = eff_key
    elif isinstance(reverb_val, dict):
        if not reverb_val.get("enabled", True):
            return None
        preset_key = str(reverb_val.get("preset", default_preset or DEFAULT_REVERB_PRESET)).strip().lower()
        if preset_key in ("none", "off", "false", "dry"):
            return None
        template = REVERB_PRESETS.get(preset_key, REVERB_PRESETS[DEFAULT_REVERB_PRESET])
        base = dict(template)
        base["preset_name"] = preset_key
        if "taps" in reverb_val and isinstance(reverb_val["taps"], list):
            base["taps"] = reverb_val["taps"]
        if "bass_boost_db" in reverb_val:
            base["bass_boost_db"] = float(reverb_val["bass_boost_db"])
        if "tail_ms" in reverb_val:
            base["tail_ms"] = int(reverb_val["tail_ms"])
        if "wet_gain_offset_db" in reverb_val:
            base["wet_gain_offset_db"] = float(reverb_val["wet_gain_offset_db"])
    else:
        return None

    if not base.get("taps") and base.get("bass_boost_db", 0) == 0:
        return None

    if custom_wet_mix is not None:
        base["wet_gain_offset_db"] = float(custom_wet_mix)
    if custom_bass_boost is not None:
        base["bass_boost_db"] = float(custom_bass_boost)

    return base


def apply_stadium_reverb(audio_clip, reverb_cfg):
    """
    Applies stadium PA acoustic reverb, multi-tap slapback echo, and low-end bass warmth
    to make announcements sound loud, booming, and arena-ready.

    DSP Chain:
      1. Low-End Bass Resonance ("Boom"): Extracts sub-220Hz warm body and layers it onto
         the dry voice for chest-thumping PA speaker authority.
      2. Multi-Tap Acoustic Reflections: Generates early arena reflections (45-120ms) and
         late stadium bowl decay taps (165-950ms), each progressively low-pass filtered
         to simulate high-frequency air absorption across a massive sports venue.
      3. Acoustic Tail Preservation: Extends the clip canvas by `tail_ms` with a smooth
         fade-out so booming echoes ring out naturally over the background music.
    """
    if not reverb_cfg:
        return audio_clip

    taps = reverb_cfg.get("taps", [])
    bass_boost_db = float(reverb_cfg.get("bass_boost_db", 0))
    tail_ms = int(reverb_cfg.get("tail_ms", 0))
    wet_offset_db = float(reverb_cfg.get("wet_gain_offset_db", 0.0))

    # Standardize sample rate for clean filtering and overlay
    working = audio_clip.set_frame_rate(44100)

    # 1. Apply low-end stadium bass warmth ("booming PA chest resonance")
    if bass_boost_db > 0:
        # Isolate low frequencies (< 220 Hz) and blend underneath the dry voice
        low_end = working.low_pass_filter(220) + (bass_boost_db - 6.0)
        working = working.overlay(low_end)

    if not taps:
        return working

    # 2. Pad clip duration so the stadium echo tail can ring out without abrupt cutoff
    max_delay = max((int(t.get("delay_ms", 0)) for t in taps), default=0)
    effective_tail = max(tail_ms, min(max_delay + 150, 1200))
    if effective_tail > 0:
        canvas = working + AudioSegment.silent(duration=effective_tail, frame_rate=44100)
    else:
        canvas = working

    # 3. Layer progressive multi-tap reflections with high-frequency damping
    wet_accumulation = AudioSegment.silent(duration=len(canvas), frame_rate=44100)
    for tap in taps:
        delay_ms = int(tap.get("delay_ms", 0))
        gain_db = float(tap.get("gain_db", -12.0)) + wet_offset_db
        lp_hz = int(tap.get("low_pass_hz", 3000))

        if delay_ms <= 0:
            continue

        reflected = audio_clip.set_frame_rate(44100)
        if lp_hz > 0:
            reflected = reflected.low_pass_filter(lp_hz)
        # Gently roll off sub-mud on long echo tails (< 120Hz) so echoes stay crisp
        reflected = reflected.high_pass_filter(120)
        reflected = reflected + gain_db

        wet_accumulation = wet_accumulation.overlay(reflected, position=delay_ms)

    # Smoothly fade out the tail end of the wet reflections
    if effective_tail > 100:
        wet_accumulation = wet_accumulation.fade_out(min(effective_tail, 500))

    return canvas.overlay(wet_accumulation)


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
            override_keys = (
                "pre_delay_ms",
                "post_delay_ms",
                "ducking",
                "thicken",
                "reverb",
                "echo",
                "voice_boost_db",
                "ducking_vol_db",
            )

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

def assemble_mix(config, roster_config_override=None, cli_reverb_preset=None, cli_no_reverb=False):
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

    # Stadium Reverb / Echo Controls
    global_reverb_preset = (
        "none"
        if cli_no_reverb
        else (
            cli_reverb_preset
            or settings.get("reverb_preset")
            or settings.get("stadium_reverb")
            or DEFAULT_REVERB_PRESET
        )
    )
    global_reverb_wet_offset = settings.get("reverb_wet_gain_offset_db")
    global_bass_boost = settings.get("reverb_bass_boost_db")
    default_apply_reverb = settings.get("apply_reverb_by_default", False)

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

        # Resolve per-clip reverb / echo setting (supports 'reverb' or 'echo' key)
        if cli_no_reverb:
            raw_reverb = False
        elif cli_reverb_preset:
            # If CLI preset is forced, apply it to all non-SFX voice clips unless explicitly false
            event_rev = event.get("reverb", event.get("echo"))
            if event_rev is False:
                raw_reverb = False
            else:
                raw_reverb = cli_reverb_preset
        else:
            raw_reverb = event.get("reverb", event.get("echo", default_apply_reverb))

        reverb_cfg = resolve_reverb_config(
            raw_reverb,
            default_preset=global_reverb_preset,
            custom_wet_mix=event.get("reverb_wet_gain_offset_db", global_reverb_wet_offset),
            custom_bass_boost=event.get("reverb_bass_boost_db", global_bass_boost),
        )
        
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

        # 1. NORMALIZE DRY CLIP BEFORE REVERB
        if normalize_clips:
            clip = normalize(clip)

        # 2. APPLY STADIUM PA REVERB / ECHO & BASS BOOM
        if reverb_cfg:
            clip = apply_stadium_reverb(clip, reverb_cfg)
            if normalize_clips:
                clip = normalize(clip)

        # 3. APPLY BOOST (Push it even louder)
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

        fx_tags = []
        if should_thicken:
            fx_tags.append("Thicken")
        if reverb_cfg:
            fx_tags.append(f"Reverb:{reverb_cfg.get('preset_name', 'stadium')}")
        fx_str = f", FX: {'+'.join(fx_tags)}" if fx_tags else ""
        print(f"   [{i+1}/{len(sequence)}] Added {filename} (Vol Boost: {item_voice_boost}dB{fx_str})")

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
    parser.add_argument(
        "--reverb",
        choices=list(REVERB_PRESETS.keys()),
        help="Override stadium echo/reverb preset across voice announcements (choices: none, subtle, arena, stadium, coliseum)"
    )
    parser.add_argument("--no-reverb", action="store_true", help="Disable all stadium echo/reverb effects")
    parser.add_argument("-f", "--force", action="store_true", help="Force re-assembly even if output file already exists")
    args = parser.parse_args()
    
    print_cli_banner(
        utility_title="AUDIO DSP MIXING & MASTERING ENGINE (assemble_show.py)",
        what_it_is="Broadcast assembly engine that mixes voice clips, sound effects, and music into a master stadium track.",
        how_it_works="Applies 0.95x voice pitch thickening, multi-tap stadium PA reverb & bass boom, dynamic music ducking, and peak normalization."
    )

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

        final_mix, out_folder, out_file = assemble_mix(
            config,
            roster_config_override=args.roster_config,
            cli_reverb_preset=args.reverb,
            cli_no_reverb=args.no_reverb,
        )

        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        path = os.path.join(out_folder, out_file)
        final_mix.export(path, format="mp3")
        print(f"\n✅ DONE! File saved to: {path}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

