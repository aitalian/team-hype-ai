# 🚀 TeamHypeAI - Sports Intro & Announcement Audio Assembly

An automated Python tool to create professional, stadium-quality audio introductions and announcements for sports teams. Powered **exclusively by Google Gemini and Lyria AI models**, TeamHypeAI generates exciting PA announcer voice clips, polishes announcer scripts, produces royalty-free stadium entrance music, and mixes them over ducked background music with voice pitch-shifting ("thickening") and precise timing.

---

## 🌟 Features

- **Google Gemini & Lyria AI Audio Stack**: Synthesize rapid-fire stadium announcer voice clips (`gemini-3.1-flash-tts-preview`), AI announcer script polishing (`gemini-3.6-flash`), and entrance music tracks (`lyria-3-clip-preview`, `lyria-3-pro-preview`).
- **High-Efficiency API Request Batching**: Reduces API calls from ~44 down to **2–3 requests per team run** via batched LLM JSON script enhancement and `pydub.silence` audio slicing, preventing Free Tier quota exhaustion (10 RPM / 100 RPD).
- **Multi-Platform AI Backend Support**: Seamlessly switch between **Google AI Studio** (`generativelanguage.googleapis.com`) and **Google Cloud Vertex AI** (`vertexai=True`) using GCP API keys or Application Default Credentials (ADC).
- **Dynamic Rate Limit Retry Delay Parsing**: Automatically extracts exact retry wait durations (e.g. `1h47m9s`) from 429 `RESOURCE_EXHAUSTED` API errors instead of arbitrary sleep times.
- **Rapid-Fire PA Pacing & Duration Control**: Prompt instructions optimized for quick, high-energy PA delivery, keeping 18+ player intros under 2 minutes.
- **Google Gemini Audio Tags Support**: Drive expressive speech delivery using Gemini TTS bracketed audio tags (e.g. `[excitedly]`, `[shouting]`, `[excitedly, very fast]`). Configure tags globally or as per-player / per-clip overrides.
- **Custom Player Intros & Template Variables**: Custom player intro overrides (`custom_intro`) supporting template placeholders (`{name}`, `{number}`, `{phonetic}`, `{phonetic_number}`) for star players or unique announcements.
- **Detailed API Execution Logging**: Timestamped API execution log (`logs/api_execution.log`) tracking prompts, candidate details, finish reasons, token counts, and error tracebacks with API key redaction.
- **Interactive First-Time Setup Wizard (`setup_wizard.py`)**: Batteries-included terminal wizard stepping first-time users through team names, announcer personas, models, intro clips, player rosters, and Vertex AI options.
- **Voice Audition Generator (`generate_voice_samples.py`)**: Synthesizes sample clips for all prebuilt Gemini voice personas (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`) in `samples/` for easy voice auditioning.
- **DRY Roster Management & `$ROSTER` Macro**: Maintain team rosters, voice personas, and prompts in `roster_templates.json`. Expand rosters dynamically in sequence files using the `$ROSTER` macro.
- **Drop-in Custom Audio Support**: Seamlessly mix custom music tracks, custom goal horns, or pre-recorded voice clips by placing files with matching filenames in `input/` or `music/`.
- **Smart File Caching & Missing-Only Cost Estimates**: Automatically skips existing files and calculates cost estimates ONLY for expected API calls to be made.
- **Dynamic Ducking & Voice Thickening**: Automatically lowers background music volume when voice announcements play and applies stadium pitch-shifting ("thickening") to voices.
- **Ultra-Low Cost**: Generates a complete 18-player team intro for **less than $0.08 USD** using Google Gemini AI models.

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Installation

- **Python 3.8+**
- **FFmpeg** (for audio encoding/decoding):
  - **macOS**: `brew install ffmpeg`
  - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

Clone the repository and set up a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
pip3 install -r requirements.txt
```

### 2. Fast-Track Interactive Setup (Recommended for First-Time Users)
Run the interactive setup wizard to generate team-specific roster and run-of-show sequence files automatically (e.g. `roster_templates_eagles.json` and `run_of_show_eagles.json`):
```bash
python3 setup_wizard.py
```

### 3. Audition Announcer Voices (Optional)
Generate sample audio clips for all Gemini voice personas (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`) in `samples/`:
```bash
# Preview sample prompts and estimated API cost (~$0.01 USD):
python3 generate_voice_samples.py --dry-run

# Generate voice sample files in samples/:
python3 generate_voice_samples.py
```

### 4. Step 1: Generate AI Audio & Music Assets
Generate voice clips in `input/` and background music in `music/`:

```bash
# Preview prompts and estimated API generation costs without making API calls:
python3 generate_gemini_audio.py --dry-run

# Generate AI audio files via Google Gemini & Lyria APIs:
python3 generate_gemini_audio.py
```

### 5. Step 2: Assemble the Final Audio Mix
Mix voice clips, sound effects, and background music into the final MP3 track:

```bash
python3 assemble_show.py -c run_of_show.json
```

The final output file will be saved in `output/intro_assembled_output.mp3` (or the `output_filename` defined in your `run_of_show.json` template).

---

## 🎙️ Prebuilt Announcer Voice Personas

Prebuilt Gemini announcer voice definitions are managed centrally in `config/gemini_voices.json`. Official Gemini Text-to-Speech (TTS) documentation and voice specifications are published by Google at:
- 🔗 **Google AI Speech Generation Documentation**: [https://ai.google.dev/gemini-api/docs/speech-generation](https://ai.google.dev/gemini-api/docs/speech-generation)
- 🔗 **Google Cloud Text-to-Speech (Gemini-TTS) Documentation**: [https://docs.cloud.google.com/text-to-speech/docs/gemini-tts](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts)

Common choices are: `Puck` (default), `Charon`, `Kore`, `Fenrir`, and `Aoede`.

---

## 🎧 Drop-in Custom Audio Clips & Hybrid Workflows

You have complete control over which audio assets are generated by AI vs. provided manually.

### How Custom Drop-in Audio Works:
The `generate_gemini_audio.py` script inspects both `input/` and `music/` for existing audio files before making any API requests:
1. **Custom Music**: Place your custom background music file in `music/background_music.mp3`. The generator detects the file, skips Lyria music generation, and uses your track for assembly.
2. **Custom Voice / Sound Effects**: Place custom pre-recorded audio or goal horn SFX (e.g. `sfx_eagle_sound.wav` or `#30 Dakota Harris.wav`) in `input/`. The generator skips those clips and preserves your custom files.
3. **Hybrid AI + Custom Roster**: Mix custom pre-recorded star player clips with Gemini AI-generated team announcements seamlessly.

---

## 📋 DRY Roster Configuration (`roster_templates.json`)

Maintain team rosters, announcer voice styles, music prompts, and model choices in `roster_templates.json`.

### 🤖 Model & Script Enhancement Settings (`models` block)
Configure default AI models and script enhancement behavior directly in JSON:
- `tts_model`: Text-to-Speech voice model (`gemini-3.1-flash-tts-preview`, `gemini-3.5-flash`).
- `llm_model`: Script synthesizer model (`gemini-3.6-flash`, `gemini-3.5-flash-lite`).
- `music_model`: Background music model (`lyria-3-clip-preview`, `lyria-3-pro-preview`).
- `enhance_scripts`: Controls LLM announcer script polishing (`"auto"`, `"always"`, or `"never"`):
  - **`"auto"` (Default)**: Automatically invokes `llm_model` (`gemini-3.6-flash`) ONLY for clips/players that do **not** have manual `phonetic` or `phonetic_number` overrides.
  - **`"always"`**: Forces LLM script enhancement across all items.
- `batch_script_enhancement`: Batches script enhancement requests into a single JSON API call (`true` by default).
- `batch_tts`: Batches TTS requests and slices audio via `pydub.silence` (`true` by default).
- `tts_batch_size`: Maximum voice clips per batched TTS request (`10` by default).
- `use_vertexai`: Optional boolean flag to route requests to Google Cloud Vertex AI infrastructure.

### 🗣️ Optional Phonetic & Timing Overrides
Add optional keys to any player entry in `roster_templates.json` to customize pronunciation or fine-tune audio properties on a per-player basis:
- **Custom Intro Overrides**: `"custom_intro": "Wearing number 15, the one, the only, {name}!"` or `"custom_intro": "Wearing number fifteen,"` (overrides default `player_template` for individual players, supports `{number}` and `{name}` variables).
- **Phonetic Name**: `"name": "Lochlane Thompson"`, `"phonetic": "Lock-lin Tom-sun"`
- **Phonetic Jersey**: `"number": "67"`, `"phonetic_number": "Six. Sev-uhn."`
- **Per-Player Timing & Effects**: Optionally specify `"pre_delay_ms"`, `"post_delay_ms"`, `"ducking"`, or `"thicken"` to fine-tune spacing and ducking for individual players (falls back to sequence defaults if omitted).

```json
{
  "models": {
    "tts_model": "gemini-3.1-flash-tts-preview",
    "llm_model": "gemini-3.6-flash",
    "music_model": "lyria-3-clip-preview",
    "enhance_scripts": "auto",
    "batch_script_enhancement": true,
    "batch_tts": true,
    "tts_batch_size": 10,
    "use_vertexai": false
  },
  "announcer_persona": {
    "style": "High-energy championship arena PA announcer",
    "voice_name": "Puck",
    "audio_tags": "[excitedly, fast-paced]",
    "prompt_prefix": "Say rapidly with intense, fast-paced stadium PA announcer energy, quick delivery, and high enthusiasm: "
  },
  "player_template": "Number {number}, {name}!",
  "roster": [
    { "number": "7", "name": "Alex Smith" },
    { "number": "87", "name": "Reese Martin", "custom_intro": "Wearing number {number}, the one, the only, {name}!" },
    { "number": "14", "name": "Lochlane Thompson", "phonetic": "Lock-lin Tom-sun" },
    { "number": "67", "name": "Peyton Garcia", "phonetic_number": "Six. Sev-uhn." },
    { "number": "98", "name": "Drew Clark", "custom_intro": "Your Team Captain, wearing number {number}, Mr. {name}!", "audio_tags": "[shouting, hype]" }
  ],
  "intro_clips": [
    { "filename": "It's Time.wav", "text": "It's time!", "audio_tags": "[excitedly]" },
    { "filename": "For Your EAAAAGLES.wav", "text": "For your Eagles!", "audio_tags": "[excitedly, very fast]" },
    { "filename": "LETS GO EAGLES.wav", "text": "Let's go Eagles!", "audio_tags": "[shouting, hype]" }
  ],
  "music": {
    "filename": "itstime.mp3",
    "prompt": "Seamless 30-second loopable high-energy driving arena rock hockey stadium entrance music with heavy drums, driving bass, and electric guitars. Ocassionally a loud crash or siren/horn will sound in the background.",
    "duration_seconds": 30,
    "max_duration_seconds": 120,
    "loopable": true
  }
}
```

---

## 🎛️ Run of Show Sequence (`run_of_show.json`)

The Run of Show JSON defines event sequencing and timing using the **`$ROSTER`** macro to keep configurations DRY:

```json
{
  "settings": {
    "music_folder": "music",
    "music_file": "background_music.mp3",
    "music_volume_db": -6,
    "input_folder": "input",
    "output_folder": "output",
    "output_filename": "intro_assembled_output.mp3",
    "roster_config": "roster_templates.json",
    "normalize_output": true,
    "default_ducking_vol_db": -8,
    "normalize_voice_clips": true,
    "default_voice_boost_db": 5
  },
  "sequence": [
    { "file": "It's Time.wav", "ducking": false, "pre_delay_ms": 2000, "post_delay_ms": 500 },
    { "file": "Make Some Noise.wav", "ducking": false, "pre_delay_ms": 0, "post_delay_ms": 0, "thicken": true },
    { "file": "For Your EAAAAGLES.wav", "ducking": false, "pre_delay_ms": 0, "post_delay_ms": 0 },
    { "file": "sfx_eagle_sound.wav", "ducking": false, "pre_delay_ms": 0, "post_delay_ms": 750, "voice_boost_db": -2 },
    { "file": "Hitting the Ice.wav", "ducking": true, "pre_delay_ms": 1500, "post_delay_ms": 100, "thicken": true },
    { "file": "$ROSTER", "ducking": true, "pre_delay_ms": 0, "post_delay_ms": 1400, "thicken": false },
    { "file": "LETS GO EAGLES.wav", "ducking": false, "pre_delay_ms": 0, "post_delay_ms": 500, "thicken": true }
  ]
}
```

---

## 🛠️ CLI Reference Guide

### 1. `setup_wizard.py`
Interactive step-by-step onboarding wizard for generating team configurations:
```text
Usage: python3 setup_wizard.py
```

### 2. `generate_voice_samples.py`
Audition sample audio generator for prebuilt Gemini voices:
```text
  -o, --output-dir DIR  Directory for voice samples (default: samples)
  --sample-text TEXT    Sample announcement text
  --tts-model MODEL     Gemini TTS model (default: gemini-3.1-flash-tts-preview)
  --llm-model MODEL     Gemini LLM model (default: gemini-3.6-flash)
  --voices VOICES       Comma-separated list of voices (default: Puck,Charon,Kore,Fenrir,Aoede)
  --enhance-scripts MODE
                        LLM script enhancement mode: auto, always, or never (default: auto)
  --vertexai            Use Google Cloud Vertex AI platform instead of Google AI Studio
  --gcp-project PROJECT Google Cloud Project ID for Vertex AI
  --gcp-location REGION Google Cloud Region for Vertex AI (default: us-central1)
  -y, --yes             Automatically accept cost estimate & bypass confirmation prompt
  --force               Force regeneration of existing sample files
  --dry-run             Preview generated prompts & cost estimate
```

### 3. `generate_gemini_audio.py`
Generates voice clips and entrance music via Gemini & Lyria APIs:
```text
  -r, --roster-config CONFIG
                        Path to roster template config JSON (default: roster_templates.json)
  --output-dir DIR      Directory for generated voice clips (default: input)
  --music-dir DIR       Directory for generated music clips (default: music)
  --tts-model MODEL     Gemini TTS model (default: gemini-3.1-flash-tts-preview)
  --llm-model MODEL     Gemini LLM model (default: gemini-3.6-flash)
  --music-model MODEL   Lyria Music model (default: lyria-3-clip-preview)
  --voice VOICE         Prebuilt voice persona (Puck, Charon, Kore, Fenrir, Aoede)
  --enhance-scripts MODE
                        LLM script enhancement mode: auto, always, or never (default: auto)
  --batch-script / --no-batch-script
                        Toggle batched LLM script enhancement (default: True)
  --batch-tts / --no-batch-tts
                        Toggle batched Gemini TTS generation (default: True)
  --batch-size N        Maximum voice clips per batched TTS request (default: 10)
  --legacy-mode         Shortcut to disable all batching and fall back to 1:1 API calls
  --vertexai            Use Google Cloud Vertex AI platform instead of Google AI Studio
  --gcp-project PROJECT Google Cloud Project ID for Vertex AI
  --gcp-location REGION Google Cloud Region for Vertex AI (default: us-central1)
  -y, --yes             Automatically accept cost estimate & bypass confirmation prompt
  --force               Force regeneration of existing audio files
  --dry-run             Preview generated text prompts & cost estimate
  --skip-music          Skip generating background music track
  --skip-voice          Skip generating voice clips
```

### 4. `assemble_show.py`
Mixes voice clips, sound effects, and music with dynamic ducking into the final output:
```text
  -c, --config CONFIG   Path to Run of Show JSON config (default: run_of_show.json)
  -r, --roster-config CONFIG
                        Path to roster template config JSON (overrides roster_config in run_of_show settings)
  -f, --force           Force re-assembly even if target output file exists
```

### 5. `update_cost_rates.py`
Automatically fetches pricing from official Google documentation URLs and updates `config/cost_rates.json`:
```text
  -c, --config CONFIG   Path to cost_rates.json (default: config/cost_rates.json)
  --dry-run             Preview pricing matrix updates without modifying config file
```

---

## 🔍 Debugging & API Execution Logging

TeamHypeAI automatically records structured, timestamped execution logs in `logs/api_execution.log` to simplify debugging and API response correlation:

- **Comprehensive Request & Response Tracking**: Logs text prompts, model parameters, candidate response counts, `finish_reason` status codes (e.g. `STOP`, `SAFETY`, `OTHER`), audio payload byte sizes, and full exception tracebacks on retries.
- **Privacy & Security Protection**: Any detected API keys (e.g. `GEMINI_API_KEY`) are automatically sanitized and replaced with `[REDACTED_API_KEY]`.
- **Git Protection**: The `logs/` folder and `*.log` files are configured in `.gitignore` to keep execution logs strictly local to your workspace.

---

## 🤖 Gemini AI Models Comparison & Selection Guide

The project utilizes specific Google Gemini and Lyria AI models tailored for distinct tasks:

| Model | Primary Purpose | Why It Is Used | Pros | Cons / Trade-offs |
| :--- | :--- | :--- | :--- | :--- |
| **`gemini-3.1-flash-tts-preview`** *(Default TTS)* | **Text-to-Speech Voice Clips** | Native TTS synthesis for PA announcer voice clips and player intros with built-in voice personas (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`). | Ultra-low latency, native audio generation, vibrant prebuilt stadium voice personas. | Preview model API surface. |
| **`gemini-3.6-flash`** *(Default LLM)* | **Announcer Prompt & Script Synthesis** | Dynamic prompt expansion, phonetic script formatting, and high-energy announcer inflection reasoning. | Latest Flash model with lower output pricing ($7.50/1M output including thinking vs $9.00/1M for 3.5), superior prompt instruction adherence. | Slightly higher input cost than Flash-Lite ($1.50 vs $0.30/1M). |
| **`gemini-3.5-flash-lite`** *(Alternative LLM)* | **Lightweight Script Formatting** | Cost-optimized script formatting for simple template rendering. | Lowest input/output cost ($0.30 input / $2.50 output per 1M tokens), high throughput. | Less expressive prompt enhancement compared to 3.6 Flash. |
| **`lyria-3-clip-preview`** *(Default Music)* | **Stadium Entrance Music Tracks** | Generates 30-second loopable high-energy arena rock background music tracks tailored for sports intros. | Fast generation, optimized for short loopable background tracks ($0.04/song). | Max 30s clips per generation. |
| **`lyria-3-pro-preview`** *(Pro Music)* | **Production-Grade Entrance Music** | High-fidelity stadium entrance track generation with richer instrumentation. | Premium audio mastering quality and complex instrumentation ($0.08/song). | Double the cost of clip-preview ($0.08/song). |

---

## 💵 Multi-Platform Cost Efficiency & Pricing Matrix

All CLI tools load rate definitions dynamically from `config/cost_rates.json`, taking into account the active platform (**Google AI Studio** vs **Google Cloud Vertex AI**) and API execution mode (**Standard** vs **Batch**).

### 🔄 How to Update Pricing Rates Automatically
You can automatically refresh and validate rate definitions from official Google documentation URLs by running:

```bash
# Preview live pricing rate changes without writing to disk:
python3 update_cost_rates.py --dry-run

# Scrape live rates and update config/cost_rates.json:
python3 update_cost_rates.py
```

The script parses live rates from:
- 🔗 **Google AI Studio Pricing**: [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)
- 🔗 **Google Cloud Vertex AI Generative AI**: [https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing)
- 🔗 **Google Cloud Vertex AI Text-to-Speech**: [https://cloud.google.com/text-to-speech/pricing](https://cloud.google.com/text-to-speech/pricing)

---

### 📊 Full Intro Generation Cost Comparison (Sample 18-Player Team Run)

Below is an estimated cost comparison for generating a complete team intro (23 voice clips, 4 LLM enhanced announcer scripts via `gemini-3.6-flash`, and 1 Lyria entrance music track):

| Execution Platform & Mode | LLM Scripting Rate (`gemini-3.6-flash`) | TTS Voice Rate (`gemini-3.1-flash-tts-preview`) | Music Rate (`lyria-3-clip-preview`) | Sample Total Generation Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Google AI Studio (Standard API)** | $1.50 in / $7.50 out | $0.50 in / $10.00 out | $0.0400 / request | **~$0.0770 USD** |
| **Google AI Studio (Batch API - 50% Off LLM)** | **$0.75 in / $3.75 out** | $0.50 in / $10.00 out | $0.0400 / request | **~$0.0762 USD** |
| **Google Cloud Vertex AI (Standard API)** | $1.50 in / $7.50 out | $1.00 in / $20.00 out | $0.0400 / request | **~$0.0937 USD** |
| **Google Cloud Vertex AI (Batch API - 50% Off LLM)** | **$0.75 in / $3.75 out** | $1.00 in / $20.00 out | $0.0400 / request | **~$0.0929 USD** |

> **\* Audio Token Conversion Rate**: Audio output tokens correspond to **25 tokens per second of generated audio** (~1,500 audio tokens per minute).

> [!IMPORTANT]
> **Platform Quota & Rate Limit Tradeoff**:
> - **Google AI Studio**: Offers lower per-unit token pricing ($0.50 / $10.00 per 1M tokens for TTS), but is subject to strict API tier caps (**10 RPM / 100 RPD** for preview models). Generating back-to-back intros for multiple teams on AI Studio can trigger rate limit quota resets (`429 RESOURCE_EXHAUSTED`).
> - **Google Cloud Vertex AI**: Slightly higher TTS unit token pricing ($1.00 / $20.00 per 1M tokens), but **is not subject to AI Studio's 100 RPD daily quota cap**. Vertex AI is backed by Google Cloud enterprise infrastructure, scaling to thousands of RPM with customizable GCP project quotas for multi-team and high-volume production environments.

---

## 📁 Directory Layout

- `config/`: Dedicated folder for static system configuration JSON files.
  - `config/cost_rates.json`: Model API pricing rate definitions.
  - `config/gemini_voices.json`: Prebuilt Gemini voice persona definitions & descriptions.
- `common.py`: Shared DRY utility module (constants, environment loader, strict JSON readers).
- `setup_wizard.py`: Interactive setup wizard for first-time onboarding and team config generation.
- `generate_voice_samples.py`: Audition sample audio generator for prebuilt Gemini voices.
- `generate_gemini_audio.py`: Generator for AI voice clips and entrance music.
- `assemble_show.py`: Audio stitching and ducking engine.
- `roster_templates.json`: Team roster template & prompt configuration.
- `run_of_show.json`: Run of Show sequence definition using `$ROSTER` macro.
- `samples/`: Audition voice preview audio clips (`Puck.wav`, `Charon.wav`, etc.).
- `logs/`: Timestamped API execution log files (`logs/api_execution.log`, git-ignored).
- `input/`: Voice clips and SFX audio files.
- `music/`: Background music tracks.
- `output/`: Final mixed audio intros.
- `requirements.txt`: Python dependencies (`pydub`, `google-genai`, `audioop-lts` for Python 3.13+).
- `pyproject.toml`: Modern PEP 517/518 packaging configuration.
- `.gitattributes`: Cross-platform git line ending normalization and binary asset rules.
- `.env`: Environment file for storing `GEMINI_API_KEY` (git-ignored).
- `LICENSE`: Project AGPLv3 license and disclaimer terms.

---

## ⚖️ Disclaimer, Terms of Service & License

### Project Disclaimer
This project is **not created, maintained, or endorsed by Google LLC**. It is created and published for **personal use only, on an as-is basis**, without any warranties or guarantees of any kind.

### API Terms of Service & Billing Responsibility
Running this tool and supplying your own API key (`GEMINI_API_KEY`) constitutes your agreement to the applicable [Google Cloud Terms of Service](https://cloud.google.com/terms) and [Google Gemini API Terms of Service](https://ai.google.dev/terms). Users are solely responsible for all API costs, billing, rate limit management, data privacy compliance, and implications generated by their usage of the APIs.

### License
This project is licensed under the **GNU Affero General Public License v3.0 (GNU AGPLv3)**. See the [LICENSE](LICENSE) file or visit https://www.gnu.org/licenses/ for full license terms.
