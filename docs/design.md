# Design — IndicVoice

**Version:** v0.2 · **Last updated:** 2026-10-03

Covers the interface, interaction flow, and voice/audio design.

## Changes from v0.1

- Voice choices now map to Indic Parler-TTS descriptions and speaker names stored in `config/voices.yaml`.
- Added a **script mismatch warning** (for example English typed while "Skip translation" is on).
- Added first-run model download and access messages.
- UI code and assets now live in `ui/` as defined in `architecture.md`.

---

## 1. Design Principles

1. **One action, one result.** Paste text, pick a language, press one button.
2. **Show your work.** Always show the translated text beside the audio.
3. **Be honest about limits.** Warn about length and translation uncertainty instead of failing silently.
4. **Render Indic scripts correctly.** Odia and other scripts need a proper font everywhere.
5. **Keep voices consistent.** Same voice setting for every sentence in one result.

## 2. Primary User Flow

```
Open app
   │
   ▼
Paste English text ─► Choose language ─► (optional) choose voice
   │
   ▼
Press "Translate & Speak"
   │
   ▼
Progress: "Translating…" then "Speaking sentence 2 of 5…"
   │
   ▼
Result: translated text + audio player + download
```

Alternate flow: tick "My text is already in this language" to skip translation.

## 3. Screen Layout (Gradio)

Two columns on desktop, stacked on mobile.

```
┌───────────────────────────────────────────────────────────┐
│  IndicVoice            English → Indian-language speech    │
├────────────────────────────┬──────────────────────────────┤
│  INPUT                     │  OUTPUT                      │
│                            │                              │
│  [ Text box              ] │  Translated text             │
│  [ (English)             ] │  [ read-only, Indic font   ] │
│  [                       ] │                              │
│  0 / 2000 characters       │  Audio                       │
│                            │  [ ▶ ───────●────  0:12 ]    │
│  Language  [ Odia      ▾ ] │  [ Download WAV ]            │
│  Voice     [ Female    ▾ ] │                              │
│  [ ] Text is already in    │  Status: Done in 6.2 s       │
│      the target language   │                              │
│  ▸ Advanced                │                              │
│                            │                              │
│  [ Translate & Speak ]     │                              │
├────────────────────────────┴──────────────────────────────┤
│  Examples:  [Welcome message] [Opening hours] [Directions]│
└───────────────────────────────────────────────────────────┘
```

## 4. Components

| Component | Behaviour |
|-----------|-----------|
| **Text box** | Multiline, placeholder "Type or paste English text…", live character counter, turns red over the limit |
| **Language dropdown** | English name plus native script, e.g. "Odia (ଓଡ଼ିଆ)". Odia first and preselected |
| **Voice dropdown** | Female or Male. Each maps to a description plus speaker name in `config/voices.yaml` |
| **Advanced (collapsed)** | Custom voice description text box; replaces the preset when filled |
| **Skip-translation checkbox** | When ticked, input label becomes the chosen language and the script check is enforced |
| **Submit button** | Disabled when empty or over limit; spinner while running |
| **Translated text box** | Read-only, copyable, large Indic font (Noto Sans Oriya for Odia) |
| **Audio player** | Play, pause, scrub, speed control |
| **Download button** | WAV named like `odia_2026-10-03.wav` |
| **Examples row** | One-click samples so first-time users see it working at once |

## 5. States

| State | What the user sees |
|-------|--------------------|
| **Empty** | Placeholder text, button disabled |
| **Ready** | Button enabled |
| **First run** | "Downloading and loading models. This can take several minutes the first time." |
| **Processing** | Button spinner and "Translating…" then "Speaking sentence 2 of 5…" |
| **Success** | Translated text, audio player, timing |
| **Partial failure** | Audio for sentences that worked, plus "1 sentence could not be spoken: [text]" |
| **Script mismatch** | Warning under the text box (see messages) |
| **Error** | Plain message and a retry button |

## 6. Messages

| Situation | Message |
|-----------|---------|
| Text too long | "Please keep the text under 2,000 characters. You can split it into parts." |
| Empty input | "Enter some text to continue." |
| Script mismatch | "This text doesn't look like Odia. Untick 'already in this language' to translate it first." |
| Model failure | "Something went wrong while generating audio. Please try again." |
| Models loading | "Getting things ready. The first request takes longer." |
| Access needed | "A model needs Hugging Face access. See the README for how to add your token." |
| Translation notice | "Machine translation can make mistakes. Please review the text before relying on it." |

## 7. Visual Design

| Item | Choice |
|------|--------|
| Theme | Light by default; follows system dark mode |
| Interface font | System sans-serif |
| Indic output font | Noto Sans family for the chosen script, bundled in `ui/assets/fonts/` |
| Colour | One accent colour for the primary button; neutral greys; red only for errors |
| Spacing | Generous padding; text boxes at least 8 rows |
| Size | Output text at least 18 px |

## 8. Accessibility

- Every control has a visible label.
- Full keyboard use; Ctrl+Enter submits from the text box.
- WCAG AA colour contrast.
- Audio always has matching text for hearing-impaired users and for verification.
- Status and errors use text, not colour alone.

## 9. Voice and Audio Design

| Decision | Choice | Reason |
|----------|--------|--------|
| TTS model | `ai4bharat/indic-parler-tts` | Free, covers Odia, voice set by text description |
| Voice definition | Description sentence plus a recommended speaker name per language, stored in `config/voices.yaml` | Keeps voice stable across sentences |
| Default voice | Female, clear, moderate pace, close recording, no background noise | Neutral and intelligible |
| Selecting speakers | Listen to each listed speaker for Odia, Hindi, Bengali; record the pick in `memory.md` | Avoid guessing |
| Sentence pause | About 250 ms (`sentence_pause_ms`) | Natural rhythm |
| Output format | Mono WAV first; MP3 later | Lossless and simplest |
| Loudness | Peak-normalize each chunk before joining | Prevents volume jumps |
| Long text | Chunk by sentence | Better quality and stability |

## 10. Developer Experience (API and CLI)

- Interactive API docs at `/docs` (FastAPI).
- Consistent error JSON: `{ "error": "message", "code": 400 }`.
- Human-readable language names (`odia`), never internal codes (`ory_Orya`).
- CLI example: `python -m indicvoice "Welcome to Odisha." --lang odia --voice female --out welcome.wav`.

## 11. Test Content for Design Review

- Short greeting
- Sentence with numbers and times
- Sentence with a place name (a temple or city)
- Three-sentence paragraph
- Over-limit input
- Empty input
- Odia text with "skip translation" ticked
- English text with "skip translation" ticked (should trigger the warning)

## 12. Future Ideas (Not in v1)

- Side-by-side output across several languages
- Word-level highlighting synced to audio
- Saved history of conversions
- Embeddable audio widget for other sites
- Optional voice cloning backend (IndicF5)
