# TeamHypeAI - Project Task & Milestone Checklist (TODO.md)

> **📋 Document Role**:
> This document tracks active pending work and completed project milestones.
> For chronological implementation change details, see [`LOG.md`](LOG.md).
> For deep technical architecture and API specifications, see [`GEMINI.md`](GEMINI.md).

---

## 📌 Active & Pending Tasks
- [ ] Monitor Google Gemini API releases for new audio generation features and voice models.
- [ ] Add DevFest Montreal session recording link to [`README.md`](README.md) post-conference.
- [x] Add DevFest Montreal presentation slides link to [`README.md`](README.md) (via the `aitalian.ca/devfestmtl2026-slides` redirect, so the target can change without a commit).
- [ ] Optional: Develop web-based touch panel UI for live game-day audio triggering.

---

## ✅ Completed Milestones

- [x] **Live Demo Start-to-Finish Setup Wizard & Mascot-Slugged Artifacts (`setup_wizard.py`, `common.py`, `generate_gemini_audio.py`, `assemble_show.py`)**: Streamlined `setup_wizard.py` for fast crowd-polling during live demos (tucking advanced model/batching settings behind an optional toggle, supporting `[K]eep / [A]dd / [N]ew` roster entry, and running `generate_gemini_audio.py` + `assemble_show.py` start-to-finish), added `get_mascot_slug()` and `apply_mascot_slug_to_filename()` so all generated voice clips, custom music tracks, and output mixes include `_{mascot_slug}` without stomping over existing artifacts, and upgraded batched TTS silence slicing to handle internal `<short pause>` tags via `(N - 1)` longest-silence detection.
- [x] **Per-Clip Fade-Out & Fade-In Envelope Controls (`assemble_show.py`)**: Added `fade_out_ms` / `fade_out` and `fade_in_ms` / `fade_in` support in `assemble_show.py` (`resolve_fade_ms`) and configured `1500ms` smooth fade-outs on example SFX across Run of Show configs.
- [x] **Stadium PA Echo, Multi-Tap Reverb & Bass Boom DSP Engine**: Extended `assemble_show.py`, `run_of_show.json`, `run_of_show_with_reverb.json`, and `setup_wizard.py` with multi-tap stadium acoustic reflections, progressive high-frequency air damping, sub-220Hz bass boom resonance, acoustic tail extension, 5 venue presets (`none`, `subtle`, `arena`, `stadium`, `coliseum`), per-clip/per-player overrides, and CLI flags (`--reverb`, `--no-reverb`).
- [x] **CLI Colored Logo & Utility Context Banners**: Added native ANSI solid colored block sports bullhorn logo (`█`, `▄`, `▀`) and ultra-legible 5-line block typography for `TeamHypeAI` (Gold "TEAM", Cyan "HYPE", White "AI"), alongside structured, word-wrapped context framing ("WHAT IT IS", "HOW IT WORKS") and `NO_COLOR` / `isatty()` degradation across all 6 CLI utilities.
- [x] **Comprehensive Utility Documentation, Architecture Diagrams & Tuning Guide**: Expanded `README.md` and `GEMINI.md` with Mermaid architecture and audio DSP timeline diagrams, end-to-end user workflow, exhaustive utility script reference for all 6 CLI tools, and a configuration fine-tuning guide for roster and run of show JSON templates.
- [x] **Gemini 3.8 Flash TTS Speech Style & Nuance Modernization**: Modernized legacy "audio tags" terminology to official Gemini 3.8 Flash TTS architecture: sustained turn-level delivery style & nuance (`speech_metadata.style`, `--speech-style`, unbracketed) vs point-in-time inline tags (`<short pause>`, angle brackets), maintaining backwards compatibility aliases for `--audio-tags`.
- [x] **Setup Wizard Implied Defaults**: Updated `setup_wizard.py` to read existing `roster_templates.json` and `run_of_show.json` as implied defaults across all prompts, preserving hardcoded defaults as fallback only when files are absent.
- [x] **Public GitHub Release Readiness**: Cleaned and refactored documentation across `README.md`, `GEMINI.md`, `PROMPT.md`, `TODO.md`, and `LOG.md` with strict DRY principles, DevFest Montreal context, slides placeholders, and open-source contribution guidelines.
- [x] **Model Platform Availability Architecture**: Added structured `availability` property to `config/cost_rates.json` (v2.2.0), implemented dynamic resolution helpers in `common.py`, and eliminated hardcoded model string checks.
- [x] **All-or-Nothing Auto-Routing & Pure Instrumental Music**: Automatically routes `lyria-3.5` to Google AI Studio Interactions API with pure instrumental audio modality constraints (strictly NO vocals/lyrics).
- [x] **Vertex AI Interactions API Compatibility**: Implemented platform-aware API engine resolution (`generate_content` on Vertex AI, `interactions` on AI Studio), sanitized error reporting, and strict model enforcement without unauthorized fallbacks.
- [x] **Google Interactions API Migration (June 2026 Preferred Standard)**: Migrated script synthesis, speech generation, and stadium music to `client.interactions.create` with full `--legacy-api` backwards compatibility and error fallback.
- [x] **Explicit Google AI Studio Override (`--aistudio`)**: Added CLI flags to override `.env` settings and force Google AI Studio backend directly from the command line.
- [x] **Regional French Canadian Accent & Francophone Pronunciation**: Integrated structured speech metadata accents, LLM synthesizer pronunciation guidance, and Quebec hockey cultural phrasing for DevFest Montreal.
- [x] **Gemini 3.8 Flash TTS Architecture Migration**: Migrated to production-grade `gemini-3.8-flash-tts` supporting structured `types.SpeechMetadata` and point-in-time angle brackets (`<short pause>`, `<cheer>`).
- [x] **Directorial Instruction & Spoken Dialogue Sanitization**: Decoupled prompt prefixes and bracketed tags from verbatim spoken dialogue via `clean_spoken_text()`.
- [x] **DevFest Montreal 80s Retro Theme**: Configured primary team templates for the 1986 Stanley Cup Champions Montreal Canadiens and 80s retro arena rock entrance music.
- [x] **Automated Voice Catalog Tracker (`skills/voice-catalog-tracker`)**: Automated voice catalog scraper and updater (`update_gemini_voices.py`) curated for high-energy English stadium announcers.
- [x] **Automated Model & Pricing Tracker (`skills/model-cost-tracker`)**: Automated rate card scraper and updater (`update_cost_rates.py`) synchronized with `config/cost_rates.json`.
- [x] **Free Tier API Quota Optimization**: Implemented batched LLM JSON script enhancement, batched TTS audio slicing via `pydub.silence`, and dynamic rate limit retry delay parsing.
- [x] **Google Cloud Vertex AI Enterprise Integration**: Unified client initializer supporting GCP API keys and Application Default Credentials (ADC).
- [x] **Audio DSP & Stitching Engine**: Stadium pitch thickening (0.95x speed-shift), dynamic ducking, normalization, and `$ROSTER` macro expansion.
