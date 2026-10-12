#!/usr/bin/env python3
"""
Generate Sports Audio Clips exclusively using Google Gemini & Lyria AI Models.

This script leverages Google Gemini models to generate high-energy stadium announcer
voice clips, player introductions, and royalty-free stadium background music.

Features:
  - Auto-sources GEMINI_API_KEY from local .env file if present.
  - Automatic rate-limit handling & exponential backoff (10 req/min API limit).
  - Resumes automatically without re-generating existing clips.

Requirements:
  - GEMINI_API_KEY environment variable must be set (or in .env).
  - google-genai Python SDK installed (pip install google-genai)

Models Used:
  - Text-to-Speech (TTS): gemini-3.8-flash-tts / gemini-3.8-flash-lite-tts / gemini-3.1-flash-tts-preview
  - Announcer Script Synthesizer: gemini-3.8-flash / gemini-3.6-flash / gemini-3.5-flash-lite
  - Music Generation: lyria-3.5 / lyria-3-clip-preview / lyria-3-pro-preview
"""

import os
import sys
import json
import time
import argparse
import wave
import random
import re


def parse_retry_duration_str(duration_str):
    """
    Parses duration strings like '1h47m9.647852093s', '2m30s', '45.5s', or '6429s' into total seconds (float).
    """
    if not duration_str:
        return None

    clean_str = str(duration_str).rstrip('.').strip()

    pattern = r'^(?:(\d+)h)?(?:(\d+)m)?(?:([\d\.]+)s)?$'
    match = re.match(pattern, clean_str)

    if not match or not any(match.groups()):
        try:
            return float(clean_str.rstrip('s'))
        except ValueError:
            return None

    hours = float(match.group(1)) if match.group(1) else 0.0
    minutes = float(match.group(2)) if match.group(2) else 0.0
    seconds = float(match.group(3)) if match.group(3) else 0.0

    total_seconds = (hours * 3600.0) + (minutes * 60.0) + seconds
    return total_seconds if total_seconds > 0 else None


def extract_retry_delay_seconds(error, default_delay=60.0):
    """
    Extracts recommended retry wait duration in seconds from API rate limit / 429 errors.
    First checks structured RetryInfo retryDelay fields, then parses regex patterns like
    'Please retry in 1h47m9.647852093s' from error messages.
    """
    error_str = str(error)

    # 1. Check structured RetryInfo retryDelay (e.g. 'retryDelay': '6429s')
    retry_delay_match = re.search(r"['\"]retryDelay['\"]\s*:\s*['\"]([^'\"]+)['\"]", error_str)
    if retry_delay_match:
        parsed_sec = parse_retry_duration_str(retry_delay_match.group(1))
        if parsed_sec is not None:
            return parsed_sec

    # 2. Check "Please retry in <duration>" pattern
    text_match = re.search(r"[Pp]lease retry in\s+([0-9hms\.]+)", error_str)
    if text_match:
        parsed_sec = parse_retry_duration_str(text_match.group(1))
        if parsed_sec is not None:
            return parsed_sec

    # 3. Fall back to default duration
    return default_delay


def format_duration_human(seconds):
    """
    Formats a duration in seconds into a clean human-readable format (e.g. 1h 47m 9.6s, 2m 30s, or 45.0s).
    """
    seconds = float(seconds)
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins, secs = divmod(seconds, 60)
    if mins < 60:
        return f"{int(mins)}m {secs:.1f}s"
    hours, mins = divmod(mins, 60)
    return f"{int(hours)}h {int(mins)}m {secs:.1f}s"


from common import (
    load_dotenv_if_present,
    load_json_file,
    load_gemini_voices,
    get_model_cost_rates,
    log_api_event,
    print_pricing_disclaimer,
    init_gemini_client,
    check_model_status,
    warn_if_inactive_models,
    get_model_availability,
    is_model_available_on_platform,
    get_available_models_for_role,
    DEFAULT_TTS_MODEL,
    DEFAULT_LLM_MODEL,
    DEFAULT_MUSIC_MODEL,
    DEFAULT_VOICE_PERSONA,
    DEFAULT_ENHANCE_MODE,
    DEFAULT_AUDIO_TAGS,
    clean_spoken_text,
    clean_style_directive,
    format_speech_style,
    build_speech_part,
    resolve_platform_backend,
    API_ENGINE_INTERACTIONS,
    API_ENGINE_LEGACY,
    DEFAULT_API_ENGINE,
    resolve_api_engine,
    extract_audio_bytes_from_interaction,
    format_error_brief,
)


def format_audio_tag(tag):
    """
    Normalizes audio tags or style strings into clean delivery style strings for Gemini 3.8 Flash TTS speech_metadata.style.
    Strips enclosing brackets or angle tags.
    """
    if not tag:
        return ""
    return clean_style_directive(str(tag).strip())


def enhance_announcer_script(client, raw_text, llm_model, persona_style="High-energy stadium PA announcer", theme_context="", delivery_instructions="", audio_tag="", regional_accent="", accent_guidance="", max_retries=3, api_engine=DEFAULT_API_ENGINE, allow_fallback=True):
    """
    Uses LLM (e.g. gemini-3.8-flash) to rewrite and format plain text into rapid-fire, high-energy PA announcer scripts
    with phonetic inflections, concise drawn-out vowels, and PA stadium emphasis cues prior to TTS generation.
    Supports Google Interactions API (June 2026 standard) and legacy generateContent API with automatic fallback.
    Observes delivery instructions, regional accent guidance, and audio tags for tone, but strictly outputs clean speech text without tags or prompt prefixes.
    """
    delivery_str = f"Delivery & Cadence Instructions: {delivery_instructions}\n" if delivery_instructions else ""
    tone_str = f"Desired Tone / Energy Cue: {audio_tag}\n" if audio_tag else ""
    accent_info = accent_guidance or (f"Authentic {regional_accent} regional pronunciation for regional/French names and places" if regional_accent else "")
    accent_str = f"Regional Accent & Pronunciation Instructions: {accent_info}\nWhen Francophone names, places, or hockey terms (e.g. Montréal, Canadiens, Patrick Roy, Forum) appear, ensure they are phoneticized or phrased with authentic French Canadian / Quebec regional pronunciation while maintaining stadium rock announcer cadence.\n\n" if accent_info else ""
    theme_str = f"Theme & Context Instructions: {theme_context}\nIncorporate thematic phrasing, tone accents, vocabulary, or puns matching this theme while keeping speech punchy and stadium-ready.\n\n" if theme_context else ""

    prompt = (
        f"You are a professional PA sports announcer script writer. "
        f"Style: {persona_style}.\n\n"
        f"{delivery_str}"
        f"{tone_str}"
        f"{accent_str}"
        f"{theme_str}"
        f"Rewrite the following announcement text into a concise, rapid-fire, high-energy stadium PA script "
        f"for Google Gemini 3.8 Flash TTS speech synthesis. Keep delivery fast-paced, quick, and punchy. Use UPPERCASE for strong stadium emphasis, "
        f"drawn-out vowels ONLY for key player names, and clear punctuation (commas, exclamation points) to guide rapid pitch, volume, and inflection.\n\n"
        f"CRITICAL REQUIREMENTS FOR GEMINI 3.8 TTS VERBATIM MODEL:\n"
        f"1. Infuse the delivery instructions, tone cues, regional accent guidance, and theme directly into the rhythm, casing, and phrasing of the spoken dialogue.\n"
        f"2. You MAY insert '<short pause>' inline for dramatic stadium timing or breathing pauses before big announcements where appropriate.\n"
        f"3. Output ONLY the clean script text to be spoken. Do NOT include explanations, quotes, prompt prefixes (such as 'Say rapidly...'), or bracketed audio tags (e.g. NEVER output [excitedly] or [shouting]) in your output text.\n\n"
        f"Input Text: {clean_spoken_text(raw_text, allow_vocal_tags=True)}"
    )
    for attempt in range(1, max_retries + 1):
        log_api_event("LLM_SCRIPT", "REQUEST", {"model": llm_model, "raw_text": raw_text, "style": persona_style, "theme_context": theme_context, "attempt": attempt, "engine": api_engine})
        try:
            enhanced = ""
            if api_engine == API_ENGINE_INTERACTIONS:
                try:
                    interaction = client.interactions.create(
                        model=llm_model,
                        input=prompt
                    )
                    enhanced = (getattr(interaction, "output_text", None) or "").strip().strip('"\'')
                except Exception as int_err:
                    if allow_fallback and not ("429" in str(int_err) or "RESOURCE_EXHAUSTED" in str(int_err)):
                        log_api_event("LLM_SCRIPT", "FALLBACK_TO_GENERATE_CONTENT", {"error": format_error_brief(int_err)})
                        response = client.models.generate_content(
                            model=llm_model,
                            contents=prompt
                        )
                        enhanced = (getattr(response, "text", "") or "").strip().strip('"\'')
                    else:
                        raise
            else:
                response = client.models.generate_content(
                    model=llm_model,
                    contents=prompt
                )
                enhanced = (getattr(response, "text", "") or "").strip().strip('"\'')

            final_script = clean_spoken_text(enhanced, allow_vocal_tags=True) if enhanced else clean_spoken_text(raw_text, allow_vocal_tags=True)
            log_api_event("LLM_SCRIPT", "SUCCESS", {"model": llm_model, "enhanced_text": final_script, "engine": api_engine})
            return final_script
        except Exception as e:
            brief_err = format_error_brief(e)
            log_api_event("LLM_SCRIPT", "ERROR", {"model": llm_model, "attempt": attempt, "error": brief_err})
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_sec = extract_retry_delay_seconds(e, default_delay=60.0)
                dur_fmt = format_duration_human(wait_sec)
                print(f"   ⏳ Rate limit hit (429) during script enhancement. Waiting {dur_fmt} ({wait_sec:.1f}s) for API quota reset (attempt {attempt}/{max_retries})...")
                time.sleep(wait_sec)
            else:
                if attempt < max_retries:
                    time.sleep(5)
                else:
                    print(f"   ⚠️ LLM Script Enhancement notice ({llm_model}): {brief_err}. Using base prompt.")
                    return clean_spoken_text(raw_text, allow_vocal_tags=True)

    return clean_spoken_text(raw_text, allow_vocal_tags=True)


