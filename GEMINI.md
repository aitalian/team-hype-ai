# TeamHypeAI - Comprehensive Technical Reference & Project Knowledge (GEMINI.md)

> **📌 Document Purpose & Single Source of Truth**:
> This document is the **authoritative Single Source of Truth for Technical Architecture & Project Knowledge** for TeamHypeAI. It contains exhaustive, un-summarized technical facts regarding Google Gemini and Lyria AI model integrations, the Interactions API contract, audio digital signal processing (DSP), regional accent phonetics, and platform resolution mechanics. All systems, developers, and AI agents should consume and interpret this file as the definitive technical standard.

## 📌 Project Identity & Core Overview
- **Project Name**: TeamHypeAI
- **Project Slug**: `team-hype-ai`
- **Description**: Automated Python pipeline and CLI suite to create stadium-quality audio introductions and announcements for youth sports teams, powered exclusively by Google Gemini and Lyria AI models.
- **Showcase Demo**: Tailored as a proof-of-concept demo for **DevFest Montreal**, featuring the 1986 Stanley Cup Champions Montreal Canadiens theme (with authentic French Canadian bilingual pronunciation) and an 80s retro synth-rock entrance music track.
- **License**: GNU Affero General Public License v3.0 (GNU AGPLv3)

---

## 🤖 Google Gemini & Lyria AI Models Stack

### 1. Text-to-Speech (TTS) Engine
- **Default Model**: `gemini-3.8-flash-tts` (Studio-grade speech generation supporting structured `speech_metadata` [speaker and style] and point-in-time angle-bracket vocal events)
- **High-Throughput Model**: `gemini-3.8-flash-lite-tts` (Conversational, low latency)
- **Deprecated / Legacy Preview Model**: `gemini-3.1-flash-tts-preview` (Deprecated legacy preview model, superseded by `gemini-3.8-flash-tts`. Directorial prompts and tags must be migrated to `speech_metadata`.)
- **Supported Prebuilt Voice Personas**:
  - **Core Featured Stadium Personas**:
    - `Puck` (Default - Male, Upbeat: Energetic / Expressive PA Announcer, style: `"excitedly, fast-paced"`)
    - `Charon` (Male, Informative: Deep / Authoritative Arena Voice, style: `"authoritative, punchy"`)
    - `Kore` (Female, Firm: Punchy / High Enthusiasm PA Voice, style: `"excitedly"`)
    - `Fenrir` (Male, Excitable: Gritty / Aggressive Arena Voice, style: `"shouting, hype"`)
    - `Aoede` (Female, Breezy: Smooth / Championship PA Announcer, style: `"excitedly, fast"`)
  - **Additional Vetted High-Energy Stadium Voices**:
    - `Zephyr` (Female, Bright: Bright / Spirited Arena Voice)
    - `Leda` (Female, Youthful: Youthful / High-Pace Sports Energy)
    - `Orus` (Male, Firm: Commanding / Authoritative Stadium Voice)
    - `Autonoe` (Female, Bright: Bright / Vibrant Stadium Voice)
    - `Algenib` (Male, Gravelly: Gravelly / Raspy Rock Arena Voice)
    - `Laomedeia` (Female, Upbeat: Upbeat / High-Enthusiasm Arena Voice)
    - `Alnilam` (Male, Firm: Firm / Powerful Stadium Voice)
    - `Pulcherrima` (Female, Forward: Forward / Rapid-Fire PA Delivery)
    - `Sadachbia` (Male, Lively: Lively / Dynamic Arena Announcer)
- **Gemini 3.8 Flash TTS Architecture & Speech Metadata (`types.SpeechMetadata`)**:
  - **Verbatim Transcript Model**: Unlike earlier preview models where directorial instructions could be placed in plain text, Gemini 3.8 Flash TTS strictly treats input text as a verbatim transcript to be spoken aloud. Placing prompt prefixes (`Say rapidly...`) or bracketed tags (`[excitedly]`) in text causes the synthesizer to verbalize them.
  - **Sustained Turn-Level Directions (`speech_metadata.style`)**: Sustained delivery instructions (emotion, overall pace, tone, stadium volume, acoustic cues) and voice attribution are moved into structured metadata via `types.SpeechMetadata(speaker=voice_name, style=style)` attached to `types.Part.speech_metadata` (`google-genai>=2.29.0`).
  - **Point-in-Time Vocal Events (Angle-Bracket Tags `<...>`):** Momentary non-speech vocalizations and pauses remain inline inside the transcript using angle brackets (such as `<short pause>`, `<cheer>`, `<sigh>`, `<cough>`, `<breath>`, `<laugh>`).
  - **LLM Announcer Script Synthesizer (`gemini-3.8-flash`) Integration**: Ingests directorial instructions (`announcer_persona.prompt_prefix`), theme context (`announcer_persona.theme_context`), and style cues. Generates rapid-fire stadium PA scripts with UPPERCASE emphasis, punctuation cadence, and point-in-time `<short pause>` tags. Output is strictly clean verbatim dialogue with zero prompt preambles or bracketed tags.
  - **Pre-TTS Dialogue Sanitization (`clean_spoken_text`)**: Prior to sending dialogue to Gemini TTS, `clean_spoken_text()` strips any leading prompt prefixes (`Say rapidly...:`), legacy square-bracket tags (`[...]`), and invalid directorial tags while strictly preserving valid point-in-time vocal event tags (`<short pause>`, `<breath>`, `<cheer>`).
- **SDK & Client Requirements**: Requires `google-genai>=2.29.0` for native `types.SpeechMetadata` and `types.Part.speech_metadata` support.
- **Voice Configurations File**: `config/gemini_voices.json` (Curated English high-energy voices, updated via `update_gemini_voices.py`)
- **Documentation & Migration Guides**: 
  - https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts
  - https://ai.google.dev/gemini-api/docs/speech-generation
  - https://docs.cloud.google.com/text-to-speech/docs/gemini-tts

### 2. Announcer Script Synthesizer & Enhancer
- **Default Model**: `gemini-3.8-flash`
- **Previous Model**: `gemini-3.6-flash`
- **Alternative Model**: `gemini-3.5-flash-lite`
- **Modes**:
  - `"auto"` (Default): Automatically invokes `gemini-3.8-flash` ONLY for clips/players that do not have manual `phonetic` or `phonetic_number` overrides.
  - `"always"`: Forces LLM announcer script enhancement across all roster items.
  - `"never"`: Disables script enhancement completely.
- **Theme / Personality Context Support**: Supports optional team-level (`announcer_persona.theme_context`) and per-item (`roster[i].theme_context`, `intro_clips[i].theme_context`) theme descriptions (e.g. nautical pirate theme for the Admirals, space commander, retro rockstar). Weaved into LLM script enhancement prompts (`gemini-3.8-flash`) to generate thematic phrasing, puns, and tone accents.
- **Batched Script Enhancement**: Combines script enhancement prompts for all roster clips into a single JSON API request, returning enhanced scripts in bulk (reduces LLM calls from N to 1).
- **Tone & Directives Ingestion**: Accepts `delivery_instructions` (prompt prefix) and `speech_style` / style cues per item to steer vocal cadence, energy, and emphasis, producing strictly sanitized dialogue for speech synthesis.
- **Functionality**: Formats raw text into rapid-fire, upper-case emphasized, stadium PA scripts with phonetic inflections before sending to TTS synthesis.

### 3. Stadium Entrance Music Generator
- **Default Model**: `lyria-3.5` (Next-generation high-energy loopable stadium entrance music tracks)
- **Vertex AI Model Garden Lyria Models**:
  - `google/lyria-3-clip-preview` (Lyria 3 for Song Clips Generation, 30-second loopable tracks)
  - `google/lyria-3-pro-preview` (Lyria 3 Pro for Full-Song Generation, high-fidelity stadium tracks)
  - `google/lyria-002` (Lyria 2 for Music Generation, foundational music generation)
