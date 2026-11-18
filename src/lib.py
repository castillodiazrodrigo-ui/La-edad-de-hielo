"""Motor de dibujo 2D (skia) para el Short 'La Edad de Hielo'.

Primitivas con contorno grueso estilo cartoon, personajes articulados,
animales, escenarios, efectos y elementos de interfaz animados.
"""
import math
import os
import random

import skia

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_MAIN = skia.Typeface.MakeFromFile(os.path.join(ROOT, "assets/fonts/luckiest-guy-latin-400-normal.ttf"))
TF_ALT = skia.Typeface.MakeFromFile(os.path.join(ROOT, "assets/fonts/bangers-latin-400-normal.ttf"))


# ----------------------------------------------------------------- utilidades
def hexc(h, a=255):
    h = h.lstrip("#")
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(a))


def rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def mix(h1, h2, t, a=255):
    """Mezcla dos colores hex -> skia color."""
    t = clamp(t)
    a1, a2 = rgb(h1), rgb(h2)
    return skia.Color(*[int(a1[i] + (a2[i] - a1[i]) * t) for i in range(3)], int(a))


def mixh(h1, h2, t):
    t = clamp(t)
    a1, a2 = rgb(h1), rgb(h2)
    return "#%02x%02x%02x" % tuple(int(a1[i] + (a2[i] - a1[i]) * t) for i in range(3))


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def pr(T, a, b):
    """progreso 0..1 de T entre a y b"""
    if b == a:
        return 1.0 if T >= a else 0.0
    return clamp((T - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_out_back(x, s=1.70158):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_out_elastic(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1


def noise(t, seed=0.0):
    """ruido suave determinista en [-1,1]"""
    return (math.sin(t * 1.7 + seed * 3.1) * 0.5 + math.sin(t * 3.9 + seed * 1.3) * 0.3
            + math.sin(t * 7.3 + seed * 5.7) * 0.2)


def pop(T, t0, dur=0.32):
    """escala de aparición con rebote; 0 antes de t0"""
    if T < t0:
        return 0.0
    return ease_out_back(pr(T, t0, t0 + dur), 2.2)


OUT = "#1c1a2e"
OUTC = hexc(OUT)
OW = 7  # grosor de contorno


def P(color, stroke=0, cap=True, alpha=None):
    p = skia.Paint(AntiAlias=True, Color=color if isinstance(color, int) else hexc(color))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap if cap else skia.Paint.kButt_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if alpha is not None:
        p.setAlphaf(clamp(alpha))
    return p


def path(points, close=True, smooth_curve=False):
    p = skia.Path()
    if not points:
        return p
    if smooth_curve and len(points) > 2:
        pts = points + ([points[0], points[1]] if close else [])
        p.moveTo(*_mid(pts[0], pts[1]))
        for i in range(1, len(pts) - 1):
            p.quadTo(*pts[i], *_mid(pts[i], pts[i + 1]))
        if not close:
            p.lineTo(*pts[-1])
    else:
        p.moveTo(*points[0])
        for q in points[1:]:
            p.lineTo(*q)
    if close:
        p.close()
    return p


def _mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def shape(c, pth, fill, ow=OW, oc=OUT, alpha=None):
    if fill is not None:
        c.drawPath(pth, P(fill, alpha=alpha))
    if ow:
        c.drawPath(pth, P(oc, ow, alpha=alpha))


def circle(c, x, y, r, fill, ow=OW, oc=OUT, alpha=None):
    if fill is not None:
        c.drawCircle(x, y, r, P(fill, alpha=alpha))
    if ow:
        c.drawCircle(x, y, r, P(oc, ow, alpha=alpha))


def ellipse(c, x, y, rx, ry, fill, ow=OW, oc=OUT, alpha=None):
    r = skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry)
    if fill is not None:
        c.drawOval(r, P(fill, alpha=alpha))
    if ow:
        c.drawOval(r, P(oc, ow, alpha=alpha))


def rrect(c, x, y, w, h, r, fill, ow=OW, oc=OUT, alpha=None):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    if fill is not None:
        c.drawRRect(rr, P(fill, alpha=alpha))
    if ow:
        c.drawRRect(rr, P(oc, ow, alpha=alpha))


def line(c, pts, w, color, ow=OW, oc=OUT, alpha=None):
    """trazo grueso con contorno (miembros, palos, trompa...)"""
    pth = path(pts, close=False)
    if ow:
        c.drawPath(pth, P(oc, w + 2 * ow, alpha=alpha))
    c.drawPath(pth, P(color, w, alpha=alpha))


def curve(pts, close=False):
    return path(pts, close=close, smooth_curve=True)


def glow(c, x, y, r, color, alpha=0.6):
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [hexc(color, int(255 * alpha)), hexc(color, 0)])
    p = skia.Paint(AntiAlias=True, Shader=sh)
    c.drawCircle(x, y, r, p)


def vgrad(c, rect, top, bottom, positions=None):
    cols = [hexc(x) if isinstance(x, str) else x for x in ([top, bottom] if not isinstance(top, list) else top)]
    sh = skia.GradientShader.MakeLinear([skia.Point(rect.left(), rect.top()), skia.Point(rect.left(), rect.bottom())],
                                        cols, positions)
    c.drawRect(rect, skia.Paint(Shader=sh))


def blur_paint(sigma, color, alpha=1.0):
    p = P(color, alpha=alpha)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    return p


def rot_pt(x, y, ang):
    a = math.radians(ang)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


def dirv(ang, ln):
    """vector de longitud ln; ang=0 hacia abajo, 90 hacia +x, 180 arriba"""
    a = math.radians(ang)
    return (math.sin(a) * ln, math.cos(a) * ln)


# ----------------------------------------------------------------- texto
_font_cache = {}


def font(size, alt=False):
    k = (size, alt)
    if k not in _font_cache:
        _font_cache[k] = skia.Font(TF_ALT if alt else TF_MAIN, size)
    return _font_cache[k]


def text(c, s, x, y, size, fill="#ffffff", stroke=OUT, sw=None, align="center", alt=False,
         shadow=True, rot=0.0, scale=1.0, alpha=1.0):
    if scale <= 0.001 or alpha <= 0.001:
        return 0
    f = font(int(size), alt)
    w = f.measureText(s)
    sw = sw if sw is not None else size * 0.2
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(scale, scale)
    tx = -w / 2 if align == "center" else (0 if align == "left" else -w)
    ty = size * 0.36
    if alpha < 1:
        c.saveLayerAlpha(None, int(255 * alpha))
    if shadow:
        c.drawString(s, tx + size * 0.05, ty + size * 0.09, f, P(stroke, sw))
        c.drawString(s, tx + size * 0.05, ty + size * 0.09, f, P(stroke))
    if sw:
        c.drawString(s, tx, ty, f, P(stroke, sw))
    c.drawString(s, tx, ty, f, P(fill))
    if alpha < 1:
        c.restore()
    c.restore()
    return w


def text_width(s, size, alt=False):
    return font(int(size), alt).measureText(s)


def callout(c, T, t0, s, x, y, size=110, fill="#ffffff", rot=-3, t1=None, wiggle=True, alt=False):
    """texto que aparece con rebote, se mece y desaparece"""
    if T < t0 or (t1 is not None and T > t1 + 0.25):
        return
    sc = pop(T, t0)
    if t1 is not None and T > t1:
        sc *= 1 - ease_in(pr(T, t1, t1 + 0.25))
    r = rot + (math.sin((T - t0) * 5) * 1.5 if wiggle else 0)
    text(c, s, x, y, size, fill, rot=r, scale=sc, alt=alt)


# ----------------------------------------------------------------- personajes
STYLES = {
    "hero": dict(skin="#f4c7a1", hair="#5b3a21", shirt="#f3f1ea", pants="#3d5f96", shoe="#2b2b36",
                 sleeve="#f3f1ea", torso_w=(72, 62), torso_h=168, thigh=100, shin=95, uarm=86, farm=80,
                 armw=30, legw=40, head_r=84, eye=(21, 25), neander=False),
    "neander": dict(skin="#c8956b", hair="#3a2414", shirt="#8b5a33", pants="#7a4c2b", shoe="#5a3a22",
                    sleeve=None, torso_w=(90, 78), torso_h=150, thigh=82, shin=78, uarm=82, farm=76,
                    armw=38, legw=46, head_r=80, eye=(14, 16), neander=True),
    "xray": dict(skin="#1d4d70", hair="#1d4d70", shirt="#1d4d70", pants="#1d4d70", shoe="#1d4d70",
                 sleeve="#1d4d70", torso_w=(72, 62), torso_h=168, thigh=100, shin=95, uarm=86, farm=80,
                 armw=30, legw=40, head_r=84, eye=(21, 25), neander=False, outline="#8ff3ff"),
    "shadow": dict(skin="#141226", hair="#141226", shirt="#141226", pants="#141226", shoe="#141226",
                   sleeve="#141226", torso_w=(72, 62), torso_h=168, thigh=100, shin=95, uarm=86, farm=80,
                   armw=30, legw=40, head_r=84, eye=(21, 25), neander=False, outline="#141226"),
}

COLD_SKIN = "#a9c4e6"


def person(c, x, y, s=1.0, style="hero", facing=1, lean=0.0, armA=(-14, -6), armB=(14, 6),
           legA=(-5, -3), legB=(5, 3), head_tilt=0.0, look=(0.0, 0.0), blink=0.0, mouth="neutral",
           mouth_open=0.5, brows=0.0, cold=0.0, frost=0.0, wet=0.0, shiver=0.0, T=0.0, sweat=0.0,
           holding=None, eyes_closed=False, blush=0.0, hold_belly=False):
    """Dibuja un personaje articulado. (x,y) = cadera. Ángulos: 0=abajo, 90=+x.
    armA/armB: (hombro, codo) relativos al torso; legA/legB absolutos."""
    st = STYLES[style]
    oc = st.get("outline", OUT)
    ow = OW
    if shiver:
        x += math.sin(T * 61) * 4 * shiver
        y += math.cos(T * 53) * 2 * shiver
    c.save()
    c.translate(x, y)
    c.scale(s * facing, s)
    skin = mixh(st["skin"], COLD_SKIN, cold * 0.8) if style in ("hero", "neander") else st["skin"]

    # piernas
    hipA, hipB = (-30, -8), (30, -8)
    for hip, lg in ((hipA, legA), (hipB, legB)):
        k = (hip[0] + dirv(lg[0], st["thigh"])[0], hip[1] + dirv(lg[0], st["thigh"])[1])
        f = (k[0] + dirv(lg[1], st["shin"])[0], k[1] + dirv(lg[1], st["shin"])[1])
        line(c, [hip, k, f], st["legw"], st["pants"], ow, oc)
        if st["neander"]:
            # envoltura de piel en los pies
            ellipse(c, f[0] + 12, f[1] + 4, 32, 18, st["shoe"], ow, oc)
        else:
            ellipse(c, f[0] + 14, f[1] + 6, 34, 18, st["shoe"], ow, oc)

    # torso (rota con lean)
    c.save()
    c.rotate(lean)
    tw1, tw0 = st["torso_w"]
    th = st["torso_h"]
    torso = skia.Path()
    torso.moveTo(-tw0, 0)
    torso.cubicTo(-tw0 - 6, -th * 0.5, -tw1 - 8, -th * 0.8, -tw1 + 10, -th)
    torso.lineTo(tw1 - 10, -th)
    torso.cubicTo(tw1 + 8, -th * 0.8, tw0 + 6, -th * 0.5, tw0, 0)
    torso.close()
    if st["neander"]:
        # túnica de piel con borde irregular
        tun = skia.Path()
        tun.moveTo(-tw0 - 4, 10)
        tun.cubicTo(-tw0 - 10, -th * 0.5, -tw1 - 8, -th * 0.8, -tw1 + 10, -th)
        tun.lineTo(tw1 - 10, -th)
        tun.cubicTo(tw1 + 8, -th * 0.8, tw0 + 10, -th * 0.5, tw0 + 4, 10)
        n = 9
        for i in range(n + 1):
            xx = tw0 + 4 - (2 * tw0 + 8) * i / n
            tun.lineTo(xx, 10 + (22 if i % 2 else 0))
        tun.close()
        shape(c, tun, st["shirt"], ow, oc)
        for i in range(6):
            fx = -tw0 + 20 + i * (2 * tw0 - 40) / 5
            c.drawPath(path([(fx, -th * 0.2 - (i % 2) * 30), (fx + 8, -th * 0.2 - (i % 2) * 30 + 22)], False),
                       P("#6b4224", 5))
    else:
        shape(c, torso, st["shirt"], ow, oc)
        if style == "hero":
            # cuello de la camiseta
            c.drawPath(curve([(-26, -th + 2), (0, -th + 26), (26, -th + 2)]), P(oc, 5))
            # cinturón/pantalón
            band = skia.Path()
            band.addRect(skia.Rect.MakeLTRB(-tw0 + 2, -14, tw0 - 2, 6))
            c.drawPath(band, P(st["pants"]))
            c.drawLine(-tw0 + 2, -14, tw0 - 2, -14, P(oc, 5))
    # humedad / sudor absorbido
    if wet > 0 and style == "hero":
        c.save()
        c.clipPath(torso, doAntiAlias=True)
        for i, (wx, wy, wr) in enumerate([(-30, -60, 40), (25, -110, 34), (10, -40, 30), (-15, -130, 26)]):
            c.drawCircle(wx, wy, wr * clamp(wet * 1.4 - i * 0.12) * 1.3, blur_paint(6, "#b9b4a8", 0.8))
        c.restore()
    # escarcha
    if frost > 0 and style == "hero":
        c.save()
        c.clipPath(torso, doAntiAlias=True)
        rnd = random.Random(7)
        for i in range(14):
            fx, fy = rnd.uniform(-tw1, tw1), rnd.uniform(-th, 0)
            if rnd.random() > frost:
                continue
            fr = rnd.uniform(12, 26) * frost
            c.drawCircle(fx, fy, fr * 1.6, blur_paint(8, "#d8f0ff", 0.85))
            snowflake(c, fx, fy, fr, "#ffffff", 3)
        c.restore()
        shape(c, torso, None, ow, oc)

    # cabeza
    hr = st["head_r"]
    neck_y = -th
    c.save()
    c.translate(0, neck_y - hr * 0.82)
    c.rotate(head_tilt)
    _head(c, st, hr, skin, look, blink, mouth, mouth_open, brows, cold, T, sweat, oc, eyes_closed, blush, style)
    c.restore()

    # brazos (relativos al torso)
    for side, arm in ((-1, armA), (1, armB)):
        sh = (side * (tw1 - 6), -th + 18)
        a1, a2 = arm[0], arm[1]
        e = (sh[0] + dirv(a1, st["uarm"])[0], sh[1] + dirv(a1, st["uarm"])[1])
        h = (e[0] + dirv(a2, st["farm"])[0], e[1] + dirv(a2, st["farm"])[1])
        line(c, [sh, e, h], st["armw"], skin, ow, oc)
        if st["sleeve"]:
            m = (sh[0] + dirv(a1, st["uarm"] * 0.55)[0], sh[1] + dirv(a1, st["uarm"] * 0.55)[1])
            line(c, [sh, m], st["armw"] + 12, st["sleeve"], ow, oc)
            if frost > 0 and style == "hero":
                c.drawCircle(*m, 10 * frost, P("#ffffff", alpha=0.8))
        circle(c, h[0], h[1], st["armw"] * 0.62, skin, ow, oc)
        if holding and side == holding[0]:
            holding[1](c, h[0], h[1], a1, a2)
    c.restore()  # torso
    c.restore()


def _head(c, st, hr, skin, look, blink, mouth, mo, brows, cold, T, sweat, oc, eyes_closed, blush, style):
    ow = OW
    # orejas
    circle(c, -hr * 0.95, 8, hr * 0.2, skin, ow, oc)
    circle(c, hr * 0.95, 8, hr * 0.2, skin, ow, oc)
    if st["neander"]:
        # pelo largo detrás
        back = curve([(-hr * 1.1, -10), (-hr * 1.2, hr * 0.9), (-hr * 0.4, hr * 0.5), (hr * 0.4, hr * 0.5),
                      (hr * 1.2, hr * 0.9), (hr * 1.1, -10), (0, -hr * 1.25)], close=True)
        shape(c, back, st["hair"], ow, oc)
    ellipse(c, 0, 0, hr, hr * 0.98, skin, ow, oc)
    # pelo
    hp = skia.Path()
    if st["neander"]:
        hp.moveTo(-hr * 1.02, -6)
        hp.cubicTo(-hr * 1.15, -hr * 1.1, hr * 1.15, -hr * 1.1, hr * 1.02, -6)
        for i in range(8):
            xx = hr * 1.02 - (2.04 * hr) * (i + 1) / 8
            hp.lineTo(xx + hr * 0.12, -hr * 0.42 + (12 if i % 2 else -6))
            hp.lineTo(xx, -hr * 0.5)
        hp.close()
    else:
        hp.moveTo(-hr * 1.02, 0)
        hp.cubicTo(-hr * 1.12, -hr * 1.05, hr * 0.9, -hr * 1.35, hr * 1.04, -hr * 0.12)
        hp.cubicTo(hr * 0.8, -hr * 0.55, hr * 0.4, -hr * 0.6, hr * 0.1, -hr * 0.48)
        hp.cubicTo(-hr * 0.3, -hr * 0.62, -hr * 0.7, -hr * 0.4, -hr * 0.82, -hr * 0.05)
        hp.close()
    shape(c, hp, st["hair"], ow, oc)

    ex, ey = hr * 0.36, -hr * 0.05
    erx, ery = st["eye"]
    if style in ("xray", "shadow"):
        if style == "shadow":
            return
    # rubor / nariz fría
    if (cold > 0.3 or blush > 0) and style == "hero":
        a = max(cold - 0.3, blush)
        circle(c, -ex - 10, hr * 0.3, 16, "#ff7a8a", 0, alpha=0.5 * a)
        circle(c, ex + 10, hr * 0.3, 16, "#ff7a8a", 0, alpha=0.5 * a)
    lx, ly = look
    bl = clamp(blink)
    for sx in (-1, 1):
        cx = sx * ex
        if eyes_closed or bl > 0.92:
            c.drawPath(curve([(cx - erx, ey), (cx, ey + 9), (cx + erx, ey)]), P(oc, 6))
        else:
            ry = ery * (1 - bl)
            ellipse(c, cx, ey, erx, ry, "#ffffff", 5, oc)
            px, py = cx + lx * erx * 0.45, ey + ly * ry * 0.4
            c.save()
            c.clipRect(skia.Rect.MakeLTRB(cx - erx, ey - ry, cx + erx, ey + ry))
            circle(c, px, py, erx * 0.5, "#1c1a2e", 0)
            circle(c, px + 3, py - 4, erx * 0.16, "#ffffff", 0)
            c.restore()
    # cejas
    bw = 5 if not st["neander"] else 0
    if st["neander"]:
        ridge = curve([(-hr * 0.7, -hr * 0.22), (0, -hr * 0.36), (hr * 0.7, -hr * 0.22)])
        c.drawPath(ridge, P(oc, 26))
        c.drawPath(ridge, P(mixh(st["skin"], "#000000", 0.15), 14))
    else:
        for sx in (-1, 1):
            cx = sx * ex
            y0 = ey - ery - 16
            ix, ox = cx - sx * erx * 0.9, cx + sx * erx * 0.9
            c.drawLine(ox, y0 + 5 * brows, ix, y0 - 13 * brows, P(oc, 7))
    # nariz
    nose_col = mixh(skin, "#ff6b6b", 0.6 * clamp(cold * 1.5 - 0.3)) if style == "hero" else skin
    if st["neander"]:
        ellipse(c, 0, hr * 0.14, hr * 0.2, hr * 0.15, nose_col, 5, oc)
    else:
        ellipse(c, 0, hr * 0.15, hr * 0.12, hr * 0.1, nose_col, 5, oc)
    # boca
    my = hr * 0.48
    if mouth == "smile":
        c.drawPath(curve([(-hr * 0.3, my - 8), (0, my + 16), (hr * 0.3, my - 8)]), P(oc, 7))
    elif mouth == "neutral":
        c.drawLine(-hr * 0.18, my, hr * 0.18, my, P(oc, 7))
    elif mouth == "worried":
        c.drawPath(curve([(-hr * 0.28, my + 6), (-hr * 0.1, my - 6), (hr * 0.1, my + 4), (hr * 0.28, my - 4)]), P(oc, 7))
    elif mouth == "sad":
        c.drawPath(curve([(-hr * 0.26, my + 10), (0, my - 8), (hr * 0.26, my + 10)]), P(oc, 7))
    elif mouth in ("o", "scream"):
        rx = hr * (0.12 + 0.12 * mo) * (1.6 if mouth == "scream" else 1)
        ry = hr * (0.1 + 0.2 * mo) * (1.4 if mouth == "scream" else 1)
        ellipse(c, 0, my + 4, rx, ry, "#5a1e2c", 6, oc)
        if mouth == "scream":
            ellipse(c, 0, my + 4 + ry * 0.5, rx * 0.6, ry * 0.35, "#e86a7c", 0)
    elif mouth == "grit":
        wv = hr * 0.32
        rrect(c, -wv, my - 12, 2 * wv, 26, 10, "#ffffff", 6, oc)
        c.drawLine(-wv + 4, my + 1 + math.sin(T * 50) * 2, wv - 4, my + 1 - math.sin(T * 50) * 2, P(oc, 4))
    if st["neander"]:
        beard = skia.Path()
        beard.moveTo(-hr * 0.9, hr * 0.1)
        beard.cubicTo(-hr * 0.9, hr * 1.3, hr * 0.9, hr * 1.3, hr * 0.9, hr * 0.1)
        beard.cubicTo(hr * 0.6, hr * 0.62, hr * 0.3, hr * 0.32, 0, hr * 0.34)
        beard.cubicTo(-hr * 0.3, hr * 0.32, -hr * 0.6, hr * 0.62, -hr * 0.9, hr * 0.1)
        shape(c, beard, st["hair"], ow, oc)
        if mouth in ("smile", "neutral"):
            c.drawLine(-hr * 0.15, my + 6, hr * 0.15, my + 6, P(oc, 6))
    if sweat > 0:
        sy = -hr * 0.3 + ((T * 1.5) % 1) * hr * 0.5
        drop(c, hr * 0.8, sy, 13 * sweat, "#9fd8ff")


def drop(c, x, y, r, color="#8fd3ff", ow=5):
    p = skia.Path()
    p.moveTo(x, y - r * 2.1)
    p.cubicTo(x + r * 0.4, y - r * 1.2, x + r, y - r * 0.6, x + r, y)
    p.cubicTo(x + r, y + r * 1.1, x - r, y + r * 1.1, x - r, y)
    p.cubicTo(x - r, y - r * 0.6, x - r * 0.4, y - r * 1.2, x, y - r * 2.1)
    p.close()
    shape(c, p, color, ow)
    circle(c, x - r * 0.35, y - r * 0.2, r * 0.25, "#ffffff", 0)


def walk(phase, amp=24, arm=22):
    s = math.sin(phase)
    knee = 12 * max(0, math.cos(phase))
    knee2 = 12 * max(0, -math.cos(phase))
    return dict(legA=(-amp * s, -amp * s - knee), legB=(amp * s, amp * s - knee2),
                armA=(arm * s - 6, arm * s + 6), armB=(-arm * s + 6, -arm * s + 14))


def run(phase, amp=42):
    s = math.sin(phase)
    return dict(legA=(amp * s + 8, amp * s - 30 * max(0, -s) - 20), legB=(-amp * s + 8, -amp * s - 30 * max(0, s) - 20),
                armA=(-40 * s + 10, -40 * s + 80), armB=(40 * s + 10, 40 * s + 80), lean=14)


def bob(phase, a=8):
    return -abs(math.sin(phase)) * a


# ----------------------------------------------------------------- animales
def mammoth(c, x, y, s, phase, facing=-1, sway=0.0, T=0.0, eye_look=0):
    """Mamut lanudo. (x,y)=suelo bajo el cuerpo. facing=1 cabeza a la derecha."""
    c.save()
    c.translate(x, y)
    c.scale(s * facing, s)
    fur, fur_d, fur_l = "#7b4a2b", "#5c361e", "#9a6640"

    def leg(lx, off, col):
        a = 13 * math.sin(phase + off)
        lift = max(0, math.sin(phase + off + math.pi / 2)) * 16
        c.save()
        c.translate(lx, -235)
        c.rotate(a)
        rrect(c, -40, 0, 80, 238 - lift, 32, col)
        for k in (-22, 0, 22):
            ellipse(c, k, 232 - lift, 12, 8, "#e8dcc6", 4)
        c.restore()

    leg(-150, math.pi, fur_d)
    leg(135, 0, fur_d)
    # cola
    line(c, [(-265, -360), (-300, -300), (-305, -250)], 16, fur_d)
    ellipse(c, -305, -240, 16, 24, fur_d)
    # cuerpo
    b = skia.Path()
    b.moveTo(-275, -300)
    b.cubicTo(-290, -470, -120, -540, 60, -525)
    b.cubicTo(180, -515, 265, -470, 290, -380)
    b.lineTo(285, -250)
    n = 16
    for i in range(n + 1):
        xx = 285 - 560 * i / n
        b.lineTo(xx, -205 + (30 if i % 2 else 0))
    b.close()
    shape(c, b, fur)
    for i in range(9):
        fx = -200 + i * 50
        fy = -420 + (i % 3) * 50
        c.drawPath(curve([(fx, fy), (fx + 14, fy + 22), (fx + 6, fy + 44)]), P(fur_d, 6))
    leg(-110, math.pi * 0.0 + 1.0, fur)
    leg(170, math.pi + 1.0, fur)
    # colmillo lejano
    tusk = lambda o: line(c, [(355, -330), (420 + o, -250), (500 + o, -260), (540 + o, -330)], 24, "#f6efdc")
    tusk(-25)
    # cabeza
    circle(c, 300, -420, 112, fur)
    circle(c, 268, -510, 70, fur, 0)
    c.drawPath(curve([(205, -490), (240, -578), (320, -560), (350, -480)]), P(OUT, OW))
    ellipse(c, 235, -420, 42, 62, fur_d)
    # trompa
    sw = math.sin(T * 1.6) * 0.6 + sway
    line(c, [(375, -380), (410, -300), (415 + sw * 25, -200), (395 + sw * 45, -120), (360 + sw * 55, -100)], 52, fur_l)
    for k in range(4):
        yy = -300 + k * 50
        c.drawLine(390 + sw * 10 * k, yy, 430 + sw * 12 * k, yy + 6, P(fur_d, 5))
    tusk(15)
    # ojo
    circle(c, 335 + eye_look * 4, -445, 12, "#1c1a2e", 0)
    circle(c, 339, -449, 4, "#ffffff", 0)
    c.drawLine(318, -470, 352, -466, P(OUT, 6))
    c.restore()


def wolf(c, x, y, s, phase=0.0, mode="stand", facing=1, T=0.0, glow_eyes=False, sniff=0.0,
         color="#8c96a6", belly="#d6dbe4", deer=False, howl=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s * facing, s)
    dark = mixh(color, "#000000", 0.25)
    legl = 120 if deer else 95
    body_y = -legl - 22
    if mode == "run":
        sp = math.sin(phase)
        angs = [(40 * sp, 40 * sp - 30), (-40 * sp, -40 * sp - 20), (-45 * sp, -45 * sp + 25), (45 * sp, 45 * sp + 15)]
        body_y += math.sin(phase * 2) * 6
    else:
        angs = [(4, 0), (-4, 0), (-6, 0), (6, 0)]
    xs = [-62, -42, 52, 72]
    # patas traseras/lejanas
    for i in (1, 3):
        a1, a2 = angs[i]
        k = (xs[i] + dirv(a1, legl * 0.5)[0], body_y + 30 + dirv(a1, legl * 0.5)[1])
        f = (k[0] + dirv(a2, legl * 0.55)[0], k[1] + dirv(a2, legl * 0.55)[1])
        line(c, [(xs[i], body_y + 30), k, f], 18, dark, 6)
    # cola
    if deer:
        ellipse(c, -100, body_y - 20, 14, 18, "#f2e6d0", 5)
    else:
        tail = curve([(-90, body_y - 10), (-150, body_y - 30 + math.sin(T * 6) * 8), (-185, body_y + 10)])
        c.drawPath(tail, P(OUT, 40))
        c.drawPath(tail, P(color, 28))
    ellipse(c, 0, body_y, 105, 48, color, 6)
    ellipse(c, 10, body_y + 22, 70, 20, belly, 0)
    for i in (0, 2):
        a1, a2 = angs[i]
        k = (xs[i] + dirv(a1, legl * 0.5)[0], body_y + 30 + dirv(a1, legl * 0.5)[1])
        f = (k[0] + dirv(a2, legl * 0.55)[0], k[1] + dirv(a2, legl * 0.55)[1])
        line(c, [(xs[i], body_y + 30), k, f], 18, color, 6)
    # cuello y cabeza
    hx, hy = 112, body_y - 40
    hy += sniff * 30 + (math.sin(T * 14) * 3 if sniff else 0)
    hx += sniff * 14
    c.save()
    c.translate(hx, hy)
    c.rotate(-howl * 45 + sniff * 18)
    line(c, [(-40, 30), (-10, 0)], 50, color, 6)
    if deer:
        for sx in (-1, 1):
            line(c, [(-5 + sx * 6, -30), (-15 + sx * 10, -90), (-45 + sx * 10, -120)], 8, "#8a6440", 5)
            line(c, [(-12 + sx * 10, -70), (20 + sx * 8, -100)], 7, "#8a6440", 5)
    head = skia.Path()
    head.moveTo(-36, -10)
    head.cubicTo(-36, -50, 20, -52, 30, -24)
    head.lineTo(78, -6 + sniff * 2)
    head.cubicTo(86, 2, 80, 16, 66, 16)
    head.lineTo(10, 26)
    head.cubicTo(-20, 30, -36, 20, -36, -10)
    head.close()
    ears = [(-18, -34), (6, -38)]
    for ex, ey in ears:
        shape(c, path([(ex - 14, ey + 8), (ex - 4, ey - 34), (ex + 12, ey + 6)]), dark if not deer else color, 6)
    shape(c, head, color, 6)
    ellipse(c, 76, -2 + math.sin(T * 30) * sniff * 2, 10, 8, "#1c1a2e", 0)
    if glow_eyes:
        glow(c, 22, -16, 40, "#ffd23f", 0.8)
        ellipse(c, 22, -16, 10, 6, "#fff4a0", 3)
    else:
        circle(c, 22, -16, 7, "#1c1a2e", 0)
        circle(c, 24, -18, 2.5, "#ffffff", 0)
    if howl > 0.3:
        ellipse(c, 60, 14, 14, 10 * howl, "#5a1e2c", 4)
    c.restore()
    c.restore()


def bear(c, x, y, s, rise=1.0, roar=0.0, T=0.0):
    """oso cavernario de pie, vista frontal. (x,y)=suelo"""
    c.save()
    c.translate(x, y)
    sy = lerp(0.52, 1.0, smooth(rise))
    c.scale(s * lerp(1.12, 1.0, rise), s * sy)
    fur, fur_d, fur_l = "#6b4026", "#4d2c18", "#a8774e"
    breathe = math.sin(T * 3) * 4
    ellipse(c, -70, -45, 58, 60, fur_d)
    ellipse(c, 70, -45, 58, 60, fur_d)
    for sx in (-1, 1):
        for k in (-20, 0, 20):
            ellipse(c, sx * 70 + k, -2, 9, 7, "#efe4cc", 3)
    # brazos
    up = smooth(rise)
    for sx in (-1, 1):
        a1 = sx * lerp(25, 135, up) + sx * roar * 10
        a2 = sx * lerp(15, 165, up)
        shp = (sx * 110, -380)
        e = (shp[0] + dirv(a1, 130)[0], shp[1] + dirv(a1, 130)[1])
        h = (e[0] + dirv(a2, 110)[0], e[1] + dirv(a2, 110)[1])
        line(c, [shp, e, h], 70, fur_d)
        circle(c, h[0], h[1], 42, fur_d)
        for k in (-1, 0, 1):
            cx, cy = h[0] + k * 20, h[1] - (34 if up > 0.5 else -34)
            shape(c, path([(cx - 6, cy), (cx, cy - (26 if up > 0.5 else -26)), (cx + 6, cy)]), "#f4ecd8", 3)
    body = curve([(0, -540), (150, -470), (175, -260), (130, -60), (0, -40), (-130, -60), (-175, -260),
                  (-150, -470)], close=True)
    c.save()
    c.translate(0, breathe)
    shape(c, body, fur)
    ellipse(c, 0, -230, 95, 130, fur_l, 0)
    for i in range(6):
        fx = -60 + (i % 3) * 60
        fy = -330 + (i // 3) * 140
        c.drawPath(curve([(fx, fy), (fx + 10, fy + 20), (fx + 2, fy + 40)]), P(fur_d, 5))
    # cabeza
    hy = -560 - roar * 10
    circle(c, -80, hy - 70, 34, fur)
    circle(c, 80, hy - 70, 34, fur)
    circle(c, -80, hy - 70, 16, fur_d, 0)
    circle(c, 80, hy - 70, 16, fur_d, 0)
    circle(c, 0, hy, 105, fur)
    ellipse(c, 0, hy + 40, 58, 46 + roar * 18, fur_l)
    ellipse(c, 0, hy + 14, 22, 15, "#1c1a2e", 0)
    if roar > 0.05:
        ellipse(c, 0, hy + 62, 34, 10 + roar * 32, "#5a1e2c", 5)
        for sx in (-1, 1):
            shape(c, path([(sx * 22, hy + 62 - roar * 30), (sx * 14, hy + 62 - roar * 12), (sx * 6, hy + 62 - roar * 30)]),
                  "#ffffff", 3)
    else:
        c.drawPath(curve([(-20, hy + 55), (0, hy + 62), (20, hy + 55)]), P(OUT, 6))
    for sx in (-1, 1):
        circle(c, sx * 42, hy - 22, 11, "#1c1a2e", 0)
        circle(c, sx * 42 + 3, hy - 25, 3.5, "#ffffff", 0)
        c.drawLine(sx * 22, hy - 44 + roar * 6, sx * 62, hy - 52 - roar * 4, P(OUT, 8))
    c.restore()
    c.restore()


# ----------------------------------------------------------------- escenario
def pine(c, x, y, h, col="#2e5e52", snow=True, sway=0.0, ow=OW, oc=OUT):
    w = h * 0.42
    line(c, [(x, y), (x, y - h * 0.2)], h * 0.07, "#5b3a22", ow, oc)
    for i in range(3):
        ty = y - h * 0.15 - i * h * 0.27
        tw = w * (1 - i * 0.26)
        top = (x + sway * (i + 1) * 3, ty - h * 0.42)
        p = path([(x - tw, ty), top, (x + tw, ty)])
        shape(c, p, col, ow, oc)
        if snow:
            sp = skia.Path()
            sp.moveTo(top[0], top[1])
            sp.lineTo(top[0] + tw * 0.42, ty - h * 0.42 * 0.55)
            for k in range(4):
                fx = top[0] + tw * 0.42 - (tw * 0.84) * (k + 1) / 4
                sp.lineTo(fx + tw * 0.1, ty - h * 0.42 * 0.5 + (10 if k % 2 else 0))
                sp.lineTo(fx, ty - h * 0.42 * 0.55)
            sp.close()
            shape(c, sp, "#f4f9ff", 5, oc)


def mountains(c, seed, base, height, col, x0=-1600, x1=2800, snow=True, ow=OW, oc=OUT, peaks=7):
    rnd = random.Random(seed)
    pts = [(x0, base)]
    n = peaks
    step = (x1 - x0) / n
    tops = []
    for i in range(n):
        px = x0 + step * (i + 0.5) + rnd.uniform(-step * 0.2, step * 0.2)
        ph = base - height * rnd.uniform(0.55, 1.0)
        vx = x0 + step * (i + 1)
        vy = base - height * rnd.uniform(0.15, 0.35)
        pts.append((px, ph))
        tops.append((px, ph, step))
        pts.append((vx, vy))
    pts.append((x1, base))
    pts.append((x1, base + 3000))
    pts.append((x0, base + 3000))
    shape(c, path(pts), col, ow, oc)
    if snow:
        for px, ph, stp in tops:
            dh = (base - ph) * 0.3
            sl = stp * 0.5 * 0.42
            cap = [(px, ph), (px + sl, ph + dh)]
            for k in range(4):
                cx = px + sl - 2 * sl * (k + 1) / 4
                cap.append((cx + sl * 0.25, ph + dh * (0.75 if k % 2 else 1.15)))
                cap.append((cx, ph + dh))
            shape(c, path(cap), "#f4f9ff", 5, oc)


def ground(c, y, col_top="#f4f9ff", col_bot="#cfe1f3", x0=-2000, x1=3200, wav=30, seed=1, ow=OW, oc=OUT):
    rnd = random.Random(seed)
    pts = []
    n = 14
    ph = rnd.uniform(0, 6)
    for i in range(n + 1):
        xx = x0 + (x1 - x0) * i / n
        pts.append((xx, y + math.sin(i * 0.9 + ph) * wav))
    pth = curve(pts, close=False)
    pth.lineTo(x1, y + 4000)
    pth.lineTo(x0, y + 4000)
    pth.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(0, y - wav), skia.Point(0, y + 900)], [hexc(col_top), hexc(col_bot)])
    c.drawPath(pth, skia.Paint(AntiAlias=True, Shader=sh))
    if ow:
        c.drawPath(curve(pts, close=False), P(oc, ow))


