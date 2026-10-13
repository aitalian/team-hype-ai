# TeamHypeAI - Chronological Milestone & Release Log (LOG.md)

> **📜 Document Role**:
> This document maintains a consolidated, chronological log of completed milestones, releases, and architectural refactors.
> For deep technical specifications and system designs, see [`GEMINI.md`](GEMINI.md).
> For public documentation and quickstart instructions, see [`README.md`](README.md).

---

## [2026-10-12] Comprehensive Utility Documentation, Architecture Diagrams & Tuning Guide
- **Visual Architecture & Pipeline Diagrams**: Embedded Mermaid flowcharts and sequence diagrams in `README.md` illustrating the end-to-end multi-layer pipeline and the audio DSP mixing sequence (ducking envelopes, thickening, pre/post delays, and `$ROSTER` macro expansion).
- **Recommended User Workflow ("Where to Start")**: Delineated an approachable 5-step roadmap prioritizing `setup_wizard.py` as the interactive starting point, followed by voice auditioning, AI asset generation, and show assembly.
- **Exhaustive Utility Scripts Reference**: Documented all 6 CLI utilities (`setup_wizard.py`, `generate_voice_samples.py`, `generate_gemini_audio.py`, `assemble_show.py`, `update_cost_rates.py`, `update_gemini_voices.py`) detailing their purpose, architectural rationale, options, and copy-pasteable command examples.
- **Configuration Fine-Tuning Guide**: Added detailed schema breakdowns and tuning advice for `roster_templates.json` (phonetics, sustained speech styles, player templates, music prompts) and `run_of_show.json` (ducking levels, sequence timing, delays, voice thickening).

---

## [2026-10-12] Gemini 3.8 Flash TTS Speech Style & Nuance Modernization
- **Official Terminology Realignment**: Modernized the legacy term "audio tags" to match official Google Gemini 3.8 Flash TTS documentation: sustained turn-level delivery style & nuance (`speech_metadata.style`) vs point-in-time inline tags (`<short pause>`, `<cheer>`, `<breath>`).
- **Bracket Deprecation & Prosody Optimization**: Replaced legacy square-bracket notation (`[excitedly]`) with clean unbracketed descriptive strings (e.g. `"excitedly, fast-paced"`, `"shouting, hype"`), preventing modern verbatim speech synthesis models from inadvertently vocalizing brackets.
- **Backwards Compatibility**: Preserved `--audio-tags` as a functional CLI alias for `--speech-style` / `--style`, and added fallback compatibility for legacy `audio_tags` JSON configuration keys in `roster_templates.json` and `setup_wizard.py`.
- **Curated Voice Catalog Synchronization**: Updated `config/gemini_voices.json`, `update_gemini_voices.py`, and the `voice-catalog-tracker` skill to reflect `recommended_style` and clean unbracketed style strings.

---

## [2026-10-12] Public Release Preparation & DRY Documentation Refactoring
- **DRY Single-Source-of-Truth Architecture**: Refactored `README.md`, `GEMINI.md`, `PROMPT.md`, `TODO.md`, and `LOG.md` to eliminate redundant catalogs, schemas, and duplicate changelogs, designating clear consumer roles for each document.
- **DevFest Montreal Demo Context**: Highlighted project context in `README.md` as an extensible proof-of-concept demo tailored for DevFest Montreal (1986 Montreal Canadiens Stanley Cup theme with French Canadian pronunciation, and 80s retro arena synth entrance music).
- **Community & Presentation Sections**: Added dedicated sections to `README.md` for open-source contributions (forking, issues, PRs) and a future link placeholder for DevFest Montreal presentation slides and recording.
- **Setup Wizard Implied Defaults**: Enhanced `setup_wizard.py` to inspect existing `roster_templates.json` and `run_of_show.json` files and surface their values as implied defaults across all interactive prompts, falling back to hardcoded defaults only if configuration files are absent.
- **Security & Git Hardening**: Confirmed zero hardcoded API keys or private project numbers; updated `.gitignore` to ignore `.env*` and temporary duplicate files.

---

## [2026-10-12] Single Source of Truth Model Availability & Dynamic Platform Resolution
- **Extended `config/cost_rates.json` (v2.2.0)**: Added structured `availability` metadata (`ai_studio`, `vertex_ai`, `exclusive_to`, `vertex_model_id`, `notes`) across all tracked models.
- **Centralized Resolution Helpers (`common.py`)**: Implemented `get_model_availability()`, `is_model_available_on_platform()`, and `get_available_models_for_role()`.
- **Eliminated Hardcoded Strings**: Removed hardcoded model checks across `common.py`, `generate_gemini_audio.py`, and `update_cost_rates.py`.
- **Dynamic Auto-Routing**: Exclusive models auto-route seamlessly (`lyria-3.5` to AI Studio, `lyria-002` to Vertex AI). Incompatible selections surface upfront tips with available alternatives.

---

## [2026-10-12] Lyria 3.5 AI Studio Auto-Routing & Pure Instrumental Modality
- **All-or-Nothing Auto-Routing to Google AI Studio**: Configured pipeline to default to Google AI Studio whenever `lyria-3.5` is active, bypassing `.env` Vertex AI settings due to platform-exclusive availability on AI Studio.
- **Pure Instrumental Modality**: Enforced `response_modalities=['audio']` paired with negative prompt framing (`strictly NO vocals, NO singing, NO lyrics`) to guarantee pure background music tracks without vocal generation.
- **Strict Model Enforcement**: Eliminated automatic fallback loops (e.g. falling back to `lyria-002`), ensuring strict adherence to user-configured music models.

---