- **Platform Availability & AI Studio Exclusivity**:
  - `lyria-3.5` is **exclusively hosted on Google AI Studio** via the Interactions API (`client.interactions.create`). It does **not** exist in Google Cloud Vertex AI (Gemini Enterprise Agent Platform) Model Garden.
  - The Vertex AI Model Garden exclusively hosts `google/lyria-3-clip-preview`, `google/lyria-3-pro-preview`, and `google/lyria-002`.
- **Dynamic Model Availability Auto-Routing Architecture (`resolve_platform_backend`)**:
  - Rather than relying on hardcoded model string checks, the pipeline queries `get_model_availability(eff_music)` dynamically against `config/cost_rates.json` (the single source of truth for model specifications and availability).
  - Whenever a configured model is exclusive to Google AI Studio (such as default `lyria-3.5`, where `availability.ai_studio == True` and `availability.vertex_ai == False`) and the user has not explicitly passed `--vertexai`, the pipeline automatically routes the entire run (script synthesizer, TTS voices, and music generation) to **Google AI Studio**.
  - Conversely, if a configured model is exclusive to Vertex AI (such as `lyria-002`, where `availability.vertex_ai == True` and `availability.ai_studio == False`) and the user has not explicitly passed `--aistudio`, the pipeline automatically routes to **Google Cloud Vertex AI**.
  - This seamlessly overrides local `.env` settings (`GOOGLE_GENAI_USE_VERTEXAI=true`) without requiring manual file edits.
- **Explicit Platform Enforcement & Dynamic Guidance**:
  - If a user explicitly specifies `--vertexai` while an AI Studio-exclusive model is configured, or `--aistudio` while a Vertex-exclusive model is configured, the CLI flag is strictly respected.
  - The generator immediately surfaces an upfront platform compatibility disclaimer and recommendation dynamically querying `get_available_models_for_role(role, platform)` (e.g., advising `--music-model lyria-3-clip-preview, lyria-3-pro-preview, or lyria-002` on Vertex AI, or omitting `--vertexai` to auto-route to Google AI Studio).
- **Pure Instrumental Output Standard (No Vocals / Lyrics)**:
  - To prevent AI music models from generating spoken lyrics, vocal chanting, or singing across stadium background tracks, the Interactions API request specifies `response_modalities=["audio"]` rather than allowing multimodal text/lyrics generation.
  - The prompt is automatically wrapped with negative cues: `Instrumental stadium entrance background music track ({duration_sec} seconds, loopable, high-energy, strictly NO vocals, NO singing, NO speech, NO lyrics): {prompt}`.
- **Strict Model Enforcement (Zero Fallback Substitutions)**:
  - Eliminates legacy multi-model fallback loops and automatic substitutions (e.g. falling back to `lyria-002`). If a specific model is selected, the pipeline adheres strictly to that selection.
- **Functionality**: Synthesizes custom background entrance music tailored to team prompt definitions.

### 4. Regional Accent & Francophone Pronunciation Architecture
- **Problem Statement**: Standard English text-to-speech models default to Americanized pronunciation for Francophone names and places (e.g. pronouncing "Montréal" as *"Mahn-tree-all"*, "Patrick Roy" as *"Pat-rick Roy"*, "Canadiens" as *"Kuh-nay-dee-enz"*, and "Forum" as *"Four-um"*).
- **Multi-Layered Accent Solution**:
  1. **Structured Speech Metadata Accent Injection (`format_speech_style()`)**: Automatically combines base vocal style with regional accent directives (e.g., `with a French Canadian accent on French and Francophone names`) into `types.SpeechMetadata(speaker=voice_name, style=style)` on `types.Part.speech_metadata`. This guides Gemini 3.8 Flash TTS's acoustic phonology without dirtying the verbatim transcript.
  2. **LLM Script Enhancer Instructions (`gemini-3.8-flash`)**: The script synthesizer prompt accepts `regional_accent` and `accent_guidance`, instructing `gemini-3.8-flash` to apply regional pronunciation guidelines and upper-case emphasis on Francophone names and locations.
  3. **Phonetic Guide Respellings (`roster_templates.json`)**: Employs authentic Quebec phonetic respellings for key names:
     - *Montréal* -> `"Mohn-ray-AL"`
     - *Patrick Roy* -> `"Pat-REEK RWAH"`
     - *Bob Gainey* -> `"Bob GAY-nee"`
     - *Chris Chelios* -> `"Chris CHEL-ee-os"`
     - *Mats Naslund* -> `"Mats NAHZ-lund"`
     - *Larry Robinson* -> `"LAIR-ee ROB-in-sun"`
     - *Canadiens* -> `"vos Canadiens de Mohn-ray-AL"` / `"Les Canadiens"`
  4. **Montreal Forum Hockey Cultural Phrasing**: Weaves celebrated bilingual Quebec sports phrasing (*"Le Petit Viking"*, *"Le Capitaine"*, *"Le Big Bird"*, *"Saint Patrick"*, *"Faites du bruit, make some noise!"*, *"GO HABS GO!"*) into player intros.
  5. **CLI Flags & Configuration**:
     - Config schema: `announcer_persona.regional_accent` and `announcer_persona.accent_guidance`.
     - CLI flags: `--regional-accent` / `--accent` across `generate_gemini_audio.py` and `generate_voice_samples.py`.

### 5. Google Interactions API Migration (June 2026 Preferred Standard)
- **Problem Statement & Strategic Evolution**: As of June 2026, Google has designated the **Interactions API** (`client.interactions.create`) as the preferred interface over the legacy `generateContent` API (`client.models.generate_content`) for all new model interactions and developer projects (`https://ai.google.dev/gemini-api/docs/interactions-overview`). Models such as `lyria-3.5` (and future multi-modal interaction models) operate primarily through interaction contracts, requiring an architectural migration away from older generate content patterns while providing graceful backwards compatibility.
- **Platform Scope & Endpoint Differences (AI Studio vs Vertex AI)**:
  - In the `google-genai` SDK (>=2.29.0), `client.interactions.create` calls `/{api_version}/interactions`.
  - **Google AI Studio** (`generativelanguage.googleapis.com`): Hosts the Interactions API endpoint at `/v1beta/interactions`.
  - **Google Cloud Vertex AI** (`aiplatform.googleapis.com`): The Interactions API endpoint `/v1beta1/interactions` is not hosted on Vertex AI, returning a raw HTML 404 error page. Vertex AI natively standardizes on `client.models.generate_content`.
  - **Client Isolation in `init_gemini_client`**: When initializing for AI Studio (`use_vertex=False`), `init_gemini_client` explicitly passes `genai.Client(vertexai=False, api_key=api_key_val)`, preventing the SDK from implicitly inheriting `GOOGLE_GENAI_USE_VERTEXAI=true` from local `.env` files.
- **Interactions API Architecture & SDK Contracts (`google-genai>=2.29.0`)**:
  - **Announcer Script Synthesizer (`gemini-3.8-flash`)**:
    - Invocation Contract: `client.interactions.create(model=llm_model, input=prompt)`
    - Output Parsing: Extracts clean text via `getattr(interaction, "output_text", None)`
    - Supported Modes: Both 1:1 single script enhancement (`enhance_announcer_script`) and single-call batched JSON enhancement (`batch_enhance_announcer_scripts`).
  - **Text-to-Speech Engine (`gemini-3.8-flash-tts`)**:
    - Invocation Contract: `client.interactions.create(model=model_name, input=clean_text, response_format={"type": "audio"}, generation_config={"speech_config": [{"voice": voice_name}]})`
    - Output Parsing: Binary audio bytes extracted from `interaction.output_audio` via `extract_audio_bytes_from_interaction()`
    - Supported Modes: Both 1:1 voice clip generation (`generate_audio_clip_gemini`) and batched silence-sliced TTS generation (`generate_audio_batch_gemini`).
  - **Stadium Entrance Music Generator (`lyria-3.5`)**:
    - Invocation Contract: `client.interactions.create(model=model_name, input=input_text, response_format={"type": "audio"})`
    - Output Parsing: Audio bytes extracted from `interaction.output_audio` via `extract_audio_bytes_from_interaction()`.
