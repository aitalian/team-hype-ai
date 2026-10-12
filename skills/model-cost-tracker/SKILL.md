---
name: model-cost-tracker
description: Keeps Gemini and Lyria AI models and pricing up to date for TeamHypeAI. Fetches available models from Google AI Studio and Vertex AI, compares against our tracked subset, suggests newer versions, and updates config/cost_rates.json, README.md, and project docs.
---

# TeamHypeAI Model & Cost Tracker Skill (`model-cost-tracker`)

This repository-scoped skill manages model discovery, tracked subset auditing, version upgrade suggestions, and documentation synchronization for **TeamHypeAI**.

## 🎯 Scope & Triggers
Trigger this skill whenever you need to:
- *"Update and track the latest models and pricing"*
- *"Check for newer Gemini models"*
- *"Sync model rates and documentation"*
- Or manually execute [`update_cost_rates.py`](update_cost_rates.py).

---

## 📋 Tracked Model Categories & Domain Scope
TeamHypeAI strictly focuses on models relevant to sports stadium introductions:

| Role | Description | Current Tracked Default | Alternatives / Previews |
| :--- | :--- | :--- | :--- |
| **`announcer_script`** | LLM stadium script inflection & enhancer | [`gemini-3.8-flash`](config/cost_rates.json) | `gemini-3.6-flash`, `gemini-3.5-flash-lite` |
| **`tts_voice`** | Stadium PA speech generation with speech_metadata | [`gemini-3.8-flash-tts`](config/cost_rates.json) | `gemini-3.8-flash-lite-tts`, `gemini-3.1-flash-tts-preview` *(deprecated)* |
| **`music_generator`** | Arena entrance music generation | [`lyria-3.5`](config/cost_rates.json) | `lyria-3-clip-preview`, `lyria-3-pro-preview` |

---

## 🛠️ Step-by-Step Execution Workflow

### Step 1: Read Current Tracking Registry
Inspect the local registry in [`config/cost_rates.json`](config/cost_rates.json):
- Verify models under `tracked_models`.
- Note currently supported usage channels (`ai_studio`, `vertex_ai`).

### Step 2: Query Available Model Catalog
Run the local repository script in audit mode:
```bash
python update_cost_rates.py --check
```
*(Add `--vertexai` if evaluating models available on Vertex AI enterprise quotas).*

### Step 3: Compare & Recommend Newer Versions
1. Compare API results against the `tracked_models` list in [`config/cost_rates.json`](config/cost_rates.json).
2. For each relevant category (`announcer_script`, `tts_voice`, `music_generator`), flag any newer versions or iterations (e.g., newer 3.x/4.x Flash releases, updated TTS voice engines, or new Lyria releases).
3. Evaluate cost, performance, and API channel availability.
4. Present a side-by-side comparison with upgrade recommendations.

### Step 4: Fetch Metadata, Docs, and Rate Cards
For verified or updated models, obtain:
- **Identifier**: Exact API model name.
- **Display Name & Description**: Capabilities, latency, and context limits.
- **Documentation Link**: Official Google AI Studio or Cloud Vertex AI documentation URL.
- **Channels**: AI Studio (`ai_studio`), Vertex AI (`vertex_ai`), or both.
- **Pricing**: Standard and Batch input/output/cache rates per 1M tokens or per-request costs.

### Step 5: Update Local Configuration Data
Apply the updates to [`config/cost_rates.json`](config/cost_rates.json):
```bash
python update_cost_rates.py --update
```
Or register a newly introduced model:
```bash
python update_cost_rates.py --add-model "gemini-3.8-flash" --role "announcer_script"
```

### Step 6: Maintain Documentation & Project References
Whenever model versions, defaults, or pricing are updated:

1. **[`README.md`](README.md)**:
   - Update all model name references in the architecture diagram, feature descriptions, and CLI examples.
   - Update default and alternative model callouts.

2. **[`GEMINI.md`](GEMINI.md)**:
   - Maintain complete, un-summarized technical specs (pricing rates, token mechanics, API batching, rate limits, and documentation links).

3. **[`TODO.md`](TODO.md)** & **[`LOG.md`](LOG.md)**:
   - Record completed model and pricing updates in [`LOG.md`](LOG.md).
   - Log pending deprecation checks or model evaluation tasks in [`TODO.md`](TODO.md).
