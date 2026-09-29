# OpenAI "Get ready" — code clone

Rebuild of the 12.1 s reference as live vector layers (Canvas2D in headless Chromium), rendered at 2560×1440 @ 60 fps.

## Layout
- `project/index.html` – scrub/loop preview (`?rs=N` = render scale), exposes `window.renderAt(t)`.
- `project/scene.js` – the scene: discs + eye glyphs, dots, text glyphs (none / outline(α) / fill states, per-frame camera pose).
- `project/data/*.js` – measured tables: `circles.js` (discs), `eyes.js` (eye-glyph affines), `eye_templates.js`,
  `dots.js`, `text_trace.js` (vector glyph outlines), `textstate.js` (per-frame glyph states + camera similarity).
- `project/render.mjs` – QA PNG renderer; `project/render_hq.mjs` – final renderer piping PNGs into ffmpeg.
- `tools/` – measurement & fitting scripts; `tools/mathfit.py` = RTS smoother, cubic-bezier easing fit, RBF helpers.

## Commands
```bash
cd project && npm i playwright-core          # uses /opt/pw-browsers chromium, no download
# QA frames at 1080p
FPS=60 node render.mjs ../qa/out --range 0 726 1
# final 2K60 (two segments in parallel) + audio copied from the reference
node render_hq.mjs ../out 1.3333333333 60 0 363 seg0 & node render_hq.mjs ../out 1.3333333333 60 363 726 seg1 & wait
cd ../out && printf "file 'seg0.mp4'\nfile 'seg1.mp4'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -i ../ref.mp4 -map 0:v -map 1:a -c:v copy -c:a copy -movflags +faststart clone_2k60.mp4
# side-by-side compare video
F=project/fonts/Inter-Medium.ttf; N=726; R=60
ffmpeg -i ref.mp4 -i out/clone_2k60.mp4 -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=0.1,fps=$R,scale=1280:720:flags=lanczos,setsar=1,drawtext=fontfile=$F:text='REFERENCE':x=24:y=22:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10[a];[1:v]tpad=stop_mode=clone:stop_duration=0.1,fps=$R,scale=1280:720:flags=area,setsar=1,drawtext=fontfile=$F:text='CLONE (code)':x=24:y=22:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10[b];[a][b]hstack=inputs=2,drawbox=x=1279:y=0:w=2:h=720:color=black@0.9:t=fill,format=yuv420p[v]" -map "[v]" -map 0:a -frames:v $N -r $R -c:v libx264 -crf 17 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv -c:a copy -movflags +faststart out/compare_ref_vs_clone.mp4
```

## Measurement pipeline
Reference frames extracted by index to `of/%05d.png` (`ffmpeg -i ref.mp4 of/%05d.png`), then:
1. Discs: `circles.py` → `tracks.py` → `tracks3.py`; eyes: `eyes.py` + `eyes_run.py`.
2. Glyph outlines: `trace_text.py`, `trace_big.py`, `trace_big_outline.py`.
3. Glyph pose/state: `glyphstate.py` → `states.py` (+ `pose_nm.py` refinement, `compile_text.py`).
4. Dots: `dots_run.py`, `dots_fix.py`, `dots_white.py`.
5. `export.py` writes `project/data/*.js`. QA: `metrics.py`, `pops.py`, `strip.py`.