- **Audio Extraction Engine (`extract_audio_bytes_from_interaction`) in `common.py`**:
  - Direct Interaction Audio: Checks `getattr(interaction, "output_audio", None)`. In the Google GenAI SDK, `interaction.output_audio` is an `AudioContent` object where `.data` is either a base64-encoded string or raw bytes. The function automatically decodes base64 strings into raw binary audio bytes.
  - Multi-Step Timeline Fallback: If `output_audio` is not present at the top level, iterates through `interaction.steps` and `step.actions` to locate any audio outputs produced during execution.
  - MIME-Type Detection: Inspects `output_audio.mime_type` or infers format from audio header signatures (RIFF/WAV, ID3/MP3).
- **Sanitized Error Presentation (`format_error_brief`) in `common.py`**:
  - Automatically intercepts API exceptions, inspects for raw HTML error dumps (`<!DOCTYPE html>` / `<html`), and converts them into succinct descriptions (such as `404 Not Found (endpoint not available on this platform)` or `403 Forbidden`).
  - Cleans excess whitespace and truncates lengthy exception payloads, preventing raw HTML dumps from leaking into CLI output.
- **Centralized Platform-Aware Engine Resolution Hierarchy (`resolve_api_engine`)**:
  Platform selection and API engine resolution across `generate_gemini_audio.py` and `generate_voice_samples.py` is resolved strictly through `resolve_api_engine(cli_legacy_api, cli_api_engine, config, use_vertex)` in `common.py`:
  1. **Explicit CLI Flags** *(Highest Precedence)*: `--legacy-api`, `--use-generate-content`, or `--legacy-generate-content` unconditionally forces `api_engine="generate_content"`.
  2. **Explicit CLI Engine Flag**: `--api-engine interactions` or `--api-engine generate_content`.
  3. **Platform Default**:
     - If `use_vertex=True`: Natively resolves to `API_ENGINE_LEGACY` (`"generateContent API (Vertex AI Standard)"`).
     - If `use_vertex=False`: Continues to check config/env or defaults to `API_ENGINE_INTERACTIONS` (`"Interactions API (Preferred)"`).
  4. **Team Roster Configuration**: `models.api_engine` (`"interactions"` -> `API_ENGINE_INTERACTIONS`, `"generate_content"` -> `API_ENGINE_LEGACY`) in `roster_templates.json`.
  5. **Environment Variables**: `GEMINI_API_ENGINE` or `GOOGLE_GENAI_API_ENGINE`.
  6. **Default Fallback** *(Lowest Precedence)*: `API_ENGINE_INTERACTIONS` (`"interactions"`, June 2026 standard on AI Studio).
- **Automatic Fallback Protection (`allow_fallback=True`)**:
  If `client.interactions.create()` encounters an API exception other than quota exhaustion (e.g. 403 `API_KEY_SERVICE_BLOCKED` or 404 for `/v1beta/interactions` on older GCP API keys or restricted service accounts), the engine:
  1. Emits a structured log event: `FALLBACK_TO_GENERATE_CONTENT` with error details in `logs/api_execution.log`.
  2. Automatically falls back to `client.models.generate_content(...)` with appropriate `GenerateContentConfig` and modalities.
  3. Seamlessly completes the generation workflow without interrupting team intro production.
- **CLI Flags & Configuration**:
  - Opt into Legacy API: `--legacy-api`, `--use-generate-content`, `--legacy-generate-content`
  - Explicit Engine Selection: `--api-engine interactions` / `--api-engine generate_content`
  - Roster Schema: `"models": {"api_engine": "interactions"}`

### 6. Model Platform Availability Architecture (`availability` in `config/cost_rates.json`)
- **Problem Statement & Motivation**: Certain models possess platform-exclusive availability across Google's developer infrastructure. For example, `lyria-3.5` is exclusively hosted on Google AI Studio via the Interactions API and does not exist in Google Cloud Vertex AI Model Garden, while `google/lyria-002` exists on Vertex AI Model Garden. Previously, handling these limitations required hardcoded model checks (such as `if eff_music == "lyria-3.5"`) scattered across `common.py` and `generate_gemini_audio.py`.
- **Single Source of Truth (`config/cost_rates.json` Schema v2.2.0)**:
  - Each tracked model defines a structured `availability` object alongside `supported_channels`:
    ```json
    "availability": {
      "ai_studio": true,
      "vertex_ai": false,
      "exclusive_to": "ai_studio",
      "notes": "Available exclusively on Google AI Studio via the Interactions API."
    }
    ```
  - Models hosted on Vertex AI with Model Garden publisher prefixes specify `vertex_model_id` (e.g. `google/lyria-3-clip-preview`, `google/lyria-3-pro-preview`, `google/lyria-002`).
- **Dynamic Helper Functions in `common.py`**:
  - `get_model_availability(model_name, json_path="config/cost_rates.json") -> dict`: Dynamically loads availability metadata (`ai_studio`, `vertex_ai`, `exclusive_to`, `supported_channels`, `vertex_model_id`, `notes`, `role`, `display_name`).
  - `is_model_available_on_platform(model_name, use_vertex, json_path="config/cost_rates.json") -> bool`: Fast boolean check for whether a given model is supported on the active platform.
  - `get_available_models_for_role(role, platform="ai_studio", json_path="config/cost_rates.json") -> list`: Returns all candidate model IDs matching a functional role (`announcer_script`, `tts_voice`, `music_generator`) available on the target platform.
- **Dynamic Platform Auto-Routing (`resolve_platform_backend`)**:
  - Automatically queries `get_model_availability(eff_music)`. If the configured music model is exclusive to AI Studio (e.g. `lyria-3.5`), routes the entire pipeline to Google AI Studio. If exclusive to Vertex AI (e.g. `lyria-002`), routes to Google Cloud Vertex AI. Completely eliminates hardcoded model name checks.
- **Platform Compatibility Validation (`warn_if_inactive_models`)**:
  - Validates `(role, model_name)` against `use_vertex`. If an incompatible model is configured with an explicit platform override (e.g., `--vertexai` with `lyria-3.5`, or `--aistudio` with `lyria-002`), surfaces clear, structured warning disclaimers with dynamically queried alternative models before any API calls are executed.
- **Dynamic Platform Matrix Synchronization (`sync_platforms_and_rates` in `update_cost_rates.py`)**:
  - Populates `platforms["ai_studio"]` and `platforms["vertex_ai"]` matrices strictly based on each model's `availability` booleans, ensuring rate card tables remain 100% accurate without leaking unavailable models into platform lookup dictionaries.

---

## ⚡ API Quota Optimization & Request Batching Architecture

To stay well within Free Tier API caps (100 RPD / 10 RPM) while generating full team intros, `generate_gemini_audio.py` uses high-efficiency request batching:

1. **Batched LLM Script Enhancement**: All un-enhanced scripts are rewritten in a single `gemini-3.8-flash` JSON generation call instead of N separate calls.
2. **Batched Gemini TTS & Silence Slicing**: Voice clip prompts are concatenated with explicit acoustic pauses (`... [pause 2s] ...`), generated in chunks (default: 10 clips/request), and sliced into individual `.wav` files using `pydub.silence.split_on_silence`.
3. **Automatic Fallback Protection**: If batching or audio slicing fails or yields segment mismatches, the engine gracefully falls back to 1:1 legacy generation per item.
4. **CLI Flags & Configuration**:
   - `--batch-script` / `--no-batch-script`: Toggle batched LLM script enhancement.
   - `--batch-tts` / `--no-batch-tts`: Toggle batched TTS audio generation.
   - `--batch-size N`: Custom batch size for TTS calls (Default: `10`).
   - `--legacy-mode`: Reverts all API calls to legacy 1:1 item-by-item execution.
