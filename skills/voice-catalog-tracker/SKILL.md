---
name: voice-catalog-tracker
description: Keeps Google Gemini TTS voice personas in config/gemini_voices.json refreshed and up to date, strictly curated for English-speaking, high-energy sports and stadium PA announcers for TeamHypeAI.
---

# TeamHypeAI Gemini Voice Catalog Tracker Skill (`voice-catalog-tracker`)

This repository-scoped skill manages voice discovery, sports announcer taxonomy curation, high-energy filtering, and configuration updates for **TeamHypeAI**.

## 🎯 Scope & Triggers
Trigger this skill whenever you need to:
- *"Refresh gemini voices"*
- *"Update voice catalog"*
- *"Audit announcer voice personas"*
- *"Check for high-energy announcer voices"*
- *"Update config/gemini_voices.json"*
- Or manually execute [`update_gemini_voices.py`](update_gemini_voices.py).

---

## 📋 High-Energy Sports Announcement Curation Criteria

TeamHypeAI strictly constrains voice personas to voices suitable for youth sports arenas and hockey rink PA systems:

1. **Language Constraint**: **English only** (`en` / `en-US` / `en-GB`).
2. **Energy & Acoustic Profile**:
   - **Target Profiles**: Rapid-fire, punchy, excitable, upbeat, authoritative, resonant, gravelly/rock, high projection.
   - **Target Tones / Keywords**: `Upbeat`, `Excitable`, `Firm`, `Bright`, `Gravelly`, `Lively`, `Forward`, `Bold`, `Punchy`.
3. **Exclusion Criteria (Non-Stadium Voices)**:
   - Soft, gentle, breathy, whispery, casual, easy-going, even/monotone, or warm/conversational voices are strictly excluded to avoid muffled or un-energetic rink announcements.

---

## 🎙️ Curated Announcer Personas Taxonomy

### 🌟 Core Featured Stadium Personas
These 5 personas are highlighted across team templates, sample auditions, and documentation:

| Persona | Gender | Tone | Announcer Persona Style | Default Audio Tags |
| :--- | :--- | :--- | :--- | :--- |
| **`Puck`** *(Default)* | Male | Upbeat | Energetic / Expressive PA Announcer | `[excitedly, fast-paced]` |
| **`Charon`** | Male | Informative | Deep / Authoritative Arena Voice | `[authoritative, punchy]` |
| **`Kore`** | Female | Firm | Punchy / High Enthusiasm PA Voice | `[excitedly]` |
| **`Fenrir`** | Male | Excitable | Gritty / Aggressive Arena Voice | `[shouting, hype]` |
| **`Aoede`** | Female | Breezy | Smooth / Championship PA Announcer | `[excitedly, fast]` |

### 🔊 Additional Vetted High-Energy Personas
Extended English voices that satisfy high-energy sports delivery criteria:
- **`Zephyr`** (Female, Bright) - Bright / Spirited Arena Voice
- **`Leda`** (Female, Youthful) - Youthful / High-Pace Sports Energy
- **`Orus`** (Male, Firm) - Commanding / Authoritative Stadium Voice
- **`Autonoe`** (Female, Bright) - Bright / Vibrant Stadium Voice
- **`Algenib`** (Male, Gravelly) - Gravelly / Raspy Rock Arena Voice
- **`Laomedeia`** (Female, Upbeat) - Upbeat / High-Enthusiasm Arena Voice
- **`Alnilam`** (Male, Firm) - Firm / Powerful Stadium Voice
- **`Pulcherrima`** (Male, Forward) - Forward / Rapid-Fire PA Delivery
- **`Sadachbia`** (Male, Lively) - Lively / Dynamic Arena Announcer

---

## 🛠️ Step-by-Step Execution Workflow

### Step 1: Audit Current Voice Catalog
Run the voice audit tool in check mode:
```bash
python update_gemini_voices.py --check
```
*(Add `--all` to display detailed rejection reasons for all excluded voices).*

### Step 2: Evaluate Upstream Google Gemini TTS Documentation
Fetch and review the latest available voice catalog from official Google sources:
- **Google AI Studio Speech Guide**: `https://ai.google.dev/gemini-api/docs/speech-generation`
- **Google Cloud Gemini-TTS Docs**: `https://docs.cloud.google.com/text-to-speech/docs/gemini-tts`

### Step 3: Apply High-Energy English Filter & Taxonomy
1. Verify English language compatibility (`language: "en"`).
2. Evaluate acoustic projection and tone for stadium environments.
3. Classify candidate voices against the vetted voices catalog (`voices`) and the exclusion taxonomy (`_meta.excluded_voices`) embedded directly in [`config/gemini_voices.json`](config/gemini_voices.json).

### Step 4: Refresh Configuration Data
Update [`config/gemini_voices.json`](config/gemini_voices.json):
```bash
python update_gemini_voices.py --update
```

### Step 5: Audition Sample Audio Clips
Generate audition previews in `samples/` for the curated voices:
```bash
# Preview all curated high-energy voices (dry run)
python generate_voice_samples.py --dry-run

# Audition only the 5 core featured stadium personas
python generate_voice_samples.py --featured-only --dry-run
```

### Step 6: Maintain Project Documentation
When voice personas are refreshed or added:
1. **[`README.md`](README.md)**: Ensure persona lists and CLI defaults reflect curated options.
2. **[`GEMINI.md`](GEMINI.md)**: Maintain full technical specifications for voice personas and acoustic profiles.
3. **[`TODO.md`](TODO.md)** & **[`LOG.md`](LOG.md)**: Record completed voice refreshes.