def batch_enhance_announcer_scripts(client, items_to_enhance, llm_model, persona_style="High-energy stadium PA announcer", theme_context="", delivery_instructions="", regional_accent="", accent_guidance="", max_retries=3, api_engine=DEFAULT_API_ENGINE, allow_fallback=True):
    """
    Uses LLM (e.g. gemini-3.8-flash) in a single API call to rewrite multiple raw scripts in batch into a JSON mapping.
    Supports Google Interactions API (June 2026 standard) and legacy generateContent API with automatic fallback.
    items_to_enhance: list of dicts [{'id': key, 'raw_text': text, 'audio_tag': tag}]
    Returns: dict mapping item id -> clean enhanced text string, or None if fallback is required
    """
    if not items_to_enhance:
        return {}

    prompt_payload = {}
    for item in items_to_enhance:
        prompt_payload[item['id']] = {
            "text": clean_spoken_text(item['raw_text'], allow_vocal_tags=True),
            "tone_cue": item.get('audio_tag', '')
        }
    prompt_json_str = json.dumps(prompt_payload, indent=2)

    delivery_str = f"Delivery & Cadence Instructions: {delivery_instructions}\n" if delivery_instructions else ""
    accent_info = accent_guidance or (f"Authentic {regional_accent} regional pronunciation for regional/French names and places" if regional_accent else "")
    accent_str = f"Regional Accent & Pronunciation Instructions: {accent_info}\nWhen Francophone names, places, or hockey terms (e.g. Montréal, Canadiens, Patrick Roy, Forum) appear, ensure they are phoneticized or phrased with authentic French Canadian / Quebec regional pronunciation while maintaining stadium rock announcer cadence.\n\n" if accent_info else ""
    theme_str = f"Theme & Context Instructions: {theme_context}\nIncorporate thematic phrasing, tone accents, vocabulary, or puns matching this theme while keeping speech punchy and stadium-ready.\n\n" if theme_context else ""

    prompt = (
        f"You are a professional PA sports announcer script writer. Style: {persona_style}.\n\n"
        f"{delivery_str}"
        f"{accent_str}"
        f"{theme_str}"
        f"Rewrite each announcement text in the input JSON into a concise, rapid-fire, high-energy stadium PA script "
        f"for Google Gemini 3.8 Flash TTS speech synthesis.\n"
        f"Keep delivery fast-paced, quick, and punchy. Use UPPERCASE for strong stadium emphasis, "
        f"drawn-out vowels ONLY for key player names, and clear punctuation (commas, exclamation points) to guide rapid pitch, volume, and inflection.\n"
        f"Observe the tone cues, regional accent guidance, and delivery instructions to shape the vocal energy, enthusiasm, and stadium excitement directly through phrasing and typography.\n\n"
        f"CRITICAL REQUIREMENTS FOR GEMINI 3.8 TTS VERBATIM MODEL:\n"
        f"1. Output ONLY the clean script text to be vocalized by the speech synthesizer.\n"
        f"2. You MAY insert '<short pause>' inline for dramatic stadium timing or breathing pauses before big announcements where appropriate.\n"
        f"3. NEVER include the prompt instructions, any directorial prefixes (e.g. 'Say rapidly...'), explanations, or bracketed audio tags (e.g. NEVER output [excitedly], [shouting], or any [tag]) in your output text.\n"
        f"4. Output ONLY a valid JSON object matching the keys of the input JSON, where values are the clean enhanced script strings.\n\n"
        f"Input JSON:\n{prompt_json_str}"
    )

    for attempt in range(1, max_retries + 1):
        log_api_event("LLM_SCRIPT_BATCH", "REQUEST", {"model": llm_model, "count": len(items_to_enhance), "style": persona_style, "attempt": attempt, "engine": api_engine})
        try:
            from google.genai import types
            raw_resp = ""
            if api_engine == API_ENGINE_INTERACTIONS:
                try:
                    interaction = client.interactions.create(
                        model=llm_model,
                        input=prompt,
                        response_format={"type": "json_object"}
                    )
                    raw_resp = (getattr(interaction, "output_text", None) or "").strip()
                except Exception as int_err:
                    if allow_fallback and not ("429" in str(int_err) or "RESOURCE_EXHAUSTED" in str(int_err)):
                        log_api_event("LLM_SCRIPT_BATCH", "FALLBACK_TO_GENERATE_CONTENT", {"error": format_error_brief(int_err)})
                        response = client.models.generate_content(
                            model=llm_model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            )
                        )
                        raw_resp = (getattr(response, "text", "") or "").strip()
                    else:
                        raise
            else:
                response = client.models.generate_content(
                    model=llm_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                raw_resp = (getattr(response, "text", "") or "").strip()

            if raw_resp.startswith("```"):
                lines = raw_resp.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_resp = "\n".join(lines).strip()

            enhanced_map = json.loads(raw_resp)
            # Ensure every output string in map is strictly sanitized
            cleaned_map = {k: clean_spoken_text(v) for k, v in enhanced_map.items()}
            log_api_event("LLM_SCRIPT_BATCH", "SUCCESS", {"model": llm_model, "count": len(cleaned_map), "engine": api_engine})
            return cleaned_map
        except Exception as e:
            brief_err = format_error_brief(e)
            log_api_event("LLM_SCRIPT_BATCH", "ERROR", {"model": llm_model, "attempt": attempt, "error": brief_err})
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_sec = extract_retry_delay_seconds(e, default_delay=60.0)
                dur_fmt = format_duration_human(wait_sec)
                print(f"   ⏳ Rate limit hit (429) during batch script enhancement. Waiting {dur_fmt} ({wait_sec:.1f}s) for API quota reset (attempt {attempt}/{max_retries})...")
                time.sleep(wait_sec)
            else:
                if attempt < max_retries:
                    time.sleep(5)
                else:
                    print(f"   ⚠️ Batched LLM Script Enhancement notice ({llm_model}): {brief_err}. Falling back to 1:1 script enhancement.")
                    return None

    return None


def load_config(config_path):
    return load_json_file(config_path, description="roster template config")



def build_intro_clip_announcement(clip, prefix="", global_audio_tags=""):
    display_text = clip.get("phonetic") or clip.get("spoken_text") or clip.get("text", "")
    return clean_spoken_text(display_text, prefix=prefix)


def build_player_announcement(player, template, prefix="", global_audio_tags=""):
    num = player.get("number", "")
    name = player.get("name", "")
    phonetic_name = player.get("phonetic") or player.get("pronunciation")
    phonetic_num = player.get("phonetic_number") or player.get("number_phonetic")
    custom_intro = player.get("custom_intro")
    pretext = player.get("pretext") or player.get("prefix")

    # Filename uses official player jersey number and name
    filename = f"#{num} {name}.wav"

    # Spoken audio prompt uses phonetic overrides if provided, else official values
    spoken_name = phonetic_name if phonetic_name else name
    spoken_num = phonetic_num if phonetic_num else num

    # 15% probability of inserting "Wearing number" before the jersey number
    rng = random.Random(f"num_prefix_{num}_{name}")
    if rng.random() < 0.15:
        active_template = "Wearing number {number}, {name}!"
    else:
        active_template = template

    if custom_intro:
        if any(k in custom_intro for k in ["{name}", "{number}", "{phonetic}", "{phonetic_number}"]):
            formatted = custom_intro.format(
                number=spoken_num,
                name=spoken_name,
                phonetic=spoken_name,
                phonetic_number=spoken_num
            )
        else:
            intro_clean = custom_intro.strip()
            if not any(intro_clean.endswith(c) for c in [",", "!", "."]):
                intro_clean = f"{intro_clean},"
            formatted = f"{intro_clean} {spoken_name}!" if not spoken_name.endswith("!") else f"{intro_clean} {spoken_name}"
    elif pretext:
        if any(k in pretext for k in ["{name}", "{number}", "{phonetic}", "{phonetic_number}"]):
            formatted = pretext.format(
                number=spoken_num,
                name=spoken_name,
                phonetic=spoken_name,
                phonetic_number=spoken_num
            )
        else:
            pretext_clean = pretext.strip()
            if not any(pretext_clean.endswith(c) for c in [",", "!", "."]):
                pretext_clean = f"{pretext_clean},"
            std_formatted = active_template.format(number=spoken_num, name=spoken_name)
            formatted = f"{pretext_clean} {std_formatted}"
    else:
        formatted = active_template.format(number=spoken_num, name=spoken_name)

    return filename, clean_spoken_text(formatted, prefix=prefix)


def print_cost_report(num_clips, tts_model, llm_model, music_model, num_enhanced_clips=0, generate_music=True, prompts=None, music_prompt="", music_duration_sec=30, batch_script=True, batch_tts=True, batch_size=10, platform_desc="Google AI Studio", use_vertex=False):
    import math
    print("\n" + "=" * 60)
    print("📊 GEMINI COST-EFFECTIVENESS ESTIMATE & API QUOTA REPORT")
    print("=" * 60)
    print(f"🌐 Platform Backend:     {platform_desc}")
    
    if prompts:
        voice_input_tokens = sum(max(1, len(p) // 4) for p in prompts)
    else:
        voice_input_tokens = num_clips * 21

    music_input_tokens = max(1, len(music_prompt) // 4) if (generate_music and music_prompt) else 0

    # LLM Announcer Script Enhancement Tokens (~120 input tokens, ~30 output tokens per script)
    if num_enhanced_clips > 0:
        llm_input_tokens = num_enhanced_clips * 120
        llm_output_tokens = num_enhanced_clips * 30
        llm_rate = get_model_cost_rates(llm_model, category="voice", use_vertex=use_vertex, is_batch=batch_script)
        llm_input_cost = (llm_input_tokens / 1_000_000) * llm_rate["input_1m"]
        llm_output_cost = (llm_output_tokens / 1_000_000) * llm_rate["output_1m"]
        llm_cost = llm_input_cost + llm_output_cost
    else:
        llm_input_tokens = 0
        llm_output_tokens = 0
        llm_cost = 0.0

    total_input_tokens = voice_input_tokens + music_input_tokens + llm_input_tokens

    # Projected Output Tokens & Audio Duration
    voice_audio_mins = num_clips * 0.05
    voice_output_tokens = int(num_clips * 3 * 25) if num_clips else 0  # ~75 tokens per ~3s clip

    music_audio_mins = (music_duration_sec / 60.0) if generate_music else 0.0
    music_output_tokens = int(music_duration_sec * 25) if generate_music else 0

    total_output_tokens = voice_output_tokens + music_output_tokens + llm_output_tokens

    if num_clips > 0:
        tts_rate = get_model_cost_rates(tts_model, category="voice", use_vertex=use_vertex, is_batch=batch_tts)
        tts_input_cost = (voice_input_tokens / 1_000_000) * tts_rate["input_1m"]
        tts_output_cost = (voice_output_tokens / 1_000_000) * tts_rate["output_1m"]
        tts_cost = tts_input_cost + tts_output_cost
    else:
        tts_cost = 0.0

    if generate_music:
        music_rate = get_model_cost_rates(music_model, category="music", use_vertex=use_vertex, is_batch=False)
        music_cost = music_rate["song_request"]
    else:
        music_cost = 0.0

    total_cost = tts_cost + music_cost + llm_cost

    # API Request Count Projections
    llm_req_count = 1 if (batch_script and num_enhanced_clips > 0) else num_enhanced_clips
    tts_req_count = math.ceil(num_clips / batch_size) if (batch_tts and num_clips > 0) else num_clips
    music_req_count = 1 if generate_music else 0
    total_req_count = llm_req_count + tts_req_count + music_req_count

    unbatched_req_count = num_enhanced_clips + num_clips + music_req_count
    saved_req_count = unbatched_req_count - total_req_count

    print(f"⚡ API Request Quota Efficiency:")
    if num_enhanced_clips > 0:
        script_mode_str = "Batched JSON" if batch_script else "1:1 Requests"
        print(f"   • Batched LLM Requests:   {llm_req_count} request(s) ({script_mode_str})")
    if num_clips > 0:
        tts_mode_str = f"Batched Slicing, batch size={batch_size}" if batch_tts else "1:1 Requests"
        print(f"   • Batched TTS Requests:   {tts_req_count} request(s) ({tts_mode_str})")
    if generate_music:
        print(f"   • Music Request:         1 request")
    if saved_req_count > 0:
        print(f"   👉 Total API Requests:    {total_req_count} request(s) (Saved {saved_req_count} API calls vs unbatched {unbatched_req_count})")
    else:
        print(f"   👉 Total API Requests:    {total_req_count} request(s)")

    print("\n🔤 Estimated Input Tokens:")
    if num_clips > 0:
        avg_tokens = (voice_input_tokens / num_clips) if num_clips else 0
        print(f"   • Voice Prompts:       ~{voice_input_tokens:,} input tokens ({num_clips} clips, ~{avg_tokens:.1f} tokens/clip)")
    if num_enhanced_clips > 0:
        print(f"   • Script Synthesizer:  ~{llm_input_tokens:,} input tokens ({num_enhanced_clips} scripts enhanced via {llm_model})")
    if generate_music and music_prompt:
        print(f"   • Music Prompt:        ~{music_input_tokens:,} input tokens ({len(music_prompt)} chars)")
    print(f"   • Total Input:         ~{total_input_tokens:,} input tokens\n")

    print("🔊 Projected Output Tokens / Audio Output:")
    if num_clips > 0:
        print(f"   • Voice Audio Output:  ~{voice_output_tokens:,} output tokens ({num_clips} clips @ ~3s/clip, ~{voice_audio_mins:.2f} mins total)")
    if num_enhanced_clips > 0:
        print(f"   • Script Text Output:  ~{llm_output_tokens:,} output tokens ({num_enhanced_clips} enhanced text scripts)")
    if generate_music:
        print(f"   • Music Audio Output:  ~{music_output_tokens:,} output tokens (1 track @ {music_duration_sec}s audio)")
    print(f"   • Total Output:        ~{total_output_tokens:,} output tokens (~{(voice_audio_mins + music_audio_mins):.2f} mins total audio)")
    print("   ℹ️  * Note: Audio tokens correspond to 25 tokens per second of generated audio.\n")

    if num_enhanced_clips > 0:
        batch_str = " [Batch Rate]" if batch_script else ""
        print(f"🧠 Script Synthesizer ({num_enhanced_clips} scripts using {llm_model}{batch_str}): ~${llm_cost:.6f} USD")
    if num_clips > 0:
        platform_str = " [Vertex AI Rate]" if use_vertex else " [AI Studio Rate]"
        print(f"🎙️ Voice Clips ({num_clips} clips using {tts_model}{platform_str}): ~${tts_cost:.6f} USD")
    if generate_music:
        print(f"🎵 Music Clip (1 song request using {music_model}): ~${music_cost:.4f} USD")
    print("------------------------------------------------------------")
    print(f"💵 ESTIMATED TOTAL GENERATION COST: ~${total_cost:.5f} USD")
    print("------------------------------------------------------------")
    print_pricing_disclaimer(
        use_vertex=use_vertex,
        has_tts=(num_clips > 0),
        has_llm=(num_enhanced_clips > 0),
        has_music=generate_music
    )
    print("=" * 60 + "\n")



def save_audio_bytes(audio_bytes, mime_type, out_path):
    """
    Saves audio bytes, automatically adding a WAV header if raw PCM is returned by Gemini.
    """
    mime_type = mime_type or ""
    if audio_bytes.startswith(b"RIFF") or audio_bytes.startswith(b"ID3") or audio_bytes.startswith(b"\xff\xfb") or audio_bytes.startswith(b"\xff\xf3"):
        with open(out_path, "wb") as f:
            f.write(audio_bytes)
    else:
        # Gemini audio output default: 24kHz 16-bit Mono PCM
        sample_rate = 24000
        if "rate=" in mime_type:
            try:
                sample_rate = int(mime_type.split("rate=")[1].split(";")[0])
            except Exception:
                sample_rate = 24000

        with wave.open(out_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)


def generate_audio_clip_gemini(client, text, filename, output_dir, model_name, voice_name="Puck", style="", force=False, max_retries=3, api_engine=DEFAULT_API_ENGINE, allow_fallback=True):
    """
    Generates high-energy announcer voice audio using Google GenAI SDK with rate-limit retries.
    Supports Google Interactions API (June 2026 standard) and legacy generateContent API with automatic fallback.
    Uses native types.SpeechMetadata(speaker=voice_name, style=style) for Gemini 3.8 Flash TTS.
    """
    out_path = os.path.join(output_dir, filename)

    # Resume/Skip check
    if not force and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"   ⏩ Skipping existing clip: {out_path}")
        return True

    from google.genai import types
    from google.genai.errors import APIError

    part = build_speech_part(text, voice_name=voice_name, style=style)
    clean_text = part.text

    for attempt in range(1, max_retries + 1):
        log_api_event("VOICE_TTS", "REQUEST", {
            "filename": filename,
            "model": model_name,
            "voice": voice_name,
            "style": style,
            "attempt": attempt,
            "text": clean_text,
            "engine": api_engine
        })
        try:
            audio_data = None
            mime_type = "audio/wav"

            if api_engine == API_ENGINE_INTERACTIONS:
                try:
                    interaction = client.interactions.create(
                        model=model_name,
                        input=clean_text,
                        response_format={"type": "audio"},
                        generation_config={"speech_config": [{"voice": voice_name}]}
                    )
                    audio_data, mime_type = extract_audio_bytes_from_interaction(interaction)
                except Exception as int_err:
                    if allow_fallback and not ("429" in str(int_err) or "RESOURCE_EXHAUSTED" in str(int_err)):
                        log_api_event("VOICE_TTS", "FALLBACK_TO_GENERATE_CONTENT", {"filename": filename, "error": format_error_brief(int_err)})
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[part],
                            config=types.GenerateContentConfig(
                                response_modalities=["AUDIO"],
                                speech_config=types.SpeechConfig(
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                                    )
                                )
                            )
                        )
                        if response and getattr(response, "candidates", None):
                            candidate = response.candidates[0]
                            if candidate and getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                                for p in candidate.content.parts:
                                    if hasattr(p, "inline_data") and p.inline_data:
                                        audio_data = p.inline_data.data
                                        mime_type = getattr(p.inline_data, "mime_type", "audio/wav")
                                        break
                    else:
                        raise
            else:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[part],
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                            )
                        )
                    )
                )
                if response and getattr(response, "candidates", None):
                    candidate = response.candidates[0]
                    if candidate and getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                        for p in candidate.content.parts:
                            if hasattr(p, "inline_data") and p.inline_data:
                                audio_data = p.inline_data.data
                                mime_type = getattr(p.inline_data, "mime_type", "audio/wav")
                                break

            if audio_data:
                save_audio_bytes(audio_data, mime_type, out_path)
                log_api_event("VOICE_TTS", "SUCCESS", {"filename": filename, "model": model_name, "voice": voice_name, "mime_type": mime_type, "bytes": len(audio_data), "engine": api_engine})
                print(f"   ✅ Gemini Voice Saved ({mime_type}): {out_path}")
                time.sleep(6)
                return True
            else:
                raise RuntimeError(f"No audio data returned by Gemini API for '{filename}'")

        except APIError as e:
            brief_err = format_error_brief(e)
            log_api_event("VOICE_TTS", "API_ERROR", {"filename": filename, "attempt": attempt, "error": brief_err})
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_sec = extract_retry_delay_seconds(e, default_delay=60.0)
                dur_fmt = format_duration_human(wait_sec)
                print(f"   ⏳ Rate limit hit (429). Waiting {dur_fmt} ({wait_sec:.1f}s) for API quota reset (attempt {attempt}/{max_retries})...")
                time.sleep(wait_sec)
            else:
                if attempt < max_retries:
                    print(f"   ⚠️ Retrying API call for '{filename}' (attempt {attempt}/{max_retries}) due to: {brief_err}")
                    time.sleep(5)
                else:
                    print(f"   ❌ API Error generating '{filename}': {brief_err}")
                    raise
        except Exception as e:
            brief_err = format_error_brief(e)
            log_api_event("VOICE_TTS", "ERROR", {"filename": filename, "attempt": attempt, "error": brief_err})
            if attempt < max_retries:
                print(f"   ⚠️ Retrying generation for '{filename}' (attempt {attempt}/{max_retries}) due to: {brief_err}")
                time.sleep(5)
            else:
                print(f"   ❌ Error generating '{filename}': {brief_err}")
                raise

    return False