5. **Dynamic Rate Limit Retry Delay Parsing**: Automatically extracts exact recommended wait durations (e.g. `'retryDelay': '6429s'` or `'Please retry in 1h47m9.647852093s'`) from 429 `RESOURCE_EXHAUSTED` API errors via `extract_retry_delay_seconds()`, sleeping for the exact quota reset duration instead of a static default.
6. **Multi-Platform Backend Support (Google AI Studio vs Vertex AI)**:
   - **Google AI Studio** *(Default)*: Initialized with `genai.Client(api_key=...)` targeting `generativelanguage.googleapis.com`. Lower per-unit TTS pricing ($0.50 / $10.00 per 1M tokens), but subject to strict daily caps (**10 RPM / 100 RPD** for preview models).
   - **Google Cloud Vertex AI**: Initialized via `init_gemini_client` targeting Vertex AI infrastructure (`us-central1-aiplatform.googleapis.com`). **Not subject to AI Studio's 100 RPD daily quota limit**. Backed by GCP enterprise project quotas (scaling to thousands of RPM) for high-volume multi-team generation runs. Supports GCP API Keys (`GEMINI_API_KEY`, initialized via `genai.Client(vertexai=True, api_key=...)` with mutually exclusive project/location omitted per Google GenAI client contract) and Application Default Credentials (ADC, initialized via `genai.Client(vertexai=True, project=..., location=...)`).
   - **Explicit Google AI Studio Override (`--aistudio` / `--ai-studio` / `--no-vertexai`)**:
     - Provides first-class CLI ability to force the Google AI Studio backend even when `.env` specifies `GOOGLE_GENAI_USE_VERTEXAI=true` without requiring developers to edit their local environment files.
     - Workaround Utility: Essential for working around platform parity differences between Google AI Studio and Vertex AI (such as publisher model availability for `lyria-3.5` stadium music generation, preview features, or regional project quota allocations).
   - **Centralized Platform Resolution Precedence (`resolve_platform_backend`)**:
     Platform selection across `generate_gemini_audio.py`, `generate_voice_samples.py`, and `update_cost_rates.py` is resolved strictly through `resolve_platform_backend()` in `common.py` using the following hierarchy:
     1. **Explicit CLI Flags** *(Highest Precedence)*: `--aistudio` / `--ai-studio` / `--no-vertexai` unconditionally forces `use_vertex=False`; `--vertexai` unconditionally forces `use_vertex=True`. Defined in a mutually exclusive argument group (`parser.add_mutually_exclusive_group()`), rejecting conflicting flags with exit code 2.
     2. **Dynamic Model Availability Auto-Routing (`get_model_availability`)**: Rather than hardcoding model names, `resolve_platform_backend()` queries `get_model_availability(eff_music)` against `config/cost_rates.json` (DRY single source of truth). If the configured model is exclusive to Google AI Studio (e.g. `lyria-3.5`, where `availability.vertex_ai == False`) and the user has not explicitly passed `--vertexai`, the pipeline automatically resolves to `use_vertex=False` (`Google AI Studio (Auto-routed for <model>)`), overriding local `.env` settings. If the model is exclusive to Vertex AI (e.g. `lyria-002`) and the user has not explicitly passed `--aistudio`, the pipeline automatically resolves to `Google Cloud Vertex AI (Auto-routed for <model>)`.
     3. **Team Roster Configuration**: `models.platform` (`"ai_studio"` -> `False`, `"vertex_ai"` -> `True`) or `models.vertexai` / `models.use_vertexai` boolean flags in `roster_templates.json`.
     4. **Environment Variables**: `GOOGLE_GENAI_PLATFORM` (`ai_studio` -> `False`, `"vertex_ai"` -> `True`) or `GOOGLE_GENAI_USE_VERTEXAI` (`true` -> `True`).
     5. **Default Fallback** *(Lowest Precedence)*: `use_vertex=False` (Google AI Studio).
   - **Interactive Setup Wizard Support (`setup_wizard.py`)**:
     - Prompts users with an explicit numbered choice: `[1] Google AI Studio (Default, required for lyria-3.5)` vs `[2] Google Cloud Vertex AI (supports lyria-3-clip/pro-preview)`, configuring the chosen backend in the generated team roster JSON.
   - **CLI Flags & Env Vars**:
     - Force AI Studio: `--aistudio`, `--ai-studio`, `--no-vertexai`
     - Force Vertex AI: `--vertexai`, `--gcp-project <ID>`, `--gcp-location <REGION>`
     - Environment: `GOOGLE_GENAI_PLATFORM`, `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`.

---

## 💵 Dynamic Cost Estimation Rates & Token Mechanics

Loaded dynamically from `config/cost_rates.json` based on active platform (`ai_studio` vs `vertex_ai`) and API execution mode (`standard` vs `batch`):

### Pricing Rate Matrix:
- **Google AI Studio Standard**:
  - `gemini-3.8-flash`: Input: $1.50/1M, Output: $7.50/1M, Cache: $0.15/1M
  - `gemini-3.6-flash`: Input: $1.50/1M, Output: $7.50/1M, Cache: $0.15/1M
  - `gemini-3.5-flash`: Input: $1.50/1M, Output: $9.00/1M, Cache: $0.15/1M
  - `gemini-3.5-flash-lite`: Input: $0.30/1M, Output: $2.50/1M, Cache: $0.03/1M
  - `gemini-3.8-flash-tts`: Input: $0.50/1M (text), Output: $10.00/1M (audio)
  - `gemini-3.8-flash-lite-tts`: Input: $0.30/1M (text), Output: $5.00/1M (audio)
  - `gemini-3.1-flash-tts-preview`: Input: $0.50/1M (text), Output: $10.00/1M (audio)
  - `lyria-3.5`: $0.0400 / song request
  - `lyria-3-clip-preview`: $0.0400 / song request
  - `lyria-3-pro-preview`: $0.0800 / song request
  - `lyria-002`: $0.0400 / song request

- **Google AI Studio Batch API (50% Discount on LLMs)**:
  - `gemini-3.8-flash` (Batch): Input: $0.75/1M, Output: $3.75/1M, Cache: $0.075/1M
  - `gemini-3.6-flash` (Batch): Input: $0.75/1M, Output: $3.75/1M, Cache: $0.075/1M
  - `gemini-3.5-flash` (Batch): Input: $0.75/1M, Output: $4.50/1M, Cache: $0.075/1M
  - `gemini-3.5-flash-lite` (Batch): Input: $0.15/1M, Output: $1.25/1M, Cache: $0.02/1M
  - `gemini-3.8-flash-tts`: Input: $0.50/1M, Output: $10.00/1M
  - `gemini-3.8-flash-lite-tts`: Input: $0.30/1M, Output: $5.00/1M
  - `gemini-3.1-flash-tts-preview`: Input: $0.50/1M, Output: $10.00/1M
  - `lyria-002`: $0.0400 / song request

- **Google Cloud Vertex AI Standard**:
  - `gemini-3.8-flash`: Input: $1.50/1M, Output: $7.50/1M, Cache: $0.15/1M
  - `gemini-3.6-flash`: Input: $1.50/1M, Output: $7.50/1M, Cache: $0.15/1M
  - `gemini-3.5-flash`: Input: $1.50/1M, Output: $9.00/1M, Cache: $0.15/1M
  - `gemini-3.5-flash-lite`: Input: $0.30/1M, Output: $2.50/1M, Cache: $0.03/1M
  - `gemini-3.8-flash-tts`: Input: $0.50/1M (text), Output: $9.00/1M (audio)
  - `gemini-3.8-flash-lite-tts`: Input: $0.50/1M (text), Output: $9.00/1M (audio)
  - `gemini-3.1-flash-tts-preview`: Input: $0.50/1M (text), Output: $9.00/1M (audio)
  - `lyria-3.5`: Unavailable on Vertex AI (Google AI Studio exclusive)
  - `lyria-3-clip-preview`: $0.0400 / song request
  - `lyria-3-pro-preview`: $0.0800 / song request
  - `lyria-002`: $0.0400 / song request

