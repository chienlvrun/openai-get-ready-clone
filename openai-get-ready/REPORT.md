# REPORT — OpenAI "Get ready" clone

## Format check
| file | size | fps | frames | duration | notes |
|---|---|---|---|---|---|
| reference | 1920×1080 | 60 | 726 | 12.10 s (+ AAC 12.16 s) | untagged colour |
| clone_2k60.mp4 | 2560×1440 | 60 | 726 | 12.10 s, reference audio copied | H.264 High, yuv420p, BT.709 TV, crf 12, faststart |
| compare_ref_vs_clone.mp4 | 2560×720 | 60 | 726 | 12.10 s, reference audio | [reference \| clone], crf 17 |

## Shots
- **A 0–280** face discs: zoom-out on the grey face, asterisk eyes turn around the sphere, expression swaps, five more faces enter, all shrink away.
- **B 281–370** dots gather → "1 day." outline (glyph by glyph, 2-frame stagger) → fill.
- **C 371–490** cut to "1 day. 20+ launches.": slow zoom-out, "launches." reveal, dots vanish, exit zoom toward the right end.
- **D 491–725** cut to "OpenAI DevDay[2026]": zoom settle, reveal, "]" slides in, slow leftward drift.

Triage: everything is rebuildable (discs, glyph eyes, dots, text). No faces, footage or photos → **no slots**. "OpenAI" appears only as wordmark text and is rebuilt as text outlines.

## Methods and key recovered results
- **Discs:** sub-pixel contours (marching squares at 0.5 alpha) + RANSAC/Kasa circle fit, median residual 0.04–0.3 px; one track per colour, per-frame table (reference fps = output fps = 60, so every clone frame lands on a measured frame).
- **Eyes:** 6 glyph templates vectorised from the sharpest reference instances (asterisk, chevron, plus, o, caret, bar). Each eye in each frame gets an affine ECC fit (template → frame), with the glyph type chosen by best correlation (typically 0.99–0.999) and propagated through time. Eyes are clipped to their disc, which reproduces the "wrap around the sphere" look.
- **Typeface:** 27 open grotesk families × weights were template-matched; best NCC 0.81 (DM Sans 500). Verdict: **unknown (proprietary OpenAI Sans)**. Glyph outlines were therefore **vectorised from the reference**: potrace on 8× upsampled coverage, with luma coverage for coloured text to avoid 4:2:0 chroma blur. The big "1 day." was traced from frame 360, with the parts hidden under dots filled from the scaled small trace. Its outline strokes were vectorised directly from frame 331.
- **Glyph states:** for each glyph in each frame, the state (none / outline with alpha / fill) is chosen by least-squares model comparison under the measured camera pose. The outline alpha is solved in closed form.
- **Camera pose:** a per-frame similarity (s, tx, ty) from per-glyph ECC. The start of shot D is refined by Nelder–Mead on the full state model.
  - Shot C zoom-out is a single CSS bezier: s: 1.0462 → 1.0002 over t = 6.183 s → 8.526 s, `cubic-bezier(0.029, 0.642, 0.376, 1.108)`, rms 7·10⁻⁵ (≈0.07 px at a 1000 px lever) — the original curve.
- **Dots:** chroma (UV) unmixing, which preserves area under 4:2:0, + a blurred union-of-discs least-squares fit with BIC model selection for touching or overlapping dots. White bracket handles are found by a 3×3 opening.
- **"]"** slides in over frames 519–523 as a measured per-glyph offset (−215, −169, −51, −16, −3 px).
- Outline strokes @1080p: big 3.3 px, small 2.1 px, final 1.6 px white (α≈0.6 on "penAI"), green 1.0 px.
- Colours: discs grey (223,223,223), purple (140,58,239), orange (242,106,32), green (17,208,78), dark (38,38,38), blue (9,107,247); text green (12,194,70); eyes black, or white on the dark disc.

## Metrics (gray, 360p, clone frame k vs reference frame k; whole frame = rebuilt area since there are no slots)
| shot | MAD /255 | SSIM |
|---|---|---|
| A faces 0–280 | 0.339 | 0.9949 |
| B dots → "1 day." 281–370 | 0.136 | 0.9991 |
| C "20+ launches" 371–490 | 0.077 | 0.9998 |
| D "DevDay[2026]" 491–725 | 0.065 | 0.9997 |
| **all 726 frames** | **0.182** | **0.9978** |

The encoded 2K mp4, decoded again and compared with the reference (every 15th frame): MAD 0.396, SSIM 0.9977.
Pop detector: 9 flags, all of them matching events in the reference (expression swaps, cuts) → **0 clone-only pops**. Timing is frame-locked.

## Slots / placeholders
None.

## Remaining differences
- **Confirmed:** disc and eye edges differ by ≤1 px of anti-aliasing softness (the reference encode is softer); worst frame MAD 0.67.
- **Confirmed:** decoded colours are off by 1–2 levels (BT.709 round trip of an untagged source).
- **Estimated:** frames 0–6 (disc larger than the frame) use an extrapolated radius. The green dots on "2026" use the disc green (too small to sample).
- **Estimated:** big-shot outline joints under the dots are bridged with the fill contour (hidden by the dots).
- **Unknown:** the exact typeface (proprietary). Glyphs are traced from the reference, not typeset.