def generate_audio_batch_gemini(client, batch_items, output_dir, model_name, voice_name="Puck", batch_style="", max_retries=3, api_engine=DEFAULT_API_ENGINE, allow_fallback=True):
    """
    Generates high-energy announcer voice audio for a batch of clips in a single Gemini TTS API request,
    then uses pydub.silence.split_on_silence to slice the generated audio into individual WAV files.
    Supports Google Interactions API (June 2026 standard) and legacy generateContent API with automatic fallback.

    batch_items: list of dicts [{'filename': fname, 'text': text, 'style': style}]
    Returns: bool (True if batch succeeded and all files sliced cleanly, False if fallback is required)
    """
    if not batch_items:
        return True

    from google.genai import types
    from google.genai.errors import APIError

    try:
        from pydub import AudioSegment
        from pydub.silence import split_on_silence
    except ImportError:
        print("   ⚠️ pydub library missing or missing audioop. Falling back to 1:1 TTS generation.")
        return False

    pause_delimiter = " <short pause> <short pause> "
    combined_text = pause_delimiter.join(clean_spoken_text(item['text'], allow_vocal_tags=True) for item in batch_items)
    batch_filenames = [item['filename'] for item in batch_items]
    part = build_speech_part(combined_text, voice_name=voice_name, style=batch_style)

    temp_batch_path = os.path.join(output_dir, "_temp_batch_output.wav")

    for attempt in range(1, max_retries + 1):
        log_api_event("VOICE_TTS_BATCH", "REQUEST", {
            "count": len(batch_items),
            "filenames": batch_filenames,
            "model": model_name,
            "voice": voice_name,
            "style": batch_style,
            "attempt": attempt,
            "engine": api_engine
        })
        try:
            audio_data = None
            mime_type = "audio/wav"

            if api_engine == API_ENGINE_INTERACTIONS:
                try:
                    interaction = client.interactions.create(
                        model=model_name,
                        input=combined_text,
                        response_format={"type": "audio"},
                        generation_config={"speech_config": [{"voice": voice_name}]}
                    )
                    audio_data, mime_type = extract_audio_bytes_from_interaction(interaction)
                except Exception as int_err:
                    if allow_fallback and not ("429" in str(int_err) or "RESOURCE_EXHAUSTED" in str(int_err)):
                        log_api_event("VOICE_TTS_BATCH", "FALLBACK_TO_GENERATE_CONTENT", {"error": format_error_brief(int_err)})
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[part],
                            config=types.GenerateContentConfig(
                                response_modalities=["AUDIO"],
                                speech_config=types.SpeechConfig(
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                                    )
                                )
                            )
                        )
                        if response and getattr(response, "candidates", None):
                            candidate = response.candidates[0]
                            if candidate and getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                                for p in candidate.content.parts:
                                    if hasattr(p, "inline_data") and p.inline_data:
                                        audio_data = p.inline_data.data
                                        mime_type = getattr(p.inline_data, "mime_type", "audio/wav")
                                        break
                    else:
                        raise
            else:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[part],
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                            )
                        )
                    )
                )
                if response and getattr(response, "candidates", None):
                    candidate = response.candidates[0]
                    if candidate and getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                        for p in candidate.content.parts:
                            if hasattr(p, "inline_data") and p.inline_data:
                                audio_data = p.inline_data.data
                                mime_type = getattr(p.inline_data, "mime_type", "audio/wav")
                                break

            if audio_data:
                save_audio_bytes(audio_data, mime_type, temp_batch_path)
                log_api_event("VOICE_TTS_BATCH", "SUCCESS", {
                    "count": len(batch_items),
                    "bytes": len(audio_data)
                })

                try:
                    full_audio = AudioSegment.from_file(temp_batch_path)
                    dBFS = full_audio.dBFS
                    silence_threshold = (dBFS - 16) if dBFS != float("-inf") else -40

                    chunks = split_on_silence(
                        full_audio,
                        min_silence_len=600,
                        silence_thresh=silence_threshold,
                        keep_silence=200
                    )

                    if len(chunks) == len(batch_items):
                        for idx, item in enumerate(batch_items):
                            out_p = os.path.join(output_dir, item['filename'])
                            chunks[idx].export(out_p, format="wav")
                            print(f"   ✅ Gemini Voice Saved (Batched Slice {idx+1}/{len(batch_items)}): {out_p}")

                        if os.path.exists(temp_batch_path):
                            os.remove(temp_batch_path)
                        time.sleep(6)
                        return True
                    else:
                        print(f"   ⚠️ Batch audio slicing produced {len(chunks)} audio segments for {len(batch_items)} items.")
                        print(f"      Triggering fallback to individual 1:1 TTS generation for this batch.")
                        if os.path.exists(temp_batch_path):
                            os.remove(temp_batch_path)
                        return False
                except Exception as slice_err:
                    print(f"   ⚠️ Error slicing batch audio: {slice_err}. Triggering fallback to 1:1 TTS generation.")
                    if os.path.exists(temp_batch_path):
                        os.remove(temp_batch_path)
                    return False
            else:
                finish_reason = "UNKNOWN"
                if response and getattr(response, "candidates", None) and response.candidates:
                    finish_reason = getattr(response.candidates[0], "finish_reason", "UNKNOWN")
                raise RuntimeError(f"No audio data returned by Gemini API for batch (finish_reason: {finish_reason})")

        except APIError as e:
            brief_err = format_error_brief(e)
            log_api_event("VOICE_TTS_BATCH", "API_ERROR", {"attempt": attempt, "error": brief_err})
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_sec = extract_retry_delay_seconds(e, default_delay=60.0)
                dur_fmt = format_duration_human(wait_sec)
                print(f"   ⏳ Rate limit hit (429) during batch TTS. Waiting {dur_fmt} ({wait_sec:.1f}s) for API quota reset...")
                time.sleep(wait_sec)
            else:
                if attempt < max_retries:
                    print(f"   ⚠️ Retrying batch API call (attempt {attempt}/{max_retries}) due to: {brief_err}")
                    time.sleep(5)
                else:
                    print(f"   ❌ Batch TTS Error: {brief_err}. Falling back to 1:1 generation.")
                    return False
        except Exception as e:
            brief_err = format_error_brief(e)
            log_api_event("VOICE_TTS_BATCH", "ERROR", {"attempt": attempt, "error": brief_err})
            if attempt < max_retries:
                print(f"   ⚠️ Retrying batch generation (attempt {attempt}/{max_retries}) due to: {brief_err}")
                time.sleep(5)
            else:
                print(f"   ❌ Batch TTS Error: {brief_err}. Falling back to 1:1 generation.")
                return False

    return False