- **Google Cloud Vertex AI Batch (50% Discount on LLMs)**:
  - `gemini-3.8-flash` (Batch): Input: $0.75/1M, Output: $3.75/1M, Cache: $0.075/1M
  - `gemini-3.6-flash` (Batch): Input: $0.75/1M, Output: $3.75/1M, Cache: $0.075/1M
  - `gemini-3.5-flash` (Batch): Input: $0.75/1M, Output: $4.50/1M, Cache: $0.075/1M
  - `gemini-3.5-flash-lite` (Batch): Input: $0.15/1M, Output: $1.25/1M, Cache: $0.02/1M
  - `gemini-3.8-flash-tts`: Input: $0.50/1M, Output: $9.00/1M
  - `gemini-3.8-flash-lite-tts`: Input: $0.50/1M, Output: $9.00/1M
  - `gemini-3.1-flash-tts-preview`: Input: $0.50/1M, Output: $9.00/1M
  - `lyria-002`: $0.0400 / song request

### Audio Token Conversion Mechanics
- Audio output tokens correspond to **25 tokens per second of generated audio** (~1,500 audio tokens per minute).
- A complete 18-player intro costs approximately **$0.05–$0.08 USD** depending on platform (Vertex AI vs AI Studio).

---

## 🎛️ Architecture & Audio Processing Engine

### 1. DRY Roster Configuration (`roster_templates.json`)
Defines models, announcer persona, default templates, roster array, intro clips, and music prompt parameters. Supports phonetic overrides (`phonetic`, `phonetic_number`), custom intro templates (`custom_intro`), and per-player delays/ducking parameters.

### 2. Run of Show Sequence (`run_of_show.json`)
Defines event timeline sequence. Incorporates the `$ROSTER` macro which dynamically expands into player clips based on `roster_templates.json`.

### 3. Audio Mixing (`assemble_show.py`)
- **Voice Pitch Thickening**: Pitch-shifts voice audio by spawning frame rate at 0.95x and resampling to 44.1kHz for stadium resonance.
- **Stadium PA Echo, Multi-Tap Reverb & Bass Boom (`apply_stadium_reverb`)**:
  - **DSP Architecture**: Pure-Python + Pydub multi-tap acoustic reflection engine requiring zero external native plugins beyond standard Pydub/FFmpeg:
    1. **Low-End Bass Resonance ("Boom")**: Isolates sub-220Hz warm body via `low_pass_filter(220)` and overlays it (`bass_boost_db - 6.0` dB) underneath the dry announcement to create chest-thumping arena speaker authority.
    2. **Progressive Multi-Tap Acoustic Reflections**: Generates early arena slapback reflections (`45ms`–`120ms`) and late stadium bowl decay taps (`165ms`–`950ms`). Each reflection tap is progressively low-pass filtered (`4800Hz` down to `1000Hz`) to model high-frequency air absorption across a massive stadium bowl, and high-pass filtered at `120Hz` to keep echo tails crisp and prevent low-end muddiness.
    3. **Acoustic Tail Preservation**: Extends the voice clip canvas (`tail_ms` up to `900ms`) with a smooth fade-out so booming stadium echoes ring out naturally over the ducked background music without abrupt truncation.
  - **Built-in Acoustic Presets (`REVERB_PRESETS`)**:
    - `"none"`: Dry signal (0 taps, 0dB bass boost, 0ms tail).
    - `"subtle"`: Tight indoor gym / studio PA slapback (3 taps: `65ms`, `135ms`, `220ms`; `+1.5dB` bass boost; `250ms` tail).
    - `"arena"`: Classic indoor hockey arena / basketball bowl reverb (5 taps: `55ms` to `390ms`; `+2.5dB` bass boost; `420ms` tail).
    - `"stadium"` *(Default)*: Loud, booming championship sports stadium PA echo & reverb (7 taps: `45ms` to `600ms`; `+3.5dB` bass boost; `600ms` tail).
    - `"coliseum"`: Massive open-air coliseum / canyon echo with dramatic long tail (8 taps: `55ms` to `950ms`; `+4.5dB` bass boost; `900ms` tail).
  - **Configuration & Override Hierarchy (`resolve_reverb_config`)**:
    - Global settings in `run_of_show.json`: `settings.reverb_preset` (default `"stadium"`), `settings.apply_reverb_by_default`, `settings.reverb_wet_gain_offset_db`, and `settings.reverb_bass_boost_db`.
    - Per-event settings in `run_of_show.json` `sequence`: `reverb` (or alias `echo`) accepts boolean (`true`/`false`), preset name (`"subtle"`, `"arena"`, `"stadium"`, `"coliseum"`, `"none"`), or a custom dictionary (`{"enabled": true, "preset": "stadium", "wet_gain_offset_db": 1.5, "bass_boost_db": 4.0, "tail_ms": 700, "taps": [...]}`).
    - Per-player overrides in `roster_templates.json` `roster`: Players expanded via `$ROSTER` inherit the `$ROSTER` event's `reverb` setting and can override `reverb` / `echo` individually.
    - CLI flags in `assemble_show.py`: `--reverb {none,subtle,arena,stadium,coliseum}` and `--no-reverb`.
- **Dynamic Ducking**: Lowers music volume (default `-8dB` to `-15dB`) during voice clip playback (including the extended stadium reverb tail).
- **Clip Fade-In & Fade-Out Envelopes (`resolve_fade_ms`)**:
  - Supports per-event `"fade_out_ms"` / `"fade_out"` and `"fade_in_ms"` / `"fade_in"` in `run_of_show.json` (plus global defaults `settings.default_fade_out_ms` [default `1500ms`] and `settings.default_fade_in_ms` [default `500ms`]).
  - Accepts integer/float milliseconds (`1500`), boolean (`true` uses default duration), or duration strings (`"1500ms"`, `"1.5s"`), automatically clamping to total clip length after `clip_duration_ms` slicing.
  - Applied after normalization, reverb, and voice boost so SFX and crowd noise clips blend seamlessly into the background track and become inaudible instead of cutting off abruptly.
- **Normalization**: Applies dry clip normalization, post-reverb clip normalization, and final mix peak normalization (`headroom=0.1`).
- **Looping & Padding**: Loops background music track seamlessly to match sequence timeline length.

---

## 📻 Arena Hardware Setup (Live Playbook)

```
[ Mobile Device (Phone/Tablet) ]
       │ Bluetooth 5.0 Audio Stream
       ▼
[ Bluetooth Auxiliary Receiver Unit ]
       │ 3.5mm Stereo Aux Cable
       ▼
[ Arena PA System Aux Input / Mixer ]
       │ Arena Amplifiers
       ▼
[ Rink Stadium Speakers ]
```

### Components & Operating Procedure:
1. **Bluetooth Receiver Unit**: Portable 3.5mm Bluetooth receiver (e.g. Avantree / Anker) plugged into arena PA soundboard aux input jack.
2. **Device Pairing**: Paired with phone hosting the assembled master mix from `output/` (e.g. `output/devfest_montreal_80s_assembled.mp3`).
3. **Execution**: Triggered as players assemble at rink entrance doors prior to taking the ice.

---

## 📁 Repository Directory Structure