def snowfall(c, T, n=90, wind=0.0, speed=180, seed=3, size=(3, 9), alpha=0.95, streak=0.0, col="#ffffff"):
    """copos en espacio de pantalla"""
    rnd = random.Random(seed)
    p = P(col, alpha=alpha)
    ps = P(col, 3, alpha=alpha * 0.7)
    for i in range(n):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        sz = rnd.uniform(*size)
        sp = speed * (0.6 + sz / size[1] * 0.6)
        xx = (x0 + wind * sp * T + math.sin(T * 1.3 + i) * 18) % (W + 100) - 50
        yy = (y0 + sp * T) % (H + 100) - 50
        if streak > 0:
            ps.setStrokeWidth(sz * 0.8)
            c.drawLine(xx, yy, xx - wind * streak * sz * 8, yy - streak * sz * 8 / max(0.3, abs(wind) + 0.3), ps)
        else:
            c.drawCircle(xx, yy, sz, p)


def snowflake(c, x, y, r, col="#ffffff", w=4, rot=0.0):
    p = P(col, w)
    for k in range(6):
        a = math.radians(rot + k * 60)
        ex, ey = x + math.cos(a) * r, y + math.sin(a) * r
        c.drawLine(x, y, ex, ey, p)
        for f in (0.55,):
            mx, my = x + math.cos(a) * r * f, y + math.sin(a) * r * f
            for d in (-40, 40):
                b = a + math.radians(d)
                c.drawLine(mx, my, mx + math.cos(b) * r * 0.35, my + math.sin(b) * r * 0.35, p)


