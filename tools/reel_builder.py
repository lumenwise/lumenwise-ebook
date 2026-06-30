#!/usr/bin/env python3
"""
reel_builder.py — Faceless-Reel-Generator für @feierabend.cashflow

Erzeugt aus einer JSON-Definition ein fertiges 9:16-Reel (1080x1920) mit
Text-Overlays im Schwarz/Gold-Markenstil. Ton wird bewusst NICHT eingebaut
(Trending-Sound in der Instagram-App draufpacken = Algorithmus-Boost).

Nutzung:
    python3 tools/reel_builder.py tools/reels/tag1.json tools/output/tag1.mp4

Hintergrund-Optionen in der JSON:
    {"type": "gradient"}                      -> generierter dunkler Look (kein Footage nötig)
    {"type": "clips", "files": ["a.mp4", ...]}-> echte Stock-Clips (Pexels/Mixkit)
"""
import json
import os
import shlex
import subprocess
import sys
import tempfile

W, H, FPS = 1080, 1920, 30
FONT_BOLD = os.path.join(os.path.dirname(__file__), "fonts", "Anton-Regular.ttf")

COLORS = {
    "white": "0xFFFFFF",
    "gold": "0xD4AF37",
}
FS = {"white": 84, "gold": 104}   # Schriftgrößen
LINE_H = 132                       # Zeilenhöhe


def fade_alpha(start, end, fin=0.4, fout=0.35):
    """Alpha-Ausdruck: sanftes Ein-/Ausblenden je Segment."""
    return (
        f"if(lt(t,{start}),0,"
        f"if(lt(t,{start + fin}),(t-{start})/{fin},"
        f"if(lt(t,{end - fout}),1,"
        f"if(lt(t,{end}),({end}-t)/{fout},0))))"
    )


def build_background(bg, duration):
    """Liefert (filter_string, input_args) für den Hintergrund."""
    if bg.get("type") == "clips" and bg.get("files"):
        files = bg["files"]
        inputs = []
        for f in files:
            inputs += ["-i", f]
        # Clips gleich lang skalieren/croppen, hintereinander, leicht abdunkeln
        per = duration / len(files)
        parts = []
        for i in range(len(files)):
            parts.append(
                f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},trim=duration={per},setpts=PTS-STARTPTS,"
                f"eq=contrast=1.25:saturation=0.85:brightness=-0.05[v{i}]"
            )
        concat = "".join(f"[v{i}]" for i in range(len(files)))
        parts.append(f"{concat}concat=n={len(files)}:v=1:a=0[bg]")
        return ";".join(parts), inputs
    # Default: generierter, cinematischer Dunkel-Look (kein Footage nötig)
    flt = (
        f"gradients=s={W}x{H}:c0=0x1c1c1c:c1=0x050505:x0={W//2}:y0=0:"
        f"x1={W//2}:y1={H}:d={duration}:r={FPS},"
        f"vignette=PI/4.2,"
        f"noise=alls=7:allf=t+u,"
        f"format=yuv420p[bg]"
    )
    return flt, []   # gradients ist selbst eine Quelle -> kein -i nötig


def main():
    if len(sys.argv) != 3:
        print("Nutzung: python3 reel_builder.py <reel.json> <output.mp4>")
        sys.exit(1)
    cfg_path, out_path = sys.argv[1], sys.argv[2]
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    duration = cfg.get("duration", 12)
    handle = cfg.get("handle", "@feierabend.cashflow")

    tmpdir = tempfile.mkdtemp(prefix="reel_")
    bg_filter, bg_inputs = build_background(cfg.get("background", {}), duration)

    chains = [bg_filter]
    cur = "[bg]"
    idx = 0

    for seg in cfg["segments"]:
        start, end = seg["start"], seg["end"]
        lines = seg["lines"]
        total_h = len(lines) * LINE_H
        y0 = (H * 0.42) - total_h / 2          # Block im oberen/mittleren Drittel
        alpha = fade_alpha(start, end)
        for li, line in enumerate(lines):
            txt = line["text"]
            color = line.get("color", "white")
            tf = os.path.join(tmpdir, f"t{idx}.txt")
            with open(tf, "w", encoding="utf-8") as fh:
                fh.write(txt)
            y = int(y0 + li * LINE_H)
            out = f"[s{idx}]"
            chains.append(
                f"{cur}drawtext=fontfile='{FONT_BOLD}':textfile='{tf}':"
                f"fontcolor={COLORS[color]}:fontsize={FS[color]}:"
                f"x=(w-text_w)/2:y={y}:"
                f"shadowcolor=black@0.6:shadowx=4:shadowy=4:"
                f"alpha='{alpha}':enable='between(t,{start},{end})'{out}"
            )
            cur = out
            idx += 1

    # Persistenter Handle unten
    hf = os.path.join(tmpdir, "handle.txt")
    open(hf, "w", encoding="utf-8").write(handle)
    chains.append(
        f"{cur}drawtext=fontfile='{FONT_BOLD}':textfile='{hf}':"
        f"fontcolor=0xD4AF37:fontsize=38:x=(w-text_w)/2:y={H-150}:"
        f"alpha=0.85[outv]"
    )

    filter_complex = ";".join(chains)
    fc_file = os.path.join(tmpdir, "fc.txt")
    open(fc_file, "w", encoding="utf-8").write(filter_complex)

    cmd = ["ffmpeg", "-y", *bg_inputs,
           "-filter_complex_script", fc_file,
           "-map", "[outv]", "-t", str(duration),
           "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-crf", "20", "-movflags", "+faststart",
           out_path]
    print("FFmpeg läuft...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FEHLER:\n", res.stderr[-2500:])
        sys.exit(1)
    print(f"✅ Fertig: {out_path}")


if __name__ == "__main__":
    main()