## [2026-10-12] Vertex AI Interactions Compatibility & Sanitized Error Handling
- **Platform-Aware API Resolution**: Automatically resolves API engine to `generate_content` on Google Cloud Vertex AI (where `/interactions` endpoint returns 404) while standardizing on `interactions` on Google AI Studio.
- **Sanitized HTML Error Reporting (`common.py`)**: Added `format_error_brief()` to intercept API exceptions, strip raw HTML error pages, and display clean, human-readable CLI error summaries.
- **Client Isolation**: Updated `init_gemini_client()` to explicitly pass `vertexai=False` when targeting AI Studio, preventing accidental inheritance of environment variables.

---

## [2026-10-12] Google Interactions API Migration (June 2026 Preferred Standard)
- **Interactions API Integration**: Migrated script synthesis (`gemini-3.8-flash`), speech generation (`gemini-3.8-flash-tts`), and stadium music (`lyria-3.5`) to Google's preferred June 2026 Interactions API contract (`client.interactions.create`).
- **Audio Extraction Engine (`common.py`)**: Built `extract_audio_bytes_from_interaction()` supporting `output_audio` base64/bytes decoding, multi-step actions, and MIME-type detection.
- **Backwards Compatibility & Error Fallback**: Added `--legacy-api` / `--api-engine` CLI flags and automated fallback to `client.models.generate_content(...)` upon non-quota API errors.

---

## [2026-10-12] Explicit Google AI Studio Override (`--aistudio`) & Precedence
- **CLI Flag Overrides**: Added `--aistudio` (aliases: `--ai-studio`, `--no-vertexai`) across CLI tools to override local `.env` settings directly from the terminal.
- **Centralized Precedence (`resolve_platform_backend`)**: Established unambiguous resolution order: CLI flags > model availability auto-routing > roster config > environment variables > default fallback.

---

## [2026-10-12] Regional French Canadian Accent & Francophone Pronunciation
- **Speech Metadata Accent Styling**: Added `regional_accent` and `accent_guidance` support, injecting regional pronunciation cues into `types.SpeechMetadata(speaker=voice_name, style=style)` for Gemini 3.8 Flash TTS.
- **Quebec Hockey Cultural Phrasing**: Integrated authentic Quebec bilingual phrasing and phonetics (*"Mohn-ray-AL"*, *"Pat-REEK RWAH"*, *"Le Petit Viking"*, *"Faites du bruit"*, *"GO HABS GO!"*) into Montreal Canadiens demo templates.

---

## [2026-10-12] Gemini 3.8 Flash TTS Architecture Migration & Speech Metadata
- **Gemini 3.8 Flash TTS Integration**: Migrated speech synthesis to `gemini-3.8-flash-tts`, adhering to official Google Gemini 3.8 migration guidelines.
- **Structured Speech Metadata**: Moved sustained delivery instructions (tone, emotion, pacing) into native `types.SpeechMetadata` attached to `types.Part.speech_metadata` (`google-genai>=2.29.0`).
- **Verbatim Dialogue & Point-in-Time Vocal Events**: Restricted inline tags strictly to valid angle brackets (`<short pause>`, `<cheer>`, `<breath>`), deprecating plain-text directorial tags.

---

## [2026-10-12] Decoupled Directorial Intent & Spoken Dialogue Sanitization
- **Tone Ingestion via LLM Synthesizer**: Configured `gemini-3.8-flash` script synthesizer to ingest prompt prefixes and tone tags, translating them into UPPERCASE emphasis and exclamation cadence without emitting tags in dialogue.
- **Dialogue Sanitization (`clean_spoken_text`)**: Added centralized pre-TTS cleaner in `common.py` to strip prompt prefixes and brackets, guaranteeing output audio never verbalizes directorial instructions.

---

## [2026-10-12] DevFest Montreal 80s Retro Theme & Active GA Model Defaults
- **DevFest Montreal Team Template**: Created primary roster configuration for the 1986 Montreal Canadiens and 80s retro arena synth-rock entrance music prompt.
- **Active GA Model Alignment**: Promoted defaults to `gemini-3.8-flash` (Script), `gemini-3.8-flash-tts` (Voice), and `lyria-3.5` (Music).
- **Automated Catalog Skills**: Created `skills/model-cost-tracker` and `skills/voice-catalog-tracker` with automated audit/update tools (`update_cost_rates.py`, `update_gemini_voices.py`).

---

## [2026-07-27] Theme Context Customization & Multi-Platform Batch Rates
- **Announcer Theme Context**: Added `announcer_persona.theme_context` and CLI flags (`--theme-context`) for thematic announcer personas (e.g. pirate theme).
- **Automated Pricing Scraper**: Created `update_cost_rates.py` scraping official Google AI Studio and Vertex AI documentation, supporting 50% LLM Batch API discount rates.

---

## [2026-07-26] Google Cloud Vertex AI Integration & Free Tier Quota Optimization
- **Enterprise Vertex AI Support**: Unified client initializer supporting GCP API keys and Application Default Credentials (ADC).
- **Request Batching & Slicing**: Implemented batched LLM JSON script enhancement and silence-sliced batched TTS via `pydub.silence`, reducing API calls from ~44 down to 2–3 requests per team run.
- **Dynamic 429 Retry Parsing**: Added automatic parsing of recommended retry delay durations directly from `RESOURCE_EXHAUSTED` errors.

---

## [2026-07-26] Initial Release & CLI Pipeline Suite
- **Initial Release**: Launched TeamHypeAI under GNU AGPLv3 with interactive onboarding wizard (`setup_wizard.py`), AI audio generation (`generate_gemini_audio.py`), and audio stitching engine (`assemble_show.py`) featuring stadium pitch thickening (0.95x) and dynamic ducking.