def generate_music_clip_lyria(client, prompt, filename, music_dir, model_name, duration_sec=30, force=False, max_retries=3, api_engine=DEFAULT_API_ENGINE, allow_fallback=True, use_vertex=False):
    """
    Generates background music track exclusively using Google Lyria AI music models.
    Supports both Google Interactions API (client.interactions.create, June 2026 standard)
    and legacy generateContent API (client.models.generate_content) with automatic fallback.
    Strictly uses the selected Lyria model without model substitution.
    """
    out_path = os.path.join(music_dir, filename)
    duration_sec = min(duration_sec, 120)

    if not force and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"   ⏩ Skipping existing music track: {out_path}")
        return True

    avail = get_model_availability(model_name)
    if use_vertex and not avail.get("vertex_ai", True):
        print(f"🎵 Generating 30s loopable background music track using Google Lyria model '{model_name}'...")
        print(f"   Prompt: '{prompt}'")
        print(f"   ⚠️ Lyria Music notice: Model '{model_name}' is not available on Google Cloud Vertex AI (exclusive to Google AI Studio).")
        vtx_alts = get_available_models_for_role("music_generator", platform="vertex_ai")
        alts_str = ", ".join([f"--music-model {m}" for m in vtx_alts]) if vtx_alts else "--music-model lyria-3-clip-preview, lyria-3-pro-preview, or lyria-002"
        print(f"      Tip: To generate music on Vertex AI, specify an available Vertex Model Garden model (e.g. {alts_str}), or omit --vertexai to auto-route to Google AI Studio.")
        print(f"      Continuing show generation without auto-generated music. You can place an audio file at '{out_path}'.")
        return False
    elif not use_vertex and not avail.get("ai_studio", True):
        print(f"🎵 Generating 30s loopable background music track using Google Lyria model '{model_name}'...")
        print(f"   Prompt: '{prompt}'")
        print(f"   ⚠️ Lyria Music notice: Model '{model_name}' is not available on Google AI Studio (exclusive to Vertex AI Model Garden).")
        ais_alts = get_available_models_for_role("music_generator", platform="ai_studio")
        alts_str = ", ".join([f"--music-model {m}" for m in ais_alts]) if ais_alts else "--music-model lyria-3.5"
        print(f"      Tip: To generate music on Google AI Studio, specify an available model (e.g. {alts_str}), or pass --vertexai.")
        print(f"      Continuing show generation without auto-generated music. You can place an audio file at '{out_path}'.")
        return False

    engine_label = "Interactions API" if api_engine == API_ENGINE_INTERACTIONS else "generateContent API"
    print(f"🎵 Generating 30s loopable background music track using Google Lyria model '{model_name}' [{engine_label}]...")
    print(f"   Prompt: '{prompt}'")

    from google.genai import types
    from google.genai.errors import APIError

    input_text = (
        f"Instrumental stadium entrance background music track ({duration_sec} seconds, loopable, high-energy, "
        f"strictly NO vocals, NO singing, NO speech, NO lyrics): {prompt}"
    )

    for attempt in range(1, max_retries + 1):
        log_api_event("LYRIA_MUSIC", "REQUEST", {
            "filename": filename,
            "model": model_name,
            "duration_sec": duration_sec,
            "attempt": attempt,
            "engine": api_engine,
            "prompt": prompt
        })

        if api_engine == API_ENGINE_INTERACTIONS:
            try:
                interaction = client.interactions.create(
                    model=model_name,
                    input=input_text,
                    response_modalities=["audio"]
                )
                audio_data, mime_type = extract_audio_bytes_from_interaction(interaction)

                if audio_data:
                    save_audio_bytes(audio_data, mime_type, out_path)
                    log_api_event("LYRIA_MUSIC", "SUCCESS", {
                        "filename": filename,
                        "model": model_name,
                        "engine": "interactions",
                        "mime_type": mime_type,
                        "bytes": len(audio_data)
                    })
                    print(f"   ✅ Lyria Music Track Saved ({mime_type}) via Interactions API: {out_path}")
                    time.sleep(6)
                    return True
                else:
                    if allow_fallback:
                        print("   ⚠️ Interactions API returned no audio payload. Attempting fallback to legacy generateContent...")
                        return generate_music_clip_lyria(
                            client, prompt, filename, music_dir, model_name,
                            duration_sec=duration_sec, force=force, max_retries=max_retries,
                            api_engine=API_ENGINE_LEGACY, allow_fallback=False, use_vertex=use_vertex
                        )
                    raise RuntimeError(f"No audio data returned by Interactions API for '{filename}'")
            except Exception as e:
                brief_err = format_error_brief(e)
                log_api_event("LYRIA_MUSIC", "INTERACTIONS_ERROR", {"attempt": attempt, "error": brief_err})
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait_sec = extract_retry_delay_seconds(e, default_delay=60.0)
                    dur_fmt = format_duration_human(wait_sec)
                    print(f"   ⏳ Rate limit hit (429). Waiting {dur_fmt} ({wait_sec:.1f}s) for API quota reset (attempt {attempt}/{max_retries})...")
                    time.sleep(wait_sec)
                    continue
                if allow_fallback:
                    print(f"   ⚠️ Interactions API call failed ({brief_err}). Falling back to legacy generateContent API...")
                    return generate_music_clip_lyria(
                        client, prompt, filename, music_dir, model_name,
                        duration_sec=duration_sec, force=force, max_retries=max_retries,
                        api_engine=API_ENGINE_LEGACY, allow_fallback=False, use_vertex=use_vertex
                    )
                if any(kw in str(e).upper() for kw in ["404", "NOT_FOUND", "PERMISSION_DENIED", "SERVICE_BLOCKED"]):
                    print(f"   ⚠️ Lyria Music notice: Model '{model_name}' is unavailable on this platform/project ({brief_err}).")
                    if use_vertex and not avail.get("vertex_ai", True):
                        vtx_alts = get_available_models_for_role("music_generator", platform="vertex_ai")
                        alts_str = ", ".join([f"--music-model {m}" for m in vtx_alts]) if vtx_alts else "--music-model lyria-3-clip-preview"
                        print(f"      Tip: '{model_name}' is exclusively available on Google AI Studio. To generate music on Vertex AI, specify a Vertex Model Garden model (e.g. {alts_str}) or run without --vertexai.")
                    elif not use_vertex and not avail.get("ai_studio", True):
                        ais_alts = get_available_models_for_role("music_generator", platform="ai_studio")
                        alts_str = ", ".join([f"--music-model {m}" for m in ais_alts]) if ais_alts else "--music-model lyria-3.5"
                        print(f"      Tip: '{model_name}' is exclusively available on Vertex AI. To generate music on AI Studio, specify an available model (e.g. {alts_str}) or pass --vertexai.")
                    else:
                        print(f"      Continuing show generation without auto-generated music. You can place an audio file at '{out_path}'.")
                    return False
                if attempt < max_retries:
                    print(f"   ⚠️ Retrying API call for music (attempt {attempt}/{max_retries}) due to: {brief_err}")
                    time.sleep(5)
                else:
                    print(f"   ⚠️ Lyria Music synthesis error: {brief_err}. Continuing show generation.")
                    return False
        else:
            # Legacy generateContent API
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=input_text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"]
                    )
                )

                audio_data = None
                mime_type = "audio/mp3"
                if response and getattr(response, "candidates", None):
                    candidate = response.candidates[0]
                    if candidate and getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                        for part in candidate.content.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                audio_data = part.inline_data.data
                                mime_type = getattr(part.inline_data, "mime_type", "audio/mp3")
                                break

                if audio_data:
                    save_audio_bytes(audio_data, mime_type, out_path)
                    log_api_event("LYRIA_MUSIC", "SUCCESS", {
                        "filename": filename,
                        "model": model_name,
                        "engine": "generate_content",
                        "mime_type": mime_type,
                        "bytes": len(audio_data)
                    })
                    print(f"   ✅ Lyria Music Track Saved ({mime_type}) via generateContent: {out_path}")
                    time.sleep(6)
                    return True
                else:
                    finish_reason = "UNKNOWN"
                    if response and getattr(response, "candidates", None) and response.candidates:
                        finish_reason = getattr(response.candidates[0], "finish_reason", "UNKNOWN")
                    raise RuntimeError(f"No audio data returned by Lyria API for '{filename}' (finish_reason: {finish_reason})")

            except APIError as e:
                brief_err = format_error_brief(e)
                log_api_event("LYRIA_MUSIC", "API_ERROR", {"filename": filename, "model": model_name, "attempt": attempt, "error": brief_err})
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait_sec = extract_retry_delay_seconds(e, default_delay=60.0)
                    dur_fmt = format_duration_human(wait_sec)
                    print(f"   ⏳ Rate limit hit (429). Waiting {dur_fmt} ({wait_sec:.1f}s) for API quota reset (attempt {attempt}/{max_retries})...")
                    time.sleep(wait_sec)
                elif any(kw in err_str.upper() for kw in ["404", "NOT_FOUND"]):
                    print(f"   ⚠️ Lyria Music notice: Model '{model_name}' is unavailable on this platform/project ({brief_err}).")
                    if use_vertex and not avail.get("vertex_ai", True):
                        vtx_alts = get_available_models_for_role("music_generator", platform="vertex_ai")
                        alts_str = ", ".join([f"--music-model {m}" for m in vtx_alts]) if vtx_alts else "--music-model lyria-3-clip-preview"
                        print(f"      Tip: '{model_name}' is exclusively available on Google AI Studio. To generate music on Vertex AI, specify a Vertex Model Garden model (e.g. {alts_str}) or run without --vertexai.")
                    elif not use_vertex and not avail.get("ai_studio", True):
                        ais_alts = get_available_models_for_role("music_generator", platform="ai_studio")
                        alts_str = ", ".join([f"--music-model {m}" for m in ais_alts]) if ais_alts else "--music-model lyria-3.5"
                        print(f"      Tip: '{model_name}' is exclusively available on Vertex AI. To generate music on AI Studio, specify an available model (e.g. {alts_str}) or pass --vertexai.")
                    else:
                        print(f"      Continuing show generation without auto-generated music. You can place an audio file at '{out_path}'.")
                    return False
                elif any(kw in err_str.upper() for kw in ["PERMISSION_DENIED", "SERVICE_BLOCKED"]):
                    print(f"   ⚠️ Lyria Music notice: Access denied for model '{model_name}' ({brief_err}).")
                    if use_vertex and not avail.get("vertex_ai", True):
                        vtx_alts = get_available_models_for_role("music_generator", platform="vertex_ai")
                        alts_str = ", ".join([f"--music-model {m}" for m in vtx_alts]) if vtx_alts else "--music-model lyria-3-clip-preview"
                        print(f"      Tip: '{model_name}' is exclusively available on Google AI Studio. To generate music on Vertex AI, specify a Vertex Model Garden model (e.g. {alts_str}) or run without --vertexai.")
                    elif not use_vertex and not avail.get("ai_studio", True):
                        ais_alts = get_available_models_for_role("music_generator", platform="ai_studio")
                        alts_str = ", ".join([f"--music-model {m}" for m in ais_alts]) if ais_alts else "--music-model lyria-3.5"
                        print(f"      Tip: '{model_name}' is exclusively available on Vertex AI. To generate music on AI Studio, specify an available model (e.g. {alts_str}) or pass --vertexai.")
                    else:
                        print(f"      Continuing show generation without auto-generated music. You can place an audio file at '{out_path}'.")
                    return False
                else:
                    if attempt < max_retries:
                        print(f"   ⚠️ Retrying API call for music (attempt {attempt}/{max_retries}) due to: {brief_err}")
                        time.sleep(5)
                    else:
                        print(f"   ⚠️ Lyria Music synthesis error: {brief_err}. Continuing show generation.")
                        return False
            except Exception as e:
                brief_err = format_error_brief(e)
                log_api_event("LYRIA_MUSIC", "ERROR", {"filename": filename, "model": model_name, "attempt": attempt, "error": brief_err})
                if attempt < max_retries:
                    print(f"   ⚠️ Retrying music generation (attempt {attempt}/{max_retries}) due to: {brief_err}")
                    time.sleep(5)
                else:
                    print(f"   ⚠️ Music generation error: {brief_err}. Continuing show generation.")
                    return False

    return False


