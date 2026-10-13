# TeamHypeAI - Agent Master Instructions & Prompt Guidelines (PROMPT.md)

> **🤖 Agent Directive & Single Source of Truth**:
> This file establishes the core operational guidelines and behavioral standards for AI coding assistants working on TeamHypeAI.
> To prevent duplication and maintain strict DRY compliance:
> - **Technical Architecture & System Design**: Consume [`GEMINI.md`](GEMINI.md) as the authoritative Single Source of Truth for all API contracts, SDK interactions, audio engineering DSP, and platform routing mechanisms.
> - **Model Specifications, Rates & Platform Availability**: Read directly from [`config/cost_rates.json`](config/cost_rates.json).
> - **Curated Announcer Voices**: Read directly from [`config/gemini_voices.json`](config/gemini_voices.json).

---

## 📌 Project Identity & Vision
- **Project Title**: `TeamHypeAI` (Slug: `team-hype-ai`)
- **Mission**: Automated Python pipeline and CLI suite generating stadium-quality sports introductions and announcements powered exclusively by Google Gemini and Lyria AI models.
- **Showcase Context**: Tailored as a live proof of concept for **DevFest Montreal** featuring the 1986 Montreal Canadiens Stanley Cup roster (with authentic Quebec Francophone pronunciation) and 1980s retro arena rock entrance music.
- **License**: GNU Affero General Public License v3.0 (GNU AGPLv3).

---

## 🛠️ Core Agent Guidelines & Standards

1. **Strict DRY Enforcement**:
   - Never duplicate rate matrices, voice catalogs, or API endpoint specifications in code or prompts.
   - Utilize centralized helpers in [`common.py`](common.py) (`get_model_availability`, `resolve_platform_backend`, `init_gemini_client`, `clean_spoken_text`).
   - Maintain naming consistency (`TeamHypeAI` / `team-hype-ai`) across code, CLI banners, packaging, and documentation.

2. **Google GenAI Architecture & API Standards**:
   - **Interactions API (`client.interactions.create`)**: June 2026 preferred standard across script enhancement (`gemini-3.8-flash`), speech generation (`gemini-3.8-flash-tts`), and music generation (`lyria-3.5`).
   - **Legacy Support**: Preserve fallback to `client.models.generate_content` via `--legacy-api` and automatic error fallback.
   - **Speech Style & Nuance vs. Inline Vocal Tags**: Keep verbatim transcripts clean. Move sustained style, emotion, volume, and pace directions into `types.SpeechMetadata(speaker=voice_name, style=style)` on `types.Part.speech_metadata` using clean unbracketed descriptive strings (e.g. `"excitedly, fast-paced"`, `"shouting, hype"`). Never use legacy square brackets. Reserve inline angle brackets (`<short pause>`, `<cheer>`) strictly for point-in-time vocal events.
   - **Pure Instrumental Music**: Ensure music generation prompts include negative framing (`strictly NO vocals, NO singing, NO lyrics`) and specify `response_modalities=["audio"]`.

3. **Security & Sensitive Data Protection**:
   - Never hardcode API keys, personal credentials, private GCP project IDs, or internal URLs.
   - Redact API keys from logs using `[REDACTED_API_KEY]`.
   - Maintain git exclusion rules for `.env*`, `logs/`, and temporary scratch files.

4. **Living Documentation Maintenance**:
   - Update [`TODO.md`](TODO.md) to track active and completed tasks.
   - Update [`LOG.md`](LOG.md) to record consolidated release milestones.
   - Retain all exhaustive technical facts in [`GEMINI.md`](GEMINI.md).
   - Update [`PROMPT.md`](PROMPT.md) as project requirements evolve.