- `common.py`: Centralized constants, environment loader (`.env`), pricing reader, and voice definition loaders.
- `setup_wizard.py`: Interactive first-time onboarding CLI wizard.
- `generate_voice_samples.py`: Prebuilt voice audition clip generator (`samples/`).
- `generate_gemini_audio.py`: Voice clip and entrance music generator via Gemini & Lyria APIs.
- `assemble_show.py`: Audio stitching and dynamic ducking engine.
- `roster_templates.json`: Team roster template & prompt configuration.
- `run_of_show.json`: Sequence timeline definition using `$ROSTER` macro.
- `config/`: JSON configuration files (`cost_rates.json`, `gemini_voices.json`).
- `input/`: Voice clips and SFX audio files.
- `music/`: Background music tracks.
- `output/`: Assembled final MP3 intros.
- `samples/`: Announcer voice audition previews (`Puck.wav`, `Charon.wav`, `Kore.wav`, `Fenrir.wav`, `Aoede.wav`).
- `logs/`: Timestamped API execution log (`logs/api_execution.log`, git-ignored).
- `BLOG.md`: Announcement blog post authored for a Google Developer Expert (GDE).
- `TODO.md`: Active task list.
- `LOG.md`: Completed milestone log.
- `PROMPT.md`: Master prompt & requirement specifications.
- `GEMINI.md`: Detailed un-summarized technical reference.
- `README.md`: Public GitHub/GitLab documentation.
- `pyproject.toml`: Modern packaging specification (`name = "team-hype-ai"`).
- `requirements.txt`: Python package dependencies (`google-genai`, `pydub`, `audioop-lts`).
- `skills/`: Project root skills directory for cross-LLM compatibility (Claude Code, Gemini, Antigravity).
- `skills/model-cost-tracker/SKILL.md`: Workspace-scoped skill for automated model tracking and pricing synchronization.
- `.agents/skills`: Symlink pointing to `../skills` ensuring native Antigravity workspace skill discovery.
- `.gemini/skills`: Symlink pointing to `../skills` ensuring native Gemini CLI workspace skill discovery.

---

## 🔄 Automated Model & Pricing Tracking Skill (`model-cost-tracker`)

### Overview & Architecture
- **Skill Location**: `skills/model-cost-tracker/SKILL.md` (Root repository location accessible by Claude Code, Antigravity, and Gemini via `.agents/skills` and `.gemini/skills` symlinks)
- **Primary CLI Utility**: `update_cost_rates.py`
- **Data Configuration Store**: `config/cost_rates.json` (Schema Version `2.0.0`)
- **Activation Prompt / Trigger**: "Update and track the latest models and pricing", "Check for newer Gemini models", or `python update_cost_rates.py --check`

### Tracked Models Subset & Functional Roles
TeamHypeAI maintains a dedicated subset of models specialized for sports stadium audio:
1. **Announcer Script Synthesizer & Enhancer (`announcer_script`)**:
   - `gemini-3.8-flash`: Default high-reasoning Flash model ($1.50 in / $7.50 out Standard, $0.75 in / $3.75 out Batch).
   - `gemini-3.6-flash`: Previous generation Flash model ($1.50 in / $7.50 out Standard, $0.75 in / $3.75 out Batch).
   - `gemini-3.5-flash`: Legacy Flash model ($1.50 in / $9.00 out Standard, $0.75 in / $4.50 out Batch).
   - `gemini-3.5-flash-lite`: Ultra-low cost script formatting ($0.30 in / $2.50 out Standard, $0.15 in / $1.25 out Batch).
2. **Text-to-Speech Engine (`tts_voice`)**:
   - `gemini-3.8-flash-tts`: Studio-grade speech generation supporting structured `speech_metadata.style` and inline angle-bracket vocal events ($0.50 in / $10.00 out AI Studio, $0.50 in / $9.00 out Vertex AI).
   - `gemini-3.8-flash-lite-tts`: High-throughput conversational speech ($0.30 in / $5.00 out AI Studio, $0.50 in / $9.00 out Vertex AI).
   - `gemini-3.1-flash-tts-preview`: Controllable low-latency speech generation preview ($0.50 in / $10.00 out AI Studio, $0.50 in / $9.00 out Vertex AI).
3. **Stadium Entrance Music Generator (`music_generator`)**:
   - `lyria-3.5`: Next-generation arena entrance music generator ($0.0400 per song request).
   - `lyria-3-clip-preview`: 30-second loopable high-energy rock entrance track generator ($0.0400 per song request).
   - `lyria-3-pro-preview`: Production-grade high-fidelity entrance track generator ($0.0800 per song request).

### Discovery, Auditing & Version Suggestion Pipeline
1. **Model Catalog Fetching**: Queries available endpoints via `genai.Client.models.list()`, falling back to official Google Developer documentation (`https://ai.google.dev/pricing`) and Vertex AI pricing registries (`cloud.google.com/vertex-ai/generative-ai/pricing`, `cloud.google.com/text-to-speech/pricing`).
2. **Tracked Subset Auditing**: Compares discovered models against the cached `tracked_models` loaded directly from `config/cost_rates.json` (eliminating duplicate hardcoded in-memory model definitions).
3. **Upgrade Suggestion Heuristics**: Analyzes version rank numbers (e.g. 3.8 > 3.6 > 3.5), preview tags, and role classifications to emit recommendations for promoting models to default status.
4. **Data Synchronization**:
   - Updates `config/cost_rates.json` metadata (`tracked_models`), platforms matrix (`platforms`), flat fallback rates (`rates`), and official source documentation URLs (`_meta.sources`).
   - Automatically synchronizes model name references and default recommendations in `README.md` via `sync_readme_models()`.

---

## 🛡️ Model Lifecycle Validation, Inactive Warnings & Fallback System

### 1. Lifecycle Status Taxonomy
Every tracked model defined in `config/cost_rates.json` possesses a designated `status` field:
- **`active`**: Fully supported General Availability (GA) model recommended for stadium production use (e.g. `gemini-3.8-flash`, `gemini-3.8-flash-tts`, `lyria-3.5`).
- **`preview`**: Experimental or preview release with dynamic API surfaces, lower request limits, or impending breaking changes (e.g. `gemini-3.1-flash-tts-preview`, `lyria-3-clip-preview`).
- **`legacy`**: Deprecated or previous generation models superseded by newer architectures (e.g. `gemini-3.6-flash`, `gemini-3.5-flash`).
- **`unknown`**: Model not present in our tracked catalog in `config/cost_rates.json`.

### 2. Validation Architecture (`common.py`)
Model lifecycle checking is centralized through two utility functions in `common.py`:
- `check_model_status(model_name: str, category: str = "general", json_path: str = "config/cost_rates.json") -> dict`:
  - Inspects `config/cost_rates.json` metadata for the given model.
  - Returns a structured dictionary:
    - `is_active`: `bool` (`True` only when `status == "active"`).
    - `status`: `str` (`"active"`, `"preview"`, `"legacy"`, or `"unknown"`).
    - `recommendation`: `Optional[str]` containing the recommended GA replacement model name.
    - `warning_message`: `Optional[str]` containing formatted multi-line warning with bulleted disclaimer and recommendation.
- `warn_if_inactive_models(models_dict: dict, json_path: str = "config/cost_rates.json") -> bool`:
  - Validates a mapping of role to model name (e.g. `{"TTS Voice": tts_model, "Announcer Script": llm_model, "Music": music_model}`).
  - Emits a prominent terminal warning banner if any model is non-active.
  - Returns `True` if any non-active model was detected, `False` otherwise.

### 3. Integrated Tool Validation Points
- **Full Intro Generator (`generate_gemini_audio.py`)**: Runs validation prior to cost calculation and API invocation across `tts_model`, `enhancer_model`, and `music_model`.
- **Voice Sample Audition Generator (`generate_voice_samples.py`)**: Validates the selected `--model` or default TTS model before generating audition audio.
- **Interactive Setup Wizard (`setup_wizard.py`)**: Checks user-selected or template models during team onboarding.

