# Happy Farm: Human Voice + Phone Landscape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Happy Farm talk to Elaina in a natural human-sounding voice and play well on a phone held sideways.

**Architecture:** Every phrase the game says is recorded once with a neural (human-like) voice by a small build script and embedded as base64 MP3 in `happy-farm.html`, so the game stays one offline file. `speak(text)` plays the matching clip through the existing Web Audio context, and falls back to the best voice the device has. On phones, the Start tap goes fullscreen, locks landscape and keeps the screen awake; the home button moves away from the notch; phone portrait shows a "turn me sideways" screen.

**Tech Stack:** Plain HTML5 canvas + Web Audio + Web Speech API (no libraries); Python 3.12 + `edge-tts` 7.3.1 (already installed) for building the clips.

**Spec:** The parent's request in chat, 2026-10-25: "the voice is like robotic can you make this sound like a human so my daughter can easy to learn and understand then make this mobile friendly in mobile its in horizontal view."

## Why it sounds robotic today

`speak()` (`happy-farm.html:85-93`) never picks a voice, so the device's default (often the oldest, flattest one) is used, and `pitch = 1.35` pushes it into a squeaky, synthetic range.

## Global Constraints

- The game stays a single file, `happy-farm.html`, that works offline after it is built. No external URLs at runtime.
- `happy-farm.html` stays under 1 MB.
- `KID_NAME = "Elaina"`.
- Neural voice: `en-US-JennyNeural`, rate `-10%` (clear, warm adult voice, a bit slower for a 3-year-old).
- Fallback device voice: `rate = 0.9`, `pitch = 1.05`.
- Fullscreen, orientation lock and wake lock only on touch devices (`matchMedia('(pointer: coarse)')`); a desktop click on Start must not go fullscreen.
- Phone = touch device with `Math.min(W, H) < 600`. Tablets keep playing in portrait.
- This folder is not a git repository. Before Task 1, copy `happy-farm.html` to `happy-farm.backup.html`; the "Save" step of each task means re-running the self-test and keeping the file, no commit.
- Building the clips sends each phrase (including the name "Elaina") to Microsoft's online TTS service once. Nothing is sent when the game is played.

## Review Focus

