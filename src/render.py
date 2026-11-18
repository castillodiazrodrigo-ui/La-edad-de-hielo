"""Compositor: transiciones, subtítulos, render multiproceso y mezcla con el audio original.

uso:  python3 src/render.py                 -> output/la_edad_de_hielo_short.mp4
      python3 src/render.py --frames 12.3 40  -> PNGs de prueba en output/preview/
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *  # noqa
import scenes as SC

AUDIO = os.path.join(ROOT, "assets/audio/narracion.mp3")
OUTPUT = os.path.join(ROOT, "output/la_edad_de_hielo_short.mp4")

# ------------------------------------------------------------- subtítulos
FIX = {"casar": "cazar", "bebés.": "bebes.", "meandertales": "neandertales", "latardecer.": "atardecer."}


def load_words():
    data = json.load(open(os.path.join(ROOT, "src/transcript_raw.json")))
    words = []
    for seg in data:
        for w in seg["words"]:
            t = w["w"].strip()
            t = FIX.get(t, t)
            words.append({"w": t, "s": w["s"], "e": w["e"]})
    return words


def build_chunks(words, max_words=3, max_w=900, size=74):
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        txt = " ".join(x["w"] for x in cur).upper()
        nxt = words[i + 1] if i + 1 < len(words) else None
        brk = (len(cur) >= max_words or w["w"][-1] in ".,?!" or nxt is None
               or (nxt and nxt["s"] - w["e"] > 0.35)
               or (nxt and text_width(txt + " " + nxt["w"].upper(), size) > max_w))
        if brk:
            chunks.append(cur)
            cur = []
    out = []
    for i, ch in enumerate(chunks):
        start = ch[0]["s"]
        end = ch[-1]["e"] + 0.25
        if i + 1 < len(chunks):
            end = min(max(end, ch[-1]["e"]), chunks[i + 1][0]["s"])
            if chunks[i + 1][0]["s"] - ch[-1]["e"] < 0.6:
                end = chunks[i + 1][0]["s"]
        out.append((start, end, ch))
    return out


WORDS = load_words()
CHUNKS = build_chunks(WORDS)


def draw_captions(c, T, y):
    for start, end, ch in CHUNKS:
        if start <= T < end:
            size = 74
            parts = [w["w"].upper() for w in ch]
            widths = [text_width(p, size) * 1.08 for p in parts]
            sp = size * 0.42
            total = sum(widths) + sp * (len(parts) - 1)
            sc = 0.85 + 0.15 * ease_out_back(pr(T, start, start + 0.15))
            c.save()
            c.translate(W / 2, y)
            c.scale(sc, sc)
            x = -total / 2
            for w, p, wd in zip(ch, parts, widths):
                active = w["s"] <= T < max(w["e"], w["s"] + 0.15) + 0.05
                said = T >= w["s"]
                col = "#ffe14a" if active else ("#ffffff" if said else "#dfe6ee")
                lift = -8 * (1 - pr(T, w["s"], w["s"] + 0.12)) if active else 0
                text(c, p, x + wd / 2, lift, size * (1.08 if active else 1), col, align="center", sw=size * 0.22)
                x += wd + sp
            c.restore()
            return


# ------------------------------------------------------------- composición
TRANS_D = {"punch": 0.22, "whip": 0.22, "fade": 0.4, "iris": 0.45, "wipe": 0.45, "cut": 0}


def scene_index(T):
    idx = 0
    for i, (s0, _, _) in enumerate(SC.SCENES):
        if T >= s0:
            idx = i
    return idx


def draw_scene(c, i, T):
    c.save()
    SC.SCENES[i][1](c, T)
    c.restore()


def compose(c, T):
    i = scene_index(T)
    s0, fn, tr = SC.SCENES[i]
    dt = T - s0
    d = TRANS_D[tr]
    nxt = SC.SCENES[i + 1] if i + 1 < len(SC.SCENES) else None
    end = nxt[0] if nxt else SC.DURATION

    if tr == "whip" and dt < d and i > 0:
        p = smooth(dt / d)
        blur = 60 * math.sin(math.pi * p) + 1
        c.save()
        c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur, 2)))
        c.save()
        c.translate(-W * p, 0)
        draw_scene(c, i - 1, T)
        c.restore()
        c.save()
        c.translate(W * (1 - p), 0)
        draw_scene(c, i, T)
        c.restore()
        c.restore()
        c.restore()
    elif tr in ("iris", "wipe") and dt < d and i > 0:
        p = smooth(dt / d)
        draw_scene(c, i - 1, T)
        clip = skia.Path()
        if tr == "iris":
            clip.addCircle(W / 2, H * 0.6, 1300 * p)
        else:
            x = lerp(-700, W + 700, p)
            clip = path([(x - 600, 0), (x + 600, 0), (x - 600 + 0, H), (x - 1800, H)]) if False else \
                path([(-200, -200), (x + 300, -200), (x - 300, H + 200), (-200, H + 200)])
        c.save()
        c.clipPath(clip, doAntiAlias=True)
        draw_scene(c, i, T)
        c.restore()
        if tr == "iris":
            c.drawCircle(W / 2, H * 0.6, 1300 * p, P("#ffffff", 16))
        else:
            c.drawLine(x + 300, -200, x - 300, H + 200, P("#ffffff", 40))
            snowfall(c, T, n=30, wind=0, speed=0, seed=99)
    elif tr == "punch" and dt < d:
        p = ease_out(dt / d)
        zz = 1 + 0.2 * (1 - p)
        c.save()
        c.translate(W / 2, H / 2)
        c.scale(zz, zz)
        c.translate(-W / 2, -H / 2)
        draw_scene(c, i, T)
        c.restore()
        if dt < 0.1:
            c.drawRect(skia.Rect.MakeWH(W, H), P("#ffffff", alpha=0.55 * (1 - dt / 0.1)))
    elif tr == "fade" and dt < d:
        draw_scene(c, i, T)
        c.drawRect(skia.Rect.MakeWH(W, H), P("#000000", alpha=1 - smooth(dt / d)))
    else:
        draw_scene(c, i, T)

    # salida en negro previa a un 'fade'
    if nxt and nxt[2] == "fade" and T > end - 0.25:
        c.drawRect(skia.Rect.MakeWH(W, H), P("#000000", alpha=smooth(pr(T, end - 0.25, end))))

    cy = SC.CAPTION_Y.get(fn, 1430)
    draw_captions(c, T, cy)


# ------------------------------------------------------------- render
_surf = {}


def render_frame(n):
    if "s" not in _surf:
        arr = np.zeros((H, W, 4), dtype=np.uint8)
        _surf["a"] = arr
        _surf["s"] = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    s = _surf["s"]
    c = s.getCanvas()
    c.clear(skia.ColorBLACK)
    T = n / FPS
    compose(c, T)
    s.flushAndSubmit() if hasattr(s, "flushAndSubmit") else None
    return _surf["a"].tobytes()


def preview(times, outdir):
    os.makedirs(outdir, exist_ok=True)
    for t in times:
        n = int(round(float(t) * FPS))
        buf = render_frame(n)
        arr = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 4)
        img = skia.Image.fromarray(arr.copy(), colorType=skia.kRGBA_8888_ColorType)
        img.save(os.path.join(outdir, "f_%05.2f.png" % float(t)))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--frames":
        preview(sys.argv[2:], os.path.join(ROOT, "output/preview"))
        return
    start = float(os.environ.get("START", 0))
    end = float(os.environ.get("END", SC.DURATION))
    out = os.environ.get("OUT", OUTPUT)
    frames = range(int(round(start * FPS)), int(round(end * FPS)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    silent = out.replace(".mp4", "_video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                           "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent],
                          stdin=subprocess.PIPE)
    with Pool(int(os.environ.get("JOBS", os.cpu_count()))) as pool:
        for k, buf in enumerate(pool.imap(render_frame, frames, chunksize=4)):
            ff.stdin.write(buf)
            if k % 150 == 0:
                print("frame", k, "/", len(frames), flush=True)
    ff.stdin.close()
    ff.wait()
    if start == 0 and end == SC.DURATION:
        # audio original intacto (copia del stream, sin recodificar)
        subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", AUDIO, "-map", "0:v",
                               "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", out])
        os.remove(silent)
    print("listo:", out if start == 0 and end == SC.DURATION else silent)


if __name__ == "__main__":
    main()