def wind_lines(c, T, n=10, speed=1800, seed=5, alpha=0.6, y0=0, y1=H, col="#ffffff"):
    rnd = random.Random(seed)
    for i in range(n):
        yy = rnd.uniform(y0, y1)
        ln = rnd.uniform(140, 320)
        ph = rnd.uniform(0, 3)
        xx = ((T + ph) * speed * rnd.uniform(0.7, 1.2)) % (W + ln * 3) - ln
        a = alpha * math.sin(clamp(((T + ph) * 1.7) % 1) * math.pi)
        pth = curve([(xx, yy), (xx + ln * 0.5, yy - 14), (xx + ln, yy + 4)])
        c.drawPath(pth, P(col, 6, alpha=a))


def sky(c, top, bot, mid=None):
    rect = skia.Rect.MakeWH(W, H)
    if mid:
        vgrad(c, rect, [hexc(top), hexc(mid), hexc(bot)], None, [0, 0.55, 1])
    else:
        vgrad(c, rect, top, bot)


def vignette(c, color="#000000", strength=0.6, r=None):
    r = r or H * 0.75
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), r,
                                        [hexc(color, 0), hexc(color, 0), hexc(color, int(255 * clamp(strength)))],
                                        [0, 0.55, 1])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))


def fire(c, x, y, s, T, logs=True, intensity=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    glow(c, 0, -60, 330 * intensity, "#ff9a3c", 0.45)
    if logs:
        line(c, [(-90, 10), (90, -15)], 30, "#6b4226")
        line(c, [(-90, -15), (90, 10)], 30, "#7c4e2c")
    layers = [("#e8452c", 1.0, 0), ("#ff9a2e", 0.72, 1.3), ("#ffe36b", 0.42, 2.7)]
    for col, k, ph in layers:
        hgt = 230 * k * intensity
        wdt = 95 * k
        pts = [(-wdt, 0)]
        for j in range(5):
            a = j / 4
            fx = -wdt + 2 * wdt * a
            tip = (0.55 + 0.45 * math.sin(a * math.pi)) * hgt
            tip *= 1 + 0.18 * noise(T * 6 + j * 2 + ph, j)
            pts.append((fx * 0.8 + noise(T * 4, j + ph) * 10, -tip * (0.6 + 0.4 * (j % 2 == 0))))
        pts.append((wdt, 0))
        pts.append((wdt * 0.6, 22))
        pts.append((-wdt * 0.6, 22))
        shape(c, curve(pts, close=True), col, 6 if k == 1.0 else 0)
    rnd = random.Random(2)
    for i in range(10):
        ph = rnd.uniform(0, 1)
        sp = ((T * 0.8 + ph) % 1)
        sx = rnd.uniform(-80, 80) + math.sin(T * 3 + i) * 20
        circle(c, sx, -80 - sp * 320 * intensity, 6 * (1 - sp), "#ffd166", 0, alpha=1 - sp)
    c.restore()


def thermometer(c, x, y, s, value, vmin=-50, vmax=40, label=True, T=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    rrect(c, -40, -420, 80, 440, 40, "#ffffff")
    circle(c, 0, 40, 62, "#ffffff")
    f = clamp((value - vmin) / (vmax - vmin))
    col = mixh("#3aa0ff", "#ff3b3b", f)
    rrect(c, -18, -400 + 380 * (1 - f), 36, 380 * f + 40, 18, col, 0)
    circle(c, 0, 40, 44, col, 0)
    for i in range(9):
        yy = -380 + i * 42
        c.drawLine(18, yy, 36, yy, P(OUT, 5))
    circle(c, -10, 28, 12, "#ffffff", 0, alpha=0.6)
    c.restore()
    if label:
        text(c, "%d°C" % round(value), x, y + 150 * s, 92 * s, "#bfe6ff" if value < 0 else "#ffd1a1")


def battery(c, x, y, s, level, T=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    rrect(c, -40, -230, 80, 30, 10, "#d9d9d9")
    rrect(c, -90, -205, 180, 410, 30, "#ffffff")
    col = mixh("#ff3b3b", "#44d36b", clamp((level - 0.15) / 0.6))
    blink = level < 0.3 and int(T * 6) % 2 == 0
    if not blink:
        hh = 370 * clamp(level)
        rrect(c, -70, 185 - hh, 140, hh, 18, col, 0)
    shape(c, path([(10, -110), (-35, 15), (0, 15), (-15, 110), (40, -20), (5, -20), (25, -110)]), "#ffe14a", 5)
    c.restore()


def red_x(c, x, y, r, p, w=34):
    if p <= 0:
        return
    pa = clamp(p * 2)
    pb = clamp(p * 2 - 1)
    pnt_o = P(OUT, w + 16)
    pnt = P("#ff3344", w)
    for (x0, y0, x1, y1, q) in ((x - r, y - r, x + r, y + r, pa), (x + r, y - r, x - r, y + r, pb)):
        if q > 0:
            c.drawLine(x0, y0, lerp(x0, x1, q), lerp(y0, y1, q), pnt_o)
    for (x0, y0, x1, y1, q) in ((x - r, y - r, x + r, y + r, pa), (x + r, y - r, x - r, y + r, pb)):
        if q > 0:
            c.drawLine(x0, y0, lerp(x0, x1, q), lerp(y0, y1, q), pnt)


def check(c, x, y, r, p, w=30):
    if p <= 0:
        return
    pts = [(x - r, y), (x - r * 0.3, y + r * 0.7), (x + r, y - r * 0.8)]
    q = clamp(p)
    if q < 0.4:
        e = (lerp(pts[0][0], pts[1][0], q / 0.4), lerp(pts[0][1], pts[1][1], q / 0.4))
        seg = [pts[0], e]
    else:
        k = (q - 0.4) / 0.6
        seg = [pts[0], pts[1], (lerp(pts[1][0], pts[2][0], k), lerp(pts[1][1], pts[2][1], k))]
    line(c, seg, w, "#3ddc6e", 8)


def skull(c, x, y, r, col="#ffffff"):
    c.save()
    c.translate(x, y)
    circle(c, 0, -r * 0.15, r, col)
    rrect(c, -r * 0.55, r * 0.45, r * 1.1, r * 0.55, r * 0.15, col)
    circle(c, 0, -r * 0.15, r * 0.95, col, 0)
    ellipse(c, -r * 0.4, -r * 0.1, r * 0.26, r * 0.3, OUT, 0)
    ellipse(c, r * 0.4, -r * 0.1, r * 0.26, r * 0.3, OUT, 0)
    shape(c, path([(0, r * 0.18), (-r * 0.12, r * 0.38), (r * 0.12, r * 0.38)]), OUT, 0)
    for k in (-1, 0, 1):
        c.drawLine(k * r * 0.25, r * 0.6, k * r * 0.25, r * 0.95, P(OUT, 6))
    c.restore()


def spear(c, x, y, ln, ang, ow=OW):
    """lanza desde (x,y) en dirección ang (0=abajo)"""
    tip = (x + dirv(ang, ln)[0], y + dirv(ang, ln)[1])
    line(c, [(x, y), tip], 14, "#8a5b33", ow)
    a = math.radians(ang)
    dx, dy = math.sin(a), math.cos(a)
    px, py = -dy, dx
    pts = [(tip[0] + px * 18, tip[1] + py * 18), (tip[0] + dx * 60, tip[1] + dy * 60), (tip[0] - px * 18, tip[1] - py * 18)]
    shape(c, path(pts), "#9aa3ad", 6)
    c.drawLine(tip[0] - dx * 10 + px * 12, tip[1] - dy * 10 + py * 12, tip[0] - dx * 10 - px * 12,
               tip[1] - dy * 10 - py * 12, P("#c79a5c", 8))


def meat(c, x, y, s, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    line(c, [(60, 40), (140, 110)], 30, "#f4ecd8")
    circle(c, 145, 100, 20, "#f4ecd8")
    circle(c, 130, 120, 20, "#f4ecd8")
    m = curve([(-90, -40), (-30, -110), (60, -80), (100, 10), (60, 70), (-40, 70), (-100, 30)], close=True)
    shape(c, m, "#c8553d")
    c.drawPath(curve([(-60, -30), (-10, -70), (50, -50)]), P("#f6c7a0", 14))
    c.drawPath(curve([(-50, 20), (0, 0), (50, 20)]), P("#f6c7a0", 10))
    circle(c, -40, -60, 10, "#ffffff", 0, alpha=0.6)
    c.restore()


def stopwatch(c, x, y, r, ang):
    circle(c, x, y - r - 18, 22, "#d0d6de")
    rrect(c, x - 14, y - r - 30, 28, 30, 6, "#d0d6de")
    circle(c, x, y, r, "#ffffff", 9)
    circle(c, x, y, r * 0.84, None, 4)
    for k in range(12):
        a = math.radians(k * 30)
        c.drawLine(x + math.sin(a) * r * 0.7, y - math.cos(a) * r * 0.7, x + math.sin(a) * r * 0.8,
                   y - math.cos(a) * r * 0.8, P(OUT, 5))
    a = math.radians(ang)
    c.drawLine(x, y, x + math.sin(a) * r * 0.72, y - math.cos(a) * r * 0.72, P("#ff3344", 9))
    circle(c, x, y, 10, OUT, 0)


def moon(c, x, y, r, col="#fff3c4"):
    glow(c, x, y, r * 2.6, col, 0.35)
    circle(c, x, y, r, col, 6)
    circle(c, x - r * 0.3, y - r * 0.2, r * 0.18, mixh(col, "#c9b98a", 0.5), 0)
    circle(c, x + r * 0.35, y + r * 0.3, r * 0.12, mixh(col, "#c9b98a", 0.5), 0)


def stars(c, alpha, seed=11, n=70, y1=1100):
    if alpha <= 0:
        return
    rnd = random.Random(seed)
    for i in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, y1)
        r = rnd.uniform(1.5, 4.5)
        circle(c, x, y, r, "#ffffff", 0, alpha=alpha * rnd.uniform(0.4, 1))


def cave_arch(c, x, y, w, h, rock="#6f7a89", inner="#14121f"):
    outer = curve([(x - w * 0.9, y + 10), (x - w * 0.95, y - h * 0.8), (x - w * 0.4, y - h * 1.25),
                   (x + w * 0.4, y - h * 1.3), (x + w * 0.98, y - h * 0.75), (x + w * 0.9, y + 10)], close=False)
    outer.lineTo(x + w * 0.9, y + 60)
    outer.lineTo(x - w * 0.9, y + 60)
    outer.close()
    shape(c, outer, rock)
    hole = curve([(x - w * 0.5, y + 8), (x - w * 0.52, y - h * 0.55), (x, y - h * 0.86), (x + w * 0.52, y - h * 0.55),
                  (x + w * 0.5, y + 8)], close=False)
    hole.close()
    shape(c, hole, inner)
    # nieve sobre la roca
    snowcap = curve([(x - w * 0.8, y - h * 0.95), (x - w * 0.4, y - h * 1.32), (x + w * 0.4, y - h * 1.36),
                     (x + w * 0.85, y - h * 0.95), (x + w * 0.4, y - h * 1.15), (x, y - h * 1.1),
                     (x - w * 0.4, y - h * 1.15)], close=True)
    shape(c, snowcap, "#f4f9ff", 5)


def bush(c, x, y, r, col="#284d43", shake=0.0, T=0.0):
    dx = math.sin(T * 40) * 8 * shake
    pts = []
    for i in range(10):
        a = math.pi + i / 9 * math.pi
        rr = r * (0.85 + 0.2 * (i % 2))
        pts.append((x + dx + math.cos(a) * rr * 1.3, y + math.sin(a) * rr))
    pth = curve(pts, close=False)
    pth.lineTo(x + r * 1.3, y + 20)
    pth.lineTo(x - r * 1.3, y + 20)
    pth.close()
    shape(c, pth, col)


def eyes_pair(c, x, y, s, alpha=1.0, blink=0.0, col="#ffd23f"):
    if alpha <= 0:
        return
    glow(c, x, y, 90 * s, col, 0.35 * alpha)
    for sx in (-1, 1):
        ry = 9 * s * (1 - clamp(blink))
        if ry < 1:
            continue
        p = skia.Path()
        ex = x + sx * 26 * s
        p.moveTo(ex - 16 * s, y)
        p.quadTo(ex, y - ry * 2, ex + 16 * s, y + sx * 3 * s)
        p.quadTo(ex, y + ry, ex - 16 * s, y)
        c.drawPath(p, P("#fff6b0", alpha=alpha))
        circle(c, ex, y, 3 * s, "#2a1a00", 0, alpha=alpha)


def puff(c, x, y, r, p, col="#ffffff"):
    if p <= 0 or p >= 1:
        return
    for k in range(7):
        a = k / 7 * math.tau
        d = r * ease_out(p)
        circle(c, x + math.cos(a) * d, y + math.sin(a) * d, r * 0.35 * (1 - p), col, 4, alpha=1 - p)


def bubble(c, x, y, rx, ry, p, tail=None):
    """globo de pensamiento"""
    if p <= 0:
        return
    if tail:
        for i, k in enumerate((0.25, 0.5, 0.75)):
            tx = lerp(tail[0], x, k)
            ty = lerp(tail[1], y + ry * 0.6, k)
            circle(c, tx, ty, (10 + i * 10) * p, "#ffffff", 6)
    pts = []
    n = 12
    for i in range(n):
        a = i / n * math.tau
        rr = 1 + 0.08 * (i % 2)
        pts.append((x + math.cos(a) * rx * rr * p, y + math.sin(a) * ry * rr * p))
    shape(c, curve(pts, close=True), "#ffffff", 8)


def kettle_weight(c, x, y, s, label="6 T"):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawPath(curve([(-60, -120), (-70, -200), (0, -230), (70, -200), (60, -120)]), P(OUT, 46))
    c.drawPath(curve([(-60, -120), (-70, -200), (0, -230), (70, -200), (60, -120)]), P("#3d4250", 30))
    shape(c, path([(-150, 40), (-110, -130), (110, -130), (150, 40)]), "#3d4250")
    rrect(c, -165, 30, 330, 40, 12, "#2c303b")
    c.restore()
    text(c, label, x, y - 30 * s, 110 * s, "#ffe14a")


def hand_print(c, x, y, s, col="#b5562f", alpha=0.7):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    ellipse(c, 0, 0, 30, 36, col, 0, alpha=alpha)
    for k, (fx, fy, ang) in enumerate([(-30, -40, -30), (-12, -58, -8), (8, -60, 6), (26, -48, 22), (40, -6, 60)]):
        c.save()
        c.translate(fx, fy)
        c.rotate(ang)
        rrect(c, -8, -26, 16, 40, 8, col, 0, alpha=alpha)
        c.restore()
    c.restore()


def tribe_icon(c, x, y, s, T):
    for i, dx in enumerate((-70, 0, 70)):
        hh = 1 + 0.04 * math.sin(T * 6 + i)
        c.save()
        c.translate(x + dx * s, y)
        c.scale(s * hh, s * hh)
        circle(c, 0, -110, 30, "#c8956b")
        c.drawPath(curve([(-30, -112), (0, -150), (30, -112)]), P("#3a2414", 18))
        shape(c, path([(-38, -76), (38, -76), (48, 0), (-48, 0)]), "#8b5a33")
        c.restore()