1. **Toddler mashing taps** — tapping bubbles fast must play only the newest word, never a pile of overlapping voices. Test in Task 2.
2. **iPhone on silent (ring switch)** — Web Audio is muted by the silent switch unless the audio session is `playback`; the voice must still be heard. Manual check in Task 2.
3. **A phrase with no clip** (e.g. the name is changed later and the script isn't re-run) — the game must still speak it with the device voice, not go silent or crash. Test in Task 2.
4. **Rotating the phone mid-game** — portrait shows the rotate screen, input is ignored, and turning back to landscape resumes with progress kept (Shapes already keeps progress in `layout()`). Test in Task 3.
5. **Notch / camera cut-out on either side in landscape** — the home button must sit fully inside the safe area. Test in Task 3.

---

### Task 1: Self-test harness + better device voice

**Files:**
- Modify: `happy-farm.html:25` (`KID_NAME`), `happy-farm.html:85-93` (`speak`), end of the `<script>` (harness)

**Interfaces:**
- Produces:
  - `check(name: string, fn: () => boolean | Promise<boolean>): void` — registers a self-test. Opening `happy-farm.html?selftest` runs all checks after `load` (awaiting promises), logs `FAIL <name>` for each failure, then exactly one of `SELFTEST PASS <n>` or `SELFTEST <k> FAILED`.
  - `pickVoice(voices: {name: string, lang: string}[]): object | null` — pure; best English voice or `null`.
  - `speakTTS(text: string): void` — device speech with `pickVoice`, `rate 0.9`, `pitch 1.05`.

- [ ] **Step 1: Write the failing checks** (just above `requestAnimationFrame(frame)` at the end)

```js
check('prefers natural voices', () => pickVoice([
  {name:'Microsoft David - English (United States)', lang:'en-US'},
  {name:'Microsoft Jenny Online (Natural) - English (United States)', lang:'en-US'},
  {name:'Google Deutsch', lang:'de-DE'}
]).name.includes('Jenny'));
check('ignores non-English voices', () => pickVoice([{name:'Google Deutsch', lang:'de-DE'}]) === null);
check('iOS enhanced beats compact', () => pickVoice([
  {name:'Samantha', lang:'en-US'}, {name:'Samantha (Enhanced)', lang:'en-US'}
]).name === 'Samantha (Enhanced)');
check('name is Elaina', () => KID_NAME === 'Elaina');
```

- [ ] **Step 2: Run, verify it fails**

Open `happy-farm.html?selftest` (built-in browser `preview_start` with the `file:///…/happy-farm.html?selftest` URL, then read console; or Chrome DevTools console).
Expected: a `ReferenceError` for `check`, or `SELFTEST 4 FAILED`.

- [ ] **Step 3: Implement**

- `check` + the `?selftest` runner as described in Interfaces.
- `pickVoice`: keep voices whose `lang` starts with `en`; score name by `/natural|neural|online/i` +4, `/enhanced|premium/i` +3, `/google/i` +2, `/jenny|aria|samantha|karen|moira|zira/i` +1; return the highest, ties keep list order.
- `speakTTS`: the current `speak` body, plus `u.voice = pickVoice(speechSynthesis.getVoices())`, `u.lang = 'en-US'`, the new rate/pitch. Voices load late on Chrome: call `speechSynthesis.getVoices()` once at startup so the list is ready by the first tap.
- `speak(text)` temporarily just calls `speakTTS(text)` (Task 2 replaces it).
- `KID_NAME = "Elaina"`.

- [ ] **Step 4: Run, verify it passes** — Expected: `SELFTEST PASS 4`. Tap through Start → Animals once and hear the new voice.

- [ ] **Step 5: Save**

---

### Task 2: Recorded human voice clips

**Files:**
- Create: `tools/make_voice.py`
- Modify: `happy-farm.html` — add the clip block after the `SFX` object (`:109`), replace `speak`, edit `audioInit` (`:45-55`)

**Interfaces:**
- Consumes: `check`, `speakTTS` (Task 1).
- Produces:
  - In `happy-farm.html`: one line between the markers `/* VOICE-CLIPS:BEGIN */` and `/* VOICE-CLIPS:END */`: `const VOICE_CLIPS = { "<exact phrase>": "<base64 mp3>", ... };`
  - `allPhrases(): string[]` — every literal the game passes to `speak`: greetings (`'Hello ' + KID_NAME + '!'`, `"Let's play!"`), the 3 menu labels, `ANIMALS[].say`, `COLORS[].n`, `'Yay! Good job!'`, `SHAPES[].name`, `SHAPES[].name + '! Well done!'`, `'Hooray ' + KID_NAME + '!'`, `'Hooray!'` (31 phrases).
  - `stopVoice(): void` — stops the playing clip and any device speech.
  - `speak(text: string): void` — same signature as today, so no call site changes.
  - `tools/make_voice.py [--voice en-US-JennyNeural] [--rate=-10%]` — run from the project folder; rewrites the marker block in `happy-farm.html`.

- [ ] **Step 1: Write the failing checks**

```js
check('every phrase has a clip', () => {
  const missing = allPhrases().filter(p => !VOICE_CLIPS[p]);
  if (missing.length) console.error('missing clips:', missing);
  return missing.length === 0;
});
check('unknown phrase falls back to device voice', () => {
  const said = [], real = speechSynthesis.speak.bind(speechSynthesis);
  speechSynthesis.speak = u => said.push(u.text);
  try { speak('Zebra time'); } finally { speechSynthesis.speak = real; }
  return said[0] === 'Zebra time';
});
check('fast taps keep only the newest word', async () => {
  audioInit(); speak('Red'); speak('Blue'); speak('Green');
  await new Promise(r => setTimeout(r, 400));
  return voiceSrc && voiceSrc._phrase === 'Green';
});
```

(`voiceSrc` is the currently playing `AudioBufferSourceNode`; set `voiceSrc._phrase = text` when starting it, for this check.)

- [ ] **Step 2: Run, verify it fails** — Expected: `ReferenceError` (`allPhrases` / `VOICE_CLIPS`) or `SELFTEST 3 FAILED`.

- [ ] **Step 3: Write `tools/make_voice.py`**

- `PHRASES`: the same 31 strings as `allPhrases()`, written out literally (the self-test catches drift).
- For each phrase: `edge_tts.Communicate(text, voice, rate=rate).save(<temp mp3>)`, read bytes, base64.
- Build the line with `json.dumps(dict, ensure_ascii=False)` and replace everything between the two markers in `happy-farm.html` (UTF-8 in, UTF-8 out).
- Exit non-zero with `markers not found in happy-farm.html` if either marker is missing; print the phrase count and final file size.

- [ ] **Step 4: Add the empty marker block to `happy-farm.html`**, run the script, check the file

Run: `python tools/make_voice.py`
Expected: `31 clips`, file size under 1 MB.

- [ ] **Step 5: Implement playback in `happy-farm.html`**

- `audioInit`: after creating `AC`, add `if (navigator.audioSession) navigator.audioSession.type = 'playback';` (lets iPhone play sound with the silent switch on).
- `stopVoice`: bump a generation counter, `voiceSrc.stop()` in try/catch, `speechSynthesis.cancel()` in try/catch.
- `speak(text)`: return if `!VOICE || !text`; `stopVoice()`; if there's no clip or no `AC`, `speakTTS(text)`; else decode once per phrase (cache the `AC.decodeAudioData` promise by phrase), and when it resolves start an `AudioBufferSourceNode` connected straight to `AC.destination` (full volume, not through the 0.55 SFX `master`), only if no newer `speak` happened meanwhile. If decoding fails, `speakTTS(text)`.
- `allPhrases()` as in Interfaces.

- [ ] **Step 6: Run, verify it passes** — Expected: `SELFTEST PASS 7`. Play every scene and listen: each word is the recorded voice and is clearly audible over the sound effects.

- [ ] **Step 7: Manual check on an iPhone with the silent switch on** — tap Start: "Hello Elaina!" is heard. (Needs iOS 17+; on older iOS the silent switch still mutes all game sound, same as today.)

- [ ] **Step 8: Save**

---

### Task 3: Phone landscape

**Files:**
- Modify: `happy-farm.html` — `<style>` + a `<div id="safe">` in `<body>`, `layoutHud` (`:297`), `Start.down` (`:333`), input handlers (`:649-660`), `resize` (`:668-675`), `frame` (`:681-690`)

**Interfaces:**
- Consumes: `check` (Task 1).
- Produces:
  - `let SAFE = {t: 0, r: 0, b: 0, l: 0}` — safe-area insets in CSS px, refreshed in `resize()` (declared with `let`; the self-test swaps it).
  - `needsRotate(w: number, h: number, coarse: boolean): boolean` — `coarse && h > w && Math.min(w, h) < 600`.
  - `goFullLandscape(): void` — touch devices only: `requestFullscreen({navigationUI:'hide'})`, then `screen.orientation.lock('landscape')`; plus `navigator.wakeLock.request('screen')`. Every call guarded by feature checks with `.catch(() => {})`, so iPhone (no fullscreen API) just keeps playing.
  - `drawRotateHint(): void`.

- [ ] **Step 1: Write the failing checks**

```js
check('phone portrait asks to rotate', () => needsRotate(390, 844, true) === true);
check('phone landscape plays', () => needsRotate(844, 390, true) === false);
check('tablet portrait plays', () => needsRotate(768, 1024, true) === false);
check('desktop never asks', () => needsRotate(500, 900, false) === false);
check('home button clears a left notch', () => {
  const old = SAFE; SAFE = {t:0, r:0, b:21, l:47}; layoutHud();
  const ok = homeBtn.x - homeBtn.r >= 47; SAFE = old; layoutHud(); return ok;
});
```

- [ ] **Step 2: Run, verify it fails** — Expected: `SELFTEST 5 FAILED` or a `ReferenceError`; earlier checks still pass.

- [ ] **Step 3: Implement**

- Safe area: `#safe{position:fixed;inset:0;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)}`; `resize()` reads its computed `padding*` into `SAFE` (`parseFloat`, default 0) before `layout()`.
- `layoutHud`: `homeBtn = {x: SAFE.l + r + 14, y: SAFE.t + r + 14, r}`.
- `Start.down`: call `goFullLandscape()` first. Also re-request the wake lock on `visibilitychange` when the page becomes visible again.
- `frame`: if `needsRotate(W, H, COARSE)`, draw `drawRotateHint()` instead of the scene (skip `scene.update` too); `COARSE = matchMedia('(pointer: coarse)').matches`.
- Input handlers: ignore pointer events while `needsRotate(W, H, COARSE)`.
- `drawRotateHint`: soft background (`drawSoftBg`), a rounded phone shape tipping between 0° and 90° (`Math.sin(T*2)`), and the text `Turn me sideways!` in the same bold outlined style as the Start title.

- [ ] **Step 4: Run, verify it passes** — Expected: `SELFTEST PASS 12`.

- [ ] **Step 5: Check the layouts in the browser**

With the built-in browser (`resize_window`, mobile preset reloads the page as a touch phone) or Chrome DevTools device mode, screenshot each:
- 844×390 (iPhone landscape) and 800×360 (small Android landscape): Start, Menu, Animals, Bubbles, Shapes all fit, nothing cut off, home button fully visible.
- 390×844: rotate screen shows; resize back to 844×390 mid-Shapes: already-placed shapes stay placed.
- 768×1024: game plays in portrait (no rotate screen).
- Reset with the desktop preset when done.

- [ ] **Step 6: Manual check on a real phone** — open the file, tap Start: Android goes fullscreen sideways and the screen doesn't dim. On iPhone, Share → Add to Home Screen gives fullscreen (Safari on iPhone has no fullscreen API).

- [ ] **Step 7: Save**