### 4. Terminal Warning Banner & Disclaimer Format
When an inactive model is selected, `warn_if_inactive_models` renders the following standardized banner:
```
======================================================================
🚨 NON-ACTIVE MODEL SELECTION DISCLAIMER & RECOMMENDATIONS
======================================================================
⚠️  WARNING: Model '<model_name>' is currently in PREVIEW status.
   • Disclaimer: Preview models have experimental API surfaces and are subject to breaking changes or quota caps.
   • Recommendation: Switch to active GA model '<recommended_replacement>' for stadium-grade stability.

⚠️  WARNING: Model '<model_name>' is currently a LEGACY model.
   • Disclaimer: Legacy models may experience higher latency, older pricing rates, or future deprecation.
   • Recommendation: Upgrade to active latest model '<recommended_replacement>'.
======================================================================
```

### 5. Recommendation Resolution Heuristics
1. If `recommended_replacement` is explicitly declared in `config/cost_rates.json` for that model, it is prioritized.
2. If omitted or the model is unknown, `check_model_status` infers the model category and maps to the active default:
   - Voice / TTS models (`"tts"` in name or category in `["tts", "tts_voice", "voice"]`): Resolves to `DEFAULT_TTS_MODEL` (`gemini-3.8-flash-tts`).
   - Music models (`"lyria"` in name or category in `["music", "music_generator"]`): Resolves to `DEFAULT_MUSIC_MODEL` (`lyria-3.5`).
   - Script enhancement / LLM models: Resolves to `DEFAULT_LLM_MODEL` (`gemini-3.8-flash`).
3. If all selected models are in `active` status, `warn_if_inactive_models` returns `False` and outputs zero warning noise.

---

## 🎙️ Gemini Voice Catalog Curation & Tracking Skill (`voice-catalog-tracker`)

### 1. Skill Overview & Architecture
- **Skill Location**: `skills/voice-catalog-tracker/SKILL.md` (Root repository location accessible by Claude Code, Antigravity, and Gemini via `.agents/skills` and `.gemini/skills` symlinks)
- **Primary CLI Utility**: `update_gemini_voices.py`
- **Data Configuration Store**: `config/gemini_voices.json`
- **Activation Prompt / Trigger**: "Refresh gemini voices", "Update voice catalog", "Audit announcer voice personas", "Check for high-energy announcer voices", or `python update_gemini_voices.py --check`

### 2. High-Energy Sports PA Announcer Filtering Criteria
The voice catalog is strictly constrained according to two mandatory rules:
1. **Language Constraint**: **English only** (`en` / `en-US` / `en-GB`).
2. **Acoustic & Energy Suitability for Arena PA Systems**:
   - **Target Profiles**: Rapid-fire, punchy, excitable, upbeat, authoritative, resonant, gravelly/rock, high projection.
   - **Target Tones / Keywords**: `Upbeat`, `Excitable`, `Firm`, `Bright`, `Gravelly`, `Lively`, `Forward`, `Bold`, `Punchy`.
   - **Exclusion Criteria**: Voices with soft, gentle, breathy, whispery, casual, easy-going, even/monotone, or warm/conversational delivery are excluded to prevent muffled or un-energetic announcements through arena speakers.

### 3. Curated Voice Catalog Breakdown (14 Vetted / 16 Excluded)

#### Core Featured Stadium Personas (5):
| Persona | Gender | Tone | Announcer Persona Style | Default Speech Style & Nuance |
| :--- | :--- | :--- | :--- | :--- |
| **`Puck`** *(Default)* | Male | Upbeat | Energetic / Expressive PA Announcer | `"excitedly, fast-paced"` |
| **`Charon`** | Male | Informative | Deep / Authoritative Arena Voice | `"authoritative, punchy"` |
| **`Kore`** | Female | Firm | Punchy / High Enthusiasm PA Voice | `"excitedly"` |
| **`Fenrir`** | Male | Excitable | Gritty / Aggressive Arena Voice | `"shouting, hype"` |
| **`Aoede`** | Female | Breezy | Smooth / Championship PA Announcer | `"excitedly, fast"` |

#### Additional Vetted High-Energy Personas (9):
| Persona | Gender | Tone | Announcer Persona Style |
| :--- | :--- | :--- | :--- |
| **`Zephyr`** | Female | Bright | Bright / Spirited Arena Voice |
| **`Leda`** | Female | Youthful | Youthful / High-Pace Sports Energy |
| **`Orus`** | Male | Firm | Commanding / Authoritative Stadium Voice |
| **`Autonoe`** | Female | Bright | Bright / Vibrant Stadium Voice |
| **`Algenib`** | Male | Gravelly | Gravelly / Raspy Rock Arena Voice |
| **`Laomedeia`** | Female | Upbeat | Upbeat / High-Enthusiasm Arena Voice |
| **`Alnilam`** | Male | Firm | Firm / Powerful Stadium Voice |
| **`Pulcherrima`** | Female | Forward | Forward / Rapid-Fire PA Delivery |
| **`Sadachbia`** | Male | Lively | Lively / Dynamic Arena Announcer |

#### Excluded Upstream Voices (16) & Rejection Rationale:
- `Enceladus` (Male, Breathy): Breathy/soft tone; lacks projection and acoustic energy for arena PA.
- `Achernar` (Female, Soft): Soft/gentle tone; delicate delivery unsuitable for high-energy hype.
- `Vindemiatrix` (Female, Gentle): Gentle/quiet delivery; insufficient power for stadium speakers.
- `Callirrhoe` (Female, Easy-going): Easy-going/relaxed tone; lacks urgency and competitive punch.
- `Umbriel` (Male, Easy-going): Easy-going/casual tone; too relaxed for pre-game introductions.
- `Zubenelgenubi` (Male, Casual): Casual/laid-back tone; lacks the intensity needed for arena hype.
- `Sulafat` (Female, Warm): Warm/conversational tone; optimized for customer service/audiobooks.
- `Schedar` (Male, Even): Even/neutral cadence; monotone delivery without dynamic range.
- `Achird` (Male, Friendly): Friendly/mild conversational tone; lacks sports stadium punch.
- `Sadaltager` (Male, Knowledgeable): Knowledgeable/instructional tone; best for documentary narration.
- `Rasalgethi` (Male, Informative): Informative/narrative tone; lacks high-energy inflection.
- `Algieba` (Male, Smooth): Smooth/narrative tone; suited for audiobooks rather than PA shouting.
- `Despina` (Female, Smooth): Smooth/gentle cadence; calm delivery unsuitable for stadium hype.
- `Erinome` (Female, Clear): Clear/neutral assistant voice; lacks emotional excitement.
- `Iapetus` (Male, Clear): Clear/neutral narrator voice; conversational rather than stadium PA.
- `Gacrux` (Female, Mature): Mature/subdued narrative tone; lacking high-tempo arena urgency.

### 4. Configuration Schema (`config/gemini_voices.json`)
The voice configuration file acts as the single source of truth for all voice-related tooling, eliminating hardcoded constants from Python code:
```json
{
  "_meta": {
    "sources": {
      "gemini_tts_guide": "https://ai.google.dev/gemini-api/docs/speech-generation",
      "cloud_tts_docs": "https://docs.cloud.google.com/text-to-speech/docs/gemini-tts"
    },
    "last_updated": "2026-10-12 17:56:36 UTC",
    "filter_criteria": {
      "language": "en",
      "energy": "high_energy",
      "domain": "sports_stadium_announcements"
    },
    "featured_order": [
      "Puck", "Charon", "Kore", "Fenrir", "Aoede"
    ],
    "total_vetted_voices": 14,
    "excluded_voices": {
      "Callirrhoe": "Easy-going / relaxed tone; lacks urgency and competitive punch.", ...
    },
    "upstream_baseline": [
      { "name": "Puck", "tone": "Upbeat", "gender": "Male", "category": "Bright / Upbeat" }, ...
    ]
  },
  "voices": [
    {
      "name": "Puck",
      "description": "Upbeat",
      "tone": "Upbeat",
      "gender": "Male",
      "category": "Bright / Upbeat",
      "language": "en",
      "is_featured": true,
      "announcer_style": "Energetic / Expressive PA Announcer",
      "energy_rating": "high",
      "recommended_tags": "[excitedly, fast-paced]",
      "notes": "Default stadium PA announcer voice. Vibrant and rapid-fire."
    }, ...
  ]
}
```

