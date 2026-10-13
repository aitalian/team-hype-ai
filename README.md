# 🚀 TeamHypeAI - Automated Sports Stadium Audio Announcements

An automated Python pipeline and proof-of-concept suite designed to create stadium-quality audio introductions and announcements for youth sports teams, powered **exclusively by Google Gemini and Lyria AI models**.

TeamHypeAI synthesizes high-energy arena PA voice clips, polishes announcer scripts, generates royalty-free stadium entrance music, and mixes them over ducked background tracks with voice pitch-shifting ("thickening") and precise timing.

---

## 🏒 DevFest Montreal 80s Retro Demo Showcase

This project was built as a live proof-of-concept demo presented at **DevFest Montreal** to showcase the real-world capabilities of Google's latest multimodal and audio models in an engaging, easy-to-follow, and extensible format:

- **1986 Stanley Cup Champions Montreal Canadiens Theme**: The sample roster showcases the legendary 1986 Montreal Canadiens roster (#24 Chris Chelios, #26 Mats Naslund, #19 Larry Robinson, #23 Bob Gainey, and #33 Patrick Roy). It demonstrates regional Francophone pronunciation guides (e.g., *"Pat-REEK RWAH"*, *"Mohn-ray-AL"*) and celebrated Montreal Forum bilingual hockey phrasing (*"Faites du bruit, make some noise!"*, *"Vos Canadiens de Montréal"*).
- **1980s Retro Arena Rock Entrance Music**: Matching the DevFest Montreal 80s retro conference theme, the stadium entrance track is generated with Google Lyria AI using prompts featuring driving analog synthesizers, punchy gated reverb drums, and screaming electric guitar solos.
- **Extensible & Adaptable**: While styled for DevFest Montreal, TeamHypeAI is fully configurable for any local minor hockey team, soccer club, little league baseball squad, or community event.

---

## 🎤 DevFest Montreal Demo & Presentation Slides

This project was showcased at **DevFest Montreal**:

- 📺 **Presentation Slides**: *[Link to DevFest Montreal Slides - Coming Soon]*
- 🏒 **Live Demo Walkthrough / Video**: *[Link to Session Recording / Demo - Coming Soon]*

---

## 🤝 Contributing & Open Source Community

We encourage forks, community collaboration, and open-source contributions!

- 🍴 **Fork & Adapt**: Fork the repository and customize it for your local sports teams, school clubs, or developer conferences.
- 💡 **Open an Issue**: Found a bug or have an idea for a new sport preset or announcer persona? Open a [GitHub Issue](https://github.com/aitalian/team-hype-ai/issues).
- 🚀 **Submit a Pull Request**: Pull requests are welcome! Whether adding support for new audio effects, improving CLI ergonomics, or adding roster templates, please submit a [Pull Request](https://github.com/aitalian/team-hype-ai/pulls).

---

## 🌟 Key Features

- **Google Gemini & Lyria AI Audio Stack**:
  - **Script Synthesis**: `gemini-3.8-flash` enhances raw roster entries into UPPERCASE-emphasized stadium announcements with authentic phonetics and tone cues.
  - **Text-to-Speech Engine**: `gemini-3.8-flash-tts` generates high-energy PA voice clips using prebuilt personas (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`) and native `types.SpeechMetadata`.
  - **Stadium Entrance Music**: `lyria-3.5` synthesizes loopable, pure-instrumental entrance music tracks (strictly NO vocals or lyrics).
- **Google Interactions API Standard**: Native integration with Google's preferred June 2026 **Interactions API** (`client.interactions.create`), with automatic backwards compatibility (`--legacy-api`) and auto-fallback.
- **Dynamic Platform Auto-Routing**: Automatically routes to **Google AI Studio** for AI Studio-exclusive models (like `lyria-3.5`) or **Google Cloud Vertex AI** for enterprise workloads, seamlessly overriding `.env` defaults.
- **Free Tier Quota Optimization**: High-efficiency request batching (batched LLM script enhancement and silence-sliced batched TTS) reduces API requests from ~44 down to **2–3 requests per team run**.
- **Dynamic Rate Limit Parsing**: Automatically parses recommended wait times (e.g. `'retryDelay': '6429s'`) from 429 `RESOURCE_EXHAUSTED` responses to sleep for the exact duration needed.
- **Audio Engineering & DSP**:
  - Voice pitch thickening (0.95x speed-shifted and resampled for stadium resonance).
  - Dynamic background music ducking (drops `-8dB` to `-15dB` during announcements).
  - Peak and clip volume normalization.
- **Drop-in Custom Audio**: Place custom MP3 background tracks in `music/` or pre-recorded clips/horns in `input/` to bypass AI generation for selected items.
- **Arena Hardware Playbook**: Stream assembled audio from your phone/tablet over Bluetooth to the arena PA soundboard aux input.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.8+** (Supports Python 3.13+)
- **FFmpeg** (Required for audio manipulation and MP3 encoding):
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/) and add to system `PATH`.
- **Google Gemini API Key**: Obtain a key from [Google AI Studio](https://aistudio.google.com/).

### 2. Installation
```bash
git clone https://github.com/aitalian/team-hype-ai.git
cd team-hype-ai
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Set your API key:
```bash
export GEMINI_API_KEY="your_api_key_here"
# Or create a local .env file (automatically git-ignored):
echo 'GEMINI_API_KEY="your_api_key_here"' > .env
```

### 3. Fast-Track Interactive Setup
Run the setup wizard to configure your team roster, announcer voice, and music prompt:
```bash
python setup_wizard.py
```

### 4. Step 1: Generate AI Audio & Music Assets
```bash
# Preview generation prompts and cost estimate without making API calls:
python generate_gemini_audio.py --dry-run

# Generate voice clips in input/ and stadium music in music/:
python generate_gemini_audio.py
```

### 5. Step 2: Assemble the Final Audio Mix
```bash
python assemble_show.py -c run_of_show.json
```
Your final stadium-ready audio file will be saved in `output/` (e.g., `output/devfest_montreal_80s_assembled.mp3`).

---

## 🤖 Model Stack & Single Source of Truth References

To adhere to strict **DRY (Don't Repeat Yourself)** principles, all model configurations, rate cards, and voice catalogs are maintained in centralized sources of truth:

| Model | Role | Platform Availability | Details & Documentation |
| :--- | :--- | :--- | :--- |
| **`gemini-3.8-flash`** | Announcer Script Synthesizer | AI Studio & Vertex AI | High-reasoning script polishing and phonetic formatting |
| **`gemini-3.8-flash-tts`** | Text-to-Speech Engine | AI Studio & Vertex AI | Studio-grade stadium speech with structured `speech_metadata` |
| **`lyria-3.5`** | Stadium Music Generator | AI Studio (Exclusive) | High-energy loopable stadium entrance tracks (no vocals) |

### 📌 Single Sources of Truth:
- 📊 **Model Specifications, Availability & Rates**: [`config/cost_rates.json`](file:///Users/aitalian/Sandbox/gitlab/aitalian/devfestmtl26-teamhypeai/config/cost_rates.json)  
  *Audit or update live rates anytime with: `python update_cost_rates.py --check`*
- 🎙️ **Stadium Voice Personas**: [`config/gemini_voices.json`](file:///Users/aitalian/Sandbox/gitlab/aitalian/devfestmtl26-teamhypeai/config/gemini_voices.json)  
  *Curated English high-energy stadium announcers (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`). Audit with: `python update_gemini_voices.py --check`*
- 📖 **Comprehensive Technical Reference**: [`GEMINI.md`](file:///Users/aitalian/Sandbox/gitlab/aitalian/devfestmtl26-teamhypeai/GEMINI.md)  
  *Full technical documentation detailing the Interactions API contract, audio DSP algorithms, regional phonetics, and platform resolution precedence.*

---

## 🎧 Drop-in Custom Audio & Hybrid Workflows

TeamHypeAI allows full flexibility to mix AI-generated audio with custom human-recorded clips or professional tracks:
1. **Custom Music**: Place an audio file at `music/background_music.mp3`. The pipeline automatically skips Lyria generation and mixes your music.
2. **Custom SFX & Goal Horns**: Drop audio files (e.g. `sfx_goal_horn.wav`, `Make Some Noise.wav`) into `input/`. Existing files are preserved and never overwritten unless `--force` is specified.
3. **Hybrid Roster**: Combine AI-generated introductions for player intros with pre-recorded coach clips or team chants.

---

## 🛠️ CLI Utilities Overview

- `python setup_wizard.py`: Interactive onboarding wizard for creating team roster configurations.
- `python generate_gemini_audio.py`: Main audio generator for AI voice clips and Lyria entrance music.
  - `--dry-run`: Preview prompts, clean dialogue, and estimated cost.
  - `--aistudio` / `--vertexai`: Select backend platform (auto-routed dynamically by default).
  - `--regional-accent "French Canadian"`: Inject regional pronunciation guidelines.
  - `--batch-script` / `--batch-tts`: Enable high-efficiency API batching (enabled by default).
  - `--legacy-api`: Opt into legacy `generateContent` API instead of the Interactions API.
- `python assemble_show.py -c run_of_show.json`: Stitches voice clips, sound effects, and music with dynamic ducking.
- `python generate_voice_samples.py`: Generates voice audition clips in `samples/` for prebuilt personas.
- `python update_cost_rates.py --check`: Audits local rate cards against official Google documentation.
- `python update_gemini_voices.py --check`: Audits local announcer voice personas against Google TTS catalog.

---

## 📻 Arena Hardware Setup (Live Playbook)

```text
[ Mobile Device (Phone/Tablet) ]
       │ Bluetooth Audio Stream
       ▼
[ Portable Bluetooth Receiver Unit ]
       │ 3.5mm Stereo Aux Cable
       ▼
[ Arena Soundboard Aux Input / Mixer ]
       │ Arena Amplifiers
       ▼
[ Rink Stadium Speakers ]
```

1. **Bluetooth Receiver**: Plug a portable Bluetooth auxiliary receiver (e.g., Anker, Avantree) into the arena soundboard 3.5mm aux input.
2. **Pair & Test**: Pair your phone or tablet hosting the assembled MP3 from `output/`.
3. **Game-Day Trigger**: Play the track as players take the ice for maximum stadium impact!

---

## ⚖️ License & Disclaimers

### License
This project is licensed under the **GNU Affero General Public License v3.0 (GNU AGPLv3)**. See the [LICENSE](LICENSE) file or visit [https://www.gnu.org/licenses/](https://www.gnu.org/licenses/) for details.

### Disclaimers & API Terms
- This project is **not created, maintained, or endorsed by Google LLC**.
- Running this tool requires a Google Gemini API key or Google Cloud account. Users are solely responsible for all API usage, billing, rate limit adherence, and compliance with the [Google Gemini API Terms of Service](https://ai.google.dev/terms) and [Google Cloud Terms of Service](https://cloud.google.com/terms).