def main():
    load_dotenv_if_present()
    parser = argparse.ArgumentParser(
        description="Generate sports audio intro clips exclusively using Google Gemini & Lyria AI models."
    )
    parser.add_argument("-r", "--roster-config", default="roster_templates.json", help="Path to roster template config JSON (default: roster_templates.json)")
    parser.add_argument("--output-dir", default="input", help="Directory for generated voice clips")
    parser.add_argument("--music-dir", default="music", help="Directory for generated music clips")
    parser.add_argument("--tts-model", default=None, help=f"Gemini TTS model (default: {DEFAULT_TTS_MODEL} or config models.tts_model)")
    parser.add_argument("--llm-model", default=None, help=f"Gemini LLM model (default: {DEFAULT_LLM_MODEL} or config models.llm_model)")
    parser.add_argument("--music-model", default=None, help=f"Google Lyria model (default: {DEFAULT_MUSIC_MODEL} or config models.music_model)")
    parser.add_argument("--voice", default=None, help=f"Prebuilt Gemini voice persona (default: {DEFAULT_VOICE_PERSONA} or config announcer_persona.voice_name)")
    parser.add_argument("--audio-tags", default=None, help=f"Gemini TTS Audio Tags (default: {DEFAULT_AUDIO_TAGS} or config announcer_persona.audio_tags)")
    parser.add_argument("--theme-context", "--announcer-theme", default=None, help="Optional theme/personality context for script synthesis & voice prompts (e.g. pirate, space commander)")
    parser.add_argument("--regional-accent", "--accent", default=None, help="Optional regional accent guidance for speech delivery and pronunciation (e.g. 'French Canadian', 'Boston')")
    parser.add_argument("--enhance-scripts", choices=["auto", "always", "never"], default=None, help=f"LLM script enhancement mode: auto (only clips without manual phonetic overrides), always, or never (default: {DEFAULT_ENHANCE_MODE} or config enhance_scripts)")
    parser.add_argument("--batch-script", action="store_true", default=None, help="Batch LLM script enhancement requests into a single JSON API call (default: True)")
    parser.add_argument("--no-batch-script", action="store_false", dest="batch_script", help="Disable batched LLM script enhancement and fall back to 1:1 API requests")
    parser.add_argument("--batch-tts", action="store_true", default=None, help="Batch Gemini TTS requests and slice generated audio via pydub (default: True)")
    parser.add_argument("--no-batch-tts", action="store_false", dest="batch_tts", help="Disable batched TTS generation and fall back to 1:1 API requests")
    parser.add_argument("--batch-size", type=int, default=None, help="Maximum number of voice clips per batched TTS request (default: 10)")
    parser.add_argument("--legacy-mode", action="store_true", help="Shortcut to disable all batching and fall back to legacy 1:1 API execution")
    parser.add_argument("--legacy-api", "--use-generate-content", "--legacy-generate-content", action="store_true", default=False, help="Use legacy generateContent API instead of the preferred Interactions API (June 2026 standard)")
    parser.add_argument("--api-engine", choices=["interactions", "generate_content", "auto"], default=None, help="Explicitly choose model API engine: 'interactions' (default) or 'generate_content'")
    platform_group = parser.add_mutually_exclusive_group()
    platform_group.add_argument("--vertexai", action="store_true", default=None, help="Use Google Cloud Vertex AI backend platform instead of Google AI Studio")
    platform_group.add_argument("--aistudio", "--ai-studio", "--no-vertexai", action="store_true", default=None, help="Force Google AI Studio backend platform (overrides GOOGLE_GENAI_USE_VERTEXAI in .env)")
    parser.add_argument("--gcp-project", "--project", default=None, help="Google Cloud Project ID for Vertex AI (default: GOOGLE_CLOUD_PROJECT or GCP_PROJECT env var)")
    parser.add_argument("--gcp-location", "--location", default=None, help="Google Cloud Region for Vertex AI (default: GOOGLE_CLOUD_LOCATION, GCP_LOCATION, or us-central1)")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically accept cost estimate and bypass confirmation prompt")
    parser.add_argument("--force", action="store_true", help="Force regeneration of existing audio clips")
    parser.add_argument("--dry-run", action="store_true", help="Preview generated prompts and cost estimate without calling Google Cloud Gemini APIs")
    parser.add_argument("--skip-music", action="store_true", help="Skip generating background music")
    parser.add_argument("--skip-voice", action="store_true", help="Skip generating voice clips")

    args = parser.parse_args()

    config = load_config(args.roster_config)
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.music_dir, exist_ok=True)

    models_cfg = config.get("models", {})
    persona = config.get("announcer_persona", {})
    music_config = config.get("music", {})

    # Model, Voice, Audio Tags, and Script Enhancement Resolution
    tts_model = args.tts_model or config.get("tts_model") or models_cfg.get("tts_model") or DEFAULT_TTS_MODEL
    llm_model = args.llm_model or config.get("llm_model") or models_cfg.get("llm_model") or DEFAULT_LLM_MODEL
    music_model = args.music_model or config.get("music_model") or models_cfg.get("music_model") or music_config.get("model") or DEFAULT_MUSIC_MODEL
    voice_persona = args.voice or config.get("voice") or persona.get("voice_name") or persona.get("voice") or DEFAULT_VOICE_PERSONA
    global_audio_tags = args.audio_tags or config.get("audio_tags") or persona.get("audio_tags") or persona.get("audio_tag") or DEFAULT_AUDIO_TAGS

    if args.legacy_mode:
        batch_script = False
        batch_tts = False
        batch_size = 1
    else:
        batch_script = args.batch_script if args.batch_script is not None else config.get("batch_script_enhancement", models_cfg.get("batch_script_enhancement", True))
        batch_tts = args.batch_tts if args.batch_tts is not None else config.get("batch_tts", models_cfg.get("batch_tts", True))
        try:
            batch_size = int(args.batch_size or config.get("tts_batch_size", models_cfg.get("tts_batch_size", 10)))
        except (ValueError, TypeError):
            batch_size = 10

    raw_enhance = args.enhance_scripts if args.enhance_scripts is not None else config.get("enhance_scripts", models_cfg.get("enhance_scripts", DEFAULT_ENHANCE_MODE))
    if isinstance(raw_enhance, bool):
        enhance_mode = "always" if raw_enhance else "never"
    else:
        enhance_mode = str(raw_enhance).lower().strip()
        if enhance_mode not in ["auto", "always", "never"]:
            enhance_mode = DEFAULT_ENHANCE_MODE

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

    # Check model lifecycle status and warn if inactive (preview/legacy) or platform-incompatible
    warn_if_inactive_models({
        "tts_voice": tts_model,
        "announcer_script": llm_model,
        "music_generator": music_model
    }, use_vertex=use_vertex)

    prefix = persona.get("prompt_prefix", "")
    player_template = config.get("player_template", "Number {number}, {name}!")
    roster = config.get("roster", [])
    intro_clips = config.get("intro_clips", [])

    # Determine which items get LLM Script Enhancement
    intro_enhancements = []
    for clip in intro_clips:
        has_override = bool(clip.get("phonetic") or clip.get("spoken_text"))
        if enhance_mode == "always" or (enhance_mode == "auto" and not has_override):
            intro_enhancements.append(True)
        else:
            intro_enhancements.append(False)

    roster_enhancements = []
    for p in roster:
        has_override = bool(p.get("phonetic") or p.get("phonetic_number") or p.get("custom_intro") or p.get("pretext"))
        if enhance_mode == "always" or (enhance_mode == "auto" and not has_override):
            roster_enhancements.append(True)
        else:
            roster_enhancements.append(False)

    theme_context = args.theme_context or config.get("theme_context") or persona.get("theme_context") or persona.get("theme") or ""
    regional_accent = args.regional_accent or config.get("regional_accent") or persona.get("regional_accent") or ""
    accent_guidance = config.get("accent_guidance") or persona.get("accent_guidance") or ""

    print("🚀 TeamHypeAI - Sports Audio Generator")
    print(f"   Platform Backend:   {platform_desc}")
    print(f"   API Engine:         {api_engine_desc}")
    print(f"   TTS Model:          {tts_model}")
    print(f"   Script Model:       {llm_model} (mode: {enhance_mode})")
    print(f"   Music AI Model:     {music_model}")
    print(f"   Announcer Voice:    {voice_persona}")
    print(f"   Audio Tags:         {format_audio_tag(global_audio_tags)}")
    if regional_accent:
        print(f"   Regional Accent:    {regional_accent}")
    if theme_context:
        print(f"   Theme Context:      \"{theme_context}\"")
    print(f"   Batching Mode:      LLM Batch={batch_script}, TTS Batch={batch_tts} (batch_size={batch_size})")

    to_generate_prompts = []
    num_voice_to_generate = 0
    num_enhanced_to_generate = 0

    items_to_process = []

    if not args.skip_voice:
        for idx, clip in enumerate(intro_clips):
            fname = clip["filename"]
            p_file = os.path.join(args.output_dir, fname)
            is_missing = args.force or not (os.path.exists(p_file) and os.path.getsize(p_file) > 0)
            if is_missing:
                num_voice_to_generate += 1
                txt = build_intro_clip_announcement(clip)
                raw_clip_tag = format_audio_tag(clip.get("audio_tags") or clip.get("audio_tag")) or format_audio_tag(global_audio_tags)
                clip_tag = format_speech_style(raw_clip_tag, regional_accent=regional_accent, accent_guidance=accent_guidance)
                to_generate_prompts.append(txt)
                needs_enh = intro_enhancements[idx]
                if needs_enh:
                    num_enhanced_to_generate += 1
                items_to_process.append({
                    "filename": fname,
                    "raw_text": txt,
                    "audio_tag": clip_tag,
                    "needs_enhancement": needs_enh
                })

        for idx, p in enumerate(roster):
            fname, txt = build_player_announcement(p, player_template)
            raw_p_tag = format_audio_tag(p.get("audio_tags") or p.get("audio_tag")) or format_audio_tag(global_audio_tags)
            p_tag = format_speech_style(raw_p_tag, regional_accent=regional_accent, accent_guidance=accent_guidance)
            full_p = os.path.join(args.output_dir, fname)
            is_missing = args.force or not (os.path.exists(full_p) and os.path.getsize(full_p) > 0)
            if is_missing:
                num_voice_to_generate += 1
                to_generate_prompts.append(txt)
                needs_enh = roster_enhancements[idx]
                if needs_enh:
                    num_enhanced_to_generate += 1
                items_to_process.append({
                    "filename": fname,
                    "raw_text": txt,
                    "audio_tag": p_tag,
                    "needs_enhancement": needs_enh
                })

    m_file = music_config.get("filename", "itstime.mp3")
    m_path = os.path.join(args.music_dir, m_file)
    generate_music_needed = not args.skip_music and (args.force or not (os.path.exists(m_path) and os.path.getsize(m_path) > 0))

    if not args.force and num_voice_to_generate == 0 and not generate_music_needed and not args.dry_run:
        print("\n" + "=" * 60)
        print("✨ All requested audio input files & music tracks are present.")
        print("   Nothing to generate! (Pass --force to regenerate existing files)")
        print("=" * 60 + "\n")
        return

    m_prompt_text = music_config.get("prompt", "") if generate_music_needed else ""
    m_dur = min(music_config.get("duration_seconds", 30), 120) if generate_music_needed else 0

    print_cost_report(
        num_clips=num_voice_to_generate,
        tts_model=tts_model,
        llm_model=llm_model,
        music_model=music_model,
        num_enhanced_clips=num_enhanced_to_generate,
        generate_music=generate_music_needed,
        prompts=to_generate_prompts,
        music_prompt=m_prompt_text,
        music_duration_sec=m_dur,
        batch_script=batch_script,
        batch_tts=batch_tts,
        batch_size=batch_size,
        platform_desc=platform_desc,
        use_vertex=use_vertex
    )

    if args.dry_run:
        print("🔍 DRY RUN MODE -- Generated Dialogue & Batch Execution Preview:")
        print("\n--- INTRO CLIPS ---")
        for idx, clip in enumerate(intro_clips):
            fname = clip["filename"]
            out_p = os.path.join(args.output_dir, fname)
            is_cached = not args.force and os.path.exists(out_p) and os.path.getsize(out_p) > 0
            cache_tag = " ⏩ [Existing File Cached - Will Skip]" if is_cached else ""
            txt = build_intro_clip_announcement(clip)
            raw_clip_tag = format_audio_tag(clip.get("audio_tags") or clip.get("audio_tag")) or format_audio_tag(global_audio_tags)
            clip_tag = format_speech_style(raw_clip_tag, regional_accent=regional_accent, accent_guidance=accent_guidance)
            enhance_tag = f" 🧠 [LLM Script Enhancement via {llm_model}]" if (intro_enhancements[idx] and not is_cached) else ""
            tag_info = f" [Speech Style: '{clip_tag}']" if clip_tag else ""
            print(f"📁 {fname} -> \"{txt}\"{tag_info}{enhance_tag}{cache_tag}")

        print("\n--- ROSTER CLIPS ---")
        for idx, p in enumerate(roster):
            fname, txt = build_player_announcement(p, player_template)
            raw_p_tag = format_audio_tag(p.get("audio_tags") or p.get("audio_tag")) or format_audio_tag(global_audio_tags)
            p_tag = format_speech_style(raw_p_tag, regional_accent=regional_accent, accent_guidance=accent_guidance)
            out_p = os.path.join(args.output_dir, fname)
            is_cached = not args.force and os.path.exists(out_p) and os.path.getsize(out_p) > 0
            cache_tag = " ⏩ [Existing File Cached - Will Skip]" if is_cached else ""
            enhance_tag = f" 🧠 [LLM Script Enhancement via {llm_model}]" if (roster_enhancements[idx] and not is_cached) else ""
            tag_info = f" [Speech Style: '{p_tag}']" if p_tag else ""
            print(f"📁 {fname} -> \"{txt}\"{tag_info}{enhance_tag}{cache_tag}")

        if not args.skip_music:
            m_cached = not args.force and os.path.exists(m_path) and os.path.getsize(m_path) > 0
            m_cache_tag = " ⏩ [Existing File Cached - Will Skip]" if m_cached else ""
            print("\n--- BACKGROUND MUSIC ---")
            print(f"📁 {music_config.get('filename', 'itstime.mp3')} -> Prompt: \"{music_config.get('prompt')}\"{m_cache_tag}")

        print("\n✨ Dry run complete. Set GEMINI_API_KEY and run without --dry-run to generate AI audio files via Google Gemini.")
        return

    # User Confirmation Prompt for Cost Acceptance
    if not args.yes and sys.stdin.isatty():
        try:
            confirm = input("⚠️  Do you accept the estimated API charges and wish to proceed with generation? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("🛑 Audio generation cancelled by user.")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\n🛑 Audio generation cancelled by user.")
            sys.exit(0)

    client = init_gemini_client(
        api_key=os.environ.get("GEMINI_API_KEY"),
        use_vertex=use_vertex,
        project=gcp_project,
        location=gcp_location
    )

    # 1. Generate Voice Clips via Gemini TTS (with optional LLM Script Enhancement)
    if not args.skip_voice and items_to_process:
        print("\n🎙️  Generating Voice Clips via Google Gemini AI...")

        # Step A: Script Enhancement (Batched vs 1:1 Fallback)
        items_needing_enh = [item for item in items_to_process if item["needs_enhancement"]]

        if items_needing_enh:
            if batch_script:
                print(f"🧠 Batch enhancing {len(items_needing_enh)} announcer script(s) via {llm_model} (1 API call)...")
                batch_payload = [
                    {
                        "id": item["filename"],
                        "raw_text": item["raw_text"],
                        "audio_tag": item.get("audio_tag", "")
                    }
                    for item in items_needing_enh
                ]
                enhanced_map = batch_enhance_announcer_scripts(
                    client, batch_payload, llm_model,
                    persona_style=persona.get("style", "High-energy stadium PA announcer"),
                    theme_context=theme_context,
                    delivery_instructions=prefix,
                    regional_accent=regional_accent,
                    accent_guidance=accent_guidance,
                    api_engine=api_engine
                )

                if enhanced_map and isinstance(enhanced_map, dict):
                    for item in items_to_process:
                        if item["filename"] in enhanced_map:
                            item["final_text"] = clean_spoken_text(enhanced_map[item["filename"]], allow_vocal_tags=True)
                        else:
                            item["final_text"] = clean_spoken_text(item["raw_text"], allow_vocal_tags=True)
                else:
                    # Fall back to 1:1 LLM enhancement
                    print("   🧠 Executing 1:1 LLM enhancement fallback per item...")
                    for item in items_to_process:
                        if item["needs_enhancement"]:
                            enhanced = enhance_announcer_script(
                                client, item["raw_text"], llm_model,
                                persona_style=persona.get("style", "High-energy stadium PA announcer"),
                                theme_context=theme_context,
                                delivery_instructions=prefix,
                                audio_tag=item.get("audio_tag", ""),
                                regional_accent=regional_accent,
                                accent_guidance=accent_guidance,
                                api_engine=api_engine
                            )
                            item["final_text"] = clean_spoken_text(enhanced, allow_vocal_tags=True)
                        else:
                            item["final_text"] = clean_spoken_text(item["raw_text"], allow_vocal_tags=True)
            else:
                for item in items_to_process:
                    if item["needs_enhancement"]:
                        print(f"🧠 Enhancing announcer script for '{item['filename']}' via {llm_model}...")
                        enhanced = enhance_announcer_script(
                            client, item["raw_text"], llm_model,
                            persona_style=persona.get("style", "High-energy stadium PA announcer"),
                            theme_context=theme_context,
                            delivery_instructions=prefix,
                            audio_tag=item.get("audio_tag", ""),
                            regional_accent=regional_accent,
                            accent_guidance=accent_guidance,
                            api_engine=api_engine
                        )
                        item["final_text"] = clean_spoken_text(enhanced, allow_vocal_tags=True)
                    else:
                        item["final_text"] = clean_spoken_text(item["raw_text"], allow_vocal_tags=True)
        else:
            for item in items_to_process:
                item["final_text"] = clean_spoken_text(item["raw_text"], allow_vocal_tags=True)

        # Step B: TTS Audio Generation (Batched Slicing vs 1:1 Fallback)
        raw_default_style = format_audio_tag(persona.get("audio_tags") or global_audio_tags)
        default_style = format_speech_style(raw_default_style, regional_accent=regional_accent, accent_guidance=accent_guidance)
        if batch_tts:
            print(f"🔊 Generating {len(items_to_process)} voice clip(s) using batched TTS requests (batch size: {batch_size})...")
            # Chunk items into batches
            chunks = [items_to_process[i:i + batch_size] for i in range(0, len(items_to_process), batch_size)]
            for chunk_idx, chunk in enumerate(chunks, start=1):
                print(f"   🎙️ Processing TTS Batch {chunk_idx}/{len(chunks)} ({len(chunk)} clip(s))...")
                batch_payload = [{"filename": item["filename"], "text": item["final_text"], "style": item.get("audio_tag", default_style)} for item in chunk]
                success = generate_audio_batch_gemini(client, batch_payload, args.output_dir, tts_model, voice_persona, batch_style=default_style, api_engine=api_engine)

                if not success:
                    print(f"   ⚠️ Falling back to 1:1 TTS generation for Batch {chunk_idx} items...")
                    for item in chunk:
                        generate_audio_clip_gemini(client, item["final_text"], item["filename"], args.output_dir, tts_model, voice_persona, style=item.get("audio_tag", default_style), force=args.force, api_engine=api_engine)
        else:
            print(f"🔊 Generating {len(items_to_process)} voice clip(s) using 1:1 TTS API requests...")
            for item in items_to_process:
                generate_audio_clip_gemini(client, item["final_text"], item["filename"], args.output_dir, tts_model, voice_persona, style=item.get("audio_tag", default_style), force=args.force, api_engine=api_engine)

    # 2. Generate Music Clip via Google Lyria Model
    if not args.skip_music:
        print("\n🎵 Generating Royalty-Free Background Music via Google Lyria AI...")
        m_prompt = music_config.get("prompt", "30-second loopable high-energy arena rock music")
        m_dur = min(music_config.get("duration_seconds", 30), 120)
        generate_music_clip_lyria(client, m_prompt, m_file, args.music_dir, music_model, duration_sec=m_dur, force=args.force, api_engine=api_engine, use_vertex=use_vertex)

    print("\n✅ All Gemini AI voice clips and Lyria music track successfully processed!")

if __name__ == "__main__":
    main()