### 5. Downstream Tool Integration
- **`generate_voice_samples.py`**:
  - Automatically reads the curated high-energy voices from `config/gemini_voices.json`.
  - Supports `--featured-only` to synthesize audition previews strictly for the 5 core stadium personas (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`).
- **`setup_wizard.py`**:
  - Displays only vetted high-energy English voices in the interactive persona selector.
  - Highlights featured personas (`★`) with descriptive announcer styles.

---

## 📐 System Architecture, Tooling & Configuration Reference

### 1. End-to-End Pipeline & Tooling Lifecycle
The full technical production lifecycle operates through 4 distinct decoupled layers (all of which can also be executed start-to-finish directly from `setup_wizard.py`):
1. **Interactive Live Demo & Configuration Layer (`setup_wizard.py`)**:
   - Interactively generates or updates `roster_templates_<mascot_slug>.json` and `run_of_show_<mascot_slug>.json`, loading implied defaults from `roster_templates.json` and `run_of_show.json`.
   - Streamlined for live conference crowd polling: keeps low-level model/batching/platform questions tucked behind an optional advanced toggle (`N` by default), auto-derives a default mascot slug when the team name is changed, adapts team-specific intro clips (`For Your <MASCOT>`, `LETS GO <MASCOT>`), and supports keeping, adding crowd-polled players (`[A]dd`), or replacing (`[N]ew`) the roster.
   - Automatically tags all generated intro clips, player clips, custom music tracks, and assembled output MP3s with `_{mascot_slug}` via `get_mascot_slug()` and `apply_mascot_slug_to_filename()` in `common.py` (while leaving shared `sfx_*` assets and `$ROSTER` untouched) to prevent cache collisions or overwriting existing team artifacts.
   - Can execute the entire production pipeline start-to-finish (`generate_gemini_audio.py -r <roster> -y` followed by `assemble_show.py -c <show> -r <roster> -f`, plus optional `afplay` speaker playback on macOS).
2. **Voice Persona Audition Layer (`generate_voice_samples.py`)**: Synthesizes short audition clips in `samples/` for Google Gemini voice personas (`Puck`, `Charon`, `Kore`, `Fenrir`, `Aoede`) across varying sustained speech styles (`speech_metadata.style`).
3. **AI Speech & Music Generation Layer (`generate_gemini_audio.py`)**:
   - Synthesizes LLM announcer scripts using `gemini-3.8-flash` via the Interactions API (`client.interactions.create`) with UPPERCASE emphasis and `<short pause>` events.
   - Synthesizes PA voice clips using `gemini-3.8-flash-tts` into `input/` using structured `types.SpeechMetadata(speaker=voice_name, style=style)` and mascot-slugged filenames (`_<mascot_slug>.wav`).
   - Uses triple-pause delimiters (`<short pause> <short pause> <short pause>`) for batched TTS requests and smart `(N - 1)` longest-silence boundary detection via `pydub.silence.detect_silence` so clips containing internal `<short pause>` tags still slice cleanly into `N` individual WAV files in a single batch call.
   - Synthesizes pure instrumental entrance music using `lyria-3.5` into `music/` with negative prompts (`strictly NO vocals, NO singing, NO lyrics`).
4. **Audio DSP Mixing & Mastering Layer (`assemble_show.py`)**:
   - Sequences audio events defined in `run_of_show.json`.
   - Expands the `$ROSTER` macro across all player entries using mascot-slugged filenames (`#Num Name_<mascot_slug>.wav`), resolving clips via `resolve_input_clip_path()` (preferring slugged files first, with graceful fallback to un-slugged files).
   - Trims clip duration (`clip_duration_ms`) and applies per-clip fade-in/fade-out volume envelopes (`fade_in_ms`, `fade_out_ms`).
   - Applies pitch thickening (0.95x speed-shift resampled back to 44.1kHz).
   - Applies multi-tap stadium PA echo/reverb (`subtle`, `arena`, `stadium`, `coliseum`) and sub-220Hz bass boom resonance.
   - Dynamically ducks background music (attenuating -9dB to -15dB during speech clips and reverb tails).
   - Applies volume gain normalization and exports the final arena master MP3 into `output/`.

### 2. Upstream Tracking Utilities
- **`update_cost_rates.py`**: Audits and synchronizes `config/cost_rates.json` (model availability matrix and pricing rates) against official Google documentation.
- **`update_gemini_voices.py`**: Discovers and audits upstream Gemini TTS voices against strict high-energy sports PA curation criteria, maintaining `config/gemini_voices.json`.

### 3. CLI Terminal Interface & Branding Architecture (`print_cli_banner`)
- **Visual Branding Standard**: All 6 CLI utilities display a unified, multi-colored athletic branding header upon execution.
- **Solid Colored Block PA Bullhorn Graphic**:
  - Rendered using solid Unicode block elements (`█`, `▄`, `▀`) similar to terminal block logos.
  - Red mouthpiece (`\033[38;5;196m` / `\033[91m`): `███`
  - Flared acoustic bell in high-visibility Orange (`\033[38;5;208m`) and Gold (`\033[38;5;220m` / `\033[93m`): `▄▄██████`, `▄██████████`, `▀██████████`, `▀▀██████`
  - Dual radiating acoustic soundwaves in Cyan (`\033[38;5;51m` / `\033[96m`) and Bright White (`\033[38;5;231m` / `\033[97m`): `▄ ▄`, `██ ██`, `▀ ▀`
  - Gold grip handle (`\033[38;5;220m` / `\033[93m`): `██`
- **Ultra-Legible 5-Line Block Typography**:
  - Full-height 5-line solid block lettering across 61 columns for maximum legibility.
  - "TEAM" in Bold Gold (`\033[38;5;220m` / `\033[93m`).
  - "HYPE" in Bold Cyan (`\033[38;5;51m` / `\033[96m`).
  - "AI" in Bold White (`\033[38;5;231m` / `\033[97m`).
  - Centered subtitle: `STADIUM INTRO AUDIO ENGINE • GOOGLE GEMINI & LYRIA`.
- **78-Character Column Boundary**: Standardized to 78 characters, cleanly fitting within standard 80-column terminal emulators without edge wrap or character misalignment.
- **Context Box Framing & Text Wrapping**:
  - Unified framed container (`┌───┐`, `│   │`, `└───┘`) displaying tool identity, "WHAT IT IS", and "HOW IT WORKS".
  - Implements word wrapping using `textwrap.TextWrapper(width=wrap_width)` with hanging indents for multi-line explanations, preventing truncation or border blowouts.
- **ANSI Color Compatibility & Graceful Degradation (`supports_color`)**:
  - Inspects `sys.stdout.isatty()` to ensure color codes are suppressed when stdout is redirected to files, pipes, or background services.
  - Honors the universal `NO_COLOR` standard (disabling ANSI styling if `NO_COLOR` is present in the environment).
  - Detects `TERM=dumb` and suppresses ANSI escapes.
  - Degrades gracefully to clean plain-text borders and unstyled text when colors are disabled, avoiding escape sequence artifacts.
- **Universal CLI Integration**: Standardized across all 6 executable entry points (`setup_wizard.py`, `generate_voice_samples.py`, `generate_gemini_audio.py`, `assemble_show.py`, `update_cost_rates.py`, `update_gemini_voices.py`).



